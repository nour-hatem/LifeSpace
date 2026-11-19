"""Hostile-input regression tests for the HTTP bounds (ADR 0002 items 20, 21, and 24).

The application is built with the in-memory fakes from the application tests,
so no database is touched. Every case must return the documented problem
response and never a 500.
"""

from __future__ import annotations

import base64
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, Response

from lifespace.application.ports import UnitOfWorkFactory
from lifespace.config import Settings
from lifespace.main import create_app
from tests.conftest import ClientFactory
from tests.unit.application.fakes import (
    FakeClock,
    InMemoryStore,
    InMemoryUnitOfWork,
    SequentialIdGenerator,
)

NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)
TASK_PATH = "/api/v1/tasks"
PROBLEM = "application/problem+json"


async def _ready() -> bool:
    return True


def _factory(store: InMemoryStore) -> UnitOfWorkFactory:
    def create() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(store)

    return create


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def ids() -> SequentialIdGenerator:
    return SequentialIdGenerator()


@pytest.fixture
def api_app(
    settings: Settings,
    store: InMemoryStore,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> FastAPI:
    return create_app(
        settings,
        ready_check=_ready,
        uow_factory=_factory(store),
        clock=clock,
        ids=ids,
    )


@pytest.fixture
async def client(api_app: FastAPI, client_factory: ClientFactory) -> AsyncIterator[AsyncClient]:
    async with client_factory(api_app) as running:
        yield running


async def _create(
    client: AsyncClient,
    body: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> Response:
    return await client.post(TASK_PATH, json=body, headers=headers)


async def _created(client: AsyncClient, body: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await _create(client, body or {"title": "Boundary task"})
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


def _assert_problem(response: Response, status_code: int, result: str) -> dict[str, Any]:
    assert response.status_code == status_code, response.text
    assert response.headers["content-type"] == PROBLEM
    body: dict[str, Any] = response.json()
    assert body["status"] == status_code
    assert body["result"] == result
    assert body["type"] == f"urn:lifespace:problem:{body['code']}"
    return body


def _b64(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


DEEP_CURSOR = _b64(b"[" * 5000)
OUT_OF_RANGE_CURSOR = f"0001-01-01T00:00:00+14:00|{UUID(int=1)}"
BAD_UUID_CURSOR = "2026-01-01T00:00:00+00:00|not-a-uuid"
HOSTILE_CURSORS = [DEEP_CURSOR, "héllo", OUT_OF_RANGE_CURSOR, BAD_UUID_CURSOR]

HOSTILE_CREATIONS: list[dict[str, Any]] = [
    {"title": "a\x00b"},
    {"title": "x", "description": "a\x00b"},
    {"title": "x" * 501},
    {"title": "x", "description": "d" * 20_001},
    {"title": ""},
    {"title": "   "},
    {"title": "x", "estimate_minutes": 10**12},
    {"title": "x", "deadline": {"kind": "date", "value": "9999-12-31"}},
    {
        "title": "x",
        "deadline": {"kind": "datetime", "value": "0001-01-01T00:00:00+05:00"},
    },
    {
        "title": "x",
        "scheduled": {
            "start": "0001-01-01T00:00:00+05:00",
            "end": "0001-01-01T01:00:00+05:00",
        },
    },
]


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"title": "a\x00b"}, "title"),
        ({"title": "x", "description": "a\x00b"}, "description"),
        ({"title": "x" * 501}, "title"),
        ({"title": "x", "description": "d" * 20_001}, "description"),
        ({"title": ""}, "title"),
        ({"title": "   "}, "title"),
    ],
)
async def test_create_rejects_unstorable_text(
    client: AsyncClient,
    body: dict[str, Any],
    field: str,
) -> None:
    problem = _assert_problem(await _create(client, body), 422, "validation_failed")

    assert problem["field"] == field


async def test_create_rejects_a_lone_surrogate(client: AsyncClient) -> None:
    response = await client.post(
        TASK_PATH,
        content=b'{"title": "\\ud800"}',
        headers={"Content-Type": "application/json"},
    )

    problem = _assert_problem(response, 422, "validation_failed")
    assert problem["field"] == "title"


@pytest.mark.parametrize("estimate", [0, -1, 2_147_483_648, 10**12, 1.5, True])
async def test_create_rejects_an_out_of_range_estimate(
    client: AsyncClient,
    estimate: int | float | bool,
) -> None:
    response = await _create(client, {"title": "x", "estimate_minutes": estimate})

    _assert_problem(response, 422, "validation_failed")


@pytest.mark.parametrize("value", ["9999-12-31", "0001-01-01", "1969-12-31", "3000-01-01"])
async def test_create_rejects_an_out_of_range_date_deadline(
    client: AsyncClient,
    value: str,
) -> None:
    response = await _create(client, {"title": "x", "deadline": {"kind": "date", "value": value}})

    _assert_problem(response, 422, "validation_failed")


