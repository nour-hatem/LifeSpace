# Task 002, Part 1 of 3: Domain foundation and time rules

**Status:** Ready. Milestone M1 (domain core) is split into 3 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and depends only on the repository, not on earlier conversation.
**Depends on:** M0 merged into main
**Branch:** `m1/domain-core`
**Binding decisions:** `docs/engineering/adr/0001-m1-domain-decisions.md` (provisional product defaults, owner may override)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/002-01-domain-time-rules.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 002 | M1 DOMAIN CORE | PART 1 OF 3 | Domain foundation and time rules

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
1. Branch handling as described in GIT RULES. git status --short must be empty.
2. Read AGENTS.md, then docs/engineering/TECHNICAL_BLUEPRINT.md, then docs/engineering/adr/0001-m1-domain-decisions.md.
3. Run: make api-setup, then make db-up (if Docker is reachable), then make api-test. All existing tests must pass (13 tests) before you change anything. Look at the layout: ls apps/api/tests apps/api/tests/unit (follow the existing convention for __init__.py files) and read apps/api/tests/conftest.py and apps/api/pyproject.toml.
4. If apps/api/src/lifespace/domain already exists, inspect it and continue from what is missing.

OBJECTIVE
Create the domain package foundation: typed errors, the TimeInterval value object, local-day helpers, the deadline value types with the overdue comparison rule, the architecture contract that keeps the domain pure, and property tests. No Task model yet (Part 2).

DELIVERABLES
1. Dependency: from apps/api run: uv add --dev "hypothesis==6.170.15" (with UV_PYTHON_DOWNLOADS=never). Only pyproject.toml and uv.lock may change. Then make api-setup must still pass with --locked.
2. apps/api/tests/conftest.py: register and load a hypothesis profile named lifespace (max_examples 200, deadline None, suppress the too_slow health check). Keep the existing helpers in that file unchanged.
3. The root .gitignore must contain a line for .hypothesis/ (already added by the architect; verify with git check-ignore -v apps/api/.hypothesis). Do not edit .gitignore if it is already ignored.
4. apps/api/src/lifespace/domain/__init__.py: a one-paragraph docstring (the domain holds pure business rules, imports only the standard library, never reads the clock).
5. domain/errors.py:
   - DomainError(Exception) with attributes code (str) and message (str).
   - DomainValidationError(DomainError): code "validation_failed", optional field name attribute.
   - InvalidTransitionError(DomainError): code "invalid_transition" (used by Part 3, define it now with attributes from_status and to_status typed as str).
6. domain/time.py:
   - ensure_aware(value: datetime, *, field: str) -> datetime. Raises DomainValidationError for a naive datetime. Returns the value unchanged otherwise.
   - local_date(instant: datetime, tz: ZoneInfo) -> date. The calendar date of the instant in the zone.
   - start_of_local_day(day: date, tz: ZoneInfo) -> datetime. The first instant whose local date is day, returned as an aware datetime in tz. Compute it as datetime.combine(day, time.min, tzinfo=tz), then normalize with .astimezone(UTC).astimezone(tz). This handles a missing local midnight (the first instant is later that morning) and an ambiguous midnight (the earlier occurrence, fold 0). Document the limitation from ADR item 18.
   - TimeInterval: frozen, slotted dataclass with start and end (aware datetimes). It validates in __post_init__: both aware, and end strictly after start, otherwise DomainValidationError. Methods: duration() -> timedelta; overlaps(other) -> bool using exactly start < other.end and other.start < end; touches(other) -> bool (adjacent: end == other.start or other.end == start); contains(instant) -> bool (start <= instant < end); intersection(other) -> TimeInterval | None (None when they do not overlap, including when only adjacent).
7. domain/deadline.py:
   - DateDeadline: frozen dataclass with day (a date). DateTimeDeadline: frozen dataclass with at (an aware datetime, validated). Deadline = DateDeadline | DateTimeDeadline (a type alias).
   - is_deadline_passed(deadline, now, tz) -> bool. For a DateTimeDeadline: now > at (ADR item 3). For a DateDeadline: now >= start_of_local_day(day + 1 day, tz) (ADR item 2). now must be aware, otherwise DomainValidationError. State both rules in the docstring.
