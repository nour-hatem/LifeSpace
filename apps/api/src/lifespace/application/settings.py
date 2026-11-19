"""Settings use cases (ADR 0002 item 8)."""

from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lifespace.application.errors import ValidationFailedError
from lifespace.application.models import AppSettings
from lifespace.application.ports import Clock, UnitOfWorkFactory


async def get_settings(uow_factory: UnitOfWorkFactory) -> AppSettings:
    """Return the stored application settings (ADR 0002 item 8)."""
    async with uow_factory() as uow:
        return AppSettings(timezone=await uow.settings.get_timezone())


async def update_timezone(
    uow_factory: UnitOfWorkFactory,
    clock: Clock,
    timezone: str,
) -> AppSettings:
    """Validate and persist the user's IANA time zone (ADR 0002 item 8).

    An empty name, a path traversal, or a zone ``zoneinfo`` does not know is
    rejected with ``ValidationFailedError`` and changes nothing (ADR 0002 item
    8). A valid zone is written in its own transaction.
    """
    _ensure_timezone(timezone)
    now = clock.now()
    async with uow_factory() as uow:
        await uow.settings.set_timezone(timezone, now=now)
        await uow.commit()
        return AppSettings(timezone=timezone)


def _ensure_timezone(timezone: str) -> None:
    """Reject an empty, traversal, oversized, or unknown zone name (ADR 0002 item 8)."""
    if not timezone:
        raise ValidationFailedError("timezone must not be empty", field="timezone")
    if len(timezone) > 64:
        raise ValidationFailedError(
            "timezone must be at most 64 characters",
            field="timezone",
        )
    if "\x00" in timezone:
        raise ValidationFailedError(
            "timezone must not contain the NUL character",
            field="timezone",
        )
    if ".." in timezone or timezone.startswith("/") or "\\" in timezone:
        raise ValidationFailedError(
            "timezone must be an IANA time zone name without a path traversal",
            field="timezone",
        )
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValidationFailedError(
            f"unknown timezone {timezone!r}",
            field="timezone",
        ) from error
