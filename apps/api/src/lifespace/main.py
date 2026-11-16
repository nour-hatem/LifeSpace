"""Composition root for the LifeSpace API.

This is the only module that wires infrastructure into the application. It
builds the engine, selects the readiness callable, registers handlers and
routes, and disposes the engine when the application shuts down. There is no
module-level application object.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from lifespace.api.errors import register_error_handlers
from lifespace.api.health import ReadyCheck
from lifespace.api.health import router as health_router
from lifespace.config import Settings
from lifespace.infrastructure.db import check_database, create_engine
from lifespace.infrastructure.logging import configure_logging


def create_app(
    settings: Settings | None = None,
    *,
    ready_check: ReadyCheck | None = None,
) -> FastAPI:
    """Build the application, optionally injecting settings and readiness."""
    resolved = settings or Settings()
    configure_logging(resolved.log_level)

    engine: AsyncEngine | None = None
    selected_ready_check: ReadyCheck
    if ready_check is not None:
        selected_ready_check = ready_check
    else:
        engine = create_engine(resolved.database_url)
        selected_ready_check = partial(check_database, engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.ready_check = selected_ready_check
        try:
            yield
        finally:
            if engine is not None:
                await engine.dispose()

    app = FastAPI(title="LifeSpace API", version="0.0.0", lifespan=lifespan)
    app.state.ready_check = selected_ready_check
    register_error_handlers(app)
    app.include_router(health_router)
    return app
