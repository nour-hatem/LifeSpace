"""Integration tests for the M2 schema constraints and indexes (ADR 0002 items 3 to 8, 14, 19).

The schema is created by running Alembic in a subprocess: Alembic's env.py calls
``asyncio.run``, which cannot run inside a pytest-asyncio event loop.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from lifespace.infrastructure.db import create_engine
from tests.integration.conftest import require_test_database_url_sync, run_alembic

NOW = datetime(2026, 1, 1, tzinfo=UTC)
TASK_ID = UUID("00000000-0000-0000-0000-000000000001")
EVENT_ID = UUID("00000000-0000-0000-0000-000000000002")

INSERT_TASK = """
insert into tasks (
    id, title, description, status, source, category, priority,
    estimate_minutes, deadline_date, deadline_at, scheduled_start,
    scheduled_end, completed_at, canceled_at, cancellation_reason,
    created_at, updated_at, version, deleted_at
) values (
    :id, :title, :description, :status, :source, :category, :priority,
    :estimate_minutes, :deadline_date, :deadline_at, :scheduled_start,
    :scheduled_end, :completed_at, :canceled_at, :cancellation_reason,
    :created_at, :updated_at, :version, :deleted_at
)
"""

INSERT_EVENT = """
insert into task_status_events (
    id, task_id, from_status, to_status, occurred_at, reason,
    discarded_schedule_start, discarded_schedule_end
) values (
    :id, :task_id, :from_status, :to_status, :occurred_at, :reason,
    :discarded_schedule_start, :discarded_schedule_end
)
"""

INSERT_IDEMPOTENCY = """
insert into idempotency_keys (key, request_fingerprint, task_id, created_at)
values (:key, :request_fingerprint, :task_id, :created_at)
"""

INSERT_SETTINGS = """
insert into app_settings (id, timezone, updated_at)
values (:id, :timezone, :updated_at)
"""

TASK_DEFAULTS: dict[str, Any] = {
    "id": TASK_ID,
    "title": "Task",
    "description": None,
    "status": "planned",
    "source": "manual",
    "category": None,
    "priority": None,
    "estimate_minutes": None,
    "deadline_date": None,
    "deadline_at": None,
    "scheduled_start": None,
    "scheduled_end": None,
    "completed_at": None,
    "canceled_at": None,
    "cancellation_reason": None,
    "created_at": NOW,
    "updated_at": NOW,
    "version": 1,
    "deleted_at": None,
}

EVENT_DEFAULTS: dict[str, Any] = {
    "id": EVENT_ID,
    "task_id": TASK_ID,
    "from_status": "planned",
    "to_status": "in_progress",
    "occurred_at": NOW,
    "reason": None,
    "discarded_schedule_start": None,
    "discarded_schedule_end": None,
}

IDEMPOTENCY_DEFAULTS: dict[str, Any] = {
    "key": "key-1",
    "request_fingerprint": "fingerprint",
    "task_id": TASK_ID,
    "created_at": NOW,
}

SETTINGS_DEFAULTS: dict[str, Any] = {
    "id": 1,
    "timezone": "UTC",
    "updated_at": NOW,
}


def _values(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Merge a constraint violation into a valid row."""
    return defaults | overrides


async def _execute(url: str, statements: list[tuple[str, dict[str, Any]]]) -> None:
    """Run statements in one committed transaction."""
    engine = create_engine(url)
    try:
        async with engine.begin() as connection:
            for statement, parameters in statements:
                await connection.execute(text(statement), parameters)
    finally:
        await engine.dispose()


def _run(url: str, statements: list[tuple[str, dict[str, Any]]]) -> None:
    """Run statements synchronously for a synchronous test."""
    asyncio.run(_execute(url, statements))


def _assert_rejected(
    url: str,
    statements: list[tuple[str, dict[str, Any]]],
    constraint: str,
) -> None:
    """Assert that the last statement fails with the named constraint."""

    async def run() -> None:
        engine = create_engine(url)
        try:
            with pytest.raises(IntegrityError) as error:
                async with engine.begin() as connection:
                    for statement, parameters in statements:
                        await connection.execute(text(statement), parameters)
            assert constraint in str(error.value), str(error.value)
        finally:
            await engine.dispose()

    asyncio.run(run())


