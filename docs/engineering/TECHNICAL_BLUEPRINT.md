# LifeSpace Technical Blueprint

**Status:** Approved technical baseline v1.1. Technical decisions were delegated to the architect by the product owner on 2026-11-12. Product decisions remain with the product owner (section 20).
**Revision:** v1.1 (2026-11-12). Adapted to the owner's actual local environment and a reduced first MVP: local single user, no authentication, no accounts.
**Author role:** Technical architect and reviewer
**Inputs:** `docs/product/PRD.md`, `docs/business/BUSINESS_RULES.md`, `docs/product/USER_FLOWS.md`, `docs/engineering/AGENT_SPEC.md`, `docs/design/UI_UX_SPEC.md`, `docs/engineering/CLAUDE_INSTRUCTIONS.md`

---

## 1. Specification audit

### 1.1 Result

All six specification files are present and preserved byte for byte under `docs/`, organized into `product/`, `design/`, `business/`, and `engineering/`. The documents are consistent in intent. The conflicts below must be settled before the affected milestone starts. Product-level resolutions are the architect's defaults and are confirmed by the product owner (section 20).

### 1.2 Conflicts and gaps

| ID | Finding | Sources | Resolution | Needed before |
|---|---|---|---|---|
| C1 | Memory Garden is P2 in the PRD and UI spec, but P1 in the user flows. | PRD FR-067, UI_UX 17, USER_FLOWS 17 | A plain History list (completed and canceled) is MVP via FR-015. The visual Memory Garden stays P2. | M6 |
| C2 | Drag-onto-task dependency creation is listed as a core bubble interaction, but dependencies are P1. | UI_UX 4.2B, PRD FR-043 | Omit the interaction from MVP. | M3 |
| C3 | Recurring fixed commitments ("every Monday 10 to 12") appear in the P0 capture flow, but recurrence is P1. | USER_FLOWS 5.5, PRD FR-020 | MVP supports single-occurrence commitments only. The AI asks for a date, or states recurrence is not yet supported. | M5 |
| C4 | Conflict detection is listed under Phase 2, but FR-033 and MVP criterion 12 make overlap detection P0. | PRD 7, FR-033, 16.12 | Basic overlap detection is MVP. Alternatives and proposals are Phase 2. | M5 |
| C5 | Inbox cannot transition to Completed, yet Journey D and FR-013 allow completing any active task. Initial status for manual creation is not defined. | BUSINESS_RULES 4.2, PRD 12D | New reviewed tasks start as Planned. Inbox is used only for unreviewed quick capture. | M1 |
| C6 | Bubble position persistence is an open decision, but the flows already assume it is saved. | PRD 18.7, USER_FLOWS 7.3, BUSINESS_RULES 11.4 | Persist positions in a layout table separate from task data. | M3 |
| C7 | Account model is an open decision, but the flows assume sign-in. | PRD 18.1, USER_FLOWS 4.1 | Owner decision 2026-11-12: the first MVP is a local single user application with no registration, sign-in, or accounts. The sign-in flow in USER_FLOWS 4.1 and the account isolation in PRD 14.3 are out of scope until the owner approves authentication. | Resolved |
| C8 | Reopen and restore is conditional in the rules but listed under P0 lifecycle flows. | BUSINESS_RULES 4.2, USER_FLOWS 9.4 | Support Completed to Planned and Canceled to Planned in MVP. | M1 |
| C9 | The category list includes "Projects", which overlaps with the Project entity. | PRD FR-016 | Keep the category value. It carries no project semantics until projects ship. | M2 |
| C10 | Voice input is mentioned in the UI spec, but deferred by the PRD and agent spec. | UI_UX 9.3, PRD 18.8 | Exclude voice from MVP. | M7 |
| C11 | CLAUDE_INSTRUCTIONS 21 says to wait for blueprint approval before creating the GitHub repository. | CLAUDE_INSTRUCTIONS 21 | The owner authorized repository creation and then, on 2026-11-12, delegated technical decisions to the architect. | Resolved |
| C12 | The UI palette uses violet, cyan, green, amber, and red. The owner's saved CSS preference is blue only. | UI_UX 2.2 | Follow the UI spec unless the owner overrides it. Decision P6 (section 20). | M3 |

### 1.3 Confirmed existing decisions

No stack, framework, database, provider, or infrastructure decision existed in the specifications. The decisions in section 2 are the architect's and are final for the foundation.

---

## 2. Final technical decisions

The owner delegated technical decisions to the architect on 2026-11-12 and asked for the smallest foundation that works on the existing machine. Existing runtimes and package versions are preferred. Nothing installed on the machine is upgraded. Versions below were verified by running the stack (section 3.4).

