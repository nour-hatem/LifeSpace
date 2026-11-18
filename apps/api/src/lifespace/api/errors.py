"""Problem+json error handling for the API (ADR 0002 items 12 and 13).

This module maps framework and application exceptions to RFC 9457 problem
documents. Every body carries a ``result`` member. It must not import
the infrastructure layer or SQLAlchemy, and error bodies must never contain
exception text, stack traces, SQL, or credentials.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from lifespace.application.errors import ApplicationError

logger = logging.getLogger(__name__)

PROBLEM_MEDIA_TYPE = "application/problem+json"

# code -> (HTTP status, result member, title) (ADR 0002 item 13).
_APPLICATION_ERRORS: dict[str, tuple[int, str, str]] = {
    "not_found": (404, "not_found", "Not Found"),
    "stale_version": (409, "conflict", "Conflict"),
    "invalid_transition": (409, "rejected", "Conflict"),
    "validation_failed": (422, "validation_failed", "Unprocessable Entity"),
    "invalid_cursor": (422, "validation_failed", "Unprocessable Entity"),
    "idempotency_key_reuse": (422, "rejected", "Unprocessable Entity"),
    "idempotency_in_progress": (409, "conflict", "Conflict"),
    "failed": (500, "failed", "Internal Server Error"),
}


def _problem_response(
    *,
    status_code: int,
    title: str,
    detail: str,
    code: str,
    result: str,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    content: dict[str, Any] = {
        "type": f"urn:lifespace:problem:{code}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "code": code,
        "result": result,
    }
    if extra:
        content.update(extra)
    return JSONResponse(
        status_code=status_code,
        media_type=PROBLEM_MEDIA_TYPE,
        content=content,
    )


async def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # The detail is deliberately generic so request values are never echoed.
    return _problem_response(
        status_code=422,
        title="Unprocessable Entity",
        detail="Request validation failed.",
        code="validation_failed",
        result="validation_failed",
    )


async def _application_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ApplicationError):
        raise exc
    status_code, result, title = _APPLICATION_ERRORS.get(
        exc.code, (500, "failed", "Internal Server Error")
    )
    code = exc.code if exc.code in _APPLICATION_ERRORS else "failed"
    extra: dict[str, Any] = {}
    field = getattr(exc, "field", None)
    if isinstance(field, str):
        extra["field"] = field
    current_version = getattr(exc, "current_version", None)
    if isinstance(current_version, int) and not isinstance(current_version, bool):
        extra["current_version"] = current_version
    return _problem_response(
        status_code=status_code,
        title=title,
        detail=exc.message,
        code=code,
        result=result,
        extra=extra,
    )


async def _http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    code = "not_found" if exc.status_code == 404 else "failed"
    result = "not_found" if exc.status_code == 404 else "failed"
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return _problem_response(
        status_code=exc.status_code,
        title=_title_for(exc.status_code),
        detail=detail,
        code=code,
        result=result,
    )


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception while handling %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return _problem_response(
        status_code=500,
        title="Internal Server Error",
        detail="Internal server error",
        code="failed",
        result="failed",
    )


def _title_for(status_code: int) -> str:
    titles = {
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
    }
    return titles.get(status_code, "Error")


def register_error_handlers(app: FastAPI) -> None:
    """Attach the problem+json handlers to an application instance (ADR 0002 items 12 and 13)."""
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(ApplicationError, _application_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
