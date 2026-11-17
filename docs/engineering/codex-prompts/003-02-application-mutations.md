# Task 003, Part 2 of 6: Application mutations: edit, delete, transitions, history

**Status:** Ready. Milestone M2 (persistence and task API) is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and depends only on the repository, not on earlier conversation.
**Depends on:** Part 1 of Task 003
**Branch:** `m2/persistence-task-api`
**Binding decisions:** `docs/engineering/adr/0002-m2-persistence-and-task-api.md` (provisional defaults, owner may override)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/003-02-application-mutations.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 003 | M2 PERSISTENCE AND TASK API | PART 2 OF 6 | Application mutations: edit, delete, transitions, history

SESSION CONTEXT
You are the implementation agent for LifeSpace, a local single-user application. Task 003 builds milestone M2 (the application layer, PostgreSQL persistence, and the task HTTP API) in 6 parts. Each part runs in a separate session and you have no memory of earlier parts. Everything you need is in this prompt and in the repository. A separate architect reviews your Git diff, so do exactly what this part asks and nothing else. Do not start work that belongs to another part.

CONTEXT BUDGET (this session has a limited context window)
- Read only the files this prompt names: AGENTS.md, docs/engineering/TECHNICAL_BLUEPRINT.md (once, in full), docs/engineering/adr/0001-m1-domain-decisions.md, docs/engineering/adr/0002-m2-persistence-and-task-api.md (binding), and the code files the prompt tells you to inspect. Do not read other documents under docs/.
- Never print lockfiles, .venv, node_modules, or full logs. Pipe long command output through "tail -n 30". Never run a server in the foreground: start it with setsid in the background, wait for health, and stop it afterwards (kill the process group and confirm the port is free).
- If the same command fails twice for the same reason, stop and report the exact error. Try at most two different fixes for one problem.
- Your training data may predate the pinned versions (Python 3.14, FastAPI 0.133, Starlette 1.10, Pydantic 2.13, SQLAlchemy 2.0.50, asyncpg 0.31, Alembic 1.18, pytest 9.1, pytest-asyncio 1.4, hypothesis 6.170, ruff 0.17, mypy 2.4). When unsure of an API, read the installed package source under apps/api/.venv/lib/python3.14/site-packages instead of guessing.

SCOPE RULES (owner decisions, binding)
- Local single-user app. No authentication, accounts, user_id, ownership fields, or multi-tenancy. Authentication is deferred and is NOT an approved requirement.
- No new runtime dependency in apps/api and no new dependency in apps/web unless this prompt says so. No Redis, queue, agent framework, CI, Dockerfile, or deployment configuration.
- Layers (import-linter enforces them): domain imports only the standard library. application imports only the standard library and lifespace.domain. infrastructure implements the application ports and never imports lifespace.api. api calls application and may import lifespace.domain value types (enums, Deadline types, TimeInterval) for mapping, but never infrastructure or SQLAlchemy. lifespace.main (and lifespace.openapi_export) are composition roots.
- Domain and application never read the clock and never generate ids: they receive a Clock and an IdGenerator. Never call datetime.now, date.today, uuid.uuid4, or uuid.uuid7 inside lifespace.domain or lifespace.application.
- Compare and subtract datetimes only through lifespace.domain.time.as_instant (ADR 0001 item 19).
- No unnecessary abstractions. Write the simplest code that satisfies this part. Every public function and class has a short docstring that cites the ADR item. Code, comments, and docstrings are in English.

