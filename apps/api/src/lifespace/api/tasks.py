"""The versioned task and settings HTTP routes (ADR 0002 items 8 to 16).

Every route reads the unit of work factory, the clock, and the id generator
from the application state wired by the composition root. The router only
translates HTTP into use case calls; domain rules stay in the application and
domain layers.
"""

from __future__ import annotations

import hashlib
import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status

from lifespace.api.errors import PROBLEM_MEDIA_TYPE
from lifespace.api.mapping import (
    create_command,
    event_out,
    settings_out,
    task_changes,
    task_out,
)
from lifespace.api.schemas import (
    ActionBody,
    CancelBody,
    EventPage,
    ProblemOut,
    SettingsBody,
    SettingsOut,
    TaskCreate,
    TaskOut,
    TaskPage,
    TaskPatch,
)
from lifespace.application import settings as settings_use_cases
from lifespace.application import tasks as task_use_cases
from lifespace.application.models import IdempotencyInput, TaskFilter
from lifespace.application.ports import Clock, IdGenerator, UnitOfWorkFactory
from lifespace.domain.limits import MAX_INT32
from lifespace.domain.task import Category, Priority, TaskStatus

router = APIRouter(prefix="/api/v1")


def _problem_response_spec(description: str) -> dict[str, Any]:
    """Describe a declared problem+json response for OpenAPI (ADR 0002 item 13)."""
    return {
        "description": description,
        "content": {PROBLEM_MEDIA_TYPE: {"schema": ProblemOut.model_json_schema()}},
    }


PROBLEM_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: _problem_response_spec("Not found"),
    409: _problem_response_spec("Conflict"),
    422: _problem_response_spec("Unprocessable entity"),
}

CREATE_RESPONSES: dict[int | str, dict[str, Any]] = {
    **PROBLEM_RESPONSES,
    200: {
        "description": "The original task for a replayed idempotency key",
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/TaskOut"}}},
    },
}


def get_uow_factory(request: Request) -> UnitOfWorkFactory:
    """Return the unit of work factory wired by the composition root (ADR 0002 item 2)."""
    uow_factory: UnitOfWorkFactory = request.app.state.uow_factory
    return uow_factory


def get_clock(request: Request) -> Clock:
    """Return the clock wired by the composition root (ADR 0002 item 1)."""
    clock: Clock = request.app.state.clock
    return clock


def get_ids(request: Request) -> IdGenerator:
    """Return the id generator wired by the composition root (ADR 0002 item 1)."""
    ids: IdGenerator = request.app.state.ids
    return ids


UowFactoryDep = Annotated[UnitOfWorkFactory, Depends(get_uow_factory)]
ClockDep = Annotated[Clock, Depends(get_clock)]
IdsDep = Annotated[IdGenerator, Depends(get_ids)]


def _fingerprint(body: TaskCreate) -> str:
    """Return the SHA-256 of the canonical validated body (ADR 0002 item 14)."""
    canonical = json.dumps(body.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@router.get("/tasks", response_model=TaskPage, responses=PROBLEM_RESPONSES)
async def list_tasks(
    uow_factory: UowFactoryDep,
    clock: ClockDep,
    statuses: Annotated[list[TaskStatus] | None, Query(alias="status")] = None,
    category: Category | None = None,
    priority: Priority | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    cursor: str | None = None,
) -> TaskPage:
    """Return one newest-first page of tasks (ADR 0002 items 15 and 16)."""
    task_filter = TaskFilter(
        statuses=frozenset(statuses or ()),
        category=category,
        priority=priority,
    )
    page = await task_use_cases.list_tasks(
        uow_factory,
        clock,
        task_filter,
        limit=limit,
        cursor=cursor,
    )
    return TaskPage(items=[task_out(view) for view in page.items], next_cursor=page.next_cursor)


@router.post(
    "/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    responses=CREATE_RESPONSES,
)
async def create_task(
    body: TaskCreate,
    response: Response,
    uow_factory: UowFactoryDep,
    clock: ClockDep,
    ids: IdsDep,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            min_length=1,
            max_length=200,
            pattern=r"^[\x20-\x7E]+$",
        ),
    ] = None,
) -> TaskOut:
    """Create a manual task, replaying a used idempotency key (ADR 0002 items 9 and 14)."""
    idempotency = (
        None
        if idempotency_key is None
        else IdempotencyInput(key=idempotency_key, fingerprint=_fingerprint(body))
    )
    result = await task_use_cases.create_task(
        uow_factory,
        clock,
        ids,
        create_command(body),
        idempotency=idempotency,
    )
    output = task_out(result.view)
    if result.replayed:
        response.status_code = status.HTTP_200_OK
        response.headers["Idempotency-Replayed"] = "true"
    else:
        response.headers["Location"] = f"/api/v1/tasks/{output.id}"
    return output


@router.get("/tasks/{task_id}", response_model=TaskOut, responses=PROBLEM_RESPONSES)
async def get_task(task_id: UUID, uow_factory: UowFactoryDep, clock: ClockDep) -> TaskOut:
    """Return one task with its overdue flag (ADR 0002 items 5 and 8)."""
    view = await task_use_cases.get_task(uow_factory, clock, task_id)
    return task_out(view)


