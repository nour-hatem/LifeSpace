"""Task use cases: create, read, edit, delete, transition, and history (ADR 0002 items 4 to 6)."""

from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from lifespace.application.errors import (
    IdempotencyKeyReuseError,
    NotFoundError,
    StaleVersionError,
    ValidationFailedError,
    translate_domain_errors,
)
from lifespace.application.models import (
    CreateResult,
    CreateTaskCommand,
    IdempotencyInput,
    IdempotencyRecord,
    Page,
    StoredStatusEvent,
    StoredTask,
    TaskChanges,
    TaskFilter,
    TaskView,
)
from lifespace.application.ports import Clock, IdGenerator, UnitOfWorkFactory
from lifespace.domain import lifecycle as domain_lifecycle
from lifespace.domain import task as domain_task
from lifespace.domain.overdue import is_overdue
from lifespace.domain.task import Task, TaskStatus, Unset

MAX_PAGE_LIMIT = 200


def _to_view(stored: StoredTask, now: datetime, timezone: str) -> TaskView:
    """Attach the overdue flag computed from the stored zone (ADR 0002 item 8)."""
    return TaskView(stored=stored, is_overdue=is_overdue(stored.task, now, ZoneInfo(timezone)))


def _build_task(ids: IdGenerator, now: datetime, command: CreateTaskCommand) -> Task:
    """Build the domain task from a command, translating domain errors (ADR 0002 item 17)."""
    with translate_domain_errors():
        return domain_task.create_task(
            task_id=ids.new_id(),
            title=command.title,
            now=now,
            source=command.source,
            status=command.status,
            description=command.description,
            category=command.category,
            priority=command.priority,
            estimate_minutes=command.estimate_minutes,
            deadline=command.deadline,
            scheduled=command.scheduled,
        )


async def create_task(
    uow_factory: UnitOfWorkFactory,
    clock: Clock,
    ids: IdGenerator,
    command: CreateTaskCommand,
    *,
    idempotency: IdempotencyInput | None = None,
) -> CreateResult:
    """Create a task, replaying the stored result for a used key (ADR 0002 item 14).

    Without a key, or with a key that was never used, the task and (when a key
    was given) its idempotency record are written in one transaction (ADR 0002
    items 2 and 14). A key with the same fingerprint replays the original task
    as it currently exists and writes nothing; a key with another fingerprint,
    or one whose task no longer exists, raises ``IdempotencyKeyReuseError``
    (ADR 0002 item 14).
    """
    now = clock.now()
    async with uow_factory() as uow:
        timezone = await uow.settings.get_timezone()

        if idempotency is None:
            task = _build_task(ids, now, command)
            stored = await uow.tasks.add(task)
            await uow.commit()
            return CreateResult(view=_to_view(stored, now, timezone), replayed=False)

        record = await uow.idempotency.get(idempotency.key)
        if record is not None:
            if record.request_fingerprint != idempotency.fingerprint:
                raise IdempotencyKeyReuseError(
                    "the idempotency key was already used for another request"
                )
            replayed = await uow.tasks.get(record.task_id)
            if replayed is None:
                raise IdempotencyKeyReuseError(
                    "the idempotency key belongs to a task that no longer exists"
                )
            return CreateResult(view=_to_view(replayed, now, timezone), replayed=True)

        task = _build_task(ids, now, command)
        stored = await uow.tasks.add(task)
        await uow.idempotency.add(
            IdempotencyRecord(
                key=idempotency.key,
                request_fingerprint=idempotency.fingerprint,
                task_id=task.id,
            ),
            now=now,
        )
        await uow.commit()
        return CreateResult(view=_to_view(stored, now, timezone), replayed=False)


async def get_task(uow_factory: UnitOfWorkFactory, clock: Clock, task_id: UUID) -> TaskView:
    """Return one task with its overdue flag (ADR 0002 items 5 and 8).

    A missing or soft deleted task raises ``NotFoundError`` (ADR 0002 item 5).
    """
    now = clock.now()
    async with uow_factory() as uow:
        timezone = await uow.settings.get_timezone()
        stored = await uow.tasks.get(task_id)
        if stored is None:
            raise NotFoundError(f"task {task_id} was not found")
        return _to_view(stored, now, timezone)


async def list_tasks(
    uow_factory: UnitOfWorkFactory,
    clock: Clock,
    task_filter: TaskFilter,
    *,
    limit: int,
    cursor: str | None = None,
) -> Page[TaskView]:
    """Return one page of tasks, newest first, with overdue flags (ADR 0002 items 8 and 15).

    ``limit`` must be between 1 and 200 (ADR 0002 item 15); ``cursor`` is the
    opaque ``next_cursor`` of the previous page.
    """
    if limit < 1 or limit > MAX_PAGE_LIMIT:
        raise ValidationFailedError(
            f"limit must be between 1 and {MAX_PAGE_LIMIT}",
            field="limit",
        )
    now = clock.now()
    async with uow_factory() as uow:
        timezone = await uow.settings.get_timezone()
        page = await uow.tasks.list(task_filter, limit=limit, cursor=cursor)
        return Page(
            items=tuple(_to_view(stored, now, timezone) for stored in page.items),
            next_cursor=page.next_cursor,
        )