| # | Decision | Choice | Alternatives rejected and why |
|---|---|---|---|
| 1 | Architecture style | Modular monolith. One API process, one web app, one PostgreSQL database. Local, single user | Microservices (no scale or team driver). Serverless (poor local development) |
| 2 | Backend framework | Python 3.14.4 with FastAPI 0.133.1 and Pydantic 2.13.4 | FastAPI 0.110.2 as installed: it runs correctly on Python 3.14 but pins Starlette 0.37.x, which has 14 known security advisories, and relies on `asyncio.iscoroutinefunction`, which Python 3.16 removes. Django, Litestar, NestJS, Flask (no gain over FastAPI for this product) |
| 3 | Python runtime | The installed 3.14.4. uv never downloads another interpreter (`UV_PYTHON_DOWNLOADS=never`) | Installing 3.12 or 3.13 (unnecessary, every dependency supports 3.14) |
| 4 | Database | PostgreSQL 18 in Docker Compose (`postgres:18`, verified 18.6), published on 127.0.0.1:5433 | Using the host PostgreSQL 18 service that already listens on 5432 (the project must not depend on or modify it). SQLite (weaker concurrency and timezone handling, and migrations would diverge from PostgreSQL). MongoDB (the domain is relational) |
| 5 | Persistence | SQLAlchemy 2.0.50 async, asyncpg 0.31.0, Alembic 1.18.4 (all installed versions) | SQLAlchemy 2.1 and psycopg (not installed, no need). SQLModel (merges API and database models). Raw SQL only (no migration tooling) |
| 6 | Frontend framework | React 19.3, TypeScript 6.0, Vite 8.3 SPA on Node 22.22.3 | TypeScript 7 (typescript-eslint 8.72 requires TypeScript below 6.1). Next.js, Remix (a second server runtime beside Python). Vue, Svelte, Angular |
| 7 | Routing | None in M0, a single page. React Router is added in M3 when a second view exists | Adding a router before it is needed |
| 8 | Frontend state | TanStack Query for server state. Component state first. Zustand only when cross-component UI state appears (M3) | Redux Toolkit. Global store for server data |
| 9 | Spatial rendering | DOM bubble elements in a CSS-transformed layer, SVG connectors, headless d3-force layout, Motion for transitions (all from M3) | Canvas, WebGL, PixiJS (lose native focus, text, and screen reader support). React Flow (graph editor semantics, reconsider for Project Universe) |
| 10 | Styling | CSS Modules with CSS custom property design tokens (from M3) | Tailwind, runtime CSS-in-JS, component kits |
| 11 | Accessible primitives | Radix Primitives (from M3) | Hand-built dialogs and menus |
| 12 | API style | REST with JSON and OpenAPI, same origin under `/api` | GraphQL, tRPC, gRPC |
| 13 | Realtime | None. Server-Sent Events later for AI streaming | WebSockets |
| 14 | Contract sharing | OpenAPI export with `openapi-typescript` and `openapi-fetch`, committed output, drift check (from M2) | Hand-written duplicate types |
| 15 | Authentication | **Deferred. Not an approved requirement.** The first MVP is a local single user application with no registration, sign-in, sessions, OAuth, or tenancy | Any authentication design now (JWT, sessions, managed identity). A product decision is required first |
| 16 | AI integration | Provider-agnostic model port, thin adapter, Pydantic validated structured output, deterministic orchestration. Provider chosen at M7 by measurement | LangChain and LangGraph in the MVP. Revisit in Phase 2 |
| 17 | Scheduling | Pure Python deterministic engine with stdlib `zoneinfo` | OR-Tools, LLM scheduling |
| 18 | Background work | None. In-app reminders are computed at read time | Celery, Redis, brokers |
| 19 | Cache | None | Redis |
| 20 | Package management | uv for Python (isolated `apps/api/.venv`, committed `uv.lock`) and npm for JavaScript (committed `package-lock.json`) | pnpm (not installed, no technical reason to add it). pip and Poetry |
| 21 | Task runner | Makefile | Nx, Turborepo, just |
| 22 | Monorepo form | Plain directories: one uv project and one npm package, no workspace tooling | pnpm workspaces |
| 23 | Logging | Standard library `logging` | structlog (an extra dependency without a current need) |
| 24 | CI | Deferred until after M2. `make check` is the quality gate | GitHub Actions and Dependabot in M0 (not needed for a local single user MVP) |
| 25 | Deployment | Out of scope. Local development only | Any hosting or cloud requirement |

