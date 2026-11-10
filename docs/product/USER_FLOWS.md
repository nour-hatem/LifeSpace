# USER_FLOWS.md

## LifeSpace User Flows

**Product:** LifeSpace\
**Tagline:** Your Life, In One Space.\
**Document type:** Product and interaction specification\
**Status:** MVP flow baseline\
**Related documents:** `PRD.md`, `UI_UX_SPEC.md`, `BUSINESS_RULES.md`

------------------------------------------------------------------------

## 1. Purpose

This document defines how users move through LifeSpace and how the
frontend, AI Companion, application services, scheduling logic, and
persistence layer should behave during each journey.

It describes observable product behavior. It does not prescribe a
technology stack or implementation framework.

## 2. Actors and Responsibilities

  -----------------------------------------------------------------------
  Actor                               Responsibility
  ----------------------------------- -----------------------------------
  User                                Provides intent, reviews proposals,
                                      makes decisions, and controls
                                      consequential changes

  LifeSpace UI                        Presents the spatial workspace,
                                      captures input, displays state, and
                                      collects approval

  AI Companion                        Interprets natural language,
                                      extracts information, explains
                                      options, and proposes actions

  Application layer                   Validates requests, enforces
                                      business rules and permissions, and
                                      coordinates operations

  Scheduling engine                   Evaluates time constraints,
                                      availability, conflicts, and
                                      schedule proposals

  Persistence layer                   Stores confirmed application state
                                      and returns the authoritative
                                      result

  Notification service                Delivers configured reminders and
                                      reports delivery failures where
                                      relevant
  -----------------------------------------------------------------------

The AI Companion must not bypass application validation or persistence.
The UI must not display an operation as completed until the application
confirms it.

## 3. Shared Interaction Contract

Most AI-assisted mutations follow this sequence.

1.  **Capture** --- The user submits a request through text or another
    enabled input method.
2.  **Interpret** --- The AI identifies the user's intent and extracts
    relevant entities and values.
3.  **Clarify or draft** --- Missing or ambiguous information is
    requested, or a proposed action is prepared.
4.  **Validate** --- The application checks data types, permissions,
    lifecycle rules, scheduling constraints, and conflicts.
5.  **Approve** --- The user confirms consequential changes when
    approval is required.
6.  **Persist** --- The application writes the accepted change.
7.  **Reflect** --- The UI updates from the confirmed result.
8.  **Report** --- The user receives a clear success, partial-success,
    or failure message.

For direct manual edits, capture and interpretation may be replaced by
an explicit form or interaction. Validation and persistence still apply.

### 3.1 Required interaction states

-   Idle
-   Capturing
-   Interpreting
-   Needs clarification
-   Draft ready for review
-   Validation failed
-   Awaiting approval
-   Executing
-   Completed
-   Partially completed
-   Failed
-   Canceled by user

The UI must distinguish these states. A loading animation alone is not a
sufficient status message.

### 3.2 Approval policy

-   Reading and summarizing existing information does not require
    approval.
-   Creating a task from an explicit user request may proceed after the
    user confirms the extracted task details. A product decision may
    later allow trusted quick-capture rules.
-   Changes to scheduled times, fixed commitments, multiple tasks,
    dependencies, or a broad schedule require a reviewable proposal
    before execution.
-   The user can edit, approve, or reject a proposal.
-   The application must revalidate a proposal at approval time. If its
    assumptions are stale, show the changed conditions and request a
    fresh decision.

------------------------------------------------------------------------

## 4. Entry and First-Time Setup

**Priority:** P0

### 4.1 First visit

1.  User opens LifeSpace.
2.  The application checks the user's session.
3.  If authentication is required, the user signs in or creates an
    account.
4.  The application loads the user's profile and workspace.
5.  If no setup data exists, LifeSpace shows a lightweight welcome
    experience.
6.  The user can enter a first task immediately. Setup must not become a
    long mandatory questionnaire.
7.  LifeSpace opens My Space and displays either the first saved task or
    a useful empty state.

**Empty-state behavior**

-   Explain that the space is ready for tasks.
-   Provide one obvious action to add a task.
-   Offer a natural-language example such as "Prepare the machine
    learning presentation by Thursday".
-   Do not fabricate tasks, deadlines, projects, or calendar events.

### 4.2 Returning user

1.  User opens LifeSpace.
2.  The application restores the last valid workspace view where
    possible.