MACHINE FACTS (do not fight them, do not change them)
- Ubuntu 26.04, Python 3.14.4, uv 0.11.28, Node 22.22.3, npm 10.9.8, GNU Make 4.4.1. Python dependencies live only in apps/api/.venv created by uv. Every uv call runs with UV_PYTHON_DOWNLOADS=never (the Makefile exports it). pnpm is not used.
- Do not install, upgrade, or remove any global tool or package. No sudo. No pip install, npm install -g, or uv python install.
- The repository path contains a space ("/home/nour/AI Factory/LifeSpace"). Quote every path and prefer relative paths.
- The login shell exports NODE_ENV=production. Run any ad hoc npm or npx command with env -u NODE_ENV.
- A host PostgreSQL service listens on 127.0.0.1:5432. Never use it. The project database is a Docker container published on 127.0.0.1:5433 (databases lifespace and lifespace_test).
- Docker Desktop must be running with the desktop-linux context. Do not start or stop Docker Desktop and do not change the Docker context. If the database container fails to start with the message "RWLayer of container ... is unexpectedly nil", run: docker rm -f lifespace-db-1 and then make db-up (the data volume is kept). If Docker is unreachable, stop and report it, except in parts that say domain and application tests need no database.
- Disk space on /home can be low. If a command fails with ENOSPC, stop and report. Do not work around it.
- Existing project facts: backend code is in apps/api/src/lifespace (packages domain, api, infrastructure, plus config.py and main.py). Make targets: api-setup, api-lint (ruff, ruff format --check, lint-imports), api-format, api-typecheck (mypy strict over src and tests), api-test (pytest, warnings are errors), migrate, migrate-down, db-up, check (everything including the web app). Ruff selects E, F, I, B, UP, SIM, BLE, RUF with line length 100 (note RUF036: write unions as "X | Unset | None", None last). Run make api-format after writing code. Tests use httpx.AsyncClient with ASGITransport (never the Starlette TestClient), run the app lifespan, and dispose every engine.

GIT RULES
- Work on branch m2/persistence-task-api. If it does not exist, create it from main, but only when main already contains apps/api/src/lifespace/domain/task.py. Any other current branch: stop and report.
- Do not commit to main, push, merge, or rewrite history. Never modify files under docs/.
- Commit your work in small conventional commits and finish with a clean git status.
- If git status is dirty at the start and the changes do not belong to this part, stop and report. Never discard changes you did not make.
- Never create or commit .env, secrets, or credentials.

START CHECK (run first)
1. Branch must be m2/persistence-task-api. git status --short must be empty.
2. Read AGENTS.md, docs/engineering/TECHNICAL_BLUEPRINT.md, docs/engineering/adr/0001-m1-domain-decisions.md, and docs/engineering/adr/0002-m2-persistence-and-task-api.md.
3. Confirm Part 1 exists: apps/api/src/lifespace/application/{errors,models,ports,tasks,settings}.py and apps/api/tests/unit/application/fakes.py. If missing, stop and tell the user to run Part 1 first.
4. Read application/errors.py, models.py, ports.py, tasks.py, and tests/unit/application/fakes.py so you reuse their exact names. Read domain/lifecycle.py and domain/task.py (edit_task, UNSET, transition_task, StatusEvent).
5. Run make api-setup and the unit tests (cd apps/api && uv run pytest tests/unit -q). All must pass before you change anything. This part needs no database.

OBJECTIVE
Add the mutating use cases to application/tasks.py: edit_task, delete_task, transition_task, and list_task_events, with full tests against the in-memory fakes. No database, no HTTP.

