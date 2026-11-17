# Task 003, Part 6 of 6: OpenAPI export, TypeScript types, documentation, and M2 audit

**Status:** Ready. Milestone M2 (persistence and task API) is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and depends only on the repository, not on earlier conversation.
**Depends on:** Parts 1 to 5 of Task 003, Docker database
**Branch:** `m2/persistence-task-api`
**Binding decisions:** `docs/engineering/adr/0002-m2-persistence-and-task-api.md` (provisional defaults, owner may override)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/003-06-openapi-types-and-audit.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 003 | M2 PERSISTENCE AND TASK API | PART 6 OF 6 | OpenAPI export, TypeScript types, documentation, and M2 audit

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
3. Confirm Part 5 exists: apps/api/src/lifespace/api/tasks.py, api/schemas.py, and the integration test file tests/integration/test_api_tasks.py. Read main.py (create_app parameters), Makefile, scripts/smoke.sh, apps/web/package.json, apps/web/eslint.config.js, apps/web/.prettierignore, apps/web/tsconfig.json, and the current README.md, apps/api/README.md, and AGENTS.md.
4. Docker must be reachable. Run make api-setup, make web-setup, make db-up, make migrate, then make check: everything must pass before you change anything.

OBJECTIVE
Export the OpenAPI document, generate and commit TypeScript types with a drift check, extend the smoke script, update the documentation, and run the full M2 audit. No new dependency in apps/api or apps/web.

DELIVERABLES
1. src/lifespace/openapi_export.py (a composition root module like main.py, NOT inside lifespace.api): a function export_openapi_json() -> str that builds the app with create_app using dummy settings (Settings(_env_file=None, database_url="postgresql+asyncpg://openapi:openapi@127.0.0.1:1/openapi")) and injected stubs so no database connection is ever attempted (a ready_check that returns True and a uow_factory that raises RuntimeError if called), then returns app.openapi() as canonical JSON (json.dumps with sort_keys=True, indent=2, ensure_ascii=False, plus a trailing newline). A main() that takes an output path argument and writes the file. Runnable as: uv run python -m lifespace.openapi_export <path>. It must work without a database and without a .env file.
2. Makefile targets (tab indentation, keep .PHONY updated, quote paths):
   - api-spec: write apps/web/src/shared/api/openapi.json with the exporter.
   - api-spec-check: export to a temporary file and diff it against the committed apps/web/src/shared/api/openapi.json; non-zero exit and a clear message ("OpenAPI spec is out of date. Run: make api-types") on any difference. This target needs no network and no database.
   - api-types: api-spec, then generate apps/web/src/shared/api/schema.d.ts with: cd apps/web && env -u NODE_ENV npx --yes openapi-typescript@7.13.0 src/shared/api/openapi.json -o src/shared/api/schema.d.ts (ADR 0002 item 18: it is deliberately not a project dependency because it declares a TypeScript 5 peer; do not add it to package.json).
   - api-types-check: regenerate the types into a temporary file with the same command and diff it with the committed schema.d.ts (needs network the first time, then the npm cache); message "Types are out of date. Run: make api-types".
   - Add api-spec-check to the lint target (through api-lint or lint) so make check catches a stale spec. Do not add api-types-check to make check.
3. Generated files, committed: apps/web/src/shared/api/openapi.json and apps/web/src/shared/api/schema.d.ts. Add schema.d.ts and openapi.json to apps/web/.prettierignore and add src/shared/api/schema.d.ts to the ESLint ignores in eslint.config.js so the generated files never fail lint or format checks. tsc must still compile the generated declarations (make web-typecheck passes). Add one tiny typed helper apps/web/src/shared/api/types.ts that re-exports convenient aliases (Task = components["schemas"]["TaskOut"], TaskPage, TaskEvent, Settings) and one Vitest test apps/web/src/shared/api/types.test.ts that only proves the aliases compile and that an object literal satisfying Task type-checks (type-level test with expectTypeOf from vitest). No runtime API client yet.
4. scripts/smoke.sh: add a fourth check, GET http://127.0.0.1:8000/api/v1/tasks must return HTTP 200 and a body containing the text "items" (the API needs the migrated database). Keep the existing three checks and the PASS or FAIL printing.
5. Documentation (only these files): README.md (status line: M0, M1, and M2 implemented, next is M3; one short paragraph and a table of the main endpoints); apps/api/README.md (a "Persistence and API (M2)" section: layers present, the application use cases and ports, the database tables, the migration workflow including the subprocess rule for async tests, the endpoint table with status codes, the problem+json codes and results from ADR 0002 item 13, the idempotency and pagination rules, and the make targets api-spec, api-spec-check, api-types, api-types-check); AGENTS.md (change only what is needed to say that the application and persistence layers now exist and to list the new make targets, keep it at 120 lines or fewer). Do not modify anything under docs/.

VERIFY AND AUDIT (run each, record the real result; keep output short)
1. make api-format, make api-lint (zero errors, 4 contracts kept, api-spec-check passes), make api-typecheck, make api-test (record unit, integration, and total counts), make web-lint, make web-typecheck, make web-test, make web-build.
2. make api-types (network needed once) then make api-types-check (passes) and make api-spec-check (passes). Then prove the drift check: change one description string in the committed openapi.json (git stash is not needed, just edit and revert with git checkout), confirm make api-spec-check fails with the message, and revert.
3. make check from a clean state (the full gate across both apps) must pass. Record the totals.
4. End to end with real servers (background pattern): make db-up, make migrate, start make dev-api and make dev-web, run make smoke (four PASS), and run through the proxy: curl -s -X POST http://127.0.0.1:5173/api/v1/tasks -H "Content-Type: application/json" -d '{"title":"Smoke task"}' returns 201 with a version 1 body, then GET http://127.0.0.1:5173/api/v1/tasks lists it. Delete that task with its version so no test data remains in the development database. Stop both servers and confirm ports 8000 and 5173 are free.
5. Layers and purity: lint-imports shows 4 contracts kept; grep -rnE "(now\(|today\(|uuid4|uuid7)" apps/api/src/lifespace/domain apps/api/src/lifespace/application prints nothing; grep -rn "lifespace.infrastructure" apps/api/src/lifespace/api apps/api/src/lifespace/application prints nothing.
6. git diff main --stat: changes limited to apps/api, apps/web (src/shared/api, eslint.config.js, .prettierignore only), Makefile, scripts/smoke.sh, README.md, AGENTS.md. docs/ must show only the architect's files (git diff main --stat -- docs may list docs/engineering/adr/0002-m2-persistence-and-task-api.md and docs/engineering/codex-prompts/003-*.md). package.json and package-lock.json of apps/web unchanged, apps/api runtime dependencies unchanged, uv.lock unchanged.
7. git status --short is empty. git log --oneline main..HEAD.

COMMIT
Small conventional commits, for example "feat(api): add openapi export and spec drift check", "feat(web): add generated api types", "chore: extend smoke script", "docs: document persistence and the task api". git status must be clean afterwards.

FINAL REPORT FOR THE WHOLE TASK (replaces the short report for this part, maximum 50 lines): summary of what was built; the endpoint list; the database tables; the result of each audit item above with real output summaries; test counts (domain, application, infrastructure, api, integration, web); deviations and why; open questions or risks; the output of git log --oneline main..HEAD.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first, at most 8 lines).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Public names the next part needs (modules, classes, functions you created).
Finish by telling the user: "Part 6 is finished. Start a new session for the next part."
```
