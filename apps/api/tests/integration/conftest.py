"""Checks shared by integration tests that need the local PostgreSQL container.

These are plain functions rather than fixtures so that an unreachable database
is reported as a test failure, with an actionable message, instead of a skip.
"""

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


def _configured_url() -> str:
    settings = Settings()
    url = settings.test_database_url
    if not url:
        pytest.fail("LIFESPACE_TEST_DATABASE_URL is not set. Run: make env")
    return url


async def require_test_database_url() -> str:
    """Return the test database URL or fail the calling async test."""
    url = _configured_url()
    if not await _is_reachable(url):
        pytest.fail("PostgreSQL is not reachable. Run: make db-up")
    return url


def require_test_database_url_sync() -> str:
    """Synchronous variant for tests that already drive their own event loop."""
    url = _configured_url()
    if not asyncio.run(_is_reachable(url)):
        pytest.fail("PostgreSQL is not reachable. Run: make db-up")
    return url
