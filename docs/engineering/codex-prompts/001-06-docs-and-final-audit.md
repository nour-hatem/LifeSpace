# Task 001, Part 6 of 6: Documentation and final audit

**Status:** Ready. The foundation task is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and does not depend on earlier conversation, only on the repository.
**Depends on:** Parts 1 to 5
**Branch:** `m0/foundation`
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/001-06-docs-and-final-audit.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 001 | M0 FOUNDATION | PART 6 OF 6 | Documentation and final audit

SESSION CONTEXT
You are the implementation agent for LifeSpace, a local single-user application. Task 001 builds the technical foundation in 6 parts. Each part runs in a separate session and you have no memory of earlier parts. Everything you need is in this prompt and in the repository. A separate architect reviews your Git diff, so do exactly what this part asks and nothing else. Do not start work that belongs to another part.

CONTEXT BUDGET (this session has a limited context window)
- Read only the files this prompt names. Read docs/engineering/TECHNICAL_BLUEPRINT.md once, in full, at the start. Do not read any other document under docs/.
- Never print lockfiles, node_modules, .venv, or full logs. Pipe long command output through "tail -n 30".
- Never run a server in the foreground. Use this background pattern and always stop the server afterwards.
    start:  setsid bash -c 'exec make dev-api' > /tmp/lifespace-api.log 2>&1 & echo $! > /tmp/lifespace-api.pid
    wait:   for i in $(seq 1 60); do curl -fsS http://127.0.0.1:8000/api/health && break; sleep 0.5; done
    stop:   kill -- -"$(cat /tmp/lifespace-api.pid)"; sleep 1; ss -ltn | grep ':8000 ' || echo "port 8000 free"
  The same pattern works for make dev-web (port 5173, files /tmp/lifespace-web.log and /tmp/lifespace-web.pid).
- If the same command fails twice for the same reason, stop and report the exact error. Try at most two different fixes for one problem.
- Your training data may predate the pinned versions (FastAPI 0.133, Starlette 1.x, SQLAlchemy 2.0.50, pytest-asyncio 1.4, Vite 8, Vitest 5, TypeScript 6, ESLint 9 flat config). When unsure of an API, read the installed package source or README (under apps/api/.venv/lib/python3.14/site-packages or apps/web/node_modules) instead of guessing.

SCOPE RULES (owner decisions, binding)
- Local single-user app. No authentication, registration, sessions, OAuth, accounts, user_id columns, or multi-tenancy. Authentication is deferred and is NOT an approved requirement.
- No Redis, vector database, message broker, agent framework, cloud infrastructure, CI, Dependabot, app Dockerfiles, or deployment configuration.
- No unnecessary abstractions. Write the simplest code that satisfies this part.

MACHINE FACTS (do not fight them, do not change them)
- Ubuntu 26.04, Node 22.22.3 (nvm), npm 10.9.8, Python 3.14.4, uv 0.11.28, Docker Desktop with Compose v5, GNU Make 4.4.1. pnpm is not installed and must not be used.
- Do not install, upgrade, or remove any global tool or package. No sudo. No npm install -g, pip install, or uv python install. Python dependencies live only in apps/api/.venv created by uv. Every uv call must run with UV_PYTHON_DOWNLOADS=never (the Makefile exports it).
- The repository path contains a space ("/home/nour/AI Factory/LifeSpace"). Quote every path in the Makefile and scripts, and prefer paths relative to the repository root.
- The login shell exports NODE_ENV=production, which makes npm skip devDependencies. apps/web/.npmrc contains include=dev and the npm scripts dev, build, preview, and test run through "env -u NODE_ENV". Run any ad hoc npm command with "env -u NODE_ENV".
- A host PostgreSQL service already listens on 127.0.0.1:5432. Never use that port or connect to it. The project database is a Docker container published on 127.0.0.1:5433.
- Docker Desktop must be running with the desktop-linux context selected. Do not change the Docker context or start or stop Docker Desktop. If Docker is unreachable, stop and report it.
- Disk space on /home can be low. If a command fails with ENOSPC, stop and report. Do not work around it.

GIT RULES
- Work on branch m0/foundation. Create it from main only if it does not exist. Do not commit to main, push, merge, or rewrite history.
- Never modify files under docs/.
- Commit your work in small conventional commits and finish with a clean git status.
- If git status is dirty at the start and the changes do not belong to this part, stop and report. Never discard changes you did not make.
- Never create or commit .env, secrets, or credentials.

START CHECK (run first)
1. git branch --show-current must print m0/foundation. git status --short must be empty.
2. Confirm Part 5 is done: Makefile contains the targets setup, lint, format, typecheck, test, build, check, smoke, and help; scripts/smoke.sh exists. If not, stop and tell the user to run Part 5 first.
3. Read docs/engineering/TECHNICAL_BLUEPRINT.md in full, then read the current README.md, Makefile, and the two files apps/api/pyproject.toml and apps/web/package.json (they are the source of truth for the documentation you write).
4. Run: docker info --format '{{.ServerVersion}}' and make db-up (the final audit needs the database).

