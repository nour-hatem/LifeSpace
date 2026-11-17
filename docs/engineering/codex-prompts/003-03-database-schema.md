# Task 003, Part 3 of 6: Database schema, Alembic revision 0002, and row mapping

**Status:** Ready. Milestone M2 (persistence and task API) is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and depends only on the repository, not on earlier conversation.
**Depends on:** Parts 1 and 2 of Task 003, Docker database
**Branch:** `m2/persistence-task-api`
**Binding decisions:** `docs/engineering/adr/0002-m2-persistence-and-task-api.md` (provisional defaults, owner may override)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/003-03-database-schema.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 003 | M2 PERSISTENCE AND TASK API | PART 3 OF 6 | Database schema, Alembic revision 0002, and row mapping

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
2. Read AGENTS.md, docs/engineering/TECHNICAL_BLUEPRINT.md (section 7), docs/engineering/adr/0001-m1-domain-decisions.md, and docs/engineering/adr/0002-m2-persistence-and-task-api.md.
3. Confirm earlier parts exist: apps/api/src/lifespace/application/{models,ports,tasks}.py. Read application/models.py (StoredTask, StoredStatusEvent), domain/task.py, domain/lifecycle.py (StatusEvent), domain/deadline.py, domain/time.py (TimeInterval, as_instant), infrastructure/db.py (metadata, NAMING_CONVENTION), migrations/env.py, migrations/versions/0001_baseline.py, and the existing tests in apps/api/tests/integration.
4. Docker must be reachable. Run make api-setup, make db-up, make migrate, then make api-test: all must pass before you change anything. If Docker is unreachable, stop and report it.

OBJECTIVE
Create the SQLAlchemy models, the Alembic revision 0002 with all constraints, and the pure mapping functions between domain objects and rows. No repositories yet (Part 4).

DELIVERABLES
1. apps/api/src/lifespace/infrastructure/models.py: typed SQLAlchemy 2.0 ORM classes on a DeclarativeBase that uses the existing metadata object from infrastructure/db.py (so the naming convention applies). Use explicit names for every CHECK constraint and every index. Tables (ADR 0002 items 3, 5, 6, 7, 8, 14, 19):
   - tasks: id (Uuid, primary key), title (Text, not null), description (Text, null), status (Text, not null), source (Text, not null), category (Text, null), priority (Text, null), estimate_minutes (Integer, null), deadline_date (Date, null), deadline_at (timestamptz, null), scheduled_start (timestamptz, null), scheduled_end (timestamptz, null), completed_at (timestamptz, null), canceled_at (timestamptz, null), cancellation_reason (Text, null), created_at (timestamptz, not null), updated_at (timestamptz, not null), version (Integer, not null), deleted_at (timestamptz, null).
     Checks, named: status_valid (status in inbox, planned, in_progress, completed, canceled), source_valid (manual, ai), category_valid (null or work, education, learning, personal, projects), priority_valid (null or critical, high, medium, low), estimate_positive (null or above 0), deadline_exclusive (deadline_date is null or deadline_at is null), scheduled_complete ((scheduled_start is null) = (scheduled_end is null)), scheduled_order (scheduled_start is null or scheduled_end > scheduled_start), completed_matches_status ((status = 'completed') = (completed_at is not null)), canceled_matches_status ((status = 'canceled') = (canceled_at is not null)), reason_only_when_canceled (cancellation_reason is null or status = 'canceled'), version_positive (version >= 1), updated_not_before_created (updated_at >= created_at), title_not_blank (length(btrim(title)) > 0).
     Indexes: ix_tasks_created_at_id on (created_at desc, id desc) where deleted_at is null; ix_tasks_status on (status) where deleted_at is null (use postgresql_where).
   - task_status_events: id (Uuid, primary key), task_id (Uuid, not null, foreign key to tasks.id, ON DELETE RESTRICT), from_status (Text, not null), to_status (Text, not null), occurred_at (timestamptz, not null), reason (Text, null), discarded_schedule_start (timestamptz, null), discarded_schedule_end (timestamptz, null). Checks: from_status_valid and to_status_valid (same five values), discarded_complete (both null or both set), discarded_order (null or end > start). Index ix_task_status_events_task_occurred on (task_id, occurred_at desc, id desc).
   - app_settings: id (SmallInteger, primary key), timezone (Text, not null, default 'UTC'), updated_at (timestamptz, not null). Checks: single_row (id = 1), timezone_not_blank (length(btrim(timezone)) > 0).
   - idempotency_keys: key (Text, primary key), request_fingerprint (Text, not null), task_id (Uuid, not null, foreign key to tasks.id, ON DELETE RESTRICT), created_at (timestamptz, not null). Check: key_length (length(key) between 1 and 200).
   ORM classes are named TaskRow, StatusEventRow, AppSettingsRow, IdempotencyKeyRow. They never leave lifespace.infrastructure.