@pytest.mark.parametrize(
    "value",
    [
        "0001-01-01T00:00:00+05:00",
        "9999-12-31T23:59:59-05:00",
        "1969-12-31T23:59:59Z",
        "3000-01-01T00:00:00Z",
    ],
)
async def test_create_rejects_an_out_of_range_datetime_deadline(
    client: AsyncClient,
    value: str,
) -> None:
    response = await _create(
        client,
        {"title": "x", "deadline": {"kind": "datetime", "value": value}},
    )

    _assert_problem(response, 422, "validation_failed")


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("0001-01-01T00:00:00+05:00", "0001-01-01T01:00:00+05:00"),
        ("9999-12-31T22:59:59Z", "9999-12-31T23:59:59Z"),
        ("1969-12-31T23:59:59Z", "1970-01-01T00:00:00Z"),
        ("3000-01-01T00:00:00Z", "3000-01-01T01:00:00Z"),
    ],
)
async def test_create_rejects_an_out_of_range_schedule(
    client: AsyncClient,
    start: str,
    end: str,
) -> None:
    response = await _create(
        client,
        {"title": "x", "scheduled": {"start": start, "end": end}},
    )

    _assert_problem(response, 422, "validation_failed")


@pytest.mark.parametrize(
    "body",
    [
        {"title": "x", "deadline": {"kind": "date", "value": "2999-12-31"}},
        {"title": "x", "deadline": {"kind": "date", "value": "1970-01-01"}},
        {"title": "t" * 500},
        {"title": "x", "description": "d" * 20_000},
        {"title": "x", "estimate_minutes": 2_147_483_647},
    ],
)
async def test_create_accepts_the_inclusive_bounds(
    client: AsyncClient,
    body: dict[str, Any],
) -> None:
    response = await _create(client, body)

    assert response.status_code == 201, response.text


@pytest.mark.parametrize("version", [0, 2_147_483_648, 2**70])
async def test_mutations_reject_out_of_range_versions(
    client: AsyncClient,
    version: int,
) -> None:
    created = await _created(client)
    task_id = created["id"]

    patched = await client.patch(
        f"{TASK_PATH}/{task_id}",
        json={"version": version, "title": "x"},
    )
    completed = await client.post(
        f"{TASK_PATH}/{task_id}/complete",
        json={"version": version},
    )
    deleted = await client.delete(f"{TASK_PATH}/{task_id}", params={"version": version})

    for response in (patched, completed, deleted):
        _assert_problem(response, 422, "validation_failed")


async def test_cancel_reason_length_is_bounded(client: AsyncClient) -> None:
    created = await _created(client)
    task_id = created["id"]

    rejected = await client.post(
        f"{TASK_PATH}/{task_id}/cancel",
        json={"version": 1, "reason": "r" * 1_001},
    )
    accepted = await client.post(
        f"{TASK_PATH}/{task_id}/cancel",
        json={"version": 1, "reason": "r" * 1_000},
    )

    _assert_problem(rejected, 422, "validation_failed")
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["cancellation_reason"] == "r" * 1_000


@pytest.mark.parametrize("cursor", HOSTILE_CURSORS)
async def test_list_rejects_a_hostile_cursor(client: AsyncClient, cursor: str) -> None:
    problem = _assert_problem(
        await client.get(TASK_PATH, params={"cursor": cursor}),
        422,
        "validation_failed",
    )

    assert problem["code"] == "invalid_cursor"


@pytest.mark.parametrize("cursor", HOSTILE_CURSORS)
async def test_history_rejects_a_hostile_cursor(client: AsyncClient, cursor: str) -> None:
    created = await _created(client)

    problem = _assert_problem(
        await client.get(
            f"{TASK_PATH}/{created['id']}/history",
            params={"cursor": cursor},
        ),
        422,
        "validation_failed",
    )

    assert problem["code"] == "invalid_cursor"


async def test_rejected_creations_never_poison_the_list(client: AsyncClient) -> None:
    for body in HOSTILE_CREATIONS:
        _assert_problem(await _create(client, body), 422, "validation_failed")

    surrogate = await client.post(
        TASK_PATH,
        content=b'{"title": "\\ud800"}',
        headers={"Content-Type": "application/json"},
    )
    _assert_problem(surrogate, 422, "validation_failed")

    listed = await client.get(TASK_PATH)
    assert listed.status_code == 200, listed.text
    assert listed.json()["items"] == []

    valid = await _created(client, {"title": "Valid after rejections"})
    after = await client.get(TASK_PATH)

    assert after.status_code == 200, after.text
    assert [item["id"] for item in after.json()["items"]] == [valid["id"]]


async def test_rejected_idempotent_create_leaves_the_key_unused(client: AsyncClient) -> None:
    headers = {"Idempotency-Key": "hostile-create"}

    rejected = await _create(client, {"title": "bad\x00title"}, headers)
    accepted = await _create(client, {"title": "Accepted"}, headers)

    _assert_problem(rejected, 422, "validation_failed")
    assert accepted.status_code == 201, accepted.text


@pytest.mark.parametrize("zone", ["A" * 65, "UTC\x00"])
async def test_settings_rejects_unstorable_timezones(
    client: AsyncClient,
    zone: str,
) -> None:
    problem = _assert_problem(
        await client.put("/api/v1/settings", json={"timezone": zone}),
        422,
        "validation_failed",
    )

    assert problem["field"] == "timezone"
