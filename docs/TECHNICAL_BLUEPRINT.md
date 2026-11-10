# LifeSpace Technical Blueprint

**Status:** Proposed. Awaiting product-owner approval. Nothing in this document is final until recorded as an ADR.
**Author role:** Technical architect and reviewer
**Inputs:** `PRD.md`, `BUSINESS_RULES.md`, `USER_FLOWS.md`, `AGENT_SPEC.md`, `UI_UX_SPEC.md`, `CLAUDE_INSTRUCTIONS.md`

---

## 1. Specification audit

### 1.1 Result

All six specification files are present and preserved byte for byte in `docs/`. The documents are consistent in intent. The conflicts below must be resolved before the affected milestone starts.

### 1.2 Conflicts and gaps

| ID | Finding | Sources | Proposed resolution | Needed before |
|---|---|---|---|---|
| C1 | Memory Garden is P2 in the PRD and UI spec, but P1 in the user flows. | PRD FR-067, UI_UX 17, USER_FLOWS 17 | A plain History list (completed and canceled) is MVP via FR-015. The visual Memory Garden stays P2. | M6 |
| C2 | Drag-onto-task dependency creation is listed as a core bubble interaction, but dependencies are P1. | UI_UX 4.2B, PRD FR-043 | Omit the interaction from MVP. | M3 |
| C3 | Recurring fixed commitments ("every Monday 10 to 12") appear in the P0 capture flow, but recurrence is P1. | USER_FLOWS 5.5, PRD FR-020 | MVP supports single-occurrence commitments only. The AI asks for a date, or states recurrence is not yet supported. | M5 |
| C4 | Conflict detection is listed under Phase 2, but FR-033 and MVP criterion 12 make overlap detection P0. | PRD 7, FR-033, 16.12 | Basic overlap detection is MVP. Alternatives and proposals are Phase 2. | M5 |
| C5 | Inbox cannot transition to Completed, yet Journey D and FR-013 allow completing any active task. Initial status for manual creation is not defined. | BUSINESS_RULES 4.2, PRD 12D | New reviewed tasks start as Planned. Inbox is used only for unreviewed quick capture. | M1 |
| C6 | Bubble position persistence is an open decision, but the flows already assume it is saved. | PRD 18.7, USER_FLOWS 7.3, BUSINESS_RULES 11.4 | Persist positions in a layout table separate from task data. | M3 |
| C7 | Account model is an open decision, but the flows assume sign-in. | PRD 18.1, USER_FLOWS 4.1 | Multi-user ready from day one. Provider decision D1. | M2 |
| C8 | Reopen and restore is conditional in the rules but listed under P0 lifecycle flows. | BUSINESS_RULES 4.2, USER_FLOWS 9.4 | Support Completed to Planned and Canceled to Planned in MVP. | M1 |
| C9 | The category list includes "Projects", which overlaps with the Project entity. | PRD FR-016 | Keep the category value. It carries no project semantics until projects ship. | M2 |
| C10 | Voice input is mentioned in the UI spec, but deferred by the PRD and agent spec. | UI_UX 9.3, PRD 18.8 | Exclude voice from MVP. | M7 |
| C11 | CLAUDE_INSTRUCTIONS 21 says to wait for blueprint approval before creating the GitHub repository. | CLAUDE_INSTRUCTIONS 21 | The owner explicitly authorized repository creation. That authorization covers repository setup only, not the stack. | Resolved |
| C12 | The UI palette uses violet, cyan, green, amber, and red. The owner's saved CSS preference is blue only. | UI_UX 2.2 | Follow the UI spec unless the owner overrides it. Decision D12. | M3 |

### 1.3 Confirmed existing decisions

No stack, framework, database, provider, or infrastructure decision exists yet. All of Section 3 is a proposal.

---

## 2. Architecture overview

A modular monolith with two deployable applications and one database.

```
 Browser (React SPA)
     | HTTPS, JSON, cookies
     v
 FastAPI (apps/api)
     |-- api/             HTTP routing, request and response schemas, auth dependency
     |-- application/     use cases, validation, approval enforcement, transactions
     |-- domain/          task rules, lifecycle, time and interval rules, scheduling
     |-- ai/              intent schemas, tool allowlist, orchestration, prompts
     |-- infrastructure/  database, model provider adapters, notifications
     v
 PostgreSQL
```

Why a monolith: the PRD forbids unnecessary distributed infrastructure, the scheduling engine and task rules must share transactions, and a single deployable keeps review tractable.

### 2.1 Dependency rules (enforced by tooling)

- `domain` imports nothing from FastAPI, SQLAlchemy, Pydantic models of the API, or any LLM SDK.
- `application` imports `domain` only, and talks to infrastructure through interfaces it defines.
- `infrastructure` implements those interfaces.
- `api` calls `application`. It never touches the database or the model provider directly.
- `ai` calls `application` use cases through a fixed allowlist. It never writes to persistence.

These rules are enforced with an import-linter contract checked in CI.

---

## 3. Recommended technology stack

