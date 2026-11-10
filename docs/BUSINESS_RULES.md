# LifeSpace --- Business Rules

**Document version:** 1.0\
**Status:** Draft for product review\
**Product:** LifeSpace\
**Repository:** `lifespace`\
**Purpose:** Define the deterministic business rules governing tasks,
time, scheduling, projects, AI permissions, and historical records.

**Related documents:** - `PRD.md` - `UI_UX_SPEC.md`

------------------------------------------------------------------------

# 1. Purpose and Authority

This document defines how LifeSpace must behave regardless of the
frontend, backend framework, database, or AI provider selected later.

These rules are product behavior requirements. They are not
implementation instructions.

The application must enforce critical business rules independently of
LLM output. The AI may interpret user intent and propose actions, but
the application remains responsible for validating and applying them.

When a rule is ambiguous or a product decision is unresolved, the system
must not silently invent behavior. It should use a safe default,
preserve user data, and request clarification where necessary.

## 1.1 Rule Priorities

-   **MUST:** Mandatory behavior.
-   **SHOULD:** Expected behavior unless a justified exception exists.
-   **MAY:** Optional behavior.
-   **P0:** Required for MVP.
-   **P1:** Later release.
-   **P2:** Future enhancement.

------------------------------------------------------------------------

# 2. Core Domain Definitions

## 2.1 Task

A task is a unit of work or responsibility that can be captured,
organized, scheduled, started, completed, canceled, or deleted.

A task may exist without a deadline or scheduled time.

## 2.2 Fixed Commitment

A fixed commitment occupies a specific time interval and must be treated
as unavailable time for other scheduled work.

Examples: - University lecture. - Work meeting. - Doctor appointment. -
Booked travel or errand. - Any event the user explicitly marks as fixed.

## 2.3 Flexible Task

A flexible task can be placed into an available time window, provided
all relevant constraints are satisfied.

## 2.4 Deadline

The latest time or date by which a task should be completed.

A deadline does not indicate when the user intends to work on the task.

## 2.5 Scheduled Time

The planned interval during which the user intends to work on a task.

A scheduled task has a start and end time, or an equivalent start time
and duration.

## 2.6 Estimate

The user's or system's predicted duration for completing a task.

## 2.7 Actual Duration

The measured or user-reported time spent working on a task.

Estimated duration and actual duration must remain separate.

## 2.8 Schedule Proposal

A proposed set of scheduling changes that has not yet been applied.

## 2.9 Confirmed Schedule

The currently accepted arrangement of fixed commitments and scheduled
tasks.

------------------------------------------------------------------------

# 3. Task Data Rules

## 3.1 Required Task Information

At minimum, a task must have:

-   A non-empty title.
-   A valid lifecycle status.
-   A unique identifier.
-   A creation timestamp.
-   An owning user or account.

Other properties may be optional.

## 3.2 Optional Task Information

A task may contain:

-   Description.
-   Category.
-   Priority.
-   Estimated duration.
-   Actual duration.
-   Deadline.
-   Scheduled start.
-   Scheduled end.
-   Project association.
-   Dependencies.
-   Recurrence settings.
-   User-defined tags.
-   Notes.
-   Source of creation.

## 3.3 Task Title

1.  A task title must not be empty or whitespace-only.
2.  The application should preserve the user's intended wording.
3.  AI-generated titles may be shortened for clarity, but must not
    change the task's meaning.
4.  Users must be able to edit titles manually.

## 3.4 Duration

1.  Estimated duration must be greater than zero when provided.
2.  Actual duration must never be negative.
3.  A missing estimate must remain unknown rather than being silently
    converted into a fabricated estimate.
4.  The assistant may ask the user for an estimate or propose one
    clearly labeled as an estimate.
5.  A task's actual duration must not automatically overwrite its
    original estimate.
6.  Duration units and storage precision must be consistent across the
    application.

## 3.5 Dates and Timezones

1.  All date-time values must be interpreted in the user's configured
    timezone.
2.  The application must preserve enough timezone information to
    interpret scheduled times correctly.
3.  Date-only deadlines must remain distinguishable from exact date-time
    deadlines.
4.  The system must not silently assume that a date-only deadline means
    midnight or the end of the day without a documented display and
    comparison rule.
5.  Daylight-saving transitions must be handled safely where applicable.
6.  Invalid or ambiguous date expressions must trigger clarification
    when they materially affect scheduling.

