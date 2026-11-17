# Task 003, Part 4 of 6: Repositories, unit of work, clock, and id generator

**Status:** Ready. Milestone M2 (persistence and task API) is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and depends only on the repository, not on earlier conversation.
**Depends on:** Parts 1 to 3 of Task 003, Docker database
**Branch:** `m2/persistence-task-api`
**Binding decisions:** `docs/engineering/adr/0002-m2-persistence-and-task-api.md` (provisional defaults, owner may override)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/003-04-repositories-and-unit-of-work.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 003 | M2 PERSISTENCE AND TASK API | PART 4 OF 6 | Repositories, unit of work, clock, and id generator

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
2. Read AGENTS.md, docs/engineering/TECHNICAL_BLUEPRINT.md, docs/engineering/adr/0001-m1-domain-decisions.md, and docs/engineering/adr/0002-m2-persistence-and-task-api.md.
3. Confirm earlier parts exist: application/{errors,models,ports,tasks}.py, infrastructure/models.py, infrastructure/mapping.py, migrations/versions/0002_tasks_and_history.py, tests/integration/test_schema.py. Read application/ports.py, application/errors.py, application/models.py, infrastructure/db.py, infrastructure/models.py, infrastructure/mapping.py, tests/unit/application/fakes.py (the in-memory repository is the behavioral reference), and tests/integration/test_schema.py (reuse its schema fixtures).
4. Docker must be reachable. Run make api-setup, make db-up, make migrate, make api-test (all must pass before you change anything). If Docker is unreachable, stop and report it.

OBJECTIVE
Implement the application ports with SQLAlchemy: the repositories, the unit of work, SystemClock, and Uuid7Generator, with integration tests against PostgreSQL. No HTTP.

DELIVERABLES
1. infrastructure/db.py: add create_session_factory(engine) -> async_sessionmaker[AsyncSession] with expire_on_commit=False.
2. infrastructure/system.py: SystemClock (now() returns an aware UTC datetime) and Uuid7Generator (new_id() returns uuid.uuid7()). These are the only places allowed to read the clock or generate ids.
3. infrastructure/cursor.py: encode_cursor(values: Sequence[str]) -> str and decode_cursor(cursor: str, expected_parts: int) -> list[str] using base64url of JSON; a malformed cursor, wrong shape, or wrong number of parts raises InvalidCursorError (ADR 0002 item 15). The cursor never contains anything but the keyset values.
4. infrastructure/repositories.py with SqlAlchemyTaskRepository, SqlAlchemySettingsRepository, SqlAlchemyIdempotencyRepository (all take an AsyncSession) and infrastructure/unit_of_work.py with SqlAlchemyUnitOfWork and create_unit_of_work_factory(session_factory) -> UnitOfWorkFactory.
   - SqlAlchemyUnitOfWork: __aenter__ opens a session and begins a transaction and exposes tasks, settings, and idempotency; commit() commits; __aexit__ rolls back when commit was not called or an exception occurred and always closes the session. A unit of work is single use.
   - add: insert with version 1, returns StoredTask.
   - get: select by id where deleted_at is null.
   - list: ADR 0002 items 15 and 16. Filters statuses (IN), category, priority; always deleted_at is null; order by created_at desc, id desc; keyset pagination: fetch limit + 1 rows, the cursor encodes created_at (isoformat UTC) and id of the last returned row, the next page uses (created_at, id) < (cursor values) as a row comparison; next_cursor is None on the last page.
   - save(task, *, expected_version): one UPDATE of every mutable column with version = expected_version + 1 where id matches and version = expected_version and deleted_at is null, RETURNING the row. When no row is returned, run a SELECT of the current version: no row or deleted raises NotFoundError, otherwise StaleVersionError(expected_version, current_version).
   - soft_delete(task_id, *, expected_version, now): one UPDATE setting deleted_at = now, updated_at = now, version + 1 with the same guards and the same error rules.
   - add_event(event_id, event): insert using event_to_values. list_events: filter by task_id, order by occurred_at desc, id desc, keyset pagination as for tasks.
   - SettingsRepository: get_timezone reads the single row; set_timezone updates timezone and updated_at.
   - IdempotencyRepository: get by key; add inserts and converts a unique violation into IdempotencyInProgressError (use a savepoint or catch IntegrityError on the key constraint and roll back only that statement as needed so the unit of work stays usable for the error path).
   All mapping goes through infrastructure/mapping.py. No SQL string formatting: use SQLAlchemy expressions and bound parameters only.
