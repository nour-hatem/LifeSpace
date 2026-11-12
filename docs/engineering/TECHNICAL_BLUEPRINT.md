# LifeSpace Technical Blueprint

**Status:** Approved technical baseline v1. Technical decisions were delegated to the architect by the product owner on 2026-11-12. Product decisions remain with the product owner (section 20).
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
| C7 | Account model is an open decision, but the flows assume sign-in. | PRD 18.1, USER_FLOWS 4.1 | Resolved technically: multi-user with first-party sessions (sections 9 and 2, decision 15). | Resolved |
| C8 | Reopen and restore is conditional in the rules but listed under P0 lifecycle flows. | BUSINESS_RULES 4.2, USER_FLOWS 9.4 | Support Completed to Planned and Canceled to Planned in MVP. | M1 |
| C9 | The category list includes "Projects", which overlaps with the Project entity. | PRD FR-016 | Keep the category value. It carries no project semantics until projects ship. | M2 |
| C10 | Voice input is mentioned in the UI spec, but deferred by the PRD and agent spec. | UI_UX 9.3, PRD 18.8 | Exclude voice from MVP. | M7 |
| C11 | CLAUDE_INSTRUCTIONS 21 says to wait for blueprint approval before creating the GitHub repository. | CLAUDE_INSTRUCTIONS 21 | The owner authorized repository creation and then, on 2026-11-12, delegated technical decisions to the architect. | Resolved |
| C12 | The UI palette uses violet, cyan, green, amber, and red. The owner's saved CSS preference is blue only. | UI_UX 2.2 | Follow the UI spec unless the owner overrides it. Decision P6 (section 20). | M3 |

### 1.3 Confirmed existing decisions

No stack, framework, database, provider, or infrastructure decision existed in the specifications. The decisions in section 2 are the architect's and are final for the foundation.

---

## 2. Final technical decisions

The owner delegated technical decisions to the architect on 2026-11-12. Each row records the choice and the alternatives rejected. Versions were verified against package registries on 2026-11-12 (section 3).

