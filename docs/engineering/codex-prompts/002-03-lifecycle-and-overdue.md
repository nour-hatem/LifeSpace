# Task 002, Part 3 of 3: Lifecycle transitions, overdue, and M1 audit

**Status:** Ready. Milestone M1 (domain core) is split into 3 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and depends only on the repository, not on earlier conversation.
**Depends on:** Parts 1 and 2 of Task 002
**Branch:** `m1/domain-core`
**Binding decisions:** `docs/engineering/adr/0001-m1-domain-decisions.md` (provisional product defaults, owner may override)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/002-03-lifecycle-and-overdue.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 002 | M1 DOMAIN CORE | PART 3 OF 3 | Lifecycle transitions, overdue, and M1 audit

SESSION CONTEXT
You are the implementation agent for LifeSpace, a local single-user application. Task 002 builds the pure Python domain core (milestone M1) in 3 parts. Each part runs in a separate session and you have no memory of earlier parts. Everything you need is in this prompt and in the repository. A separate architect reviews your Git diff, so do exactly what this part asks and nothing else. Do not start work that belongs to another part.

CONTEXT BUDGET (this session has a limited context window)
- Read only the files this prompt names: AGENTS.md, docs/engineering/TECHNICAL_BLUEPRINT.md (once, in full), docs/engineering/adr/0001-m1-domain-decisions.md (binding), and the code files the prompt tells you to inspect. Do not read other documents under docs/.
- Never print lockfiles, .venv, or full logs. Pipe long command output through "tail -n 30".
- If the same command fails twice for the same reason, stop and report the exact error. Try at most two different fixes for one problem.
- Your training data may predate the pinned versions (Python 3.14, pytest 9.1, pytest-asyncio 1.4, hypothesis 6.170, ruff 0.17, mypy 2.4). When unsure of an API, read the installed package source under apps/api/.venv/lib/python3.14/site-packages instead of guessing.

SCOPE RULES (owner decisions, binding)
- Local single-user app. No authentication, accounts, user_id, ownership fields, or multi-tenancy.
- This milestone is the domain layer only: no HTTP, no database, no Alembic migration, no AI code, no frontend change, no new runtime dependency. The only new dependency in Task 002 is hypothesis (a dev dependency, added in Part 1).
- Domain purity (binding): modules under apps/api/src/lifespace/domain import only the Python standard library (dataclasses, enum, datetime, zoneinfo, collections.abc, typing, and other pure stdlib modules) and other lifespace.domain modules. Never import pydantic, fastapi, sqlalchemy, or any third-party package. No I/O, no logging, no randomness. Never read the clock or generate ids inside the domain: never call datetime.now, date.today, uuid.uuid4, or uuid.uuid7 in src. The current time (now), identifiers, and the user's ZoneInfo are always function parameters.
- No unnecessary abstractions. Write the simplest code that satisfies this part. Every public function and class has a short docstring that states the rule it implements (cite the ADR item number or BUSINESS_RULES section).
- Code, comments, and docstrings are written in English.

MACHINE FACTS (do not fight them, do not change them)
- Ubuntu 26.04, Python 3.14.4, uv 0.11.28, GNU Make 4.4.1. Python dependencies live only in apps/api/.venv created by uv. Every uv call must run with UV_PYTHON_DOWNLOADS=never (the Makefile exports it).
- Do not install, upgrade, or remove any global tool or package. No sudo. No pip install. No uv python install.
- The repository path contains a space ("/home/nour/AI Factory/LifeSpace"). Quote every path and prefer paths relative to the repository root.
- Docker is only needed for the existing integration tests. If the database container is not running and Docker is reachable, run make db-up. Domain tests never need a database. If Docker is unreachable, run only the unit tests with: cd apps/api && uv run pytest tests/unit -q.
- Disk space on /home can be low. If a command fails with ENOSPC, stop and report. Do not work around it.
- Existing project facts: backend code is in apps/api/src/lifespace (packages api and infrastructure, plus config.py and main.py). Tests are in apps/api/tests/unit and apps/api/tests/integration. Make targets: api-setup, api-lint (ruff, ruff format --check, lint-imports), api-format, api-typecheck (mypy strict), api-test (pytest, warnings are errors), check (everything including the web app). Ruff selects E, F, I, B, UP, SIM, BLE, RUF with line length 100. Run make api-format after writing code.