5. Integration tests in apps/api/tests/integration/test_repositories.py and test_unit_of_work.py (real PostgreSQL, test database; reuse the Part 3 schema fixtures: subprocess Alembic upgrade, truncation between tests; dispose every engine; tests fail, never skip, when the database is down):
   - Each repository method matches the behavior in the in-memory fake: run the same behavioral assertions where practical (write a small shared set of scenario functions or parametrize over fake and real units of work for add, get, save, soft delete, filters, pagination, events, settings, idempotency).
   - Optimistic concurrency: two units of work read the same task and both save with the same expected_version using asyncio.gather; exactly one succeeds and the other raises StaleVersionError; the stored version is 2.
   - save and soft_delete on a missing or deleted task raise NotFoundError; on a stale version raise StaleVersionError with the current version.
   - Soft-deleted tasks are invisible to get and list; their events remain in the table (select directly).
   - Pagination over 25 tasks with limit 10: 3 pages, no duplicates, no gaps, strictly descending order, next_cursor None at the end; tasks with identical created_at are still ordered and paged correctly by id; events paginate the same way; a malformed cursor raises InvalidCursorError.
   - Filters: several statuses, category, priority, and combinations.
   - Round trip: a task and its events written through the repositories read back equal (compare instants), including a Cairo ambiguous-hour deadline and a schedule.
   - Unit of work: commit persists; leaving without commit rolls back; an exception inside the block rolls back; two units of work do not see each other's uncommitted rows; the session is closed afterwards.
   - Transition atomicity: a failure after save and before add_event leaves neither the task change nor the event (simulate by raising inside the block after save).
   - Idempotency: add then get; a second add with the same key raises IdempotencyInProgressError; the foreign key restricts deleting the task row.
   - End to end with the real use cases: run application.tasks.create_task, edit_task, transition_task, delete_task, list_tasks, and list_task_events through create_unit_of_work_factory with SystemClock and Uuid7Generator against the test database and assert the results.
   - Unit tests (no database) for cursor encoding and decoding including malformed input (not base64, not JSON, wrong part count) and for SystemClock (aware UTC) and Uuid7Generator (every id has version 7 and 1000 generated ids are unique).

VERIFY (run each, record the real result)
1. make api-format, make api-lint (zero errors, 4 contracts kept), make api-typecheck (zero errors), make api-test (all pass, zero warnings, record the counts).
2. Integration tests twice in a row (cd apps/api && for i in 1 2; do uv run pytest tests/integration -q 2>&1 | tail -n 1; done). No flakiness and no leftover rows.
3. Prove the concurrency test is meaningful: temporarily remove "and version = expected_version" from the UPDATE in save, run the concurrency test, confirm it fails, then git checkout the file.
4. grep -rnE "(now\(|today\(|uuid4|uuid7)" apps/api/src/lifespace/domain apps/api/src/lifespace/application prints nothing. grep -rn "lifespace.infrastructure" apps/api/src/lifespace/api apps/api/src/lifespace/application prints nothing.
5. git status --short is empty after the commits.

COMMIT
Small conventional commits, for example "feat(infrastructure): add clock, id generator, and cursor helpers", "feat(infrastructure): add sqlalchemy repositories and unit of work", "test(infrastructure): add repository and unit of work integration tests". git status must be clean afterwards. Leave the database running.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first, at most 8 lines).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Public names the next part needs (modules, classes, functions you created).
Finish by telling the user: "Part 4 is finished. Start a new session for the next part."
```
