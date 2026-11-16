"""Tests for database helpers."""

from sqlalchemy.ext.asyncio import AsyncEngine

from lifespace.infrastructure.db import check_database, create_engine, metadata


async def test_check_database_is_false_for_unreachable_host() -> None:
    engine: AsyncEngine = create_engine(
        "postgresql+asyncpg://user:password@127.0.0.1:9/unreachable"
    )
    try:
        assert await check_database(engine) is False
    finally:
        await engine.dispose()


def test_metadata_naming_convention_has_all_keys() -> None:
    assert set(metadata.naming_convention) == {"ix", "uq", "ck", "fk", "pk"}
