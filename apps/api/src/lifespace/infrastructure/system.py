"""System clock and UUIDv7 generator (ADR 0002 item 1).

These are the only places in the codebase allowed to read the clock or generate
identifiers. Domain and application code always receive them as ports.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid7


class SystemClock:
    """A clock that reads the operating system time as an aware UTC instant (ADR 0002 item 1)."""

    def now(self) -> datetime:
        """Return the current instant in UTC (ADR 0002 item 1)."""
        return datetime.now(UTC)


class Uuid7Generator:
    """An identifier generator producing time-ordered UUIDv7 values (ADR 0002 item 1)."""

    def new_id(self) -> UUID:
        """Return a new UUIDv7 (ADR 0002 item 1)."""
        return uuid7()
