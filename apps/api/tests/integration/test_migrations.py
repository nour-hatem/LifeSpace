"""Integration test for the Alembic revisions.

The test is synchronous on purpose: Alembic's env.py calls ``asyncio.run``, so
invoking the Alembic command API from inside a running event loop would fail.
The drift check runs Alembic in a subprocess for the same reason.
"""

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from lifespace.infrastructure.db import create_engine
from tests.integration.conftest import require_test_database_url_sync, run_alembic

API_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI = API_DIR / "alembic.ini"

M2_TABLES = ("tasks", "task_status_events", "app_settings", "idempotency_keys")


def _config(url: str) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def _applied_revisions(url: str) -> list[str]:
    async def read() -> list[str]:
        engine = create_engine(url)
        try:
            async with engine.connect() as connection:
                result = await connection.execute(text("select version_num from alembic_version"))
                return [str(row[0]) for row in result]
        finally:
            await engine.dispose()

    return asyncio.run(read())


def _public_tables(url: str) -> set[str]:
    async def read() -> set[str]:
        engine = create_engine(url)
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        "select table_name from information_schema.tables "
                        "where table_schema = 'public'"
                    )
                )
                return {str(row[0]) for row in result}
        finally:
            await engine.dispose()

    return asyncio.run(read())


def test_revision_0002_migrates_up_and_down() -> None:
    """Revision 0002 applies from 0001 and drops every M2 table at base (ADR 0002 item 19)."""
    url = require_test_database_url_sync()
    config = _config(url)
    try:
        command.upgrade(config, "head")
        assert _applied_revisions(url) == ["0002"]
        assert set(M2_TABLES) <= _public_tables(url)

        check = run_alembic(url, "check")
        assert check.returncode == 0, check.stderr

        command.downgrade(config, "base")
        assert _applied_revisions(url) == []
        assert _public_tables(url).isdisjoint(M2_TABLES)

        command.upgrade(config, "0001")
        assert _applied_revisions(url) == ["0001"]
        assert _public_tables(url).isdisjoint(M2_TABLES)

        command.upgrade(config, "0002")
        assert _applied_revisions(url) == ["0002"]
        assert set(M2_TABLES) <= _public_tables(url)
    finally:
        command.downgrade(config, "base")