GIT RULES
- Work on branch m1/domain-core. If it does not exist, create it from main, but only when main already contains apps/api/src/lifespace/main.py. If main does not contain it, stop and tell the user to merge the M0 foundation branch into main first. Any other current branch: stop and report.
- Do not commit to main, push, merge, or rewrite history. Never modify files under docs/.
- Commit your work in small conventional commits and finish with a clean git status.
- If git status is dirty at the start and the changes do not belong to this part, stop and report. Never discard changes you did not make.
- Never create or commit .env, secrets, or credentials.

START CHECK (run first)
1. Branch must be m1/domain-core. git status --short must be empty.
2. Read AGENTS.md, then docs/engineering/TECHNICAL_BLUEPRINT.md, then docs/engineering/adr/0001-m1-domain-decisions.md.
3. Confirm earlier parts exist: apps/api/src/lifespace/domain/{errors,time,deadline,task}.py and apps/api/tests/unit/domain/{strategies.py,test_task.py}. If missing, stop and tell the user which part to run first.
4. Read domain/task.py, domain/errors.py, domain/time.py, and domain/deadline.py so you reuse their exact names, and apps/api/tests/unit/domain/strategies.py. Run make api-setup and make api-test (all must pass before you change anything).
5. If domain/lifecycle.py already exists, inspect it and continue from what is missing.

OBJECTIVE
Add the lifecycle transitions with status events, the overdue computation, and finish M1 with documentation and a full audit.

DELIVERABLES
1. domain/lifecycle.py containing:
   - ALLOWED_TRANSITIONS: a read-only mapping from TaskStatus to a frozenset of allowed next statuses, exactly: INBOX to {PLANNED, IN_PROGRESS, CANCELED}; PLANNED to {IN_PROGRESS, COMPLETED, CANCELED}; IN_PROGRESS to {PLANNED, COMPLETED, CANCELED}; COMPLETED to {PLANNED}; CANCELED to {PLANNED} (BUSINESS_RULES 4.2, ADR items 5 and 6). Use types.MappingProxyType or an equivalent immutable form.
   - StatusEvent: frozen dataclass with task_id (UUID), from_status, to_status (TaskStatus), occurred_at (aware datetime), reason (str or None), discarded_schedule (TimeInterval or None).
   - TransitionResult: frozen dataclass with task (Task) and event (StatusEvent).
   - transition_task(task: Task, to_status: TaskStatus, *, now: datetime, reason: str | None = None) -> TransitionResult. Rules:
     a. now must be aware and not before task.updated_at, otherwise DomainValidationError.
     b. A transition not listed in ALLOWED_TRANSITIONS, including a transition to the same status, raises InvalidTransitionError whose message names the current status, the requested status, and the allowed next statuses (BUSINESS_RULES 4.2).
     c. To COMPLETED: set completed_at to now. Keep deadline, scheduled, and estimate_minutes unchanged (ADR item 7).
     d. To CANCELED: set canceled_at to now and cancellation_reason to the stripped reason (None when empty or not given). Keep deadline, scheduled, and estimate unchanged (ADR item 7).
     e. From COMPLETED or CANCELED to PLANNED (reopen): clear completed_at, canceled_at, and cancellation_reason on the new task. If task.scheduled is present and its end is at or before now, set scheduled to None on the new task and store the old interval in event.discarded_schedule. If the scheduled interval ends after now, keep it and leave discarded_schedule None (ADR item 8).
     f. Every other allowed transition changes only status and updated_at.
     g. The new task has updated_at equal to now. The event has from_status, to_status, occurred_at equal to now, the stripped reason (or None), and discarded_schedule as above. The original task is never mutated.
   The reason argument is stored in the event for any transition. It is stored on the task only for cancellation.
