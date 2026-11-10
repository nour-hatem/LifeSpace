# LifeSpace Documentation

## Specifications

The six original specification files are preserved unchanged.

| File | Purpose |
|---|---|
| `PRD.md` | Product-level source of truth for goals, scope, and requirements |
| `BUSINESS_RULES.md` | Deterministic domain rules for tasks, time, scheduling, and AI permissions |
| `USER_FLOWS.md` | User journeys and system behavior |
| `AGENT_SPEC.md` | AI Companion behavior, tool boundaries, and approval contract |
| `UI_UX_SPEC.md` | Visual identity, spatial navigation, and interaction design |
| `CLAUDE_INSTRUCTIONS.md` | Responsibilities of the architect and reviewer, and the collaboration workflow |

## Technical documents

| File | Purpose |
|---|---|
| `TECHNICAL_BLUEPRINT.md` | Proposed architecture, stack, source structure, roadmap, specification audit, and decisions awaiting approval |
| `adr/` | Architecture decision records, one file per approved decision |
| `codex-prompts/` | Numbered implementation prompts issued to the coding agent |
| `reviews/` | Review reports for each completed implementation task |

## Document authority

When documents conflict, apply this order and raise the conflict for a product decision. Do not resolve it silently.

1. `PRD.md`
2. `BUSINESS_RULES.md`
3. `USER_FLOWS.md`
4. `AGENT_SPEC.md`
5. `UI_UX_SPEC.md`
6. `CLAUDE_INSTRUCTIONS.md`
