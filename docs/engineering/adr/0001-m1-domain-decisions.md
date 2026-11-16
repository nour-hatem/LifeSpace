# ADR 0001: M1 domain decisions

**Status:** Provisional. The architect's defaults, adopted on 2026-11-16 because the owner asked to proceed to M1 without answering product decisions P1 to P4 (blueprint section 20). The domain is pure Python, so changing any decision later is cheap. The owner may override any item before or after M1 runs.
**Sources:** BUSINESS_RULES sections 3 to 6, PRD FR-011 to FR-018 and FR-030, blueprint sections 4, 7, and 12.

## Scope of M1

In scope: the Task model, creation and editing rules, validation, the lifecycle and its transition history events, overdue computation, the deadline semantics, and time interval rules. Pure Python, no I/O.

Out of scope, and not to be started in M1:
- Fixed commitments as an entity (M5), recurrence, projects, dependencies, tags, notes, and actual duration (FR-019 is P1).
- Task deletion. BUSINESS_RULES 4.5 leaves retention and recovery open. The default for M2 is soft delete.
- Ownership, users, accounts, persistence, HTTP, and AI.

## Decisions

| # | Decision | Rationale |
|---|---|---|
| 1 | P1 default: a fixed commitment will be a separate entity (built in M5). M1 contains only the shared `TimeInterval` | BUSINESS_RULES 5.4 allows either and asks for a documented decision |
| 2 | P2 default: a date-only deadline D is a deadline at the end of the local day D. The task becomes overdue at the first instant of local day D+1 (`now >= start_of_local_day(D + 1)`) | BUSINESS_RULES 3.5.4 requires a documented comparison rule |
| 3 | An exact date-time deadline is overdue strictly after the instant (`now > deadline`). At the exact deadline instant the task is still on time | Matches the wording "deadline has passed" |
| 4 | P3 default: a task created after review starts as Planned. Inbox is only for unreviewed capture. `create_task` accepts only Inbox or Planned | BUSINESS_RULES 4.2 forbids Inbox to Completed, so a directly completable task must be Planned |
| 5 | P4 default: reopening is supported. Completed to Planned and Canceled to Planned are allowed | BUSINESS_RULES 4.2 and 4.6 |
| 6 | Transitions follow BUSINESS_RULES 4.2 exactly. A transition to the same status is rejected. Every rejection explains the allowed next statuses | BUSINESS_RULES 4.2 |
| 7 | Completing or canceling keeps the deadline, the scheduled interval, and the estimate on the task. It records `completed_at` or `canceled_at` and returns a status event | BUSINESS_RULES 4.3 and 4.4 |
| 8 | Reopening clears `completed_at`, `canceled_at`, and the cancellation reason on the task snapshot, but the earlier status events keep them. If the scheduled interval has already ended (`end <= now`), the reopened task drops it and the event records it as `discarded_schedule`. A future interval is kept | BUSINESS_RULES 4.6 (do not erase timestamps, do not restore an invalid schedule) |
| 9 | Overdue is computed, never stored: deadline present, deadline passed, status not Completed or Canceled. In Progress tasks can be overdue | BUSINESS_RULES 4.7 |
| 10 | Estimated duration is a whole number of minutes and must be greater than zero. A missing estimate stays `None` | BUSINESS_RULES 3.4. One unit everywhere |
| 11 | A title is trimmed at both ends and must not be empty afterwards. Internal wording, spacing, case, and non-Latin text are preserved | BUSINESS_RULES 3.3 |
| 12 | Deadline and scheduled interval are independent. Editing one never changes the other, or the estimate | BUSINESS_RULES 5.1 and 5.6 |
| 13 | Intervals are half-open: start inclusive, end exclusive. Overlap is `a.start < b.end and b.start < a.end`. Adjacent intervals do not overlap | BUSINESS_RULES 5.5 |
| 14 | All datetimes in the domain are timezone-aware. Naive values are rejected. The domain never reads the clock: `now`, ids, and the user's `ZoneInfo` are passed in | Determinism and testability |
| 15 | Priority is optional (Critical, High, Medium, Low). Category is optional (Work, Education, Learning, Personal, Projects). Source is Manual or AI | PRD FR-016 and FR-017, BUSINESS_RULES 6.1 |
| 16 | Edits are not restricted by status. The specifications do not forbid editing completed or canceled tasks. Status changes only through `transition_task` | No invented restriction |
| 17 | Domain errors are typed: `DomainValidationError` (code `validation_failed`) and `InvalidTransitionError` (code `invalid_transition`) | The API layer maps them to problem+json in M2 |
| 18 | Limitation: a calendar day that does not exist in a time zone (for example Pacific/Apia on 2011-12-30) is out of scope. Property tests use zones where every day exists | Not relevant to the owner's use |

## Verified time zone facts (Africa/Cairo, 2026, from the system tz database)
- Spring forward: 2026-04-23T22:00:00Z. Local 00:00 on 2026-04-24 does not exist, so the first instant of that local day is 01:00+03:00 (2026-04-23T22:00:00Z).
- Fall back: 2026-10-29T21:00:00Z, when 24:00+03:00 becomes 23:00+02:00. The hour 23:00 to 24:00 on 2026-10-29 occurs twice. Local midnight of 2026-10-30 is 2026-10-29T22:00:00Z.
