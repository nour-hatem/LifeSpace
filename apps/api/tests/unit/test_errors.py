"""Tests for problem+json error handling."""

import logging

from fastapi import FastAPI
from httpx import Response
from pytest import LogCaptureFixture

from lifespace.config import Settings
from lifespace.main import create_app
from tests.conftest import ClientFactory


async def _ready() -> bool:
    return True


def _app_with_validation_route(settings: Settings) -> FastAPI:
    app = create_app(settings, ready_check=_ready)

    @app.get("/api/_test/echo")
    async def echo(value: int) -> dict[str, int]:
        return {"value": value}

    return app


def _app_with_failing_route(settings: Settings) -> FastAPI:
    app = create_app(settings, ready_check=_ready)

    @app.get("/api/_test/boom")
    async def boom() -> dict[str, str]:
        raise RuntimeError("secret internal detail")

    return app


async def test_unknown_route_returns_problem_json(
    settings: Settings, client_factory: ClientFactory
) -> None:
    app = create_app(settings, ready_check=_ready)
    async with client_factory(app) as client:
        response: Response = await client.get("/api/nope")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "urn:lifespace:problem:not_found"
    assert body["title"] == "Not Found"
    assert body["status"] == 404
    assert body["detail"]
    assert body["code"] == "not_found"


async def test_validation_failure_returns_validation_failed(
    settings: Settings, client_factory: ClientFactory
) -> None:
    app = _app_with_validation_route(settings)
    async with client_factory(app) as client:
        response: Response = await client.get("/api/_test/echo", params={"value": "not-a-number"})

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "urn:lifespace:problem:validation_failed"
    assert body["status"] == 422
    assert body["detail"] == "Request validation failed."
    assert body["code"] == "validation_failed"
    assert "not-a-number" not in response.text


async def test_unhandled_error_is_generic_and_logged(
    settings: Settings,
    client_factory: ClientFactory,
    caplog: LogCaptureFixture,
) -> None:
    app = _app_with_failing_route(settings)
    with caplog.at_level(logging.ERROR):
        async with client_factory(app) as client:
            response: Response = await client.get("/api/_test/boom")

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "urn:lifespace:problem:failed"
    assert body["detail"] == "Internal server error"
    assert body["code"] == "failed"
    assert "secret internal detail" not in response.text
    assert "secret internal detail" in caplog.text
