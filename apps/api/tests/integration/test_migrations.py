"""Integration test for the Alembic baseline migration.

The test is synchronous on purpose: Alembic's env.py calls ``asyncio.run``, so
invoking the Alembic command API from inside a running event loop would fail.
"""

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from lifespace.infrastructure.db import create_engine
from tests.integration.conftest import require_test_database_url_sync

API_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI = API_DIR / "alembic.ini"


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


def test_baseline_migrates_up_and_down() -> None:
    url = require_test_database_url_sync()
    config = _config(url)
    try:
        command.upgrade(config, "head")
        assert _applied_revisions(url) == ["0001"]

        command.downgrade(config, "base")
        assert _applied_revisions(url) == []
    finally:
        command.downgrade(config, "base")
