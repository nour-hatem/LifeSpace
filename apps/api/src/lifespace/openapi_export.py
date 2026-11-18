"""Export the OpenAPI document without a database or a `.env` file (ADR 0002 item 18).

This module is a composition root like ``lifespace.main``. It builds the app
with dummy settings and injected stubs, so exporting the contract never touches
PostgreSQL. Run it as ``uv run python -m lifespace.openapi_export <path>``.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path

from lifespace.application.ports import UnitOfWork
from lifespace.config import Settings
from lifespace.main import create_app

OPENAPI_DATABASE_URL = "postgresql+asyncpg://openapi:openapi@127.0.0.1:1/openapi"


async def _ready() -> bool:
    """Report readiness without contacting a database (ADR 0002 item 18)."""
    return True


def _unused_uow_factory() -> UnitOfWork:
    """Fail loudly if an export ever tries to open a unit of work (ADR 0002 item 18)."""
    raise RuntimeError("the OpenAPI export never opens a unit of work")


def export_openapi_json() -> str:
    """Return the canonical OpenAPI JSON document as text (ADR 0002 item 18)."""
    settings = Settings(_env_file=None, database_url=OPENAPI_DATABASE_URL)
    app = create_app(settings, ready_check=_ready, uow_factory=_unused_uow_factory)
    document = app.openapi()
    return json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def main(argv: Sequence[str] | None = None) -> None:
    """Write the OpenAPI document to the path given on the command line (ADR 0002 item 18)."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        raise SystemExit("usage: python -m lifespace.openapi_export <path>")
    Path(arguments[0]).write_text(export_openapi_json(), encoding="utf-8")


if __name__ == "__main__":
    main()
