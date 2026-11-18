"""Contract test for the generated OpenAPI document (ADR 0002 item 18)."""

from __future__ import annotations

from fastapi import FastAPI

from lifespace.config import Settings
from lifespace.main import create_app
from tests.unit.application.fakes import (
    InMemoryStore,
    InMemoryUnitOfWork,
    SequentialIdGenerator,
)

TASK_OPERATION_IDS = {
    "list_tasks",
    "create_task",
    "get_task",
    "patch_task",
    "delete_task",
    "start_task",
    "plan_task",
    "complete_task",
    "cancel_task",
    "reopen_task",
    "list_task_history",
    "get_settings",
    "update_settings",
}
PROBLEM_MEDIA_TYPE = "application/problem+json"


async def _ready() -> bool:
    return True


def _app(settings: Settings) -> FastAPI:
    store = InMemoryStore()
    return create_app(
        settings,
        ready_check=_ready,
        uow_factory=lambda: InMemoryUnitOfWork(store),
        ids=SequentialIdGenerator(),
    )


async def test_openapi_declares_operation_ids_and_responses(settings: Settings) -> None:
    document = _app(settings).openapi()
    operation_ids: set[str] = set()

    for path, operations in document["paths"].items():
        for method, operation in operations.items():
            operation_ids.add(operation["operationId"])
            responses = operation["responses"]
            assert responses, f"{method} {path} declares no response"

            if path.startswith("/api/v1/tasks"):
                for code in ("404", "409", "422"):
                    content = responses[code]["content"]
                    assert PROBLEM_MEDIA_TYPE in content

            if method == "delete":
                assert "204" in responses
            else:
                success_code = "201" if "201" in responses else "200"
                assert "application/json" in responses[success_code]["content"]
                assert "schema" in responses[success_code]["content"]["application/json"]

    assert operation_ids >= TASK_OPERATION_IDS