------------------------------------------------------------------------

# 4. Task Lifecycle Rules

## 4.1 Supported Statuses

The initial lifecycle contains:

  Status        Meaning
  ------------- -----------------------------------------------
  Inbox         Captured but not yet reviewed or organized
  Planned       Reviewed and ready for execution
  In Progress   Work has started
  Completed     Successfully finished
  Canceled      Intentionally abandoned or no longer required

Archived is a retention or visibility concept, not a lifecycle status.

Overdue is a computed condition, not a lifecycle status.

## 4.2 Allowed Transitions

  Current Status   Allowed Next Status
  ---------------- ------------------------------------
  Inbox            Planned, In Progress, Canceled
  Planned          In Progress, Completed, Canceled
  In Progress      Planned, Completed, Canceled
  Completed        Planned, if reopening is supported
  Canceled         Planned, if restoring is supported

Unsupported transitions must be rejected with a clear explanation.

The application must preserve status transition history.

## 4.3 Completion

When a task is completed:

1.  Its status becomes Completed.
2.  A completion timestamp is recorded.
3.  It is removed from active-task views by default.
4.  Its historical record is retained.
5.  It must count as completed work in relevant reporting.
6.  It must not be classified as canceled.
7.  Its prior schedule and deadline information must remain available.

The application may ask for confirmation if completion is triggered
through an ambiguous AI instruction.

## 4.4 Cancellation

When a task is canceled:

1.  Its status becomes Canceled.
2.  A cancellation timestamp is recorded.
3.  It is removed from the active workload by default.
4.  Its historical record is retained.
5.  It must not count as completed work.
6.  The system should optionally capture a cancellation reason.
7.  Its previous scheduling information must remain available for
    historical review.

## 4.5 Deletion

Deletion is different from cancellation.

-   Cancel means the task is intentionally no longer being pursued.
-   Delete means the user wants to remove the task record.

Deletion must be an explicit action. Destructive deletion should require
appropriate confirmation.

The exact retention and recovery policy for deleted records remains an
open product decision.

## 4.6 Reopening

If reopening is supported:

1.  The current status changes back to Planned or another valid active
    state.
2.  The previous completion or cancellation event remains in history.
3.  The system must not erase prior timestamps.
4.  Reopening must not automatically restore an old scheduled time if
    that time is now invalid.

## 4.7 Overdue Calculation

A task is overdue when all applicable conditions are met:

-   It has a deadline.
-   The deadline has passed according to the user's timezone and the
    defined deadline semantics.
-   Its status is not Completed or Canceled.

Overdue must be computed from task data.

The system must not permanently store Overdue as a replacement lifecycle
status.

A task may be both In Progress and Overdue.

------------------------------------------------------------------------

# 5. Deadline and Scheduling Rules

## 5.1 Deadline vs Scheduled Time

These fields have different meanings and must never be treated as
interchangeable.

Example:

-   Deadline: Thursday at 11:59 PM.
-   Scheduled time: Tuesday from 5:00 PM to 7:00 PM.

The user intends to work on Tuesday but must finish by Thursday.

Changing one field must not automatically change the other unless the
user explicitly requests it.

## 5.2 Tasks Without Deadlines

A task may exist without a deadline.

It can still be prioritized and scheduled according to user preferences
and available time.

The system must not invent a deadline.

## 5.3 Tasks Without Scheduled Times

A task may have a deadline and duration but no scheduled time.

It remains eligible for planning.

A task without a duration may require user clarification before it can
be placed accurately into a time slot.

## 5.4 Fixed Commitments

1.  Fixed commitments occupy their entire defined time interval.
2.  Flexible tasks must not overlap fixed commitments.
3.  Automatic scheduling must not move fixed commitments.
4.  Only an explicit user action may change a fixed commitment.
5.  The system must identify fixed commitments visually and logically.
6.  A fixed commitment may be represented as a task or a separate event
    entity. The final domain-model decision must be documented before
    implementation.

## 5.5 Time Intervals

For scheduling calculations, time intervals should use a consistent
convention.

Recommended convention:

**Start inclusive, end exclusive.**

For example:

-   Event A: 10:00--11:00.
-   Event B: 11:00--12:00.

These events are adjacent, not overlapping.

Two intervals overlap when:

`A.start < B.end AND B.start < A.end`

The implementation must consistently apply this rule.

