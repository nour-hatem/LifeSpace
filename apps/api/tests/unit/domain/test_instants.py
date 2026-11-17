"""Regression tests for comparing and subtracting datetimes by UTC instant (ADR 0001 item 19).

Python compares and subtracts two aware datetimes that share the same
``tzinfo`` object by their wall-clock fields, ignoring the UTC offset and the
``fold``. These tests use one ``ZoneInfo("Africa/Cairo")`` object so every
value shares a ``tzinfo``, and assert the real UTC answer across a daylight
saving change and inside the ambiguous hour.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from hypothesis import assume, given

from lifespace.domain.deadline import DateTimeDeadline, is_deadline_passed
from lifespace.domain.errors import DomainValidationError
from lifespace.domain.lifecycle import transition_task
from lifespace.domain.overdue import is_overdue
from lifespace.domain.task import Task, TaskSource, TaskStatus, create_task, edit_task
from lifespace.domain.time import TimeInterval, as_instant

from .strategies import same_zone_instants, same_zone_intervals

CAIRO = ZoneInfo("Africa/Cairo")

# Africa/Cairo in 2026 (ADR 0001 "Verified time zone facts"):
# spring forward at 2026-04-23T22:00:00Z, fall back at 2026-10-29T21:00:00Z.
AMBIGUOUS_DEADLINE = datetime(2026, 10, 29, 23, 30, tzinfo=CAIRO, fold=0)  # 20:30Z
AMBIGUOUS_NOW_LATER = datetime(2026, 10, 29, 23, 10, tzinfo=CAIRO, fold=1)  # 21:10Z
AMBIGUOUS_NOW_EARLIER = datetime(2026, 10, 29, 23, 10, tzinfo=CAIRO, fold=0)  # 20:10Z


def _task(created_at: datetime, updated_at: datetime) -> Task:
    """Build a minimal planned task with the given timestamps."""
    return Task(
        id=UUID(int=1),
        title="Task",
        status=TaskStatus.PLANNED,
        source=TaskSource.MANUAL,
        created_at=created_at,
        updated_at=updated_at,
    )


def test_as_instant_converts_to_utc() -> None:
    """``as_instant`` returns the UTC value whatever the input offset (ADR 0001 item 19)."""
    assert as_instant(AMBIGUOUS_DEADLINE) == datetime(2026, 10, 29, 20, 30, tzinfo=UTC)
    assert as_instant(AMBIGUOUS_NOW_LATER) == datetime(2026, 10, 29, 21, 10, tzinfo=UTC)


def test_as_instant_rejects_a_naive_value() -> None:
    """A naive datetime is rejected before it can be compared (ADR 0001 items 14 and 19)."""
    with pytest.raises(DomainValidationError) as excinfo:
        as_instant(datetime(2026, 10, 29, 23, 30))
    assert excinfo.value.field == "value"


def test_duration_across_spring_forward() -> None:
    """An interval across the missing hour lasts 2 real hours, not 3 (ADR 0001 item 19)."""
    interval = TimeInterval(
        start=datetime(2026, 4, 23, 23, 0, tzinfo=CAIRO),
        end=datetime(2026, 4, 24, 2, 0, tzinfo=CAIRO),
    )
    assert interval.duration() == timedelta(hours=2)
    # The stored bounds keep the zone and wall clock the caller gave.
    assert interval.start.utcoffset() == timedelta(hours=2)
    assert interval.end.utcoffset() == timedelta(hours=3)


def test_duration_across_fall_back() -> None:
    """An interval across the repeated hour lasts 4 real hours, not 3 (ADR 0001 item 19)."""
    interval = TimeInterval(
        start=datetime(2026, 10, 29, 22, 0, tzinfo=CAIRO),
        end=datetime(2026, 10, 30, 1, 0, tzinfo=CAIRO),
    )
    assert interval.duration() == timedelta(hours=4)


def test_duration_inside_the_ambiguous_hour() -> None:
    """Wall-clock 23:30 fold 0 to 23:10 fold 1 is a valid 40 minute interval."""
    interval = TimeInterval(start=AMBIGUOUS_DEADLINE, end=AMBIGUOUS_NOW_LATER)
    assert interval.duration() == timedelta(minutes=40)
    assert as_instant(interval.start) < as_instant(interval.end)


def test_ordering_uses_instants_when_wall_clock_disagrees() -> None:
    """23:10 fold 1 is later than 23:30 fold 0 even though its wall clock is smaller."""
    early = TimeInterval(
        start=datetime(2026, 10, 29, 23, 30, tzinfo=CAIRO, fold=0),
        end=datetime(2026, 10, 29, 23, 50, tzinfo=CAIRO, fold=0),
    )
    late = TimeInterval(
        start=datetime(2026, 10, 29, 23, 10, tzinfo=CAIRO, fold=1),
        end=datetime(2026, 10, 29, 23, 20, tzinfo=CAIRO, fold=1),
    )
    assert late.start.replace(tzinfo=None) < early.start.replace(tzinfo=None)
    assert early < late
    assert not early.overlaps(late)
    assert not late.overlaps(early)
    assert early.intersection(late) is None


def test_overlaps_and_intersection_across_the_ambiguous_hour() -> None:
    """A fold 0 interval can overlap a later fold 1 interval by UTC instant."""
    wide = TimeInterval(
        start=datetime(2026, 10, 29, 23, 50, tzinfo=CAIRO, fold=0),
        end=datetime(2026, 10, 30, 0, 10, tzinfo=CAIRO),
    )
    second = TimeInterval(
        start=datetime(2026, 10, 29, 23, 0, tzinfo=CAIRO, fold=1),
        end=datetime(2026, 10, 30, 0, 0, tzinfo=CAIRO),
    )
    assert wide.overlaps(second)
    assert second.overlaps(wide)
    shared = wide.intersection(second)
    assert shared is not None
    # The result is expressed in UTC, not in the Cairo zone of the inputs.
    assert shared.start.tzinfo is UTC
    assert shared == TimeInterval(
        start=datetime(2026, 10, 29, 21, 0, tzinfo=UTC),
        end=datetime(2026, 10, 29, 22, 0, tzinfo=UTC),
    )
    assert shared.duration() == timedelta(hours=1)


def test_contains_uses_instants_when_wall_clock_disagrees() -> None:
    """23:00 fold 1 is inside an interval that starts at 23:50 fold 0."""
    interval = TimeInterval(
        start=datetime(2026, 10, 29, 23, 50, tzinfo=CAIRO, fold=0),
        end=datetime(2026, 10, 30, 0, 10, tzinfo=CAIRO),
    )
    assert interval.contains(datetime(2026, 10, 29, 23, 0, tzinfo=CAIRO, fold=1))
    # Start is inclusive and end is exclusive, by instant.
    assert interval.contains(interval.start)
    assert not interval.contains(interval.end)
    # 21:40Z (23:40 fold 1) is inside [20:50Z, 22:10Z).
    assert interval.contains(datetime(2026, 10, 29, 23, 40, tzinfo=CAIRO, fold=1))
    # 20:40Z (23:40 fold 0) is before the start (20:50Z).
    assert not interval.contains(datetime(2026, 10, 29, 23, 40, tzinfo=CAIRO, fold=0))


def test_is_deadline_passed_inside_the_ambiguous_hour() -> None:
    """The 20:30Z deadline has passed at 21:10Z but not at 20:10Z (ADR 0001 items 3 and 19)."""
    deadline = DateTimeDeadline(at=AMBIGUOUS_DEADLINE)
    assert is_deadline_passed(deadline, AMBIGUOUS_NOW_LATER, CAIRO)
    assert not is_deadline_passed(deadline, AMBIGUOUS_NOW_EARLIER, CAIRO)


def test_is_overdue_inside_the_ambiguous_hour() -> None:
    """A planned task with the 20:30Z deadline follows the same rule (ADR 0001 item 9)."""
    task = create_task(
        task_id=UUID(int=1),
        title="Task",
        now=datetime(2026, 10, 29, 19, 0, tzinfo=UTC),
        status=TaskStatus.PLANNED,
        deadline=DateTimeDeadline(at=AMBIGUOUS_DEADLINE),
    )
    assert is_overdue(task, AMBIGUOUS_NOW_LATER, CAIRO)
    assert not is_overdue(task, AMBIGUOUS_NOW_EARLIER, CAIRO)


def test_transition_task_accepts_a_later_instant_with_a_smaller_wall_clock() -> None:
    """23:10 fold 1 is after a task updated at 23:30 fold 0 (ADR 0001 item 19)."""
    task = create_task(
        task_id=UUID(int=1),
        title="Task",
        now=AMBIGUOUS_DEADLINE,
        status=TaskStatus.PLANNED,
    )
    result = transition_task(task, TaskStatus.IN_PROGRESS, now=AMBIGUOUS_NOW_LATER)
    assert result.task.status is TaskStatus.IN_PROGRESS
    assert result.task.updated_at == AMBIGUOUS_NOW_LATER


def test_transition_task_rejects_an_earlier_instant_with_a_larger_wall_clock() -> None:
    """23:10 fold 0 is before a task updated at 23:30 fold 0 (ADR 0001 item 19)."""
    task = create_task(
        task_id=UUID(int=1),
        title="Task",
        now=AMBIGUOUS_DEADLINE,
        status=TaskStatus.PLANNED,
    )
    with pytest.raises(DomainValidationError) as excinfo:
        transition_task(task, TaskStatus.IN_PROGRESS, now=AMBIGUOUS_NOW_EARLIER)
    assert excinfo.value.field == "now"


def test_edit_task_accepts_a_later_instant_with_a_smaller_wall_clock() -> None:
    """Editing at 23:10 fold 1 after 23:30 fold 0 is accepted (ADR 0001 item 19)."""
    task = create_task(
        task_id=UUID(int=1),
        title="Task",
        now=AMBIGUOUS_DEADLINE,
        status=TaskStatus.PLANNED,
    )
    edited = edit_task(task, now=AMBIGUOUS_NOW_LATER, title="Renamed")
    assert edited.title == "Renamed"
    assert edited.updated_at == AMBIGUOUS_NOW_LATER


def test_edit_task_rejects_an_earlier_instant_with_a_larger_wall_clock() -> None:
    """Editing at 23:10 fold 0 after 23:30 fold 0 is rejected (ADR 0001 item 19)."""
    task = create_task(
        task_id=UUID(int=1),
        title="Task",
        now=AMBIGUOUS_DEADLINE,
        status=TaskStatus.PLANNED,
    )
    with pytest.raises(DomainValidationError) as excinfo:
        edit_task(task, now=AMBIGUOUS_NOW_EARLIER, title="Renamed")
    assert excinfo.value.field == "now"


def test_task_accepts_created_at_then_later_updated_at_across_fold() -> None:
    """created_at 23:30 fold 0, updated_at 23:10 fold 1 is valid (ADR 0001 item 19)."""
    task = _task(created_at=AMBIGUOUS_DEADLINE, updated_at=AMBIGUOUS_NOW_LATER)
    assert as_instant(task.updated_at) > as_instant(task.created_at)


def test_task_rejects_updated_at_before_created_at_across_fold() -> None:
    """created_at 23:10 fold 1, updated_at 23:30 fold 0 is rejected (ADR 0001 item 19)."""
    with pytest.raises(DomainValidationError) as excinfo:
        _task(created_at=AMBIGUOUS_NOW_LATER, updated_at=AMBIGUOUS_DEADLINE)
    assert excinfo.value.field == "updated_at"


def test_reopen_keeps_a_schedule_that_has_not_ended_by_instant() -> None:
    """A schedule ending at 21:10Z is kept when reopening at 20:30Z (ADR 0001 items 8 and 19)."""
    scheduled = TimeInterval(
        start=datetime(2026, 10, 29, 23, 0, tzinfo=CAIRO, fold=0),  # 20:00Z
        end=AMBIGUOUS_NOW_LATER,  # 21:10Z
    )
    task = create_task(
        task_id=UUID(int=1),
        title="Task",
        now=datetime(2026, 10, 29, 19, 0, tzinfo=UTC),
        status=TaskStatus.PLANNED,
        scheduled=scheduled,
    )
    canceled = transition_task(
        task, TaskStatus.CANCELED, now=datetime(2026, 10, 29, 20, 0, tzinfo=UTC)
    ).task
    result = transition_task(canceled, TaskStatus.PLANNED, now=AMBIGUOUS_DEADLINE)
    assert result.task.scheduled == scheduled
    assert result.event.discarded_schedule is None


def test_reopen_drops_a_schedule_that_has_ended_by_instant() -> None:
    """A schedule ending at 21:10Z is dropped when reopening at 21:30Z (ADR 0001 items 8 and 19)."""
    scheduled = TimeInterval(
        start=datetime(2026, 10, 29, 23, 0, tzinfo=CAIRO, fold=0),  # 20:00Z
        end=AMBIGUOUS_NOW_LATER,  # 21:10Z
    )
    task = create_task(
        task_id=UUID(int=1),
        title="Task",
        now=datetime(2026, 10, 29, 19, 0, tzinfo=UTC),
        status=TaskStatus.PLANNED,
        scheduled=scheduled,
    )
    canceled = transition_task(
        task, TaskStatus.CANCELED, now=datetime(2026, 10, 29, 20, 0, tzinfo=UTC)
    ).task
    later = datetime(2026, 10, 29, 23, 30, tzinfo=CAIRO, fold=1)  # 21:30Z
    result = transition_task(canceled, TaskStatus.PLANNED, now=later)
    assert result.task.scheduled is None
    assert result.event.discarded_schedule == scheduled


@given(pair=same_zone_instants())
def test_duration_matches_the_utc_difference(
    pair: tuple[ZoneInfo, datetime, datetime, datetime],
) -> None:
    """Duration equals the UTC difference for values sharing one zone object."""
    zone, first, second, _ = pair
    assume(as_instant(first) != as_instant(second))
    start, end = sorted((first, second), key=as_instant)
    interval = TimeInterval(start=start, end=end)
    assert interval.duration() == as_instant(end) - as_instant(start)
    assert interval.start.tzinfo is zone
    assert interval.end.tzinfo is zone


@given(intervals_pair=same_zone_intervals())
def test_overlaps_and_intersection_match_utc(
    intervals_pair: tuple[ZoneInfo, TimeInterval, TimeInterval],
) -> None:
    """Overlap and intersection bounds equal the UTC comparison for one zone object."""
    zone, first, second = intervals_pair
    assert first.start.tzinfo is zone
    assert second.start.tzinfo is zone
    first_start, first_end = as_instant(first.start), as_instant(first.end)
    second_start, second_end = as_instant(second.start), as_instant(second.end)
    expected_overlap = first_start < second_end and second_start < first_end
    assert first.overlaps(second) is expected_overlap
    assert second.overlaps(first) is expected_overlap

    shared = first.intersection(second)
    if not expected_overlap:
        assert shared is None
        return
    assert shared is not None
    assert as_instant(shared.start) == max(first_start, second_start)
    assert as_instant(shared.end) == min(first_end, second_end)
    assert shared.duration() == min(first_end, second_end) - max(first_start, second_start)


@given(intervals_pair=same_zone_intervals())
def test_ordering_matches_utc(
    intervals_pair: tuple[ZoneInfo, TimeInterval, TimeInterval],
) -> None:
    """Interval ordering follows UTC instants for values sharing one zone object."""
    _, first, second = intervals_pair
    first_key = (as_instant(first.start), as_instant(first.end))
    second_key = (as_instant(second.start), as_instant(second.end))
    assert (first < second) is (first_key < second_key)
    assert (first <= second) is (first_key <= second_key)
    assert (first > second) is (first_key > second_key)
    assert (first >= second) is (first_key >= second_key)
    assert (first == second) is (first_key == second_key)


@given(values=same_zone_instants())
def test_contains_matches_utc(
    values: tuple[ZoneInfo, datetime, datetime, datetime],
) -> None:
    """Contains equals the half-open UTC comparison for values sharing one zone object."""
    _, first, second, instant = values
    assume(as_instant(first) != as_instant(second))
    start, end = sorted((first, second), key=as_instant)
    interval = TimeInterval(start=start, end=end)
    expected = as_instant(start) <= as_instant(instant) < as_instant(end)
    assert interval.contains(instant) is expected


@given(values=same_zone_instants())
def test_deadline_passed_matches_utc(
    values: tuple[ZoneInfo, datetime, datetime, datetime],
) -> None:
    """is_deadline_passed equals ``now > at`` on UTC instants (ADR 0001 items 3 and 19)."""
    zone, at, now, _ = values
    deadline = DateTimeDeadline(at=at)
    expected = as_instant(now) > as_instant(at)
    assert is_deadline_passed(deadline, now, zone) is expected


@given(values=same_zone_instants())
def test_is_overdue_matches_utc(
    values: tuple[ZoneInfo, datetime, datetime, datetime],
) -> None:
    """is_overdue equals the UTC deadline comparison for a planned task (ADR 0001 item 9)."""
    zone, at, now, _ = values
    task = create_task(
        task_id=UUID(int=1),
        title="Task",
        now=datetime(2000, 1, 1, tzinfo=UTC),
        status=TaskStatus.PLANNED,
        deadline=DateTimeDeadline(at=at),
    )
    expected = as_instant(now) > as_instant(at)
    assert is_overdue(task, now, zone) is expected
