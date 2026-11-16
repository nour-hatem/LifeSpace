"""Tests for lifecycle transitions and status events (ADR 0001 items 5 to 8)."""

from __future__ import annotations

import contextlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lifespace.domain.deadline import DateDeadline
from lifespace.domain.errors import DomainValidationError, InvalidTransitionError
from lifespace.domain.lifecycle import (
    ALLOWED_TRANSITIONS,
    StatusEvent,
    TransitionResult,
    transition_task,
)
from lifespace.domain.task import Task, TaskStatus, create_task
from lifespace.domain.time import TimeInterval

from .strategies import valid_tasks

NOW = datetime(2026, 1, 5, 12, tzinfo=UTC)
LATER = NOW + timedelta(hours=1)
BASE_ID = UUID("00000000-0000-0000-0000-000000000003")


def _task_in(status: TaskStatus, *, scheduled: TimeInterval | None = None) -> Task:
    task = create_task(
        task_id=BASE_ID,
        title="Task",
        now=NOW,
        scheduled=scheduled,
    )
    if status is TaskStatus.INBOX or status is TaskStatus.IN_PROGRESS:
        return replace(task, status=status)
    if status is TaskStatus.COMPLETED:
        return replace(task, status=status, completed_at=NOW)
    if status is TaskStatus.CANCELED:
        return replace(task, status=status, canceled_at=NOW, cancellation_reason="Canceled")
    return task


def _scheduled_around(start: datetime, end: datetime) -> TimeInterval:
    return TimeInterval(start=start, end=end)


@pytest.mark.parametrize("from_status", list(TaskStatus))
@pytest.mark.parametrize("to_status", list(TaskStatus))
def test_transition_matrix(from_status: TaskStatus, to_status: TaskStatus) -> None:
    task = _task_in(from_status)
    if to_status in ALLOWED_TRANSITIONS[from_status]:
        result = transition_task(task, to_status, now=LATER)
        assert result.task.status is to_status
        assert result.event.from_status is from_status
        assert result.event.to_status is to_status
        return

    with pytest.raises(InvalidTransitionError) as excinfo:
        transition_task(task, to_status, now=LATER)
    message = str(excinfo.value)
    assert from_status.value in message
    assert to_status.value in message
    for allowed in ALLOWED_TRANSITIONS[from_status]:
        assert allowed.value in message


def test_inbox_to_completed_is_explicitly_rejected() -> None:
    task = _task_in(TaskStatus.INBOX)
    with pytest.raises(InvalidTransitionError) as excinfo:
        transition_task(task, TaskStatus.COMPLETED, now=LATER)
    assert excinfo.value.from_status == TaskStatus.INBOX.value
    assert excinfo.value.to_status == TaskStatus.COMPLETED.value


def test_transition_to_the_same_status_is_rejected() -> None:
    task = _task_in(TaskStatus.PLANNED)
    with pytest.raises(InvalidTransitionError) as excinfo:
        transition_task(task, TaskStatus.PLANNED, now=LATER)
    assert "planned" in str(excinfo.value)


def test_completion_sets_completed_at_and_keeps_the_deadline_schedule_and_estimate() -> None:
    deadline = DateDeadline(day=datetime(2026, 1, 8).date())
    scheduled = _scheduled_around(
        datetime(2026, 1, 6, 17, tzinfo=UTC), datetime(2026, 1, 6, 19, tzinfo=UTC)
    )
    task = create_task(
        task_id=BASE_ID,
        title="Task",
        now=NOW,
        estimate_minutes=45,
        deadline=deadline,
        scheduled=scheduled,
    )
    result = transition_task(task, TaskStatus.COMPLETED, now=LATER)
    assert result.task.status is TaskStatus.COMPLETED
    assert result.task.completed_at == LATER
    assert result.task.canceled_at is None
    assert result.task.cancellation_reason is None
    assert result.task.deadline == deadline
    assert result.task.scheduled == scheduled
    assert result.task.estimate_minutes == 45
    assert result.task.updated_at == LATER
    assert result.event == StatusEvent(
        task_id=task.id,
        from_status=TaskStatus.PLANNED,
        to_status=TaskStatus.COMPLETED,
        occurred_at=LATER,
    )


def test_cancellation_sets_canceled_at_and_strips_the_reason() -> None:
    deadline = DateDeadline(day=datetime(2026, 1, 8).date())
    scheduled = _scheduled_around(
        datetime(2026, 1, 6, 17, tzinfo=UTC), datetime(2026, 1, 6, 19, tzinfo=UTC)
    )
    task = create_task(
        task_id=BASE_ID,
        title="Task",
        now=NOW,
        estimate_minutes=45,
        deadline=deadline,
        scheduled=scheduled,
    )
    result = transition_task(task, TaskStatus.CANCELED, now=LATER, reason="  No longer needed  ")
    assert result.task.status is TaskStatus.CANCELED
    assert result.task.canceled_at == LATER
    assert result.task.cancellation_reason == "No longer needed"
    assert result.task.completed_at is None
    assert result.task.deadline == deadline
    assert result.task.scheduled == scheduled
    assert result.task.estimate_minutes == 45
    assert result.event.reason == "No longer needed"
    assert result.event.discarded_schedule is None


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_cancellation_with_an_empty_reason_stores_none(reason: str | None) -> None:
    result = transition_task(
        _task_in(TaskStatus.PLANNED), TaskStatus.CANCELED, now=LATER, reason=reason
    )
    assert result.task.cancellation_reason is None
    assert result.event.reason is None


