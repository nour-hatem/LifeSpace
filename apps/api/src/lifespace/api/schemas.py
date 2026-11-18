"""Request and response schemas for the versioned task API (ADR 0002 item 10).

Request models forbid unknown fields and use strict scalar types so that an
integer or a string is never silently coerced. Response models carry UTC
timestamps with an offset and the computed overdue flag (ADR 0002 item 8).
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictStr

from lifespace.domain.task import Category, Priority, TaskSource, TaskStatus


class _RequestModel(BaseModel):
    """Base for request bodies: unknown members are rejected (ADR 0002 item 10)."""

    model_config = ConfigDict(extra="forbid")


class DateDeadlineSchema(_RequestModel):
    """A deadline at the end of a local calendar day (ADR 0002 item 10)."""

    kind: Literal["date"]
    value: date


class DateTimeDeadlineSchema(_RequestModel):
    """A deadline at an exact aware instant (ADR 0002 item 10)."""

    kind: Literal["datetime"]
    value: AwareDatetime


DeadlineSchema = DateDeadlineSchema | DateTimeDeadlineSchema
DeadlineField = Annotated[DeadlineSchema, Field(discriminator="kind")]


class IntervalSchema(_RequestModel):
    """A half-open scheduled interval (ADR 0002 item 10)."""

    start: AwareDatetime
    end: AwareDatetime


class TaskCreate(_RequestModel):
    """The request body for creating a task (ADR 0002 items 9 and 10)."""

    title: StrictStr
    description: StrictStr | None = None
    category: Category | None = None
    priority: Priority | None = None
    estimate_minutes: Annotated[int, Field(strict=True)] | None = None
    deadline: DeadlineField | None = None
    scheduled: IntervalSchema | None = None
    status: Literal["inbox", "planned"] = "planned"


class TaskPatch(_RequestModel):
    """A partial edit; ``model_fields_set`` separates omitted from null (ADR 0002 item 10)."""

    version: Annotated[int, Field(strict=True, ge=1)]
    title: StrictStr | None = None
    description: StrictStr | None = None
    category: Category | None = None
    priority: Priority | None = None
    estimate_minutes: Annotated[int, Field(strict=True)] | None = None
    deadline: DeadlineField | None = None
    scheduled: IntervalSchema | None = None


class ActionBody(_RequestModel):
    """A lifecycle action carrying the expected version (ADR 0002 item 11)."""

    version: Annotated[int, Field(strict=True, ge=1)]


class CancelBody(_RequestModel):
    """A cancel action with an optional reason (ADR 0002 item 11)."""

    version: Annotated[int, Field(strict=True, ge=1)]
    reason: StrictStr | None = None


class SettingsBody(_RequestModel):
    """The request body for changing the user's time zone (ADR 0002 item 8)."""

    timezone: StrictStr


class TaskOut(BaseModel):
    """A task as returned by the API (ADR 0002 items 8, 10, and 11)."""

    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    source: TaskSource
    category: Category | None
    priority: Priority | None
    estimate_minutes: int | None
    deadline: DeadlineField | None
    scheduled: IntervalSchema | None
    completed_at: AwareDatetime | None
    canceled_at: AwareDatetime | None
    cancellation_reason: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int
    is_overdue: bool


class EventOut(BaseModel):
    """One recorded lifecycle change (ADR 0002 item 6)."""

    id: UUID
    task_id: UUID
    from_status: TaskStatus
    to_status: TaskStatus
    occurred_at: AwareDatetime
    reason: str | None
    discarded_schedule: IntervalSchema | None


class TaskPage(BaseModel):
    """One page of tasks (ADR 0002 item 15)."""

    items: list[TaskOut]
    next_cursor: str | None


class EventPage(BaseModel):
    """One page of status events (ADR 0002 item 15)."""

    items: list[EventOut]
    next_cursor: str | None


class SettingsOut(BaseModel):
    """The stored application settings (ADR 0002 item 8)."""

    timezone: str


class ProblemOut(BaseModel):
    """The documented shape of a problem+json error body (ADR 0002 items 12 and 13)."""

    type: str
    title: str
    status: int
    detail: str
    code: str
    result: Literal["validation_failed", "rejected", "conflict", "not_found", "failed"]
    field: str | None = None
    current_version: int | None = None
