# ADR 0002: M2 persistence and task API decisions

**Status:** Provisional. The architect's defaults, adopted on 2026-11-16 when the owner approved starting M2. The owner may override any item.
**Sources:** blueprint sections 4, 7, 8, and 13, ADR 0001, BUSINESS_RULES 4.5, PRD FR-010 to FR-018, FR-030, and FR-015.

## Scope of M2

In scope: the `application` layer (use cases and ports), PostgreSQL persistence for tasks, status history, one settings row, and idempotency keys, the task HTTP API under `/api/v1`, problem+json errors with a `result` member, and generated OpenAPI and TypeScript types.

Out of scope: authentication and ownership (not approved), fixed commitments (M5), the frontend (M3), AI (M7), a restore endpoint, idempotency key expiry, `request_id` in error bodies, and any new runtime dependency.

## Decisions

| # | Decision |
|---|---|
| 1 | The application layer is `lifespace.application`. It imports only the standard library and `lifespace.domain`. It never reads the clock or generates ids: a `Clock` port and an `IdGenerator` port are injected. Infrastructure supplies `SystemClock` (aware UTC) and `Uuid7Generator` (`uuid.uuid7()`) |
| 2 | Use cases are plain async functions that take a `UnitOfWorkFactory` and the ports they need. One use case call is one transaction. Reads never commit. Leaving a unit of work without `commit()` rolls back |
| 3 | The domain `Task` has no version. The application wraps it as `StoredTask(task, version)`. ORM models never leave `lifespace.infrastructure` |
| 4 | Version starts at 1 and increases by exactly 1 on every successful edit, transition, or delete. Every mutating call carries the expected version. A mismatch raises `StaleVersionError` (HTTP 409, code `stale_version`, result `conflict`) and changes nothing |
| 5 | Deletion is soft (`deleted_at`). A deleted task is invisible to every read and to every mutation (HTTP 404). Its status events are kept. There is no restore endpoint in M2. Deleting also needs the expected version |
| 6 | Status history is the append-only table `task_status_events`, written in the same transaction as the transition. Task creation is not an event (the task has `created_at`) |
| 7 | All timestamps are `timestamptz`, stored and returned in UTC. A date-only deadline is a `date` column and an exact deadline is a `timestamptz` column. At most one of them is set (database check) |
| 8 | The single settings row `app_settings` (id 1) holds the user's IANA time zone, default `UTC`. `GET` and `PUT /api/v1/settings` read and change it. Overdue is computed at read time from the clock and that zone. A zone that `zoneinfo` does not know is rejected |
| 9 | HTTP clients always create tasks with source `manual`. Source `ai` is reserved for use cases called by the AI layer in M7 |
| 10 | The API is REST under `/api/v1`. Timestamps are ISO 8601 with offset. A deadline is `{"kind": "date", "value": "2026-12-01"}` or `{"kind": "datetime", "value": "2026-12-01T21:59:00Z"}`. A schedule is `{"start": ..., "end": ...}`. JSON `null` clears an optional field in a patch. An omitted field is left unchanged. A patch with no field besides `version` is rejected (422) |
| 11 | Lifecycle actions are sub-resources: `start` (to in_progress), `plan` (to planned), `complete`, `cancel` (optional `reason`), and `reopen` (to planned). `plan` and `reopen` both target planned, and the domain decides which source statuses are legal. Each carries `version` in the JSON body. A delete carries `version` as a query parameter |
| 12 | Problem+json bodies gain a `result` member with one of: `validation_failed`, `rejected`, `conflict`, `not_found`, `failed`. A domain validation failure also carries `field`. A stale version also carries `current_version` when known |
| 13 | Error mapping: `not_found` 404, `stale_version` 409, `invalid_transition` 409 (result `rejected`), `validation_failed` 422, `invalid_cursor` 422, `idempotency_key_reuse` 422 (result `rejected`), `idempotency_in_progress` 409 (result `conflict`), anything unexpected 500 with code `failed` |
| 14 | `POST /api/v1/tasks` accepts an optional `Idempotency-Key` header (1 to 200 printable ASCII characters). The fingerprint is the SHA-256 of the canonical JSON of the validated body. The same key and fingerprint return the original task as it currently exists with HTTP 200 and `Idempotency-Replayed: true`. The same key with a different body returns 422 `idempotency_key_reuse`. If the original task was deleted, the key counts as used and the request is rejected the same way. There is no expiry in M2 |
| 15 | Lists use keyset pagination with an opaque cursor (base64url of JSON). `limit` defaults to 100, minimum 1, maximum 200. Tasks are ordered by `created_at` descending then `id` descending. Status events are ordered by `occurred_at` descending then `id` descending. A malformed cursor is `invalid_cursor` (422) |
| 16 | Task filters: `status` (repeatable), `category`, `priority`. There is no overdue filter. Every task in a response carries a computed `is_overdue` |
| 17 | API schemas validate shape and types. The domain validates business rules. A `DomainValidationError` becomes 422 `validation_failed` with its `field` |
| 18 | OpenAPI is exported by `lifespace.openapi_export` to `apps/web/src/shared/api/openapi.json`. Types are generated into `apps/web/src/shared/api/schema.d.ts` with `npx --yes openapi-typescript@7.13.0`. That package declares TypeScript 5 as a peer, the project uses TypeScript 6 (ADR in the blueprint), so it runs through `npx` with its own copy and is not a project dependency. Both generated files are committed. A drift check fails when they differ from a fresh export |
| 19 | Database checks mirror the domain invariants (status values, estimate above zero, deadline columns exclusive, schedule both-or-none and ordered, completed and canceled timestamps match the status, version at least 1, updated not before created, non-blank title). Checks back the application rules and never replace them |
| 20 | Input limits (added after the M2 review of 2026-11-19, they apply to domain objects and therefore to every caller). Instants must lie in [1970-01-01T00:00:00Z, 3000-01-01T00:00:00Z). Date-only deadlines must lie in [1970-01-01, 2999-12-31]. A title is 1 to 500 characters after trimming, a description at most 20,000, a cancellation or transition reason at most 1,000. Text must not contain the NUL character or a lone surrogate (PostgreSQL cannot store them). `estimate_minutes` and every `version` are at most 2,147,483,647 (the storage limit). A violation is a `DomainValidationError`, HTTP 422 `validation_failed` with its `field`, and never a 500 |
| 21 | An overflowing datetime conversion is a validation failure, not an unhandled `OverflowError`. `as_instant` converts it to `DomainValidationError` |
| 22 | A use case builds the response view before it commits, so a failure while rendering can never leave a committed change behind |
| 23 | The SQLAlchemy engine hides statement parameters (`hide_parameters=True`) so database errors never put task content into logs. Request bodies and SQL parameters are never logged |
| 24 | Cursor decoding is total: any malformed input, including deeply nested JSON, an out-of-range instant, or a non-ASCII string, is `invalid_cursor` (422), never a 500 |
