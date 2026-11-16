"""Fixtures for integration tests that need the local PostgreSQL container."""

import asyncio

import pytest

from lifespace.config import Settings
from lifespace.infrastructure.db import check_database, create_engine


async def _is_reachable(url: str) -> bool:
    engine = create_engine(url)
    try:
        return await check_database(engine)
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Return the test database URL, failing with an actionable message."""
    settings = Settings()
    url = settings.test_database_url
    if not url:
        pytest.fail("LIFESPACE_TEST_DATABASE_URL is not set. Run: make env")
    if not asyncio.run(_is_reachable(url)):
        pytest.fail("PostgreSQL is not reachable. Run: make db-up")
    return url