| Area | Recommendation | Rationale |
|---|---|---|
| Backend language | Python 3.12 | Strong typing support, mature scheduling and AI ecosystem |
| Backend framework | FastAPI with Pydantic v2 | Typed contracts, OpenAPI generation, async support for AI calls |
| ORM and migrations | SQLAlchemy 2.x (async) and Alembic | Explicit transactions, mature migrations |
| Database | PostgreSQL 16 | Time zone aware timestamps, range types, transactional integrity |
| Package tooling | uv (Python), pnpm (Node) | Fast, lockfile based |
| Backend quality | ruff, mypy (strict), pytest, import-linter | Lint, typing, tests, architecture boundaries |
| Frontend | React, TypeScript (strict), Vite | Component model suited to a reusable design system |
| Routing | React Router | Deep links per environment, animated transitions |
| Server state | TanStack Query | Confirmed-state caching, retries, explicit loading and error states |
| UI state | Zustand (only when needed) | Small store for selection, panels, and drafts |
| Spatial layout | SVG and DOM nodes with d3-force for layout | Real focusable elements give keyboard and screen reader support. Canvas would not. |
| Motion | Motion (Framer Motion) with reduced-motion support | Layout and presence animation |
| Accessible primitives | Radix UI | Menus, dialogs, popovers with correct focus handling |
| Styling | CSS variables for design tokens, CSS Modules or Tailwind | To be fixed in the design system milestone |
| Frontend quality | ESLint, Prettier, Vitest, Testing Library, Playwright (from M3) | Unit, component, and end-to-end coverage |
| API contract | OpenAPI export and generated TypeScript types (from M2) | Removes hand-written duplicate types |
| Local infrastructure | Docker Compose with PostgreSQL only | No Redis or vector database until a feature needs one |
| CI | GitHub Actions | Lint, type check, test, build on every pull request |

Deliberately excluded from the MVP: Redis, Qdrant or any vector store, message queues, microservices, an agent framework, GraphQL, server-side rendering.

---

## 4. Responsibilities

### 4.1 Frontend
- Render My Space, Time Flow, the task detail surface, and the AI Companion.
- Collect input, show drafts and proposals, collect approval.
- Hold only temporary UI state. Render persisted state returned by the backend.
- Provide loading, empty, error, and conflict states, keyboard alternatives to drag, and a list fallback for small screens.
- Never fabricate a successful mutation. Optimistic updates require rollback.

### 4.2 Backend
- Authenticate every request and verify ownership on every read and write.
- Validate all input, including all AI output, at the application boundary.
- Enforce lifecycle transitions, interval rules, approval, optimistic concurrency, and idempotency.
- Persist atomically and return authoritative results with explicit result categories (`succeeded`, `rejected`, `validation_failed`, `conflict`, `not_found`, `unauthorized`, `partially_succeeded`, `failed`, `unknown_pending_verification`).
- Compute overdue state, never store it.

### 4.3 Database
- Source of truth for tasks, commitments, status history, workspace layout, proposals, and activity records.
- Every user-owned table carries `user_id`.
- Timestamps are stored as UTC with the user's IANA time zone held on the profile.
- Date-only deadlines are stored as dates, distinct from timestamp deadlines.
- Constraints back up the application rules (positive durations, end after start). They do not replace them.

### 4.4 AI agent
- Classify intent, extract structured fields, mark uncertainty, ask clarifying questions, explain results.
- Use only an explicit allowlist of typed application operations.
- Treat task text and retrieved records as untrusted data.
- Never compute authoritative availability, never write to storage, never report success before an authoritative result.
- Provider sits behind an interface. Failure of the provider must leave all manual workflows working.

### 4.5 Infrastructure
- Docker Compose for local PostgreSQL.
- Environment based configuration. Secrets never reach client code or the repository.
- CI on every pull request. Deployment target is undecided (decision D10).

---

## 5. Proposed source structure

```
lifespace/
├── apps/
│   ├── api/
│   │   ├── pyproject.toml
│   │   ├── alembic.ini
│   │   ├── migrations/
│   │   ├── src/lifespace/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── domain/            tasks, lifecycle, time, scheduling (pure Python)
│   │   │   ├── application/       use cases and ports
│   │   │   ├── infrastructure/    db, ai providers, notifications
│   │   │   ├── api/               routers, schemas, dependencies, error mapping
│   │   │   └── ai/                intents, tool registry, orchestration, prompts
│   │   └── tests/
│   │       ├── unit/
│   │       └── integration/
│   └── web/
│       ├── package.json
│       ├── index.html
│       └── src/
│           ├── app/               providers, router, shell
│           ├── design-system/     tokens and primitives
│           ├── features/
│           │   ├── my-space/
│           │   ├── time-flow/
│           │   ├── tasks/
│           │   ├── companion/
│           │   ├── history/
│           │   └── settings/
│           └── shared/            api client, utilities
├── docs/
├── docker-compose.yml
├── Makefile
├── AGENTS.md
└── .github/workflows/ci.yml
```

---

## 6. Key technical design decisions (proposed, reversible where noted)

