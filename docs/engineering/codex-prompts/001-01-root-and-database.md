# Task 001, Part 1 of 6: Root tooling and database

**Status:** Ready. The foundation task is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and does not depend on earlier conversation, only on the repository.
**Depends on:** none (first part)
**Branch:** `m0/foundation`
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/001-01-root-and-database.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 001 | M0 FOUNDATION | PART 1 OF 6 | Root tooling and database

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
1. git branch --show-current must print m0/foundation (if not, switch to it, or create it from main). git status --short must be empty.
2. Read docs/engineering/TECHNICAL_BLUEPRINT.md in full.
3. Run: df -h /home | tail -1 and docker info --format '{{.ServerVersion}}'. Stop and report if Docker is unreachable or free space is below 3 GB.
4. Expected state: the repository holds only README.md, .gitignore, and docs/. If other project files already exist, list them in your report and only create what this part names.

OBJECTIVE
Create the root tooling and the local PostgreSQL 18 database. No application code.

DELIVERABLES
1. .editorconfig: utf-8, LF, final newline, trim trailing whitespace, 4 spaces for Python, 2 spaces for json, yaml, ts, tsx, js, css, html, md, tabs for Makefile.
2. .nvmrc containing exactly: 22.22.3
3. .env.example with these variables and local-only values (these are not secrets):
   LIFESPACE_ENVIRONMENT=development
   LIFESPACE_DATABASE_URL=postgresql+asyncpg://lifespace:lifespace_dev_only@127.0.0.1:5433/lifespace
   LIFESPACE_TEST_DATABASE_URL=postgresql+asyncpg://lifespace:lifespace_dev_only@127.0.0.1:5433/lifespace_test
   LIFESPACE_LOG_LEVEL=INFO
   API_PROXY_TARGET=http://127.0.0.1:8000
   POSTGRES_USER=lifespace
   POSTGRES_PASSWORD=lifespace_dev_only
   POSTGRES_DB=lifespace
   POSTGRES_PORT=5433
   Add a one-line comment above each variable explaining it.
4. docker-compose.yml: top-level name lifespace. One service, db, image postgres:18, restart unless-stopped. Environment POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB taken from the environment with defaults lifespace, lifespace_dev_only, lifespace. Ports: "127.0.0.1:${POSTGRES_PORT:-5433}:5432" only. Named volume pgdata mounted at /var/lib/postgresql (the postgres:18 image requires this path, NOT /var/lib/postgresql/data). Mount ./infra/postgres/init at /docker-entrypoint-initdb.d read-only. Healthcheck: pg_isready -U ${POSTGRES_USER:-lifespace} -d ${POSTGRES_DB:-lifespace}, interval 5s, timeout 3s, retries 12.
5. infra/postgres/init/01-create-test-db.sql containing: CREATE DATABASE lifespace_test;
6. scripts/doctor.sh (bash, executable, starts with: set -u, then cd to the repository root using "$(dirname "${BASH_SOURCE[0]}")/..". Print one line per check as "OK name: detail", "WARN name: detail", or "FAIL name: detail". Exit 1 if any FAIL.)
   FAIL when: Node is not >=22.22.2 and <23 (compare with sort -V); npm is missing; uv is missing; "UV_PYTHON_DOWNLOADS=never uv python find 3.14" fails; the docker CLI is missing; "docker info" fails (message: start Docker Desktop and run: docker context use desktop-linux); free space on the filesystem of the repository is below 3 GB (print the free space in every case); port 5433 is listening and the process is not the project's db container (check with: docker ps --filter publish=5433 --format '{{.Names}}' and require a name starting with lifespace).
   WARN when: NODE_ENV is production (explain that apps/web/.npmrc and the npm scripts neutralize it); ports 8000 or 5173 are in use; something listens on 5432 (informational, the project never uses it).
7. Makefile, created now and extended by later parts. Start with: SHELL := /bin/bash, export UV_PYTHON_DOWNLOADS := never, API := apps/api, WEB := apps/web, and a .PHONY line you keep updated. Targets for this part:
   - doctor: bash scripts/doctor.sh
   - env: create .env from .env.example only if .env does not exist, then print which happened
   - db-up: docker compose up -d --wait
   - db-down: docker compose down (keeps data)
   - db-reset: ask "This deletes all local database data. Continue? [y/N]" with read, abort unless y or Y, then docker compose down -v and docker compose up -d --wait
   Use tab indentation. Quote paths. Do not add targets that belong to later parts.
8. .gitignore already ignores .env. Confirm with: git check-ignore -v .env, and confirm .env.example is NOT ignored (git check-ignore .env.example must print nothing).

VERIFY (run each, record the real result)
- make doctor (expect no FAIL; record the free space line).
- make env, then ls -l .env, then git status --short (the .env file must not appear).
- make db-up, then docker compose ps (db must be healthy and published on 127.0.0.1:5433 only).
- docker compose exec -T db psql -U lifespace -d lifespace -Atc "select datname from pg_database where datname like 'lifespace%' order by 1" (must print lifespace and lifespace_test).
- ss -ltn | grep ':5433' (must show 127.0.0.1:5433, not 0.0.0.0).
- echo y | make db-reset, then repeat the psql check (must still list both databases and be healthy).
- echo n | make db-reset must abort without deleting anything.
- Leave the database running at the end.

COMMIT
Small conventional commits, for example "chore: add editorconfig, nvmrc, and env template" and "chore: add postgres compose service, doctor script, and make db targets". git status must be clean afterwards (.env is ignored).

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Anything the next part must know.
Finish by telling the user: "Part 1 is finished. Start a new session for the next part."
```