@router.patch("/tasks/{task_id}", response_model=TaskOut, responses=PROBLEM_RESPONSES)
async def patch_task(
    task_id: UUID,
    body: TaskPatch,
    uow_factory: UowFactoryDep,
    clock: ClockDep,
) -> TaskOut:
    """Edit a task; null clears a field and an omitted field is kept (ADR 0002 item 10)."""
    view = await task_use_cases.edit_task(
        uow_factory,
        clock,
        task_id,
        body.version,
        task_changes(body),
    )
    return task_out(view)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=PROBLEM_RESPONSES,
)
async def delete_task(
    task_id: UUID,
    version: Annotated[int, Query(ge=1, le=MAX_INT32)],
    uow_factory: UowFactoryDep,
    clock: ClockDep,
) -> Response:
    """Soft delete a task at the expected version (ADR 0002 items 4 and 5)."""
    await task_use_cases.delete_task(uow_factory, clock, task_id, version)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/tasks/{task_id}/start", response_model=TaskOut, responses=PROBLEM_RESPONSES)
async def start_task(
    task_id: UUID,
    body: ActionBody,
    uow_factory: UowFactoryDep,
    clock: ClockDep,
    ids: IdsDep,
) -> TaskOut:
    """Move a task to in progress (ADR 0002 item 11)."""
    view = await task_use_cases.transition_task(
        uow_factory,
        clock,
        ids,
        task_id,
        TaskStatus.IN_PROGRESS,
        body.version,
    )
    return task_out(view)


@router.post("/tasks/{task_id}/plan", response_model=TaskOut, responses=PROBLEM_RESPONSES)
async def plan_task(
    task_id: UUID,
    body: ActionBody,
    uow_factory: UowFactoryDep,
    clock: ClockDep,
    ids: IdsDep,
) -> TaskOut:
    """Move a task back to planned (ADR 0002 item 11)."""
    view = await task_use_cases.transition_task(
        uow_factory,
        clock,
        ids,
        task_id,
        TaskStatus.PLANNED,
        body.version,
    )
    return task_out(view)


@router.post("/tasks/{task_id}/complete", response_model=TaskOut, responses=PROBLEM_RESPONSES)
async def complete_task(
    task_id: UUID,
    body: ActionBody,
    uow_factory: UowFactoryDep,
    clock: ClockDep,
    ids: IdsDep,
) -> TaskOut:
    """Complete a task and record its event (ADR 0002 items 6 and 11)."""
    view = await task_use_cases.transition_task(
        uow_factory,
        clock,
        ids,
        task_id,
        TaskStatus.COMPLETED,
        body.version,
    )
    return task_out(view)


@router.post("/tasks/{task_id}/cancel", response_model=TaskOut, responses=PROBLEM_RESPONSES)
async def cancel_task(
    task_id: UUID,
    body: CancelBody,
    uow_factory: UowFactoryDep,
    clock: ClockDep,
    ids: IdsDep,
) -> TaskOut:
    """Cancel a task with an optional reason (ADR 0002 item 11)."""
    view = await task_use_cases.transition_task(
        uow_factory,
        clock,
        ids,
        task_id,
        TaskStatus.CANCELED,
        body.version,
        reason=body.reason,
    )
    return task_out(view)


@router.post("/tasks/{task_id}/reopen", response_model=TaskOut, responses=PROBLEM_RESPONSES)
async def reopen_task(
    task_id: UUID,
    body: ActionBody,
    uow_factory: UowFactoryDep,
    clock: ClockDep,
    ids: IdsDep,
) -> TaskOut:
    """Reopen a completed or canceled task to planned (ADR 0002 item 11)."""
    view = await task_use_cases.transition_task(
        uow_factory,
        clock,
        ids,
        task_id,
        TaskStatus.PLANNED,
        body.version,
    )
    return task_out(view)


@router.get("/tasks/{task_id}/history", response_model=EventPage, responses=PROBLEM_RESPONSES)
async def list_task_history(
    task_id: UUID,
    uow_factory: UowFactoryDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    cursor: str | None = None,
) -> EventPage:
    """Return one newest-first page of a task's status events (ADR 0002 item 15)."""
    page = await task_use_cases.list_task_events(uow_factory, task_id, limit=limit, cursor=cursor)
    return EventPage(
        items=[event_out(stored) for stored in page.items],
        next_cursor=page.next_cursor,
    )


@router.get("/settings", response_model=SettingsOut, responses=PROBLEM_RESPONSES)
async def get_settings(uow_factory: UowFactoryDep) -> SettingsOut:
    """Return the stored settings (ADR 0002 item 8)."""
    return settings_out(await settings_use_cases.get_settings(uow_factory))


@router.put("/settings", response_model=SettingsOut, responses=PROBLEM_RESPONSES)
async def update_settings(
    body: SettingsBody,
    uow_factory: UowFactoryDep,
    clock: ClockDep,
) -> SettingsOut:
    """Validate and store the user's IANA time zone (ADR 0002 item 8)."""
    settings = await settings_use_cases.update_timezone(uow_factory, clock, body.timezone)
    return settings_out(settings)