3.  It loads persisted tasks, projects, schedule data, and user
    preferences.
4.  The UI displays the latest confirmed state.
5.  If data cannot be loaded, show a recoverable error and a retry
    action. Do not replace missing server data with misleading
    empty-state content.

------------------------------------------------------------------------

## 5. Natural-Language Task Capture

**Priority:** P0

### 5.1 Single task with clear details

**Example input:** "Finish the RAG evaluation report tomorrow. It should
take two hours."

1.  User submits the sentence to the AI Companion.
2.  The AI extracts a task title, a deadline candidate, and an estimated
    duration.
3.  The application resolves relative dates using the user's configured
    timezone.
4.  The UI presents a reviewable task draft.
5.  User checks or edits the extracted details.
6.  User confirms.
7.  The application validates and persists the task.
8.  The new task appears in My Space and is available in task search and
    other relevant views.

**Important:** A deadline does not automatically become a scheduled work
session. If the user says "by tomorrow", that defines a deadline, not a
confirmed start time.

### 5.2 Multiple tasks in one message

**Example input:** "Tomorrow I need to review the NLP paper, send the
internship email, and study Fourier analysis."

1.  AI detects multiple task candidates.
2.  It extracts each task independently.
3.  The UI displays all drafts together with any uncertain fields
    clearly marked.
4.  User can edit or remove individual drafts.
5.  User confirms the selected drafts.
6.  The application validates and saves them.
7.  The UI reports which tasks were created.

If only some tasks can be saved, show the successful and failed items
separately. Never imply that the entire batch succeeded.

### 5.3 Ambiguous input

**Example input:** "Remind me to prepare for the exam."

1.  AI identifies a likely task but cannot infer a reliable date or
    time.
2.  It asks only for information needed to proceed.
3.  User can provide a date, leave the deadline unset, or cancel.
4.  The application does not invent a deadline.

### 5.4 Missing duration

1.  AI extracts the task without an estimated duration.
2.  The task can still be saved if duration is optional under the
    product rules.
3.  Scheduling features that require a duration must ask the user or use
    an explicitly labeled estimate.
4.  An estimate must never be represented as a user-confirmed value.

### 5.5 Fixed commitment recognition

**Example input:** "I have a lecture every Monday from 10 to 12."

1.  AI recognizes a possible recurring fixed commitment.
2.  The UI presents the proposed commitment and recurrence details.
3.  User reviews the day, time, recurrence, and timezone.
4.  User confirms before it is stored as a fixed commitment.
5.  The scheduling engine treats confirmed fixed commitments as
    constraints.

If the recurrence or date range is unclear, ask for clarification rather
than guessing.

------------------------------------------------------------------------

## 6. Manual Task Creation

**Priority:** P0

1.  User selects the add-task action.
2.  A compact task editor opens.
3.  User enters the title and any optional details such as description,
    category, priority, deadline, or estimated duration.
4.  User saves the task.
5.  The application validates the fields and persists the task.
6.  My Space displays the new task.

If validation fails, keep the user's entered values and show the issue
beside the relevant field. Do not silently discard the draft.

------------------------------------------------------------------------

## 7. My Space

**Priority:** P0

### 7.1 Explore the workspace

1.  User opens My Space.
2.  LifeSpace displays task bubbles and visual groupings based on
    persisted task data and workspace preferences.
3.  User can pan, zoom, and navigate the 2D space using supported input
    methods.
4.  Selecting a bubble opens its contextual task surface.
5.  The user can return to the workspace without losing the current view
    unnecessarily.

Spatial placement is a presentation and organization property. It must
not silently change a task's deadline or scheduled time.

### 7.2 Select and inspect a task

1.  User selects a task bubble.
2.  The bubble receives a clear selected state.
3.  A contextual surface shows the task's title, status, priority,
    deadline, scheduled time if any, duration estimate, and available
    actions.
4.  User can open the full task detail view or perform a supported quick
    action.

### 7.3 Move a bubble

1.  User drags a bubble to a new position.
2.  The UI previews the new spatial position.
3.  On release, the application saves the workspace position.
4.  The UI confirms the new position after persistence succeeds.

Dragging a bubble changes its spatial position only. It does not
reschedule the task unless the user is explicitly interacting with a
scheduling surface in Time Flow.

### 7.4 Organize tasks

