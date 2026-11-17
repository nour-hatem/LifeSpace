# Task 003, Part 1 of 6: Application foundation: errors, models, ports, fakes, create and read use cases

**Status:** Ready. Milestone M2 (persistence and task API) is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and depends only on the repository, not on earlier conversation.
**Depends on:** M1 merged into main
**Branch:** `m2/persistence-task-api`
**Binding decisions:** `docs/engineering/adr/0002-m2-persistence-and-task-api.md` (provisional defaults, owner may override)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/003-01-application-foundation.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 003 | M2 PERSISTENCE AND TASK API | PART 1 OF 6 | Application foundation: errors, models, ports, fakes, create and read use cases

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
1. Branch handling as in GIT RULES. git status --short must be empty.
2. Read AGENTS.md, docs/engineering/TECHNICAL_BLUEPRINT.md, docs/engineering/adr/0001-m1-domain-decisions.md, and docs/engineering/adr/0002-m2-persistence-and-task-api.md.
3. Read apps/api/src/lifespace/domain/task.py, lifecycle.py, overdue.py, errors.py, and time.py so you reuse their exact names (Task, TaskStatus, Priority, Category, TaskSource, UNSET, Unset, create_task, edit_task, StatusEvent, TransitionResult, transition_task, is_overdue, as_instant, DomainValidationError, InvalidTransitionError, TimeInterval, Deadline). Read apps/api/pyproject.toml (the import-linter section) and apps/api/tests/conftest.py.
4. Run make api-setup. Run make db-up if Docker is reachable, then make api-test: all 199 tests must pass before you change anything. (This part needs no database for its own tests.)
5. If apps/api/src/lifespace/application already exists, inspect it and continue from what is missing.

OBJECTIVE
Create the application layer foundation: typed errors, models, ports, in-memory fakes for tests, and the use cases create_task (with idempotency), get_task, list_tasks, get_settings, and update_timezone. No database, no HTTP, no migration.

DELIVERABLES
1. apps/api/src/lifespace/application/__init__.py: docstring (the application layer holds use cases and the ports they need, imports only the standard library and lifespace.domain, never reads the clock or generates ids).
2. application/errors.py (ADR 0002 items 4, 12, 13, 14, 15):
   - ApplicationError(Exception) with attributes code (str), result (str), message (str).
   - NotFoundError (code not_found, result not_found). StaleVersionError(expected_version: int, current_version: int | None) (code stale_version, result conflict). ValidationFailedError(message, field: str | None = None) (code validation_failed, result validation_failed). TransitionRejectedError(message, from_status: str, to_status: str) (code invalid_transition, result rejected). IdempotencyKeyReuseError (code idempotency_key_reuse, result rejected). IdempotencyInProgressError (code idempotency_in_progress, result conflict). InvalidCursorError (code invalid_cursor, result validation_failed).
   - A context manager translate_domain_errors() that converts DomainValidationError into ValidationFailedError (keeping the field) and InvalidTransitionError into TransitionRejectedError, chaining the original with "from".
3. application/models.py: frozen, slotted dataclasses (use PEP 695 syntax class Page[T] for the generic):
   - StoredTask(task: Task, version: int). StoredStatusEvent(id: UUID, event: StatusEvent). TaskView(stored: StoredTask, is_overdue: bool). Page[T](items: tuple[T, ...], next_cursor: str | None).
   - TaskFilter(statuses: frozenset[TaskStatus] = frozenset(), category: Category | None = None, priority: Priority | None = None). An empty statuses set means all statuses.
   - CreateTaskCommand(title, description=None, category=None, priority=None, estimate_minutes=None, deadline=None, scheduled=None, status=TaskStatus.PLANNED, source=TaskSource.MANUAL).
   - TaskChanges with fields title, description, category, priority, estimate_minutes, deadline, scheduled, each defaulting to UNSET (same types as edit_task parameters). Used by Part 2.
   - IdempotencyInput(key: str, fingerprint: str). IdempotencyRecord(key: str, request_fingerprint: str, task_id: UUID). CreateResult(view: TaskView, replayed: bool). AppSettings(timezone: str).
4. application/ports.py: Protocols, all repository methods async:
   - Clock.now() -> datetime (aware). IdGenerator.new_id() -> UUID.
   - TaskRepository: add(task) -> StoredTask (version 1); get(task_id) -> StoredTask | None (never returns a deleted task); list(task_filter, *, limit, cursor) -> Page[StoredTask]; save(task, *, expected_version) -> StoredTask (raises StaleVersionError or NotFoundError; the new version is expected_version + 1); soft_delete(task_id, *, expected_version, now) -> None (same errors); add_event(event_id, event) -> None; list_events(task_id, *, limit, cursor) -> Page[StoredStatusEvent].
   - SettingsRepository: get_timezone() -> str; set_timezone(timezone, *, now) -> None.
   - IdempotencyRepository: get(key) -> IdempotencyRecord | None; add(record, *, now) -> None (raises IdempotencyInProgressError when the key already exists).
   - UnitOfWork: attributes tasks, settings, idempotency; async __aenter__ returning the unit of work, async __aexit__, async commit(), async rollback(). UnitOfWorkFactory = Callable[[], UnitOfWork].
