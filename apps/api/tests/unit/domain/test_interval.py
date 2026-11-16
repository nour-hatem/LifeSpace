"""Tests for the TimeInterval value object (ADR 0001 items 13 and 14)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lifespace.domain.errors import DomainValidationError
from lifespace.domain.time import TimeInterval

from .strategies import ZONES, durations, intervals, utc_instants


def test_rejects_naive_start() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        TimeInterval(start=datetime(2026, 1, 1), end=datetime(2026, 1, 2, tzinfo=UTC))
    assert excinfo.value.field == "start"


def test_rejects_naive_end() -> None:
    with pytest.raises(DomainValidationError) as excinfo:
        TimeInterval(start=datetime(2026, 1, 1, tzinfo=UTC), end=datetime(2026, 1, 2))
    assert excinfo.value.field == "end"


def test_rejects_end_equal_to_start() -> None:
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(DomainValidationError):
        TimeInterval(start=instant, end=instant)


def test_rejects_end_before_start() -> None:
    with pytest.raises(DomainValidationError):
        TimeInterval(
            start=datetime(2026, 1, 2, tzinfo=UTC),
            end=datetime(2026, 1, 1, tzinfo=UTC),
        )


@given(first=intervals(), second=intervals())
def test_overlaps_is_symmetric(first: TimeInterval, second: TimeInterval) -> None:
    assert first.overlaps(second) is second.overlaps(first)


@given(interval=intervals())
def test_interval_overlaps_itself(interval: TimeInterval) -> None:
    assert interval.overlaps(interval)


@given(start=utc_instants, span=durations)
def test_adjacent_intervals_do_not_overlap_and_touch(start: datetime, span: timedelta) -> None:
    first = TimeInterval(start=start, end=start + span)
    second = TimeInterval(start=first.end, end=first.end + span)
    assert not first.overlaps(second)
    assert not second.overlaps(first)
    assert first.touches(second)
    assert second.touches(first)
    assert first.intersection(second) is None


@given(first=intervals(), second=intervals())
def test_overlap_matches_the_brute_force_rule(first: TimeInterval, second: TimeInterval) -> None:
    assert first.overlaps(second) == (first.start < second.end and second.start < first.end)


@given(first=intervals(), second=intervals())
def test_intersection_is_none_exactly_when_there_is_no_overlap(
    first: TimeInterval, second: TimeInterval
) -> None:
    intersection = first.intersection(second)
    if not first.overlaps(second):
        assert intersection is None
        return
    assert intersection is not None
    assert intersection.start == max(first.start, second.start)
    assert intersection.end == min(first.end, second.end)
    assert intersection.duration() > timedelta(0)
    assert first.contains(intersection.start)
    assert second.contains(intersection.start)


@given(interval=intervals())
def test_contains_is_start_inclusive_and_end_exclusive(interval: TimeInterval) -> None:
    assert interval.contains(interval.start)
    assert not interval.contains(interval.end)


@given(start=utc_instants, span=durations)
def test_contains_an_instant_strictly_inside(start: datetime, span: timedelta) -> None:
    interval = TimeInterval(start=start, end=start + span)
    assert interval.contains(start + span / 2)


@given(interval=intervals())
def test_duration_equals_end_minus_start(interval: TimeInterval) -> None:
    assert interval.duration() == interval.end - interval.start


@given(start=utc_instants, span=durations, tz=st.sampled_from(ZONES))
def test_the_same_interval_in_two_offsets_is_equal(
    start: datetime, span: timedelta, tz: ZoneInfo
) -> None:
    in_utc = TimeInterval(start=start, end=start + span)
    in_zone = TimeInterval(start=start.astimezone(tz), end=(start + span).astimezone(tz))
    assert in_zone == in_utc
    assert not in_zone < in_utc
    assert not in_utc < in_zone


def test_equality_uses_instants_in_an_ambiguous_local_hour() -> None:
    cairo = ZoneInfo("Africa/Cairo")
    end = datetime(2025, 10, 30, 20, tzinfo=UTC)
    local_end = end.astimezone(cairo)
    in_utc = TimeInterval(start=end - timedelta(hours=1), end=end)
    in_cairo = TimeInterval(start=(end - timedelta(hours=1)).astimezone(cairo), end=local_end)
    assert in_cairo == in_utc
    assert not in_cairo < in_utc
    assert in_cairo.touches(
        TimeInterval(start=local_end, end=datetime(2025, 10, 30, 21, tzinfo=UTC))
    )


@given(start=utc_instants, span=durations)
def test_ordering_uses_the_instant(start: datetime, span: timedelta) -> None:
    earlier = TimeInterval(start=start, end=start + span)
    later = TimeInterval(start=start + span, end=start + span + span)
    assert earlier < later
