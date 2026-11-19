"""Deadline value types and the overdue comparison rule (ADR 0001 items 2, 3, 9)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from lifespace.domain.limits import ensure_date_in_range
from lifespace.domain.time import as_instant, ensure_instant_in_range, start_of_local_day


@dataclass(frozen=True, slots=True)
class DateDeadline:
    """A deadline at the end of the local calendar day ``day`` (ADR 0001 item 2)."""

    day: date

    def __post_init__(self) -> None:
        """Reject a day outside the supported date range (ADR 0002 item 20)."""
        ensure_date_in_range(self.day, field="day")


@dataclass(frozen=True, slots=True)
class DateTimeDeadline:
    """A deadline at an exact timezone-aware instant (ADR 0001 item 3)."""

    at: datetime

    def __post_init__(self) -> None:
        """Reject a naive or out of range instant (ADR 0001 item 14; ADR 0002 item 20)."""
        ensure_instant_in_range(self.at, field="at")


Deadline = DateDeadline | DateTimeDeadline


def is_deadline_passed(deadline: Deadline, now: datetime, tz: ZoneInfo) -> bool:
    """Return whether ``deadline`` has passed at ``now`` in ``tz`` (ADR 0001 items 2 and 3).

    A ``DateTimeDeadline`` has passed strictly after its instant: ``now > at``.
    A ``DateDeadline`` has passed from the first instant of the next local
    calendar day: ``now >= start_of_local_day(day + 1 day, tz)``. Both sides
    are compared as UTC instants (ADR 0001 item 19), and ``now`` must be
    timezone-aware.
    """
    ensure_instant_in_range(now, field="now")
    now_instant = as_instant(now)
    if isinstance(deadline, DateTimeDeadline):
        return now_instant > as_instant(deadline.at)
    next_day = deadline.day + timedelta(days=1)
    return now_instant >= as_instant(start_of_local_day(next_day, tz))
