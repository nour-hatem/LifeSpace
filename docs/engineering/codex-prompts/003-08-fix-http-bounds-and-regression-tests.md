# Task 003, Correction 2 of 2: HTTP bounds, regression tests, and generated types

**Status:** Ready. Review findings for milestone M2 (persistence and task API), reproduced against the running API on 2026-11-19. Sized for a 200K token context. Send in order.
**Depends on:** Task 003 Parts 1 to 6 (already on the branch)
**Branch:** `m2/persistence-task-api` (stay on it)
**Binding decisions:** `docs/engineering/adr/0002-m2-persistence-and-task-api.md` (items 20 to 24 are new)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line: `Read the file docs/engineering/codex-prompts/003-08-fix-http-bounds-and-regression-tests.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 003 | M2 | CORRECTION 2 OF 2 | HTTP bounds, regression tests, and generated types

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
2. Read AGENTS.md and docs/engineering/adr/0002-m2-persistence-and-task-api.md (items 20 to 24 are binding). Confirm Correction 1 is on the branch: apps/api/src/lifespace/domain/limits.py exists. If not, stop and tell the user to run Correction 1 first.
3. Read api/schemas.py, api/tasks.py, api/errors.py, and the Makefile targets api-spec, api-spec-check, api-types, and api-types-check.
4. Docker must be reachable. Run make api-setup, make db-up, make migrate, then make check: everything must pass before you change anything.

THE DEFECTS (architect review, all reproduced against the running API with a hostile-input probe)
D1. Poison row. POST /api/v1/tasks with deadline {"kind":"date","value":"9999-12-31"} returns 500 AND the task is already committed (the use case commits before it builds the response view, and is_overdue overflows on "day + 1 day"). From then on GET /api/v1/tasks (the whole list) and GET of that task return 500 permanently.
D2. Text the database cannot store gives 500: a title or description containing the NUL character, and a lone surrogate (JSON "\ud800").
D3. Integers beyond the database range give 500: estimate_minutes 10**12, and DELETE /api/v1/tasks/{id}?version=2**70 (PATCH and the lifecycle actions give a misleading 409 with a huge number).
D4. Datetime extremes give 500: a deadline "0001-01-01T00:00:00+05:00", a deadline "9999-12-31T23:59:59-05:00", a schedule near year 1 (OverflowError during UTC conversion).
D5. A well formed cursor with an out-of-range instant (for example the instant 0001-01-01T00:00:00+14:00) gives 500 instead of 422 invalid_cursor.
D6. Logs contain task content: a database error is logged with SQLAlchemy "[parameters: (...)]", which includes the title and description.
D7. There are no length limits (a 2 MB title is accepted).

Correction 1 fixed the domain, application, and infrastructure causes. This session closes the HTTP layer and proves the fixes end to end.

OBJECTIVE
Bound the numeric inputs at the HTTP layer, regenerate the OpenAPI document and the TypeScript types, add the hostile-input regression tests at API level, and update the documentation. No new dependency.

DELIVERABLES
1. api/schemas.py and api/tasks.py (ADR 0002 item 20): every version (TaskPatch, ActionBody, CancelBody bodies and the DELETE query parameter) is an integer from 1 to 2,147,483,647 (strict integer in bodies, Query(ge=1, le=2147483647) for the DELETE). estimate_minutes in TaskCreate and TaskPatch is a strict integer with ge=1 and le=2147483647. Text length, character, and date range rules stay in the domain (single source of truth); do not duplicate them in the schemas. A violation of the bounds above is the generic 422 validation_failed.
2. Make sure a DomainValidationError raised while mapping request bodies (for example TimeInterval or the date deadline range checks inside api/mapping.py) is translated to the application ValidationFailedError so the response is 422 with result validation_failed and the right field, never a 500. Check every call of a domain constructor inside api/mapping.py is wrapped in translate_domain_errors().
3. Regenerate the committed OpenAPI document and the TypeScript types with make api-types, then run make api-spec-check and make api-types-check. The only expected diff is the new numeric bounds.
4. Tests (typed, warnings are errors):
   - apps/api/tests/unit/api/test_robustness_api.py with the in-memory fakes (same style as test_tasks_api.py). Each case below must return the stated status with content type application/problem+json and a body whose code and result are correct, and must never return 500:
     - POST title with the NUL character, description with NUL, a lone surrogate sent as raw JSON bytes b'{"title": "\\ud800"}', a 501 character title, a 20,001 character description, an empty and a whitespace-only title: 422 validation_failed with field "title" or "description" where the domain provides it.
     - POST estimate_minutes 0, -1, 2147483648, 10**12, 1.5, true: 422.
     - POST deadline date 9999-12-31, 0001-01-01, 1969-12-31, 3000-01-01; deadline datetime 0001-01-01T00:00:00+05:00, 9999-12-31T23:59:59-05:00, 1969-12-31T23:59:59Z, 3000-01-01T00:00:00Z; scheduled with those bounds: 422 validation_failed.
     - POST deadline date 2999-12-31 and 1970-01-01, a 500 character title, a 20,000 character description, estimate 2147483647: 201.
     - PATCH, POST /complete, and DELETE with version 0, 2147483648, and 2**70: 422. A cancel reason of 1,001 characters: 422; 1,000: 200.
     - GET /api/v1/tasks and /history with cursors: deeply nested JSON (5000 opening brackets, base64url encoded), non-ASCII text, valid shape with an out-of-range instant, valid shape with a bad UUID: 422 invalid_cursor.
     - Poison-row regression: after every rejected creation above, GET /api/v1/tasks returns 200 and contains none of the rejected tasks, and a valid task created afterwards is listed.
     - Idempotency-Key with a valid key and a body containing the NUL title: 422 and the key stays unused (a later valid request with the same key creates the task).
     - PUT /api/v1/settings with a 65 character zone and with a NUL zone: 422 with field "timezone".
   - apps/api/tests/integration/test_api_robustness.py (real PostgreSQL, same fixtures as test_api_tasks.py): the hostile creations (NUL, lone surrogate, estimate 10**12, date 9999-12-31, datetime 0001..., oversized title) return 422 and leave the tasks table empty (select count); the list endpoint answers 200 afterwards; DELETE with version 2**70 is 422; and a captured log record check (caplog) proves that no log record produced during a 500-free hostile run contains the marker text of a rejected title ("SECRET-TITLE-MARKER").
   - Keep the contract test for the 13 operation ids passing and update it if the schemas changed shape.
5. Documentation (only these): apps/api/README.md gets an "Input limits (ADR 0002 item 20)" section with the table of limits and ranges and the rule that every violation is 422 and never 500; README.md needs no change unless it contradicts the limits; AGENTS.md: add at most one line under the machine or testing rules saying that user input must be bounded and that tests must include hostile inputs (keep the file at 120 lines or fewer). Do not modify anything under docs/.

VERIFY AND AUDIT (run each and record the real result)
1. make api-format, make api-lint (zero errors, 4 contracts kept, api-spec-check passes), make api-typecheck, make api-test (record unit and integration counts), make web-lint, make web-typecheck, make web-test, make web-build.
2. make api-types and make api-types-check pass. make check passes from a clean state. Record the totals.
3. Live probe with real servers (background pattern, development database after make migrate). With curl, run these and show the status codes (every one must be as stated, none may be 500):
   - POST /api/v1/tasks with {"title":"a\u0000b"} gives 422.
   - POST with {"title":"x","deadline":{"kind":"date","value":"9999-12-31"}} gives 422, then GET /api/v1/tasks gives 200.
   - POST with {"title":"x","estimate_minutes":1000000000000} gives 422.
   - DELETE /api/v1/tasks/00000000-0000-0000-0000-000000000000?version=1180591620717411303424 gives 422.
   - GET /api/v1/tasks?cursor=<base64url of 5000 opening brackets> gives 422 with code invalid_cursor.
   - POST a normal task, GET it, delete it with its version (204) so no test data remains in the development database. Stop the servers and confirm ports 8000 and 5173 are free.
4. grep the API log produced during step 3 for the marker characters of rejected content and for "[parameters:" (must print nothing).
5. git diff main --stat: apps/api, apps/web/src/shared/api (generated files only), README or AGENTS.md lines named above; docs/ only the architect files; no dependency file changed. git status clean.

COMMIT
Small conventional commits, for example "fix(api): bound version and estimate inputs", "test(api): add hostile input regression tests", "chore(web): regenerate api spec and types", "docs: document input limits". git status must be clean afterwards.

FINAL REPORT FOR BOTH CORRECTIONS (replaces the short report, maximum 40 lines): which defects D1 to D7 are fixed and how, the live probe status codes, test counts, deviations and why, and the output of git log --oneline main..HEAD (the last 12 lines).

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first, at most 8 lines).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Public names the next part needs (modules, classes, functions you created).
Finish by telling the user: "Correction 2 of 2 is finished."
```
