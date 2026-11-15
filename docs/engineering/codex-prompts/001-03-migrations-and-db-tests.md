# Task 001, Part 3 of 6: Alembic baseline and database integration tests

**Status:** Ready. The foundation task is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and does not depend on earlier conversation, only on the repository.
**Depends on:** Parts 1 and 2 (Docker database, backend core)
**Branch:** `m0/foundation`
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/001-03-migrations-and-db-tests.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 001 | M0 FOUNDATION | PART 3 OF 6 | Alembic baseline and database integration tests

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
2. Confirm earlier parts exist: Makefile, docker-compose.yml, apps/api/pyproject.toml, apps/api/uv.lock, apps/api/src/lifespace/infrastructure/db.py, apps/api/src/lifespace/config.py. If any is missing, stop and tell the user to run the missing part first.
3. Read docs/engineering/TECHNICAL_BLUEPRINT.md in full.
4. Run: make env, make api-setup, make db-up, then make api-test. All existing tests must pass before you change anything. If they do not, stop and report.
5. If apps/api/alembic.ini or apps/api/migrations already exist, inspect them and continue from what is missing.

OBJECTIVE
Add the Alembic async baseline migration, the make migrate target, and integration tests against the real PostgreSQL test database. No other changes.

DELIVERABLES
1. Alembic setup in apps/api. Run, from apps/api: uv run alembic init -t async migrations. Then:
   - alembic.ini: set script_location = %(here)s/migrations. Remove or blank the placeholder sqlalchemy.url line so no credentials or placeholder URL remain in the file.
   - migrations/env.py: use the async template. The database URL is config.get_main_option("sqlalchemy.url") when it is set and non-empty, otherwise Settings().database_url (import Settings from lifespace.config). target_metadata is the metadata object from lifespace.infrastructure.db. Use NullPool for the migration engine. Do not log or print the URL.
   - One revision created with: uv run alembic revision --rev-id 0001 -m baseline (run from apps/api). Its upgrade() and downgrade() are empty (pass) and the docstring says it is the empty baseline. The file must be named 0001_baseline.py.
2. Makefile: add target migrate: uv run --project $(API) alembic -c $(API)/alembic.ini upgrade head (it must work from the repository root). Keep .PHONY updated. Add also target migrate-down: same with "downgrade base" (development use).
3. Integration tests in apps/api/tests/integration (all use LIFESPACE_TEST_DATABASE_URL from Settings.test_database_url, never the development database):
   - A fixture or conftest check that fails (never skips) with the message "PostgreSQL is not reachable. Run: make db-up" when the test database cannot be reached, or when test_database_url is not set (message: "Run: make env").
   - check_database returns True against the test database.
   - check_database returns False when the password is wrong (build the URL by replacing the password; dispose the engine).
   - Migration test: upgrade to head, assert the alembic_version table holds exactly one row with 0001, downgrade to base, assert the table is empty. Always leave lifespace_test at base afterwards, even when the test fails (use try/finally).
   IMPORTANT: alembic's env.py calls asyncio.run(). Calling the alembic command API from inside a running event loop fails. Therefore write the migration test as a plain synchronous test function (def, not async def), call alembic.command.upgrade and alembic.command.downgrade with a Config whose sqlalchemy.url is set with set_main_option, and read alembic_version through a small helper that uses asyncio.run with a short-lived async engine that is always disposed. pytest runs with filterwarnings = error, so every engine must be disposed.

VERIFY (run each, record the real result)
1. make migrate, then: docker compose exec -T db psql -U lifespace -d lifespace -Atc "select version_num from alembic_version" (must print 0001).
2. make migrate again (must succeed and change nothing). Then make migrate-down, confirm the table is empty, then make migrate again.
3. make api-lint, make api-typecheck, and make api-test (all pass, zero warnings; record the number of unit and integration tests).
4. Run make db-down, then run only the integration tests (cd apps/api && uv run pytest tests/integration -q 2>&1 | tail -n 15). They must FAIL with the clear message about make db-up and must not skip. Then run make db-up again and confirm the integration tests pass.
5. Confirm git grep -n "lifespace_dev_only" -- apps/api/alembic.ini apps/api/migrations returns nothing (no credentials in tracked Alembic files).

COMMIT
Small conventional commits, for example "feat(api): add alembic async baseline migration", "chore: add migrate make targets", "test(api): add database integration tests". git status must be clean afterwards. Leave the database running.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Anything the next part must know.
Finish by telling the user: "Part 3 is finished. Start a new session for the next part."
```
