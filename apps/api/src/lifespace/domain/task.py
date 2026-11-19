"""The Task model: enums, creation, editing, and validation.

The rules are ADR 0001 items 4, 10, 11, 12, 14, and 16.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from lifespace.domain.deadline import Deadline
from lifespace.domain.errors import DomainValidationError
from lifespace.domain.limits import (
    MAX_DESCRIPTION_LENGTH,
    MAX_INT32,
    MAX_REASON_LENGTH,
    MAX_TITLE_LENGTH,
    ensure_text,
)
from lifespace.domain.time import TimeInterval, as_instant, ensure_instant_in_range


class TaskStatus(StrEnum):
    """The lifecycle status of a task (ADR 0001 items 4 to 6)."""

    INBOX = "inbox"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


class Priority(StrEnum):
    """The optional task priority, ordered from most to least important (ADR 0001 item 15)."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def rank(self) -> int:
        """Return 1 for ``CRITICAL`` through 4 for ``LOW``.

        Lower is more important (ADR 0001 item 15).
        """
        return _PRIORITY_RANKS[self]


_PRIORITY_RANKS: dict[Priority, int] = {
    Priority.CRITICAL: 1,
    Priority.HIGH: 2,
    Priority.MEDIUM: 3,
    Priority.LOW: 4,
}


class Category(StrEnum):
    """The optional task category (ADR 0001 item 15)."""

    WORK = "work"
    EDUCATION = "education"
    LEARNING = "learning"
    PERSONAL = "personal"
    PROJECTS = "projects"


class TaskSource(StrEnum):
    """How a task entered the system (ADR 0001 item 15)."""

    MANUAL = "manual"
    AI = "ai"


class _Unset:
    """The type of the ``UNSET`` sentinel."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"


Unset = _Unset
UNSET = _Unset()


@dataclass(frozen=True, slots=True)
class Task:
    """A task snapshot with its validated deadline, estimate, and schedule.

    The model implements ADR 0001 items 4, 7, 10, 11, 12, 14, 16, and 19. A
    deadline and a scheduled interval are independent: editing one never
    changes the other or the estimate (ADR 0001 item 12).
    """

    id: UUID
    title: str
    status: TaskStatus
    source: TaskSource
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    category: Category | None = None
    priority: Priority | None = None
    estimate_minutes: int | None = None
    deadline: Deadline | None = None
    scheduled: TimeInterval | None = None
    completed_at: datetime | None = None
    canceled_at: datetime | None = None
    cancellation_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate every task invariant (ADR 0001 items 4, 7, 10, 11, 14, 16, 19)."""
        stripped_title = self.title.strip()
        if not stripped_title:
            raise DomainValidationError("title must not be empty", field="title")
        if stripped_title != self.title:
            raise DomainValidationError(
                "title must not have leading or trailing whitespace", field="title"
            )
        ensure_text(self.title, field="title", max_length=MAX_TITLE_LENGTH)
        if self.description is not None:
            ensure_text(
                self.description,
                field="description",
                max_length=MAX_DESCRIPTION_LENGTH,
            )

        ensure_instant_in_range(self.created_at, field="created_at")
        ensure_instant_in_range(self.updated_at, field="updated_at")
        if self.completed_at is not None:
            ensure_instant_in_range(self.completed_at, field="completed_at")
        if self.canceled_at is not None:
            ensure_instant_in_range(self.canceled_at, field="canceled_at")
        if as_instant(self.updated_at) < as_instant(self.created_at):
            raise DomainValidationError(
                "updated_at must not be before created_at", field="updated_at"
            )

        if self.estimate_minutes is not None:
            if isinstance(self.estimate_minutes, bool) or not isinstance(
                self.estimate_minutes, int
            ):
                raise DomainValidationError(
                    "estimate_minutes must be a whole number", field="estimate_minutes"
                )
            if self.estimate_minutes <= 0:
                raise DomainValidationError(
                    "estimate_minutes must be greater than zero", field="estimate_minutes"
                )
            if self.estimate_minutes > MAX_INT32:
                raise DomainValidationError(
                    "estimate_minutes must not exceed 2147483647",
                    field="estimate_minutes",
                )

        if (self.status is TaskStatus.COMPLETED) != (self.completed_at is not None):
            raise DomainValidationError(
                "completed_at is required exactly when the task is completed",
                field="completed_at",
            )
        if (self.status is TaskStatus.CANCELED) != (self.canceled_at is not None):
            raise DomainValidationError(
                "canceled_at is required exactly when the task is canceled",
                field="canceled_at",
            )

        if self.cancellation_reason is not None:
            if self.status is not TaskStatus.CANCELED:
                raise DomainValidationError(
                    "cancellation_reason is only allowed on a canceled task",
                    field="cancellation_reason",
                )
            if not self.cancellation_reason.strip():
                raise DomainValidationError(
                    "cancellation_reason must not be empty", field="cancellation_reason"
                )
            ensure_text(
                self.cancellation_reason,
                field="cancellation_reason",
                max_length=MAX_REASON_LENGTH,
            )


