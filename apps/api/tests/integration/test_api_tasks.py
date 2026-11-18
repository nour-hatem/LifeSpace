"""End-to-end API tests against the local PostgreSQL test database (ADR 0002 items 4 to 15)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, Response

from lifespace.config import Settings
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


async def _create(
    client: AsyncClient,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    return await client.post(TASK_PATH, json=body or {"title": "Integration task"}, headers=headers)


async def _created(client: AsyncClient, body: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await _create(client, body)
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


async def test_full_lifecycle_flow(client: AsyncClient) -> None:
    created = await _created(client, {"title": "Lifecycle"})
    task_id = created["id"]

    listed = await client.get(TASK_PATH)
    assert [item["id"] for item in listed.json()["items"]] == [task_id]

    patched = await client.patch(f"{TASK_PATH}/{task_id}", json={"version": 1, "title": "Renamed"})
    assert patched.status_code == 200
    assert patched.json()["version"] == 2

    started = await client.post(f"{TASK_PATH}/{task_id}/start", json={"version": 2})
    completed = await client.post(f"{TASK_PATH}/{task_id}/complete", json={"version": 3})
    history = await client.get(f"{TASK_PATH}/{task_id}/history")
    reopened = await client.post(f"{TASK_PATH}/{task_id}/reopen", json={"version": 4})
    canceled = await client.post(
        f"{TASK_PATH}/{task_id}/cancel",
        json={"version": 5, "reason": "no longer relevant"},
    )

    assert started.json()["status"] == "in_progress"
    assert completed.json()["status"] == "completed"
    assert [item["to_status"] for item in history.json()["items"]] == [
        "completed",
        "in_progress",
    ]
    assert reopened.json()["status"] == "planned"
    assert canceled.json()["status"] == "canceled"
    assert canceled.json()["cancellation_reason"] == "no longer relevant"

    deleted = await client.delete(f"{TASK_PATH}/{task_id}", params={"version": 6})
    assert deleted.status_code == 204
    assert (await client.get(f"{TASK_PATH}/{task_id}")).status_code == 404
    assert (await client.get(TASK_PATH)).json()["items"] == []


async def test_stale_version_and_missing_task(client: AsyncClient) -> None:
    created = await _created(client)
    task_id = created["id"]

    updated = await client.patch(f"{TASK_PATH}/{task_id}", json={"version": 1, "title": "New"})
    stale = await client.patch(f"{TASK_PATH}/{task_id}", json={"version": 1, "title": "Old"})

    assert updated.status_code == 200
    assert stale.status_code == 409
    assert stale.headers["content-type"] == "application/problem+json"
    assert stale.json()["code"] == "stale_version"
    assert stale.json()["result"] == "conflict"
    assert stale.json()["current_version"] == 2

    missing = await client.get(f"{TASK_PATH}/00000000-0000-0000-0000-000000000099")
    assert missing.status_code == 404
    assert missing.json()["result"] == "not_found"


async def test_idempotency_replay(client: AsyncClient) -> None:
    headers = {"Idempotency-Key": "integration-key"}

    first = await _create(client, {"title": "Replay me"}, headers)
    replay = await _create(client, {"title": "Replay me"}, headers)
    reused = await _create(client, {"title": "Other"}, headers)

    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.headers["idempotency-replayed"] == "true"
    assert replay.json()["id"] == first.json()["id"]
    assert len((await client.get(TASK_PATH)).json()["items"]) == 1
    assert reused.status_code == 422
    assert reused.json()["code"] == "idempotency_key_reuse"


async def test_pagination_across_25_tasks(client: AsyncClient) -> None:
    created_ids = [
        (await _created(client, {"title": f"Task {index}"}))["id"] for index in range(25)
    ]

    collected: list[str] = []
    cursor: str | None = None
    while True:
        params: dict[str, Any] = {"limit": 10}
        if cursor is not None:
            params["cursor"] = cursor
        page = await client.get(TASK_PATH, params=params)
        assert page.status_code == 200
        collected.extend(item["id"] for item in page.json()["items"])
        cursor = page.json()["next_cursor"]
        if cursor is None:
            break

    assert len(collected) == 25
    assert set(collected) == set(created_ids)


async def test_settings_timezone_flips_overdue_near_spring_forward(
    client: AsyncClient,
    clock: FakeClock,
) -> None:
    clock.set(datetime(2026, 4, 23, 22, 30, tzinfo=UTC))
    created = await _created(
        client,
        {"title": "Cairo deadline", "deadline": {"kind": "date", "value": "2026-04-23"}},
    )
    assert created["is_overdue"] is False

    updated = await client.put("/api/v1/settings", json={"timezone": "Africa/Cairo"})
    fetched = await client.get(f"{TASK_PATH}/{created['id']}")

    assert updated.json() == {"timezone": "Africa/Cairo"}
    assert fetched.json()["is_overdue"] is True


async def test_concurrent_patch_allows_exactly_one_winner(client: AsyncClient) -> None:
    created = await _created(client)
    task_id = created["id"]

    first, second = await asyncio.gather(
        client.patch(f"{TASK_PATH}/{task_id}", json={"version": 1, "title": "First"}),
        client.patch(f"{TASK_PATH}/{task_id}", json={"version": 1, "title": "Second"}),
    )

    assert sorted([first.status_code, second.status_code]) == [200, 409]
    conflict = first if first.status_code == 409 else second
    assert conflict.json()["result"] == "conflict"
    assert conflict.json()["current_version"] == 2
    final = await client.get(f"{TASK_PATH}/{task_id}")
    assert final.json()["version"] == 2
