"""Ports the application layer needs from infrastructure (ADR 0002 items 1 to 7, 14, and 15)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from lifespace.application.models import (
    IdempotencyRecord,
    Page,
    StoredStatusEvent,
    StoredTask,
    TaskFilter,
)
from lifespace.domain.lifecycle import StatusEvent
from lifespace.domain.task import Task


class Clock(Protocol):
    """Supplies the current instant to use cases (ADR 0002 item 1)."""

    def now(self) -> datetime:
        """Return the current time as an aware datetime."""
        ...


class IdGenerator(Protocol):
    """Supplies new identifiers to use cases (ADR 0002 item 1)."""

    def new_id(self) -> UUID:
        """Return a new identifier."""
        ...


class TaskRepository(Protocol):
    """The persistence operations for tasks and their status events (ADR 0002 items 3 to 6)."""

    async def add(self, task: Task) -> StoredTask:
        """Store a new task at version 1 (ADR 0002 item 4)."""
        ...

    async def get(self, task_id: UUID) -> StoredTask | None:
        """Return a task, or ``None`` when it is missing or soft deleted (ADR 0002 item 5)."""
        ...

    async def list(
        self,
        task_filter: TaskFilter,
        *,
        limit: int,
        cursor: str | None = None,
    ) -> Page[StoredTask]:
        """Return one page of tasks, newest first (ADR 0002 item 15)."""
        ...

    async def save(self, task: Task, *, expected_version: int) -> StoredTask:
        """Replace a task, raising ``StaleVersionError`` or ``NotFoundError`` (ADR 0002 item 4).

        The returned version is ``expected_version + 1``.
        """
        ...

    async def soft_delete(
        self,
        task_id: UUID,
        *,
        expected_version: int,
        now: datetime,
    ) -> None:
        """Hide a task from every read, raising the same errors as ``save`` (ADR 0002 item 5)."""
        ...

    async def add_event(self, event_id: UUID, event: StatusEvent) -> None:
        """Append a status event (ADR 0002 item 6)."""
        ...

    async def list_events(
        self,
        task_id: UUID,
        *,
        limit: int,
        cursor: str | None = None,
    ) -> Page[StoredStatusEvent]:
        """Return one page of a task's events, newest first (ADR 0002 item 15)."""
        ...


class SettingsRepository(Protocol):
    """The persistence operations for the single settings row (ADR 0002 item 8)."""

    async def get_timezone(self) -> str:
        """Return the user's IANA time zone."""
        ...

    async def set_timezone(self, timezone: str, *, now: datetime) -> None:
        """Replace the user's IANA time zone."""
        ...


class IdempotencyRepository(Protocol):
    """The persistence operations for idempotency keys (ADR 0002 item 14)."""

    async def get(self, key: str) -> IdempotencyRecord | None:
        """Return the record stored for ``key``, if any."""
        ...

    async def add(self, record: IdempotencyRecord, *, now: datetime) -> None:
        """Store a record, raising ``IdempotencyInProgressError`` when the key exists."""
        ...


class UnitOfWork(Protocol):
    """One transaction with its repositories (ADR 0002 item 2)."""

    tasks: TaskRepository
    settings: SettingsRepository
    idempotency: IdempotencyRepository

    async def __aenter__(self) -> UnitOfWork:
        """Begin the transaction and return the unit of work."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Discard uncommitted work when the block leaves (ADR 0002 item 2)."""
        ...

    async def commit(self) -> None:
        """Persist every change made in this transaction."""
        ...

    async def rollback(self) -> None:
        """Discard every change made in this transaction."""
        ...


UnitOfWorkFactory = Callable[[], UnitOfWork]
