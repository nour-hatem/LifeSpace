# Task 002, Correction 1 of 1: compare datetimes by UTC instants

**Status:** Ready. Review findings for milestone M1 (domain core). One self-contained session, sized for a 200K token context.
**Depends on:** Task 002 Parts 1 to 3 (already on the branch)
**Branch:** `m1/domain-core`
**Binding decisions:** `docs/engineering/adr/0001-m1-domain-decisions.md` (item 19 is new)
**How to send:** open a new session, then paste the block below. Alternatively paste this single line: `Read the file docs/engineering/codex-prompts/002-04-fix-instant-comparisons.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 002 | M1 DOMAIN CORE | CORRECTION 1 | Compare and subtract datetimes by UTC instants

SESSION CONTEXT
You are the implementation agent for LifeSpace, a local single-user application. This is a focused correction after an architect review of milestone M1. You have no memory of earlier sessions. Everything you need is in this prompt and in the repository. Fix exactly what is listed and nothing else.

CONTEXT BUDGET (limited context window)
- Read only: AGENTS.md, docs/engineering/adr/0001-m1-domain-decisions.md (binding, item 19 is new), and the domain files named below. Do not read other documents under docs/.
- Never print lockfiles, .venv, or full logs. Pipe long output through "tail -n 30". If the same command fails twice for the same reason, stop and report the exact error.

SCOPE RULES
- Domain layer only (apps/api/src/lifespace/domain and apps/api/tests/unit/domain). No new dependency, no HTTP, no database, no frontend, no migration, no change under docs/.
- Domain purity stays binding: standard library only inside lifespace.domain, never read the clock, never generate ids, no logging, no I/O.
- Code, comments, and docstrings in English. Every changed public function keeps a docstring that cites the ADR item.

MACHINE FACTS
- Ubuntu 26.04, Python 3.14.4, uv 0.11.28, GNU Make. Do not install, upgrade, or remove any global tool or package. No sudo. uv runs with UV_PYTHON_DOWNLOADS=never (the Makefile exports it).
- The repository path contains a space ("/home/nour/AI Factory/LifeSpace"). Quote paths.
- Domain tests need no database. make api-test also runs the integration tests, which need Docker. If Docker is reachable run make db-up first, otherwise run only: cd apps/api && uv run pytest tests/unit -q (and say so in your report).
- Disk space can be low. If a command fails with ENOSPC, stop and report.
- Make targets: api-format, api-lint (ruff, ruff format --check, lint-imports with 3 contracts), api-typecheck (mypy strict), api-test, check. Ruff selects E, F, I, B, UP, SIM, BLE, RUF with line length 100. Run make api-format after writing code.

GIT RULES
- Stay on branch m1/domain-core. Do not commit to main, push, merge, or rewrite history. git status must be clean at the end.
- The architect committed two docs files on this branch (the ADR update and this prompt). git diff main --stat -- docs may list only docs/engineering/adr/0001-m1-domain-decisions.md and docs/engineering/codex-prompts/002-04-fix-instant-comparisons.md. No other file under docs/ may change.
- If git status is dirty at the start, stop and report. Never discard changes you did not make.

START CHECK (run first)
1. git branch --show-current must print m1/domain-core and git status --short must be empty.
2. Read AGENTS.md and docs/engineering/adr/0001-m1-domain-decisions.md.
3. Read apps/api/src/lifespace/domain/time.py, deadline.py, task.py, lifecycle.py, overdue.py, and apps/api/tests/unit/domain/strategies.py. Run make api-setup, then the domain tests (cd apps/api && uv run pytest tests/unit/domain -q). All 162 must pass before you change anything.

THE DEFECT (architect review, reproduced on this branch)
Python compares and subtracts two aware datetimes that share the SAME tzinfo object (for example two values in the same ZoneInfo("Africa/Cairo")) by their wall-clock fields and ignores the UTC offset and fold. That is wrong across a daylight saving change and inside an ambiguous hour. Reproduced with the current code:
1. TimeInterval(start=2026-04-23 23:00 Cairo, end=2026-04-24 02:00 Cairo).duration() returns 3 hours. The real duration is 2 hours (the clock jumps from 00:00 to 01:00 on 2026-04-24).
2. is_deadline_passed(DateTimeDeadline(at=23:30 on 2026-10-29 Cairo, fold=0, which is 20:30Z), now=23:10 on 2026-10-29 Cairo, fold=1, which is 21:10Z), cairo) returns False. It must return True, because now is 40 real minutes later than the deadline.
3. transition_task(task whose updated_at is that 23:30 fold=0 value, ..., now=that 23:10 fold=1 value) raises "now must not be before the task updated_at". It must be accepted, because now is 40 real minutes later.
The same class of defect exists wherever the domain uses <, <=, >, >=, or - on datetimes that a caller may express in the same zone: TimeInterval.duration, overlaps, contains, intersection; deadline.is_deadline_passed; task.Task.__post_init__ (updated_at before created_at) and edit_task (now before updated_at); lifecycle.transition_task (now before updated_at, and the discarded schedule test end <= now).
start_of_local_day is correct (the architect verified it for 580,740 zone and day pairs including zones with midnight daylight saving). Do not change it.

DELIVERABLES
1. domain/time.py: add a public function as_instant(value: datetime) -> datetime that returns value.astimezone(UTC) (it must reject a naive value with DomainValidationError, reuse ensure_aware with field "value"). Use it as the single way to compare or subtract datetimes in the domain (ADR item 19). Keep the stored start and end of a TimeInterval exactly as the caller gave them (do not convert the stored fields).
   - TimeInterval.duration() returns the UTC instant of end minus the UTC instant of start.
   - overlaps, contains, and intersection compare UTC instants. intersection returns a TimeInterval built from the UTC instants of the shared bounds (document that the result is expressed in UTC).
   - touches and the ordering and equality methods already use instants. Keep them, and reuse as_instant where it removes duplication.
2. domain/deadline.py: is_deadline_passed compares as_instant(now) with as_instant(deadline.at) for a DateTimeDeadline, and as_instant(now) with as_instant(start_of_local_day(day + 1 day, tz)) for a DateDeadline.
3. domain/task.py: the updated_at versus created_at invariant and the now versus updated_at check in edit_task compare instants.
4. domain/lifecycle.py: the now versus updated_at check and the schedule test (scheduled.end at or before now) compare instants.
5. Search the whole domain package for any remaining raw <, <=, >, >=, or - between datetimes (grep -nE "( < | <= | > | >= | - )" on the files above and inspect each hit). Every datetime comparison or subtraction must go through as_instant. Comparisons between plain numbers, dates, or timedeltas are fine.
6. Tests (new file apps/api/tests/unit/domain/test_instants.py, typed, pytest and hypothesis, warnings are errors). Use ZoneInfo("Africa/Cairo") and the verified facts: spring forward at 2026-04-23T22:00:00Z (local 00:00 on 2026-04-24 does not exist), fall back at 2026-10-29T21:00:00Z (local 24:00+03:00 becomes 23:00+02:00, so 23:00 to 24:00 on 2026-10-29 occurs twice). Build ambiguous values with datetime(2026, 10, 29, 23, 30, tzinfo=cairo, fold=0) (20:30Z) and datetime(2026, 10, 29, 23, 10, tzinfo=cairo, fold=1) (21:10Z).
   - duration across the spring forward: 2026-04-23 23:00 to 2026-04-24 02:00 in Cairo is 2 hours. Duration across the fall back: 2026-10-29 22:00 to 2026-10-30 01:00 in Cairo is 4 hours. Duration of an interval entirely inside the ambiguous hour: start 23:30 fold 0, end 23:10 fold 1, is 40 minutes (and the interval is accepted).
   - overlaps, contains (start inclusive, end exclusive), and intersection with same-zone ambiguous-hour values, including a case where the wall-clock order and the real order disagree.
   - is_deadline_passed in the ambiguous hour: the 20:30Z deadline is passed at 23:10 fold 1 and not passed at 23:10 fold 0 (20:10Z).
   - is_overdue: the same two cases through a Planned task.
   - transition_task: accepted with updated_at at 23:30 fold 0 and now at 23:10 fold 1; rejected with now at 23:10 fold 0.
   - edit_task: the same accept and reject pair.
   - Task construction: created_at at 23:30 fold 0 and updated_at at 23:10 fold 1 is accepted; the reverse is rejected.
   - Reopen schedule rule: a scheduled interval that ends at 23:10 fold 1 (21:10Z) with now at 23:30 fold 0 (20:30Z) is KEPT, and with now at 23:30 fold 1 (21:30Z) it is dropped and reported in discarded_schedule.
   - Property tests (hypothesis): draw a zone from the six test zones (UTC, Africa/Cairo, America/New_York, Europe/London, Asia/Kolkata, Pacific/Auckland) and draw UTC instants between 2000 and 2100, convert every instant with the SAME zone object (value.astimezone(zone), so they share one tzinfo), and assert that duration, overlaps, contains, intersection bounds, is_deadline_passed, and is_overdue give exactly the answers computed from the UTC values. Add the needed strategies to tests/unit/domain/strategies.py (for example same_zone_instants and same_zone_intervals). Include times near the Cairo and New York daylight saving transitions by also drawing from a list of instants within a few hours of the 2026 transitions of Cairo (2026-04-23T22:00Z and 2026-10-29T21:00Z) and New York (2026-03-08T07:00Z and 2026-11-01T06:00Z).
   - Keep every existing test passing unchanged. Do not weaken or delete an existing assertion.

VERIFY (run each and record the real result)
1. make api-format, make api-lint (zero errors, 3 import contracts kept), make api-typecheck (zero errors).
2. make api-test (all pass, zero warnings; record the number of tests). If Docker is unreachable run only the unit tests and say so.
3. Run the domain tests three times in a row: cd apps/api && for i in 1 2 3; do uv run pytest tests/unit/domain -q 2>&1 | tail -n 1; done. No flakiness.
4. Prove the new tests catch the defect: temporarily restore the old duration (return self.end - self.start), run the new tests, confirm at least one fails, then git checkout the file. git status must show only your intended changes.
5. Purity: grep -rnE "^(import|from) " apps/api/src/lifespace/domain | grep -vE "(dataclasses|enum|datetime|zoneinfo|typing|collections|types|uuid|lifespace\.domain|__future__)" prints nothing. grep -rnE "(now\(|today\(|uuid4|uuid7)" apps/api/src/lifespace/domain prints nothing.
6. git diff main --stat: apps/api changes only in src/lifespace/domain and tests/unit/domain (plus AGENTS.md or apps/api/README.md only if you document as_instant there in one line), and docs changes limited to the two architect files named in GIT RULES.

COMMIT
Small conventional commits, for example "fix(domain): compare and subtract datetimes by UTC instants" and "test(domain): add same-zone and ambiguous-hour regression tests". git status must be clean afterwards.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first, the last 4 lines).
- Each verification command and its real result (pass or fail, test counts).
- Which raw comparisons or subtractions you found and changed (file and function).
- Deviations from this prompt and why. The exact error text for any blocker.
Finish by telling the user: "Correction 1 is finished."
```
