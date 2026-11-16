"""Tests for the task model: creation, editing, and validation.

The rules are ADR 0001 items 4, 10, 11, 12, 14, and 16.
"""

from __future__ import annotations

from dataclasses import fields, replace
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lifespace.domain.deadline import DateDeadline, DateTimeDeadline, Deadline
from lifespace.domain.errors import DomainValidationError
from lifespace.domain.task import (
    Category,
    Priority,
    Task,
    TaskSource,
    TaskStatus,
    create_task,
    edit_task,
)
from lifespace.domain.time import TimeInterval

from .strategies import deadlines, intervals, titles, valid_tasks

NOW = datetime(2026, 1, 5, 12, tzinfo=UTC)
LATER = NOW + timedelta(minutes=5)
BASE_ID = UUID("00000000-0000-0000-0000-000000000001")


def _base_task() -> Task:
    return create_task(task_id=BASE_ID, title="Base task", now=NOW)


def _changed_fields(before: Task, after: Task) -> set[str]:
    """Return the names of the fields whose values differ."""
    return {
        field.name
        for field in fields(before)
        if getattr(before, field.name) != getattr(after, field.name)
    }


def test_create_minimal_task() -> None:
    task = create_task(task_id=BASE_ID, title="Write report", now=NOW)
    assert task.id == BASE_ID
    assert task.title == "Write report"
    assert task.status is TaskStatus.PLANNED
    assert task.source is TaskSource.MANUAL
    assert task.created_at == NOW
    assert task.updated_at == NOW
    assert task.description is None
    assert task.category is None
    assert task.priority is None
    assert task.estimate_minutes is None
    assert task.deadline is None
    assert task.scheduled is None
    assert task.completed_at is None
    assert task.canceled_at is None
    assert task.cancellation_reason is None


def test_create_full_task() -> None:
    deadline = DateDeadline(day=date(2026, 1, 8))
    scheduled = TimeInterval(
        start=datetime(2026, 1, 6, 17, tzinfo=UTC),
        end=datetime(2026, 1, 6, 19, tzinfo=UTC),
    )
    task = create_task(
        task_id=BASE_ID,
        title="  Plan launch  ",
        now=NOW,
        source=TaskSource.AI,
        status=TaskStatus.INBOX,
        description="  Details  ",
        category=Category.WORK,
        priority=Priority.HIGH,
        estimate_minutes=90,
        deadline=deadline,
        scheduled=scheduled,
    )
    assert task.title == "Plan launch"
    assert task.status is TaskStatus.INBOX
    assert task.source is TaskSource.AI
    assert task.description == "Details"
    assert task.category is Category.WORK
    assert task.priority is Priority.HIGH
    assert task.estimate_minutes == 90
    assert task.deadline == deadline
    assert task.scheduled == scheduled


def test_create_accepts_inbox_and_defaults_to_planned() -> None:
    default_task = create_task(task_id=BASE_ID, title="Default", now=NOW)
    inbox_task = create_task(task_id=BASE_ID, title="Inbox", now=NOW, status=TaskStatus.INBOX)
    assert default_task.status is TaskStatus.PLANNED
    assert inbox_task.status is TaskStatus.INBOX


@pytest.mark.parametrize(
    "status", [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS, TaskStatus.CANCELED]
)
def test_create_rejects_non_initial_status(status: TaskStatus) -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        create_task(task_id=BASE_ID, title="Task", now=NOW, status=status)
    assert excinfo.value.field == "status"


@pytest.mark.parametrize("title", ["", "   ", "\t\n "])
def test_create_rejects_empty_titles(title: str) -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        create_task(task_id=BASE_ID, title=title, now=NOW)
    assert excinfo.value.field == "title"


def test_create_trims_title_edges_and_preserves_inner_text() -> None:
    task = create_task(task_id=BASE_ID, title="  Write  The   Report  ", now=NOW)
    assert task.title == "Write  The   Report"


def test_create_preserves_arabic_title() -> None:
    task = create_task(task_id=BASE_ID, title="  اكتب تقرير المشروع  ", now=NOW)
    assert task.title == "اكتب تقرير المشروع"


