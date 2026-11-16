# LifeSpace API

FastAPI application for LifeSpace. It runs locally on Python 3.14 with an
isolated `uv` environment and talks to PostgreSQL 18 through SQLAlchemy's async
engine.

## Layers

| Package | Responsibility | Status |
|---|---|---|
| `lifespace.api` | HTTP routing, request and response schemas, problem+json error mapping. It must not import `lifespace.infrastructure` or SQLAlchemy. | Present |
| `lifespace.infrastructure` | Technical adapters: the async engine, shared metadata, and logging. It must not import `lifespace.api`. | Present |
| `lifespace.domain` | Frozen dataclasses and pure rules: lifecycle, time intervals, scheduling. No framework, database, HTTP, or Pydantic imports. | M1 |
| `lifespace.application` | Use cases, validation, and the ports they need. It imports `domain` only. | M1 |
| `lifespace.ai` | Intents, tool allowlist, orchestration, and the model port. It calls `application` only. | M7 |

`lifespace.main` is the composition root and the only module that wires
infrastructure into the application. There is no module-level `app`; uvicorn
uses the `create_app` factory.

## Dependency rules

The rules from the technical blueprint are enforced where both sides exist:

- `api` may call `application` (and in M0 reads wiring from `app.state`). It
  never imports `infrastructure` or SQLAlchemy.
- `infrastructure` implements ports and never imports `api` or `ai`.
- `domain` imports no framework, database library, HTTP library, model SDK,
  Pydantic, or other LifeSpace layer.
- `application` imports `domain` only and reaches infrastructure through ports.
- `ai` calls `application` through a fixed tool allowlist and never imports
  `infrastructure`, `api`, FastAPI, or SQLAlchemy.

`make api-lint` runs import-linter with two forbidden contracts:

1. `lifespace.api` must not import `lifespace.infrastructure` or `sqlalchemy`.
2. `lifespace.infrastructure` must not import `lifespace.api`.

Contracts for the other layers are added when those packages exist.

## Settings

`lifespace.config.Settings` reads `LIFESPACE_`-prefixed variables and the
repository-root `.env` file (resolved from the source file, never from the
current directory). Unprefixed variables in `.env` are ignored.

| Variable | Required | Purpose |
|---|---|---|
| `LIFESPACE_ENVIRONMENT` | No (`development`) | `development`, `test`, or `production` |
| `LIFESPACE_DATABASE_URL` | Yes | SQLAlchemy async URL for the development database |
| `LIFESPACE_TEST_DATABASE_URL` | No | Async URL for the test database used by integration tests |
| `LIFESPACE_LOG_LEVEL` | No (`INFO`) | Root log level |

The database URL is never logged or included in responses. The local values in
`.env.example` are not secrets.

## Tests

```bash
make api-test     # from the repository root
```

Or directly:

```bash
cd apps/api
uv run pytest                    # everything
uv run pytest tests/unit         # no database needed
uv run pytest tests/integration  # needs make db-up
```

Unit tests use no external service. Integration tests use
`LIFESPACE_TEST_DATABASE_URL` and never the development database. They fail,
never skip, with `PostgreSQL is not reachable. Run: make db-up` when the test
database is unavailable.

Testing rules:

- Use `httpx.AsyncClient` with `ASGITransport`. Do not use the deprecated
  `fastapi.testclient` or `starlette.testclient`.
- Pass `raise_app_exceptions=False` when a test expects a 500 response, and run
  the application lifespan in every HTTP test.
- `filterwarnings = error` is enabled. Warnings are fixed, not silenced.
- Dispose every engine, including when a test fails, so no unclosed-socket
  warning leaks into other tests.
- Alembic calls `asyncio.run`, so tests that drive Alembic must be synchronous.

## Database

PostgreSQL 18 runs in Docker on `127.0.0.1:5433` with the databases `lifespace`
and `lifespace_test`. Migrations live in `migrations/`; apply them with
`make migrate` and revert them with `make migrate-down` (development only).
