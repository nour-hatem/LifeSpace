"""In-memory fakes for the application ports (ADR 0002 items 1 to 7, 14, and 15)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

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
from lifespace.application.ports import (
    IdempotencyRepository,
    SettingsRepository,
    TaskRepository,
)
from lifespace.domain.errors import DomainValidationError
from lifespace.domain.lifecycle import StatusEvent
from lifespace.domain.task import Task
from lifespace.domain.time import as_instant, ensure_instant_in_range


class FakeClock:
    """A settable clock that returns an aware UTC instant (ADR 0002 item 1)."""

    def __init__(self, now: datetime | None = None) -> None:
        self._now = now if now is not None else datetime(2026, 1, 1, tzinfo=UTC)
        if self._now.tzinfo is None:
            raise ValueError("FakeClock needs an aware datetime")

    def now(self) -> datetime:
        """Return the instant the test set (ADR 0002 item 1)."""
        return self._now

    def set(self, now: datetime) -> None:
        """Move the clock to ``now``, which must be aware (ADR 0002 item 1)."""
        if now.tzinfo is None:
            raise ValueError("FakeClock needs an aware datetime")
        self._now = now


class SequentialIdGenerator:
    """Deterministic ids built from an incrementing counter (ADR 0002 item 1)."""

    def __init__(self, start: int = 1) -> None:
        self._next = start

    def new_id(self) -> UUID:
        """Return the next deterministic identifier (ADR 0002 item 1)."""
        value = UUID(int=self._next)
        self._next += 1
        return value


def _encode_cursor(instant: datetime, item_id: UUID) -> str:
    """Encode a keyset position as ``<iso instant>|<uuid>`` (ADR 0002 item 15)."""
    return f"{as_instant(instant).isoformat()}|{item_id}"


def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    """Decode a keyset position, raising ``InvalidCursorError`` when malformed."""
    instant_text, separator, id_text = cursor.partition("|")
    if not separator:
        raise InvalidCursorError("the cursor is invalid")
    try:
        instant = datetime.fromisoformat(instant_text)
        item_id = UUID(id_text)
    except ValueError as error:
        raise InvalidCursorError("the cursor is invalid") from error
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise InvalidCursorError("the cursor is invalid")
    try:
        normalized = as_instant(instant)
        ensure_instant_in_range(normalized, field="instant")
    except (DomainValidationError, OverflowError) as error:
        raise InvalidCursorError("the cursor is invalid") from error
    return normalized, item_id


def _task_key(stored: StoredTask) -> tuple[datetime, UUID]:
    """Return the task ordering key, newest first (ADR 0002 item 15)."""
    return (as_instant(stored.task.created_at), stored.task.id)


def _event_key(stored: StoredStatusEvent) -> tuple[datetime, UUID]:
    """Return the event ordering key, newest first (ADR 0002 item 15)."""
    return (as_instant(stored.event.occurred_at), stored.id)


class InMemoryStore:
    """The shared state behind the in-memory unit of work (ADR 0002 items 2 to 7)."""

    def __init__(self) -> None:
        self.tasks: dict[UUID, StoredTask] = {}
        self.deleted_at: dict[UUID, datetime] = {}
        self.events: dict[UUID, list[StoredStatusEvent]] = {}
        self.timezone: str = "UTC"
        self.timezone_updated_at: datetime | None = None
        self.idempotency: dict[str, IdempotencyRecord] = {}

    def copy(self) -> InMemoryStore:
        """Return a detached copy used as one transaction's working state."""
        clone = InMemoryStore()
        clone.tasks = dict(self.tasks)
        clone.deleted_at = dict(self.deleted_at)
        clone.events = {task_id: list(events) for task_id, events in self.events.items()}
        clone.timezone = self.timezone
        clone.timezone_updated_at = self.timezone_updated_at
        clone.idempotency = dict(self.idempotency)
        return clone

    def replace_with(self, other: InMemoryStore) -> None:
        """Write a committed working copy back into this store."""
        self.tasks = dict(other.tasks)
        self.deleted_at = dict(other.deleted_at)
        self.events = {task_id: list(events) for task_id, events in other.events.items()}
        self.timezone = other.timezone
        self.timezone_updated_at = other.timezone_updated_at
        self.idempotency = dict(other.idempotency)


