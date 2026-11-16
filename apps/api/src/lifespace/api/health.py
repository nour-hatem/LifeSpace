"""Health and readiness endpoints.

This module only answers HTTP health probes and reads the readiness callable
from the application state. It must not import ``lifespace.infrastructure`` or
SQLAlchemy, and it never exposes exception text or connection details.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

ReadyCheck = Callable[[], Awaitable[bool]]

router = APIRouter(prefix="/api", tags=["health"])


def get_ready_check(request: Request) -> ReadyCheck:
    """Return the readiness callable wired by the composition root."""
    ready_check: ReadyCheck = request.app.state.ready_check
    return ready_check


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe that never touches the database."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(
    ready_check: Annotated[ReadyCheck, Depends(get_ready_check)],
) -> JSONResponse:
    """Readiness probe backed by the configured readiness callable."""
    try:
        ready = await ready_check()
    except Exception as exc:  # noqa: BLE001 - a failed probe is reported as unavailable
        logger.warning("Readiness check raised: %s", type(exc).__name__)
        ready = False
    if ready:
        return JSONResponse({"status": "ready"}, status_code=status.HTTP_200_OK)
    return JSONResponse(
        {"status": "unavailable"},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