def _read(url: str, statement: str) -> list[Any]:
    """Return the rows of one query."""

    async def run() -> list[Any]:
        engine = create_engine(url)
        try:
            async with engine.connect() as connection:
                result = await connection.execute(text(statement))
                return list(result)
        finally:
            await engine.dispose()

    return asyncio.run(run())


def _reset(url: str) -> None:
    """Remove test rows and restore the single settings row."""
    _run(
        url,
        [
            (
                "truncate table tasks, task_status_events, idempotency_keys cascade",
                {},
            ),
            ("truncate table app_settings", {}),
            (INSERT_SETTINGS, SETTINGS_DEFAULTS),
        ],
    )


@pytest.fixture(scope="module")
def database_url() -> str:
    """Upgrade the test database to head in a subprocess (ADR 0002 item 19)."""
    url = require_test_database_url_sync()
    result = run_alembic(url, "upgrade", "head")
    assert result.returncode == 0, result.stderr
    return url


@pytest.fixture(autouse=True)
def clean_schema(database_url: str) -> Iterator[None]:
    """Start and end every test from an empty M2 schema."""
    _reset(database_url)
    yield
    _reset(database_url)


def test_upgrade_creates_the_single_settings_row(database_url: str) -> None:
    """The migration inserts one UTC settings row (ADR 0002 item 8)."""
    rows = _read(database_url, "select id, timezone from app_settings")

    assert [(row[0], row[1]) for row in rows] == [(1, "UTC")]


def test_a_valid_task_row_inserts(database_url: str) -> None:
    """A row satisfying every task constraint is accepted (ADR 0002 item 3)."""
    _run(
        database_url,
        [
            (
                INSERT_TASK,
                _values(
                    TASK_DEFAULTS,
                    {
                        "status": "completed",
                        "completed_at": NOW,
                        "deadline_date": date(2026, 2, 1),
                        "scheduled_start": NOW,
                        "scheduled_end": NOW + timedelta(hours=1),
                    },
                ),
            )
        ],
    )

    rows = _read(database_url, "select status, version from tasks")
    assert [(row[0], row[1]) for row in rows] == [("completed", 1)]


@pytest.mark.parametrize(
    ("overrides", "constraint"),
    [
        ({"status": "blocked"}, "ck_tasks_status_valid"),
        ({"source": "imported"}, "ck_tasks_source_valid"),
        ({"category": "misc"}, "ck_tasks_category_valid"),
        ({"priority": "urgent"}, "ck_tasks_priority_valid"),
        ({"estimate_minutes": 0}, "ck_tasks_estimate_positive"),
        (
            {"deadline_date": date(2026, 2, 1), "deadline_at": NOW},
            "ck_tasks_deadline_exclusive",
        ),
        ({"scheduled_start": NOW}, "ck_tasks_scheduled_complete"),
        (
            {"scheduled_start": NOW, "scheduled_end": NOW},
            "ck_tasks_scheduled_order",
        ),
        ({"status": "completed"}, "ck_tasks_completed_matches_status"),
        ({"canceled_at": NOW}, "ck_tasks_canceled_matches_status"),
        ({"cancellation_reason": "no longer needed"}, "ck_tasks_reason_only_when_canceled"),
        ({"version": 0}, "ck_tasks_version_positive"),
        (
            {"updated_at": NOW - timedelta(seconds=1)},
            "ck_tasks_updated_not_before_created",
        ),
        ({"title": "   "}, "ck_tasks_title_not_blank"),
    ],
)
def test_task_check_constraints(
    database_url: str,
    overrides: dict[str, Any],
    constraint: str,
) -> None:
    """Every named task check rejects its violating row (ADR 0002 item 3)."""
    _assert_rejected(
        database_url,
        [(INSERT_TASK, _values(TASK_DEFAULTS, overrides))],
        constraint,
    )


