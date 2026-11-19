"""Time value objects and local-day helpers (ADR 0001 items 2, 3, 13, 14, 18)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from lifespace.domain.errors import DomainValidationError
from lifespace.domain.limits import MAX_INSTANT, MIN_INSTANT


def ensure_aware(value: datetime, *, field: str) -> datetime:
    """Return ``value`` unchanged when it is timezone-aware (ADR 0001 item 14).

    Raises ``DomainValidationError`` for a naive datetime, because every domain
    datetime must carry a time zone.
    """
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{field} must be timezone-aware", field=field)
    return value


def as_instant(value: datetime, *, field: str = "value") -> datetime:
    """Return ``value`` as a UTC instant (ADR 0001 item 19).

    Python compares and subtracts two aware datetimes that share the same
    ``tzinfo`` object by their wall-clock fields, ignoring the UTC offset and
    the ``fold``. Every comparison and subtraction in the domain therefore goes
    through this function, which converts with ``astimezone(UTC)``. A naive
    value is rejected with ``DomainValidationError`` (ADR 0001 item 14), and an
    instant whose UTC conversion overflows is a validation failure rather than
    an ``OverflowError`` (ADR 0002 item 21).
    """
    aware = ensure_aware(value, field=field)
    try:
        return aware.astimezone(UTC)
    except OverflowError as error:
        raise DomainValidationError(
            f"{field} is outside the supported range",
            field=field,
        ) from error


def ensure_instant_in_range(value: datetime, *, field: str) -> datetime:
    """Return ``value`` when its UTC instant is in the supported range (ADR 0002 item 20).

    The supported range is ``MIN_INSTANT <= instant < MAX_INSTANT``. A naive
    value or an instant outside that range raises ``DomainValidationError``, and
    an overflowing UTC conversion never escapes as ``OverflowError`` (ADR 0002
    item 21).
    """
    instant = as_instant(value, field=field)
    if not MIN_INSTANT <= instant < MAX_INSTANT:
        raise DomainValidationError(
            f"{field} is outside the supported range",
            field=field,
        )
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


@dataclass(frozen=True, slots=True, eq=False)
class TimeInterval:
    """A half-open interval ``[start, end)`` of timezone-aware datetimes.

    ``start`` is included and ``end`` is excluded (ADR 0001 item 13). Both
    bounds are validated as aware, and ``end`` must be strictly after ``start``
    (ADR 0001 item 14). Equality and ordering use the instants, so the same
    interval written in two different offsets is equal.
    """

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        """Validate the bounds, range, and order (ADR 0001 item 13; ADR 0002 item 20)."""
        ensure_instant_in_range(self.start, field="start")
        ensure_instant_in_range(self.end, field="end")
        start_instant, end_instant = self._instant_key()
        if end_instant <= start_instant:
            raise DomainValidationError("end must be strictly after start", field="end")

    def _instant_key(self) -> tuple[datetime, datetime]:
        """Return both bounds normalized to UTC, removing any fold ambiguity."""
        return (as_instant(self.start), as_instant(self.end))

    def __eq__(self, other: object) -> bool:
        """Compare the interval by its instants (ADR 0001 item 14)."""
        if not isinstance(other, TimeInterval):
            return NotImplemented
        return self._instant_key() == other._instant_key()

    def __hash__(self) -> int:
        """Hash the interval by its instants (ADR 0001 item 14)."""
        return hash(self._instant_key())

    def __lt__(self, other: TimeInterval) -> bool:
        """Order intervals by their start and end instants."""
        return self._instant_key() < other._instant_key()

    def __le__(self, other: TimeInterval) -> bool:
        """Order intervals by their start and end instants."""
        return self._instant_key() <= other._instant_key()

    def __gt__(self, other: TimeInterval) -> bool:
        """Order intervals by their start and end instants."""
        return self._instant_key() > other._instant_key()

    def __ge__(self, other: TimeInterval) -> bool:
        """Order intervals by their start and end instants."""
        return self._instant_key() >= other._instant_key()

    def duration(self) -> timedelta:
        """Return the real elapsed time from ``start`` to ``end`` (ADR 0001 item 19).

        The bounds are converted to UTC instants first, so a daylight saving
        change between them is reflected in the result.
        """
        start_instant, end_instant = self._instant_key()
        return end_instant - start_instant

    def overlaps(self, other: TimeInterval) -> bool:
        """Return whether the intervals share an instant (ADR 0001 item 13).

        Uses exactly ``start < other.end and other.start < end`` on UTC
        instants (ADR 0001 item 19); adjacent intervals therefore do not
        overlap.
        """
        self_start, self_end = self._instant_key()
        other_start, other_end = other._instant_key()
        return self_start < other_end and other_start < self_end

    def touches(self, other: TimeInterval) -> bool:
        """Return whether the intervals are adjacent, sharing only a boundary (ADR 0001 item 13)."""
        self_start, self_end = self._instant_key()
        other_start, other_end = other._instant_key()
        return self_end == other_start or other_end == self_start

    def contains(self, instant: datetime) -> bool:
        """Return whether ``start <= instant < end`` by UTC instant (ADR 0001 item 19)."""
        instant_utc = as_instant(instant)
        start_instant, end_instant = self._instant_key()
        return start_instant <= instant_utc < end_instant

    def intersection(self, other: TimeInterval) -> TimeInterval | None:
        """Return the shared interval, or ``None`` when the intervals do not overlap.

        The rule is ADR 0001 item 13, applied to UTC instants (ADR 0001 item
        19). The result is expressed in UTC, not in the zone of either input.
        """
        if not self.overlaps(other):
            return None
        self_start, self_end = self._instant_key()
        other_start, other_end = other._instant_key()
        return TimeInterval(start=max(self_start, other_start), end=min(self_end, other_end))