1.  User chooses a supported grouping or organization action.
2.  The UI previews the resulting arrangement.
3.  User confirms if the action affects multiple items or changes
    persisted organization.
4.  The application saves the organization state.
5.  The UI updates from the confirmed result.

------------------------------------------------------------------------

## 8. Task Details and Editing

**Priority:** P0

### 8.1 Edit task details

1.  User opens a task.
2.  User selects edit.
3.  The editor shows current persisted values.
4.  User changes one or more fields.
5.  User saves.
6.  The application validates the update.
7.  The application persists the change and returns the authoritative
    task.
8.  The UI refreshes the task bubble and detail surface.

If the task changed elsewhere while the editor was open, the application
must detect the stale update and ask the user to refresh or reconcile
changes.

### 8.2 Change a deadline

1.  User edits the deadline field or asks the AI to change it.
2.  The UI clearly labels the field as a deadline.
3.  User confirms the new value.
4.  The application validates and persists it.
5.  The UI updates the deadline.

Changing a deadline must not automatically move a scheduled session
unless the user explicitly requests schedule adjustment and approves the
resulting proposal.

### 8.3 Change scheduled time

1.  User changes the scheduled start or duration in Time Flow or task
    details.
2.  The application checks availability and constraints.
3.  If there is a conflict, the UI explains it and offers valid next
    steps.
4.  User selects or approves a valid option.
5.  The application persists the new schedule.
6.  Time Flow and the task detail surface update.

A scheduled time is distinct from a deadline. Both may exist on the same
task.

------------------------------------------------------------------------

## 9. Task Lifecycle

**Priority:** P0

### 9.1 Complete a task

1.  User selects Complete.
2.  The application checks whether the transition is valid.
3.  The application persists the completed status and completion
    timestamp.
4.  The task leaves active views according to workspace rules and
    appears in history or Memory Garden.
5.  The UI confirms completion.

Do not mark a task completed merely because its scheduled time has
passed or a Focus Mode timer ended.

### 9.2 Cancel a task

1.  User selects Cancel.
2.  The UI may request confirmation when the action is consequential.
3.  The application persists the canceled status and cancellation
    metadata.
4.  The task is removed from active work views and retained in history.
5.  The UI confirms cancellation.

Canceled and completed are different states and must remain
distinguishable.

### 9.3 Delete a task

1.  User selects Delete.
2.  The UI explains the consequence and requests confirmation where
    required.
3.  The application applies the defined deletion policy.
4.  The UI removes the task only after confirmed success.

Deletion behavior and retention policy must follow `BUSINESS_RULES.md`.
Do not treat deletion as completion or cancellation.

### 9.4 Reopen or restore

1.  User opens a historical task.
2.  User selects the supported reopen or restore action.
3.  The application validates the transition.
4.  The application persists the new state.
5.  The task returns to the appropriate active view.

If the action is not valid for the task's current state, explain why and
preserve history.

------------------------------------------------------------------------

## 10. Time Flow

**Priority:** P0 for daily view; P1 for expanded views

### 10.1 Open the daily timeline

1.  User opens Time Flow.
2.  The application loads scheduled sessions and fixed commitments for
    the selected date.
3.  The timeline displays available time and occupied periods.
4.  Unscheduled tasks remain visibly distinct from scheduled sessions.
5.  User can move to another date.

The timeline must not imply that an unscheduled task has a confirmed
time.

### 10.2 Schedule a task manually

1.  User selects an unscheduled task.
2.  User chooses an available time slot or enters a time.
3.  The application checks duration, availability, fixed commitments,
    and conflicts.
4.  If valid, the UI previews the scheduled session.
5.  User confirms.
6.  The application persists the schedule.
7.  Time Flow and the task detail view update.

### 10.3 Resize a scheduled session

1.  User drags the session boundary to change its duration.
2.  The UI previews the new duration.
3.  The application checks whether the change creates conflicts or
    violates constraints.
4.  User confirms the valid change.
5.  The application persists the update.
6.  The timeline refreshes.

### 10.4 Scheduling conflict

1.  User attempts to schedule or move a task into an occupied period.
2.  The application detects the conflict.
3.  The UI identifies the conflicting item and time range.
4.  LifeSpace offers alternatives only when it can calculate valid
    alternatives.
5.  User chooses an option or cancels.
6.  No conflicting schedule is persisted without an explicit supported
    override.

### 10.5 Day, week, and month navigation