def _existing(stored: StoredTask | None, task_id: UUID) -> StoredTask:
    """Return the stored task or raise ``NotFoundError`` (ADR 0002 item 5)."""
    if stored is None:
        raise NotFoundError(f"task {task_id} was not found")
    return stored


def _require_version(stored: StoredTask, expected_version: int) -> None:
    """Raise ``StaleVersionError`` when the caller's version is out of date (ADR 0002 item 4)."""
    if stored.version != expected_version:
        raise StaleVersionError(expected_version, stored.version)


def _has_changes(changes: TaskChanges) -> bool:
    """Return whether at least one field is not ``UNSET`` (ADR 0001 item 12)."""
    return any(not isinstance(getattr(changes, field.name), Unset) for field in fields(changes))


async def edit_task(
    uow_factory: UnitOfWorkFactory,
    clock: Clock,
    task_id: UUID,
    expected_version: int,
    changes: TaskChanges,
) -> TaskView:
    """Edit a stored task and return its new view (ADR 0002 item 4).

    The task must exist and at least one field must be given. The stale version
    check deliberately runs before the domain rule: a caller whose picture of
    the task is out of date gets ``StaleVersionError`` even when the edit would
    also be rejected, because the domain verdict on an outdated snapshot may be
    meaningless (ADR 0002 item 4). ``UNSET`` fields are left unchanged and
    ``None`` clears an optional field (ADR 0001 item 12).
    """
    now = clock.now()
    async with uow_factory() as uow:
        timezone = await uow.settings.get_timezone()
        stored = _existing(await uow.tasks.get(task_id), task_id)
        if not _has_changes(changes):
            raise ValidationFailedError("no changes given")
        _require_version(stored, expected_version)
        with translate_domain_errors():
            edited = domain_task.edit_task(
                stored.task,
                now=now,
                title=changes.title,
                description=changes.description,
                category=changes.category,
                priority=changes.priority,
                estimate_minutes=changes.estimate_minutes,
                deadline=changes.deadline,
                scheduled=changes.scheduled,
            )
        saved = await uow.tasks.save(edited, expected_version=expected_version)
        await uow.commit()
        return _to_view(saved, now, timezone)


async def delete_task(
    uow_factory: UnitOfWorkFactory,
    clock: Clock,
    task_id: UUID,
    expected_version: int,
) -> None:
    """Soft delete a task after the version check (ADR 0002 items 4 and 5).

    A missing or already deleted task raises ``NotFoundError`` and an outdated
    version raises ``StaleVersionError``; both write nothing.
    """
    now = clock.now()
    async with uow_factory() as uow:
        await uow.tasks.soft_delete(task_id, expected_version=expected_version, now=now)
        await uow.commit()


async def transition_task(
    uow_factory: UnitOfWorkFactory,
    clock: Clock,
    ids: IdGenerator,
    task_id: UUID,
    to_status: TaskStatus,
    expected_version: int,
    reason: str | None = None,
) -> TaskView:
    """Transition a task and record its status event (ADR 0002 item 6).

    The task must exist and the expected version must be current; the stale
    version check wins over a domain rejection because the caller's picture is
    out of date (ADR 0002 item 4). The domain decides which transitions are
    legal and rejects the rest with ``TransitionRejectedError`` (ADR 0001 item
    6). The new task and its event are written and committed together, so a
    failure in either leaves neither stored (ADR 0002 item 6).
    """
    now = clock.now()
    async with uow_factory() as uow:
        timezone = await uow.settings.get_timezone()
        stored = _existing(await uow.tasks.get(task_id), task_id)
        _require_version(stored, expected_version)
        with translate_domain_errors():
            result = domain_lifecycle.transition_task(
                stored.task,
                to_status,
                now=now,
                reason=reason,
            )
        saved = await uow.tasks.save(result.task, expected_version=expected_version)
        await uow.tasks.add_event(ids.new_id(), result.event)
        await uow.commit()
        return _to_view(saved, now, timezone)


async def list_task_events(
    uow_factory: UnitOfWorkFactory,
    task_id: UUID,
    *,
    limit: int,
    cursor: str | None = None,
) -> Page[StoredStatusEvent]:
    """Return one page of a task's status events, newest first (ADR 0002 item 15).

    The task must exist and must not be deleted, even though a deleted task
    keeps its events (ADR 0002 items 5 and 6). ``limit`` must be between 1 and
    200 (ADR 0002 item 15).
    """
    if limit < 1 or limit > MAX_PAGE_LIMIT:
        raise ValidationFailedError(
            f"limit must be between 1 and {MAX_PAGE_LIMIT}",
            field="limit",
        )
    async with uow_factory() as uow:
        _existing(await uow.tasks.get(task_id), task_id)
        return await uow.tasks.list_events(task_id, limit=limit, cursor=cursor)