---

## 3. Technology stack and versions

### 3.1 Machine (installed, none upgraded)

| Component | Version | Role |
|---|---|---|
| Ubuntu | 26.04 LTS | Host |
| Node.js (nvm) | 22.22.3 | Frontend tooling. Must stay at 22.22.2 or newer because jsdom 31 requires it |
| npm | 10.9.8 | Frontend package manager |
| Python | 3.14.4 | Backend runtime |
| uv | 0.11.28 | Backend environment and lockfile |
| Docker CLI and Docker Desktop | 29.7.2 and 4.85.0 | Runs PostgreSQL. Desktop must be running and the `desktop-linux` context selected |
| Docker Compose | v5.3.1 | Local database definition |
| GNU Make, Git, psql client | 4.4.1, 2.53.0, 18.6 | Tooling |
| PostgreSQL server | `postgres:18` container (18.6 verified) | Application database. The host PostgreSQL service on port 5432 is not used |

Corepack is installed but not used. pnpm is not installed and is not used.

### 3.2 Backend dependencies (isolated environment, locked in `apps/api/uv.lock`)

The project never imports from the global Python packages. `uv sync` creates `apps/api/.venv`.

| Package | Project version | Global version | Note |
|---|---|---|---|
| fastapi | 0.133.1 | 0.110.2 | Changed. See 3.4 |
| starlette | `>=1.3.1` (locks 1.10.0) | 0.37.2 | Follows FastAPI. 1.3.1 is the first release without known advisories |
| uvicorn[standard] | 0.52.4 | 0.52.4 | Same |
| pydantic | 2.13.4 | 2.13.4 | Same |
| pydantic-settings | 2.14.2 | 2.14.1 | Patch bump that fixes an advisory |
| sqlalchemy[asyncio] | 2.0.50 | 2.0.50 | Same |
| asyncpg | 0.31.0 | 0.31.0 | Same |
| alembic | 1.18.4 | 1.18.4 | Same. Its Mako dependency locks 1.4.3 |
| pytest | 9.1.0 | 9.1.0 | Same |
| pytest-asyncio | 1.4.0 | 1.4.0 | Same |
| httpx | 0.28.1 | not installed | Test client |
| ruff | 0.17.4 | not installed | Lint and format |
| mypy | 2.4.1 | not installed | Strict typing |
| import-linter | 2.16 | not installed | Layer rules |

### 3.3 Frontend dependencies (`apps/web/package-lock.json`)

| Package | Version | Note |
|---|---|---|
| react, react-dom | 19.3.1 | |
| @tanstack/react-query | 5.107.1 | |
| vite | 8.3.8 | Requires Node 20.19 or 22.12 and newer |
| @vitejs/plugin-react | 6.3.0 | |
| typescript | 6.0.3 (`~6.0`) | Not 7. See 3.4 |
| vitest | 5.1.0 | Requires Node 22.12 or newer |
| jsdom | 31.0.0 | Requires Node 22.22.2 or newer |
| @testing-library/react, dom, jest-dom | 16.3.3, 10.4.2, 7.0.1 | |
| eslint, @eslint/js | 9.39.5 | Not 10. See 3.4 |
| typescript-eslint | 8.72.2 | |
| eslint-plugin-react-hooks, eslint-plugin-jsx-a11y | 7.1.1, 6.10.2 | |
| globals | 17.14.0 | |
| prettier | 3.10.1 | |
| @types/react, @types/react-dom, @types/node | 19.3.0, 19.3.0, 22.20.5 | Node types match the Node 22 runtime |

Added in later milestones: react-router (M3), zustand, motion, d3-force, Radix primitives, react-hook-form with zod (M3), date-fns (M5), openapi-typescript and openapi-fetch (M2), Playwright (M3), hypothesis (M1).

### 3.4 Compatibility findings (verified on this machine, 2026-11-12)

