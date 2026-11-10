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
    └── codex-prompts/
```

Folders for architecture decision records (`engineering/adr/`) and review reports (`engineering/reviews/`) are created when the first record exists.

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
| [`engineering/TECHNICAL_BLUEPRINT.md`](engineering/TECHNICAL_BLUEPRINT.md) | Proposed architecture, stack, source structure, roadmap, specification audit, and decisions awaiting approval |
| [`engineering/codex-prompts/`](engineering/codex-prompts/) | Numbered implementation prompts issued to the coding agent |

## Document authority

When documents conflict, apply this order and raise the conflict for a product decision. Do not resolve it silently.

1. `PRD.md`
2. `BUSINESS_RULES.md`
3. `USER_FLOWS.md`
4. `AGENT_SPEC.md`
5. `UI_UX_SPEC.md`
6. `CLAUDE_INSTRUCTIONS.md`