| # | Decision | Choice | Alternatives rejected and why |
|---|---|---|---|
| 1 | Architecture style | Modular monolith: one API process, one static web app, one PostgreSQL database | Microservices (no scale or team driver, and the scheduler must share transactions with task data). Serverless functions (cold starts, long AI calls, poor local development) |
| 2 | Backend framework | Python 3.14 with FastAPI and Pydantic v2 | Django with DRF or Ninja (ORM centric, couples the domain to persistence, async is second class, admin not needed). Litestar (smaller ecosystem, no decisive gain). Node with NestJS (splits AI work into a weaker SDK ecosystem). Flask (no typed contracts) |
| 3 | Python version | 3.14 | 3.13 and 3.12 (shorter remaining support, no stdlib `uuid.uuid7`). All compiled dependencies ship cp314 wheels and all key libraries declare 3.14 support (verified) |
| 4 | Database | PostgreSQL 18 | SQLite (weak concurrency, timezone handling, and migration parity for a multi-user product). MongoDB (the domain is relational: status history, ownership, constraints). Managed-only databases (vendor lock-in) |
| 5 | Persistence | SQLAlchemy 2.1 async, psycopg 3, Alembic | SQLModel (merges API and database models, violating the layer rules). Django ORM and Tortoise (framework coupling). Raw SQL only (boilerplate and no migration tooling). asyncpg (viable, but psycopg 3 serves async app code and tooling with one driver) |
| 6 | Frontend framework | React 19, TypeScript strict, Vite SPA | Next.js and Remix framework mode (a second server runtime beside Python, no SEO need for an authenticated interactive app). Vue, Svelte (smaller ecosystem of accessible primitives and spatial tooling). Angular (heavier than needed) |
| 7 | Routing | React Router in library mode | TanStack Router (second paradigm beside TanStack Query with no clear gain). Framework mode (SSR assumptions) |
| 8 | Frontend state | TanStack Query for server state. Component state first. Zustand only for cross-component UI state, introduced when needed (M3) | Redux Toolkit (boilerplate). Caching server data in a global store (duplicates Query and breaks the rule that the UI renders confirmed state) |
| 9 | Spatial rendering | DOM bubble elements inside a CSS-transformed layer, SVG for connectors, headless d3-force for layout, Motion for transitions | Canvas, WebGL, PixiJS (lose native focus, text, and screen reader support, and MVP volumes do not need a GPU). React Flow (graph editor model imposes node and edge semantics, reconsider for Project Universe). Physics engines (not required) |
| 10 | Styling | CSS Modules with CSS custom property design tokens | Tailwind (token ownership is weaker for a distinctive visual identity with many bubble states). Runtime CSS-in-JS (cost under animated layouts). Component kits such as MUI (fights the custom identity) |
| 11 | Accessible primitives | Radix Primitives | Hand-built dialogs and menus (focus management defects). React Aria (valid, larger surface) |
| 12 | API style | REST with JSON and OpenAPI, same-origin under `/api` | GraphQL (no multi-client need). tRPC (TypeScript only). gRPC (no benefit in a browser app) |
| 13 | Realtime | None in MVP. Server-Sent Events later for AI streaming | WebSockets (no bidirectional need) |
| 14 | Contract sharing | OpenAPI export, `openapi-typescript` and `openapi-fetch`, generated file committed with a CI drift check (from M2) | Hand-written duplicate types |
| 15 | Authentication | First-party email and password, server-side sessions stored in PostgreSQL, HttpOnly cookie, argon2id through `pwdlib`. Introduced in M2 | JWT in localStorage (XSS exposure). JWT access and refresh pairs (revocation complexity). Managed identity providers such as Clerk, Auth0, Supabase (recurring cost and vendor dependency, kept as a swap behind an `Authenticator` port). fastapi-users (owns the user model and routers through ORM mixins, which conflicts with the layer rules) |
| 16 | AI integration | Provider-agnostic port, thin adapters, Pydantic validated structured output, deterministic orchestration. Provider chosen at M7 by measurement | LangChain and LangGraph in the MVP (the pipeline is linear and approval gated, and its state already lives in the application database, so a framework would duplicate proposals and add an abstraction over tool calling). Revisit in Phase 2 |
| 17 | Scheduling | Pure Python deterministic engine with stdlib `zoneinfo` | OR-Tools and CP-SAT (heavy, unjustified before multi-constraint optimization exists). LLM scheduling (forbidden by BUSINESS_RULES) |
| 18 | Background work | None in MVP. In-app reminders are computed at read time | Celery, Redis, brokers (no MVP requirement). Extension: a PostgreSQL-backed job table with `FOR UPDATE SKIP LOCKED` when email or push reminders arrive |
| 19 | Cache | None | Redis (no measured need) |
| 20 | Package management | uv for Python, pnpm through corepack for JavaScript | pip and Poetry (slower, weaker locking). npm and yarn (pnpm is stricter and has native release-age gating) |
| 21 | Task runner | Makefile | Nx, Turborepo, just (one JavaScript app does not justify them) |
| 22 | Monorepo form | Plain directories, no JavaScript workspace | pnpm workspaces (only one JavaScript package exists) |
| 23 | Logging | structlog, JSON in production, console in development | Plain stdlib formatting (no structured context binding) |
| 24 | CI | GitHub Actions | Self-hosted runners (operational burden) |
| 25 | Deployment | Not decided in M0. Apps are twelve-factor and same-origin behind a reverse proxy. Dockerfiles arrive in the release milestone | Premature platform lock-in |

---

## 3. Technology stack and versions

**Version policy.** The table gives the version line to use and the latest release verified on 2026-11-12. Within a line, install the newest release that is at least 14 days old. This is enforced by tooling (`minimumReleaseAge` in pnpm, `exclude-newer` when locking with uv), not by memory. If a selected major is not supported by the rest of the toolchain, use the newest major that all tools support. Never use `--force`, `--legacy-peer-deps`, or peer dependency overrides.

### 3.1 Platform

