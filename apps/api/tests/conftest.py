"""Shared fixtures for the LifeSpace API unit tests."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from hypothesis import HealthCheck
from hypothesis import settings as hypothesis_settings

from lifespace.config import Settings

hypothesis_settings.register_profile(
    "lifespace",
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
hypothesis_settings.load_profile("lifespace")

UNREACHABLE_DATABASE_URL = "postgresql+asyncpg://user:password@127.0.0.1:9/unreachable"

ClientFactory = Callable[[FastAPI], AbstractAsyncContextManager[AsyncClient]]


@asynccontextmanager
async def _running_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Run the application lifespan and yield a client bound to it."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client


@pytest.fixture
def client_factory() -> ClientFactory:
    """Return a factory that runs an app and yields a client for it."""
    return _running_client


@pytest.fixture
def settings() -> Settings:
    """Return settings that never read the repository .env file."""
    return Settings(_env_file=None, database_url=UNREACHABLE_DATABASE_URL)
