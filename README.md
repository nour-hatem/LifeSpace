# LifeSpace

**Your Life, In One Space.**

LifeSpace is an AI-powered personal productivity environment. Users describe their commitments in natural language, and LifeSpace turns them into structured tasks, schedules, and projects shown through an interactive 2D spatial workspace instead of a conventional task dashboard.

> **Project status:** Pre-implementation. The product specification is complete and the technical blueprint is awaiting approval. No application code exists yet.

## Core principles

- AI assists, and the user stays in control.
- Structured, persisted data is the source of truth.
- The LLM interprets and proposes. Deterministic application logic validates, authorizes, and persists.
- A deadline is not a scheduled time. Completed work is not canceled work. A bubble's position is not its schedule.
- The product must remain useful when AI is unavailable.

## Product at a glance

| Environment | Purpose | Release |
|---|---|---|
| My Space | Spatial workspace of interactive task bubbles | MVP |
| Time Flow | Daily timeline with fixed commitments and scheduled tasks | MVP (daily view) |
| AI Companion | Natural-language capture, extraction, review, and proposals | MVP (basic) |
| Project Universe | Projects, milestones, and dependencies | Later |
| Focus Mode | Distraction-free single-task sessions | Later |
| Memory Garden | Visual history of completed work | Later |

Release scope is defined in `docs/product/PRD.md`.

## Documentation

All specifications live in [`docs/`](docs/README.md).

| Document | Governs |
|---|---|
| [`PRD.md`](docs/product/PRD.md) | Product vision, scope, requirements, acceptance criteria |
| [`BUSINESS_RULES.md`](docs/business/BUSINESS_RULES.md) | Domain behavior, lifecycle, scheduling, AI permissions |
| [`USER_FLOWS.md`](docs/product/USER_FLOWS.md) | End-to-end journeys and edge cases |
| [`AGENT_SPEC.md`](docs/engineering/AGENT_SPEC.md) | AI Companion behavior, tools, approval orchestration |
| [`UI_UX_SPEC.md`](docs/design/UI_UX_SPEC.md) | Visual language, navigation, interaction design |
| [`CLAUDE_INSTRUCTIONS.md`](docs/engineering/CLAUDE_INSTRUCTIONS.md) | Architect and reviewer responsibilities, collaboration workflow |
| [`TECHNICAL_BLUEPRINT.md`](docs/engineering/TECHNICAL_BLUEPRINT.md) | Proposed architecture, stack, roadmap, open decisions |

## Repository layout

Current:

```
lifespace/
├── .gitignore
├── README.md
└── docs/
    ├── README.md        Documentation index and authority order
    ├── product/         PRD, user flows
    ├── design/          UI and UX specification
    ├── business/        Business rules
    └── engineering/     Agent spec, workflow, blueprint, Codex prompts
```

Planned application directories (`apps/web`, `apps/api`) are defined in the technical blueprint and will be created during the first implementation milestone after the stack is approved.

## Development workflow

LifeSpace is built with three roles.

- **Product owner and product partner** define requirements, business rules, and acceptance criteria.
- **Technical architect and reviewer** plans architecture, writes scoped implementation tasks, and reviews every change against the specifications.
- **Coding agent (Codex in VS Code)** is the only agent that writes application source code.

Every feature moves through product definition, technical planning, implementation, review, correction, verification, and product acceptance. No milestone starts before the previous one is reviewed.

## Getting started

Not available yet. Setup instructions will be added when the foundation milestone is accepted.

## License

Not yet decided.
