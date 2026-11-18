"""SQLAlchemy implementations of the application repositories (ADR 0002 items 3 to 8, 14, 15)."""

from __future__ import annotations

from datetime import datetime
from typing import Never
from uuid import UUID

from sqlalchemy import insert, select, tuple_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from lifespace.application.errors import (
    IdempotencyInProgressError,
    InvalidCursorError,
    NotFoundError,
    StaleVersionError,
)
from lifespace.application.models import (
    IdempotencyRecord,
    Page,
    StoredStatusEvent,
    StoredTask,
    TaskFilter,
)
from lifespace.domain.lifecycle import StatusEvent
from lifespace.domain.task import Task
from lifespace.domain.time import as_instant
from lifespace.infrastructure.cursor import decode_cursor, encode_cursor
from lifespace.infrastructure.mapping import (
    event_to_values,
    row_to_stored_event,
    row_to_stored_task,
    task_to_values,
)
from lifespace.infrastructure.models import (
    AppSettingsRow,
    IdempotencyKeyRow,
    StatusEventRow,
    TaskRow,
)


def _encode_keyset(instant: datetime, item_id: UUID) -> str:
    """Encode one ordering position as a cursor (ADR 0002 item 15)."""
    return encode_cursor([as_instant(instant).isoformat(), str(item_id)])


def _decode_keyset(cursor: str) -> tuple[datetime, UUID]:
    """Decode a cursor into its instant and identifier, or raise ``InvalidCursorError``."""
    instant_text, id_text = decode_cursor(cursor, 2)
    try:
        instant = datetime.fromisoformat(instant_text)
        item_id = UUID(id_text)
    except ValueError as error:
        raise InvalidCursorError("the cursor is invalid") from error
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise InvalidCursorError("the cursor is invalid")
    return as_instant(instant), item_id


def _task_conditions(task_filter: TaskFilter) -> list[ColumnElement[bool]]:
    """Return the SQL conditions for a task list filter (ADR 0002 item 16)."""
    conditions: list[ColumnElement[bool]] = [TaskRow.deleted_at.is_(None)]
    if task_filter.statuses:
        conditions.append(TaskRow.status.in_(status.value for status in task_filter.statuses))
    if task_filter.category is not None:
        conditions.append(TaskRow.category == task_filter.category.value)
    if task_filter.priority is not None:
        conditions.append(TaskRow.priority == task_filter.priority.value)
    return conditions