| Component | Line | Verified 2026-11-12 | Notes |
|---|---|---|---|
| Node.js | 26 LTS | 26.13.1 | Active LTS. Pinned in `.nvmrc` |
| pnpm | 12 | 12.18.0 | Provided by corepack through the `packageManager` field |
| Python | 3.14 | 3.14.4 | Pinned in `.python-version` and `requires-python` |
| uv | current | 0.11.28 (local) | |
| PostgreSQL | 18 | `postgres:18` image | |
| Docker Compose | v2 or later | 5.3.1 (local) | PostgreSQL only |

### 3.2 Backend

| Package | Line | Verified | First used |
|---|---|---|---|
| fastapi | 0.162 | 0.162.5 | M0 |
| uvicorn (standard) | 0.54 | 0.54.0 | M0 |
| pydantic | 2.14 | 2.14.3 | M0 |
| pydantic-settings | 2.16 | 2.16.2 | M0 |
| sqlalchemy (asyncio) | 2.1 | 2.1.8 | M0 |
| psycopg (binary) | 3.3 | 3.3.8 | M0 |
| alembic | 1.20 | 1.20.1 | M0 |
| structlog | 26.1 | 26.1.0 | M0 |
| httpx | 0.28 | 0.28.1 | M0 (tests) |
| pytest, pytest-asyncio | 9.2, 1.4 | 9.2.0, 1.4.1 | M0 |
| ruff | 0.17 | 0.17.4 | M0 |
| mypy | 2.4 | 2.4.1 | M0 |
| import-linter | 2.16 | 2.16 | M0 |
| pip-audit | 2.10 | 2.10.1 | M0 |
| hypothesis | 6.170 | 6.170.15 | M1 |
| pwdlib (argon2) | 0.3 | 0.3.1 | M2 |

### 3.3 Frontend

| Package | Line | Verified | First used |
|---|---|---|---|
| react, react-dom | 19 | 19.3.1 | M0 |
| vite | 8 | 8.3.8 | M0 |
| @vitejs/plugin-react | 6 | 6.3.0 | M0 |
| typescript | 7 (fallback to newest supported major) | 7.0.2 | M0 |
| react-router | 8 | 8.5.1 | M0 |
| @tanstack/react-query | 5 | 5.107.1 | M0 |
| vitest, jsdom | 5, 31 (fallback to newest compatible) | 5.1.0, 31.0.0 | M0 |
| @testing-library/react, jest-dom, user-event | 16, 7, 14 | 16.3.3, 7.0.1, 14.6.9 | M0 |
| eslint (+ typescript-eslint, react-hooks, jsx-a11y) | newest major supported by every plugin | 10.14.0, 8.72.2, 7.1.1, 6.10.2 | M0 |
| prettier | 3 | 3.10.0 | M0 |
| zustand | 5 | 5.1.0 | M3 |
| motion | 14 | 14.12.0 | M3 |
| d3-force | 3 | 3.0.1 | M3 |
| @radix-ui primitives | 1 | 1.3.1 (dialog) | M3 |
| react-hook-form, zod | 7, 4 | 7.92.0, 4.6.7 | M3 |
| date-fns, @date-fns/tz | 4, 1 | 4.4.0, 1.5.0 | M5 |
| openapi-typescript, openapi-fetch | 7, 0.17 | 7.13.0, 0.17.0 | M2 |
| @playwright/test | 1 | 1.65.0 | M3 |
| msw | 3 | 3.0.5 | M3 |

Libraries marked M2 or later are not installed in M0. Nothing is added before a milestone uses it.

### 3.4 Paid services and cost

- No paid service is required to build or test M0 to M6.
- The AI provider (M7) is billed per token. Tests use a deterministic fake model, so development cost is near zero. A budget guard (per user rate limit and token ceiling) is part of M7.
- An email provider is needed for password reset and email verification. Both are deferred, so no email cost exists in the MVP.
- Hosting is undecided. Cost and vendor will be listed before the release milestone.

---

## 4. System architecture