1. **Python 3.14 with the installed FastAPI 0.110.2 works functionally.** 16 of 16 probes passed: both annotation styles (postponed and plain), dependency injection, response models, problem+json handlers, the sync test client, a real Uvicorn server, and SQLAlchemy with asyncpg against PostgreSQL 18.
2. **Two defects block keeping it.** It emits a deprecation warning from `asyncio.iscoroutinefunction`, which Python 3.16 removes, and it pins Starlette 0.37.x, which has 14 known advisories (OSV). The smallest change is FastAPI 0.133.1, the first line that allows Starlette 1.3.1 or newer. With it, 16 of 16 probes pass and the resolved set (35 packages) has one advisory left, fixed by pydantic-settings 2.14.2.
3. **Starlette 1.x deprecates the httpx based `TestClient`.** Tests use `httpx.AsyncClient` with `ASGITransport` instead.
4. **Pytest with `filterwarnings = error` is clean** when the SQLAlchemy engine is disposed in the application lifespan. Leaving it open produces an unclosed socket warning.
5. **Alembic async template, asyncpg, and Python 3.14 work.** A baseline revision upgraded and downgraded against PostgreSQL 18 with warnings treated as errors.
6. **ruff 0.17 enables blind exception checking by default.** The readiness check intentionally catches every exception and needs a justified `noqa`.
7. **mypy 2.4.1 strict and import-linter 2.16 run correctly on Python 3.14.**
8. **TypeScript 7 conflicts with typescript-eslint 8.72.2** (peer range `>=4.8.4 <6.1.0`). Smallest change: TypeScript 6.0.
9. **ESLint 10 conflicts with eslint-plugin-jsx-a11y 6.10.2** (peer range up to ESLint 9). Smallest change: ESLint 9.
10. **With those two choices** npm installs 340 packages with no overrides, `tsc` reports 0 errors, ESLint 0, Vitest passes, `vite build` succeeds, and `npm audit` reports 0 vulnerabilities, all on Node 22.22.3 and npm 10.9.8.
11. **Docker Compose runs PostgreSQL 18** from a project path that contains a space. The healthcheck passes, the init script creates `lifespace_test`, and the host reaches it on 127.0.0.1:5433.

### 3.5 Cost

No paid service is required. The AI provider (M7) is billed per token and is not part of M0 to M6.

---

## 4. System architecture

```
 Browser: React SPA
     |  same origin, JSON
     v
 Vite dev proxy (/api)
     v
 FastAPI process (apps/api), bound to 127.0.0.1
     |-- api/             HTTP routing, request and response schemas, error mapping
     |-- application/     use cases, validation, approval enforcement, ports        (from M1)
     |-- domain/          task rules, lifecycle, time and interval rules, scheduling (from M1)
     |-- ai/              intents, tool allowlist, orchestration, model port         (from M7)
     |-- infrastructure/  database, logging, model provider adapters
     v
 PostgreSQL 18 (Docker, 127.0.0.1:5433)
```

The application is local and single user. There are no accounts, sessions, or tenants. Same origin is kept because it removes CORS and keeps a later authentication decision simple.

### 4.1 Dependency rules (enforced by import-linter)

- `domain` imports no framework, database library, HTTP library, LLM SDK, Pydantic, or other LifeSpace layer.
- `application` imports `domain` only and reaches infrastructure through ports it defines.
- `infrastructure` implements ports. It never imports `api` or `ai`.
- `api` calls `application` (and in M0 reads wiring from `app.state`). It never imports `infrastructure` or SQLAlchemy.
- `ai` calls `application` through a fixed tool allowlist. It never imports `infrastructure`, `api`, FastAPI, or SQLAlchemy.
- `lifespace.main` is the composition root and the only module that wires infrastructure into the application.

Contracts are added with each layer. M0 enforces the two that exist (`api` and `infrastructure`). `domain`, `application`, and `ai` contracts arrive with those packages.

### 4.2 Request flow

`HTTP request` to an `api` router, schema validation, an `application` use case, `domain` rules, one transaction through a port, a typed result, and a response. AI initiated changes take the same use cases, so there is one write path.

---

## 5. Monorepo structure

```
lifespace/
├── .editorconfig
├── .env.example
├── .gitignore
├── .nvmrc                          22.22.3
├── AGENTS.md
├── Makefile
├── README.md
├── docker-compose.yml
├── docs/
├── infra/postgres/init/01-create-test-db.sql
├── scripts/
│   ├── doctor.sh                   prerequisite checks
│   └── smoke.sh                    endpoint checks
└── apps/
    ├── api/                        one uv project
    │   ├── pyproject.toml
    │   ├── uv.lock
    │   ├── alembic.ini
    │   ├── migrations/             env.py and versions/0001_baseline.py
    │   ├── src/lifespace/
    │   │   ├── main.py             composition root, create_app()
    │   │   ├── config.py           typed settings
    │   │   ├── api/                health.py, errors.py
    │   │   └── infrastructure/     db.py, logging.py
    │   └── tests/                  unit/, integration/
    └── web/                        one npm package
        ├── .npmrc                  include=dev
        ├── package.json
        ├── package-lock.json
        ├── vite.config.ts
        ├── tsconfig.json
        ├── eslint.config.js
        ├── .prettierrc.json
        ├── index.html
        └── src/                    main.tsx, App.tsx, shared/api/, test setup
```

