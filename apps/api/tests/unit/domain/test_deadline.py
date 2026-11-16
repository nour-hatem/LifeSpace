"""Tests for deadline values and the overdue rule (ADR 0001 items 2, 3, 9, 14)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lifespace.domain.deadline import DateDeadline, DateTimeDeadline, Deadline, is_deadline_passed
from lifespace.domain.errors import DomainValidationError
from lifespace.domain.time import start_of_local_day

from .strategies import ZONES, dates, deadlines, utc_instants

CAIRO = ZoneInfo("Africa/Cairo")
UTC_ZONE = ZoneInfo("UTC")


def test_date_time_deadline_rejects_a_naive_instant() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        DateTimeDeadline(at=datetime(2026, 5, 1, 12))
    assert excinfo.value.field == "at"


def test_date_time_deadline_is_not_passed_at_the_instant() -> None:
    deadline = DateTimeDeadline(at=datetime(2026, 5, 1, 12, tzinfo=UTC))
    assert not is_deadline_passed(deadline, datetime(2026, 5, 1, 12, tzinfo=UTC), UTC_ZONE)


def test_date_time_deadline_is_passed_one_microsecond_later() -> None:
    deadline = DateTimeDeadline(at=datetime(2026, 5, 1, 12, tzinfo=UTC))
    just_after = datetime(2026, 5, 1, 12, tzinfo=UTC) + timedelta(microseconds=1)
    assert is_deadline_passed(deadline, just_after, UTC_ZONE)


def test_date_deadline_boundary_in_utc() -> None:
    deadline = DateDeadline(day=date(2026, 4, 23))
    just_before = datetime(2026, 4, 23, 23, 59, 59, 999999, tzinfo=UTC)
    assert not is_deadline_passed(deadline, just_before, UTC_ZONE)
    assert is_deadline_passed(deadline, datetime(2026, 4, 24, tzinfo=UTC), UTC_ZONE)


def test_date_deadline_boundary_in_cairo_across_spring_forward() -> None:
    deadline = DateDeadline(day=date(2026, 4, 23))
    assert not is_deadline_passed(
        deadline, datetime(2026, 4, 23, 21, 59, 59, 999999, tzinfo=UTC), CAIRO
    )
    assert is_deadline_passed(deadline, datetime(2026, 4, 23, 22, tzinfo=UTC), CAIRO)


def test_date_deadline_boundary_in_cairo_across_fall_back() -> None:
    deadline = DateDeadline(day=date(2026, 10, 29))
    assert not is_deadline_passed(
        deadline, datetime(2026, 10, 29, 21, 59, 59, 999999, tzinfo=UTC), CAIRO
    )
    assert is_deadline_passed(deadline, datetime(2026, 10, 29, 22, tzinfo=UTC), CAIRO)


@pytest.mark.parametrize(
    "deadline",
    [
        DateDeadline(day=date(2026, 4, 23)),
        DateTimeDeadline(at=datetime(2026, 4, 23, 12, tzinfo=UTC)),
    ],
)
def test_naive_now_is_rejected(deadline: Deadline) -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        is_deadline_passed(deadline, datetime(2026, 4, 23, 12), CAIRO)
    assert excinfo.value.field == "now"


@given(
    deadline=deadlines,
    now=utc_instants,
    offset=st.timedeltas(min_value=timedelta(microseconds=1), max_value=timedelta(days=365)),
    tz=st.sampled_from(ZONES),
)
def test_overdue_is_monotonic(
    deadline: Deadline, now: datetime, offset: timedelta, tz: ZoneInfo
) -> None:
    if is_deadline_passed(deadline, now, tz):
        assert is_deadline_passed(deadline, now + offset, tz)


@given(day=dates, tz=st.sampled_from(ZONES))
def test_date_deadline_is_not_passed_at_the_start_of_its_own_day(day: date, tz: ZoneInfo) -> None:
    assert not is_deadline_passed(DateDeadline(day=day), start_of_local_day(day, tz), tz)
