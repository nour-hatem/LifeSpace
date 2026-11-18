"""Composition root for the LifeSpace API.

This is the only module that wires infrastructure into the application. It
builds the engine when it is needed, selects the readiness callable, the unit
of work factory, the clock, and the id generator, registers handlers and
routes, and disposes the engine when the application shuts down. There is no
module-level application object.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncEngine

from lifespace.api.errors import register_error_handlers
from lifespace.api.health import ReadyCheck
from lifespace.api.health import router as health_router
from lifespace.api.tasks import router as tasks_router
from lifespace.application.ports import Clock, IdGenerator, UnitOfWorkFactory
from lifespace.config import Settings
from lifespace.infrastructure.db import check_database, create_engine, create_session_factory
from lifespace.infrastructure.logging import configure_logging
from lifespace.infrastructure.system import SystemClock, Uuid7Generator
from lifespace.infrastructure.unit_of_work import create_unit_of_work_factory


def _operation_id(route: APIRoute) -> str:
    """Use the endpoint function name as the OpenAPI operation id (ADR 0002 item 18)."""
    return route.name


def create_app(
    settings: Settings | None = None,
    *,
    ready_check: ReadyCheck | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    clock: Clock | None = None,
    ids: IdGenerator | None = None,
) -> FastAPI:
    """Build the application, injecting settings, ports, and readiness for tests."""
    resolved = settings or Settings()
    configure_logging(resolved.log_level)

    selected_clock: Clock = clock if clock is not None else SystemClock()
    selected_ids: IdGenerator = ids if ids is not None else Uuid7Generator()

    engine: AsyncEngine | None = None
    if ready_check is None or uow_factory is None:
        engine = create_engine(resolved.database_url)

    if ready_check is not None:
        selected_ready_check = ready_check
    else:
        assert engine is not None
        selected_ready_check = partial(check_database, engine)

    if uow_factory is not None:
        selected_uow_factory = uow_factory
    else:
        assert engine is not None
        selected_uow_factory = create_unit_of_work_factory(create_session_factory(engine))

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            if engine is not None:
                await engine.dispose()

    app = FastAPI(
        title="LifeSpace API",
        version="0.0.0",
        lifespan=lifespan,
        generate_unique_id_function=_operation_id,
    )
    app.state.ready_check = selected_ready_check
    app.state.uow_factory = selected_uow_factory
    app.state.clock = selected_clock
    app.state.ids = selected_ids
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(tasks_router)
    return app
