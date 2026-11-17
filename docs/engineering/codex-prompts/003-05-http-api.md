# Task 003, Part 5 of 6: HTTP API: schemas, routes, error mapping, wiring

**Status:** Ready. Milestone M2 (persistence and task API) is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and depends only on the repository, not on earlier conversation.
**Depends on:** Parts 1 to 4 of Task 003, Docker database
**Branch:** `m2/persistence-task-api`
**Binding decisions:** `docs/engineering/adr/0002-m2-persistence-and-task-api.md` (provisional defaults, owner may override)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/003-05-http-api.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 003 | M2 PERSISTENCE AND TASK API | PART 5 OF 6 | HTTP API: schemas, routes, error mapping, wiring

SESSION CONTEXT
You are the implementation agent for LifeSpace, a local single-user application. Task 003 builds milestone M2 (the application layer, PostgreSQL persistence, and the task HTTP API) in 6 parts. Each part runs in a separate session and you have no memory of earlier parts. Everything you need is in this prompt and in the repository. A separate architect reviews your Git diff, so do exactly what this part asks and nothing else. Do not start work that belongs to another part.

CONTEXT BUDGET (this session has a limited context window)
- Read only the files this prompt names: AGENTS.md, docs/engineering/TECHNICAL_BLUEPRINT.md (once, in full), docs/engineering/adr/0001-m1-domain-decisions.md, docs/engineering/adr/0002-m2-persistence-and-task-api.md (binding), and the code files the prompt tells you to inspect. Do not read other documents under docs/.
- Never print lockfiles, .venv, node_modules, or full logs. Pipe long command output through "tail -n 30". Never run a server in the foreground: start it with setsid in the background, wait for health, and stop it afterwards (kill the process group and confirm the port is free).
- If the same command fails twice for the same reason, stop and report the exact error. Try at most two different fixes for one problem.
- Your training data may predate the pinned versions (Python 3.14, FastAPI 0.133, Starlette 1.10, Pydantic 2.13, SQLAlchemy 2.0.50, asyncpg 0.31, Alembic 1.18, pytest 9.1, pytest-asyncio 1.4, hypothesis 6.170, ruff 0.17, mypy 2.4). When unsure of an API, read the installed package source under apps/api/.venv/lib/python3.14/site-packages instead of guessing.

SCOPE RULES (owner decisions, binding)
- Local single-user app. No authentication, accounts, user_id, ownership fields, or multi-tenancy. Authentication is deferred and is NOT an approved requirement.
- No new runtime dependency in apps/api and no new dependency in apps/web unless this prompt says so. No Redis, queue, agent framework, CI, Dockerfile, or deployment configuration.
- Layers (import-linter enforces them): domain imports only the standard library. application imports only the standard library and lifespace.domain. infrastructure implements the application ports and never imports lifespace.api. api calls application and may import lifespace.domain value types (enums, Deadline types, TimeInterval) for mapping, but never infrastructure or SQLAlchemy. lifespace.main (and lifespace.openapi_export) are composition roots.
- Domain and application never read the clock and never generate ids: they receive a Clock and an IdGenerator. Never call datetime.now, date.today, uuid.uuid4, or uuid.uuid7 inside lifespace.domain or lifespace.application.
- Compare and subtract datetimes only through lifespace.domain.time.as_instant (ADR 0001 item 19).
- No unnecessary abstractions. Write the simplest code that satisfies this part. Every public function and class has a short docstring that cites the ADR item. Code, comments, and docstrings are in English.

MACHINE FACTS (do not fight them, do not change them)
- Ubuntu 26.04, Python 3.14.4, uv 0.11.28, Node 22.22.3, npm 10.9.8, GNU Make 4.4.1. Python dependencies live only in apps/api/.venv created by uv. Every uv call runs with UV_PYTHON_DOWNLOADS=never (the Makefile exports it). pnpm is not used.
- Do not install, upgrade, or remove any global tool or package. No sudo. No pip install, npm install -g, or uv python install.
- The repository path contains a space ("/home/nour/AI Factory/LifeSpace"). Quote every path and prefer relative paths.
- The login shell exports NODE_ENV=production. Run any ad hoc npm or npx command with env -u NODE_ENV.
- A host PostgreSQL service listens on 127.0.0.1:5432. Never use it. The project database is a Docker container published on 127.0.0.1:5433 (databases lifespace and lifespace_test).
- Docker Desktop must be running with the desktop-linux context. Do not start or stop Docker Desktop and do not change the Docker context. If the database container fails to start with the message "RWLayer of container ... is unexpectedly nil", run: docker rm -f lifespace-db-1 and then make db-up (the data volume is kept). If Docker is unreachable, stop and report it, except in parts that say domain and application tests need no database.
- Disk space on /home can be low. If a command fails with ENOSPC, stop and report. Do not work around it.
- Existing project facts: backend code is in apps/api/src/lifespace (packages domain, api, infrastructure, plus config.py and main.py). Make targets: api-setup, api-lint (ruff, ruff format --check, lint-imports), api-format, api-typecheck (mypy strict over src and tests), api-test (pytest, warnings are errors), migrate, migrate-down, db-up, check (everything including the web app). Ruff selects E, F, I, B, UP, SIM, BLE, RUF with line length 100 (note RUF036: write unions as "X | Unset | None", None last). Run make api-format after writing code. Tests use httpx.AsyncClient with ASGITransport (never the Starlette TestClient), run the app lifespan, and dispose every engine.

