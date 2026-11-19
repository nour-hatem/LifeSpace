"""Tests for domain input limits and instant ranges (ADR 0002 items 20 and 21)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lifespace.domain.deadline import DateDeadline, DateTimeDeadline, Deadline, is_deadline_passed
from lifespace.domain.errors import DomainValidationError
from lifespace.domain.limits import (
    MAX_DATE,
    MAX_DESCRIPTION_LENGTH,
    MAX_INSTANT,
    MAX_INT32,
    MAX_REASON_LENGTH,
    MAX_TITLE_LENGTH,
    MIN_DATE,
    MIN_INSTANT,
    ensure_date_in_range,
    ensure_text,
)
from lifespace.domain.overdue import is_overdue
from lifespace.domain.task import Task, TaskStatus, create_task
from lifespace.domain.time import TimeInterval, as_instant, ensure_instant_in_range

NOW = datetime(2026, 1, 1, tzinfo=UTC)
BASE_ID = UUID("00000000-0000-0000-0000-000000000001")
ONE_MICROSECOND = timedelta(microseconds=1)

ZONE_NAMES = (
    "UTC",
    "Africa/Cairo",
    "America/New_York",
    "Europe/London",
    "Asia/Kolkata",
    "Pacific/Auckland",
)
TEST_ZONES = tuple(ZoneInfo(name) for name in ZONE_NAMES)


def _base_task() -> Task:
    """Return a planned task with no deadline."""
    return create_task(task_id=BASE_ID, title="Task", now=NOW)


def _task_with(deadline: Deadline) -> Task:
    """Return a planned task carrying ``deadline``."""
    return replace(_base_task(), deadline=deadline)


def test_ensure_text_accepts_the_exact_maximum_length() -> None:
    """Text of exactly the maximum length is storable (ADR 0002 item 20)."""
    value = "a" * 10
    assert ensure_text(value, field="title", max_length=10) == value


def test_ensure_text_rejects_one_character_over_the_maximum() -> None:
    """One character over the maximum is a field validation failure (ADR 0002 item 20)."""
    with pytest.raises(DomainValidationError) as error:
        ensure_text("a" * 11, field="title", max_length=10)
    assert error.value.field == "title"


@pytest.mark.parametrize("value", ["a\x00b", "a\ud800b", "a\udfffb"])
def test_ensure_text_rejects_nul_and_surrogates(value: str) -> None:
    """PostgreSQL cannot store NUL or lone surrogates (ADR 0002 item 20)."""
    with pytest.raises(DomainValidationError) as error:
        ensure_text(value, field="title", max_length=10)
    assert error.value.field == "title"


@pytest.mark.parametrize("value", ["اكتب تقرير المشروع", "📝 📚 ✅", "مرحبا📝"])
def test_ensure_text_accepts_arabic_and_emoji(value: str) -> None:
    """Non-Latin text and emoji are valid (ADR 0002 item 20)."""
    assert ensure_text(value, field="title", max_length=100) == value


def test_ensure_date_in_range_accepts_both_boundaries() -> None:
    """The date range includes MIN_DATE and MAX_DATE (ADR 0002 item 20)."""
    assert ensure_date_in_range(MIN_DATE, field="day") == MIN_DATE
    assert ensure_date_in_range(MAX_DATE, field="day") == MAX_DATE


@pytest.mark.parametrize(
    "day",
    [date(1969, 12, 31), date(3000, 1, 1), date.min, date.max],
)
def test_ensure_date_in_range_rejects_outside_values(day: date) -> None:
    """A date outside the supported range is a field validation failure (ADR 0002 item 20)."""
    with pytest.raises(DomainValidationError) as error:
        ensure_date_in_range(day, field="day")
    assert error.value.field == "day"


def test_title_boundaries_pass_and_fail() -> None:
    """A title of 1 or 500 characters passes; 501 fails with field title (ADR 0002 item 20)."""
    assert create_task(task_id=BASE_ID, title="a", now=NOW).title == "a"
    assert len(create_task(task_id=BASE_ID, title="a" * MAX_TITLE_LENGTH, now=NOW).title) == 500
    with pytest.raises(DomainValidationError) as error:
        create_task(task_id=BASE_ID, title="a" * (MAX_TITLE_LENGTH + 1), now=NOW)
    assert error.value.field == "title"


@pytest.mark.parametrize("title", ["", "   ", "\t\n "])
def test_empty_and_whitespace_titles_fail_with_field_title(title: str) -> None:
    """An empty title is still rejected with field title (ADR 0001 item 11)."""
    with pytest.raises(DomainValidationError) as error:
        create_task(task_id=BASE_ID, title=title, now=NOW)
    assert error.value.field == "title"


def test_description_boundaries() -> None:
    """A description of 20,000 characters passes and 20,001 fails (ADR 0002 item 20)."""
    accepted = create_task(
        task_id=BASE_ID,
        title="Task",
        now=NOW,
        description="d" * MAX_DESCRIPTION_LENGTH,
    )
    assert accepted.description is not None
    assert len(accepted.description) == MAX_DESCRIPTION_LENGTH

    with pytest.raises(DomainValidationError) as error:
        create_task(
            task_id=BASE_ID,
            title="Task",
            now=NOW,
            description="d" * (MAX_DESCRIPTION_LENGTH + 1),
        )
    assert error.value.field == "description"


def test_cancellation_reason_boundaries() -> None:
    """A task reason of 1,000 characters passes and 1,001 fails (ADR 0002 item 20)."""
    accepted = replace(
        _base_task(),
        status=TaskStatus.CANCELED,
        canceled_at=NOW,
        cancellation_reason="r" * MAX_REASON_LENGTH,
    )
    assert accepted.cancellation_reason is not None
    assert len(accepted.cancellation_reason) == MAX_REASON_LENGTH

    with pytest.raises(DomainValidationError) as error:
        replace(
            _base_task(),
            status=TaskStatus.CANCELED,
            canceled_at=NOW,
            cancellation_reason="r" * (MAX_REASON_LENGTH + 1),
        )
    assert error.value.field == "cancellation_reason"


@pytest.mark.parametrize("day", [MIN_DATE, MAX_DATE])
def test_date_deadline_range_boundaries_pass(day: date) -> None:
    """Date deadlines accept 1970-01-01 and 2999-12-31 (ADR 0002 item 20)."""
    assert DateDeadline(day=day).day == day


@pytest.mark.parametrize(
    "day",
    [date(1969, 12, 31), date(3000, 1, 1), date.min, date.max],
)
def test_date_deadline_range_rejects_outside_values(day: date) -> None:
    """Date deadlines reject days outside the range with field day (ADR 0002 item 20)."""
    with pytest.raises(DomainValidationError) as error:
        DateDeadline(day=day)
    assert error.value.field == "day"


def test_date_time_deadline_range_boundaries() -> None:
    """Datetime deadlines accept MIN_INSTANT and the last microsecond before MAX_INSTANT."""
    assert DateTimeDeadline(at=MIN_INSTANT).at == MIN_INSTANT
    last = MAX_INSTANT - ONE_MICROSECOND
    assert DateTimeDeadline(at=last).at == last


@pytest.mark.parametrize(
    "instant",
    [MIN_INSTANT - ONE_MICROSECOND, MAX_INSTANT],
)
def test_date_time_deadline_range_rejects_outside_values(instant: datetime) -> None:
    """Datetime deadlines reject instants outside the range with field at (ADR 0002 item 20)."""
    with pytest.raises(DomainValidationError) as error:
        DateTimeDeadline(at=instant)
    assert error.value.field == "at"


@pytest.mark.parametrize(
    ("start", "end", "field"),
    [
        (MIN_INSTANT - ONE_MICROSECOND, MIN_INSTANT, "start"),
        (MIN_INSTANT, MAX_INSTANT, "end"),
        (MAX_INSTANT, MAX_INSTANT + ONE_MICROSECOND, "start"),
    ],
)
def test_schedule_bounds_reject_outside_values(start: datetime, end: datetime, field: str) -> None:
    """A schedule bound outside the instant range fails with its field (ADR 0002 item 20)."""
    with pytest.raises(DomainValidationError) as error:
        TimeInterval(start=start, end=end)
    assert error.value.field == field


def test_schedule_accepts_the_range_boundaries() -> None:
    """A schedule may start at MIN_INSTANT and end just before MAX_INSTANT."""
    interval = TimeInterval(start=MIN_INSTANT, end=MAX_INSTANT - ONE_MICROSECOND)
    assert interval.start == MIN_INSTANT


@pytest.mark.parametrize(
    "text",
    ["0001-01-01T00:00:00+05:00", "9999-12-31T23:59:59-05:00"],
)
def test_as_instant_turns_overflow_into_a_validation_error(text: str) -> None:
    """An overflowing UTC conversion is a validation failure (ADR 0002 item 21)."""
    with pytest.raises(DomainValidationError) as error:
        as_instant(datetime.fromisoformat(text))
    assert error.value.field == "value"


@pytest.mark.parametrize(
    "text",
    ["0001-01-01T00:00:00+05:00", "9999-12-31T23:59:59-05:00"],
)
def test_date_time_deadline_rejects_overflowing_conversions(text: str) -> None:
    """Deadline construction never leaks OverflowError (ADR 0002 item 21)."""
    with pytest.raises(DomainValidationError):
        DateTimeDeadline(at=datetime.fromisoformat(text))


def test_ensure_instant_in_range_turns_overflow_into_a_validation_error() -> None:
    """Range validation never leaks OverflowError (ADR 0002 item 21)."""
    with pytest.raises(DomainValidationError) as error:
        ensure_instant_in_range(datetime.fromisoformat("0001-01-01T00:00:00+05:00"), field="at")
    assert error.value.field == "at"


def test_estimate_boundaries() -> None:
    """2,147,483,647 passes and 2,147,483,648 fails (ADR 0002 item 20)."""
    assert (
        create_task(
            task_id=BASE_ID, title="Task", now=NOW, estimate_minutes=MAX_INT32
        ).estimate_minutes
        == MAX_INT32
    )
    with pytest.raises(DomainValidationError) as error:
        create_task(task_id=BASE_ID, title="Task", now=NOW, estimate_minutes=MAX_INT32 + 1)
    assert error.value.field == "estimate_minutes"
    assert "2147483647" in error.value.message


def test_date_deadline_at_the_top_of_the_range_does_not_overflow() -> None:
    """A 2999-12-31 date deadline compares in extreme zones without OverflowError."""
    deadline = DateDeadline(day=MAX_DATE)
    cairo = ZoneInfo("Africa/Cairo")
    kiritimati = ZoneInfo("Pacific/Kiritimati")
    pago_pago = ZoneInfo("Pacific/Pago_Pago")

    cairo_threshold = datetime(2999, 12, 31, 22, tzinfo=UTC)
    assert not is_deadline_passed(deadline, cairo_threshold - ONE_MICROSECOND, cairo)
    assert is_deadline_passed(deadline, cairo_threshold, cairo)

    kiritimati_threshold = datetime(2999, 12, 31, 10, tzinfo=UTC)
    assert not is_deadline_passed(deadline, kiritimati_threshold - ONE_MICROSECOND, kiritimati)
    assert is_deadline_passed(deadline, kiritimati_threshold, kiritimati)

    latest = MAX_INSTANT - ONE_MICROSECOND
    assert not is_deadline_passed(deadline, latest, pago_pago)


def test_is_deadline_passed_rejects_an_out_of_range_now() -> None:
    """An out of range now is a validation failure with field now (ADR 0002 item 20)."""
    with pytest.raises(DomainValidationError) as error:
        is_deadline_passed(DateDeadline(day=date(2026, 1, 1)), MAX_INSTANT, ZoneInfo("UTC"))
    assert error.value.field == "now"


@given(
    deadline=st.one_of(
        st.dates(min_value=MIN_DATE, max_value=MAX_DATE).map(DateDeadline),
        st.datetimes(
            min_value=MIN_INSTANT,
            max_value=MAX_INSTANT - ONE_MICROSECOND,
            timezones=st.just(UTC),
        ).map(DateTimeDeadline),
    ),
    now=st.datetimes(
        min_value=MIN_INSTANT,
        max_value=MAX_INSTANT - ONE_MICROSECOND,
        timezones=st.just(UTC),
    ),
    tz=st.sampled_from(TEST_ZONES),
)
def test_deadline_comparisons_never_raise(deadline: Deadline, now: datetime, tz: ZoneInfo) -> None:
    """is_deadline_passed and is_overdue are total over valid inputs (ADR 0002 item 20)."""
    is_deadline_passed(deadline, now, tz)
    is_overdue(_task_with(deadline), now, tz)
