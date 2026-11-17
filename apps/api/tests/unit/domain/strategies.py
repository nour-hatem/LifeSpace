"""Shared generated values for the domain property tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from hypothesis import strategies as st

from lifespace.domain.deadline import DateDeadline, DateTimeDeadline, Deadline
from lifespace.domain.task import (
    Category,
    Priority,
    Task,
    TaskSource,
    TaskStatus,
    create_task,
)
from lifespace.domain.time import TimeInterval

ZONES: tuple[ZoneInfo, ...] = tuple(
    ZoneInfo(name)
    for name in (
        "UTC",
        "Africa/Cairo",
        "America/New_York",
        "Europe/London",
        "Asia/Kolkata",
        "Pacific/Auckland",
    )
)

MIN_DATE = date(2000, 1, 1)
MAX_DATE = date(2100, 12, 31)
MIN_INSTANT = datetime(2000, 1, 1, tzinfo=UTC)
MAX_INSTANT = datetime(2100, 12, 31, tzinfo=UTC)

TRANSITION_INSTANTS: tuple[datetime, ...] = (
    # Africa/Cairo spring forward and fall back in 2026.
    datetime(2026, 4, 23, 22, tzinfo=UTC),
    datetime(2026, 10, 29, 21, tzinfo=UTC),
    # America/New_York spring forward and fall back in 2026.
    datetime(2026, 3, 8, 7, tzinfo=UTC),
    datetime(2026, 11, 1, 6, tzinfo=UTC),
)

dates: st.SearchStrategy[date] = st.dates(min_value=MIN_DATE, max_value=MAX_DATE)
utc_instants: st.SearchStrategy[datetime] = st.datetimes(
    min_value=MIN_INSTANT, max_value=MAX_INSTANT, timezones=st.just(UTC)
)
near_transition_instants: st.SearchStrategy[datetime] = st.one_of(
    utc_instants,
    st.sampled_from(TRANSITION_INSTANTS).flatmap(
        lambda base: st.timedeltas(min_value=timedelta(hours=-6), max_value=timedelta(hours=6)).map(
            lambda delta: base + delta
        )
    ),
)
durations: st.SearchStrategy[timedelta] = st.timedeltas(
    min_value=timedelta(microseconds=1), max_value=timedelta(days=365)
)
date_deadlines: st.SearchStrategy[DateDeadline] = dates.map(DateDeadline)
datetime_deadlines: st.SearchStrategy[DateTimeDeadline] = utc_instants.map(DateTimeDeadline)
deadlines: st.SearchStrategy[Deadline] = st.one_of(date_deadlines, datetime_deadlines)

ARABIC_TITLES: tuple[str, ...] = (
    "اكتب تقرير المشروع",
    "اجتماع فريق العمل",
    "مراجعة الخطة الأسبوعية",
)

_TEXT_CHARACTERS = st.characters(blacklist_categories=("Cc", "Cs"))

titles: st.SearchStrategy[str] = st.one_of(
    st.text(alphabet=_TEXT_CHARACTERS, min_size=1).filter(lambda value: bool(value.strip())),
    st.sampled_from(ARABIC_TITLES),
)
descriptions: st.SearchStrategy[str] = st.text(alphabet=_TEXT_CHARACTERS)


@st.composite
def intervals(draw: st.DrawFn) -> TimeInterval:
    """Generate a valid half-open interval inside the test instant range."""
    start = draw(
        st.datetimes(
            min_value=MIN_INSTANT,
            max_value=MAX_INSTANT - timedelta(days=366),
            timezones=st.just(UTC),
        )
    )
    duration = draw(durations)
    return TimeInterval(start=start, end=start + duration)


@st.composite
def same_zone_instants(
    draw: st.DrawFn,
) -> tuple[ZoneInfo, datetime, datetime, datetime]:
    """Draw one zone object and three instants expressed with that same object.

    Using one ``ZoneInfo`` object for every value means the datetimes share a
    ``tzinfo``, which is the case where Python compares wall-clock fields
    instead of UTC instants (ADR 0001 item 19).
    """
    zone = draw(st.sampled_from(ZONES))
    first = draw(near_transition_instants)
    second = draw(near_transition_instants)
    third = draw(near_transition_instants)
    return (
        zone,
        first.astimezone(zone),
        second.astimezone(zone),
        third.astimezone(zone),
    )


@st.composite
def same_zone_intervals(
    draw: st.DrawFn,
) -> tuple[ZoneInfo, TimeInterval, TimeInterval]:
    """Draw one zone object and two intervals expressed with that same object.

    Every bound is converted with the same ``ZoneInfo`` object, so the two
    intervals share one ``tzinfo`` (ADR 0001 item 19).
    """
    zone = draw(st.sampled_from(ZONES))
    first_start = draw(near_transition_instants)
    first_duration = draw(durations)
    second_start = draw(near_transition_instants)
    second_duration = draw(durations)
    return (
        zone,
        TimeInterval(
            start=first_start.astimezone(zone),
            end=(first_start + first_duration).astimezone(zone),
        ),
        TimeInterval(
            start=second_start.astimezone(zone),
            end=(second_start + second_duration).astimezone(zone),
        ),
    )


@st.composite
def valid_tasks(draw: st.DrawFn) -> Task:
    """Generate a valid task created through ``create_task`` in Planned or Inbox status."""
    return create_task(
        task_id=draw(st.uuids()),
        title=draw(titles),
        now=draw(utc_instants),
        source=draw(st.sampled_from(TaskSource)),
        status=draw(st.sampled_from((TaskStatus.INBOX, TaskStatus.PLANNED))),
        description=draw(st.none() | descriptions),
        category=draw(st.none() | st.sampled_from(Category)),
        priority=draw(st.none() | st.sampled_from(Priority)),
        estimate_minutes=draw(st.none() | st.integers(min_value=1, max_value=10_080)),
        deadline=draw(st.none() | deadlines),
        scheduled=draw(st.none() | intervals()),
    )
