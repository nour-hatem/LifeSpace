"""Task use cases: create, get, and list (ADR 0002 items 4, 5, 8, 14, 15, and 16)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from lifespace.application.errors import (
    IdempotencyKeyReuseError,
    NotFoundError,
    ValidationFailedError,
    translate_domain_errors,
)
from lifespace.application.models import (
    CreateResult,
    CreateTaskCommand,
    IdempotencyInput,
    IdempotencyRecord,
    Page,
    StoredTask,
    TaskFilter,
    TaskView,
)
from lifespace.application.ports import Clock, IdGenerator, UnitOfWorkFactory
from lifespace.domain import task as domain_task
from lifespace.domain.overdue import is_overdue
from lifespace.domain.task import Task

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