@given(title=titles)
def test_create_strips_any_generated_title(title: str) -> None:
    task = create_task(task_id=uuid4(), title=title, now=NOW)
    assert task.title == title.strip()
    assert task.title


@pytest.mark.parametrize("estimate", [0, -5, True])
def test_create_rejects_invalid_estimates(estimate: int) -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        create_task(task_id=BASE_ID, title="Task", now=NOW, estimate_minutes=estimate)
    assert excinfo.value.field == "estimate_minutes"


def test_missing_estimate_is_never_replaced_by_a_default() -> None:
    task = create_task(task_id=BASE_ID, title="Task", now=NOW)
    assert task.estimate_minutes is None


def test_naive_now_is_rejected() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        create_task(task_id=BASE_ID, title="Task", now=datetime(2026, 1, 5, 12))
    assert excinfo.value.field == "now"


def test_naive_created_at_is_rejected() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        replace(_base_task(), created_at=datetime(2026, 1, 5, 12))
    assert excinfo.value.field == "created_at"


def test_naive_updated_at_is_rejected() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        replace(_base_task(), updated_at=datetime(2026, 1, 5, 12))
    assert excinfo.value.field == "updated_at"


def test_naive_deadline_instant_is_rejected() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        DateTimeDeadline(at=datetime(2026, 1, 8, 23, 59))
    assert excinfo.value.field == "at"


def test_naive_scheduled_interval_is_rejected() -> None:
    start = datetime(2026, 1, 6, 17)
    with pytest.raises(DomainValidationError):
        TimeInterval(start=start, end=start + timedelta(hours=2))


def test_completed_requires_completed_at() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        replace(_base_task(), status=TaskStatus.COMPLETED)
    assert excinfo.value.field == "completed_at"


def test_completed_at_is_only_allowed_when_completed() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        replace(_base_task(), completed_at=NOW)
    assert excinfo.value.field == "completed_at"


def test_canceled_requires_canceled_at() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        replace(_base_task(), status=TaskStatus.CANCELED)
    assert excinfo.value.field == "canceled_at"


def test_canceled_at_is_only_allowed_when_canceled() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        replace(_base_task(), canceled_at=NOW)
    assert excinfo.value.field == "canceled_at"


def test_cancellation_reason_is_only_allowed_when_canceled() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        replace(_base_task(), cancellation_reason="No longer needed")
    assert excinfo.value.field == "cancellation_reason"


def test_cancellation_reason_must_not_be_empty() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        replace(
            _base_task(),
            status=TaskStatus.CANCELED,
            canceled_at=NOW,
            cancellation_reason="",
        )
    assert excinfo.value.field == "cancellation_reason"


def test_cancellation_reason_must_not_be_blank() -> None:
    with pytest.raises(DomainValidationError):
        replace(
            _base_task(),
            status=TaskStatus.CANCELED,
            canceled_at=NOW,
            cancellation_reason="   ",
        )


def test_canceled_task_accepts_a_reason() -> None:
    task = replace(
        _base_task(),
        status=TaskStatus.CANCELED,
        canceled_at=NOW,
        cancellation_reason="No longer needed",
    )
    assert task.status is TaskStatus.CANCELED
    assert task.cancellation_reason == "No longer needed"


def test_updated_at_must_not_be_before_created_at() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        replace(_base_task(), updated_at=NOW - timedelta(microseconds=1))
    assert excinfo.value.field == "updated_at"


def test_direct_construction_rejects_an_untrimmed_title() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        replace(_base_task(), title="  Untrimmed  ")
    assert excinfo.value.field == "title"


def test_priority_rank_orders_most_important_first() -> None:
    assert Priority.CRITICAL.rank == 1
    assert Priority.HIGH.rank == 2
    assert Priority.MEDIUM.rank == 3
    assert Priority.LOW.rank == 4


def test_edit_returns_a_new_task_and_leaves_the_original_unchanged() -> None:
    original = create_task(task_id=BASE_ID, title="Original", now=NOW)
    edited = edit_task(original, now=LATER, title="Updated")
    assert edited is not original
    assert original.title == "Original"
    assert edited.title == "Updated"


