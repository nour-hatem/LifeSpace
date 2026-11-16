"""Time value objects and local-day helpers (ADR 0001 items 2, 3, 13, 14, 18)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from lifespace.domain.errors import DomainValidationError


def ensure_aware(value: datetime, *, field: str) -> datetime:
    """Return ``value`` unchanged when it is timezone-aware (ADR 0001 item 14).

    Raises ``DomainValidationError`` for a naive datetime, because every domain
    datetime must carry a time zone.
    """
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{field} must be timezone-aware", field=field)
    return value


def local_date(instant: datetime, tz: ZoneInfo) -> date:
    """Return the calendar date of ``instant`` in ``tz`` (ADR 0001 item 2)."""
    return ensure_aware(instant, field="instant").astimezone(tz).date()


def start_of_local_day(day: date, tz: ZoneInfo) -> datetime:
    """Return the first instant whose local date in ``tz`` is ``day`` (ADR 0001 item 2).

    The value is computed as ``datetime.combine(day, time.min, tzinfo=tz)`` and
    normalized with ``.astimezone(UTC).astimezone(tz)``. A missing local midnight
    therefore resolves to the first instant later that morning, and an ambiguous
    midnight to the earlier occurrence (fold 0). A calendar day that does not
    exist at all in ``tz`` is out of scope (ADR 0001 item 18).
    """
    local_midnight = datetime.combine(day, time.min, tzinfo=tz)
    return local_midnight.astimezone(UTC).astimezone(tz)


@dataclass(frozen=True, slots=True, order=True)
class TimeInterval:
    """A half-open interval ``[start, end)`` of timezone-aware datetimes.

    ``start`` is included and ``end`` is excluded (ADR 0001 item 13). Both
    bounds are validated as aware, and ``end`` must be strictly after ``start``
    (ADR 0001 item 14).
    """

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        """Validate the bounds and their order (ADR 0001 items 13 and 14)."""
        ensure_aware(self.start, field="start")
        ensure_aware(self.end, field="end")
        if self.end <= self.start:
            raise DomainValidationError("end must be strictly after start", field="end")

    def duration(self) -> timedelta:
        """Return ``end - start``."""
        return self.end - self.start

    def overlaps(self, other: TimeInterval) -> bool:
        """Return whether the intervals share an instant (ADR 0001 item 13).

        Uses exactly ``start < other.end and other.start < end``; adjacent
        intervals therefore do not overlap.
        """
        return self.start < other.end and other.start < self.end

    def touches(self, other: TimeInterval) -> bool:
        """Return whether the intervals are adjacent, sharing only a boundary (ADR 0001 item 13)."""
        return self.end == other.start or other.end == self.start

    def contains(self, instant: datetime) -> bool:
        """Return whether ``start <= instant < end`` (ADR 0001 item 13)."""
        ensure_aware(instant, field="instant")
        return self.start <= instant < self.end

    def intersection(self, other: TimeInterval) -> TimeInterval | None:
        """Return the shared interval, or ``None`` when the intervals do not overlap.

        The rule is ADR 0001 item 13.
        """
        if not self.overlaps(other):
            return None
        return TimeInterval(start=max(self.start, other.start), end=min(self.end, other.end))
