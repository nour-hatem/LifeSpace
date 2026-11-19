# LifeSpace API

FastAPI application for LifeSpace. It runs locally on Python 3.14 with an
isolated `uv` environment and talks to PostgreSQL 18 through SQLAlchemy's async
engine.

## Layers

| Package | Responsibility | Status |
|---|---|---|
| `lifespace.api` | HTTP routing, request and response schemas, problem+json error mapping. It must not import `lifespace.infrastructure` or SQLAlchemy. | Present |
| `lifespace.infrastructure` | Technical adapters: the async engine, SQLAlchemy models, repositories, unit of work, cursor and system ports, and logging. It must not import `lifespace.api`. | Present |
| `lifespace.domain` | Frozen dataclasses and pure rules: lifecycle, time intervals, scheduling. No framework, database, HTTP, or Pydantic imports. | Present |
| `lifespace.application` | Use cases, validation, and the ports they need. It imports `domain` only. | Present |
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

`make api-lint` runs import-linter with four forbidden contracts:

1. `lifespace.api` must not import `lifespace.infrastructure` or `sqlalchemy`.
2. `lifespace.infrastructure` must not import `lifespace.api`.
3. `lifespace.application` must not import frameworks, SQLAlchemy, or other LifeSpace layers except `domain`.
4. `lifespace.domain` must import no framework, database, HTTP, Pydantic, or other LifeSpace layer.

`lifespace.main` and `lifespace.openapi_export` are the composition roots.

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

## Persistence and API (M2)

The application layer turns HTTP and future AI requests into one transaction
each. Use cases receive a `UnitOfWorkFactory`, a `Clock`, and an `IdGenerator`;
they never read the clock, generate ids, or import infrastructure (ADR 0002
items 1 and 2). The API validates shape, calls a use case, and renders the
result. The domain owns the business rules.

| Application module | Public API |
|---|---|
| `tasks` | `create_task`, `get_task`, `list_tasks`, `edit_task`, `delete_task`, `transition_task`, `list_task_events` |
| `settings` | `get_settings`, `update_timezone` |
| `errors` | `ApplicationError`, `NotFoundError`, `StaleVersionError`, `ValidationFailedError`, `TransitionRejectedError`, `IdempotencyKeyReuseError`, `IdempotencyInProgressError`, `InvalidCursorError`, `translate_domain_errors` |
| `models` | `StoredTask`, `TaskView`, `StoredStatusEvent`, `Page`, `TaskFilter`, commands, results, `IdempotencyInput`, `AppSettings` |
| `ports` | `Clock`, `IdGenerator`, `TaskRepository`, `SettingsRepository`, `IdempotencyRepository`, `UnitOfWork`, `UnitOfWorkFactory` |

Infrastructure implements every port: `SqlAlchemyUnitOfWork` and its
repositories, `SystemClock`, `Uuid7Generator`, and the cursor helpers. ORM
models and SQLAlchemy never leave `lifespace.infrastructure`.

| Table | Purpose |
|---|---|
| `tasks` | Task rows with status, deadline columns, schedule, estimate, version, timestamps, and `deleted_at` for soft delete (ADR 0002 items 3 to 7) |
| `task_status_events` | Append-only lifecycle history, written in the same transaction as the transition (ADR 0002 item 6) |
| `idempotency_keys` | Create key, request fingerprint, and the task it produced (ADR 0002 item 14) |
| `app_settings` | The single row (id 1) holding the user's IANA time zone (ADR 0002 item 8) |

Migrations live in `migrations/`. Apply them with `make migrate` and revert them
with `make migrate-down` (development only). Autogenerated revisions are
reviewed by a human. Alembic's `env.py` calls `asyncio.run`, so tests drive
Alembic through a subprocess (`run_alembic` in
`tests/integration/conftest.py`) and remain synchronous. Integration tests reset
the M2 tables and the UTC settings row with `reset_database`.

