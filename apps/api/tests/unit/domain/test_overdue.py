"""Tests for the overdue computation (BUSINESS_RULES 4.7, ADR 0001 item 9)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from lifespace.domain.deadline import DateDeadline, DateTimeDeadline, Deadline
from lifespace.domain.errors import DomainValidationError
from lifespace.domain.lifecycle import transition_task
from lifespace.domain.overdue import is_overdue
from lifespace.domain.task import Task, TaskStatus, create_task

NOW = datetime(2026, 1, 5, 12, tzinfo=UTC)
CREATED = NOW - timedelta(hours=10)
BASE_ID = UUID("00000000-0000-0000-0000-000000000009")
UTC_ZONE = ZoneInfo("UTC")
CAIRO = ZoneInfo("Africa/Cairo")


def _task(deadline: Deadline | None, status: TaskStatus = TaskStatus.PLANNED) -> Task:
    task = create_task(task_id=BASE_ID, title="Task", now=CREATED, deadline=deadline)
    if status is TaskStatus.INBOX or status is TaskStatus.IN_PROGRESS:
        return replace(task, status=status)
    if status is TaskStatus.COMPLETED:
        return replace(task, status=status, completed_at=NOW)
    if status is TaskStatus.CANCELED:
        return replace(task, status=status, canceled_at=NOW, cancellation_reason="Canceled")
    return task


def test_a_task_without_a_deadline_is_not_overdue() -> None:
    assert not is_overdue(_task(None), NOW, UTC_ZONE)


@pytest.mark.parametrize("status", [TaskStatus.INBOX, TaskStatus.PLANNED])
def test_active_tasks_past_their_deadline_are_overdue(status: TaskStatus) -> None:
    deadline = DateTimeDeadline(at=NOW - timedelta(seconds=1))
    assert is_overdue(_task(deadline, status), NOW, UTC_ZONE)


def test_an_in_progress_task_can_be_overdue() -> None:
    deadline = DateTimeDeadline(at=NOW - timedelta(hours=1))
    task = _task(deadline, TaskStatus.IN_PROGRESS)
    assert task.status is TaskStatus.IN_PROGRESS
    assert is_overdue(task, NOW, UTC_ZONE)


@pytest.mark.parametrize("status", [TaskStatus.COMPLETED, TaskStatus.CANCELED])
def test_terminal_tasks_are_never_overdue(status: TaskStatus) -> None:
    deadline = DateTimeDeadline(at=NOW - timedelta(days=1))
    assert not is_overdue(_task(deadline, status), NOW, UTC_ZONE)


def test_date_time_deadline_boundary() -> None:
    task = _task(DateTimeDeadline(at=NOW))
    assert not is_overdue(task, NOW, UTC_ZONE)
    assert is_overdue(task, NOW + timedelta(microseconds=1), UTC_ZONE)


def test_date_deadline_boundary_in_utc() -> None:
    task = _task(DateDeadline(day=date(2026, 4, 23)))
    assert not is_overdue(task, datetime(2026, 4, 23, 23, 59, 59, 999999, tzinfo=UTC), UTC_ZONE)
    assert is_overdue(task, datetime(2026, 4, 24, tzinfo=UTC), UTC_ZONE)


def test_date_deadline_boundary_in_cairo_across_spring_forward() -> None:
    task = _task(DateDeadline(day=date(2026, 4, 23)))
    assert not is_overdue(task, datetime(2026, 4, 23, 21, 59, 59, 999999, tzinfo=UTC), CAIRO)
    assert is_overdue(task, datetime(2026, 4, 23, 22, tzinfo=UTC), CAIRO)


def test_date_deadline_boundary_in_cairo_across_fall_back() -> None:
    task = _task(DateDeadline(day=date(2026, 10, 29)))
    assert not is_overdue(task, datetime(2026, 10, 29, 21, 59, 59, 999999, tzinfo=UTC), CAIRO)
    assert is_overdue(task, datetime(2026, 10, 29, 22, tzinfo=UTC), CAIRO)


def test_completing_an_overdue_task_makes_it_not_overdue() -> None:
    task = _task(DateTimeDeadline(at=NOW - timedelta(hours=1)))
    assert is_overdue(task, NOW, UTC_ZONE)
    completed = transition_task(task, TaskStatus.COMPLETED, now=NOW)
    assert not is_overdue(completed.task, NOW, UTC_ZONE)


def test_overdue_is_a_pure_function_of_its_inputs() -> None:
    task = _task(DateTimeDeadline(at=NOW))
    instant = NOW + timedelta(seconds=1)
    first = is_overdue(task, instant, UTC_ZONE)
    assert first
    for _ in range(3):
        assert is_overdue(task, instant, UTC_ZONE) is first


def test_naive_now_is_rejected() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        is_overdue(_task(None), datetime(2026, 1, 5, 12), UTC_ZONE)
    assert excinfo.value.field == "now"