def _normalize_description(description: str | None) -> str | None:
    """Strip a description and return ``None`` when nothing remains."""
    if description is None:
        return None
    return description.strip() or None


def create_task(
    *,
    task_id: UUID,
    title: str,
    now: datetime,
    source: TaskSource = TaskSource.MANUAL,
    status: TaskStatus = TaskStatus.PLANNED,
    description: str | None = None,
    category: Category | None = None,
    priority: Priority | None = None,
    estimate_minutes: int | None = None,
    deadline: Deadline | None = None,
    scheduled: TimeInterval | None = None,
) -> Task:
    """Create a reviewed or inbox task as it is at ``now`` (ADR 0001 items 4, 10, 11, 14).

    Only ``INBOX`` and ``PLANNED`` are allowed at creation; a directly
    completable task must be planned (ADR 0001 item 4). The title is stripped
    (ADR 0001 item 11), and ``created_at`` and ``updated_at`` both equal ``now``.
    """
    ensure_instant_in_range(now, field="now")
    if status is not TaskStatus.INBOX and status is not TaskStatus.PLANNED:
        raise DomainValidationError(
            f"a task cannot be created with status {status!s}", field="status"
        )
    return Task(
        id=task_id,
        title=title.strip(),
        status=status,
        source=source,
        created_at=now,
        updated_at=now,
        description=_normalize_description(description),
        category=category,
        priority=priority,
        estimate_minutes=estimate_minutes,
        deadline=deadline,
        scheduled=scheduled,
    )


def edit_task(
    task: Task,
    *,
    now: datetime,
    title: str | Unset = UNSET,
    description: str | Unset | None = UNSET,
    category: Category | Unset | None = UNSET,
    priority: Priority | Unset | None = UNSET,
    estimate_minutes: int | Unset | None = UNSET,
    deadline: Deadline | Unset | None = UNSET,
    scheduled: TimeInterval | Unset | None = UNSET,
) -> Task:
    """Return a new task with only the given fields changed (ADR 0001 items 12 and 16).

    ``UNSET`` leaves a field unchanged and ``None`` clears an optional field.
    The title is stripped when given. The id, status, source, created_at, and
    the lifecycle timestamps never change here; ``updated_at`` becomes ``now``.
    Editing is not restricted by status (ADR 0001 item 16), and editing the
    deadline, the schedule, or the estimate never changes the other two
    (ADR 0001 item 12). The ``now`` check compares UTC instants (ADR 0001
    item 19).
    """
    ensure_instant_in_range(now, field="now")
    if as_instant(now) < as_instant(task.updated_at):
        raise DomainValidationError("now must not be before the task updated_at", field="now")

    return Task(
        id=task.id,
        title=task.title if isinstance(title, Unset) else title.strip(),
        status=task.status,
        source=task.source,
        created_at=task.created_at,
        updated_at=now,
        description=(
            task.description
            if isinstance(description, Unset)
            else _normalize_description(description)
        ),
        category=task.category if isinstance(category, Unset) else category,
        priority=task.priority if isinstance(priority, Unset) else priority,
        estimate_minutes=(
            task.estimate_minutes if isinstance(estimate_minutes, Unset) else estimate_minutes
        ),
        deadline=task.deadline if isinstance(deadline, Unset) else deadline,
        scheduled=task.scheduled if isinstance(scheduled, Unset) else scheduled,
        completed_at=task.completed_at,
        canceled_at=task.canceled_at,
        cancellation_reason=task.cancellation_reason,
    )
