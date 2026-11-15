# Task 001, Part 2 of 6: Backend core (API without migrations)

**Status:** Ready. The foundation task is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and does not depend on earlier conversation, only on the repository.
**Depends on:** Part 1 (Makefile, .env.example, scripts/doctor.sh)
**Branch:** `m0/foundation`
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/001-02-backend-core.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 001 | M0 FOUNDATION | PART 2 OF 6 | Backend core (API without migrations)

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
2. Confirm Part 1 exists: Makefile, .env.example, docker-compose.yml, scripts/doctor.sh. If any is missing, stop and tell the user to run Part 1 first.
3. Read docs/engineering/TECHNICAL_BLUEPRINT.md in full.
4. Run make env (creates .env if missing). Run docker info --format '{{.ServerVersion}}' (Docker is needed only for the last check of this part).
5. If apps/api already exists, inspect it with git status and ls, and continue from what is missing. Do not redo finished work.

OBJECTIVE
Create the FastAPI backend project: settings, app factory, health endpoints, problem+json errors, logging, database helpers, quality tooling, unit tests, and the import-linter contracts. No Alembic and no integration tests yet (Part 3).

APPROVED VERSIONS (exact, final)
- apps/api/pyproject.toml: name lifespace-api, version 0.0.0, requires-python ">=3.14,<3.15", build backend hatchling with the src layout ([tool.hatch.build.targets.wheel] packages = ["src/lifespace"]).
- Runtime dependencies: fastapi==0.133.1, starlette>=1.3.1, uvicorn[standard]==0.52.4, pydantic==2.13.4, pydantic-settings==2.14.2, sqlalchemy[asyncio]==2.0.50, asyncpg==0.31.0, alembic==1.18.4.
- Dependency group dev: pytest==9.1.0, pytest-asyncio==1.4.0, httpx==0.28.1, ruff, mypy, import-linter (leave these three unpinned in pyproject, uv.lock fixes them; they are known to work at ruff 0.17.4, mypy 2.4.1, import-linter 2.16).
- Do not add any other dependency (no structlog, psycopg, pip-audit, python-multipart, redis, celery).

TOOL CONFIGURATION (in pyproject.toml)
- ruff: line-length 100, lint select = ["E", "F", "I", "B", "UP", "SIM", "BLE", "RUF"].
- mypy: strict = true, files = ["src", "tests"].
- pytest: asyncio_mode = "auto", testpaths = ["tests"], filterwarnings = ["error"]. If a third-party deprecation warning appears, add a narrowly scoped ignore (module and message) with a comment, and report it. Never ignore warnings broadly.
- import-linter: root_package = "lifespace", include_external_packages = true, with exactly two "forbidden" contracts: (1) source lifespace.api, forbidden lifespace.infrastructure and sqlalchemy; (2) source lifespace.infrastructure, forbidden lifespace.api.

