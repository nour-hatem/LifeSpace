"""Add the M2 task, history, settings, and idempotency tables.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-18 10:00:00.000000

The schema is ADR 0002 items 3 to 8, 14, and 19. Every constraint and index is
named explicitly so the models and the database agree, and ``alembic check``
reports no drift.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATUSES = "'inbox', 'planned', 'in_progress', 'completed', 'canceled'"
CATEGORIES = "'work', 'education', 'learning', 'personal', 'projects'"
PRIORITIES = "'critical', 'high', 'medium', 'low'"


def upgrade() -> None:
    """Create the M2 tables, their constraints and indexes, and the settings row."""
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("priority", sa.Text(), nullable=True),
        sa.Column("estimate_minutes", sa.Integer(), nullable=True),
        sa.Column("deadline_date", sa.Date(), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
        sa.CheckConstraint(f"status in ({STATUSES})", name=op.f("ck_tasks_status_valid")),
        sa.CheckConstraint("source in ('manual', 'ai')", name=op.f("ck_tasks_source_valid")),
        sa.CheckConstraint(
            f"category is null or category in ({CATEGORIES})",
            name=op.f("ck_tasks_category_valid"),
        ),
        sa.CheckConstraint(
            f"priority is null or priority in ({PRIORITIES})",
            name=op.f("ck_tasks_priority_valid"),
        ),
        sa.CheckConstraint(
            "estimate_minutes is null or estimate_minutes > 0",
            name=op.f("ck_tasks_estimate_positive"),
        ),
        sa.CheckConstraint(
            "deadline_date is null or deadline_at is null",
            name=op.f("ck_tasks_deadline_exclusive"),
        ),
        sa.CheckConstraint(
            "(scheduled_start is null) = (scheduled_end is null)",
            name=op.f("ck_tasks_scheduled_complete"),
        ),
        sa.CheckConstraint(
            "scheduled_start is null or scheduled_end > scheduled_start",
            name=op.f("ck_tasks_scheduled_order"),
        ),
        sa.CheckConstraint(
            "(status = 'completed') = (completed_at is not null)",
            name=op.f("ck_tasks_completed_matches_status"),
        ),
        sa.CheckConstraint(
            "(status = 'canceled') = (canceled_at is not null)",
            name=op.f("ck_tasks_canceled_matches_status"),
        ),
        sa.CheckConstraint(
            "cancellation_reason is null or status = 'canceled'",
            name=op.f("ck_tasks_reason_only_when_canceled"),
        ),
        sa.CheckConstraint("version >= 1", name=op.f("ck_tasks_version_positive")),
        sa.CheckConstraint(
            "updated_at >= created_at",
            name=op.f("ck_tasks_updated_not_before_created"),
        ),
        sa.CheckConstraint("length(btrim(title)) > 0", name=op.f("ck_tasks_title_not_blank")),
    )
    op.create_index(
        "ix_tasks_created_at_id",
        "tasks",
        [sa.text("created_at DESC"), sa.text("id DESC")],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_tasks_status",
        "tasks",
        ["status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "task_status_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=False),
        sa.Column("to_status", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("discarded_schedule_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discarded_schedule_end", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_status_events")),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name=op.f("fk_task_status_events_task_id_tasks"),
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            f"from_status in ({STATUSES})",
            name=op.f("ck_task_status_events_from_status_valid"),
        ),
        sa.CheckConstraint(
            f"to_status in ({STATUSES})",
            name=op.f("ck_task_status_events_to_status_valid"),
        ),
        sa.CheckConstraint(
            "(discarded_schedule_start is null) = (discarded_schedule_end is null)",
            name=op.f("ck_task_status_events_discarded_complete"),
        ),
        sa.CheckConstraint(
            "discarded_schedule_start is null or discarded_schedule_end > discarded_schedule_start",
            name=op.f("ck_task_status_events_discarded_order"),
        ),
    )
    op.create_index(
        "ix_task_status_events_task_occurred",
        "task_status_events",
        ["task_id", sa.text("occurred_at DESC"), sa.text("id DESC")],
    )

    op.create_table(
        "app_settings",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False, server_default=sa.text("'UTC'")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_app_settings")),
        sa.CheckConstraint("id = 1", name=op.f("ck_app_settings_single_row")),
        sa.CheckConstraint(
            "length(btrim(timezone)) > 0",
            name=op.f("ck_app_settings_timezone_not_blank"),
        ),
    )
    op.execute(
        sa.text("insert into app_settings (id, timezone, updated_at) values (1, 'UTC', now())")
    )

    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("request_fingerprint", sa.Text(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_idempotency_keys")),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name=op.f("fk_idempotency_keys_task_id_tasks"),
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "length(key) between 1 and 200",
            name=op.f("ck_idempotency_keys_key_length"),
        ),
    )


def downgrade() -> None:
    """Drop the M2 schema in reverse dependency order."""
    op.drop_index("ix_task_status_events_task_occurred", table_name="task_status_events")
    op.drop_table("idempotency_keys")
    op.drop_table("app_settings")
    op.drop_table("task_status_events")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_created_at_id", table_name="tasks")
    op.drop_table("tasks")