DELIVERABLES
1. application/tasks.py additions (same conventions as Part 1: explicit dependencies, one unit of work per call, translate_domain_errors around domain calls, commit only after a successful write):
   - edit_task(uow_factory, clock, task_id, expected_version, changes: TaskChanges) -> TaskView. Load the stored task (NotFoundError when missing or deleted), apply domain.edit_task(task, now=clock.now(), **only the changed fields) so UNSET fields are left alone, save with expected_version, commit, return the view. A TaskChanges in which every field is UNSET raises ValidationFailedError (message "no changes given", no field). A stale expected version raises StaleVersionError(expected_version, current_version).
   - delete_task(uow_factory, clock, task_id, expected_version) -> None: soft delete with the version check (ADR 0002 item 5). A missing or already deleted task raises NotFoundError.
   - transition_task(uow_factory, clock, ids, task_id, to_status, expected_version, reason=None) -> TaskView. Load the task, call domain.transition_task(task, to_status, now=clock.now(), reason=reason), save the new task with expected_version, then add_event(ids.new_id(), result.event), all in one unit of work, then commit (ADR 0002 item 6). A rejected transition raises TransitionRejectedError and writes nothing (no task change and no event).
   - list_task_events(uow_factory, task_id, *, limit, cursor=None) -> Page[StoredStatusEvent]: NotFoundError when the task is missing or deleted; limit between 1 and 200 (ValidationFailedError with field "limit" otherwise).
   Check order for every mutation: not found, then validation or domain rule, then version. Decide and document in the docstring whether a stale version wins over a domain rejection: the stale version check wins (the caller's picture of the task is out of date, so the domain rule result may be meaningless).
2. Tests in apps/api/tests/unit/application (reuse the fakes, extend them only if something is missing; typed, warnings are errors):
   - edit_task: fields change, version becomes 2, updated_at equals the clock, None clears and UNSET keeps (parametrize over all seven fields); editing the deadline never changes scheduled or estimate_minutes and the same for the other two (hypothesis property test over the three fields); an invalid edit (empty title, estimate 0) raises ValidationFailedError with the right field and leaves the stored task and version unchanged; a stale version raises StaleVersionError with expected and current versions and changes nothing; a missing and a deleted task raise NotFoundError; an all-UNSET TaskChanges raises ValidationFailedError.
   - delete_task: the task disappears from get_task and list_tasks, version check, deleting twice raises NotFoundError, stale version rejected, the status events stay in the store but list_task_events raises NotFoundError.
   - transition_task: every allowed first transition from Planned and Inbox works and produces exactly one stored event with the right from and to statuses and occurred_at equal to the clock; version increments by one; a rejected transition (Inbox to Completed, Completed to Completed) raises TransitionRejectedError with the allowed statuses in the message and leaves task, version, and events unchanged; cancel stores the stripped reason on the task and the event; reopen after complete restores Planned and clears completed_at; reopen discards a schedule that already ended and the event carries it in discarded_schedule (use the fake clock to move time); a stale version raises StaleVersionError and writes nothing; a task that is completed is no longer overdue in its TaskView even when the deadline has passed; the task and its event are committed together or not at all (simulate a failure inside add_event with a fake subclass that raises, and assert nothing was stored).
   - list_task_events: newest first, pagination across pages with no duplicates, limit validation, NotFoundError for a missing task.
   - Sequence property test (hypothesis): generate lists of up to 15 operations (create, edit title, edit estimate, start, complete, cancel, reopen, delete) against the fakes, each carrying the current version or deliberately a wrong one. Run them with asyncio.run inside a synchronous test. After every step assert: a successful mutation raised the version by exactly 1; a failed mutation changed nothing; the number of stored events equals the number of successful transitions; deleted tasks are invisible; every task still satisfies the domain invariants.

VERIFY (run each, record the real result)
1. make api-format, make api-lint (zero errors, 4 import contracts kept), make api-typecheck (zero errors), make api-test (all pass, zero warnings, record the count; if Docker is unreachable run only unit tests and say so).
2. Application tests three times in a row (cd apps/api && for i in 1 2 3; do uv run pytest tests/unit/application -q 2>&1 | tail -n 1; done). No flakiness.
3. Mutation sanity: temporarily remove the expected-version check in the fake repository save method, run the application tests, confirm at least one test fails, then git checkout the file.
4. Purity greps as in Part 1: no now(, today(, uuid4, uuid7 in lifespace/application, and only allowed imports.

COMMIT
Small conventional commits, for example "feat(application): add edit, delete, and transition use cases", "feat(application): add status history listing", "test(application): add mutation and sequence tests". git status must be clean afterwards.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first, at most 8 lines).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Public names the next part needs (modules, classes, functions you created).
Finish by telling the user: "Part 2 is finished. Start a new session for the next part."
```
