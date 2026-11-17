"""Tests for the settings use cases (ADR 0002 item 8)."""

from __future__ import annotations

import pytest

from lifespace.application.errors import ValidationFailedError
from lifespace.application.models import AppSettings
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.settings import get_settings, update_timezone
from tests.unit.application.fakes import FakeClock, InMemoryStore


async def test_default_timezone_is_utc(uow_factory: UnitOfWorkFactory) -> None:
    """The single settings row defaults to UTC (ADR 0002 item 8)."""
    assert await get_settings(uow_factory) == AppSettings(timezone="UTC")


async def test_update_persists_the_timezone(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    store: InMemoryStore,
) -> None:
    """A valid zone is stored and returned (ADR 0002 item 8)."""
    result = await update_timezone(uow_factory, clock, "Africa/Cairo")

    assert result == AppSettings(timezone="Africa/Cairo")
    assert await get_settings(uow_factory) == AppSettings(timezone="Africa/Cairo")
    assert store.timezone == "Africa/Cairo"
    assert store.timezone_updated_at == clock.now()


@pytest.mark.parametrize("timezone", ["Mars/Base", "", "../etc/passwd"])
async def test_invalid_timezones_are_rejected_and_change_nothing(
    timezone: str,
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    store: InMemoryStore,
) -> None:
    """Unknown, empty, and traversal names fail with a field (ADR 0002 item 8)."""
    with pytest.raises(ValidationFailedError) as error:
        await update_timezone(uow_factory, clock, timezone)

    assert error.value.field == "timezone"
    assert await get_settings(uow_factory) == AppSettings(timezone="UTC")
    assert store.timezone == "UTC"
