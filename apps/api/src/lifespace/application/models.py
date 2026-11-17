"""Application data models (ADR 0002 items 3, 4, 8, 14, and 15)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from lifespace.domain.deadline import Deadline
from lifespace.domain.lifecycle import StatusEvent
from lifespace.domain.task import UNSET, Category, Priority, Task, TaskSource, TaskStatus, Unset
from lifespace.domain.time import TimeInterval


@dataclass(frozen=True, slots=True)
class StoredTask:
    """A task snapshot with its optimistic concurrency version (ADR 0002 items 3 and 4)."""

    task: Task
    version: int


@dataclass(frozen=True, slots=True)
class StoredStatusEvent:
    """A status event paired with its stable identifier (ADR 0002 item 6)."""

    id: UUID
    event: StatusEvent


@dataclass(frozen=True, slots=True)
class TaskView:
    """A stored task with its computed overdue flag (ADR 0002 item 8)."""

    stored: StoredTask
    is_overdue: bool


@dataclass(frozen=True, slots=True)
class Page[T]:
    """One page of a keyset paginated list (ADR 0002 item 15)."""

    items: tuple[T, ...]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class TaskFilter:
    """The supported task list filters (ADR 0002 item 16).

    An empty ``statuses`` set means every status.
    """

    statuses: frozenset[TaskStatus] = frozenset()
    category: Category | None = None
    priority: Priority | None = None


@dataclass(frozen=True, slots=True)
class CreateTaskCommand:
    """The inputs for creating a task (ADR 0002 items 9 and 14)."""

    title: str
    description: str | None = None
    category: Category | None = None
    priority: Priority | None = None
    estimate_minutes: int | None = None
    deadline: Deadline | None = None
    scheduled: TimeInterval | None = None
    status: TaskStatus = TaskStatus.PLANNED
    source: TaskSource = TaskSource.MANUAL


@dataclass(frozen=True, slots=True)
class TaskChanges:
    """The optional edits for an existing task (ADR 0001 item 12).

    A field left at ``UNSET`` is unchanged and ``None`` clears an optional
    field, exactly like the ``edit_task`` parameters (ADR 0001 item 12).
    """

    title: str | Unset = UNSET
    description: str | Unset | None = UNSET
    category: Category | Unset | None = UNSET
    priority: Priority | Unset | None = UNSET
    estimate_minutes: int | Unset | None = UNSET
    deadline: Deadline | Unset | None = UNSET
    scheduled: TimeInterval | Unset | None = UNSET


@dataclass(frozen=True, slots=True)
class IdempotencyInput:
    """The key and request fingerprint supplied for a create (ADR 0002 item 14)."""

    key: str
    fingerprint: str


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    """A stored idempotency key bound to the task it produced (ADR 0002 item 14)."""

    key: str
    request_fingerprint: str
    task_id: UUID


@dataclass(frozen=True, slots=True)
class CreateResult:
    """The created or replayed task view plus the replay flag (ADR 0002 item 14)."""

    view: TaskView
    replayed: bool


@dataclass(frozen=True, slots=True)
class AppSettings:
    """The user's application settings (ADR 0002 item 8)."""

    timezone: str