def test_reopening_a_completed_task_clears_its_timestamps_and_keeps_the_history() -> None:
    completed_at = NOW + timedelta(hours=1)
    reopened_at = NOW + timedelta(hours=2)
    completed = transition_task(
        _task_in(TaskStatus.PLANNED), TaskStatus.COMPLETED, now=completed_at
    )
    reopened = transition_task(completed.task, TaskStatus.PLANNED, now=reopened_at)

    assert reopened.task.status is TaskStatus.PLANNED
    assert reopened.task.completed_at is None
    assert reopened.task.canceled_at is None
    assert reopened.task.cancellation_reason is None
    assert reopened.event.from_status is TaskStatus.COMPLETED
    assert reopened.event.to_status is TaskStatus.PLANNED

    assert completed.event.occurred_at == completed_at
    assert completed.event.to_status is TaskStatus.COMPLETED
    assert completed.task.completed_at == completed_at


def test_reopening_a_canceled_task_clears_timestamps_and_reason() -> None:
    canceled = transition_task(
        _task_in(TaskStatus.PLANNED),
        TaskStatus.CANCELED,
        now=NOW + timedelta(hours=1),
        reason="  Changed plans  ",
    )
    reopened = transition_task(canceled.task, TaskStatus.PLANNED, now=NOW + timedelta(hours=2))
    assert reopened.task.status is TaskStatus.PLANNED
    assert reopened.task.completed_at is None
    assert reopened.task.canceled_at is None
    assert reopened.task.cancellation_reason is None
    assert canceled.event.reason == "Changed plans"
    assert canceled.task.canceled_at == NOW + timedelta(hours=1)


def test_reopening_drops_a_schedule_that_already_ended() -> None:
    scheduled = _scheduled_around(NOW - timedelta(hours=2), NOW - timedelta(hours=1))
    completed = transition_task(
        _task_in(TaskStatus.PLANNED, scheduled=scheduled),
        TaskStatus.COMPLETED,
        now=NOW + timedelta(hours=1),
    )
    reopened = transition_task(completed.task, TaskStatus.PLANNED, now=NOW + timedelta(hours=2))
    assert reopened.task.scheduled is None
    assert reopened.event.discarded_schedule == scheduled


def test_reopening_keeps_a_schedule_that_has_not_ended() -> None:
    scheduled = _scheduled_around(NOW + timedelta(hours=1), NOW + timedelta(hours=2))
    completed = transition_task(
        _task_in(TaskStatus.PLANNED, scheduled=scheduled),
        TaskStatus.COMPLETED,
        now=NOW + timedelta(minutes=30),
    )
    reopened = transition_task(completed.task, TaskStatus.PLANNED, now=NOW + timedelta(minutes=45))
    assert reopened.task.scheduled == scheduled
    assert reopened.event.discarded_schedule is None


def test_reopening_drops_a_schedule_that_ends_exactly_at_now() -> None:
    scheduled = _scheduled_around(NOW - timedelta(hours=1), NOW + timedelta(hours=1))
    completed = transition_task(
        _task_in(TaskStatus.PLANNED, scheduled=scheduled),
        TaskStatus.COMPLETED,
        now=NOW + timedelta(minutes=30),
    )
    reopened = transition_task(completed.task, TaskStatus.PLANNED, now=scheduled.end)
    assert reopened.task.scheduled is None
    assert reopened.event.discarded_schedule == scheduled


@pytest.mark.parametrize("from_status", list(TaskStatus))
@pytest.mark.parametrize("to_status", list(TaskStatus))
def test_a_transition_never_mutates_the_input_task(
    from_status: TaskStatus, to_status: TaskStatus
) -> None:
    task = _task_in(from_status)
    snapshot = replace(task)
    with contextlib.suppress(InvalidTransitionError):
        transition_task(task, to_status, now=LATER)
    assert task == snapshot


def test_transition_rejects_a_naive_now() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        transition_task(
            _task_in(TaskStatus.PLANNED),
            TaskStatus.IN_PROGRESS,
            now=datetime(2026, 1, 5, 12),
        )
    assert excinfo.value.field == "now"


def test_transition_rejects_now_before_updated_at() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        transition_task(
            _task_in(TaskStatus.PLANNED),
            TaskStatus.IN_PROGRESS,
            now=NOW - timedelta(microseconds=1),
        )
    assert excinfo.value.field == "now"


@given(
    task=valid_tasks(),
    targets=st.lists(st.sampled_from(TaskStatus), max_size=12),
)
def test_random_transition_sequences_keep_the_task_valid(
    task: Task, targets: list[TaskStatus]
) -> None:
    current = task
    now = task.updated_at
    events: list[StatusEvent] = []

    for target in targets:
        now = now + timedelta(minutes=1)
        snapshot = replace(current)
        try:
            result: TransitionResult = transition_task(current, target, now=now, reason="step")
        except InvalidTransitionError:
            assert current == snapshot
            continue

        assert current == snapshot
        assert result.task.status is target
        assert result.task.updated_at == now
        assert result.event.task_id == current.id
        assert result.event.from_status is current.status
        assert result.event.to_status is target
        assert result.event.occurred_at == now
        assert target in ALLOWED_TRANSITIONS[current.status]
        events.append(result.event)
        current = result.task

    completed_events = sum(1 for event in events if event.to_status is TaskStatus.COMPLETED)
    canceled_events = sum(1 for event in events if event.to_status is TaskStatus.CANCELED)
    if current.status is TaskStatus.COMPLETED:
        assert completed_events >= 1
        assert current.completed_at is not None
    if current.status is TaskStatus.CANCELED:
        assert canceled_events >= 1
        assert current.canceled_at is not None
    assert completed_events <= len(events)
    assert canceled_events <= len(events)