GIT RULES
- Work on branch m2/persistence-task-api. If it does not exist, create it from main, but only when main already contains apps/api/src/lifespace/domain/task.py. Any other current branch: stop and report.
- Do not commit to main, push, merge, or rewrite history. Never modify files under docs/.
- Commit your work in small conventional commits and finish with a clean git status.
- If git status is dirty at the start and the changes do not belong to this part, stop and report. Never discard changes you did not make.
- Never create or commit .env, secrets, or credentials.

START CHECK (run first)
1. Branch must be m2/persistence-task-api. git status --short must be empty.
2. Read AGENTS.md, docs/engineering/TECHNICAL_BLUEPRINT.md (sections 8 and 13), docs/engineering/adr/0001-m1-domain-decisions.md, and docs/engineering/adr/0002-m2-persistence-and-task-api.md.
3. Confirm earlier parts exist: application/tasks.py with create_task, get_task, list_tasks, edit_task, delete_task, transition_task, list_task_events; application/settings.py; infrastructure/{repositories,unit_of_work,system,cursor}.py. Read application/models.py, application/errors.py, application/tasks.py (signatures only), infrastructure/unit_of_work.py (create_unit_of_work_factory), infrastructure/system.py, src/lifespace/main.py, api/errors.py, api/health.py, tests/conftest.py, tests/unit/test_errors.py, and tests/unit/application/fakes.py.
4. Docker must be reachable for the integration tests. Run make api-setup, make db-up, make migrate, make api-test (all must pass before you change anything).

OBJECTIVE
Expose the use cases as the /api/v1 task API with problem+json errors that carry a result member, and wire everything in the composition root. No frontend, no new dependency.

DELIVERABLES
1. main.py: create_app(settings=None, *, ready_check=None, uow_factory=None, clock=None, ids=None). Defaults: SystemClock, Uuid7Generator, and a unit of work factory built from an engine and session factory created from settings. Create the engine only when it is needed (when ready_check or uow_factory is not injected), use it for the readiness callable when none is injected, and dispose it in the lifespan. Store uow_factory, clock, and ids on app.state beside ready_check. Register the new router. Keep every existing health test passing.
2. api/schemas.py: Pydantic models (extra="forbid" on every request model; strict types where integers or strings must not be coerced):
   - DeadlineSchema: a discriminated union on "kind": date (value: date) or datetime (value: AwareDatetime). IntervalSchema: start and end (AwareDatetime).
   - TaskCreate: title, description, category, priority, estimate_minutes, deadline, scheduled, status (inbox or planned, default planned). TaskPatch: version (required, integer at least 1) and the fields title, description, category, priority, estimate_minutes, deadline, scheduled; use model_fields_set to tell "omitted" from "null". ActionBody: version. CancelBody: version and reason (optional). SettingsBody: timezone.
   - TaskOut: id, title, description, status, source, category, priority, estimate_minutes, deadline (DeadlineSchema or null), scheduled (or null), completed_at, canceled_at, cancellation_reason, created_at, updated_at, version, is_overdue. EventOut: id, task_id, from_status, to_status, occurred_at, reason, discarded_schedule. TaskPage and EventPage: items, next_cursor. SettingsOut: timezone. Output datetimes are UTC with an offset.
   - Mapping helpers between schemas and application commands and between TaskView and TaskOut live in api (a small api/mapping.py or inside the routes module). They may import lifespace.domain value types and enums, never infrastructure.
3. api/tasks.py router (prefix /api/v1), with stable operation ids equal to the function names: list_tasks, create_task, get_task, patch_task, delete_task, start_task, plan_task, complete_task, cancel_task, reopen_task, list_task_history, get_settings, update_settings. Set the FastAPI generate_unique_id_function so every operation id is the route name. Dependencies read uow_factory, clock, and ids from request.app.state.
   - GET /api/v1/tasks: query status (repeatable), category, priority, limit (default 100, 1 to 200), cursor. 200 TaskPage.
   - POST /api/v1/tasks: body TaskCreate, optional header Idempotency-Key (1 to 200 printable ASCII characters, otherwise 422). The use case source is always manual. 201 with TaskOut and a Location header /api/v1/tasks/{id}. With a key the fingerprint is the SHA-256 hex digest of the canonical JSON (sorted keys, no spaces) of the validated body (model_dump(mode="json")). A replay returns 200 with the current TaskOut and the header Idempotency-Replayed: true.
   - GET /api/v1/tasks/{id}: 200 TaskOut. PATCH: body TaskPatch, 200 TaskOut; JSON null clears an optional field; a body with no field besides version is 422. DELETE /api/v1/tasks/{id}?version=N: 204 with no body.
   - POST /api/v1/tasks/{id}/start, /plan, /complete, /reopen (body ActionBody) and /cancel (body CancelBody): each returns 200 TaskOut. Targets: start in_progress, plan planned, complete completed, cancel canceled, reopen planned.
   - GET /api/v1/tasks/{id}/history: query limit and cursor, 200 EventPage.
   - GET and PUT /api/v1/settings: SettingsOut.