```
 Browser: React SPA (static assets)
     |  same origin, HTTPS, JSON, session cookie
     v
 Reverse proxy (production) / Vite dev proxy (development)
     |  /api/*
     v
 FastAPI process (apps/api)
     |-- api/             HTTP routing, request and response schemas, session dependency, error mapping
     |-- application/     use cases, validation, approval enforcement, transactions, ports
     |-- domain/          task rules, lifecycle, time and interval rules, scheduling (pure Python)
     |-- ai/              intents, schemas, tool registry, orchestration, prompts, model port
     |-- infrastructure/  database, model provider adapters, logging, clock
     v
 PostgreSQL 18
```

Same origin is a deliberate decision. The SPA and API share one origin in every environment, so session cookies are first party, CORS is unnecessary, and CSRF defenses stay simple.

### 4.1 Dependency rules (enforced by import-linter in CI)

- `domain` imports no framework, no database library, no HTTP library, no LLM SDK, no Pydantic, and no other LifeSpace layer.
- `application` imports `domain` only, and reaches infrastructure through ports (Protocols) that it defines.
- `infrastructure` implements ports. It never imports `api` or `ai`.
- `api` calls `application`. It never imports `infrastructure` or SQLAlchemy.
- `ai` calls `application` through a fixed tool allowlist. It never imports `infrastructure`, `api`, FastAPI, or SQLAlchemy.
- `lifespace.main` is the composition root. It is the only module that wires infrastructure into the application.

### 4.2 Request flow

`HTTP request` to `api` router, then schema validation, then session resolution, then an `application` use case, which loads state through ports, applies `domain` rules, persists in one transaction, and returns a typed result. The router maps the result to a response. AI initiated changes take the same use cases through the `ai` tool allowlist, so there is exactly one write path.

---

## 5. Monorepo structure

```
lifespace/
├── .editorconfig
├── .env.example
├── .github/
│   ├── dependabot.yml
│   └── workflows/ci.yml
├── .gitignore
├── .nvmrc
├── .python-version
├── AGENTS.md
├── Makefile
├── README.md
├── docker-compose.yml
├── docs/                          specifications, blueprint, Codex prompts
├── infra/
│   └── postgres/init/01-create-test-db.sql
├── scripts/
│   └── smoke.sh
└── apps/
    ├── api/
    │   ├── pyproject.toml
    │   ├── uv.lock
    │   ├── alembic.ini
    │   ├── migrations/            env.py and versions/
    │   ├── src/lifespace/
    │   │   ├── main.py            composition root and app factory
    │   │   ├── config.py          typed settings
    │   │   ├── domain/            pure rules
    │   │   ├── application/       use cases and ports
    │   │   ├── infrastructure/    db/, logging, later ai providers
    │   │   ├── api/               routers, schemas, errors, middleware
    │   │   └── ai/                intents, tools, orchestrator, prompts
    │   └── tests/
    │       ├── unit/
    │       └── integration/
    └── web/
        ├── package.json
        ├── pnpm-lock.yaml
        ├── vite.config.ts
        ├── tsconfig.json
        ├── eslint.config.js
        ├── index.html
        └── src/
            ├── main.tsx
            ├── app/               providers and router
            ├── features/          one folder per product feature, added per milestone
            ├── shared/            api client, utilities
            └── test/              test setup
```

Directories are created only when they hold files. `design-system/` and the feature folders appear in the milestone that needs them.

---

## 6. Backend architecture

- **Domain.** Frozen dataclasses and pure functions. No clock access: `now` is passed in. No I/O. Lifecycle transitions, interval arithmetic, overdue computation, and validation live here.
- **Application.** One module per use case family, each function taking a unit of work and a clock. Defines ports such as `TaskRepository`, `UnitOfWork`, `Clock`, `ReadinessProbe`, `Authenticator`, and `LanguageModel`. Returns typed result objects carrying the result categories from AGENT_SPEC 13.1.
- **Infrastructure.** SQLAlchemy models and repositories, the async engine, structlog configuration, provider adapters. ORM models never leave this layer.
- **API.** Thin routers. Pydantic request and response schemas live here, separate from domain objects.
- **Concurrency.** Async end to end. Each request gets one session and one transaction managed by the unit of work. `expire_on_commit=False`, and relationships are loaded explicitly to avoid implicit lazy loads.
- **Configuration.** `pydantic-settings`, prefix `LIFESPACE_`, fail fast on missing required values.

