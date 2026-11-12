# Codex Prompt 001: M0 Foundation

**Status:** Ready to send. Technical decisions are final per `docs/engineering/TECHNICAL_BLUEPRINT.md` (baseline v1).
**Milestone:** M0 Foundation
**Branch:** `m0/foundation`
**Authority:** Product owner delegated technical decisions to the architect on 2026-11-12.

---

```text
TASK 001 | M0 FOUNDATION | LifeSpace

ROLE
You are the implementation agent for LifeSpace and the only agent that writes application source code. A separate technical architect reviews every change from the Git diff against the blueprint. Implement exactly this task and nothing else.

READ FIRST (in this order, completely, before writing anything)
1. docs/README.md
2. docs/engineering/TECHNICAL_BLUEPRINT.md (all sections; sections 2 to 9 and 16 to 18 are binding for this task)
3. docs/engineering/CLAUDE_INSTRUCTIONS.md sections 3, 6, 7, 10, 12, and 13
4. docs/business/BUSINESS_RULES.md section 1
5. docs/product/PRD.md section 14 (non-functional requirements)
Then run git status and create branch m0/foundation from main. If the docs conflict with this task or leave something ambiguous, stop and ask. Never invent product behavior.

OBJECTIVE
Build a verified technical foundation: the monorepo, both applications, tooling, local PostgreSQL, migration infrastructure, health checks, an error and logging baseline, CI, and enforced architecture boundaries. This task contains zero product features.

APPROVED TECHNOLOGY DECISIONS (final, do not substitute)
- Node 26 LTS. pnpm 12 through corepack (set the packageManager field). Python 3.14. uv. PostgreSQL 18 (postgres:18). Docker Compose.
- Backend: FastAPI, Uvicorn (standard), Pydantic v2, pydantic-settings, SQLAlchemy 2.1 async, psycopg 3 (binary), Alembic, structlog. Dev: pytest, pytest-asyncio, httpx, ruff, mypy (strict), import-linter, pip-audit.
- Frontend: React 19, TypeScript strict, Vite, @vitejs/plugin-react, React Router (library mode), TanStack Query. Dev: Vitest, jsdom, Testing Library (react, jest-dom, user-event), ESLint with typescript-eslint, eslint-plugin-react-hooks, and eslint-plugin-jsx-a11y, Prettier.
- The blueprint section 3 lists the version line for each tool. Within a line use the newest release that is at least 14 days old. Enforce this with tooling: set pnpm minimumReleaseAge to 14 days (check the pnpm 12 documentation for the exact setting and file), and lock Python dependencies using uv with an exclude-newer cutoff 14 days before today (implement as a make lock target that computes the cutoff).
- If a selected major version is not supported by the rest of the toolchain (for example TypeScript 7 with typescript-eslint, or ESLint 10 with a plugin), use the newest major that every tool supports. Never use --force, --legacy-peer-deps, peer dependency overrides, or resolutions. Record every such fallback in apps/web/README.md under "Dependency notes".
- Do not add: Playwright, Zustand, Motion, d3, Radix, Tailwind, any UI kit, zod, react-hook-form, date-fns, any LLM SDK, Redis, Qdrant, Celery, or any dependency not listed above.

REPOSITORY LAYOUT TO CREATE (see blueprint section 5)
Create only directories that contain real files. No .gitkeep placeholders and no empty folders.
- Root: .editorconfig, .env.example, .nvmrc, .python-version, AGENTS.md, Makefile, docker-compose.yml, scripts/smoke.sh, infra/postgres/init/01-create-test-db.sql, .github/workflows/ci.yml, .github/dependabot.yml. Update the existing README.md "Getting started" section only. Append to .gitignore only if a tool you add produces files that are not yet ignored.
- apps/api and apps/web as described below.

DELIVERABLES

1. Root tooling
- docker-compose.yml: one service only, postgres:18. Bind to 127.0.0.1 only. Named volume. For the postgres:18 image mount the volume at /var/lib/postgresql (not /var/lib/postgresql/data). Healthcheck using pg_isready. Credentials and port come from POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT with local-only defaults. Mount infra/postgres/init as the init directory.
- infra/postgres/init/01-create-test-db.sql creates the lifespace_test database. Note in the README that init scripts run only on first volume creation.
- .env.example documents every variable in the table below. Never create or commit a real .env.
- Makefile targets: setup, lock, db-up, db-down, db-reset (development only, asks for confirmation), migrate, dev-api, dev-web, lint, format, typecheck, test, build, check, audit, smoke. lint runs ruff check, ruff format --check, lint-imports, eslint, and prettier --check. check runs lint, typecheck, test, and build for both apps. audit runs pip-audit and pnpm audit and reports without failing the build. All targets work from the repository root.
- scripts/smoke.sh: curl /api/health and /api/health/ready on the API, then /api/health through the Vite dev server proxy. Exit non-zero on any failure and print which check failed.
- AGENTS.md (maximum 120 lines) for future Codex sessions: documentation reading order and authority, the three-role workflow, domain invariants (a deadline is not a scheduled time, completed is not canceled, a bubble position is not a schedule, the AI proposes and the application validates), the layer dependency rules, common commands, testing expectations, no secrets in code, no product decisions without approval, branch and commit conventions, and the final report format.
- .github/workflows/ci.yml: backend job (setup uv, ruff check, ruff format --check, mypy, lint-imports, pytest against a postgres:18 service container, pip-audit as non-blocking) and frontend job (corepack and pnpm, node from .nvmrc, eslint, prettier --check, tsc, vitest, build, pnpm audit as non-blocking). Use official actions by major version tag. Steps must match the Makefile commands.
- .github/dependabot.yml for uv, npm, github-actions, and docker with a 14-day cooldown.

2. Backend (apps/api)
- pyproject.toml with requires-python ">=3.14,<3.15", the src layout, a committed uv.lock, and tool configuration for ruff, mypy (strict), pytest (asyncio auto mode is acceptable), and import-linter.
- Packages under src/lifespace: domain, application, infrastructure, api, ai. Each __init__.py contains a one-paragraph docstring stating the layer's responsibility and what it may not import. These packages hold no other code except what is listed below.
- config.py: typed Settings (pydantic-settings, env prefix LIFESPACE_) for environment name, database URL, test database URL, log level, and CORS allowed origins. Fail fast on missing required values. No defaults for secrets. Reject a wildcard origin. Settings must load correctly whether the app is started from the repository root through make or from apps/api.
- main.py: create_app() factory and a module-level app. main.py is the composition root and the only place that wires infrastructure into the application.
- infrastructure/logging.py: structlog configured once at startup, JSON output unless environment is development. Request bodies and headers carrying credentials are never logged.
- infrastructure/db/: async engine and session factory built from settings, and base.py holding a SQLAlchemy MetaData with a fixed naming_convention for constraints and indexes. No models, no tables.
- api/middleware.py: request ID middleware. Read or generate X-Request-ID, bind it to the structlog context, return it on every response.
- api/errors.py: exception handlers returning RFC 9457 application/problem+json with fields type (urn:lifespace:problem:<code>), title, status, detail, code, result, and request_id. Cover validation errors (422, code validation_failed), HTTP errors such as 404, and unhandled exceptions (500, generic detail, no exception text, full detail only in logs). Allowed result values: rejected, validation_failed, conflict, not_found, unauthorized, failed, unknown_pending_verification.
- GET /api/health: liveness. Returns 200 {"status": "ok"}. Must not touch the database.
- GET /api/health/ready: readiness. Returns 200 {"status": "ready"} when the database answers SELECT 1, otherwise 503 {"status": "unavailable"}. The body never contains exception text or connection details.
- Readiness design: application/ports.py defines a ReadinessProbe Protocol. infrastructure/db implements it with SELECT 1. The api layer depends only on the Protocol, obtained through a FastAPI dependency. main.py wires the implementation.
- CORS: only when LIFESPACE_CORS_ALLOWED_ORIGINS is non-empty, explicit origins only. Empty means same origin only and no CORS middleware.
- Alembic in apps/api (alembic.ini and migrations/), configured for async, reading the URL from settings and the MetaData from infrastructure/db/base.py. Create exactly one revision, a baseline with an empty upgrade and downgrade and a clear docstring. make migrate runs alembic upgrade head.
- import-linter contracts in pyproject.toml (set include_external_packages = true where forbidden external imports are checked):
  - domain must not import fastapi, starlette, sqlalchemy, psycopg, pydantic, httpx, structlog, openai, anthropic, langchain, langgraph, or any other lifespace layer.
  - application must not import fastapi, starlette, sqlalchemy, lifespace.api, lifespace.infrastructure, or lifespace.ai.
  - api must not import lifespace.infrastructure or sqlalchemy.
  - ai must not import lifespace.infrastructure, lifespace.api, fastapi, or sqlalchemy.
  - infrastructure must not import lifespace.api or lifespace.ai.
  The lifespace.main module is the composition root and is outside these contracts.
- Tests (tests/unit and tests/integration):
  - /api/health returns 200 and the exact body.
  - /api/health/ready returns 200 with a passing fake probe, and 503 with a failing fake probe whose exception text never appears in the body.
  - An unknown route returns a problem+json 404 with the expected fields and an X-Request-ID header.
  - A request validation failure returns a problem+json 422 with code validation_failed.
  - An unhandled exception returns a generic problem+json 500 and the exception text appears only in captured logs.
  - Settings fail fast when a required variable is missing and reject a wildcard CORS origin.
  - Integration: the real database probe passes against PostgreSQL, fails against an unreachable URL, and after make migrate the alembic_version table holds the baseline revision.
  - Database tests must never skip silently. If PostgreSQL is unreachable they fail with a message that says to run make db-up.

3. Frontend (apps/web)
- Vite, React, TypeScript strict (including noUncheckedIndexedAccess), pnpm with a committed pnpm-lock.yaml, packageManager and engines fields, ESLint flat config, Prettier, Vitest with jsdom and Testing Library.
- Dev server on 127.0.0.1:5173 proxying /api to API_PROXY_TARGET (default http://127.0.0.1:8000). The app has no API base URL setting. It always calls /api on its own origin.
- src/main.tsx, src/app/ (providers with QueryClientProvider and a router created in library mode, a top-level error boundary, and a single route "/"), src/shared/api/ (a small fetch wrapper that parses problem+json into a typed ApiError), src/features/system-status/ (the placeholder feature below), src/test/ (test setup).
- The "/" route renders the text "LifeSpace" and one status line showing API reachability, using TanStack Query against GET /api/health. Loading, success, and error states are each shown as explicit text and never by color alone.
- Apply no visual design: no colors, no design tokens, no UI library, no CSS framework. Browser defaults plus minimal layout CSS only.
- Tests: the API client parses a problem+json error into ApiError. The status line renders loading, then success when the request succeeds, and the error state when it fails.
- Scripts: dev, build, lint, format, typecheck, test.
- apps/web/README.md with commands and the "Dependency notes" section.

4. Documentation
- Update the "Getting started" section of the root README.md with prerequisites (nvm and Node 26, corepack enable, uv, Docker with Compose, GNU Make), the exact first-run command sequence, the make targets, the dev URLs, and a short troubleshooting list (port in use, database not healthy, db-reset after changing init scripts, corepack download prompt).
- apps/api/README.md with layer responsibilities, the dependency rules, and how to run tests.

ENVIRONMENT VARIABLES (document all of them in .env.example)
- LIFESPACE_ENVIRONMENT (development, test, production), LIFESPACE_DATABASE_URL (postgresql+psycopg://), LIFESPACE_TEST_DATABASE_URL, LIFESPACE_LOG_LEVEL, LIFESPACE_CORS_ALLOWED_ORIGINS (empty by default).
- API_PROXY_TARGET (Vite dev server only).
- POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT (Compose only), with local-only defaults.

NON-GOALS (do not implement)
- Any product feature: tasks, users, authentication, sessions, scheduling, projects, reminders, workspace layout, the AI Companion, or any domain model or table.
- Any design system, visual identity, bubble UI, or animation.
- Playwright, Dockerfiles for the apps, deployment configuration, security headers, or generated API clients.
- Any file under docs/ may not be modified.

CONSTRAINTS
- Do not create or commit .env, secrets, or credentials.
- Do not commit to main. Do not push. Do not merge. Commit on m0/foundation in small logical commits with conventional commit messages.
- Code comments and documentation are written in English.
- Keep every file focused and simple. Do not add abstractions that this task does not require.

ACCEPTANCE CRITERIA (each must be demonstrated with real command output)
1. From a clean checkout, make setup succeeds for both apps.
2. make db-up starts PostgreSQL 18 and docker compose ps shows it healthy. Both lifespace and lifespace_test databases exist.
3. make migrate succeeds. docker compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "select version_num from alembic_version" returns the baseline revision.
4. make dev-api starts the backend. curl http://127.0.0.1:8000/api/health returns 200 {"status":"ok"}. /api/health/ready returns 200 with the database up and 503 after docker compose stop db, with no error details in the body.
5. make dev-web starts the frontend. curl http://127.0.0.1:5173/api/health returns the same 200 body through the proxy, and the page in a browser shows "LifeSpace" and the API status line in its success state.
6. make smoke passes with both servers running.
7. make test passes for both apps. Report the number of tests.
8. make lint, make typecheck, and make build pass with zero errors and zero warnings.
9. Each import-linter contract is proven. For every contract, add a deliberate violation, run lint-imports and confirm it fails, then revert. Report the outputs. Leave no violation in the final tree.
10. make audit runs and its output is reported.
11. The CI workflow is valid YAML and runs the same commands as the Makefile.
12. No .env, secret, or credential is tracked. Lockfiles are committed. git status is clean after the final commit.
13. No file under docs/ is modified (git diff main --stat -- docs shows nothing).
14. The layout matches blueprint section 5. Nothing exists that the blueprint marks as a later milestone.

VERIFICATION COMMANDS (run in this order and report the results)
  corepack enable
  make setup
  make db-up
  make migrate
  make check
  make dev-api     (second terminal)
  make dev-web     (third terminal)
  make smoke
  docker compose stop db && curl -i http://127.0.0.1:8000/api/health/ready && docker compose start db
  git diff main --stat -- docs
  git status
  git log --oneline main..HEAD

FINAL REPORT (required)
- Summary of what was built.
- Files created, grouped by area.
- Every command you ran with its real result (pass or fail, test counts). Mark anything you could not run, with the reason.
- Dependency versions actually installed, and every fallback from the blueprint's version lines with the reason.
- Deviations from this task and why.
- Open questions or risks.
- Output of git log --oneline main..HEAD.
```