4. api/errors.py: add a result member to every problem body (ADR 0002 items 12 and 13). Request validation and invalid cursor and application validation errors: 422 with result validation_failed (application and domain validation failures also carry field when known). Starlette 404 and application not_found: 404 result not_found. Other Starlette HTTP errors and the unhandled 500: result failed. stale_version: 409 result conflict with the extra member current_version when known. invalid_transition: 409 result rejected. idempotency_key_reuse: 422 result rejected. idempotency_in_progress: 409 result conflict. Add a handler for ApplicationError that maps by code through one table, and keep the generic detail rule: never put exception text from unexpected errors, stack traces, SQL, or credentials in a body. Messages from ApplicationError are written by the application layer and are safe to return. Update the existing health and error tests for the new result member.
5. Tests:
   - apps/api/tests/unit/api/test_tasks_api.py with the in-memory fakes (inject uow_factory, clock, ids, ready_check into create_app; Settings(_env_file=None, database_url=<unreachable URL>)): create (201, Location header, defaults, inbox status), invalid bodies (422 with result validation_failed: empty title, unknown field, naive datetime, estimate 0, bad status), deadline both kinds, scheduled, get, 404 for unknown and deleted ids, list with filters and pagination (cursor round trip, invalid cursor 422, limit 0 and 201 are 422), patch (null clears, omitted keeps, only version is 422, stale version is 409 with current_version, independence of deadline schedule and estimate), delete (204 then 404, stale 409, missing version query is 422), every lifecycle action (allowed path, rejected path 409 with result rejected, cancel with reason, reopen), history (newest first, pagination, 404 for a missing task), settings get and put (valid zone, invalid zone 422 with field timezone), is_overdue in responses under Africa/Cairo, idempotency (201 then 200 with Idempotency-Replayed, same key different body 422 with result rejected, a bad key header 422), problem+json content type everywhere, and that no error body contains a traceback or the text of an injected failing use case (inject a uow_factory that raises RuntimeError("secret internal detail") and assert a generic 500 with result failed).
   - apps/api/tests/integration/test_api_tasks.py: the same main flows end to end through create_app with the real database (Settings with the test database URL, schema fixtures from Part 3): create, list, patch, start, complete, reopen, cancel path, history, delete, 404 afterwards, stale version, idempotency replay, pagination across 25 tasks, settings timezone change flips is_overdue for a date deadline near the Cairo spring forward, and concurrent PATCH requests with the same version where exactly one gets 200 and the other 409.
   - Contract test: the generated OpenAPI document (app.openapi()) contains all 13 operation ids above and no operation without a response schema; the problem+json responses are declared (409, 404, 422) for the task routes.

VERIFY (run each, record the real result)
1. make api-format, make api-lint (zero errors, 4 import contracts kept; the api package must not import infrastructure or sqlalchemy), make api-typecheck (zero errors), make api-test (all pass, zero warnings, record unit, integration, and total counts).
2. Start the API with the background pattern (make dev-api) against the development database (make migrate first). With curl: create a task (note the id and version), list, patch the title with the version, start it, complete it, show the history (two events), try to complete it again (409 rejected), reopen it, delete it with the version, confirm GET returns 404 and the list is empty. Show the status codes and the problem+json body of the 409 and 404. Stop the server and confirm port 8000 is free.
3. Run the integration tests twice in a row. No flakiness.
4. grep -rn "lifespace.infrastructure" apps/api/src/lifespace/api prints nothing. grep -rnE "(now\(|today\(|uuid4|uuid7)" apps/api/src/lifespace/domain apps/api/src/lifespace/application prints nothing.
5. git status --short is empty after the commits.

COMMIT
Small conventional commits, for example "feat(api): add task schemas and routes", "feat(api): add result member and application error mapping", "feat(api): wire use cases in the composition root", "test(api): add task api unit and integration tests". git status must be clean afterwards. Leave the database running.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first, at most 8 lines).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Public names the next part needs (modules, classes, functions you created).
Finish by telling the user: "Part 5 is finished. Start a new session for the next part."
```