2. domain/overdue.py (or inside lifecycle.py if you prefer one module) containing is_overdue(task: Task, now: datetime, tz: ZoneInfo) -> bool: true only when the task has a deadline, the status is not COMPLETED and not CANCELED, and is_deadline_passed(task.deadline, now, tz) is true (BUSINESS_RULES 4.7, ADR item 9). Overdue is never stored on the task and is never a status.
3. Tests in apps/api/tests/unit/domain/test_lifecycle.py and test_overdue.py (pytest and hypothesis, typed, warnings are errors):
   - A full matrix test over all 25 pairs of statuses (parametrize): allowed pairs succeed, every other pair raises InvalidTransitionError, and the message contains the allowed statuses. Inbox to Completed is explicitly rejected.
   - Completion: sets completed_at, keeps deadline, scheduled, and estimate, status becomes COMPLETED, the event matches. Cancellation: sets canceled_at, stores the stripped reason, empty reason becomes None, keeps schedule and deadline.
   - Reopen from COMPLETED and from CANCELED: status PLANNED, completed_at, canceled_at, and cancellation_reason cleared on the task, the original completed event timestamp is still in the event that was returned when the task was completed (build a two-step sequence and check both events). A past scheduled interval is dropped and reported in discarded_schedule, a future scheduled interval is kept, a scheduled interval that ends exactly at now is dropped (end is exclusive, ADR item 13).
   - Immutability: the input task is unchanged after every transition. naive now and now before updated_at are rejected.
   - Property (hypothesis): apply a random sequence of up to 12 requested target statuses starting from a valid task; each step either succeeds, producing a valid Task (all invariants hold) and an event whose from and to statuses are an allowed pair, or raises InvalidTransitionError and leaves the previous state usable. Completed and canceled counts never exceed what the events show. Use a stateful loop or hypothesis.stateful, your choice.
   - Overdue: false without a deadline; true for an In Progress task past its deadline (a task can be both In Progress and overdue); false for Completed and Canceled tasks even when the deadline has passed; Planned and Inbox tasks past deadline are overdue; boundary tests for a DateTimeDeadline (at the instant false, one microsecond later true) and for a DateDeadline in UTC and in Africa/Cairo around 2026-04-24 and 2026-10-30 (use the verified instants in ADR 0001 and the Part 1 tests); a task that was overdue and is then completed is no longer overdue; overdue is a pure function of its inputs (same inputs, same output).
4. Documentation: add a "Domain layer (M1)" section to apps/api/README.md (modules and public API names, the purity rules, how to run the domain tests, and a short table of the ADR 0001 decisions that matter to callers). In AGENTS.md change only the existing layer line so that it says the domain package now exists (keep the file at 120 lines or fewer). Do not modify anything under docs/.

VERIFY AND AUDIT (run each, record the real result; keep output short)
1. make api-format, make api-lint (zero errors, 3 import contracts kept), make api-typecheck (zero errors), make api-test (all pass, zero warnings; record the number of tests: domain unit tests, other unit tests, integration tests).
2. Run the domain tests three times in a row. No flakiness allowed.
3. make check (the full gate across both apps) must pass. If Docker is reachable, run make db-up first. Record the totals.
4. Purity: grep -rnE "^(import|from) " apps/api/src/lifespace/domain | grep -vE "(dataclasses|enum|datetime|zoneinfo|typing|collections|types|uuid|lifespace\.domain|__future__)" must print nothing. grep -rnE "(now\(|today\(|uuid4|uuid7)" apps/api/src/lifespace/domain must print nothing.
5. Prove the domain contract again: add "import sqlalchemy" to domain/task.py, run make api-lint, confirm it fails, run git checkout -- apps/api/src, confirm git status --short is empty (commit your work first).
6. git diff main --stat: the changed files must be limited to apps/api (src/lifespace/domain, tests, pyproject.toml, uv.lock, README.md) and AGENTS.md. Confirm git diff main --stat -- docs prints nothing, no web file changed, no migration added, and the runtime dependency list in apps/api/pyproject.toml is unchanged (only the dev dependency hypothesis was added in Part 1).
7. git status --short must be empty. git log --oneline main..HEAD.

COMMIT
Small conventional commits, for example "feat(domain): add lifecycle transitions with status events", "feat(domain): add overdue computation", "test(domain): add lifecycle and overdue tests", "docs: document the domain layer". git status must be clean afterwards.

FINAL REPORT FOR THE WHOLE TASK (replaces the short report for this part, maximum 50 lines): summary of what was built; the public API (module, function, and class names); the result of each audit item above with real command output summaries; test counts; deviations and why; open questions or risks; the output of git log --oneline main..HEAD.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Anything the next part must know (names of public functions and classes you created).
Finish by telling the user: "Part 3 is finished. Start a new session for the next part."
```