class InMemoryTaskRepository:
    """In-memory task repository with versions, soft delete, and keyset pages (ADR 0002 item 4)."""

    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def add(self, task: Task) -> StoredTask:
        """Store a new task at version 1 (ADR 0002 item 4)."""
        stored = StoredTask(task=task, version=1)
        self._store.tasks[task.id] = stored
        return stored

    async def get(self, task_id: UUID) -> StoredTask | None:
        """Return a task, or ``None`` when it is missing or soft deleted (ADR 0002 item 5)."""
        if task_id in self._store.deleted_at:
            return None
        return self._store.tasks.get(task_id)

    async def list(
        self,
        task_filter: TaskFilter,
        *,
        limit: int,
        cursor: str | None = None,
    ) -> Page[StoredTask]:
        """Return one page ordered by created_at then id, newest first (ADR 0002 item 15)."""
        ordered = sorted(
            (
                stored
                for task_id, stored in self._store.tasks.items()
                if task_id not in self._store.deleted_at
            ),
            key=_task_key,
            reverse=True,
        )
        ordered = [stored for stored in ordered if _matches(stored, task_filter)]
        if cursor is not None:
            cursor_key = _decode_cursor(cursor)
            ordered = [stored for stored in ordered if _task_key(stored) < cursor_key]
        page_items = ordered[:limit]
        next_cursor = (
            _encode_cursor(*_task_key(page_items[-1]))
            if page_items and len(ordered) > len(page_items)
            else None
        )
        return Page(items=tuple(page_items), next_cursor=next_cursor)

    async def save(self, task: Task, *, expected_version: int) -> StoredTask:
        """Replace a task and increment its version (ADR 0002 item 4)."""
        self._current(task.id, expected_version)
        stored = StoredTask(task=task, version=expected_version + 1)
        self._store.tasks[task.id] = stored
        return stored

    async def soft_delete(
        self,
        task_id: UUID,
        *,
        expected_version: int,
        now: datetime,
    ) -> None:
        """Hide a task from every read and keep its events (ADR 0002 items 4 and 5)."""
        current = self._current(task_id, expected_version)
        self._store.tasks[task_id] = StoredTask(task=current.task, version=expected_version + 1)
        self._store.deleted_at[task_id] = now

    async def add_event(self, event_id: UUID, event: StatusEvent) -> None:
        """Append a status event (ADR 0002 item 6)."""
        self._store.events.setdefault(event.task_id, []).append(
            StoredStatusEvent(id=event_id, event=event)
        )

    async def list_events(
        self,
        task_id: UUID,
        *,
        limit: int,
        cursor: str | None = None,
    ) -> Page[StoredStatusEvent]:
        """Return one page of a task's events, newest first (ADR 0002 item 15)."""
        ordered = sorted(self._store.events.get(task_id, []), key=_event_key, reverse=True)
        if cursor is not None:
            cursor_key = _decode_cursor(cursor)
            ordered = [stored for stored in ordered if _event_key(stored) < cursor_key]
        page_items = ordered[:limit]
        next_cursor = (
            _encode_cursor(*_event_key(page_items[-1]))
            if page_items and len(ordered) > len(page_items)
            else None
        )
        return Page(items=tuple(page_items), next_cursor=next_cursor)

    def _current(self, task_id: UUID, expected_version: int) -> StoredTask:
        """Return the stored task when it exists at the expected version."""
        stored = self._store.tasks.get(task_id)
        if stored is None or task_id in self._store.deleted_at:
            raise NotFoundError(f"task {task_id} was not found")
        if stored.version != expected_version:
            raise StaleVersionError(expected_version, stored.version)
        return stored


def _matches(stored: StoredTask, task_filter: TaskFilter) -> bool:
    """Return whether a stored task passes the filter (ADR 0002 item 16)."""
    task = stored.task
    if task_filter.statuses and task.status not in task_filter.statuses:
        return False
    if task_filter.category is not None and task.category is not task_filter.category:
        return False
    return task_filter.priority is None or task.priority is task_filter.priority


class InMemorySettingsRepository:
    """In-memory ``SettingsRepository`` with a UTC default (ADR 0002 item 8)."""

    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def get_timezone(self) -> str:
        """Return the stored zone, UTC by default (ADR 0002 item 8)."""
        return self._store.timezone

    async def set_timezone(self, timezone: str, *, now: datetime) -> None:
        """Store the zone and the instant it changed (ADR 0002 item 8)."""
        self._store.timezone = timezone
        self._store.timezone_updated_at = now


class InMemoryIdempotencyRepository:
    """In-memory ``IdempotencyRepository`` with unique keys (ADR 0002 item 14)."""

    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def get(self, key: str) -> IdempotencyRecord | None:
        """Return the record stored for ``key``, if any (ADR 0002 item 14)."""
        return self._store.idempotency.get(key)

    async def add(self, record: IdempotencyRecord, *, now: datetime) -> None:
        """Store a record, raising when the key is already in use (ADR 0002 item 14)."""
        if record.key in self._store.idempotency:
            raise IdempotencyInProgressError()
        self._store.idempotency[record.key] = record


class InMemoryUnitOfWork:
    """A transaction over an ``InMemoryStore`` (ADR 0002 item 2).

    Entering copies the shared store, ``commit`` writes the copy back, and
    leaving without a commit discards it (ADR 0002 item 2).
    """

    def __init__(self, store: InMemoryStore) -> None:
        self._store = store
        self._working: InMemoryStore | None = None
        self._committed = False
        self.tasks: TaskRepository
        self.settings: SettingsRepository
        self.idempotency: IdempotencyRepository

    async def __aenter__(self) -> InMemoryUnitOfWork:
        """Start a transaction on a copy of the shared store (ADR 0002 item 2)."""
        self._working = self._store.copy()
        self._committed = False
        self.tasks = InMemoryTaskRepository(self._working)
        self.settings = InMemorySettingsRepository(self._working)
        self.idempotency = InMemoryIdempotencyRepository(self._working)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Discard uncommitted work when the block leaves (ADR 0002 item 2)."""
        if not self._committed:
            await self.rollback()

    async def commit(self) -> None:
        """Write the working copy back into the shared store (ADR 0002 item 2)."""
        if self._working is None:
            raise RuntimeError("the unit of work is not active")
        self._store.replace_with(self._working)
        self._committed = True

    async def rollback(self) -> None:
        """Discard the working copy (ADR 0002 item 2)."""
        self._working = None
        self._committed = False
