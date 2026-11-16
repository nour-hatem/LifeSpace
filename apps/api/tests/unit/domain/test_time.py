"""Tests for ensure_aware and the local-day helpers (ADR 0001 items 2, 14, 18)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lifespace.domain.errors import DomainValidationError
from lifespace.domain.time import ensure_aware, local_date, start_of_local_day

from ._strategies import ZONES, dates

CAIRO = ZoneInfo("Africa/Cairo")


def test_ensure_aware_returns_aware_values_unchanged() -> None:
    instant = datetime(2026, 4, 24, 12, tzinfo=UTC)
    assert ensure_aware(instant, field="now") is instant


def test_ensure_aware_rejects_naive_values() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        ensure_aware(datetime(2026, 4, 24, 12), field="now")
    assert excinfo.value.code == "validation_failed"
    assert excinfo.value.field == "now"


@given(day=dates, tz=st.sampled_from(ZONES))
def test_start_of_local_day_starts_the_requested_local_date(day: date, tz: ZoneInfo) -> None:
    start = start_of_local_day(day, tz)
    assert start.tzinfo is tz
    assert local_date(start, tz) == day
    earlier = (start.astimezone(UTC) - timedelta(microseconds=1)).astimezone(tz)
    assert earlier.date() < day


def test_start_of_local_day_skips_a_missing_midnight() -> None:
    spring_forward = start_of_local_day(date(2026, 4, 24), CAIRO)
    assert spring_forward == datetime(2026, 4, 23, 22, tzinfo=UTC)
    assert spring_forward.hour == 1
    assert start_of_local_day(date(2026, 4, 25), CAIRO) == datetime(2026, 4, 24, 21, tzinfo=UTC)


def test_start_of_local_day_uses_the_earlier_ambiguous_midnight() -> None:
    fall_back = start_of_local_day(date(2026, 10, 30), CAIRO)
    assert fall_back == datetime(2026, 10, 29, 22, tzinfo=UTC)
    assert fall_back.fold == 0