## 5.6 Scheduled Task Duration

When both start and end times are present:

-   End must be later than start.
-   Scheduled duration is calculated from the interval.
-   The interval must satisfy applicable scheduling constraints.

If the user changes duration, the system must not silently modify the
deadline.

------------------------------------------------------------------------

# 6. Priority and Urgency Rules

## 6.1 Priority Levels

The initial levels are:

1.  Critical.
2.  High.
3.  Medium.
4.  Low.

Users may manually set or change priority.

## 6.2 Priority Is Not the Same as Urgency

Priority reflects importance.

Urgency reflects time pressure.

A task can be important but not urgent, or urgent but not especially
important.

The system should evaluate both when making recommendations.

## 6.3 Prioritization Inputs

Planning may consider:

-   User-assigned priority.
-   Deadline proximity.
-   Estimated duration.
-   Fixed commitments.
-   Dependencies.
-   Project importance, when available.
-   Available time.
-   User preferences.
-   Previous planning behavior, when explicitly supported.

## 6.4 Prioritization Safeguards

1.  The AI must not silently downgrade a user-assigned priority.
2.  A system-generated recommendation must be distinguishable from a
    user-defined priority.
3.  Missing information must not be treated as evidence of low
    importance.
4.  A task with no deadline must not automatically be ignored.
5.  The system should explain significant priority recommendations.

The exact ranking formula is a scheduling-engine decision and must be
documented separately from LLM prompts.

------------------------------------------------------------------------

# 7. Scheduling Engine Rules

## 7.1 Scheduling Objective

The scheduling engine should create a feasible plan that respects user
constraints and makes sensible use of available time.

It must not optimize for a visually full calendar at the expense of
realism.

## 7.2 Scheduling Inputs

The engine may consider:

-   Fixed commitments.
-   Available time windows.
-   Flexible tasks.
-   Estimated durations.
-   Deadlines.
-   Priority.
-   Dependencies.
-   User-defined working hours.
-   Break preferences.
-   Buffer time.
-   Existing confirmed schedule.
-   User-approved scheduling preferences.

## 7.3 Scheduling Constraints

The engine must:

1.  Avoid overlaps with fixed commitments.
2.  Avoid overlaps between scheduled tasks unless the user explicitly
    supports parallel work.
3.  Respect task dependencies.
4.  Respect deadline constraints when possible.
5.  Avoid scheduling canceled or completed tasks as active work.
6.  Respect fixed user-defined availability restrictions.
7.  Avoid assigning a task to a time window shorter than its required
    duration unless task splitting is explicitly supported.
8.  Clearly identify tasks that cannot be scheduled.
9.  Preserve already confirmed commitments unless the user approves
    changes.
10. Avoid silently changing task estimates.

## 7.4 Available Time

Available time is time not occupied by:

-   Fixed commitments.
-   Confirmed scheduled tasks.
-   User-defined unavailable periods.
-   Breaks or buffers where configured.

The system must distinguish between:

-   Free time.
-   Available working time.
-   Unallocated time.
-   Unscheduled task workload.

These concepts should not be treated as identical.

## 7.5 Insufficient Capacity

If total required work exceeds available time:

1.  The engine must identify the shortfall.
2.  It must not compress durations without permission.
3.  It must not overlap tasks to force a complete plan.
4.  It should propose alternatives such as moving flexible work,
    splitting tasks if supported, or asking the user to reprioritize.
5.  The user must see which tasks remain unscheduled.

## 7.6 Task Splitting

Task splitting is not assumed to be supported in the MVP.

If introduced later:

-   The original task must retain its identity.
-   Work sessions or subtasks must be linked to the original task.
-   The system must avoid double-counting estimated duration.
-   The user must be able to understand whether the task is partially
    completed or fully completed.

## 7.7 Buffer Time and Breaks

The scheduler should support configurable buffers between work blocks
and breaks.

It must not assume that every minute between commitments is productive
working time.

Default buffer values require product-owner approval.

## 7.8 Schedule Proposal

A proposal must include:

-   Proposed placements.
-   Tasks left unscheduled.
-   Conflicts.
-   Moved tasks.
-   Relevant deadline risks.
-   Assumptions.
-   Reasons for major changes.

A proposal must not be treated as a confirmed schedule.

## 7.9 Proposal Approval