def test_edit_strips_the_title() -> None:
    task = _base_task()
    edited = edit_task(task, now=LATER, title="  Updated title  ")
    assert edited.title == "Updated title"


def test_edit_with_only_now_changes_only_updated_at() -> None:
    original = _base_task()
    edited = edit_task(original, now=LATER)
    assert edited.updated_at == LATER
    assert _changed_fields(original, edited) == {"updated_at"}


def test_edit_with_none_clears_optional_fields() -> None:
    deadline = DateTimeDeadline(at=datetime(2026, 1, 8, 23, 59, tzinfo=UTC))
    scheduled = TimeInterval(
        start=datetime(2026, 1, 6, 17, tzinfo=UTC),
        end=datetime(2026, 1, 6, 19, tzinfo=UTC),
    )
    task = create_task(
        task_id=BASE_ID,
        title="Task",
        now=NOW,
        description="Details",
        category=Category.WORK,
        priority=Priority.HIGH,
        estimate_minutes=60,
        deadline=deadline,
        scheduled=scheduled,
    )
    edited = edit_task(
        task,
        now=LATER,
        description=None,
        category=None,
        priority=None,
        estimate_minutes=None,
        deadline=None,
        scheduled=None,
    )
    assert edited.description is None
    assert edited.category is None
    assert edited.priority is None
    assert edited.estimate_minutes is None
    assert edited.deadline is None
    assert edited.scheduled is None


def test_editing_deadline_leaves_schedule_and_estimate_untouched() -> None:
    task = create_task(
        task_id=BASE_ID,
        title="Task",
        now=NOW,
        estimate_minutes=30,
        deadline=DateDeadline(day=date(2026, 1, 8)),
        scheduled=TimeInterval(
            start=datetime(2026, 1, 6, 17, tzinfo=UTC),
            end=datetime(2026, 1, 6, 19, tzinfo=UTC),
        ),
    )
    new_deadline = DateTimeDeadline(at=datetime(2026, 1, 9, 23, 59, tzinfo=UTC))
    edited = edit_task(task, now=LATER, deadline=new_deadline)
    assert edited.deadline == new_deadline
    assert edited.scheduled == task.scheduled
    assert edited.estimate_minutes == task.estimate_minutes


def test_editing_schedule_leaves_deadline_and_estimate_untouched() -> None:
    task = create_task(
        task_id=BASE_ID,
        title="Task",
        now=NOW,
        estimate_minutes=30,
        deadline=DateDeadline(day=date(2026, 1, 8)),
        scheduled=TimeInterval(
            start=datetime(2026, 1, 6, 17, tzinfo=UTC),
            end=datetime(2026, 1, 6, 19, tzinfo=UTC),
        ),
    )
    new_scheduled = TimeInterval(
        start=datetime(2026, 1, 7, 9, tzinfo=UTC),
        end=datetime(2026, 1, 7, 11, tzinfo=UTC),
    )
    edited = edit_task(task, now=LATER, scheduled=new_scheduled)
    assert edited.scheduled == new_scheduled
    assert edited.deadline == task.deadline
    assert edited.estimate_minutes == task.estimate_minutes


def test_editing_estimate_leaves_deadline_and_schedule_untouched() -> None:
    task = create_task(
        task_id=BASE_ID,
        title="Task",
        now=NOW,
        estimate_minutes=30,
        deadline=DateDeadline(day=date(2026, 1, 8)),
        scheduled=TimeInterval(
            start=datetime(2026, 1, 6, 17, tzinfo=UTC),
            end=datetime(2026, 1, 6, 19, tzinfo=UTC),
        ),
    )
    edited = edit_task(task, now=LATER, estimate_minutes=45)
    assert edited.estimate_minutes == 45
    assert edited.deadline == task.deadline
    assert edited.scheduled == task.scheduled


