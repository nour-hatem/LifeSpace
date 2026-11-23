# LifeSpace Documentation

## Structure

```
docs/
├── product/
│   ├── PRD.md
│   └── USER_FLOWS.md
├── design/
│   └── UI_UX_SPEC.md
├── business/
│   └── BUSINESS_RULES.md
└── engineering/
    ├── AGENT_SPEC.md
    ├── CLAUDE_INSTRUCTIONS.md
    ├── TECHNICAL_BLUEPRINT.md
    └── adr/
```

Architecture decision records live in `engineering/adr/` (one file per decision: `0001-m1-domain-decisions.md`, `0002-m2-persistence-and-task-api.md`, `0003-m3-frontend-decisions.md`). A folder for review reports (`engineering/reviews/`) is created when the first report is written.

## Specifications

The six original specification files are preserved unchanged. They refer to each other by file name only (for example `PRD.md`), and every file name is unique, so use this table to find the current location.

| File | Location | Purpose |
|---|---|---|
| `PRD.md` | [`product/PRD.md`](product/PRD.md) | Product-level source of truth for goals, scope, and requirements |
| `USER_FLOWS.md` | [`product/USER_FLOWS.md`](product/USER_FLOWS.md) | User journeys and system behavior |
| `UI_UX_SPEC.md` | [`design/UI_UX_SPEC.md`](design/UI_UX_SPEC.md) | Visual identity, spatial navigation, and interaction design |
| `BUSINESS_RULES.md` | [`business/BUSINESS_RULES.md`](business/BUSINESS_RULES.md) | Deterministic domain rules for tasks, time, scheduling, and AI permissions |
| `AGENT_SPEC.md` | [`engineering/AGENT_SPEC.md`](engineering/AGENT_SPEC.md) | AI Companion behavior, tool boundaries, and approval contract |
| `CLAUDE_INSTRUCTIONS.md` | [`engineering/CLAUDE_INSTRUCTIONS.md`](engineering/CLAUDE_INSTRUCTIONS.md) | Responsibilities of the architect and reviewer, and the collaboration workflow |

## Technical documents

| Item | Purpose |
|---|---|
| [`engineering/TECHNICAL_BLUEPRINT.md`](engineering/TECHNICAL_BLUEPRINT.md) | Approved architecture, stack and versions, repository structure, conventions, roadmap, specification audit, and open product decisions |

## Document authority

When documents conflict, apply this order and raise the conflict for a product decision. Do not resolve it silently.

1. `PRD.md`
2. `BUSINESS_RULES.md`
3. `USER_FLOWS.md`
4. `AGENT_SPEC.md`
5. `UI_UX_SPEC.md`
6. `CLAUDE_INSTRUCTIONS.md`