1.  The user can review the proposal.
2.  The user can approve or reject it.
3.  The user should be able to inspect affected tasks.
4.  Approval applies only to the proposal version being reviewed.
5.  If underlying schedule data changes before approval, the proposal
    must be revalidated.
6.  Rejected proposals must not modify the confirmed schedule.
7.  Successful application must be recorded.

------------------------------------------------------------------------

# 8. Dynamic Rescheduling Rules

## 8.1 Trigger Conditions

Rescheduling may be requested when:

-   A task takes longer than expected.
-   A user becomes unavailable.
-   A fixed commitment changes.
-   A task is added with an urgent deadline.
-   A user manually requests a revised plan.
-   A previously confirmed plan becomes infeasible.

## 8.2 Rescheduling Behavior

When rescheduling:

1.  Retrieve the current confirmed schedule.
2.  Identify the affected time window.
3.  Identify tasks that can and cannot move.
4.  Preserve fixed commitments.
5.  Preserve completed work.
6.  Respect task dependencies.
7.  Generate feasible alternatives.
8.  Explain significant changes.
9.  Request approval when required.
10. Apply and record only approved changes.

## 8.3 Rescheduling Scope

The assistant should prefer the smallest reasonable change that restores
feasibility.

It should not unnecessarily rebuild the entire week when only one
afternoon has changed.

## 8.4 Completed and In-Progress Tasks

Completed tasks must never be rescheduled as unfinished work.

In-progress tasks require special care.

The system must not discard actual time already spent when changing
their remaining schedule.

The exact representation of remaining work is an open decision for the
MVP.

## 8.5 Change Transparency

For every applied rescheduling operation, users should be able to see:

-   What moved.
-   Previous scheduled time.
-   New scheduled time.
-   Why the change was proposed.
-   Whether the change was user-approved or authorized automatically.

------------------------------------------------------------------------

# 9. Task Dependencies and Projects

## 9.1 Project Association

A task may belong to a project or remain independent.

Changing a task's project association must not change its lifecycle
status or deadline automatically.

## 9.2 Dependencies

A dependency indicates that one task requires another task to reach an
appropriate state before it can begin.

For a simple finish-to-start dependency:

-   Task B cannot begin until Task A is completed.

## 9.3 Dependency Validation

1.  The system must prevent dependency cycles.
2.  A blocked task must be identifiable.
3.  The system should explain which dependency is blocking it.
4.  Completing a prerequisite should update the dependent task's
    eligibility.
5.  Canceling a prerequisite must trigger a review of affected dependent
    tasks.
6.  The system must not silently delete dependent tasks.

Advanced dependency types are outside the MVP unless explicitly
approved.

## 9.4 Milestones

Milestones represent project checkpoints.

They should be based on actual associated task progress and explicit
completion rules.

The system must not mark a milestone complete simply because a visual
animation has finished.

------------------------------------------------------------------------

# 10. AI Agent Permission Rules

## 10.1 General Principle

The AI is an assistant that operates through authorized application
tools.

It is not an unrestricted administrator.

Every action must be validated by the application.

## 10.2 Action Categories

### Category A --- Low-Risk Actions

Examples:

-   Read task details.
-   List tasks.
-   Summarize the day.
-   Identify overdue tasks.
-   Suggest priorities.
-   Draft new tasks.
-   Explain schedule conflicts.

These actions may generally happen without confirmation, subject to
normal access controls.

### Category B --- Controlled Mutations

Examples:

-   Create a clearly specified task.
-   Update a task field.
-   Change a task category.
-   Change a flexible task's scheduled time.
-   Mark a task completed.
-   Cancel a task.

These actions must follow explicit user permissions and confirmation
preferences.

For the MVP, ambiguous creation and consequential updates should require
review.

### Category C --- High-Impact Actions

Examples:

-   Move multiple scheduled tasks.
-   Change a fixed commitment.
-   Delete task records.
-   Cancel multiple tasks.
-   Apply a schedule affecting several days.
-   Change important user availability settings.

These actions must require explicit user approval.

## 10.3 AI Data Validation

Before applying an action:

1.  Validate required fields.
2.  Validate date and time values.
3.  Validate ownership and permissions.
4.  Validate lifecycle transitions.
5.  Validate scheduling constraints.
6.  Check for stale or conflicting data.
7.  Persist the action.
8.  Return the actual result to the assistant.

## 10.4 No False Success