Added by later milestones, only when they contain files: `domain/` and `application/` (M1), `ai/` (M7), `features/`, `design-system/`, and a router (M3).

The repository path can contain spaces. Every script and Makefile recipe must quote paths.

---

## 6. Backend architecture

- **Domain (from M1).** Frozen dataclasses and pure functions. No clock access (`now` is passed in) and no I/O.
- **Application (from M1).** Use cases that take a unit of work and a clock, and define the ports they need. Return typed results carrying the result categories from AGENT_SPEC 13.1.
- **Infrastructure.** SQLAlchemy models and repositories, the async engine, logging, provider adapters. ORM models never leave this layer.
- **API.** Thin routers. Pydantic request and response schemas live here, separate from domain objects.
- **Wiring in M0.** `create_app(settings, ready_check=None)` builds the engine and stores a readiness callable on `app.state`. Tests inject a fake callable. The engine is disposed in the application lifespan.
- **Concurrency.** Async end to end. One session and one transaction per request. `expire_on_commit=False` and explicit loading.
- **Configuration.** `pydantic-settings` with prefix `LIFESPACE_`, failing fast on missing required values.

---

## 7. Database design approach

- The database serves one local user. Tables carry no `user_id`. If the owner later approves accounts, ownership columns are added in a dedicated milestone.
- Primary keys are UUIDs generated in the application with `uuid.uuid7()` (available in Python 3.14), which sorts by creation time.
- Mutable tables carry `created_at`, `updated_at` (`timestamptz`, UTC), and an integer `version` for optimistic concurrency.
- Deadline and scheduled interval are separate columns that never update each other. A date-only deadline is a `date`, a timestamp deadline is a `timestamptz`, and a check constraint allows exactly one.
- The user's IANA time zone is stored in a single settings row. Day boundaries are computed from it.
- Deletion is soft (`deleted_at`) where the product requires recovery. Status history is append only.
- Constraints back the application rules (positive duration, end after start). Overlap is a visible warning, never a database exclusion.
- Constraint and index names follow a fixed SQLAlchemy `naming_convention` from the first migration.
- Alembic async template. Autogenerate output is reviewed by a human. M0 contains one empty baseline revision.
- Two databases exist locally: `lifespace` and `lifespace_test`.

---

## 8. API conventions

- **Layout.** Infrastructure endpoints live at `/api/health` and `/api/health/ready`. Product endpoints are versioned under `/api/v1/`.
- **Resources.** Plural nouns, standard verbs, and explicit action sub-resources for lifecycle changes (for example `POST /api/v1/tasks/{id}/complete`). No verbs in collection paths.
- **IDs and time.** UUID strings. Timestamps are ISO 8601 UTC with offset. A deadline is a tagged value: `{"kind": "date", "value": "2026-12-01"}` or `{"kind": "datetime", "value": "..."}`.
- **Errors.** RFC 9457 `application/problem+json` with an extra `code` member in M0. `result` and `request_id` are added with the first use case. `result` is one of `rejected`, `validation_failed`, `conflict`, `not_found`, `unauthorized`, `failed`, `unknown_pending_verification`. Responses never include stack traces or internal details.
- **Concurrency.** Updates carry the expected `version`. A mismatch returns 409 with code `stale_version`.
- **Idempotency.** Creating operations accept an `Idempotency-Key` header. The stored key and request hash return the original result on retry.
- **Pagination.** Cursor based for lists that can grow (history).
- **Contract.** FastAPI generates OpenAPI. The web app consumes generated TypeScript types from M2, and CI fails on drift.

---

## 9. Authentication

**Authentication is deferred and is not an approved requirement.** The first MVP is a local single user application. There is no registration, sign-in, session, OAuth, account, or tenancy, and no code, table, or setting for them in M0 to M8 unless the owner approves a change.

Consequences accepted for the MVP:

- The API binds to `127.0.0.1` only and the Compose database is published on `127.0.0.1` only. The application must never be exposed to a network in this configuration.
- Endpoints are unauthenticated by design. This is safe only because of the loopback binding.
- PRD 14.3 (account isolation) and USER_FLOWS 4.1 (sign-in) are out of scope until a product decision is made.

If the owner later approves accounts, the work is a dedicated milestone: choose a mechanism, add ownership columns and repository filters, add the sign-in flow, and add authorization tests. Nothing in the M0 design prevents it.

---

## 10. Frontend architecture