1.  User selects a time range.
2.  The application loads the relevant schedule data.
3.  The UI changes its time scale while preserving the distinction
    between deadlines, scheduled sessions, and fixed commitments.
4.  User can navigate forward and backward.

The MVP should prioritize a useful daily timeline. Week and month views
may be staged according to the release plan.

------------------------------------------------------------------------

## 11. AI-Assisted Daily Planning

**Priority:** P1

### 11.1 Generate a daily plan

1.  User asks the AI Companion to plan the day.
2.  AI retrieves relevant tasks, deadlines, priorities, durations, and
    confirmed fixed commitments.
3.  Scheduling logic calculates available time and feasible placements.
4.  The system generates a proposal with explanations and any
    unscheduled tasks.
5.  The UI displays the proposed timeline and trade-offs.
6.  User can approve, edit, or reject the proposal.
7.  On approval, the application revalidates all affected items.
8.  The application persists the approved schedule changes.
9.  Time Flow updates from the persisted result.

The proposal must not be treated as an executed schedule before approval
and successful persistence.

### 11.2 Insufficient available time

1.  The scheduling engine determines that all tasks cannot fit.
2.  The proposal identifies the tasks that cannot be scheduled.
3.  It explains the relevant constraints, such as limited available time
    or conflicting commitments.
4.  User can change priorities, durations, deadlines, or the planning
    horizon.
5.  The system generates a revised proposal.

Do not hide overload by placing tasks into unavailable time.

### 11.3 Reject a proposal

1.  User rejects the proposal.
2.  No proposed schedule changes are persisted.
3.  Existing confirmed schedule remains unchanged.
4.  The UI returns to the prior view and may retain the rejected
    proposal for reference during the current interaction.

------------------------------------------------------------------------

## 12. Dynamic Rescheduling

**Priority:** P1

**Example:** A meeting runs late and the user asks LifeSpace to
reorganize the remaining day.

1.  User tells the AI Companion what changed.
2.  AI identifies the affected time window and relevant tasks.
3.  Scheduling logic recalculates availability.
4.  Existing fixed commitments are preserved.
5.  The system minimizes unnecessary changes to unaffected scheduled
    sessions.
6.  The UI shows a before-and-after proposal and explains important
    changes.
7.  User approves, edits, or rejects the proposal.
8.  The application revalidates the proposal.
9.  Approved changes are persisted.
10. Time Flow updates from the confirmed result.

If the application cannot determine what time was lost or which
commitments changed, it asks a focused clarification question.

------------------------------------------------------------------------

## 13. AI Companion

**Priority:** P0 for basic task operations; P1 for planning

### 13.1 Open the Companion

1.  User activates the floating AI Companion.
2.  A compact interaction surface opens within the spatial workspace.
3.  The user can enter a request.
4.  The current workspace remains accessible where practical.

The Companion is not a replacement for the workspace and should not
become a permanent, dominant chat sidebar.

### 13.2 Read-only request

**Example:** "What are my most urgent tasks?"

1.  AI identifies the request as read-only.
2.  The application retrieves current task data.
3.  AI summarizes the results using persisted values.
4.  The UI presents the answer and links or actions to relevant tasks.

No mutation approval is needed.

### 13.3 Create or update through the Companion

1.  User states the requested change.
2.  AI extracts the intended operation and target records.
3.  If the target is ambiguous, AI asks which item the user means.
4.  The application validates the proposed operation.
5.  The UI presents a review surface when approval is required.
6.  User approves or rejects.
7.  The application executes and persists the operation.
8.  The UI reflects the confirmed result.

### 13.4 Multiple operations in one request

1.  AI decomposes the request into individual operations.
2.  The application validates each operation and identifies dependencies
    between them.
3.  The UI presents a grouped proposal.
4.  User reviews the scope and approves or edits it.
5.  The application executes according to the defined transaction and
    partial-failure policy.
6.  The UI reports the result for each operation.

Never report a whole request as successful if only some operations
succeeded.

### 13.5 Tool or service failure

1.  An AI or application operation fails.
2.  The UI shows that the action was not completed.
3.  The application preserves the last confirmed state.
4.  The user receives a retry or manual alternative where possible.
5.  If the result is uncertain because a request timed out, the
    application checks the operation status before retrying to avoid
    duplicate records.

### 13.6 AI unavailable

1.  The UI indicates that AI assistance is temporarily unavailable.
2.  Manual task creation, editing, completion, and workspace navigation
    remain usable.