| Method and path | Success | Notes |
|---|---|---|
| `GET /api/v1/tasks` | 200 | Filters `status` (repeatable), `category`, `priority`; `limit` 1 to 200; `cursor` |
| `POST /api/v1/tasks` | 201 | Optional `Idempotency-Key`; a replay returns 200 |
| `GET /api/v1/tasks/{id}` | 200 | Includes the computed `is_overdue` |
| `PATCH /api/v1/tasks/{id}` | 200 | `version` required; null clears; an omitted field is kept |
| `DELETE /api/v1/tasks/{id}?version=N` | 204 | Soft delete, no restore endpoint |
| `POST /api/v1/tasks/{id}/start` | 200 | To `in_progress` |
| `POST /api/v1/tasks/{id}/plan` | 200 | To `planned` |
| `POST /api/v1/tasks/{id}/complete` | 200 | To `completed` |
| `POST /api/v1/tasks/{id}/cancel` | 200 | To `canceled`, optional `reason` |
| `POST /api/v1/tasks/{id}/reopen` | 200 | To `planned` |
| `GET /api/v1/tasks/{id}/history` | 200 | Newest first, paginated |
| `GET /api/v1/settings` | 200 | The stored time zone |
| `PUT /api/v1/settings` | 200 | Rejects an unknown IANA zone |

Every error is `application/problem+json` with `type`, `title`, `status`,
`detail`, `code`, and `result`; validation failures add `field`, and a stale
version adds `current_version` when known (ADR 0002 items 12 and 13).

| Code | HTTP | Result | When |
|---|---|---|---|
| `not_found` | 404 | `not_found` | Missing or soft-deleted task, or an unknown route |
| `stale_version` | 409 | `conflict` | The expected version is no longer current |
| `invalid_transition` | 409 | `rejected` | The domain rejects the lifecycle change |
| `idempotency_in_progress` | 409 | `conflict` | Another request is recording the same key |
| `validation_failed` | 422 | `validation_failed` | Request shape or application validation |
| `invalid_cursor` | 422 | `validation_failed` | A malformed pagination cursor |
| `idempotency_key_reuse` | 422 | `rejected` | The key was used for another body or a deleted task |
| `failed` | 500 | `failed` | An unexpected failure; details stay in logs |

Idempotent creation accepts an `Idempotency-Key` of 1 to 200 printable ASCII
characters. The fingerprint is the SHA-256 of the canonical JSON of the
validated body. The same key and fingerprint replay the current task with HTTP
200 and `Idempotency-Replayed: true`; a different body is rejected. There is no
expiry in M2.

Lists use keyset pagination with an opaque base64url cursor. `limit` defaults to
100 and accepts 1 to 200. Tasks are ordered by `created_at` and `id` descending;
status events by `occurred_at` and `id` descending.

### Input limits (ADR 0002 item 20)

| Input | Rule |
|---|---|
| `estimate_minutes` | strict integer from 1 to 2,147,483,647 |
| `version` (body or delete query) | strict integer from 1 to 2,147,483,647 |
| `title` | 1 to 500 characters after trimming leading and trailing whitespace |
| `description` | at most 20,000 characters after trimming; JSON `null` clears it |
| cancel or transition `reason` | at most 1,000 characters after trimming |
| text | no NUL character and no lone surrogate |
| date-only deadline | 1970-01-01 to 2999-12-31 inclusive |
| datetime deadline, schedule, and clock instant | 1970-01-01T00:00:00Z up to, but not including, 3000-01-01T00:00:00Z |
| cursor instant | the same instant range; any malformed or out-of-range cursor is `invalid_cursor` |

Numeric bounds live in the request schemas and are reported as the generic 422
`validation_failed`. Text, character, date, and instant rules live in the domain
(single source of truth) and are reported as 422 `validation_failed` with their
`field`. Every violation is a `problem+json` 422 response, never a 500 (ADR 0002
items 20, 21, and 24).

The contract workflow keeps the generated files committed:

```bash
make api-spec          # export apps/web/src/shared/api/openapi.json
make api-spec-check    # fail when the committed spec is stale (part of api-lint)
make api-types         # export the spec and regenerate schema.d.ts
make api-types-check   # fail when the committed TypeScript types are stale
```

`openapi-typescript@7.13.0` runs through `npx` and is deliberately not a project
dependency because it declares a TypeScript 5 peer (ADR 0002 item 18).

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