- **Structure.** `app/` (providers, and from M3 the router and shell), `features/<name>/` (UI, hooks, API calls for one feature), `shared/` (API client, utilities), and `design-system/` (tokens and primitives, from M3).
- **Data.** TanStack Query owns server state. Components render confirmed server state. Optimistic updates are allowed only with rollback and never present a pending change as saved.
- **UI state.** Component state first. Zustand for cross-component state such as selection, open panels, and unsaved drafts.
- **Spatial workspace (M3).** A pure TypeScript layout engine, seeded and deterministic, wraps d3-force. A rendering layer places DOM bubble elements (real buttons, so focus and screen readers work) inside a pan and zoom layer driven by CSS transforms, with SVG for connectors. Position changes are saved to the layout table and never touch task schedules. Bubbles outside the viewport are culled. Target: 200 bubbles at 60 fps, graceful degradation beyond.
- **Accessibility.** Keyboard alternatives for every drag interaction, visible focus, `prefers-reduced-motion` respected, color never the only signal, and a list view as the small screen fallback.
- **Design tokens.** CSS custom properties from UI_UX_SPEC (dark first). Components consume tokens, never raw colors.
- **Time.** All timestamps arrive in UTC and are displayed in the user's configured zone with date-fns and `@date-fns/tz`.
- **Errors.** One API client parses problem+json into a typed `ApiError`. A top level error boundary and per-query error states exist from M0.

---

## 11. AI integration boundaries

- **Port.** `ai` defines a `LanguageModel` protocol: given messages and a Pydantic output schema, return a validated object or a typed failure. Provider adapters live in `infrastructure` and are wired by `main.py`.
- **Pipeline (deterministic).** Context builder, model call, schema validation, policy gate, tool execution through the allowlist, response composer. Each stage is a plain function so it can be unit tested without a model.
- **Tool allowlist.** A registry maps each tool name to one application use case with typed input and output and a permission class: `read`, `draft`, `propose`, or `mutate_with_approval`. The model cannot call anything outside the registry.
- **Write path.** The model never writes to storage. Consequential changes become persisted proposals bound to a version and a data fingerprint. Approval references that version, and the use case revalidates before applying.
- **Untrusted input.** Task text and retrieved records are data, delimited and never treated as instructions. Output that fails schema validation is rejected, never repaired silently.
- **Truth boundaries.** The model never computes authoritative availability, conflicts, or success. It reports results returned by use cases.
- **Fallback.** If the provider fails or times out, manual workflows continue to work and the Companion reports the failure honestly.
- **Observability.** An `ai_runs` record stores prompt version, model identifier, token counts, latency, and outcome. Raw prompt text is not stored by default.
- **Evaluation.** A golden test set derived from the AGENT_SPEC test scenarios runs against the fake model in CI and against a live model on demand.
- **Provider choice.** Decided at M7 by running the golden set against candidate providers and comparing accuracy, latency, and cost. The architect is itself built by Anthropic, so the choice must be made on measured results, not on assertion.

---

## 12. Scheduling engine boundaries

- Lives entirely in `domain/scheduling`. Pure functions over value objects. No database, no network, no clock, no model.
- Intervals are start inclusive and end exclusive. Overlap is `a.start < b.end and b.start < a.end`.
- Determinism is a requirement. The same inputs always give the same outputs, and every result carries the reasons that produced it so the UI and Companion can explain it.
- MVP scope (M5): overlap detection, available time within working hours, and feasibility checks. Proposal generation is Phase 2, starting with a deterministic first-fit algorithm and a documented tie-breaking order.
- The AI may request scheduling results through use cases. It may never replace the engine.
- Property tests (hypothesis) cover interval algebra, daylight saving transitions, and midnight crossing.

---

## 13. Error handling

- Domain code raises typed domain errors. Application code converts them to result categories. The API layer maps categories to HTTP status and problem+json.
- Unhandled exceptions return a generic 500 problem body with a request ID. Details go to logs only.
- Validation failures return 422 with field level detail and never echo secrets.
- The frontend never shows an optimistic success for a failed mutation, and distinguishes `unknown_pending_verification` from failure.
- Retries are safe only where an idempotency key exists.

---

## 14. Security and privacy

- Local single user scope. API and database are bound to `127.0.0.1`. See section 9.
- Secrets only in environment variables. `.env` is ignored and `.env.example` documents every variable with local-only values. No secret reaches client code or Git.
- Input is validated at the API boundary. Output is encoded by React. User and AI content is never rendered as raw HTML.
- Error responses never include stack traces or internal details. Details go to logs.
- Logs never contain task content, request bodies, or credentials.
- AI requests send only the minimum context required for the intent.
- Dependencies are locked (`uv.lock`, `package-lock.json`). Before adding or upgrading a dependency, check `npm audit` and an OSV query for the Python set.
- Export and deletion of the user's data are planned requirements, not afterthoughts.

