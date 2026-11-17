"""Property test over randomised mutation sequences (ADR 0002 items 2 to 6)."""

from __future__ import annotations

import asyncio
from dataclasses import fields
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lifespace.application.errors import ApplicationError, NotFoundError
from lifespace.application.models import (
    CreateTaskCommand,
    StoredStatusEvent,
    StoredTask,
    TaskChanges,
    TaskFilter,
)
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.tasks import (
    create_task,
    delete_task,
    edit_task,
    get_task,
    list_task_events,
    list_tasks,
    transition_task,
)
from lifespace.domain.task import Task, TaskStatus
from tests.unit.application.fakes import (
    FakeClock,
    InMemoryStore,
    InMemoryUnitOfWork,
    SequentialIdGenerator,
)

BASE = datetime(2026, 1, 1, tzinfo=UTC)
MISSING = UUID(int=10_000)

OPERATIONS = [
    "create",
    "edit_title",
    "edit_estimate",
    "start",
    "complete",
    "cancel",
    "reopen",
    "delete",
]

TRANSITIONS: dict[str, TaskStatus] = {
    "start": TaskStatus.IN_PROGRESS,
    "complete": TaskStatus.COMPLETED,
    "cancel": TaskStatus.CANCELED,
    "reopen": TaskStatus.PLANNED,
}


def _factory(store: InMemoryStore) -> UnitOfWorkFactory:
    """Return a factory that opens a transaction over ``store``."""

    def create() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(store)

    return create


def _snapshot(
    store: InMemoryStore,
) -> tuple[dict[UUID, StoredTask], dict[UUID, datetime], dict[UUID, list[StoredStatusEvent]]]:
    """Copy the three mutable parts of the store for an unchanged assertion."""
    return (
        dict(store.tasks),
        dict(store.deleted_at),
        {task_id: list(events) for task_id, events in store.events.items()},
    )


@given(
    operations=st.lists(
        st.tuples(st.sampled_from(OPERATIONS), st.booleans()),
        max_size=15,
    )
)
def test_random_mutation_sequences_keep_the_invariants(
    operations: list[tuple[str, bool]],
) -> None:
    """Any create, edit, transition, and delete sequence keeps the rules (ADR 0002 item 4)."""
    asyncio.run(_run_sequence(operations))


async def _run_sequence(operations: list[tuple[str, bool]]) -> None:
    """Run one generated sequence and assert every invariant after each step (ADR 0002 item 2)."""
    store = InMemoryStore()
    clock = FakeClock()
    ids = SequentialIdGenerator()
    uow_factory = _factory(store)
    current_id: UUID | None = None
    current_version = 0
    successful_transitions = 0

    for index, (operation, wrong_version) in enumerate(operations, start=1):
        clock.set(BASE + timedelta(minutes=index))
        before = _snapshot(store)
        target_id = current_id if current_id is not None else MISSING
        expected_version = current_version + 3 if wrong_version else current_version
        succeeded = True

        try:
            if operation == "create":
                result = await create_task(
                    uow_factory,
                    clock,
                    ids,
                    CreateTaskCommand(title=f"Task {index}"),
                )
                current_id = result.view.stored.task.id
                current_version = result.view.stored.version
                assert current_version == 1
            elif operation == "edit_title":
                await edit_task(
                    uow_factory,
                    clock,
                    target_id,
                    expected_version,
                    TaskChanges(title=f"Title {index}"),
                )
            elif operation == "edit_estimate":
                await edit_task(
                    uow_factory,
                    clock,
                    target_id,
                    expected_version,
                    TaskChanges(estimate_minutes=index),
                )
            elif operation == "delete":
                await delete_task(uow_factory, clock, target_id, expected_version)
            else:
                await transition_task(
                    uow_factory,
                    clock,
                    ids,
                    target_id,
                    TRANSITIONS[operation],
                    expected_version,
                )
        except ApplicationError:
            succeeded = False
            assert _snapshot(store) == before

        if succeeded and operation != "create":
            assert store.tasks[target_id].version == current_version + 1
            if operation == "delete":
                assert target_id in store.deleted_at
            else:
                current_version += 1
                if operation in TRANSITIONS:
                    successful_transitions += 1

        assert sum(len(events) for events in store.events.values()) == successful_transitions
        _assert_domain_invariants(store)
        await _assert_deleted_are_invisible(uow_factory, clock, store)


def _assert_domain_invariants(store: InMemoryStore) -> None:
    """Rebuild every stored task so its domain invariants run again (ADR 0001 item 14)."""
    for stored in store.tasks.values():
        task = stored.task
        rebuilt = Task(**{field.name: getattr(task, field.name) for field in fields(task)})
        assert rebuilt == task
        assert stored.version >= 1


async def _assert_deleted_are_invisible(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    store: InMemoryStore,
) -> None:
    """Every deleted task is absent from reads and listings (ADR 0002 item 5)."""
    for task_id in store.deleted_at:
        with pytest.raises(NotFoundError):
            await get_task(uow_factory, clock, task_id)
        with pytest.raises(NotFoundError):
            await list_task_events(uow_factory, task_id, limit=10)
    page = await list_tasks(uow_factory, clock, TaskFilter(), limit=200)
    visible = {view.stored.task.id for view in page.items}
    assert not visible & set(store.deleted_at)
