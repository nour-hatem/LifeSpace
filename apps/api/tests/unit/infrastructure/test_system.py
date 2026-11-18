"""Unit tests for the system clock and identifier generator (ADR 0002 item 1)."""

from __future__ import annotations

from datetime import timedelta

from lifespace.infrastructure.system import SystemClock, Uuid7Generator


def test_system_clock_returns_an_aware_utc_instant() -> None:
    """The system clock never returns a naive or non-UTC datetime (ADR 0002 item 1)."""
    now = SystemClock().now()

    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_uuid7_generator_is_unique_and_version_seven() -> None:
    """A thousand generated identifiers are distinct UUIDv7 values (ADR 0002 item 1)."""
    generator = Uuid7Generator()

    identifiers = [generator.new_id() for _ in range(1000)]

    assert len(set(identifiers)) == 1000
    assert all(identifier.version == 7 for identifier in identifiers)