class SqlAlchemyTaskRepository:
    """Task and status history persistence over one session (ADR 0002 items 3 to 6)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, task: Task) -> StoredTask:
        """Insert a new task at version 1 and return it (ADR 0002 item 4)."""
        row = TaskRow(**task_to_values(task, version=1))
        self._session.add(row)
        await self._session.flush()
        return row_to_stored_task(row)

    async def get(self, task_id: UUID) -> StoredTask | None:
        """Return a task, or ``None`` when it is missing or soft deleted (ADR 0002 item 5)."""
        row = (
            await self._session.execute(
                select(TaskRow).where(
                    TaskRow.id == task_id,
                    TaskRow.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        return None if row is None else row_to_stored_task(row)

    async def list(
        self,
        task_filter: TaskFilter,
        *,
        limit: int,
        cursor: str | None = None,
    ) -> Page[StoredTask]:
        """Return one keyset page of tasks, newest first (ADR 0002 items 15 and 16)."""
        statement = (
            select(TaskRow)
            .where(*_task_conditions(task_filter))
            .order_by(TaskRow.created_at.desc(), TaskRow.id.desc())
        )
        if cursor is not None:
            created_at, last_id = _decode_keyset(cursor)
            statement = statement.where(
                tuple_(TaskRow.created_at, TaskRow.id) < (created_at, last_id)
            )
        rows = (await self._session.execute(statement.limit(limit + 1))).scalars().all()
        page = rows[:limit]
        next_cursor = None
        if len(rows) > limit:
            last = page[-1]
            next_cursor = _encode_keyset(last.created_at, last.id)
        return Page(
            items=tuple(row_to_stored_task(row) for row in page),
            next_cursor=next_cursor,
        )

    async def save(self, task: Task, *, expected_version: int) -> StoredTask:
        """Update every mutable column, guarded by the version (ADR 0002 item 4)."""
        values = task_to_values(task, version=expected_version + 1)
        for immutable in ("id", "created_at", "deleted_at"):
            values.pop(immutable, None)
        statement = (
            update(TaskRow)
            .where(
                TaskRow.id == task.id,
                TaskRow.version == expected_version,
                TaskRow.deleted_at.is_(None),
            )
            .values(**values)
            .returning(TaskRow)
        )
        row = (await self._session.execute(statement)).scalar_one_or_none()
        if row is None:
            await self._raise_not_found_or_stale(task.id, expected_version)
        return row_to_stored_task(row)

    async def soft_delete(
        self,
        task_id: UUID,
        *,
        expected_version: int,
        now: datetime,
    ) -> None:
        """Mark a task deleted with the same version guard as ``save`` (ADR 0002 item 5)."""
        instant = as_instant(now)
        statement = (
            update(TaskRow)
            .where(
                TaskRow.id == task_id,
                TaskRow.version == expected_version,
                TaskRow.deleted_at.is_(None),
            )
            .values(
                deleted_at=instant,
                updated_at=instant,
                version=TaskRow.version + 1,
            )
            .returning(TaskRow.id)
        )
        deleted_id = (await self._session.execute(statement)).scalar_one_or_none()
        if deleted_id is None:
            await self._raise_not_found_or_stale(task_id, expected_version)

    async def add_event(self, event_id: UUID, event: StatusEvent) -> None:
        """Append one status event (ADR 0002 item 6)."""
        await self._session.execute(
            insert(StatusEventRow).values(**event_to_values(event_id, event))
        )

    async def list_events(
        self,
        task_id: UUID,
        *,
        limit: int,
        cursor: str | None = None,
    ) -> Page[StoredStatusEvent]:
        """Return one keyset page of events, newest first (ADR 0002 item 15)."""
        statement = (
            select(StatusEventRow)
            .where(StatusEventRow.task_id == task_id)
            .order_by(StatusEventRow.occurred_at.desc(), StatusEventRow.id.desc())
        )
        if cursor is not None:
            occurred_at, last_id = _decode_keyset(cursor)
            statement = statement.where(
                tuple_(StatusEventRow.occurred_at, StatusEventRow.id) < (occurred_at, last_id)
            )
        rows = (await self._session.execute(statement.limit(limit + 1))).scalars().all()
        page = rows[:limit]
        next_cursor = None
        if len(rows) > limit:
            last = page[-1]
            next_cursor = _encode_keyset(last.occurred_at, last.id)
        return Page(
            items=tuple(row_to_stored_event(row) for row in page),
            next_cursor=next_cursor,
        )

    async def _raise_not_found_or_stale(self, task_id: UUID, expected_version: int) -> Never:
        """Report why the guarded update matched no row (ADR 0002 items 4 and 5)."""
        current_version = await self._session.scalar(
            select(TaskRow.version).where(
                TaskRow.id == task_id,
                TaskRow.deleted_at.is_(None),
            )
        )
        if current_version is None:
            raise NotFoundError(f"task {task_id} was not found")
        raise StaleVersionError(expected_version, current_version)


class SqlAlchemySettingsRepository:
    """Persistence for the single settings row (ADR 0002 item 8)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_timezone(self) -> str:
        """Return the stored IANA time zone (ADR 0002 item 8)."""
        timezone = await self._session.scalar(
            select(AppSettingsRow.timezone).where(AppSettingsRow.id == 1)
        )
        if timezone is None:
            raise NotFoundError("the settings row was not found")
        return timezone

    async def set_timezone(self, timezone: str, *, now: datetime) -> None:
        """Replace the stored IANA time zone and its update instant (ADR 0002 item 8)."""
        await self._session.execute(
            update(AppSettingsRow)
            .where(AppSettingsRow.id == 1)
            .values(timezone=timezone, updated_at=as_instant(now))
        )


class SqlAlchemyIdempotencyRepository:
    """Persistence for idempotency keys (ADR 0002 item 14)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, key: str) -> IdempotencyRecord | None:
        """Return the record stored for ``key``, if any (ADR 0002 item 14)."""
        row = await self._session.scalar(
            select(IdempotencyKeyRow).where(IdempotencyKeyRow.key == key)
        )
        if row is None:
            return None
        return IdempotencyRecord(
            key=row.key,
            request_fingerprint=row.request_fingerprint,
            task_id=row.task_id,
        )

    async def add(self, record: IdempotencyRecord, *, now: datetime) -> None:
        """Insert a record, mapping a duplicate key to ``IdempotencyInProgressError``."""
        try:
            async with self._session.begin_nested():
                await self._session.execute(
                    insert(IdempotencyKeyRow).values(
                        key=record.key,
                        request_fingerprint=record.request_fingerprint,
                        task_id=record.task_id,
                        created_at=as_instant(now),
                    )
                )
        except IntegrityError as error:
            if "pk_idempotency_keys" in str(error.orig):
                raise IdempotencyInProgressError() from error
            raise