OBJECTIVE
Write the documentation, then run the final audit of the whole of Task 001. Write documentation only. Change no source code in this part unless the audit exposes a defect, and list every such fix in your report.

DELIVERABLES
1. README.md: replace ONLY the "Getting started" section (keep every other section unchanged). It must contain, in this order: prerequisites (nvm and Node 22.22.3, npm, uv, Docker Desktop, GNU Make, and that pnpm is not used); one-time Docker preparation (start Docker Desktop, run: docker context use desktop-linux); the disk space note (at least 3 GB free); the first-run command sequence (cd into the repository, make doctor, make setup, make db-up, make migrate); the daily commands (make dev-api in one terminal, make dev-web in another, make smoke, make test, make check, make db-down, make db-reset); the dev URLs (http://127.0.0.1:5173 and http://127.0.0.1:8000/api/health); a note that the database is published on 127.0.0.1:5433 and that the host PostgreSQL on 5432 is not used; a note that init scripts run only on first volume creation so changes need make db-reset; and a troubleshooting list (Docker not reachable, port in use, ENOSPC, NODE_ENV=production and why apps/web/.npmrc handles it, uv never downloads Python).
2. apps/api/README.md: layer responsibilities (api, infrastructure now; domain, application, ai later), the dependency rules and the two import-linter contracts, the settings variables, how to run tests (unit needs no database, integration needs make db-up), and the testing rules (httpx.AsyncClient with ASGITransport, no TestClient, filterwarnings = error, dispose engines).
3. apps/web/README.md: commands, the folder layout, and a "Dependency notes" section explaining why TypeScript is 6.0.3 (typescript-eslint requires TypeScript below 6.1) and ESLint is 9.39.5 (eslint-plugin-jsx-a11y supports ESLint 9 or lower), that jsdom 31 requires Node 22.22.2 or newer, and that NODE_ENV=production is neutralized by .npmrc and the npm scripts.
4. AGENTS.md at the repository root, maximum 120 lines, agent neutral (it is read by any coding agent, including OpenCode). Sections: documentation reading order and authority (docs/README.md is the index; PRD, BUSINESS_RULES, USER_FLOWS, AGENT_SPEC, UI_UX_SPEC, then CLAUDE_INSTRUCTIONS; conflicts are raised, never silently resolved); the three roles (product owner decides product, architect plans and reviews, the coding agent is the only one that writes application source code); domain invariants (a deadline is not a scheduled time, completed is not canceled, a bubble position is not a schedule, the AI proposes and the application validates); the layer dependency rules; the machine facts (paths with a space, NODE_ENV=production, host PostgreSQL on 5432 unused, database on 5433, Docker Desktop context, uv never downloads Python, no global installs, no sudo); common commands; testing rules; no secrets in code; no product decisions without approval; branch and commit conventions (branch m<milestone>/<slug>, conventional commits, no push or merge without the owner); context budget habits for agents with a limited context window (read only what is needed, short command output, background servers); and the final report format.

FINAL AUDIT (run each, record the real result; keep output short)
1. make doctor (no FAIL).
2. make check (zero errors and zero warnings; record test counts for backend unit, backend integration, and frontend).
3. Start both servers with the background pattern, run make smoke (all PASS), stop both servers, confirm ports 8000 and 5173 are free.
4. git diff main --stat -- docs must print nothing (no file under docs/ changed).
5. git status --short must be empty. git ls-files must show no .env, node_modules, .venv, dist, or credentials. git ls-files | grep -E 'uv.lock|package-lock.json' must show both lockfiles.
6. git grep -nE "(ghp_|github_pat_|sk-[A-Za-z0-9]{20}|BEGIN [A-Z ]*PRIVATE KEY)" must print nothing.
7. Layout check against blueprint section 5: list git ls-files at depth 3 (git ls-files | awk -F/ 'NF<=3' | head -80). Nothing may exist that the blueprint assigns to a later milestone (no domain, application, ai, features, design-system, router, Playwright, CI workflow, Dockerfile, or authentication code).
8. The two import-linter contracts pass: cd apps/api && uv run lint-imports | tail -n 5.
9. Versions actually installed: uv pip list --project apps/api (or uv run --project apps/api python -c) for fastapi, starlette, pydantic, pydantic-settings, sqlalchemy, asyncpg, alembic, uvicorn, pytest, pytest-asyncio, httpx, ruff, mypy, import-linter; and cd apps/web && env -u NODE_ENV npm ls --depth=0. Compare with the approved versions and list any difference.
10. git log --oneline main..HEAD (the whole branch).

COMMIT
One commit for the documentation, for example "docs: add getting started, app readmes, and agent instructions", plus one commit per defect fix if the audit required any. git status must be clean afterwards.

FINAL REPORT FOR THE WHOLE TASK (replaces the short report for this part, maximum 60 lines): summary of what was built; files created grouped by area; the result of each audit item above with real command output summaries; dependency versions installed and any deviation from the approved versions with the exact error; deviations from the task and why; open questions or risks; the output of git log --oneline main..HEAD.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Anything the next part must know.
Finish by telling the user: "Part 6 is finished. Start a new session for the next part."
```