@pytest.mark.parametrize(
    ("overrides", "constraint"),
    [
        ({"from_status": "bogus"}, "ck_task_status_events_from_status_valid"),
        ({"to_status": "bogus"}, "ck_task_status_events_to_status_valid"),
        (
            {"discarded_schedule_start": NOW},
            "ck_task_status_events_discarded_complete",
        ),
        (
            {"discarded_schedule_start": NOW, "discarded_schedule_end": NOW},
            "ck_task_status_events_discarded_order",
        ),
    ],
)
def test_event_check_constraints(
    database_url: str,
    overrides: dict[str, Any],
    constraint: str,
) -> None:
    """Every named event check rejects its violating row (ADR 0002 item 6)."""
    _assert_rejected(
        database_url,
        [
            (INSERT_TASK, TASK_DEFAULTS),
            (INSERT_EVENT, _values(EVENT_DEFAULTS, overrides)),
        ],
        constraint,
    )


def test_a_valid_event_row_inserts(database_url: str) -> None:
    """A status event for an existing task is accepted (ADR 0002 item 6)."""
    _run(
        database_url,
        [
            (INSERT_TASK, TASK_DEFAULTS),
            (
                INSERT_EVENT,
                _values(EVENT_DEFAULTS, {"reason": "started"}),
            ),
        ],
    )

    rows = _read(database_url, "select from_status, to_status from task_status_events")
    assert [(row[0], row[1]) for row in rows] == [("planned", "in_progress")]


def test_an_event_for_a_missing_task_is_rejected(database_url: str) -> None:
    """The event foreign key requires an existing task (ADR 0002 item 6)."""
    _assert_rejected(
        database_url,
        [(INSERT_EVENT, _values(EVENT_DEFAULTS, {"task_id": UUID(int=99)}))],
        "fk_task_status_events_task_id_tasks",
    )


def test_deleting_a_task_with_events_is_rejected(database_url: str) -> None:
    """Events prevent a hard delete of their task (ADR 0002 item 6)."""
    _run(
        database_url,
        [
            (INSERT_TASK, TASK_DEFAULTS),
            (INSERT_EVENT, EVENT_DEFAULTS),
        ],
    )

    _assert_rejected(
        database_url,
        [("delete from tasks where id = :task_id", {"task_id": TASK_ID})],
        "fk_task_status_events_task_id_tasks",
    )


def test_an_idempotency_key_longer_than_200_characters_is_rejected(database_url: str) -> None:
    """The key length is bounded (ADR 0002 item 14)."""
    _assert_rejected(
        database_url,
        [
            (INSERT_TASK, TASK_DEFAULTS),
            (INSERT_IDEMPOTENCY, _values(IDEMPOTENCY_DEFAULTS, {"key": "x" * 201})),
        ],
        "ck_idempotency_keys_key_length",
    )


def test_an_empty_idempotency_key_is_rejected(database_url: str) -> None:
    """An idempotency key cannot be empty (ADR 0002 item 14)."""
    _assert_rejected(
        database_url,
        [
            (INSERT_TASK, TASK_DEFAULTS),
            (INSERT_IDEMPOTENCY, _values(IDEMPOTENCY_DEFAULTS, {"key": ""})),
        ],
        "ck_idempotency_keys_key_length",
    )


def test_an_idempotency_key_for_a_missing_task_is_rejected(database_url: str) -> None:
    """An idempotency key must reference an existing task (ADR 0002 item 14)."""
    _assert_rejected(
        database_url,
        [
            (INSERT_IDEMPOTENCY, _values(IDEMPOTENCY_DEFAULTS, {"task_id": UUID(int=99)})),
        ],
        "fk_idempotency_keys_task_id_tasks",
    )


def test_settings_only_accept_id_one(database_url: str) -> None:
    """The settings table holds exactly one row with id 1 (ADR 0002 item 8)."""
    _assert_rejected(
        database_url,
        [(INSERT_SETTINGS, _values(SETTINGS_DEFAULTS, {"id": 2}))],
        "ck_app_settings_single_row",
    )
    _assert_rejected(
        database_url,
        [("update app_settings set id = 2", {})],
        "ck_app_settings_single_row",
    )


def test_settings_timezone_must_not_be_blank(database_url: str) -> None:
    """The time zone cannot be empty or whitespace (ADR 0002 item 8)."""
    _assert_rejected(
        database_url,
        [("update app_settings set timezone = '   '", {})],
        "ck_app_settings_timezone_not_blank",
    )


def test_alembic_check_reports_no_drift(database_url: str) -> None:
    """The models and revision 0002 describe the same schema (ADR 0002 item 19)."""
    result = run_alembic(database_url, "check")

    assert result.returncode == 0, result.stderr
