"""Task lifecycle transitions and status events (ADR 0001 items 5 to 8)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from types import MappingProxyType
from uuid import UUID

from lifespace.domain.errors import DomainValidationError, InvalidTransitionError
from lifespace.domain.task import Task, TaskStatus
from lifespace.domain.time import TimeInterval, ensure_aware

ALLOWED_TRANSITIONS: Mapping[TaskStatus, frozenset[TaskStatus]] = MappingProxyType(
    {
        TaskStatus.INBOX: frozenset(
            {TaskStatus.PLANNED, TaskStatus.IN_PROGRESS, TaskStatus.CANCELED}
        ),
        TaskStatus.PLANNED: frozenset(
            {TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.CANCELED}
        ),
        TaskStatus.IN_PROGRESS: frozenset(
            {TaskStatus.PLANNED, TaskStatus.COMPLETED, TaskStatus.CANCELED}
        ),
        TaskStatus.COMPLETED: frozenset({TaskStatus.PLANNED}),
        TaskStatus.CANCELED: frozenset({TaskStatus.PLANNED}),
    }
)


@dataclass(frozen=True, slots=True)
class StatusEvent:
    """A recorded lifecycle change (BUSINESS_RULES 4.2, ADR 0001 items 6 to 8)."""

    task_id: UUID
    from_status: TaskStatus
    to_status: TaskStatus
    occurred_at: datetime
    reason: str | None = None
    discarded_schedule: TimeInterval | None = None

    def __post_init__(self) -> None:
        """Reject a naive event instant (ADR 0001 item 14)."""
        ensure_aware(self.occurred_at, field="occurred_at")


@dataclass(frozen=True, slots=True)
class TransitionResult:
    """The new task snapshot paired with the event that records the change (BUSINESS_RULES 4.2)."""

    task: Task
    event: StatusEvent


def _normalized_reason(reason: str | None) -> str | None:
    """Strip a reason and return ``None`` when nothing remains."""
    if reason is None:
        return None
    return reason.strip() or None


def transition_task(
    task: Task,
    to_status: TaskStatus,
    *,
    now: datetime,
    reason: str | None = None,
) -> TransitionResult:
    """Return a new task snapshot and its status event (ADR 0001 items 5 to 8).

    Only transitions in ``ALLOWED_TRANSITIONS`` are allowed, including no
    transition to the same status (BUSINESS_RULES 4.2, ADR 0001 items 5 and 6).
    Completing or canceling sets the agreeing timestamp and keeps the deadline,
    the schedule, and the estimate (ADR 0001 item 7). Reopening a completed or
    canceled task clears the lifecycle timestamps and drops a schedule that has
    already ended (ADR 0001 item 8). The input task is never mutated.
    """
    ensure_aware(now, field="now")
    if now < task.updated_at:
        raise DomainValidationError("now must not be before the task updated_at", field="now")

    allowed = ALLOWED_TRANSITIONS[task.status]
    if to_status not in allowed:
        raise InvalidTransitionError(
            task.status.value,
            to_status.value,
            allowed=tuple(sorted(status.value for status in allowed)),
        )

    normalized_reason = _normalized_reason(reason)
    completed_at = task.completed_at
    canceled_at = task.canceled_at
    cancellation_reason = task.cancellation_reason
    scheduled = task.scheduled
    discarded_schedule: TimeInterval | None = None

    if to_status is TaskStatus.COMPLETED:
        completed_at = now
    elif to_status is TaskStatus.CANCELED:
        canceled_at = now
        cancellation_reason = normalized_reason
    elif task.status is TaskStatus.COMPLETED or task.status is TaskStatus.CANCELED:
        completed_at = None
        canceled_at = None
        cancellation_reason = None
        if scheduled is not None and scheduled.end <= now:
            discarded_schedule = scheduled
            scheduled = None

    new_task = replace(
        task,
        status=to_status,
        updated_at=now,
        completed_at=completed_at,
        canceled_at=canceled_at,
        cancellation_reason=cancellation_reason,
        scheduled=scheduled,
    )
    event = StatusEvent(
        task_id=task.id,
        from_status=task.status,
        to_status=to_status,
        occurred_at=now,
        reason=normalized_reason,
        discarded_schedule=discarded_schedule,
    )
    return TransitionResult(task=new_task, event=event)
