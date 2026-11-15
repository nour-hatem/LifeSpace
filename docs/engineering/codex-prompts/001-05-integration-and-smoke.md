# Task 001, Part 5 of 6: Aggregate targets, smoke script, and end-to-end verification

**Status:** Ready. The foundation task is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and does not depend on earlier conversation, only on the repository.
**Depends on:** Parts 1 to 4
**Branch:** `m0/foundation`
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/001-05-integration-and-smoke.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 001 | M0 FOUNDATION | PART 5 OF 6 | Aggregate targets, smoke script, and end-to-end verification

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
2. Confirm the earlier parts exist: Makefile, docker-compose.yml, scripts/doctor.sh, apps/api/uv.lock, apps/api/migrations/versions/0001_baseline.py, apps/web/package-lock.json. If any is missing, stop and tell the user which part to run first.
3. Read docs/engineering/TECHNICAL_BLUEPRINT.md in full.
4. Run: docker info --format '{{.ServerVersion}}' and df -h /home | tail -1. Stop if Docker is unreachable or free space is below 3 GB.
5. Run: grep -nE '^[a-z-]+:' Makefile | cut -d: -f1,2 to list existing targets. The existing targets must be: doctor, env, db-up, db-down, db-reset, lock, api-setup, api-lint, api-format, api-typecheck, api-test, dev-api, migrate, migrate-down, web-setup, web-lint, web-format, web-typecheck, web-test, web-build, dev-web.

OBJECTIVE
Add the aggregate Makefile targets and the smoke script, then verify the whole foundation end to end. You may fix defects found in files from earlier parts, but only the minimum needed, and you must list every such fix in your report. Do not add features.

DELIVERABLES
1. Aggregate Makefile targets (tab indentation, keep .PHONY updated). Each simply runs the per-app targets:
   - setup: env, api-setup, web-setup (in that order)
   - lint: api-lint, web-lint
   - format: api-format, web-format
   - typecheck: api-typecheck, web-typecheck
   - test: api-test, web-test
   - build: web-build
   - check: lint, typecheck, test, build (run in this order, stop at the first failure)
   - smoke: bash scripts/smoke.sh
   Also add a help target (the default goal) that lists all targets with one-line descriptions using comments of the form "target: ## description".
2. scripts/smoke.sh (bash, executable, set -u, quote everything). With both dev servers running it checks, using curl -fsS --max-time 5: GET http://127.0.0.1:8000/api/health must return {"status":"ok"}; GET http://127.0.0.1:8000/api/health/ready must return status ready; GET http://127.0.0.1:5173/api/health (through the Vite proxy) must return {"status":"ok"}. Ports come from the environment variables API_PORT and WEB_PORT with defaults 8000 and 5173. Print PASS or FAIL for each check. Exit non-zero if any check fails.

VERIFY (run each in this order, record the real result; keep output short with tail)
1. NODE_ENV=production make setup
2. make doctor
3. make db-up, then make migrate
4. make check (record the number of backend and frontend tests; zero errors and zero warnings)
5. Start the API and the web server with the background pattern (make dev-api and make dev-web), wait until both answer, then run make smoke (all three checks must PASS) and: curl -i http://127.0.0.1:5173/api/health (200 through the proxy).
6. With both servers still running: docker compose stop db, then curl -i http://127.0.0.1:8000/api/health/ready (must be 503 with body {"status":"unavailable"} and no error details), then docker compose up -d --wait (db healthy again), then curl ready again (200).
7. Stop both servers. Confirm ports 8000 and 5173 are free (ss -ltn).
8. Reproducibility from a clean clone (run only if df -h /tmp shows more than 2 GB free):
     rm -rf /tmp/lifespace-fresh
     git clone --quiet --branch m0/foundation "$(pwd)" /tmp/lifespace-fresh
     cd /tmp/lifespace-fresh
     UV_LINK_MODE=copy NODE_ENV=production make setup 2>&1 | tail -n 15
     make lint typecheck build 2>&1 | tail -n 25
     cd - && rm -rf /tmp/lifespace-fresh
   Both setup and the checks must succeed in the clean clone. Remove the clone afterwards.
9. git status --short must be empty and no .env, node_modules, .venv, or dist may be tracked (git ls-files | grep -E '(^|/)(\.env|node_modules|\.venv|dist)(/|$)' must print nothing).

COMMIT
Small conventional commits, for example "chore: add aggregate make targets and smoke script" and, if needed, one commit per fix to an earlier file ("fix: <what>"). git status must be clean afterwards. Leave the database running.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Anything the next part must know.
Finish by telling the user: "Part 5 is finished. Start a new session for the next part."
```