---

## 7. Database design approach

- Primary keys are UUIDs generated in the application with `uuid.uuid7()`, which sorts by creation time.
- Every user owned table has `user_id NOT NULL` with a foreign key, and every repository query filters by it. Row level security is a later defense in depth option.
- Mutable tables carry `created_at`, `updated_at` (both `timestamptz`, UTC), and an integer `version` for optimistic concurrency.
- Deadline and scheduled interval are separate columns that never update each other. A date-only deadline is a `date` column, a timestamp deadline is `timestamptz`, and a check constraint allows exactly one of them.
- The user's IANA time zone is stored on the profile. Day boundaries are computed from it.
- Deletion is soft (`deleted_at`) where recovery is required by the product, and status history is append only.
- Constraints back the application rules (positive duration, end after start). They never replace them. Overlap is a visible warning, not a database exclusion, per BUSINESS_RULES.
- Constraint and index names follow a fixed SQLAlchemy `naming_convention` from the first migration.
- Migrations: Alembic, autogenerate then human reviewed, one revision per change, tested in CI by upgrading an empty database and running `alembic check` for drift.
- Local development uses a development database and a separate `lifespace_test` database.

---

## 8. API conventions

- **Layout.** Infrastructure endpoints live at `/api/health` and `/api/health/ready`. Product endpoints are versioned under `/api/v1/`.
- **Resources.** Plural nouns, standard verbs, and explicit action sub-resources for lifecycle changes (for example `POST /api/v1/tasks/{id}/complete`). No verbs in collection paths.
- **IDs and time.** UUID strings. Timestamps are ISO 8601 UTC with offset. A deadline is a tagged value: `{"kind": "date", "value": "2026-12-01"}` or `{"kind": "datetime", "value": "..."}`.
- **Errors.** RFC 9457 `application/problem+json` with extra members `code`, `result`, and `request_id`. `result` is one of `rejected`, `validation_failed`, `conflict`, `not_found`, `unauthorized`, `failed`, `unknown_pending_verification`. Responses never include stack traces or internal details.
- **Concurrency.** Updates carry the expected `version`. A mismatch returns 409 with code `stale_version`.
- **Idempotency.** Creating operations accept an `Idempotency-Key` header. The stored key and request hash return the original result on retry.
- **Pagination.** Cursor based for lists that can grow (history).
- **Contract.** FastAPI generates OpenAPI. The web app consumes generated TypeScript types from M2, and CI fails on drift.
- **Request IDs.** Every response carries `X-Request-ID`. The same ID appears in logs and in error bodies.

---

## 9. Authentication strategy

Authentication is introduced in M2, together with the first user owned table, so no data endpoint ever exists without ownership checks.

- Email and password. Passwords hashed with argon2id (`pwdlib`). Minimum length 12, no composition rules.
- Server side sessions. A random 256-bit token is sent in an HttpOnly, Secure, SameSite=Lax cookie. Only a hash of the token is stored in PostgreSQL. Sessions have idle and absolute expiry and can be revoked.
- CSRF defense for same-origin SPA: SameSite=Lax, an `Origin` header check on non-GET requests, and a required custom request header on non-GET requests.
- Login throttling is stored in PostgreSQL (no Redis).
- A single `Authenticator` port isolates the mechanism so a managed identity provider or OAuth can replace or extend it later.
- Email verification and password reset are deferred until an email provider is chosen, because they add a paid dependency. This is acceptable for a private alpha.
- The AI Companion runs with the authenticated user's identity and has no privileges beyond the tool allowlist.

---

## 10. Frontend architecture

- **Structure.** `app/` (providers, router, shell), `features/<name>/` (UI, hooks, API calls for one feature), `shared/` (API client, utilities), and `design-system/` (tokens and primitives, from M3).
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