3.  The user can retry AI assistance later.

------------------------------------------------------------------------

## 14. Projects and Dependencies

**Priority:** P1

### 14.1 Create a project

1.  User selects the project creation action or asks the AI Companion.
2.  User enters a project name and optional description or target date.
3.  The application validates and saves the project.
4.  Project Universe displays the new project as a distinct cluster or
    constellation.

### 14.2 Add or move a task into a project

1.  User selects a task and chooses a project.
2.  The application validates the association.
3.  The application persists the relationship.
4.  The project view and task detail update.

### 14.3 Add a dependency

1.  User selects a predecessor and successor task.
2.  The UI previews the dependency relationship.
3.  The application checks for invalid relationships, including cycles
    where applicable.
4.  User confirms.
5.  The application persists the dependency.
6.  Project Universe displays the relationship.

A dependency must affect planning only according to the rules defined in
`BUSINESS_RULES.md`.

------------------------------------------------------------------------

## 15. Focus Mode

**Priority:** P1

### 15.1 Start a focus session

1.  User selects a task and starts Focus Mode.
2.  The UI displays the selected task and a focus timer.
3.  The application records the session start when supported.
4.  The user can pause, resume, or end the session.

### 15.2 End a focus session

1.  User ends the session or the timer reaches its configured endpoint.
2.  The application records the actual session duration where supported.
3.  The task remains active unless the user explicitly marks it
    complete.
4.  The UI offers a brief option to record progress or update the task.

Timer completion must not automatically complete the task.

------------------------------------------------------------------------

## 16. Reminders and Notifications

**Priority:** P1 unless a minimal reminder capability is included in MVP

1.  A reminder is created from an explicit user action or a confirmed
    supported rule.
2.  The application validates the reminder time and related task.
3.  The reminder is persisted.
4.  At the configured time, the notification service attempts delivery
    through enabled channels.
5.  The user can open the related task from the notification where
    supported.
6.  Delivery failures are handled without changing the task's lifecycle
    state.

Notification channels, permissions, and delivery guarantees are product
and implementation decisions. Do not claim a reminder was delivered
based only on successful reminder creation.

------------------------------------------------------------------------

## 17. History and Memory Garden

**Priority:** P1

1.  User opens Memory Garden or task history.
2.  The application loads completed and canceled tasks from persisted
    records.
3.  The UI distinguishes completed, canceled, and other historical
    states.
4.  User selects an item to inspect its details and timestamps.
5.  User may reopen or restore an item if that transition is supported.
6.  The application persists the transition before moving the item back
    into active views.

Historical records must not be silently rewritten to make current
workspace views look cleaner.

------------------------------------------------------------------------

## 18. Preferences and Personalization

**Priority:** P1

1.  User opens settings.
2.  The application displays current persisted preferences.
3.  User changes supported preferences such as timezone, default view,
    or planning behavior.
4.  The application validates and saves the change.
5.  Relevant views and future AI interpretations use the updated
    preferences.

The system must distinguish an explicit user preference from a pattern
inferred by AI. Inferred preferences should be reviewable and must not
silently override explicit settings.

------------------------------------------------------------------------

## 19. Responsive and Accessible Interaction

**Priority:** P0

### Desktop

-   Support pointer, keyboard, and trackpad interactions.
-   Provide non-drag alternatives for important spatial actions.
-   Keep task details and approval controls easy to reach.

### Tablet

-   Support touch and pointer where available.
-   Ensure contextual surfaces fit the viewport.
-   Avoid requiring precise drag gestures for essential actions.

### Mobile

-   Prioritize capture, task details, completion, and a readable
    timeline.
-   Use touch-friendly controls.
-   Provide a practical list or agenda fallback when the full spatial
    environment is too constrained.
-   Do not remove essential task information to preserve a visual
    effect.

### Accessibility

-   Provide keyboard navigation and visible focus.
-   Give interactive bubbles accessible names and states.
-   Do not communicate priority, status, or conflicts through color
    alone.
-   Respect reduced-motion preferences.
-   Ensure timers and status changes are available to assistive
    technology.
-   Provide alternatives to drag-and-drop.

------------------------------------------------------------------------

