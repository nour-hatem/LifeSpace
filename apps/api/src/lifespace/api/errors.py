"""Problem+json error handling for the API.

This module maps framework and application exceptions to RFC 9457 problem
documents. It must not import ``lifespace.infrastructure`` or SQLAlchemy, and
error bodies must never contain exception text, stack traces, or credentials.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

PROBLEM_MEDIA_TYPE = "application/problem+json"


def _problem_response(
    *,
    status_code: int,
    title: str,
    detail: str,
    code: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        media_type=PROBLEM_MEDIA_TYPE,
        content={
            "type": f"urn:lifespace:problem:{code}",
            "title": title,
            "status": status_code,
            "detail": detail,
            "code": code,
        },
    )


async def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # The detail is deliberately generic so request values are never echoed.
    return _problem_response(
        status_code=422,
        title="Unprocessable Entity",
        detail="Request validation failed.",
        code="validation_failed",
    )


async def _http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    code = "not_found" if exc.status_code == 404 else "failed"
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return _problem_response(
        status_code=exc.status_code,
        title=_title_for(exc.status_code),
        detail=detail,
        code=code,
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
    """Attach the problem+json handlers to an application instance."""
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