- Secrets only in environment variables. `.env` is ignored and `.env.example` documents every variable. No secret reaches client code.
- Ownership check on every read and write. Cross-user access returns `not_found`.
- Input validated at the boundary. Output encoded by React. No raw HTML rendering of user or AI content.
- Cookies as in section 9. Explicit security headers and a content security policy are added with deployment configuration.
- Logs contain request metadata, never task content, passwords, tokens, or prompts.
- AI requests send only the minimum context required for the intent.
- Dependency hygiene: 14-day release-age gating, Dependabot with a 14-day cooldown, and `pip-audit` and `pnpm audit` reported in CI.
- Privacy by design: account export and account deletion are planned requirements, not afterthoughts.

---

## 15. Testing strategy

| Layer | Tooling | Scope |
|---|---|---|
| Domain | pytest, hypothesis | Lifecycle, intervals, overdue, validation. High branch coverage required from M1 |
| Application | pytest with in-memory fakes of ports | Use cases, approval, concurrency, idempotency |
| Infrastructure | pytest against real PostgreSQL | Repositories, migrations, constraints |
| API | pytest, httpx ASGI transport | Contracts, error format, auth, ownership |
| AI | pytest with fake model, golden set | Extraction, tool policy, injection resistance |
| Frontend unit and component | Vitest, Testing Library | Components, hooks, API client |
| End to end | Playwright (from M3) against the real stack | PRD acceptance criteria 1 to 18 |
| Accessibility | axe checks inside Playwright (from M4) | Keyboard and screen reader basics |
| Architecture | import-linter | Layer rules, run in CI |

Rules: database tests never skip silently when PostgreSQL is unreachable. Each PRD acceptance criterion maps to at least one automated test by M8.

---

## 16. Local development workflow

Prerequisites: Node 26 through nvm, corepack, uv, Docker with Compose, GNU Make.

```
make setup      install dependencies for both apps
make db-up      start PostgreSQL 18 (healthcheck gated)
make migrate    apply migrations
make dev-api    API on http://127.0.0.1:8000
make dev-web    web on http://127.0.0.1:5173, proxying /api to the API
make check      lint, typecheck, tests, build for both apps
make smoke      curl the health endpoints, including through the dev proxy
make db-reset   destroy and recreate the local database (development only)
```

The web dev server proxies `/api` to the API, so the browser sees one origin exactly as in production.

---

## 17. Environment configuration

