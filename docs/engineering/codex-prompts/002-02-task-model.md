# Task 002, Part 2 of 3: Task model, creation, editing, and validation

**Status:** Ready. Milestone M1 (domain core) is split into 3 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and depends only on the repository, not on earlier conversation.
**Depends on:** Part 1 of Task 002
**Branch:** `m1/domain-core`
**Binding decisions:** `docs/engineering/adr/0001-m1-domain-decisions.md` (provisional product defaults, owner may override)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/002-02-task-model.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 002 | M1 DOMAIN CORE | PART 2 OF 3 | Task model, creation, editing, and validation

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
3. Confirm Part 1 exists: apps/api/src/lifespace/domain/{errors,time,deadline}.py and apps/api/tests/unit/domain. If missing, stop and tell the user to run Part 1 first.
4. Read apps/api/src/lifespace/domain/errors.py, time.py, and deadline.py so you reuse their exact names. Run make api-setup and make api-test (all must pass before you change anything).
5. If apps/api/src/lifespace/domain/task.py already exists, inspect it and continue from what is missing.

OBJECTIVE
Create the Task model with enums, creation, editing, and validation. No lifecycle transitions yet (Part 3) and no overdue function yet (Part 3).

DELIVERABLES
1. domain/task.py containing:
   - Enums (all StrEnum): TaskStatus (INBOX "inbox", PLANNED "planned", IN_PROGRESS "in_progress", COMPLETED "completed", CANCELED "canceled"); Priority (CRITICAL "critical", HIGH "high", MEDIUM "medium", LOW "low") with a rank property (critical 1, high 2, medium 3, low 4; lower is more important); Category (WORK "work", EDUCATION "education", LEARNING "learning", PERSONAL "personal", PROJECTS "projects"); TaskSource (MANUAL "manual", AI "ai").
   - Task: frozen, slotted dataclass with fields: id (UUID), title (str), status (TaskStatus), source (TaskSource), created_at (aware datetime), updated_at (aware datetime), description (str or None), category (Category or None), priority (Priority or None), estimate_minutes (int or None), deadline (Deadline or None), scheduled (TimeInterval or None), completed_at (datetime or None), canceled_at (datetime or None), cancellation_reason (str or None). Give optional fields default None.
   - Task.__post_init__ validates every invariant and raises DomainValidationError with the field name: title is non-empty after stripping and equals its own stripped form; created_at, updated_at, completed_at, and canceled_at are aware when present; updated_at is not before created_at; estimate_minutes is an int (not a bool) greater than zero when present; completed_at is present if and only if status is COMPLETED; canceled_at is present if and only if status is CANCELED; cancellation_reason is only allowed when status is CANCELED and is non-empty when present.
   - UNSET: a module-level sentinel (a single instance of a small private class, with a typed alias so mypy strict accepts parameters such as "str | None | Unset") that means "leave this field unchanged", so that None can mean "clear this field".
   - create_task(*, task_id: UUID, title: str, now: datetime, source: TaskSource = TaskSource.MANUAL, status: TaskStatus = TaskStatus.PLANNED, description=None, category=None, priority=None, estimate_minutes=None, deadline=None, scheduled=None) -> Task. status must be INBOX or PLANNED, otherwise DomainValidationError (ADR item 4). The title is stripped before validation (ADR item 11). created_at and updated_at are both now. Strip a description and store None when it becomes empty.
   - edit_task(task: Task, *, now: datetime, title=UNSET, description=UNSET, category=UNSET, priority=UNSET, estimate_minutes=UNSET, deadline=UNSET, scheduled=UNSET) -> Task. It returns a new Task (the original is never mutated), sets updated_at to now, keeps id, status, source, created_at, and the lifecycle timestamps unchanged, strips the title when given, and re-validates. Only the fields that were passed change (ADR items 12 and 16). It has no parameter for status, id, or created_at. now must be aware and not before task.updated_at, otherwise DomainValidationError.
   Type every parameter precisely (mypy strict). Keep the module focused. Do not add actual duration, tags, notes, project, dependencies, recurrence, ownership, or deletion.
2. apps/api/tests/unit/domain/strategies.py: shared hypothesis strategies used by this and later tests: aware datetimes (2000 to 2100, zones UTC, Africa/Cairo, America/New_York, Europe/London, Asia/Kolkata, Pacific/Auckland), time intervals, deadlines (both kinds), titles (printable text with at least one non-space character, include Arabic text samples), and a valid_tasks strategy that builds Tasks through create_task in Planned or Inbox status with random optional fields.
3. Tests in apps/api/tests/unit/domain/test_task.py (use pytest and hypothesis, typed, warnings are errors):
   - create_task: minimal task, full task, default status is PLANNED, INBOX accepted, COMPLETED, IN_PROGRESS, and CANCELED rejected at creation, created_at equals updated_at equals now, source defaults to MANUAL.
   - Title rules: empty and whitespace-only rejected; edges trimmed; internal spacing, case, and Arabic text preserved exactly (for example the title "  اكتب تقرير المشروع  " becomes "اكتب تقرير المشروع").
   - Estimate rules: 0, negative, and True rejected; a missing estimate stays None and is never replaced by a default (ADR item 10).
   - Datetime rules: naive created/updated/deadline datetime/scheduled interval rejected, naive now rejected.
   - Invariants: constructing a Task directly with status COMPLETED and no completed_at fails, with CANCELED and no canceled_at fails, with a cancellation_reason while not CANCELED fails, with an empty cancellation_reason fails, with updated_at before created_at fails.
   - edit_task: returns a new object and leaves the original unchanged; UNSET leaves a field unchanged; None clears an optional field; changing the deadline leaves scheduled and estimate_minutes untouched; changing scheduled leaves deadline and estimate_minutes untouched; changing estimate_minutes leaves deadline and scheduled untouched (property tests with hypothesis over all combinations); updated_at becomes now; id, status, source, created_at never change; invalid edits (empty title, bad estimate) raise DomainValidationError and do not return a partial result; now earlier than updated_at is rejected.
   - A deadline and a scheduled interval can coexist and differ (the BUSINESS_RULES 5.1 example: deadline Thursday 23:59, scheduled Tuesday 17:00 to 19:00).

VERIFY (run each, record the real result)
1. make api-format, make api-lint (zero errors, 3 import contracts kept), make api-typecheck (zero errors), make api-test (all pass, zero warnings; record the number of tests).
2. Run the domain tests three times (cd apps/api && for i in 1 2 3; do uv run pytest tests/unit/domain -q 2>&1 | tail -n 2; done). No flakiness allowed.
3. Confirm purity: grep -rnE "^(import|from) " apps/api/src/lifespace/domain | grep -vE "(dataclasses|enum|datetime|zoneinfo|typing|collections|uuid|lifespace\.domain|__future__)" must print nothing.
4. Confirm no clock or id generation in the domain: grep -rnE "(now\(|today\(|uuid4|uuid7)" apps/api/src/lifespace/domain must print nothing (docstrings must not contain these call patterns either; reword them).

COMMIT
Small conventional commits, for example "feat(domain): add task model with creation, editing, and validation" and "test(domain): add task tests and shared strategies". git status must be clean afterwards.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Anything the next part must know (names of public functions and classes you created).
Finish by telling the user: "Part 2 is finished. Start a new session for the next part."
```
