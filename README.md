# LifeSpace

**Your Life, In One Space.**

LifeSpace is an AI-powered personal productivity environment. Users describe their commitments in natural language, and LifeSpace turns them into structured tasks, schedules, and projects shown through an interactive 2D spatial workspace instead of a conventional task dashboard.

> **Project status:** Foundation (M0) is implemented: a local single-user FastAPI backend, a React frontend, PostgreSQL 18 in Docker, a migration baseline, and quality tooling. There are no product features yet. The next milestone is M1 (domain core).

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

```
lifespace/
├── .editorconfig  .env.example  .gitignore  .nvmrc
├── AGENTS.md  Makefile  README.md  docker-compose.yml
├── apps/
│   ├── api/         FastAPI backend (uv project, Alembic migrations, tests)
│   └── web/         React frontend (npm package, Vite, Vitest)
├── docs/            Specifications, blueprint, implementation prompts
├── infra/postgres/  Database init scripts
└── scripts/         doctor.sh and smoke.sh
```

The layout follows section 5 of the technical blueprint. Later milestones add `domain/`, `application/`, and `ai/` to the API and features, a router, and a design system to the web app.

## Development workflow

LifeSpace is built with three roles.

- **Product owner and product partner** define requirements, business rules, and acceptance criteria.
- **Technical architect and reviewer** plans architecture, writes scoped implementation tasks, and reviews every change against the specifications.
- **Coding agent (OpenCode with DeepSeek)** is the only agent that writes application source code.

Every feature moves through product definition, technical planning, implementation, review, correction, verification, and product acceptance. No milestone starts before the previous one is reviewed.

## Getting started

### Prerequisites

- **Node 22.22.3** through nvm (the version in `.nvmrc`)
- **npm 10.9.8**, installed with Node. pnpm is not installed and is not used.
- **uv 0.11.28** for the isolated Python environment
- **Docker Desktop** with Compose, which runs PostgreSQL 18
- **GNU Make**

### One-time Docker preparation

Start Docker Desktop, then select its context:

```bash
docker context use desktop-linux
```

`make doctor` fails when the Docker daemon is unreachable.

### Disk space

Keep at least 3 GB free on the filesystem that holds the repository. `make doctor` fails below that threshold.

### First run

```bash
cd "/path/to/LifeSpace"
make doctor    # check Node, npm, uv, Docker, disk space, and ports
make setup     # create .env and install the Python and JavaScript dependencies
make db-up     # start PostgreSQL 18 on 127.0.0.1:5433
make migrate   # apply the Alembic migrations
```

### Daily commands

```bash
make dev-api    # API on 127.0.0.1:8000 (one terminal)
make dev-web    # web app on 127.0.0.1:5173 (another terminal)
make smoke      # check both servers and the Vite proxy
make test       # backend and frontend tests
make check      # lint, typecheck, test, and build
make db-down    # stop the database, keeping its data
make db-reset   # delete local database data and recreate the database
```

The web app runs at <http://127.0.0.1:5173> and the API health endpoint at <http://127.0.0.1:8000/api/health>.

The database is published only on `127.0.0.1:5433`. A host PostgreSQL service on port 5432 is not used by this project. SQL files in `infra/postgres/init/` run only when the database volume is created for the first time, so after changing them run `make db-reset`.

### Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `docker info` or `make db-up` fails | Docker Desktop is not running. Start it and run `docker context use desktop-linux`. |
| A port is in use (`5433`, `8000`, `5173`) | Another process owns it. Stop that process; `make doctor` lists the ports it checks. |
| Writes fail with `ENOSPC` | Free space on the filesystem that holds the repository. At least 3 GB is required. |
| npm skips devDependencies | The login shell exports `NODE_ENV=production`. `apps/web/.npmrc` sets `include=dev`, and every npm script runs through `env -u NODE_ENV`. |
| uv tries to download Python | Not allowed here. Every uv call runs with `UV_PYTHON_DOWNLOADS=never` (exported by the Makefile); Python 3.14.4 is already installed. |

## License

Not yet decided.