| Variable | Used by | Purpose | Local default |
|---|---|---|---|
| `LIFESPACE_ENVIRONMENT` | API | `development`, `test`, or `production` | `development` |
| `LIFESPACE_DATABASE_URL` | API | SQLAlchemy URL, `postgresql+psycopg://` | local dev database |
| `LIFESPACE_TEST_DATABASE_URL` | tests | Test database | local test database |
| `LIFESPACE_LOG_LEVEL` | API | Log level | `INFO` |
| `LIFESPACE_CORS_ALLOWED_ORIGINS` | API | Optional explicit origins. Empty means same origin only. Wildcard is rejected | empty |
| `API_PROXY_TARGET` | Vite dev server | Where `/api` is proxied | `http://127.0.0.1:8000` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT` | Compose | Local database container | local-only values |

The web app has no API base URL variable because it always calls `/api` on its own origin.

---

## 18. Delivery workflow and CI

- One branch per Codex task named `m<milestone>/<slug>`. Conventional commit messages. No direct commits to `main`.
- CI runs on every push and pull request. Backend job: ruff check, ruff format check, mypy strict, import-linter, pytest with a PostgreSQL service, pip-audit. Frontend job: ESLint, Prettier check, tsc, Vitest, build, pnpm audit.
- Audit steps report but do not block until a policy for unfixable advisories exists.
- Dependabot covers uv, npm, GitHub Actions, and Docker with a 14-day cooldown.

---

## 19. Future extension points

| Need | Extension |
|---|---|
| Managed identity or OAuth | New `Authenticator` implementation |
| Email or push reminders | PostgreSQL-backed job table and worker (`SKIP LOCKED`) |
| AI streaming | Server-Sent Events from the `ai` orchestrator |
| Multi-step planning loops | Evaluate LangGraph behind the existing `ai` port in Phase 2 |
| Advanced scheduling | Constraint solver behind the scheduling interface, only if first-fit proves insufficient |
| Semantic memory or search | PostgreSQL `pgvector` before any separate vector database |
| Project Universe graph | Evaluate React Flow for the graph view |
| Tenant isolation hardening | PostgreSQL row level security |
| Horizontal scale | Stateless API processes already share sessions through PostgreSQL |

---

## 20. Product decisions still owned by the product owner

These are not technical decisions and are not made here. Each blocks the milestone shown.

| ID | Question | Architect's default if no answer | Blocks |
|---|---|---|---|
| P1 | Fixed commitments: separate entity or task type | Separate entity | M1 |
| P2 | Date-only deadline: overdue after the end of that local day | Yes | M1 |
| P3 | Initial status of new tasks (conflict C5) | Planned for reviewed creation, Inbox for unreviewed capture | M1 |
| P4 | Reopen completed and canceled tasks in MVP | Yes | M1 |
| P5 | Default bubble size when duration is unknown | Neutral fixed size labeled "no estimate" | M3 |
| P6 | UI palette versus the owner's blue-only preference (C12) | Follow UI_UX_SPEC | M3 |
| P7 | Default working hours, breaks, buffers | None invented. Owner supplies values | M5 |
| P8 | Week and month Time Flow views | After the daily view | M5 |
| P9 | AI task creation always shows a review step in MVP | Yes | M7 |

---

## 21. Development roadmap

Each milestone ends with a review report and owner acceptance. No milestone starts before the previous one is reviewed.

| Milestone | Scope | PRD alignment |
|---|---|---|
| M0 Foundation | Monorepo, tooling, health checks, database connectivity, migration baseline, error and logging baseline, CI, architecture enforcement | Maintainability 14.5 |
| M1 Domain core | Task model, lifecycle, time and interval rules, overdue computation, validation. Pure Python with unit and property tests | FR-011 to FR-018, FR-030 |
| M2 Persistence, auth, task API | Schema, migrations, repositories, authentication, ownership, task endpoints, status history, versioning, idempotency, generated API types | FR-005, FR-010 to FR-015, 14.2, 14.3 |
| M3 Design system and My Space | Tokens, primitives, shell, bubbles, layout, detail panel, manual create and edit, lifecycle actions, saved positions, empty, loading, error states, list fallback, Playwright | FR-060 to FR-063, 14.4 |
| M4 Spatial hardening | Keyboard alternatives, reduced motion, touch, performance with large collections, axe checks | NFR 14.1, 14.4 |
| M5 Commitments and Time Flow | Fixed commitments, manual scheduling, overlap detection, daily timeline, available time | FR-030 to FR-034, FR-064 |
| M6 History and reminders | Completed and canceled history, overdue indication, in-app reminders | FR-015, FR-070, FR-071 |
| M7 AI Companion (basic) | Model port, provider bake-off, structured extraction, draft review, clarification, read-only intents, allowlisted task operations, activity records, fallback | FR-001 to FR-004, FR-006, FR-050 to FR-055 |
| M8 Proposals and MVP hardening | Approval enforcement, stale revalidation, end to end coverage of PRD criteria 1 to 18, accessibility and responsive audit | FR-037, FR-053, MVP criteria |
| Phase 2 and later | Per the PRD | PRD Phases 2 to 4 |

Manual workflows (M1 to M6) precede the AI Companion so the product is useful without AI (PRD principle 10).

---

## 22. Review and verification policy

- Every task is reviewed from the actual Git diff, never from the agent's summary.
- Findings use the format in CLAUDE_INSTRUCTIONS section 14.3.
- A milestone closes only when blocking findings are fixed, tests were observed passing, and the owner accepts it.
- Where the reviewer cannot run a check, the exact command is provided to run locally.