The assistant must never say a task was created, updated, completed, or
rescheduled unless the application confirms the operation succeeded.

If an operation fails, the assistant must communicate the failure
accurately.

## 10.5 Ambiguity Handling

The assistant should ask a clarification question when ambiguity
changes:

-   Which task is affected.
-   The date or time.
-   The task duration.
-   Whether an event is fixed.
-   The deadline.
-   Whether the user intends to cancel or complete a task.
-   Whether an existing schedule should be modified.

The assistant should not ask unnecessary questions when a safe,
reversible action is clear.

## 10.6 Auditability

The system should retain an activity record for important AI actions,
including:

-   Requested operation.
-   Affected records.
-   Previous values where relevant.
-   Applied values.
-   Timestamp.
-   Result.
-   Approval information where applicable.

------------------------------------------------------------------------

# 11. Visual Workspace Rules

## 11.1 Spatial Position vs Business Data

A task's visual position is not automatically its scheduled time.

The application must distinguish:

-   Spatial placement: where an object appears in My Space.
-   Schedule placement: when the task is planned to happen.

Moving a bubble in My Space must not change the schedule unless the
interaction explicitly communicates that behavior.

## 11.2 Bubble Representation

Bubble size, color, glow, and labels may represent task information.

However:

-   Essential task information must remain accessible as text.
-   Color must not be the only indicator of status or priority.
-   Visual emphasis must not imply a false deadline.
-   Bubble size must not replace the actual duration label.
-   The layout must avoid hiding important tasks.

## 11.3 Visual State Consistency

Visual state must reflect persisted business state.

An animation must not imply success before the backend confirms the
operation.

If persistence fails, the interface must restore or clearly mark the
previous state.

## 11.4 Spatial Organization

The system should support:

-   Stable object placement.
-   Automatic organization.
-   Clear grouping.
-   Collision avoidance.
-   Accessible selection.
-   Alternative non-drag interactions.

User-defined spatial preferences should be preserved when possible.

------------------------------------------------------------------------

# 12. History and Analytics Rules

## 12.1 Historical Records

Completed and canceled tasks must remain distinguishable.

History must preserve relevant original task information.

## 12.2 Completion Metrics

Only tasks with Completed status count as completed work.

Canceled tasks must not count toward completion totals.

## 12.3 Duration Metrics

Estimated duration and actual duration must be stored separately.

The system must distinguish measured time from user-entered or inferred
time.

## 12.4 Historical Schedule Changes

Where practical, schedule changes should preserve previous and new time
values.

This supports review of planning behavior and schedule accuracy.

## 12.5 Data Corrections

If users correct historical information, the system should preserve
enough audit context to avoid silently rewriting important activity
history.

------------------------------------------------------------------------

# 13. Notifications and Reminder Rules

## 13.1 Reminder Eligibility

A reminder may be triggered by:

-   An approaching scheduled start.
-   An approaching deadline.
-   An overdue task.
-   A user-requested reminder.
-   A planning event.

## 13.2 Reminder Behavior

1.  Respect user notification preferences.
2.  Avoid duplicate reminders for the same trigger.
3.  Do not send reminders for completed or canceled tasks unless
    explicitly requested.
4.  Use the user's timezone.
5.  Clearly distinguish deadline reminders from scheduled-start
    reminders.
6.  Avoid claiming a reminder was delivered when delivery has not been
    confirmed.

## 13.3 Notification Channels

The MVP notification channel is an open product decision.

Do not assume email, push, or browser notifications are available until
selected and implemented.

------------------------------------------------------------------------

# 14. Error Handling and Recovery

## 14.1 Invalid Task Data

Reject invalid data and explain the specific issue.

Do not silently discard unrelated valid fields unless the operation's
atomicity rules require rejection.

## 14.2 Scheduling Conflict

Do not apply a conflicting schedule as if it were valid.

Return the conflict and affected records.

## 14.3 Partial Failure

If an operation affects multiple tasks and only some updates succeed,
the application must report the exact result.

Prefer atomic operations for multi-task schedule application where
feasible.

## 14.4 Duplicate Requests

Repeated requests must not unintentionally create duplicate tasks or
apply the same mutation multiple times.

Use suitable idempotency and request-tracking mechanisms during
implementation.

## 14.5 Concurrent Updates

If the same task changes between proposal generation and approval, the
system must detect stale data and revalidate before applying the
proposal.

------------------------------------------------------------------------

