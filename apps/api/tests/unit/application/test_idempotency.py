"""Tests for idempotent creation (ADR 0002 item 14)."""

from __future__ import annotations

from uuid import UUID

import pytest

from lifespace.application.errors import IdempotencyKeyReuseError, ValidationFailedError
from lifespace.application.models import CreateTaskCommand, IdempotencyInput
from lifespace.application.ports import UnitOfWorkFactory
from lifespace.application.tasks import create_task
from tests.unit.application.fakes import FakeClock, InMemoryStore, SequentialIdGenerator

FIRST = IdempotencyInput(key="key-1", fingerprint="fingerprint-1")
REPLAY = IdempotencyInput(key="key-1", fingerprint="fingerprint-1")
OTHER = IdempotencyInput(key="key-1", fingerprint="fingerprint-2")


async def test_first_call_with_a_key_creates_the_task(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A new key creates the task and stores the record (ADR 0002 item 14)."""
    result = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(title="Write report"),
        idempotency=FIRST,
    )

    assert result.replayed is False
    assert len(store.tasks) == 1
    assert store.idempotency["key-1"].request_fingerprint == "fingerprint-1"
    assert store.idempotency["key-1"].task_id == result.view.stored.task.id


async def test_same_key_and_fingerprint_replays_the_task(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """A retry returns the original task and writes nothing (ADR 0002 item 14)."""
    first = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(title="Write report"),
        idempotency=FIRST,
    )
    replay = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(title="Write report"),
        idempotency=REPLAY,
    )

    assert replay.replayed is True
    assert replay.view.stored.task.id == first.view.stored.task.id
    assert len(store.tasks) == 1


async def test_same_key_with_another_fingerprint_is_rejected(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A key cannot be reused for a different request (ADR 0002 item 14)."""
    await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(title="Write report"),
        idempotency=FIRST,
    )

    with pytest.raises(IdempotencyKeyReuseError):
        await create_task(
            uow_factory,
            clock,
            ids,
            CreateTaskCommand(title="Another report"),
            idempotency=OTHER,
        )


async def test_replay_after_soft_delete_is_rejected(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
) -> None:
    """A key whose task was deleted counts as used (ADR 0002 item 14)."""
    created = await create_task(
        uow_factory,
        clock,
        ids,
        CreateTaskCommand(title="Write report"),
        idempotency=FIRST,
    )
    await _soft_delete(uow_factory, clock, created.view.stored.task.id)

    with pytest.raises(IdempotencyKeyReuseError):
        await create_task(
            uow_factory,
            clock,
            ids,
            CreateTaskCommand(title="Write report"),
            idempotency=REPLAY,
        )


async def test_a_failed_creation_leaves_no_record(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    ids: SequentialIdGenerator,
    store: InMemoryStore,
) -> None:
    """Validation runs before any write, so the key stays free (ADR 0002 item 14)."""
    with pytest.raises(ValidationFailedError):
        await create_task(
            uow_factory,
            clock,
            ids,
            CreateTaskCommand(title=""),
            idempotency=FIRST,
        )

    assert store.idempotency == {}


async def _soft_delete(
    uow_factory: UnitOfWorkFactory,
    clock: FakeClock,
    task_id: UUID,
) -> None:
    """Soft delete a task directly through the port (ADR 0002 item 5)."""
    async with uow_factory() as uow:
        await uow.tasks.soft_delete(task_id, expected_version=1, now=clock.now())
        await uow.commit()