FILES TO CREATE under apps/api/src/lifespace (every __init__.py has a one-paragraph docstring stating the layer's responsibility and what it must not import)
- __init__.py, config.py, main.py, api/__init__.py, api/health.py, api/errors.py, infrastructure/__init__.py, infrastructure/db.py, infrastructure/logging.py.
- config.py: pydantic-settings Settings with env_prefix "LIFESPACE_", fields environment (Literal development, test, production; default development), database_url (str, required), test_database_url (str or None), log_level (default "INFO"). Load the repository-root .env resolved from the file location (Path(__file__).resolve().parents[4] / ".env"), never from the current directory. Set extra="ignore" in the model config, otherwise the unprefixed variables in .env (POSTGRES_*, API_PROXY_TARGET) make validation fail. Never print or log the database password.
- infrastructure/db.py: create_engine(url) returning an AsyncEngine; a module-level SQLAlchemy MetaData named metadata with a naming_convention (ix, uq, ck, fk, pk) for constraints and indexes; and async check_database(engine) that runs "select 1" under a short timeout (3 seconds) and returns True or False. Catching Exception there is deliberate at a health boundary: add "# noqa: BLE001" with a reason. Log only the exception type, never the URL or password. No models and no tables.
- infrastructure/logging.py: configure_logging(level) using only the standard library logging, safe to call more than once. Never log request bodies or credentials.
- api/health.py: define the type alias ReadyCheck = Callable[[], Awaitable[bool]], a FastAPI dependency get_ready_check(request) that returns request.app.state.ready_check, and a router with GET /api/health (200 {"status": "ok"}, never touches the database) and GET /api/health/ready (200 {"status": "ready"} when the callable returns True, otherwise 503 {"status": "unavailable"}). The body never contains exception text or connection details. This module must not import infrastructure or sqlalchemy.
- api/errors.py: register_error_handlers(app) with handlers returning media_type application/problem+json and the members type (urn:lifespace:problem:<code>), title, status, detail, code. Request validation: 422, code validation_failed, a fixed generic detail that does not echo input values. Starlette HTTPException (import it from starlette.exceptions): 404 gives code not_found, other statuses give code failed. Unhandled Exception: 500, code failed, detail "Internal server error", log the exception with logging, and never put exception text in the body.
- main.py (the composition root, the only module that wires infrastructure into the app): create_app(settings: Settings | None = None, *, ready_check: ReadyCheck | None = None) -> FastAPI. It configures logging, creates the engine from settings only when no ready_check is injected, stores the ready_check on app.state, registers handlers and the health router, and disposes the engine in the lifespan shutdown (an engine left open breaks pytest with an unclosed socket warning). There is NO module-level app object.

MAKEFILE TARGETS TO ADD (tab indentation, keep .PHONY updated)
- lock: uv lock --project $(API)
- api-setup: uv sync --project $(API) --locked
- api-lint: ruff check, ruff format --check, and lint-imports, all run with uv run --project $(API) (set the working directory so ruff and lint-imports find the config: use "cd $(API) && uv run ...")
- api-format: ruff format
- api-typecheck: mypy
- api-test: pytest
- dev-api: from the repository root, uv run --project $(API) uvicorn --factory lifespace.main:create_app --reload --reload-dir $(API)/src --host 127.0.0.1 --port 8000

UNIT TESTS (apps/api/tests/unit, plus tests/conftest.py)
Use httpx.AsyncClient with httpx.ASGITransport. Do NOT use fastapi.testclient or starlette.testclient (deprecated with httpx). Build the transport as ASGITransport(app=app, raise_app_exceptions=False) so a 500 response is returned instead of raised. Run the app lifespan in every test (async with app.router.lifespan_context(app)). Put a small helper in conftest.py that yields a client for a given app. Tests construct Settings explicitly, for example Settings(_env_file=None, database_url="postgresql+asyncpg://u:p@127.0.0.1:9/x"), so they never read the real .env.
- GET /api/health returns 200 and exactly {"status": "ok"}.
- GET /api/health/ready returns 200 with an injected passing callable, and 503 with an injected failing callable. The exception text of a failing callable never appears in the body.
- Unknown route returns 404 with content type application/problem+json and members type, title, status, detail, code (code not_found).
- A route that fails validation returns 422 with code validation_failed. To test this, add a small test-only route to a test app instance inside the test, not to the production app.
- A test-only route that raises RuntimeError("secret internal detail") returns 500 with code failed, the secret text is absent from the body, and the secret text appears in the captured log (caplog).
- Settings: fails fast when database_url is missing (set the environment with monkeypatch and pass _env_file=None), and rejects an invalid environment value.
- check_database returns False for an unreachable URL (host 127.0.0.1, port 9) and the engine is disposed afterwards.
- metadata.naming_convention contains the five keys.

VERIFY (run each, record the real result)
1. make lock, then make api-setup.
2. make api-lint (zero errors), make api-typecheck (zero errors), make api-test (all pass, zero warnings; record the number of tests).
3. Commit your work now (see COMMIT), then prove each import-linter contract:
   a. In api/health.py add "import sqlalchemy", run make api-lint, confirm lint-imports fails, then run git checkout -- apps/api/src.
   b. In api/health.py add "from lifespace.infrastructure import db", confirm failure, then git checkout -- apps/api/src.
   c. In infrastructure/db.py add "from lifespace.api import health", confirm failure, then git checkout -- apps/api/src.
   After each revert, git status --short must be empty.
4. Start the API with the background pattern (make dev-api). Then: curl -i http://127.0.0.1:8000/api/health (200, exact body), curl -i http://127.0.0.1:8000/api/health/ready (200 if the database from Part 1 is running, otherwise 503; the body must be only the status object), curl -i http://127.0.0.1:8000/api/nope (404, application/problem+json). Stop the server and confirm port 8000 is free.

COMMIT
Small conventional commits, for example "chore(api): scaffold backend project and tooling", "feat(api): add settings, health endpoints, error handling, and database helpers", "test(api): add unit tests", "chore: add api make targets". uv.lock must be committed. git status must be clean afterwards.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Anything the next part must know.
Finish by telling the user: "Part 2 is finished. Start a new session for the next part."
```