## 20. Global Edge Cases and Recovery

  -----------------------------------------------------------------------
  Situation                           Required behavior
  ----------------------------------- -----------------------------------
  Network unavailable                 Preserve local draft input where
                                      feasible; show that persistence did
                                      not occur

  Save request times out              Check operation status before
                                      retrying to prevent duplicates

  Concurrent edit                     Detect stale data and request
                                      refresh or reconciliation

  Invalid date or timezone            Explain the invalid value and
                                      request correction

  Relative date is ambiguous          Ask for clarification; do not guess

  Deadline is in the past             Allow or reject according to
                                      business rules and clearly disclose
                                      the result

  Task has no duration                Permit storage if valid; request or
                                      label an estimate before
                                      duration-based scheduling

  Fixed commitment conflict           Preserve the commitment and explain
                                      the conflict

  AI returns malformed data           Reject invalid output and ask the
                                      AI to retry or let the user edit
                                      manually

  Partial batch failure               Report success and failure per item

  User rejects an action              Leave persisted state unchanged

  User closes a proposal              Do not execute it

  AI service unavailable              Keep core manual workflows
                                      available

  Empty workspace                     Show a helpful empty state without
                                      fabricated content

  Large task collection               Keep navigation and interaction
                                      responsive; use progressive loading
                                      where needed
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 21. Priority Summary

  -----------------------------------------------------------------------
  Priority                            User journeys
  ----------------------------------- -----------------------------------
  P0 --- MVP                          Entry and empty state,
                                      natural-language capture and
                                      review, manual task creation, My
                                      Space, task details and editing,
                                      deadline versus scheduled-time
                                      distinction, lifecycle actions,
                                      basic daily Time Flow, basic AI
                                      Companion operations, error and
                                      recovery states, accessibility
                                      baseline

  P1 --- Next                         Daily planning proposals,
                                      conflict-aware scheduling, dynamic
                                      rescheduling, projects and
                                      dependencies, Focus Mode,
                                      reminders, Memory Garden,
                                      preferences, expanded timeline
                                      views

  P2 --- Later                        Voice-first workflows, deeper
                                      calendar and external integrations,
                                      advanced proactive planning, richer
                                      analytics, advanced personalization
  -----------------------------------------------------------------------

Priorities are release guidance. The PRD remains the source for final
scope decisions.

------------------------------------------------------------------------

## 22. Acceptance Criteria

A flow is ready for release when all applicable criteria are met.

1.  The user can complete the journey without relying on hidden or
    fabricated data.
2.  Required fields and ambiguous intent are handled explicitly.
3.  The application validates every mutation independently of AI output.
4.  Consequential proposals are reviewable and require the defined
    approval.
5.  Rejected or canceled proposals do not alter persisted state.
6.  UI success states appear only after confirmed persistence.
7.  Failures preserve the last confirmed state and provide a recovery
    path.
8.  Deadline, scheduled time, fixed commitment, and spatial position
    remain distinct concepts.
9.  Completed and canceled tasks remain distinguishable in history.
10. Essential workflows have keyboard and touch-accessible alternatives.
11. The flow remains understandable when AI assistance is unavailable.
12. Automated tests cover the main path and the relevant edge cases.

------------------------------------------------------------------------

## 23. Traceability

Use these documents together.

-   `PRD.md` defines product goals, scope, requirements, and release
    intent.
-   `UI_UX_SPEC.md` defines visual language, layout, navigation, and
    interaction presentation.
-   `BUSINESS_RULES.md` defines domain constraints, lifecycle
    transitions, scheduling rules, and AI permissions.
-   `USER_FLOWS.md` defines end-to-end user journeys and expected system
    behavior.

If a flow appears to conflict with a business rule, `BUSINESS_RULES.md`
governs domain behavior. If a flow appears to conflict with product
scope, `PRD.md` governs scope. Record unresolved conflicts as open
decisions rather than silently choosing an implementation.

## 24. Open Product Decisions

The following decisions must be resolved before implementing the
affected flows.

-   Authentication provider and account model.
-   Whether task creation from AI can use a trusted one-step
    confirmation setting.
-   Exact deletion and retention policy.
-   Reminder channels and delivery guarantees.
-   Whether recurring fixed commitments are included in MVP.
-   Exact scheduling proposal and partial-commit behavior.
-   Offline draft persistence expectations.
-   Mobile navigation and the threshold for switching to an agenda
    fallback.
-   Whether week and month Time Flow views ship in the first release.

Do not invent answers to these questions during implementation. Use
explicit defaults only after the product owner approves them.