1. **Domain model.** `Task`, `FixedCommitment` (separate entity, decision D4), `TaskStatusEvent`, `WorkspaceLayout` (position only, never schedule), `Proposal`, `ActivityRecord`.
2. **Time.** Intervals are start inclusive, end exclusive. Overlap is `A.start < B.end AND B.start < A.end`. Deadline and scheduled interval are separate columns that never update each other.
3. **Concurrency.** An integer `version` on mutable records. Updates carry the expected version. A mismatch returns `conflict`.
4. **Idempotency.** Creating operations accept an idempotency key. Retried requests return the original result.
5. **Proposals.** Persisted with a version and a snapshot fingerprint of the data they depend on. Approval refers to one proposal version. Application revalidates before applying and rejects stale proposals.
6. **AI boundary.** Model output is parsed into typed schemas. Anything that fails validation is rejected, never repaired silently.
7. **Audit.** Every AI initiated mutation writes an activity record with previous value, applied value, approval information, and result.
8. **Observability.** Structured logs that never include task content by default.

---

## 7. Decisions requiring owner approval

| ID | Decision | Recommendation | Blocks |
|---|---|---|---|
| D1 | Account model and authentication approach (self-built sessions, managed provider, or single-user local) | Multi-user ready schema. Choose provider before M2. | M2 |
| D2 | Confirm stack: FastAPI, PostgreSQL, React with TypeScript and Vite | Approve as proposed | M0 |
| D3 | Confirm monorepo layout `apps/api` and `apps/web` | Approve as proposed | M0 |
| D4 | Fixed commitments as a separate entity or a task type | Separate entity | M1 |
| D5 | Date-only deadline semantics | Stored as a date. Overdue after the end of that day in the user's time zone. | M1 |
| D6 | Initial status of new tasks (see C5) | Planned for reviewed creation, Inbox for unreviewed capture | M1 |
| D7 | Deletion policy | Soft delete with a recoverable state | M2 |
| D8 | Reopen and restore in MVP | Yes | M1 |
| D9 | Reminder channel in MVP | In-app only | M6 |
| D10 | Hosting and deployment target | Defer until after MVP | Release |
| D11 | Default working hours, breaks, buffers for available time display | Owner supplies values. No defaults are invented. | M5 |
| D12 | UI color palette versus blue-only preference | Follow UI spec | M3 |
| D13 | AI task creation confirmation | Always review before save in MVP | M7 |
| D14 | Model provider and whether to use an orchestration framework | Provider behind an interface. No framework in MVP. | M7 |
| D15 | Default bubble size when duration is unknown | Fixed neutral size, labeled "no estimate" | M3 |
| D16 | Week and month Time Flow views | Defer after daily view | M5 |

---

## 8. Development roadmap

Each milestone ends with a review report in `docs/reviews/` and owner acceptance.

| Milestone | Scope | PRD alignment |
|---|---|---|
| M0 Foundation | Repository tooling, backend and frontend skeletons, PostgreSQL via Compose, CI, import boundary enforcement, health endpoints | Maintainability 14.5 |
| M1 Domain core | Task model, lifecycle transitions, time and interval rules, overdue computation, validation. Pure Python with unit tests. | FR-011 to FR-018, FR-030 |
| M2 Persistence, auth, task API | Schema and migrations, repositories, authentication, ownership checks, CRUD and lifecycle endpoints, status history, versioning, idempotency, generated API types | FR-005, FR-010 to FR-015, 14.2, 14.3 |
| M3 Design system and My Space | Tokens, primitives, shell and navigation, task bubbles, layout, detail panel, manual create and edit, lifecycle actions, saved positions, empty, loading, error states, list fallback | FR-060 to FR-063, 14.4 |
| M4 Spatial hardening | Keyboard alternatives, reduced motion, touch behavior, performance with large collections | NFR 14.1, 14.4 |
| M5 Commitments and Time Flow | Fixed commitments, manual scheduling, overlap detection, daily timeline, available time view | FR-030 to FR-034, FR-064 |
| M6 History and reminders | Completed and canceled history, overdue indication, in-app reminders | FR-015, FR-070, FR-071 |
| M7 AI Companion (basic) | Provider interface, structured extraction, draft review, clarification, read-only intents, task create and supported updates through the allowlist, activity records, AI-unavailable fallback | FR-001 to FR-004, FR-006, FR-050 to FR-055 |
| M8 Proposals and MVP hardening | Approval enforcement for consequential changes, stale revalidation, end-to-end tests of PRD criteria 1 to 18, accessibility and responsive audit | FR-037, FR-053, MVP criteria |
| Phase 2 | Scheduling proposals, dynamic rescheduling, dependencies, recurrence, daily and weekly review, Project Universe | PRD Phase 2 |
| Phase 3 and 4 | Per the PRD | PRD Phases 3 and 4 |

Manual workflows (M1 to M6) deliberately precede the AI Companion, so the product is useful without AI (PRD principle 10).

---

## 9. Review and verification policy

- Every task is reviewed from the actual Git diff, never from the agent's summary.
- Review findings use the format in `CLAUDE_INSTRUCTIONS.md` section 14.3.
- A milestone is not closed until blocking findings are fixed, tests were observed passing, and the owner accepts it.
- Where checks cannot be run by the reviewer, the exact command is provided to run locally.
