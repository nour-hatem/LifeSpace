# LifeSpace API

FastAPI application for LifeSpace. It runs locally on Python 3.14 with an
isolated `uv` environment and talks to PostgreSQL 18 through SQLAlchemy's async
engine.

## Layers

| Package | Responsibility | Status |
|---|---|---|
| `lifespace.api` | HTTP routing, request and response schemas, problem+json error mapping. It must not import `lifespace.infrastructure` or SQLAlchemy. | Present |
| `lifespace.infrastructure` | Technical adapters: the async engine, shared metadata, and logging. It must not import `lifespace.api`. | Present |
| `lifespace.domain` | Frozen dataclasses and pure rules: lifecycle, time intervals, scheduling. No framework, database, HTTP, or Pydantic imports. | Present |
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

## Domain layer (M1)

The pure domain lives in `apps/api/src/lifespace/domain` and has no I/O. It
imports only the standard library and other `lifespace.domain` modules. It
never reads the clock or generates ids: callers pass `now`, identifiers, and
the user's `ZoneInfo`. `make api-lint` enforces the purity contract.

| Module | Public API |
|---|---|
| `errors` | `DomainError`, `DomainValidationError`, `InvalidTransitionError` |
| `time` | `ensure_aware`, `local_date`, `start_of_local_day`, `TimeInterval` |
| `deadline` | `DateDeadline`, `DateTimeDeadline`, `Deadline`, `is_deadline_passed` |
| `task` | `Task`, `TaskStatus`, `Priority`, `Category`, `TaskSource`, `UNSET`, `create_task`, `edit_task` |
| `lifecycle` | `ALLOWED_TRANSITIONS`, `StatusEvent`, `TransitionResult`, `transition_task` |
| `overdue` | `is_overdue` |

Run the domain tests without a database:

```bash
cd apps/api
uv run pytest tests/unit/domain
```

Caller-facing ADR 0001 decisions:

| Item | Rule |
|---|---|
| 2 | A date-only deadline ends at the end of that local day; it passes at the first instant of the next local day. |
| 3 | A date-time deadline passes strictly after its instant. |
| 4 | `create_task` accepts only `INBOX` and `PLANNED`. |
| 5, 6 | Only `ALLOWED_TRANSITIONS` are legal; a transition to the same status is rejected. |
| 7 | Completing or canceling keeps the deadline, the schedule, and the estimate. |
| 8 | Reopening clears `completed_at`, `canceled_at`, and the reason, and drops a schedule that already ended. |
| 9 | Overdue is computed from the deadline and status, never stored. |
| 10, 11 | An estimate is a positive whole number of minutes; a title is trimmed and non-empty. |
| 12 | Deadline, schedule, and estimate are independent. |
| 13 | Intervals are half-open: start inclusive, end exclusive. |
| 14 | Every datetime is timezone-aware; the domain never reads the clock. |
| 16 | Edits are not restricted by status. |

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
