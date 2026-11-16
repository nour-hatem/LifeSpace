"""Tests for the health and readiness endpoints."""

from httpx import Response

from lifespace.config import Settings
from lifespace.main import create_app
from tests.conftest import ClientFactory


async def _ready() -> bool:
    return True


async def _unavailable() -> bool:
    raise RuntimeError("postgresql://user:secret@127.0.0.1:5433/lifespace")


async def test_health_returns_ok(settings: Settings, client_factory: ClientFactory) -> None:
    app = create_app(settings, ready_check=_ready)
    async with client_factory(app) as client:
        response: Response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_returns_ready(settings: Settings, client_factory: ClientFactory) -> None:
    app = create_app(settings, ready_check=_ready)
    async with client_factory(app) as client:
        response: Response = await client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def test_ready_returns_unavailable_without_leaking_details(
    settings: Settings, client_factory: ClientFactory
) -> None:
    app = create_app(settings, ready_check=_unavailable)
    async with client_factory(app) as client:
        response: Response = await client.get("/api/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "secret" not in response.text
