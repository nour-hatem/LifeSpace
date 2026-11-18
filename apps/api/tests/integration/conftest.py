"""Checks shared by integration tests that need the local PostgreSQL container.

These are plain functions rather than fixtures so that an unreachable database
is reported as a test failure, with an actionable message, instead of a skip.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest

from lifespace.config import Settings
from lifespace.infrastructure.db import check_database, create_engine

API_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI = API_DIR / "alembic.ini"


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


def run_alembic(url: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run an Alembic command in a subprocess against ``url``.

    Alembic's env.py calls ``asyncio.run``, so a subprocess is the safe way to
    migrate from an async test or fixture.
    """
    environment = os.environ | {"LIFESPACE_DATABASE_URL": url}
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), *arguments],
        cwd=API_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def reset_database(url: str) -> None:
    """Empty the M2 tables and restore the single UTC settings row."""
    from sqlalchemy import text

    from lifespace.infrastructure.db import create_engine

    async def run() -> None:
        engine = create_engine(url)
        try:
            async with engine.begin() as connection:
                for statement in [
                    "truncate table tasks, task_status_events, idempotency_keys cascade",
                    "delete from app_settings",
                    "insert into app_settings (id, timezone, updated_at) values (1, 'UTC', now())",
                ]:
                    await connection.execute(text(statement))
        finally:
            await engine.dispose()

    asyncio.run(run())