2. Alembic revision 0002 (rev-id 0002, down revision 0001, file 0002_tasks_and_history.py), written by hand with explicit op.create_table, op.create_check_constraint (or table-level constraints), op.create_index calls that match the models exactly, plus an INSERT of the single settings row (id 1, timezone 'UTC', updated_at now()). The downgrade drops the indexes and tables in reverse dependency order. Do not rely on autogenerate output without reading it.
3. apps/api/src/lifespace/infrastructure/mapping.py: pure functions with no database access:
   - task_to_values(task: Task, *, version: int, deleted_at: datetime | None = None) -> dict[str, Any]: column values for tasks. Datetimes are written as UTC instants via as_instant. A DateDeadline fills deadline_date, a DateTimeDeadline fills deadline_at, never both. A TimeInterval fills scheduled_start and scheduled_end.
   - row_to_stored_task(row: TaskRow) -> StoredTask: builds the domain Task through its constructor (so invariants are validated), enums from their string values, deadline_date to DateDeadline, deadline_at to DateTimeDeadline, both scheduled columns to a TimeInterval.
   - event_to_values(event_id: UUID, event: StatusEvent) -> dict[str, Any] and row_to_stored_event(row: StatusEventRow) -> StoredStatusEvent (discarded schedule columns to TimeInterval or None).
4. Tests:
   - Unit (no database) apps/api/tests/unit/infrastructure/test_mapping.py (create the folder with __init__.py following the convention): hypothesis round trips. A task built with create_task (reuse tests/unit/domain/strategies.py valid_tasks) and every task reached through domain transitions (completed with a reason-less path, canceled with a reason, reopened) survives task_to_values then a row built from those values then row_to_stored_task, comparing instants (compare datetimes with as_instant, because stored values are UTC). Date-only and exact deadlines both round trip. The two deadline columns are never both set. A schedule round trips. A status event with and without a discarded schedule round trips.
   - Integration apps/api/tests/integration/test_schema.py (real PostgreSQL, test database lifespace_test). Schema setup must run Alembic in a SUBPROCESS (sys.executable -m alembic -c apps/api/alembic.ini upgrade head with the environment variable LIFESPACE_DATABASE_URL set to the test URL), never through the Alembic Python API inside an async fixture, because Alembic calls asyncio.run and that breaks pytest-asyncio loops. Use a module-scoped synchronous fixture that upgrades to head, and a function-level cleanup that truncates tasks, task_status_events, and idempotency_keys (CASCADE) and resets app_settings to 'UTC'. Follow the existing integration convention: tests fail (never skip) with the message "PostgreSQL is not reachable. Run: make db-up" when the database is down.
     For every named CHECK constraint, insert a violating row with raw SQL (sqlalchemy text) inside a transaction and assert an IntegrityError that names the constraint. Also test: a valid task row inserts; both deadline columns set is rejected; a half-set schedule is rejected; end not after start is rejected; completed status without completed_at is rejected; a reason on a non-canceled task is rejected; version 0 is rejected; a blank title is rejected; a status event for a missing task is rejected (foreign key); deleting a task row that has events is rejected (restrict); idempotency key longer than 200 characters is rejected; app_settings accepts only id 1; a second app_settings row is rejected.
   - Update the existing migration test in tests/integration/test_migrations.py: after upgrade to head the version table holds exactly "0002"; downgrade to base leaves the version table empty and the tables tasks, task_status_events, app_settings, and idempotency_keys no longer exist; upgrade 0001 then 0002 also works. Keep the test synchronous and leave lifespace_test at base only if the other integration tests re-upgrade it (they do through the module fixture).
   - Drift check: after upgrade to head run alembic check with the same subprocess approach (python -m alembic -c apps/api/alembic.ini check) against the test database and assert it exits 0 (no differences between the models and the migration). If alembic check reports differences, fix the model or the migration so they match.

VERIFY (run each, record the real result)
1. make db-up, make migrate (the development database moves to 0002), then: docker compose exec -T db psql -U lifespace -d lifespace -Atc "select version_num from alembic_version" prints 0002, and "select count(*) from app_settings" prints 1.
2. make migrate-down then make migrate again (both succeed).
3. make api-format, make api-lint (zero errors, 4 contracts kept), make api-typecheck (zero errors), make api-test (all pass, zero warnings, record the counts).
4. Run the integration tests twice in a row (cd apps/api && for i in 1 2; do uv run pytest tests/integration -q 2>&1 | tail -n 1; done). No flakiness and no leftover rows between runs.
5. git grep -n "lifespace_dev_only" -- apps/api/migrations apps/api/alembic.ini prints nothing.
6. git status --short is empty after the commits.

COMMIT
Small conventional commits, for example "feat(infrastructure): add task, history, settings, and idempotency models", "feat(infrastructure): add alembic revision 0002", "feat(infrastructure): add domain to row mapping", "test(infrastructure): add schema constraint and mapping tests". git status must be clean afterwards. Leave the database running.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first, at most 8 lines).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Public names the next part needs (modules, classes, functions you created).
Finish by telling the user: "Part 3 is finished. Start a new session for the next part."
```
