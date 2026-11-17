"""Property tests for the domain to row mapping (ADR 0002 items 3, 6, and 19)."""

from __future__ import annotations

from dataclasses import fields
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from hypothesis import given
from hypothesis import strategies as st

from lifespace.domain.deadline import DateDeadline, DateTimeDeadline
from lifespace.domain.lifecycle import StatusEvent, transition_task
from lifespace.domain.task import Task, TaskStatus, create_task, edit_task
from lifespace.domain.time import TimeInterval, as_instant
from lifespace.infrastructure.mapping import (
    event_to_values,
    row_to_stored_event,
    row_to_stored_task,
    task_to_values,
)
from lifespace.infrastructure.models import StatusEventRow, TaskRow
from tests.unit.domain.strategies import intervals, utc_instants, valid_tasks


def _round_trip_task(
    task: Task,
    *,
    version: int = 1,
    deleted_at: datetime | None = None,
) -> Task:
    """Map a task to row values and back, returning the rebuilt domain task."""
    values = task_to_values(task, version=version, deleted_at=deleted_at)
    stored = row_to_stored_task(TaskRow(**values))
    assert stored.version == version
    return stored.task


def _assert_same_task(actual: Task, expected: Task) -> None:
    """Compare every task field, comparing datetimes as UTC instants (ADR 0001 item 19)."""
    for field in fields(Task):
        left = getattr(actual, field.name)
        right = getattr(expected, field.name)
        if isinstance(right, datetime):
            assert as_instant(left) == as_instant(right), field.name
        else:
            assert left == right, field.name


@given(task=valid_tasks(), version=st.integers(min_value=1, max_value=1_000_000))
def test_a_created_task_round_trips(task: Task, version: int) -> None:
    """A task created through the domain survives row values unchanged (ADR 0002 item 3)."""
    _assert_same_task(_round_trip_task(task, version=version), task)


@given(task=valid_tasks())
def test_tasks_reached_through_transitions_round_trip(task: Task) -> None:
    """Started, completed, canceled, and reopened tasks keep every field (ADR 0002 item 3)."""
    now = task.updated_at + timedelta(minutes=1)
    started = transition_task(task, TaskStatus.IN_PROGRESS, now=now)
    completed = transition_task(started.task, TaskStatus.COMPLETED, now=now + timedelta(minutes=1))
    canceled = transition_task(task, TaskStatus.CANCELED, now=now, reason="no longer needed")
    reopened = transition_task(completed.task, TaskStatus.PLANNED, now=now + timedelta(minutes=2))

    for reached in (started.task, completed.task, canceled.task, reopened.task):
        _assert_same_task(_round_trip_task(reached), reached)


def test_a_reopened_task_can_round_trip_without_a_schedule() -> None:
    """Reopening after the schedule ended drops it in the row values (ADR 0001 item 8)."""
    task = _fixed_task()
    assert task.scheduled is not None
    later = task.scheduled.end + timedelta(minutes=1)
    completed = transition_task(task, TaskStatus.COMPLETED, now=later)
    reopened = transition_task(completed.task, TaskStatus.PLANNED, now=later + timedelta(minutes=1))

    rebuilt = _round_trip_task(reopened.task)

    assert rebuilt.scheduled is None
    assert reopened.event.discarded_schedule is not None


def test_deleted_at_is_written_as_a_utc_instant() -> None:
    """The soft delete marker is normalized with ``as_instant`` (ADR 0001 item 19)."""
    task = _fixed_task()
    deleted_at = task.updated_at + timedelta(hours=1)

    values = task_to_values(task, version=2, deleted_at=deleted_at)

    assert values["deleted_at"] == as_instant(deleted_at)
    assert values["version"] == 2


@given(task=valid_tasks())
def test_the_deadline_columns_are_exclusive(task: Task) -> None:
    """A date deadline fills only its date column and an instant only its instant column."""
    values = task_to_values(task, version=1)

    assert not (values["deadline_date"] is not None and values["deadline_at"] is not None)
    if isinstance(task.deadline, DateDeadline):
        assert values["deadline_date"] == task.deadline.day
        assert values["deadline_at"] is None
    elif isinstance(task.deadline, DateTimeDeadline):
        assert values["deadline_date"] is None
        assert values["deadline_at"] == as_instant(task.deadline.at)
    else:
        assert values["deadline_date"] is None
        assert values["deadline_at"] is None


@given(task=valid_tasks(), schedule=intervals())
def test_a_schedule_round_trips_in_its_two_columns(
    task: Task,
    schedule: TimeInterval,
) -> None:
    """A schedule fills both columns and comes back as the same interval (ADR 0001 item 13)."""
    edited = edit_task(task, now=task.updated_at, scheduled=schedule)
    values = task_to_values(edited, version=1)

    assert edited.scheduled is not None
    assert values["scheduled_start"] == as_instant(edited.scheduled.start)
    assert values["scheduled_end"] == as_instant(edited.scheduled.end)
    rebuilt = _round_trip_task(edited)
    assert rebuilt.scheduled == edited.scheduled


@given(
    event_id=st.uuids(),
    task_id=st.uuids(),
    from_status=st.sampled_from(TaskStatus),
    to_status=st.sampled_from(TaskStatus),
    occurred_at=utc_instants,
    reason=st.none() | st.text(),
    discarded=st.none() | intervals(),
)
def test_status_events_round_trip(
    event_id: UUID,
    task_id: UUID,
    from_status: TaskStatus,
    to_status: TaskStatus,
    occurred_at: datetime,
    reason: str | None,
    discarded: TimeInterval | None,
) -> None:
    """An event with or without a discarded schedule round trips (ADR 0002 item 6)."""
    event = StatusEvent(
        task_id=task_id,
        from_status=from_status,
        to_status=to_status,
        occurred_at=occurred_at,
        reason=reason,
        discarded_schedule=discarded,
    )

    stored = row_to_stored_event(StatusEventRow(**event_to_values(event_id, event)))

    assert stored.id == event_id
    assert stored.event.task_id == task_id
    assert stored.event.from_status is from_status
    assert stored.event.to_status is to_status
    assert as_instant(stored.event.occurred_at) == as_instant(occurred_at)
    assert stored.event.reason == reason
    assert stored.event.discarded_schedule == event.discarded_schedule


def _fixed_task() -> Task:
    """Return a planned task with a known past deadline and schedule."""
    return create_task(
        task_id=UUID(int=7),
        title="A task",
        now=datetime(2026, 1, 1, tzinfo=UTC),
        deadline=DateDeadline(day=date(2026, 2, 1)),
        scheduled=TimeInterval(
            start=datetime(2026, 1, 2, 9, tzinfo=UTC),
            end=datetime(2026, 1, 2, 10, tzinfo=UTC),
        ),
    )
