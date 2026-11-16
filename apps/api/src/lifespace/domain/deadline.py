"""Deadline value types and the overdue comparison rule (ADR 0001 items 2, 3, 9)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from lifespace.domain.time import ensure_aware, start_of_local_day


@dataclass(frozen=True, slots=True)
class DateDeadline:
    """A deadline at the end of the local calendar day ``day`` (ADR 0001 item 2)."""

    day: date


@dataclass(frozen=True, slots=True)
class DateTimeDeadline:
    """A deadline at an exact timezone-aware instant (ADR 0001 item 3)."""

    at: datetime

    def __post_init__(self) -> None:
        """Reject a naive instant (ADR 0001 item 14)."""
        ensure_aware(self.at, field="at")


Deadline = DateDeadline | DateTimeDeadline


def is_deadline_passed(deadline: Deadline, now: datetime, tz: ZoneInfo) -> bool:
    """Return whether ``deadline`` has passed at ``now`` in ``tz`` (ADR 0001 items 2 and 3).

    A ``DateTimeDeadline`` has passed strictly after its instant: ``now > at``.
    A ``DateDeadline`` has passed from the first instant of the next local
    calendar day: ``now >= start_of_local_day(day + 1 day, tz)``.
    ``now`` must be timezone-aware.
    """
    ensure_aware(now, field="now")
    if isinstance(deadline, DateTimeDeadline):
        return now > deadline.at
    next_day = deadline.day + timedelta(days=1)
    return now >= start_of_local_day(next_day, tz)
