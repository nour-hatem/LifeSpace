"""SQLAlchemy models for the M2 tables (ADR 0002 items 3 to 8 and 19).

The models are internal to ``lifespace.infrastructure`` and never leave it. The
shared metadata carries the project naming convention, so every constraint and
index has a stable name.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from lifespace.infrastructure.db import metadata


class Base(DeclarativeBase):
    """Declarative base bound to the shared metadata (ADR 0002 item 19)."""

    metadata = metadata


class TaskRow(Base):
    """A persisted task with its version and soft delete marker (ADR 0002 items 3 to 7)."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "status in ('inbox', 'planned', 'in_progress', 'completed', 'canceled')",
            name="status_valid",
        ),
        CheckConstraint("source in ('manual', 'ai')", name="source_valid"),
        CheckConstraint(
            "category is null or category in "
            "('work', 'education', 'learning', 'personal', 'projects')",
            name="category_valid",
        ),
        CheckConstraint(
            "priority is null or priority in ('critical', 'high', 'medium', 'low')",
            name="priority_valid",
        ),
        CheckConstraint(
            "estimate_minutes is null or estimate_minutes > 0",
            name="estimate_positive",
        ),
        CheckConstraint(
            "deadline_date is null or deadline_at is null",
            name="deadline_exclusive",
        ),
        CheckConstraint(
            "(scheduled_start is null) = (scheduled_end is null)",
            name="scheduled_complete",
        ),
        CheckConstraint(
            "scheduled_start is null or scheduled_end > scheduled_start",
            name="scheduled_order",
        ),
        CheckConstraint(
            "(status = 'completed') = (completed_at is not null)",
            name="completed_matches_status",
        ),
        CheckConstraint(
            "(status = 'canceled') = (canceled_at is not null)",
            name="canceled_matches_status",
        ),
        CheckConstraint(
            "cancellation_reason is null or status = 'canceled'",
            name="reason_only_when_canceled",
        ),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint("updated_at >= created_at", name="updated_not_before_created"),
        CheckConstraint("length(btrim(title)) > 0", name="title_not_blank"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str | None] = mapped_column(Text)
    estimate_minutes: Mapped[int | None] = mapped_column(Integer)
    deadline_date: Mapped[date | None] = mapped_column(Date)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scheduled_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scheduled_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StatusEventRow(Base):
    """An append-only lifecycle event (ADR 0002 item 6)."""

    __tablename__ = "task_status_events"
    __table_args__ = (
        CheckConstraint(
            "from_status in ('inbox', 'planned', 'in_progress', 'completed', 'canceled')",
            name="from_status_valid",
        ),
        CheckConstraint(
            "to_status in ('inbox', 'planned', 'in_progress', 'completed', 'canceled')",
            name="to_status_valid",
        ),
        CheckConstraint(
            "(discarded_schedule_start is null) = (discarded_schedule_end is null)",
            name="discarded_complete",
        ),
        CheckConstraint(
            "discarded_schedule_start is null "
            r"or discarded_schedule_end > discarded_schedule_start",
            name="discarded_order",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="RESTRICT"),
        nullable=False,
    )
    from_status: Mapped[str] = mapped_column(Text, nullable=False)
    to_status: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    discarded_schedule_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    discarded_schedule_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AppSettingsRow(Base):
    """The single settings row holding the user's IANA time zone (ADR 0002 item 8)."""

    __tablename__ = "app_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_row"),
        CheckConstraint("length(btrim(timezone)) > 0", name="timezone_not_blank"),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    timezone: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="UTC",
        server_default=text("'UTC'"),
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IdempotencyKeyRow(Base):
    """A stored idempotency key bound to the task it produced (ADR 0002 item 14)."""

    __tablename__ = "idempotency_keys"
    __table_args__ = (CheckConstraint("length(key) between 1 and 200", name="key_length"),)

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    request_fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index(
    "ix_tasks_created_at_id",
    TaskRow.created_at.desc(),
    TaskRow.id.desc(),
    postgresql_where=TaskRow.deleted_at.is_(None),
)
Index(
    "ix_tasks_status",
    TaskRow.status,
    postgresql_where=TaskRow.deleted_at.is_(None),
)
Index(
    "ix_task_status_events_task_occurred",
    StatusEventRow.task_id,
    StatusEventRow.occurred_at.desc(),
    StatusEventRow.id.desc(),
)
