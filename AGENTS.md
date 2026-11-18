# AGENTS.md

Instructions for any coding agent working on LifeSpace, including OpenCode.
Read this file before changing the repository.

## Documentation order and authority

`docs/README.md` is the index. Read these in order, stopping when the task is answered:

1. `docs/product/PRD.md`
2. `docs/business/BUSINESS_RULES.md`
3. `docs/product/USER_FLOWS.md`
4. `docs/engineering/AGENT_SPEC.md`
5. `docs/design/UI_UX_SPEC.md`
6. `docs/engineering/CLAUDE_INSTRUCTIONS.md`
7. `docs/engineering/TECHNICAL_BLUEPRINT.md` for the technical baseline

The product owner's decisions outrank every document. Raise conflicts to the
owner or architect; never resolve them silently or edit `docs/` on your own.

## Roles

- **Product owner** decides product behavior, scope, and acceptance.
- **Architect** plans the work, writes scoped tasks, and reviews the Git diff.
- **Coding agent** is the only role that writes application source code.

The coding agent implements the current task only, never another milestone.

## Domain invariants

- A deadline is not a scheduled time. They are separate values and never update
  each other.
- Completed is not canceled. Both are terminal states with separate history.
- A bubble position is presentation only, never a schedule.
- The AI interprets and proposes. The application validates, authorizes, and
  persists. The model never writes storage directly.

## Layer dependency rules

- The `domain` package (present) imports no framework, database, HTTP, or model SDK.
- `application` (present) imports `domain` only and reaches infrastructure through ports.
- `infrastructure` (present) implements ports; it never imports `api` or `ai`.
- `api` (present) calls `application`; it never imports `infrastructure` or SQLAlchemy.
- `ai` calls `application` through its tool allowlist; it never imports
  `infrastructure`, `api`, FastAPI, or SQLAlchemy.
- `lifespace.main` and `lifespace.openapi_export` are the composition roots.

The application and persistence layers exist: use cases, PostgreSQL repositories, a unit of work, and the task API.

Import-linter enforces the contracts that exist. Run `make api-lint`.

## Machine facts

- The repository path contains a space. Quote every path in scripts and the
  Makefile.
- The login shell exports `NODE_ENV=production`. `apps/web/.npmrc` sets
  `include=dev` and the npm scripts run with `env -u NODE_ENV`.
- The project database is PostgreSQL 18 in Docker on `127.0.0.1:5433`. The host
  PostgreSQL on port 5432 is never used.
- Docker Desktop must run with the `desktop-linux` context. Do not change the
  context or start/stop Docker Desktop unless the owner asks.
- `uv` never downloads Python: every call uses `UV_PYTHON_DOWNLOADS=never` (the
  Makefile exports it). Python dependencies live only in `apps/api/.venv`.
- Never install, upgrade, or remove a global tool or package, and never use
  sudo. pnpm is not installed and is not used.
- If a command fails with `ENOSPC`, stop and report. Do not work around it.

## Common commands

```bash
make doctor     # prerequisites, disk space, ports, Docker
make setup      # .env plus Python and JavaScript dependencies
make db-up      # PostgreSQL on 127.0.0.1:5433
make migrate    # apply Alembic migrations
make dev-api    # API on 127.0.0.1:8000
make dev-web    # web app on 127.0.0.1:5173
make test       # backend and frontend tests
make check      # lint, typecheck, test, build
make smoke      # running servers and the Vite proxy
make api-spec   # export the OpenAPI document to the web app
make api-spec-check api-types-check  # fail on stale generated files
make api-types  # regenerate the committed TypeScript types
make db-down    # stop the database, keep data
make db-reset   # delete local data and recreate the database
```

## Testing rules

- `pytest` runs with `filterwarnings = error`. Fix warnings; never silence them broadly.
- API tests use `httpx.AsyncClient` with `ASGITransport`. The Starlette
  `TestClient` is deprecated and not used.
- Run the application lifespan in HTTP tests and dispose every engine. Unit tests
  need no database; integration tests need `make db-up` and must fail, never skip.
- Frontend tests use Vitest with Testing Library and mock `fetch`.

## Secrets and safety

- Never commit `.env`, credentials, tokens, or private keys. `.env.example` documents every local-only variable.
- Never log database URLs, passwords, request bodies, or user content.
- Error responses never include stack traces or internal details.

## Decisions and Git

- Do not make product decisions. Authentication, accounts, and tenancy are not
  approved and must not be added.
- Branch per task as `m<milestone>/<slug>`. Never commit to `main`.
- Use conventional commits. Do not push, merge, or rewrite history without the owner.
- Finish with a clean `git status`.

## Context budget

- Read only the files the task names; do not scan the whole repository.
- Pipe long command output through `tail -n 30`. Never print lockfiles,
  `node_modules`, or `.venv`.
- Run servers in the background (`setsid`) and always stop them afterwards.

## Final report

End every task with: part and result, commits (`git log --oneline main..HEAD`), each verification command and its result,
deviations and why, and notes for the next part.