# 15. MVP Rule Prioritization

  Rule Area                                  Priority
  ------------------------------------------ ----------
  Task identity and required fields          P0
  Task lifecycle                             P0
  Completion vs cancellation                 P0
  Deadline vs scheduled time                 P0
  Timezone handling                          P0
  Fixed commitment protection                P0
  Interval overlap detection                 P0
  Manual scheduling validation               P0
  AI action validation                       P0
  Confirmation for consequential changes     P0
  History preservation                       P0
  Spatial position vs schedule distinction   P0
  Automated scheduling proposals             P1
  Dynamic rescheduling                       P1
  Task dependencies                          P1
  Project milestones                         P1
  Actual-time analytics                      P1
  Proactive AI actions                       P2

------------------------------------------------------------------------

# 16. Business Rule Acceptance Criteria

The implementation must demonstrate the following behaviors.

1.  A task can exist without a deadline.
2.  A task can exist without a scheduled time.
3.  Deadline and scheduled time can be edited independently.
4.  A completed task is not classified as canceled.
5.  A canceled task is not counted as completed.
6.  An overdue task retains its lifecycle status.
7.  Fixed commitments are protected from automatic rescheduling.
8.  Adjacent intervals are not incorrectly identified as overlapping.
9.  Conflicting intervals are detected.
10. An infeasible schedule is not presented as feasible.
11. A schedule proposal does not modify confirmed data before approval.
12. Stale proposals are revalidated.
13. AI actions cannot bypass application validation.
14. Failed actions are never reported as successful.
15. Visual bubble movement does not accidentally modify scheduled time.
16. Historical task information remains retrievable.
17. Multi-task operations report their actual outcomes.
18. Important AI actions have an auditable record.

------------------------------------------------------------------------

# 17. Open Product Decisions

The following decisions require explicit approval before they are
treated as final behavior.

1.  **Default working hours:** What are the default daily working
    windows?
2.  **Break policy:** Should the product use default break durations or
    require user configuration?
3.  **Task duration:** What happens when a task has no estimate?
4.  **Task splitting:** Should long tasks be split into multiple work
    sessions?
5.  **Fixed commitments:** Should these be a separate event entity or a
    special task type?
6.  **Reopening:** Should completed and canceled tasks be restorable?
7.  **Deletion:** Should deletion be soft-delete, recoverable trash, or
    permanent deletion?
8.  **AI auto-creation:** Which unambiguous task creations may happen
    without confirmation?
9.  **Automatic scheduling:** Should users be able to authorize specific
    low-risk schedule changes?
10. **In-progress tasks:** How should remaining work be represented
    after interruption?
11. **Spatial persistence:** Should users be able to manually arrange
    and save bubble positions?
12. **Reminders:** Which notification channels belong in the MVP?
13. **Date-only deadlines:** What is the exact end-of-day interpretation
    in the user's timezone?
14. **Recurring tasks:** How should skipped or incomplete occurrences
    behave?

Until resolved, implementation agents must document assumptions and
avoid making irreversible product decisions.

------------------------------------------------------------------------

# 18. Instructions for Implementation Agents

Before coding:

1.  Read this document and `PRD.md`.
2.  Read `UI_UX_SPEC.md`.
3.  Identify contradictions and unresolved decisions.
4.  Propose a domain model that supports these rules.
5.  Separate AI interpretation from deterministic business logic.
6.  Identify validation boundaries.
7.  Propose test cases for each P0 rule.
8.  Present assumptions for approval.

During implementation:

-   Never use LLM output as the final authority for data validity.
-   Never conflate deadlines with scheduled times.
-   Never conflate completion with cancellation.
-   Never allow fixed commitments to move silently.
-   Never apply unapproved consequential schedule changes.
-   Never report a mutation as successful before persistence confirms
    it.
-   Never let spatial presentation state silently mutate business data.
-   Preserve historical records and important state transitions.
-   Add automated tests for business rules.
-   Document any deviation from this specification.

If a rule conflicts with the PRD or UI/UX specification, stop and report
the conflict instead of silently choosing one.

------------------------------------------------------------------------

# 19. Final Business Principle

LifeSpace must make organization easier without taking control away from
the user.

The system should be intelligent enough to understand, recommend, and
adapt, but disciplined enough to respect time constraints, preserve
data, and explain its actions.

**AI proposes. The application validates. The user stays in control.**