---

## 15. Testing strategy

| Layer | Tooling | Scope |
|---|---|---|
| Domain (M1) | pytest, hypothesis | Lifecycle, intervals, overdue, validation. High branch coverage |
| Application (M1) | pytest with in-memory fakes of ports | Use cases, approval, concurrency, idempotency |
| Infrastructure | pytest against real PostgreSQL | Repositories, migrations, constraints |
| API | pytest with `httpx.AsyncClient` and `ASGITransport` | Contracts and error format. Never the Starlette `TestClient` |
| AI (M7) | pytest with a fake model, golden set | Extraction, tool policy, injection resistance |
| Frontend | Vitest, Testing Library | Components, hooks, API client |
| End to end (M3) | Playwright against the real stack | PRD acceptance criteria 1 to 18 |
| Accessibility (M4) | axe inside Playwright | Keyboard and screen reader basics |
| Architecture | import-linter | Layer rules |

Rules: pytest runs with `filterwarnings = error`. Database tests never skip silently when PostgreSQL is unreachable, they fail with a message to run `make db-up`. Each PRD acceptance criterion maps to at least one automated test by M8.

---

## 16. Local development workflow

One-time machine preparation (owner):

```
systemctl --user start docker-desktop      # or open Docker Desktop
docker context use desktop-linux
```

Daily commands from the repository root:

```
make doctor     check Node, npm, uv, Python, Docker, disk space, and ports
make setup      uv sync for apps/api and npm ci for apps/web
make db-up      start PostgreSQL 18 in Docker (healthcheck gated)
make migrate    apply Alembic migrations
make dev-api    API on http://127.0.0.1:8000
make dev-web    web on http://127.0.0.1:5173, proxying /api to the API
make test       backend and frontend tests
make check      lint, typecheck, test, and build for both apps
make smoke      curl the health endpoints, including through the dev proxy
make db-down    stop the database (data kept)
make db-reset   destroy and recreate the local database (development only)
```

### Known environment hazards on this machine

| Hazard | Effect | Handling |
|---|---|---|
| `NODE_ENV=production` is exported in login shells | npm silently skips devDependencies, and the Vite dev server and Vitest would run in a production environment | `apps/web/.npmrc` sets `include=dev`. Makefile runs web commands with `env -u NODE_ENV` |
| `/home` was 100 percent full (about 160 MB free) when checked | npm, uv, and Docker writes fail with `ENOSPC` | `make doctor` fails below 3 GB free. The owner frees space before setup |
| A host PostgreSQL 18 service listens on 127.0.0.1:5432 | A Compose port 5432 would collide | Compose publishes on 127.0.0.1:5433. The host service is never used or modified |
| Docker Desktop is not started by default and uses its own socket | `docker compose` fails with no daemon | Start it and select the `desktop-linux` context. `make doctor` checks it |
| Repository path contains a space | Unquoted paths break recipes and scripts | Quote every path. Use relative paths from the repository root |
| Global Python packages are installed | They could be imported by accident | uv uses an isolated `apps/api/.venv` and never the global site-packages |

---

## 17. Environment configuration