@given(task=valid_tasks(), new_deadline=st.none() | deadlines)
def test_property_editing_deadline_never_changes_schedule_or_estimate(
    task: Task, new_deadline: Deadline | None
) -> None:
    edited = edit_task(task, now=task.updated_at, deadline=new_deadline)
    assert edited.deadline == new_deadline
    assert edited.scheduled == task.scheduled
    assert edited.estimate_minutes == task.estimate_minutes


@given(task=valid_tasks(), new_scheduled=st.none() | intervals())
def test_property_editing_schedule_never_changes_deadline_or_estimate(
    task: Task, new_scheduled: TimeInterval | None
) -> None:
    edited = edit_task(task, now=task.updated_at, scheduled=new_scheduled)
    assert edited.scheduled == new_scheduled
    assert edited.deadline == task.deadline
    assert edited.estimate_minutes == task.estimate_minutes


@given(
    task=valid_tasks(),
    new_estimate=st.none() | st.integers(min_value=1, max_value=10_080),
)
def test_property_editing_estimate_never_changes_deadline_or_schedule(
    task: Task, new_estimate: int | None
) -> None:
    edited = edit_task(task, now=task.updated_at, estimate_minutes=new_estimate)
    assert edited.estimate_minutes == new_estimate
    assert edited.deadline == task.deadline
    assert edited.scheduled == task.scheduled


@given(task=valid_tasks(), new_title=titles)
def test_property_editing_title_changes_only_title_and_updated_at(
    task: Task, new_title: str
) -> None:
    edited = edit_task(task, now=task.updated_at, title=new_title)
    assert edited.title == new_title.strip()
    assert _changed_fields(task, edited) <= {"title", "updated_at"}


@given(task=valid_tasks())
def test_property_editing_keeps_identity_and_lifecycle_fields(task: Task) -> None:
    edited = edit_task(
        task,
        now=task.updated_at + timedelta(minutes=1),
        title=task.title,
        description=task.description,
        category=task.category,
        priority=task.priority,
        estimate_minutes=task.estimate_minutes,
        deadline=task.deadline,
        scheduled=task.scheduled,
    )
    assert edited.id == task.id
    assert edited.status == task.status
    assert edited.source == task.source
    assert edited.created_at == task.created_at
    assert edited.completed_at == task.completed_at
    assert edited.canceled_at == task.canceled_at
    assert edited.cancellation_reason == task.cancellation_reason
    assert edited.updated_at == task.updated_at + timedelta(minutes=1)


def test_edit_rejects_an_empty_title() -> None:
    task = _base_task()
    with pytest.raises(DomainValidationError) as excinfo:
        edit_task(task, now=LATER, title="   ")
    assert excinfo.value.field == "title"
    assert task.title == "Base task"


def test_edit_rejects_an_invalid_estimate_without_a_partial_result() -> None:
    task = _base_task()
    with pytest.raises(DomainValidationError) as excinfo:
        edit_task(task, now=LATER, title="New title", estimate_minutes=0)
    assert excinfo.value.field == "estimate_minutes"
    assert task.title == "Base task"


def test_edit_rejects_now_before_updated_at() -> None:
    task = _base_task()
    with pytest.raises(DomainValidationError) as excinfo:
        edit_task(task, now=NOW - timedelta(microseconds=1), title="New")
    assert excinfo.value.field == "now"


def test_edit_rejects_a_naive_now() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        edit_task(_base_task(), now=datetime(2026, 1, 5, 12), title="New")
    assert excinfo.value.field == "now"


def test_deadline_and_schedule_coexist_and_differ() -> None:
    deadline = DateTimeDeadline(at=datetime(2026, 1, 8, 23, 59, tzinfo=UTC))
    scheduled = TimeInterval(
        start=datetime(2026, 1, 6, 17, tzinfo=UTC),
        end=datetime(2026, 1, 6, 19, tzinfo=UTC),
    )
    task = create_task(
        task_id=BASE_ID,
        title="Independent values",
        now=NOW,
        deadline=deadline,
        scheduled=scheduled,
    )
    assert task.deadline == deadline
    assert task.scheduled == scheduled
    assert task.scheduled.start.date() != deadline.at.date()
