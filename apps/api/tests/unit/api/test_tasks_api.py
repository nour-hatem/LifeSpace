"""Unit tests for the versioned task and settings HTTP API (ADR 0002 items 8 to 16).

The application is built with the in-memory fakes from the application tests,
so no database is touched.
"""

from __future__ import annotations

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
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    return await client.post(TASK_PATH, json=body or {"title": "Write the plan"}, headers=headers)


async def _created(client: AsyncClient, body: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await _create(client, body)
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
    assert "traceback" not in response.text.lower()
    return body


async def test_create_returns_201_with_location_header(
    client: AsyncClient,
) -> None:
    response = await _create(client, {"title": "Write the plan"})

    assert response.status_code == 201
    body = response.json()
    assert response.headers["location"] == f"/api/v1/tasks/{body['id']}"
    assert body["title"] == "Write the plan"
    assert body["status"] == "planned"
    assert body["source"] == "manual"
    assert body["version"] == 1
    assert body["description"] is None
    assert body["created_at"] == "2026-01-01T12:00:00Z"
    assert body["is_overdue"] is False
    assert response.headers["content-type"] == "application/json"


async def test_create_accepts_inbox_status(client: AsyncClient) -> None:
    body = await _created(client, {"title": "Quick capture", "status": "inbox"})

    assert body["status"] == "inbox"


@pytest.mark.parametrize(
    "body",
    [
        {"title": ""},
        {"title": "x", "unknown": 1},
        {"title": "x", "deadline": {"kind": "datetime", "value": "2026-02-01T10:00:00"}},
        {"title": "x", "estimate_minutes": 0},
        {"title": "x", "status": "completed"},
        {"title": "x", "estimate_minutes": "30"},
    ],
)
async def test_create_rejects_invalid_bodies(client: AsyncClient, body: dict[str, Any]) -> None:
    _assert_problem(await _create(client, body), 422, "validation_failed")


async def test_empty_title_names_the_field(client: AsyncClient) -> None:
    body = _assert_problem(await _create(client, {"title": "   "}), 422, "validation_failed")

    assert body["field"] == "title"


async def test_create_accepts_both_deadline_kinds(client: AsyncClient) -> None:
    date_task = await _created(
        client,
        {"title": "Date", "deadline": {"kind": "date", "value": "2026-02-01"}},
    )
    datetime_task = await _created(
        client,
        {
            "title": "Instant",
            "deadline": {"kind": "datetime", "value": "2026-02-01T12:30:00+02:00"},
        },
    )

    assert date_task["deadline"] == {"kind": "date", "value": "2026-02-01"}
    assert datetime_task["deadline"] == {
        "kind": "datetime",
        "value": "2026-02-01T10:30:00Z",
    }


async def test_create_accepts_a_scheduled_interval(client: AsyncClient) -> None:
    body = await _created(
        client,
        {
            "title": "Scheduled",
            "scheduled": {
                "start": "2026-02-01T09:00:00+02:00",
                "end": "2026-02-01T10:00:00+02:00",
            },
        },
    )

    assert body["scheduled"] == {
        "start": "2026-02-01T07:00:00Z",
        "end": "2026-02-01T08:00:00Z",
    }


async def test_get_returns_the_task_and_404_for_unknown(client: AsyncClient) -> None:
    created = await _created(client)

    found = await client.get(f"{TASK_PATH}/{created['id']}")
    missing = await client.get(f"{TASK_PATH}/{UUID(int=99)}")

    assert found.status_code == 200
    assert found.json()["id"] == created["id"]
    body = _assert_problem(missing, 404, "not_found")
    assert body["code"] == "not_found"


async def test_list_filters_by_status_category_and_priority(client: AsyncClient) -> None:
    await _create(client, {"title": "Work", "category": "work", "priority": "high"})
    await _create(client, {"title": "Learn", "category": "learning", "priority": "low"})
    inbox = await _created(client, {"title": "Inbox", "status": "inbox"})

    by_category = await client.get(TASK_PATH, params={"category": "work"})
    by_priority = await client.get(TASK_PATH, params={"priority": "low"})
    by_status = await client.get(TASK_PATH, params={"status": "inbox"})
    both = await client.get(TASK_PATH, params=[("status", "planned"), ("status", "inbox")])

    assert [item["title"] for item in by_category.json()["items"]] == ["Work"]
    assert [item["title"] for item in by_priority.json()["items"]] == ["Learn"]
    assert [item["id"] for item in by_status.json()["items"]] == [inbox["id"]]
    assert len(both.json()["items"]) == 3


async def test_list_paginates_with_an_opaque_cursor(client: AsyncClient) -> None:
    first = await _created(client, {"title": "One"})
    second = await _created(client, {"title": "Two"})
    third = await _created(client, {"title": "Three"})

    page_one = await client.get(TASK_PATH, params={"limit": 2})
    assert page_one.status_code == 200
    assert [item["id"] for item in page_one.json()["items"]] == [third["id"], second["id"]]
    cursor = page_one.json()["next_cursor"]
    assert cursor

    page_two = await client.get(TASK_PATH, params={"limit": 2, "cursor": cursor})
    assert [item["id"] for item in page_two.json()["items"]] == [first["id"]]
    assert page_two.json()["next_cursor"] is None

    invalid = await client.get(TASK_PATH, params={"cursor": "not-a-cursor"})
    _assert_problem(invalid, 422, "validation_failed")


@pytest.mark.parametrize("limit", [0, 201])
async def test_list_rejects_an_out_of_range_limit(client: AsyncClient, limit: int) -> None:
    _assert_problem(await client.get(TASK_PATH, params={"limit": limit}), 422, "validation_failed")


async def test_patch_clears_null_and_keeps_omitted_fields(client: AsyncClient) -> None:
    created = await _created(
        client,
        {
            "title": "Before",
            "description": "Details",
            "estimate_minutes": 30,
            "deadline": {"kind": "date", "value": "2026-02-01"},
            "scheduled": {
                "start": "2026-02-01T09:00:00Z",
                "end": "2026-02-01T10:00:00Z",
            },
        },
    )

    response = await client.patch(
        f"{TASK_PATH}/{created['id']}",
        json={"version": 1, "title": "After", "description": None, "deadline": None},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "After"
    assert body["description"] is None
    assert body["deadline"] is None
    assert body["estimate_minutes"] == 30
    assert body["scheduled"] is not None
    assert body["version"] == 2


async def test_patch_with_only_version_is_rejected(client: AsyncClient) -> None:
    created = await _created(client)

    response = await client.patch(f"{TASK_PATH}/{created['id']}", json={"version": 1})

    _assert_problem(response, 422, "validation_failed")


async def test_patch_with_a_stale_version_reports_the_current_version(
    client: AsyncClient,
) -> None:
    created = await _created(client)

    response = await client.patch(f"{TASK_PATH}/{created['id']}", json={"version": 5, "title": "X"})

    body = _assert_problem(response, 409, "conflict")
    assert body["code"] == "stale_version"
    assert body["current_version"] == 1


async def test_patch_changes_deadline_schedule_and_estimate_independently(
    client: AsyncClient,
) -> None:
    created = await _created(client)

    estimated = await client.patch(
        f"{TASK_PATH}/{created['id']}", json={"version": 1, "estimate_minutes": 45}
    )
    deadline = await client.patch(
        f"{TASK_PATH}/{created['id']}",
        json={"version": 2, "deadline": {"kind": "date", "value": "2026-02-01"}},
    )
    scheduled = await client.patch(
        f"{TASK_PATH}/{created['id']}",
        json={
            "version": 3,
            "scheduled": {"start": "2026-02-01T09:00:00Z", "end": "2026-02-01T10:00:00Z"},
        },
    )

    assert estimated.json()["estimate_minutes"] == 45
    assert estimated.json()["deadline"] is None
    assert deadline.json()["deadline"] == {"kind": "date", "value": "2026-02-01"}
    assert deadline.json()["scheduled"] is None
    assert scheduled.json()["estimate_minutes"] == 45
    assert scheduled.json()["deadline"] == {"kind": "date", "value": "2026-02-01"}


async def test_delete_removes_the_task_and_checks_the_version(client: AsyncClient) -> None:
    first = await _created(client)
    second = await _created(client, {"title": "Second"})

    deleted = await client.delete(f"{TASK_PATH}/{first['id']}", params={"version": 1})
    assert deleted.status_code == 204
    assert deleted.content == b""

    _assert_problem(await client.get(f"{TASK_PATH}/{first['id']}"), 404, "not_found")
    listed = await client.get(TASK_PATH)
    assert [item["id"] for item in listed.json()["items"]] == [second["id"]]

    stale = await client.delete(f"{TASK_PATH}/{second['id']}", params={"version": 9})
    body = _assert_problem(stale, 409, "conflict")
    assert body["current_version"] == 1


async def test_delete_requires_the_version_query(client: AsyncClient) -> None:
    created = await _created(client)

    _assert_problem(await client.delete(f"{TASK_PATH}/{created['id']}"), 422, "validation_failed")


async def test_lifecycle_path_and_rejected_transition(client: AsyncClient) -> None:
    created = await _created(client)
    task_id = created["id"]

    started = await client.post(f"{TASK_PATH}/{task_id}/start", json={"version": 1})
    completed = await client.post(f"{TASK_PATH}/{task_id}/complete", json={"version": 2})
    rejected = await client.post(f"{TASK_PATH}/{task_id}/complete", json={"version": 3})
    reopened = await client.post(f"{TASK_PATH}/{task_id}/reopen", json={"version": 3})
    started_again = await client.post(f"{TASK_PATH}/{task_id}/start", json={"version": 4})
    planned = await client.post(f"{TASK_PATH}/{task_id}/plan", json={"version": 5})

    assert started.json()["status"] == "in_progress"
    assert started.json()["version"] == 2
    assert completed.json()["status"] == "completed"
    assert completed.json()["completed_at"] == "2026-01-01T12:00:00Z"
    body = _assert_problem(rejected, 409, "rejected")
    assert body["code"] == "invalid_transition"
    assert reopened.json()["status"] == "planned"
    assert reopened.json()["completed_at"] is None
    assert started_again.json()["status"] == "in_progress"
    assert planned.json()["status"] == "planned"


async def test_cancel_records_the_reason(client: AsyncClient) -> None:
    created = await _created(client)

    response = await client.post(
        f"{TASK_PATH}/{created['id']}/cancel",
        json={"version": 1, "reason": "  changed my mind  "},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "canceled"
    assert body["cancellation_reason"] == "changed my mind"
    assert body["canceled_at"] == "2026-01-01T12:00:00Z"


async def test_history_is_newest_first_and_paginates(client: AsyncClient) -> None:
    created = await _created(client)
    task_id = created["id"]
    await client.post(f"{TASK_PATH}/{task_id}/start", json={"version": 1})
    await client.post(f"{TASK_PATH}/{task_id}/complete", json={"version": 2})

    first_page = await client.get(f"{TASK_PATH}/{task_id}/history", params={"limit": 1})
    cursor = first_page.json()["next_cursor"]
    second_page = await client.get(
        f"{TASK_PATH}/{task_id}/history", params={"limit": 1, "cursor": cursor}
    )

    assert first_page.status_code == 200
    assert first_page.json()["items"][0]["to_status"] == "completed"
    assert second_page.json()["items"][0]["to_status"] == "in_progress"
    assert second_page.json()["next_cursor"] is None

    _assert_problem(
        await client.get(f"{TASK_PATH}/{UUID(int=99)}/history"),
        404,
        "not_found",
    )


async def test_settings_get_and_update(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/settings")).json() == {"timezone": "UTC"}

    updated = await client.put("/api/v1/settings", json={"timezone": "Africa/Cairo"})
    assert updated.status_code == 200
    assert updated.json() == {"timezone": "Africa/Cairo"}
    assert (await client.get("/api/v1/settings")).json() == {"timezone": "Africa/Cairo"}

    invalid = await client.put("/api/v1/settings", json={"timezone": "Mars/Olympus"})
    body = _assert_problem(invalid, 422, "validation_failed")
    assert body["field"] == "timezone"


async def test_is_overdue_follows_the_cairo_spring_forward(
    client: AsyncClient,
    clock: FakeClock,
) -> None:
    clock.set(datetime(2026, 4, 23, 22, 30, tzinfo=UTC))
    created = await _created(
        client,
        {"title": "Due", "deadline": {"kind": "date", "value": "2026-04-23"}},
    )
    assert created["is_overdue"] is False

    await client.put("/api/v1/settings", json={"timezone": "Africa/Cairo"})
    updated = await client.get(f"{TASK_PATH}/{created['id']}")

    assert updated.json()["is_overdue"] is True


async def test_idempotency_replays_the_same_body(client: AsyncClient) -> None:
    headers = {"Idempotency-Key": "create-once"}
    body = {"title": "Only once"}

    first = await _create(client, body, headers)
    replay = await _create(client, body, headers)

    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.headers["idempotency-replayed"] == "true"
    assert replay.json()["id"] == first.json()["id"]
    assert len((await client.get(TASK_PATH)).json()["items"]) == 1

    reused = await _create(client, {"title": "Different"}, headers)
    problem = _assert_problem(reused, 422, "rejected")
    assert problem["code"] == "idempotency_key_reuse"


async def test_idempotency_rejects_an_invalid_key_header(client: AsyncClient) -> None:
    response = await _create(client, headers={"Idempotency-Key": "a" * 201})

    _assert_problem(response, 422, "validation_failed")


async def test_application_errors_are_problem_json(client: AsyncClient) -> None:
    body = _assert_problem(await client.get(f"{TASK_PATH}/{UUID(int=99)}"), 404, "not_found")
    assert body["code"] == "not_found"


async def test_unexpected_failure_is_generic_and_never_leaks(
    settings: Settings,
    client_factory: ClientFactory,
) -> None:
    def failing_factory() -> InMemoryUnitOfWork:
        raise RuntimeError("secret internal detail")

    app = create_app(
        settings,
        ready_check=_ready,
        uow_factory=failing_factory,
        clock=FakeClock(),
        ids=SequentialIdGenerator(),
    )
    async with client_factory(app) as running:
        response = await running.get(f"{TASK_PATH}/{UUID(int=1)}")

    body = _assert_problem(response, 500, "failed")
    assert body["detail"] == "Internal server error"
    assert "secret internal detail" not in response.text
    assert "RuntimeError" not in response.text
