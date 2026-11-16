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

dates: st.SearchStrategy[date] = st.dates(min_value=MIN_DATE, max_value=MAX_DATE)
utc_instants: st.SearchStrategy[datetime] = st.datetimes(
    min_value=MIN_INSTANT, max_value=MAX_INSTANT, timezones=st.just(UTC)
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
