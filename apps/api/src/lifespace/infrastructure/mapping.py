"""Pure mapping between domain objects and database row values (ADR 0002 item 19).

The functions here never touch the database. They translate between the domain
types, which never see SQLAlchemy, and the column values stored by the
repositories in Part 4.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from lifespace.application.models import StoredStatusEvent, StoredTask
from lifespace.domain.deadline import DateDeadline, DateTimeDeadline, Deadline
from lifespace.domain.lifecycle import StatusEvent
from lifespace.domain.task import Category, Priority, Task, TaskSource, TaskStatus
from lifespace.domain.time import TimeInterval, as_instant
from lifespace.infrastructure.models import StatusEventRow, TaskRow


def _instant_or_none(value: datetime | None) -> datetime | None:
    """Return ``value`` as a UTC instant, or ``None`` (ADR 0001 item 19)."""
    return None if value is None else as_instant(value)


def _columns_for_deadline(
    deadline: Deadline | None,
) -> tuple[date | None, datetime | None]:
    """Return the deadline date and instant columns, never both set (ADR 0001 items 2 and 3)."""
    if isinstance(deadline, DateDeadline):
        return deadline.day, None
    if isinstance(deadline, DateTimeDeadline):
        return None, as_instant(deadline.at)
    return None, None


def _columns_for_schedule(
    scheduled: TimeInterval | None,
) -> tuple[datetime | None, datetime | None]:
    """Return the two schedule columns, both ``None`` without a schedule (ADR 0001 item 13)."""
    if scheduled is None:
        return None, None
    return as_instant(scheduled.start), as_instant(scheduled.end)


def task_to_values(
    task: Task,
    *,
    version: int,
    deleted_at: datetime | None = None,
) -> dict[str, Any]:
    """Return the ``tasks`` column values for ``task`` (ADR 0002 items 3, 5, and 7)."""
    deadline_date, deadline_at = _columns_for_deadline(task.deadline)
    scheduled_start, scheduled_end = _columns_for_schedule(task.scheduled)
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "source": task.source.value,
        "category": None if task.category is None else task.category.value,
        "priority": None if task.priority is None else task.priority.value,
        "estimate_minutes": task.estimate_minutes,
        "deadline_date": deadline_date,
        "deadline_at": deadline_at,
        "scheduled_start": scheduled_start,
        "scheduled_end": scheduled_end,
        "completed_at": _instant_or_none(task.completed_at),
        "canceled_at": _instant_or_none(task.canceled_at),
        "cancellation_reason": task.cancellation_reason,
        "created_at": as_instant(task.created_at),
        "updated_at": as_instant(task.updated_at),
        "version": version,
        "deleted_at": _instant_or_none(deleted_at),
    }


def row_to_stored_task(row: TaskRow) -> StoredTask:
    """Build a validated domain task and its version from a ``tasks`` row (ADR 0002 item 3).

    The domain constructor runs every task invariant again (ADR 0001 item 14),
    so a corrupt row fails loudly instead of entering the application layer.
    """
    deadline: Deadline | None
    if row.deadline_date is not None:
        deadline = DateDeadline(day=row.deadline_date)
    elif row.deadline_at is not None:
        deadline = DateTimeDeadline(at=row.deadline_at)
    else:
        deadline = None

    scheduled: TimeInterval | None = None
    if row.scheduled_start is not None and row.scheduled_end is not None:
        scheduled = TimeInterval(start=row.scheduled_start, end=row.scheduled_end)

    task = Task(
        id=row.id,
        title=row.title,
        status=TaskStatus(row.status),
        source=TaskSource(row.source),
        created_at=row.created_at,
        updated_at=row.updated_at,
        description=row.description,
        category=None if row.category is None else Category(row.category),
        priority=None if row.priority is None else Priority(row.priority),
        estimate_minutes=row.estimate_minutes,
        deadline=deadline,
        scheduled=scheduled,
        completed_at=row.completed_at,
        canceled_at=row.canceled_at,
        cancellation_reason=row.cancellation_reason,
    )
    return StoredTask(task=task, version=row.version)


def event_to_values(event_id: UUID, event: StatusEvent) -> dict[str, Any]:
    """Return the ``task_status_events`` column values for ``event`` (ADR 0002 item 6)."""
    discarded_start, discarded_end = _columns_for_schedule(event.discarded_schedule)
    return {
        "id": event_id,
        "task_id": event.task_id,
        "from_status": event.from_status.value,
        "to_status": event.to_status.value,
        "occurred_at": as_instant(event.occurred_at),
        "reason": event.reason,
        "discarded_schedule_start": discarded_start,
        "discarded_schedule_end": discarded_end,
    }


def row_to_stored_event(row: StatusEventRow) -> StoredStatusEvent:
    """Build an event and its identifier from a ``task_status_events`` row (ADR 0002 item 6)."""
    discarded: TimeInterval | None = None
    if row.discarded_schedule_start is not None and row.discarded_schedule_end is not None:
        discarded = TimeInterval(
            start=row.discarded_schedule_start,
            end=row.discarded_schedule_end,
        )
    event = StatusEvent(
        task_id=row.task_id,
        from_status=TaskStatus(row.from_status),
        to_status=TaskStatus(row.to_status),
        occurred_at=row.occurred_at,
        reason=row.reason,
        discarded_schedule=discarded,
    )
    return StoredStatusEvent(id=row.id, event=event)