| Variable | Used by | Purpose | Local default |
|---|---|---|---|
| `LIFESPACE_ENVIRONMENT` | API | `development`, `test`, or `production` | `development` |
| `LIFESPACE_DATABASE_URL` | API | SQLAlchemy URL, `postgresql+asyncpg://` | `postgresql+asyncpg://lifespace:lifespace_dev_only@127.0.0.1:5433/lifespace` |
| `LIFESPACE_TEST_DATABASE_URL` | tests | Test database | same host, database `lifespace_test` |
| `LIFESPACE_LOG_LEVEL` | API | Log level | `INFO` |
| `API_PROXY_TARGET` | Vite dev server | Where `/api` is proxied | `http://127.0.0.1:8000` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT` | Compose | Local database container | `lifespace`, `lifespace_dev_only`, `lifespace`, `5433` |

The web app has no API base URL because it always calls `/api` on its own origin. The defaults are local-only and are not secrets. `.env` is never committed.

---

## 18. Delivery workflow

- One branch per implementation task named `m<milestone>/<slug>`. Conventional commit messages. No direct commits to `main`.
- `make check` is the quality gate and must pass before a task is reported complete.
- CI and dependency update automation are deferred until after M2, when real tests justify them.

---

## 19. Future extension points

| Need | Extension |
|---|---|
| Accounts and sign-in | A dedicated milestone after an owner decision. See section 9 |
| Continuous integration | GitHub Actions running `make check`, after M2 |
| Email or push reminders | PostgreSQL-backed job table and worker (`SKIP LOCKED`) |
| AI streaming | Server-Sent Events from the `ai` orchestrator |
| Multi-step planning loops | Evaluate LangGraph behind the existing `ai` port in Phase 2 |
| Advanced scheduling | Constraint solver behind the scheduling interface, only if first-fit proves insufficient |
| Semantic memory or search | PostgreSQL `pgvector` before any separate vector database |
| Project Universe graph | Evaluate React Flow |
| Deployment | Dockerfiles and a reverse proxy in a release milestone |

---

## 20. Product decisions still owned by the product owner

These are not technical decisions. Each blocks the milestone shown.

| ID | Question | Architect's default if no answer | Blocks |
|---|---|---|---|
| P0 | Authentication and accounts | Not in MVP (section 9) | Any multi-user work |
| P1 | Fixed commitments: separate entity or task type | Separate entity | M1 |
| P2 | Date-only deadline: overdue after the end of that local day | Yes | M1 |
| P3 | Initial status of new tasks (conflict C5) | Planned for reviewed creation, Inbox for unreviewed capture | M1 |
| P4 | Reopen completed and canceled tasks in MVP | Yes | M1 |
| P5 | Default bubble size when duration is unknown | Neutral fixed size labeled "no estimate" | M3 |
| P6 | UI palette versus the owner's blue-only preference (C12) | Follow UI_UX_SPEC | M3 |
| P7 | Default working hours, breaks, buffers | None invented. Owner supplies values | M5 |
| P8 | Week and month Time Flow views | After the daily view | M5 |
| P9 | AI task creation always shows a review step in MVP | Yes | M7 |

P1 to P4 were adopted provisionally on 2026-11-16 so that M1 could start, and the M2 decisions are recorded in `adr/0002-m2-persistence-and-task-api.md`. They are recorded, with the other M1 rules, in `adr/0001-m1-domain-decisions.md`. The owner may override them at any time.

---

## 21. Development roadmap

Each milestone ends with a review report and owner acceptance. No milestone starts before the previous one is reviewed. The first MVP is local and single user.

| Milestone | Scope | PRD alignment |
|---|---|---|
| M0 Foundation | Monorepo, tooling, health checks, database connectivity, migration baseline, error and logging baseline, architecture enforcement, environment checks | Maintainability 14.5 |
| M1 Domain core | Task model, lifecycle, time and interval rules, overdue computation, validation. Pure Python with unit and property tests | FR-011 to FR-018, FR-030 |
| M2 Persistence and task API | Schema, migrations, repositories, task endpoints, status history, versioning, idempotency, generated API types | FR-005, FR-010 to FR-015 |
| M3 Design system and My Space | Router, tokens, primitives, shell, bubbles, layout, detail panel, manual create and edit, lifecycle actions, saved positions, empty, loading, error states, list fallback, Playwright | FR-060 to FR-063, 14.4 |
| M4 Spatial hardening | Keyboard alternatives, reduced motion, touch, performance, axe checks | NFR 14.1, 14.4 |
| M5 Commitments and Time Flow | Fixed commitments, manual scheduling, overlap detection, daily timeline, available time | FR-030 to FR-034, FR-064 |
| M6 History and reminders | Completed and canceled history, overdue indication, in-app reminders | FR-015, FR-070, FR-071 |
| M7 AI Companion (basic) | Model port, provider bake-off, structured extraction, draft review, clarification, read-only intents, allowlisted task operations, activity records, fallback | FR-001 to FR-004, FR-006, FR-050 to FR-055 |
| M8 Proposals and MVP hardening | Approval enforcement, stale revalidation, end to end coverage of PRD criteria 1 to 18, accessibility and responsive audit, CI | FR-037, FR-053, MVP criteria |
| Phase 2 and later | Per the PRD | PRD Phases 2 to 4 |

Manual workflows (M1 to M6) precede the AI Companion so the product is useful without AI (PRD principle 10).

---

## 22. Review and verification policy

- Every task is reviewed from the actual Git diff, never from the agent's summary.
- Findings use the format in CLAUDE_INSTRUCTIONS section 14.3.
- A milestone closes only when blocking findings are fixed, tests were observed passing, and the owner accepts it.
- Where the reviewer cannot run a check, the exact command is provided to run locally.