8. import-linter: add a third contract to apps/api/pyproject.toml, type "forbidden", name "domain must stay pure", source lifespace.domain, forbidden modules: fastapi, starlette, sqlalchemy, asyncpg, alembic, pydantic, pydantic_settings, httpx, uvicorn, lifespace.api, lifespace.infrastructure, lifespace.config.
9. Tests in apps/api/tests/unit/domain (create the folder following the existing convention). Use pytest and hypothesis. Zones for tests: UTC, Africa/Cairo, America/New_York, Europe/London, Asia/Kolkata, Pacific/Auckland. Datetime and date ranges for generated values: 2000-01-01 to 2100-12-31.
   - TimeInterval: rejects naive datetimes, rejects end equal to start, rejects end before start. Property: overlaps is symmetric; an interval overlaps itself; adjacent intervals (a.end == b.start) do not overlap and touch; overlap equals a brute-force check (a.start < b.end and b.start < a.end); intersection is None exactly when they do not overlap, and otherwise lies inside both intervals; contains is start-inclusive and end-exclusive; duration equals end minus start; equality and ordering use the instant, so the same interval written in two different offsets is equal.
   - start_of_local_day: property for every zone and date: local_date(result, tz) == day, and one microsecond earlier (compute in UTC: (result.astimezone(UTC) - timedelta(microseconds=1)).astimezone(tz)) has a local date strictly before day. Example tests for the verified Africa/Cairo facts in ADR 0001: start_of_local_day(date(2026, 4, 24), cairo) equals 2026-04-23T22:00:00Z (01:00+03:00), start_of_local_day(date(2026, 4, 25), cairo) equals 2026-04-24T21:00:00Z, and start_of_local_day(date(2026, 10, 30), cairo) equals 2026-10-29T22:00:00Z.
   - is_deadline_passed: exact boundary tests for a DateTimeDeadline (at the instant: not passed; one microsecond later: passed). Exact boundary tests for a DateDeadline in UTC and in Cairo, including the spring-forward gap (deadline date 2026-04-23: the instant 2026-04-23T22:00:00Z is passed and 2026-04-23T21:59:59.999999Z is not) and the fall-back (deadline date 2026-10-29: the instant 2026-10-29T22:00:00Z is passed and 2026-10-29T21:59:59.999999Z is not). Property: monotonic, if passed at some instant it is passed at every later instant; a DateDeadline is never passed before the start of its own local day plus 24 hours of calendar days (use: not passed at start_of_local_day(day, tz)); naive now is rejected.
   - ensure_aware and DomainError attributes (code values).
   Tests are typed (mypy strict covers tests) and run with filterwarnings = error.

VERIFY (run each, record the real result)
1. make api-format, then make api-lint (zero errors; lint-imports must show 3 contracts kept), make api-typecheck (zero errors), make api-test (all pass, zero warnings; record the number of tests).
2. Prove the new contract. Commit first (see COMMIT). Then add "import pydantic" at the top of domain/time.py, run make api-lint, confirm lint-imports fails on "domain must stay pure", then run git checkout -- apps/api/src. git status --short must be empty afterwards.
3. Run the new property tests three times in a row (cd apps/api && for i in 1 2 3; do uv run pytest tests/unit/domain -q 2>&1 | tail -n 2; done). They must pass every time with no flakiness.
4. git status --short must not list .hypothesis.

COMMIT
Small conventional commits, for example "chore(api): add hypothesis dev dependency and test profile", "feat(domain): add errors, time interval, local day helpers, and deadline rules", "chore(api): add domain purity import contract", "test(domain): add time and deadline tests". uv.lock must be committed. git status must be clean afterwards.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Anything the next part must know (names of public functions and classes you created).
Finish by telling the user: "Part 1 is finished. Start a new session for the next part."
```
