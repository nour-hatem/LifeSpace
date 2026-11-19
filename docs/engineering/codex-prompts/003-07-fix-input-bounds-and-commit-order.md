# Task 003, Correction 1 of 2: Domain, application, and infrastructure hardening

**Status:** Ready. Review findings for milestone M2 (persistence and task API), reproduced against the running API on 2026-11-19. Sized for a 200K token context. Send in order.
**Depends on:** Task 003 Parts 1 to 6 (already on the branch)
**Branch:** `m2/persistence-task-api` (stay on it)
**Binding decisions:** `docs/engineering/adr/0002-m2-persistence-and-task-api.md` (items 20 to 24 are new)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line: `Read the file docs/engineering/codex-prompts/003-07-fix-input-bounds-and-commit-order.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 003 | M2 | CORRECTION 1 OF 2 | Domain, application, and infrastructure hardening

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
1. git branch --show-current must print m2/persistence-task-api and git status --short must be empty.
2. Read AGENTS.md, docs/engineering/adr/0001-m1-domain-decisions.md, and docs/engineering/adr/0002-m2-persistence-and-task-api.md (items 20 to 24 are new and binding).
3. Read domain/time.py, deadline.py, task.py, lifecycle.py, errors.py; application/tasks.py, settings.py, errors.py; infrastructure/db.py, cursor.py, repositories.py.
4. Docker must be reachable for the integration tests: run make api-setup, make db-up, make migrate, then make api-test. All 400 tests must pass before you change anything.

THE DEFECTS (architect review, all reproduced against the running API with a hostile-input probe)
D1. Poison row. POST /api/v1/tasks with deadline {"kind":"date","value":"9999-12-31"} returns 500 AND the task is already committed (the use case commits before it builds the response view, and is_overdue overflows on "day + 1 day"). From then on GET /api/v1/tasks (the whole list) and GET of that task return 500 permanently.
D2. Text the database cannot store gives 500: a title or description containing the NUL character, and a lone surrogate (JSON "\ud800").
D3. Integers beyond the database range give 500: estimate_minutes 10**12, and DELETE /api/v1/tasks/{id}?version=2**70 (PATCH and the lifecycle actions give a misleading 409 with a huge number).
D4. Datetime extremes give 500: a deadline "0001-01-01T00:00:00+05:00", a deadline "9999-12-31T23:59:59-05:00", a schedule near year 1 (OverflowError during UTC conversion).
D5. A well formed cursor with an out-of-range instant (for example the instant 0001-01-01T00:00:00+14:00) gives 500 instead of 422 invalid_cursor.
D6. Logs contain task content: a database error is logged with SQLAlchemy "[parameters: (...)]", which includes the title and description.
D7. There are no length limits (a 2 MB title is accepted).

OBJECTIVE
Fix D1, D2, D3, D4, D5, D6, and D7 at the right layer (domain rules, application ordering, infrastructure), with regression tests. The HTTP schemas, the generated OpenAPI and types, and the API level tests belong to Correction 2, do not touch apps/web or the OpenAPI files in this session.

DELIVERABLES
1. domain/limits.py (new, standard library plus lifespace.domain.errors only), ADR 0002 item 20:
   - Constants: MIN_INSTANT = datetime(1970, 1, 1, tzinfo=UTC), MAX_INSTANT = datetime(3000, 1, 1, tzinfo=UTC) (exclusive), MIN_DATE = date(1970, 1, 1), MAX_DATE = date(2999, 12, 31), MAX_TITLE_LENGTH = 500, MAX_DESCRIPTION_LENGTH = 20_000, MAX_REASON_LENGTH = 1_000, MAX_INT32 = 2_147_483_647.
   - ensure_text(value: str, *, field: str, max_length: int) -> str: raises DomainValidationError (with the field) when the text is longer than max_length, contains the NUL character, or contains a surrogate code point (U+D800 to U+DFFF); returns the value unchanged otherwise.
   - ensure_date_in_range(value: date, *, field: str) -> date: raises DomainValidationError unless MIN_DATE <= value <= MAX_DATE.
2. domain/time.py (ADR 0002 items 20 and 21):
   - as_instant(value, *, field: str = "value"): a datetime whose UTC conversion overflows (OverflowError) raises DomainValidationError with the field and a message that says the value is outside the supported range. Existing callers keep working.
   - ensure_instant_in_range(value: datetime, *, field: str) -> datetime: requires an aware datetime (reuse ensure_aware) whose UTC instant satisfies MIN_INSTANT <= instant < MAX_INSTANT, otherwise DomainValidationError with the field. It must never raise OverflowError.
   - TimeInterval.__post_init__ validates start and end with ensure_instant_in_range (fields "start" and "end"), then the order rule as before.
3. domain/deadline.py: DateDeadline validates its day with ensure_date_in_range (field "day"); DateTimeDeadline validates "at" with ensure_instant_in_range. is_deadline_passed must never raise OverflowError for any valid deadline and any aware now (an out-of-range now raises DomainValidationError with field "now").
4. domain/task.py: Task.__post_init__ additionally enforces: title length 1 to MAX_TITLE_LENGTH and the ensure_text rules (check order: empty, untrimmed, then ensure_text); description (when not None) ensure_text with MAX_DESCRIPTION_LENGTH; cancellation_reason ensure_text with MAX_REASON_LENGTH; created_at, updated_at, completed_at, canceled_at with ensure_instant_in_range; estimate_minutes at most MAX_INT32 (message "estimate_minutes must not exceed 2147483647"). create_task and edit_task validate now with ensure_instant_in_range(field "now"). Keep every existing validation message for the existing rules unchanged.
5. domain/lifecycle.py: transition_task validates now with ensure_instant_in_range (field "now") and the stripped reason, when given, with ensure_text (MAX_REASON_LENGTH, field "reason"). A blank reason still becomes None.
6. application/tasks.py (ADR 0002 items 20 and 22):
   - In create_task (both the keyed and the keyless path), edit_task, and transition_task, build the TaskView (the _to_view call) BEFORE await uow.commit(), then commit, then return the view. A failure while building the view must leave nothing committed.
   - Add a private check _check_version(expected_version: int) used at the start of edit_task, delete_task, and transition_task: a value below 1 or above MAX_INT32 (or not an int) raises ValidationFailedError with field "version" before any database access.
   application/settings.py: update_timezone also rejects a time zone name longer than 64 characters or containing the NUL character with ValidationFailedError(field "timezone"), before calling ZoneInfo.
7. infrastructure/db.py (ADR 0002 item 23): create_engine passes hide_parameters=True to create_async_engine, keeping pool_pre_ping and everything else as is.
8. infrastructure/cursor.py and repositories.py (ADR 0002 item 24): decode_cursor also catches RecursionError and OverflowError and raises InvalidCursorError; _decode_keyset rejects (InvalidCursorError) a cursor whose instant is outside [MIN_INSTANT, MAX_INSTANT), a non-ISO instant, a naive instant, a bad UUID, and any DomainValidationError or OverflowError raised while normalizing it.
9. Tests (typed, warnings are errors; keep every existing test passing unchanged, do not weaken any assertion):
   - Domain (apps/api/tests/unit/domain/test_limits.py and additions): ensure_text accepts exactly MAX length and rejects MAX plus one, NUL, "\ud800", "\udfff", and accepts emoji and Arabic text; titles of 1 and 500 characters pass, 501 and an empty or whitespace-only title fail with field "title"; description 20,000 passes and 20,001 fails; reason 1,000 passes and 1,001 fails (task and transition); date deadlines 1970-01-01 and 2999-12-31 pass, 1969-12-31, 3000-01-01, date.min, and date.max fail with field "day"; datetime deadlines and schedule bounds at 1970-01-01T00:00:00Z pass and one microsecond earlier fails, 2999-12-31T23:59:59.999999Z passes and 3000-01-01T00:00:00Z fails, "0001-01-01T00:00:00+05:00" and "9999-12-31T23:59:59-05:00" fail with DomainValidationError (never OverflowError); as_instant of those two values raises DomainValidationError; estimate_minutes 2,147,483,647 passes and 2,147,483,648 fails; is_deadline_passed with DateDeadline(2999-12-31) in Africa/Cairo and in Pacific/Kiritimati (UTC+14) and Pacific/Pago_Pago (UTC-11) does not overflow and returns the right boolean; a property test (hypothesis) over valid dates in range, all six test zones, and instants in range proves is_deadline_passed and is_overdue never raise.
   - Application (tests/unit/application): create_task, edit_task, and transition_task leave NOTHING committed when building the view fails: make the fake settings repository return an unknown time zone "Invalid/Zone" (extend the fake minimally, for example a settable timezone attribute on the shared store) so _to_view raises, assert the exception propagates and the store has no new task, no new version, no event, and no idempotency record. Out-of-range deadline, NUL title, and oversized title on create raise ValidationFailedError with the right field and store nothing. A poison-row regression: after a failed creation with deadline 9999-12-31 the list still works and returns the earlier tasks. Version checks: edit_task, delete_task, and transition_task with version 0, -1, and 2**31 raise ValidationFailedError(field "version") and change nothing. update_timezone rejects a 65 character name and a name with NUL.
   - Infrastructure (unit, no database, tests/unit/infrastructure): decode_cursor raises InvalidCursorError for deeply nested JSON (5000 opening brackets), for non-ASCII text, for a non-base64 string, for the wrong number of parts; _decode_keyset rejects the out-of-range and naive instants listed above and accepts a normal cursor produced by _encode_keyset. 
   - Integration (real PostgreSQL): hide_parameters works: execute an INSERT through the engine that violates the check constraint title_not_blank with a description containing the marker "SECRET-MARKER-12345", catch the IntegrityError, and assert the marker is not in str(error). A repository round trip with a description of exactly 20,000 characters and a title of exactly 500 characters including Arabic and emoji characters.

VERIFY (run each and record the real result)
1. make api-format, make api-lint (zero errors, 4 contracts kept), make api-typecheck (zero errors).
2. make api-test (all pass, zero warnings; record unit and integration counts). Run the domain and application tests three times in a row. No flakiness.
3. Mutation sanity (do each, confirm a test fails, then git checkout the file): (a) move the commit in create_task back before building the view; (b) remove hide_parameters=True; (c) remove the OverflowError handling in as_instant.
4. Purity: grep -rnE "(datetime\.now|date\.today|uuid4|uuid7)" apps/api/src/lifespace/domain apps/api/src/lifespace/application prints nothing; domain imports only the standard library and lifespace.domain.
5. git diff main --stat: only apps/api src and tests (no apps/web, no OpenAPI files, no docs beyond the two architect files). git status clean.

COMMIT
Small conventional commits, for example "fix(domain): add input limits and range checks", "fix(application): build views before commit and validate versions", "fix(infrastructure): hide sql parameters and harden cursor decoding", "test: add robustness regression tests". git status must be clean afterwards.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first, at most 8 lines).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Public names the next part needs (modules, classes, functions you created).
Finish by telling the user: "Correction 1 of 2 is finished. Start a new session for Correction 2."
```
