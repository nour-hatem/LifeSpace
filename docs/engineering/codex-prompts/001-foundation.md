# Codex Prompt 001: M0 Foundation

**Status:** Ready to send once decisions D2 (stack) and D3 (monorepo layout) are approved.
**Milestone:** M0 Foundation
**Branch:** `m0/foundation`

---

```text
TASK 001 | M0 FOUNDATION | LifeSpace

ROLE
You are the implementation agent for LifeSpace. A separate technical architect reviews every change from the Git diff. Implement exactly this task and nothing else.

BEFORE WRITING ANY CODE
1. Read docs/README.md, docs/engineering/TECHNICAL_BLUEPRINT.md (sections 2 to 5), docs/engineering/CLAUDE_INSTRUCTIONS.md (sections 3, 6, 7), and docs/business/BUSINESS_RULES.md (section 1).
2. Run git status. Create the branch m0/foundation from main.
3. If anything in this task conflicts with the docs or is ambiguous, stop and ask. Do not invent product behavior.

OBJECTIVE
Establish the approved technical foundation: monorepo skeleton, tooling, local database, CI, and enforced architecture boundaries. This task contains zero product features.

APPROVED DECISIONS
- Backend: Python 3.12, FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2.x async with asyncpg, Alembic, uv.
- Database: PostgreSQL 16 through Docker Compose.
- Frontend: React, TypeScript (strict), Vite, pnpm, React Router, TanStack Query.
- Layout: apps/api and apps/web.
- Use current stable versions. Do not use any package version published within the last 14 days. Commit lockfiles.

DELIVERABLES

1. Repository root
- docker-compose.yml with one service only: postgres:16, named volume, healthcheck, credentials and port read from environment variables with safe local-only defaults.
- .env.example documenting every variable used by either app. Never create or commit a real .env.
- Makefile with targets: setup, db-up, db-down, dev-api, dev-web, lint, typecheck, test, check. The check target runs lint, typecheck, and test for both apps.
- AGENTS.md for future Codex sessions, maximum 120 lines, covering: documentation reading order and authority, the three-role workflow, domain invariants (deadline is not scheduled time, completed is not canceled, bubble position is not schedule, AI proposes and the application validates), layer dependency rules, common commands, testing expectations, no secrets in code, no product decisions without approval, and the final report format.
- .github/workflows/ci.yml with two jobs. Backend job: ruff check, ruff format --check, mypy, lint-imports, pytest with a postgres service. Frontend job: eslint, tsc, vitest, build. Steps must match the Makefile commands.
- .vscode/extensions.json with recommended extensions only.
- Append to .gitignore only if a tool you add produces files that are not yet ignored.

2. Backend (apps/api)
- pyproject.toml with requires-python, uv lockfile, and the package layout from docs/engineering/TECHNICAL_BLUEPRINT.md section 5.
- Packages under src/lifespace: domain, application, infrastructure, api, ai. Each __init__.py holds a one-paragraph docstring stating the layer's responsibility and what it may not import. No other code in these packages except what is listed below.
- main.py: application factory create_app() and a module-level app. main.py is the composition root and is the only place that wires infrastructure into the application.
- config.py: typed Settings from environment covering environment name, database URL, allowed CORS origins, and log level. No default values for secrets. Reject a wildcard CORS origin.
- GET /health: liveness. Returns {"status": "ok"}. Must not touch the database.
- GET /health/ready: readiness. Returns 200 {"status": "ready"} when the database answers a trivial query, otherwise 503 {"status": "unavailable"}. The body must never contain exception text or connection details.
- Readiness design: application/ defines a ReadinessProbe protocol. infrastructure/ implements it with a trivial database query. The api layer depends only on the protocol. main.py wires the implementation.
- infrastructure/: async SQLAlchemy engine and session factory built from settings. No models and no tables.
- Alembic configured for async, reading the URL from settings. Create no migration revisions.
- Logging: structured logging configured once at startup. Request bodies must never be logged.
- CORS: explicit origins from settings only.
- import-linter contracts in pyproject.toml:
  - domain must not import fastapi, sqlalchemy, asyncpg, pydantic, httpx, openai, anthropic, langchain, langgraph, or any lifespace layer.
  - application must not import fastapi, sqlalchemy, lifespace.api, lifespace.infrastructure, or lifespace.ai.
  - api must not import lifespace.infrastructure or sqlalchemy.
  - ai must not import lifespace.infrastructure, lifespace.api, fastapi, or sqlalchemy.
  - infrastructure must not import lifespace.api or lifespace.ai.
- Tooling: ruff (lint and format), mypy in strict mode, pytest, pytest-asyncio, httpx.
- Tests:
  - /health returns 200 and the expected body.
  - /health/ready returns 200 with a passing fake probe.
  - /health/ready returns 503 with a failing fake probe, and the body contains no exception text.
  - Settings fail fast when a required variable is missing.
  - Settings reject a wildcard CORS origin.
  - Integration test of the real database probe against PostgreSQL, running locally through Compose and in CI through the service container.

3. Frontend (apps/web)
- Vite, React, TypeScript strict. ESLint (typescript-eslint, react-hooks, jsx-a11y), Prettier, Vitest, Testing Library.
- Pin the Node LTS version in .nvmrc and the engines field of package.json.
- Folders under src, each containing only a .gitkeep unless listed below: app, design-system, features, shared/api, shared/lib.
- src/app: providers (QueryClientProvider, router) and a single route "/".
- The "/" route renders the text "LifeSpace" and one line showing API reachability, using TanStack Query against GET /health. The base URL comes from VITE_API_BASE_URL. Loading, success, and error states must each be shown as explicit text, never color alone.
- Apply no visual design: no colors, no design tokens, no UI library, no CSS framework. Browser defaults plus minimal layout CSS only.
- Tests: the status line renders the loading state, then the success state when the request succeeds, and the error state when it fails.
- Scripts: dev, build, lint, typecheck, test, format.

CONSTRAINTS
- No product code of any kind: no tasks, users, authentication, AI integration, scheduling, or domain models.
- Do not add Playwright, Redis, Qdrant, any LLM SDK, any UI component library, Tailwind, or Zustand.
- Do not edit any file under docs/.
- Do not create or commit .env, secrets, or credentials.
- Do not commit to main. Do not push. Do not merge. Commit on m0/foundation in small logical commits using conventional commit messages.
- Keep code comments and documentation in English.

ACCEPTANCE CRITERIA
1. make setup installs both apps' dependencies from a clean checkout.
2. make db-up starts PostgreSQL and the healthcheck reports healthy.
3. make dev-api serves the API. GET /health returns 200 {"status": "ok"}. GET /health/ready returns 200 with the database up and 503 with it stopped, and never exposes error details.
4. make dev-web serves the frontend and the page shows the API status line.
5. make check passes: ruff, mypy strict, lint-imports, pytest, eslint, tsc, vitest, and the production build.
6. Each import-linter contract is proven to work. For every contract, add a deliberate violation, run lint-imports and confirm it fails, then revert the violation. Report the outputs. Leave no violation in the final tree.
7. The CI workflow is valid and runs the same commands as the Makefile.
8. git status is clean after the final commit. No .env or secret is tracked. Lockfiles are committed.
9. No file under docs/ is modified.

FINAL REPORT (required)
- Summary of what was built.
- Files created, grouped by area.
- Every command you ran with its real result (pass or fail, test counts). Mark anything you could not run, with the reason.
- Deviations from this task and why.
- Open questions or risks.
- Output of git log --oneline for the branch.
```
