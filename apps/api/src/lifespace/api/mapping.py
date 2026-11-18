"""Mapping between API schemas and application commands and views (ADR 0002 item 10).

This module may import domain value types and enums for mapping. It never
imports infrastructure or SQLAlchemy, and it converts every output instant to
UTC so responses carry an explicit offset (ADR 0002 item 7).
"""

from __future__ import annotations

from datetime import UTC, datetime

from lifespace.api.schemas import (
    DateDeadlineSchema,
    DateTimeDeadlineSchema,
    EventOut,
    IntervalSchema,
    SettingsOut,
    TaskCreate,
    TaskOut,
    TaskPatch,
)
from lifespace.application.errors import ValidationFailedError, translate_domain_errors
from lifespace.application.models import (
    AppSettings,
    CreateTaskCommand,
    StoredStatusEvent,
    TaskChanges,
    TaskView,
)
from lifespace.domain.deadline import DateDeadline, DateTimeDeadline, Deadline
from lifespace.domain.task import UNSET, TaskSource, TaskStatus, Unset
from lifespace.domain.time import TimeInterval


def _utc(value: datetime) -> datetime:
    """Return ``value`` as a UTC instant with an offset (ADR 0002 item 7)."""
    return value.astimezone(UTC)


def _utc_or_none(value: datetime | None) -> datetime | None:
    """Return an optional instant in UTC (ADR 0002 item 7)."""
    return None if value is None else _utc(value)


def deadline_from_schema(
    schema: DateDeadlineSchema | DateTimeDeadlineSchema | None,
) -> Deadline | None:
    """Build a domain deadline from its tagged representation (ADR 0002 item 10)."""
    if schema is None:
        return None
    if isinstance(schema, DateDeadlineSchema):
        return DateDeadline(day=schema.value)
    return DateTimeDeadline(at=schema.value)


def interval_from_schema(schema: IntervalSchema | None) -> TimeInterval | None:
    """Build a domain interval, translating its validation errors (ADR 0002 item 17)."""
    if schema is None:
        return None
    with translate_domain_errors():
        return TimeInterval(start=schema.start, end=schema.end)


def deadline_to_schema(
    deadline: Deadline | None,
) -> DateDeadlineSchema | DateTimeDeadlineSchema | None:
    """Render a domain deadline as a tagged object (ADR 0002 item 10)."""
    if deadline is None:
        return None
    if isinstance(deadline, DateDeadline):
        return DateDeadlineSchema(kind="date", value=deadline.day)
    return DateTimeDeadlineSchema(kind="datetime", value=_utc(deadline.at))


def interval_to_schema(interval: TimeInterval | None) -> IntervalSchema | None:
    """Render a domain interval with UTC bounds (ADR 0002 item 7)."""
    if interval is None:
        return None
    return IntervalSchema(start=_utc(interval.start), end=_utc(interval.end))


def create_command(body: TaskCreate) -> CreateTaskCommand:
    """Build the create command; HTTP clients always create manual tasks (ADR 0002 item 9)."""
    return CreateTaskCommand(
        title=body.title,
        description=body.description,
        category=body.category,
        priority=body.priority,
        estimate_minutes=body.estimate_minutes,
        deadline=deadline_from_schema(body.deadline),
        scheduled=interval_from_schema(body.scheduled),
        status=TaskStatus(body.status),
        source=TaskSource.MANUAL,
    )


def task_changes(patch: TaskPatch) -> TaskChanges:
    """Build the edit changes from the fields the client actually sent (ADR 0002 item 10).

    An omitted field stays ``UNSET`` and an explicit JSON null clears an
    optional field. A null title is rejected because a task always needs one
    (ADR 0001 item 11).
    """
    given = patch.model_fields_set
    title: str | Unset = UNSET
    if "title" in given:
        if patch.title is None:
            raise ValidationFailedError("title must not be null", field="title")
        title = patch.title
    return TaskChanges(
        title=title,
        description=patch.description if "description" in given else UNSET,
        category=patch.category if "category" in given else UNSET,
        priority=patch.priority if "priority" in given else UNSET,
        estimate_minutes=patch.estimate_minutes if "estimate_minutes" in given else UNSET,
        deadline=deadline_from_schema(patch.deadline) if "deadline" in given else UNSET,
        scheduled=interval_from_schema(patch.scheduled) if "scheduled" in given else UNSET,
    )


def task_out(view: TaskView) -> TaskOut:
    """Render a stored task with its version and overdue flag (ADR 0002 items 4 and 8)."""
    task = view.stored.task
    return TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        source=task.source,
        category=task.category,
        priority=task.priority,
        estimate_minutes=task.estimate_minutes,
        deadline=deadline_to_schema(task.deadline),
        scheduled=interval_to_schema(task.scheduled),
        completed_at=_utc_or_none(task.completed_at),
        canceled_at=_utc_or_none(task.canceled_at),
        cancellation_reason=task.cancellation_reason,
        created_at=_utc(task.created_at),
        updated_at=_utc(task.updated_at),
        version=view.stored.version,
        is_overdue=view.is_overdue,
    )


def event_out(stored: StoredStatusEvent) -> EventOut:
    """Render a stored status event (ADR 0002 item 6)."""
    event = stored.event
    return EventOut(
        id=stored.id,
        task_id=event.task_id,
        from_status=event.from_status,
        to_status=event.to_status,
        occurred_at=_utc(event.occurred_at),
        reason=event.reason,
        discarded_schedule=interval_to_schema(event.discarded_schedule),
    )


def settings_out(settings: AppSettings) -> SettingsOut:
    """Render the stored settings (ADR 0002 item 8)."""
    return SettingsOut(timezone=settings.timezone)
