"""Hostile-input regression tests against PostgreSQL (ADR 0002 items 20 to 24).

The hostile creations must be rejected before they reach storage, the list
endpoint must stay healthy afterwards, and no log record may contain task
content or SQL parameters.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text

from lifespace.config import Settings
from lifespace.infrastructure.db import create_engine
from lifespace.main import create_app
from tests.conftest import ClientFactory
from tests.integration.conftest import (
    require_test_database_url_sync,
    reset_database,
    run_alembic,
)
from tests.unit.application.fakes import FakeClock, SequentialIdGenerator

NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)
TASK_PATH = "/api/v1/tasks"
MARKER = "SECRET-TITLE-MARKER"

HOSTILE_BODIES: list[dict[str, Any]] = [
    {"title": f"{MARKER}\x00"},
    {"title": "x", "description": f"{MARKER}\x00"},
    {"title": MARKER, "estimate_minutes": 10**12},
    {"title": MARKER, "deadline": {"kind": "date", "value": "9999-12-31"}},
    {
        "title": MARKER,
        "deadline": {"kind": "datetime", "value": "0001-01-01T00:00:00+05:00"},
    },
    {"title": MARKER + "x" * 600},
]


@pytest.fixture(scope="module")
def database_url() -> str:
    """Upgrade the test database to head once for this module (ADR 0002 item 19)."""
    url = require_test_database_url_sync()
    result = run_alembic(url, "upgrade", "head")
    assert result.returncode == 0, result.stderr
    return url


@pytest.fixture
def clean_database(database_url: str) -> str:
    """Empty the M2 tables before each test (ADR 0002 items 5, 6, 8, and 14)."""
    reset_database(database_url)
    return database_url


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def api_app(clean_database: str, clock: FakeClock) -> FastAPI:
    return create_app(
        Settings(_env_file=None, database_url=clean_database),
        clock=clock,
        ids=SequentialIdGenerator(),
    )


@pytest.fixture
async def client(api_app: FastAPI, client_factory: ClientFactory) -> AsyncIterator[AsyncClient]:
    async with client_factory(api_app) as running:
        yield running


async def _count_tasks(url: str) -> int:
    """Return the number of rows in ``tasks`` (ADR 0002 items 20 and 22)."""
    engine = create_engine(url)
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("select count(*) from tasks"))
            return int(result.scalar_one())
    finally:
        await engine.dispose()


async def test_hostile_creations_store_nothing_and_keep_the_list_healthy(
    client: AsyncClient,
    clean_database: str,
) -> None:
    for body in HOSTILE_BODIES:
        assert (await client.post(TASK_PATH, json=body)).status_code == 422

    surrogate = await client.post(
        TASK_PATH,
        content=b'{"title": "SECRET-TITLE-MARKER\\ud800"}',
        headers={"Content-Type": "application/json"},
    )
    assert surrogate.status_code == 422

    assert await _count_tasks(clean_database) == 0
    listed = await client.get(TASK_PATH)
    assert listed.status_code == 200, listed.text
    assert listed.json()["items"] == []

    deleted = await client.delete(f"{TASK_PATH}/{UUID(int=1)}", params={"version": 2**70})
    assert deleted.status_code == 422
    assert deleted.headers["content-type"] == "application/problem+json"
    assert deleted.json()["result"] == "validation_failed"


async def test_hostile_run_logs_no_task_content(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    for body in HOSTILE_BODIES:
        assert (await client.post(TASK_PATH, json=body)).status_code == 422

    surrogate = await client.post(
        TASK_PATH,
        content=b'{"title": "SECRET-TITLE-MARKER\\ud800"}',
        headers={"Content-Type": "application/json"},
    )
    assert surrogate.status_code == 422

    assert MARKER not in caplog.text
    assert "[parameters:" not in caplog.text
