# Codex Prompt 001: M0 Foundation

**Status:** Reference specification for the whole task. It is executed as 6 self-contained parts (`001-01` to `001-06` in this folder) because the implementation agent has a 200K token context. If a part and this file disagree, the part wins.
**Milestone:** M0 Foundation (local, single user)
**Branch:** `m0/foundation`
**Blueprint:** `docs/engineering/TECHNICAL_BLUEPRINT.md` v1.1

---

```text
TASK 001 | M0 FOUNDATION | LifeSpace (local, single user)

ROLE
You are the implementation agent for LifeSpace and the only agent that writes application source code. A separate technical architect reviews every change from the Git diff against the blueprint. Implement exactly this task and nothing else.

READ FIRST (in this order, completely, before writing anything)
1. docs/README.md
2. docs/engineering/TECHNICAL_BLUEPRINT.md (all sections. Sections 2 to 9 and 14 to 18 are binding for this task)
3. docs/engineering/CLAUDE_INSTRUCTIONS.md sections 3, 6, 7, 10, 12, and 13
4. docs/business/BUSINESS_RULES.md section 1
5. docs/product/PRD.md section 14 (non-functional requirements)
Then run git status and create branch m0/foundation from main. If the docs conflict with this task or leave something ambiguous, stop and ask. Never invent product behavior.

OBJECTIVE
Build a small, verified local foundation: a monorepo with a FastAPI backend, a React frontend, a PostgreSQL 18 database in Docker Compose, a migration baseline, health checks, an error and logging baseline, quality tooling, and enforced layer boundaries. This task contains zero product features.

SCOPE RULES (owner decisions, binding)
- Local single user application. No authentication, registration, sessions, OAuth, user accounts, user_id columns, or multi-tenancy. Authentication is deferred and is NOT an approved requirement.
- No Redis, vector database, message broker, agent framework, cloud infrastructure, CI, Dependabot, Dockerfiles for the apps, or deployment configuration.
- No unnecessary abstractions. Prefer the simplest code that satisfies this task.

MACHINE FACTS (do not fight them, do not change them)
- Ubuntu 26.04. Node 22.22.3 (nvm), npm 10.9.8, Python 3.14.4, uv 0.11.28, Docker CLI 29.7.2 with Docker Desktop, Docker Compose v5.3.1, GNU Make 4.4.1. pnpm is not installed and must not be used.
- Do not install, upgrade, or remove any global tool or global package. Do not use sudo. Do not run npm install -g, pip install, or uv python install. Python dependencies live only in the project's isolated apps/api/.venv created by uv. Set UV_PYTHON_DOWNLOADS=never wherever the Makefile calls uv so no interpreter is ever downloaded.
- The repository path contains a space ("/home/nour/AI Factory/LifeSpace"). Quote every path in the Makefile and scripts, and prefer paths relative to the repository root.
- The login shell exports NODE_ENV=production. With that value npm silently skips devDependencies. Handle it in the project: apps/web/.npmrc contains include=dev, and the npm scripts dev, build, preview, and test run through "env -u NODE_ENV".
- A host PostgreSQL 18 service already listens on 127.0.0.1:5432. Never connect to it, change it, or use that port. The Compose database is published on 127.0.0.1:5433.
- Docker Desktop must be running with the desktop-linux context selected. Do not change the Docker context or start or stop Docker Desktop. If Docker is not reachable, stop and report it.
- The filesystem holding /home can be nearly full. make doctor must fail with a clear message when less than 3 GB is free. If a command fails with ENOSPC, stop and report it. Do not work around it.

APPROVED VERSIONS (exact, final)
Backend, declared in apps/api/pyproject.toml, requires-python ">=3.14,<3.15", locked in a committed uv.lock:
- Runtime: fastapi==0.133.1, starlette>=1.3.1, uvicorn[standard]==0.52.4, pydantic==2.13.4, pydantic-settings==2.14.2, sqlalchemy[asyncio]==2.0.50, asyncpg==0.31.0, alembic==1.18.4.
- Dev group: pytest==9.1.0, pytest-asyncio==1.4.0, httpx==0.28.1, ruff, mypy, import-linter. Lock them at their current releases (verified working: ruff 0.17.4, mypy 2.4.1, import-linter 2.16).
- Use hatchling as the build backend with the src layout so the package is importable as lifespace.
Frontend, exact versions saved with save-exact (set save-exact=true in apps/web/.npmrc), locked in a committed package-lock.json:
- Runtime: react 19.3.1, react-dom 19.3.1, @tanstack/react-query 5.107.1.
- Dev: vite 8.3.8, @vitejs/plugin-react 6.3.0, typescript 6.0.3 (NOT 7, typescript-eslint requires below 6.1), vitest 5.1.0, jsdom 31.0.0, @testing-library/react 16.3.3, @testing-library/dom 10.4.2, @testing-library/jest-dom 7.0.1, eslint 9.39.5 (NOT 10, eslint-plugin-jsx-a11y requires 9 or lower), @eslint/js 9.39.5, typescript-eslint 8.72.2, eslint-plugin-react-hooks 7.1.1, eslint-plugin-jsx-a11y 6.10.2, globals 17.14.0, prettier 3.10.1, @types/react 19.3.0, @types/react-dom 19.3.0, @types/node 22.20.5.
- Never use --force, --legacy-peer-deps, overrides, or resolutions. If a listed version cannot be installed, stop and report the exact error.
- Do not add any dependency that is not listed (no React Router, Zustand, Motion, d3, Radix, Tailwind, zod, UI kits, structlog, psycopg, pip-audit, Playwright).

LAYOUT (create only directories that contain real files, no .gitkeep placeholders)
Root: .editorconfig, .env.example, .nvmrc (22.22.3), AGENTS.md, Makefile, docker-compose.yml, scripts/doctor.sh, scripts/smoke.sh, infra/postgres/init/01-create-test-db.sql. Update only the "Getting started" section of README.md. Append to .gitignore only for files a tool you add produces and that are not already ignored.
apps/api: pyproject.toml, uv.lock, alembic.ini, migrations/ (env.py, script.py.mako, versions/0001_baseline.py), src/lifespace/{__init__.py, config.py, main.py, api/{__init__.py, health.py, errors.py}, infrastructure/{__init__.py, db.py, logging.py}}, tests/{unit, integration}, README.md.
apps/web: .npmrc, package.json, package-lock.json, index.html, vite.config.ts, tsconfig.json, eslint.config.js, .prettierrc.json, README.md, src/{main.tsx, App.tsx, shared/api/client.ts, features/system-status/ApiStatus.tsx, test/setup.ts} and their tests.
Do not create domain/, application/, or ai/ packages yet. They arrive in later milestones.

DELIVERABLES

1. Docker Compose and environment
- docker-compose.yml with top-level name lifespace and one service, db, using postgres:18. Publish 127.0.0.1:${POSTGRES_PORT:-5433}:5432 only. Named volume mounted at /var/lib/postgresql (the postgres:18 image requires this path, not /var/lib/postgresql/data). Mount ./infra/postgres/init at /docker-entrypoint-initdb.d read-only. Healthcheck with pg_isready. Credentials from POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB with local-only defaults lifespace, lifespace_dev_only, lifespace.
- infra/postgres/init/01-create-test-db.sql creates the database lifespace_test. State in the README that init scripts run only when the volume is first created, so a change needs make db-reset.
- .env.example documents every variable below with local-only values. make setup copies it to .env only if .env does not exist. .env is ignored by Git and never committed.
  LIFESPACE_ENVIRONMENT=development, LIFESPACE_DATABASE_URL=postgresql+asyncpg://lifespace:lifespace_dev_only@127.0.0.1:5433/lifespace, LIFESPACE_TEST_DATABASE_URL=postgresql+asyncpg://lifespace:lifespace_dev_only@127.0.0.1:5433/lifespace_test, LIFESPACE_LOG_LEVEL=INFO, API_PROXY_TARGET=http://127.0.0.1:8000, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT=5433.

2. Makefile and scripts (all targets run from the repository root)
- doctor: runs scripts/doctor.sh. Fail (non-zero) when Node is not >=22.22.2 and <23, npm or uv is missing, uv cannot find Python 3.14 (uv python find 3.14), the docker CLI is missing, the Docker daemon is unreachable (print: start Docker Desktop and run docker context use desktop-linux), free space on the repository filesystem is below 3 GB, or port 5433 is in use by something other than the lifespace db container. Warn (do not fail) when NODE_ENV is production, when ports 8000 or 5173 are in use, or when a PostgreSQL service is listening on 5432 (informational, it is not used).
- setup: copy .env.example to .env if missing, uv sync --locked for apps/api, npm ci for apps/web (through env -u NODE_ENV).
- lock: uv lock for apps/api.
- db-up: docker compose up -d --wait. db-down: docker compose down (keeps data). db-reset: asks for confirmation, then docker compose down -v and up -d --wait (development only).
- migrate: alembic upgrade head using apps/api/alembic.ini.
- dev-api: uvicorn --factory lifespace.main:create_app --reload on 127.0.0.1:8000 with the reload directory limited to apps/api/src.
- dev-web: Vite dev server on 127.0.0.1:5173 with strictPort.
- lint: ruff check, ruff format --check, lint-imports, eslint, prettier --check.
- format: ruff format and prettier --write.
- typecheck: mypy (strict) and tsc --noEmit.
- test: pytest for apps/api and vitest run for apps/web.
- build: vite build.
- check: lint, typecheck, test, build.
- smoke: scripts/smoke.sh. With both dev servers running it requests /api/health and /api/health/ready on the API (port 8000) and /api/health through the Vite proxy (port 5173) with curl -fsS, prints PASS or FAIL per check, and exits non-zero on any failure.

3. Backend (apps/api)
- config.py: typed Settings (pydantic-settings, env prefix LIFESPACE_) with environment (development, test, production), database_url (required), test_database_url (optional), log_level (default INFO). Fail fast on missing required values. Load the repository-root .env resolved from the file location, not the working directory, so it works from the repo root and from apps/api. Never print or log the database password.
- main.py: create_app(settings=None, *, ready_check=None) factory. It configures logging, builds the async engine from settings unless a ready_check is injected, stores the readiness callable on app.state, registers the error handlers and the health router, and disposes the engine in the application lifespan. There is no module-level app. main.py is the composition root.
- api/health.py: GET /api/health returns 200 {"status": "ok"} and never touches the database. GET /api/health/ready returns 200 {"status": "ready"} when the readiness callable returns True, otherwise 503 {"status": "unavailable"}. The route reads the callable from app.state through a FastAPI dependency. The body never contains exception text or connection details.
- api/errors.py: handlers that return application/problem+json (RFC 9457) with the members type (urn:lifespace:problem:<code>), title, status, detail, and code. Cover request validation (422, code validation_failed), HTTP errors such as 404 (code not_found) and other statuses (code failed), and unhandled exceptions (500, code failed, generic detail, no exception text in the body, full details in logs only).
- infrastructure/db.py: create_engine(url) returning an AsyncEngine, a SQLAlchemy MetaData with a fixed naming_convention for constraints and indexes, and async check_database(engine) that runs select 1 with a short timeout and returns True or False. Catching Exception here is deliberate at a health boundary, so add a justified noqa for ruff BLE001. No models and no tables.
- infrastructure/logging.py: configure logging once at startup with the standard library, level from settings. Request bodies and credentials are never logged.
- Alembic: configured with the async template and asyncpg. env.py uses sqlalchemy.url from the Alembic config when set, otherwise the URL from Settings, and uses the MetaData from infrastructure/db.py. alembic.ini contains no credentials. Create exactly one revision with --rev-id 0001, named baseline, with empty upgrade and downgrade and a clear docstring. It must work when started from the repository root.
- Tooling in pyproject.toml: ruff with line length 100 and select E, F, I, B, UP, SIM, BLE, RUF; mypy strict over src and tests; pytest with asyncio_mode auto, testpaths, and filterwarnings = ["error"]. If a third-party deprecation warning appears, add a narrowly scoped ignore (module and message) with a comment and report it.
- import-linter contracts (include_external_packages = true), exactly these two for now:
  - api must not import lifespace.infrastructure or sqlalchemy.
  - infrastructure must not import lifespace.api.
- Tests use httpx.AsyncClient with httpx.ASGITransport. Do NOT use fastapi.testclient or starlette.testclient (deprecated with httpx). For the unhandled exception test use ASGITransport(raise_app_exceptions=False). Always run the app lifespan in tests (app.router.lifespan_context) so the engine is disposed.
- Tests to write:
  - Unit: /api/health returns 200 and the exact body. /api/health/ready returns 200 with a passing fake callable and 503 with a failing one, and the exception text never appears in the body. An unknown route returns problem+json 404 with the expected members. A validation failure returns problem+json 422 with code validation_failed. An unhandled exception returns a generic problem+json 500 and the exception text appears only in captured logs. Settings fail fast without a database URL and reject an invalid environment value.
  - Integration (real PostgreSQL, test database): check_database returns True against the test database and False for a wrong password. After upgrading to head, the alembic_version table holds 0001, and downgrading to base empties it. Integration tests never skip silently. If PostgreSQL is unreachable they fail with a message saying to run make db-up.

4. Frontend (apps/web)
- Vite, React, TypeScript strict with noUncheckedIndexedAccess, ESLint 9 flat config (typescript-eslint recommended, jsx-a11y recommended via jsxA11y.flatConfigs.recommended, react-hooks via reactHooks.configs.flat.recommended), Prettier, Vitest with jsdom and Testing Library.
- The Vite dev server listens on 127.0.0.1:5173 with strictPort and proxies /api to API_PROXY_TARGET (default http://127.0.0.1:8000). The app has no API base URL setting and always calls /api on its own origin.
- package.json scripts: dev, build, preview, test (all through env -u NODE_ENV), lint, format, format:check, typecheck.
- src/shared/api/client.ts: a small fetch wrapper that parses a problem+json error body into a typed ApiError. src/features/system-status/ApiStatus.tsx: a status line that uses TanStack Query against GET /api/health. src/App.tsx renders the text "LifeSpace" and the status line. src/main.tsx mounts the app inside QueryClientProvider. There is no router and no error boundary yet.
- The status line shows loading, success, and error as explicit text and never by color alone.
- No visual design: no colors, no design tokens, no UI library, no CSS framework.
- Tests: the API client parses problem+json into ApiError and handles a non-problem error body. The status line renders loading, then success when the request succeeds, and the error state when it fails.

5. Documentation
- Root README.md "Getting started": prerequisites, the one-time Docker preparation (start Docker Desktop, docker context use desktop-linux), the disk space note, the exact first-run sequence, all make targets, dev URLs, and a troubleshooting list (Docker not reachable, port in use, ENOSPC, NODE_ENV=production, db-reset after changing init scripts).
- apps/api/README.md (layer responsibilities, dependency rules, how to run tests) and apps/web/README.md (commands, version decisions and why TypeScript is 6.0 and ESLint is 9).
- AGENTS.md at the root, maximum 120 lines, for future Codex sessions: documentation reading order and authority, the three-role workflow, the domain invariants (a deadline is not a scheduled time, completed is not canceled, a bubble position is not a schedule, the AI proposes and the application validates), layer dependency rules, the machine facts above, common commands, testing rules, no secrets in code, no product decisions without approval, branch and commit conventions, and the final report format.

NON-GOALS (do not implement)
- Any product feature: tasks, users, authentication, scheduling, projects, reminders, workspace layout, the AI Companion, or any domain model, table, or migration beyond the empty baseline.
- Routing, error boundaries, request IDs, a design system, visual identity, bubble UI, or animation.
- CI workflows, Dependabot, audit tooling, Playwright, app Dockerfiles, deployment, or security headers.
- Any change to files under docs/.

CONSTRAINTS
- Do not create or commit .env, secrets, or credentials.
- Do not commit to main. Do not push. Do not merge. Commit on m0/foundation in small logical commits with conventional commit messages.
- Code comments and documentation are written in English.
- Keep every file focused and simple.

ACCEPTANCE CRITERIA (each must be demonstrated with real command output)
1. make doctor passes, and reports the free disk space.
2. make setup succeeds from a clean checkout, including when NODE_ENV=production is exported. Show that the devDependencies are installed (for example npm ls --depth=0 lists vite and vitest).
3. make db-up starts PostgreSQL 18 and docker compose ps shows it healthy on 127.0.0.1:5433. Both lifespace and lifespace_test databases exist (psql through docker compose exec).
4. make migrate succeeds and select version_num from alembic_version returns 0001.
5. make dev-api starts the backend. curl http://127.0.0.1:8000/api/health returns 200 {"status":"ok"}. /api/health/ready returns 200 with the database up and 503 after docker compose stop db, with no error details in the body.
6. make dev-web starts the frontend. curl http://127.0.0.1:5173/api/health returns the same 200 body through the proxy, and a browser at http://127.0.0.1:5173 shows "LifeSpace" with the status line in its success state.
7. make smoke passes with both servers running.
8. make test passes for both apps with zero warnings. Report the number of tests per app.
9. make lint, make typecheck, and make build pass with zero errors and zero warnings.
10. Each of the two import-linter contracts is proven. Add a deliberate violation for each, confirm lint-imports fails, then revert it. Report the outputs. Leave no violation in the final tree.
11. No .env, secret, or credential is tracked. uv.lock and package-lock.json are committed. git status is clean after the final commit.
12. No file under docs/ is modified (git diff main --stat -- docs prints nothing).
13. The layout matches blueprint section 5 and nothing that the blueprint assigns to a later milestone exists.

VERIFICATION COMMANDS (run in this order and report the results)
  make doctor
  make setup
  make db-up
  make migrate
  make check
  make dev-api            (second terminal)
  make dev-web            (third terminal)
  make smoke
  docker compose stop db && curl -i http://127.0.0.1:8000/api/health/ready ; docker compose start db
  NODE_ENV=production make setup
  git diff main --stat -- docs
  git status
  git log --oneline main..HEAD

FINAL REPORT (required)
- Summary of what was built.
- Files created, grouped by area.
- Every command you ran with its real result (pass or fail, test counts). Mark anything you could not run, with the reason.
- Dependency versions actually installed, and any deviation from the approved versions with the exact error.
- Deviations from this task and why.
- Open questions or risks.
- Output of git log --oneline main..HEAD.
```