5. application/tasks.py (this part: create, get, list) and application/settings.py. Each use case is an async function taking explicit dependencies (uow_factory, clock, ids where needed). Every use case opens "async with uow_factory() as uow", calls await uow.commit() only when it wrote something, and wraps domain calls in translate_domain_errors().
   - create_task(uow_factory, clock, ids, command, *, idempotency: IdempotencyInput | None = None) -> CreateResult. Without a key: build the domain task with domain.create_task(task_id=ids.new_id(), now=clock.now(), ...), add it, commit, return the view with replayed False. With a key, inside one unit of work: look the key up. Found with the same fingerprint: load the task; if it still exists return its current view with replayed True and do not create anything; if it no longer exists raise IdempotencyKeyReuseError. Found with a different fingerprint: raise IdempotencyKeyReuseError. Not found: create the task, add an IdempotencyRecord in the same transaction, commit (ADR 0002 item 14).
   - get_task(uow_factory, clock, task_id) -> TaskView (NotFoundError when missing).
   - list_tasks(uow_factory, clock, task_filter, *, limit, cursor=None) -> Page[TaskView]. limit must be between 1 and 200, otherwise ValidationFailedError with field "limit" (ADR 0002 item 15).
   - Every returned TaskView carries is_overdue computed with domain is_overdue(task, clock.now(), ZoneInfo(timezone)) where timezone comes from uow.settings.get_timezone() (ADR 0002 item 8). Read the timezone once per call.
   - get_settings(uow_factory) -> AppSettings. update_timezone(uow_factory, clock, timezone) -> AppSettings: validate with zoneinfo.ZoneInfo (an empty string, a name with a path traversal, or an unknown name raises ValidationFailedError with field "timezone"), persist with set_timezone, commit.
6. In-memory fakes for tests: apps/api/tests/unit/application/__init__.py and apps/api/tests/unit/application/fakes.py with FakeClock (settable now, aware UTC), SequentialIdGenerator (UUID(int=n) from a counter), and InMemoryUnitOfWork plus a shared InMemoryStore implementing EVERY port method of ADR 0002 (tasks with versions and soft delete, filters, keyset-style pagination ordered by created_at descending then id descending, status events ordered by occurred_at descending then id descending, settings default "UTC", idempotency records). Transaction behavior: entering a unit of work works on a copy, commit() writes the copy back, leaving without commit discards it. The fake cursor is a plain string "<iso instant>|<uuid>" and a malformed cursor raises InvalidCursorError. These fakes are reused by Parts 2 and 5, so keep them simple and typed.
7. Tests in apps/api/tests/unit/application (pytest, typed, warnings are errors; asyncio_mode is auto, so async tests need no marker):
   - create_task: default PLANNED, INBOX accepted, other statuses rejected with ValidationFailedError, an empty title raises ValidationFailedError with field "title", version is 1, created_at and updated_at equal the fake clock, the id comes from the generator, source defaults to MANUAL, a failed creation stores nothing (rollback).
   - Idempotency: first call creates (replayed False); the same key and fingerprint replays (replayed True, same id, exactly one task stored); the same key with another fingerprint raises IdempotencyKeyReuseError; a replay after the task was soft-deleted in the store raises IdempotencyKeyReuseError; a creation that fails validation leaves no idempotency record.
   - get_task: found, missing raises NotFoundError, soft-deleted raises NotFoundError.
   - list_tasks: ordering newest first, filters by status (several statuses), category, priority, pagination (limit 2 over 5 tasks gives 3 pages with no duplicates and no gaps and next_cursor None on the last page), limit 0 and limit 201 raise ValidationFailedError with field "limit", a malformed cursor raises InvalidCursorError, an empty store returns an empty page.
   - is_overdue in views: a date-only deadline with the stored timezone Africa/Cairo flips exactly at the verified instant 2026-04-23T22:00:00Z for the deadline date 2026-04-23 (the instant before it is not overdue); the same task is judged differently under UTC after update_timezone; a task without a deadline is never overdue.
   - Settings: default timezone "UTC"; update to Africa/Cairo persists; "Mars/Base", "" and "../etc/passwd" raise ValidationFailedError with field "timezone" and change nothing.
8. Architecture contract: add a fourth import-linter contract to apps/api/pyproject.toml, type forbidden, name "application must stay clean", source lifespace.application, forbidden modules: fastapi, starlette, sqlalchemy, asyncpg, alembic, pydantic, pydantic_settings, httpx, uvicorn, lifespace.api, lifespace.infrastructure, lifespace.config.

VERIFY (run each, record the real result)
1. make api-format, make api-lint (zero errors, 4 import contracts kept), make api-typecheck (zero errors), make api-test (all pass, zero warnings, record the count; if Docker is unreachable run only: cd apps/api && uv run pytest tests/unit -q and say so).
2. Commit first, then prove the new contract: add "import sqlalchemy" to application/tasks.py, run make api-lint, confirm lint-imports fails on "application must stay clean", run git checkout -- apps/api/src, confirm git status --short is empty.
3. Run the application tests three times in a row (cd apps/api && for i in 1 2 3; do uv run pytest tests/unit/application -q 2>&1 | tail -n 1; done). No flakiness.
4. Purity: grep -rnE "(now\(|today\(|uuid4|uuid7)" apps/api/src/lifespace/application must print nothing (reword docstrings that mention these calls). grep -rnE "^(import|from) " apps/api/src/lifespace/application | grep -vE "(dataclasses|enum|datetime|zoneinfo|typing|collections|contextlib|uuid|lifespace\.(domain|application)|__future__|abc)" must print nothing.

COMMIT
Small conventional commits, for example "feat(application): add errors, models, and ports", "feat(application): add create, get, list, and settings use cases", "test(application): add in-memory fakes and use case tests", "chore(api): add application import contract". git status must be clean afterwards.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first, at most 8 lines).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Public names the next part needs (modules, classes, functions you created).
Finish by telling the user: "Part 1 is finished. Start a new session for the next part."
```
