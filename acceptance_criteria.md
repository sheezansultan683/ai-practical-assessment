# Acceptance Criteria

Checklist for verifying the Support Ticket Management System against
[`requirements_analysis.md`](requirements_analysis.md). Each item cites `FR-*` /
`NFR-*` / `A-*` for traceability. Check off when verified.

Items marked **(brief)** are the brief's own 11 Core Acceptance Criteria from
[`project_requirement.txt`](project_requirement.txt) — none should be dropped.

## Verification legend

| Tag | Meaning |
|-----|---------|
| `[int]` | Integration test (API / DB) |
| `[unit]` | Unit test |
| `[ui]` | Manual UI check |
| `[cmd]` | Run a command (seed, migrate, compose, test suite) |
| `[insp]` | Inspect the repo / code / config |

An item may carry more than one tag when verification spans layers.

---

## Core

### Authentication and identity

- [ ] `[int]` `[ui]` Seeded user can log in with email + password and receives access + refresh tokens (`FR-1`)
- [ ] `[int]` Unauthenticated requests to ticket/comment endpoints return 401 (`FR-2`)
- [ ] `[int]` Authenticated user can fetch their own profile (id, name, email, role) (`FR-3`)
- [ ] `[int]` `[ui]` Expired access token can be refreshed without re-entering credentials (`FR-4`)
- [ ] `[int]` Logout invalidates the refresh token; reuse returns 401 (`FR-5`)
- [ ] `[int]` `[ui]` API returns seeded users for the assignee picker (`FR-6`)
- [ ] `[insp]` `[ui]` Frontend gates ticket routes behind login; access token in memory, refresh in `localStorage` (`A-21`)

### Tickets — create, list, detail, update

- [ ] `[ui]` `[int]` **(brief)** Authenticated user can create a ticket via the UI with title, description, priority, and optional assignee (`FR-7`)
- [ ] `[int]` Newly created ticket always has status `OPEN`; client cannot choose initial status (`FR-8`, `A-8`)
- [ ] `[int]` `created_by` is set from the authenticated user; client-supplied `created_by` is ignored (`FR-9`)
- [ ] `[ui]` `[int]` **(brief)** Authenticated user can list / view all tickets from the database (`FR-10`, `A-12`)
- [ ] `[int]` `[ui]` Ticket list can be filtered by status, priority, and assignee (`FR-11`, `FR-12`, `FR-13`)
- [ ] `[int]` `[ui]` Ticket list supports free-text `q` search on title or description, case-insensitive (`FR-14`)
- [ ] `[int]` Default list order is newest first (`FR-15`)
- [ ] `[int]` `[ui]` Ticket list uses page-number pagination with default page size 20 (`A-16`)
- [ ] `[insp]` Filter and search columns used by the list endpoint are backed by indexes (`NFR-9`)
- [ ] `[ui]` `[int]` **(brief)** User can open a ticket detail view with full fields and comments (`FR-16`)
- [ ] `[int]` `[ui]` Detail response includes `allowed_transitions` for the current status (`FR-17`, `NFR-3`)
- [ ] `[ui]` `[int]` **(brief)** User can update ticket fields and reassign (title, description, priority, assignee) on a non-terminal ticket (`FR-18`)
- [ ] `[int]` Status cannot be changed via the field-update endpoint (`FR-19`)
- [ ] `[int]` `[ui]` Field updates on `CLOSED` or `CANCELLED` tickets are rejected; UI disables the edit form (`FR-20`, `A-7`)
- [ ] `[int]` `updated_at` reflects the most recent ticket modification (`FR-21`)
- [ ] `[cmd]` `[ui]` **(brief)** Data persists in PostgreSQL and remains available after container/app restart (`NFR-1`)

### Status transitions

- [ ] `[int]` Status changes use a dedicated transition endpoint, separate from field updates (`FR-22`, `A-9`)
- [ ] `[int]` `[ui]` These transitions succeed: `OPEN→IN_PROGRESS`, `OPEN→CANCELLED`, `IN_PROGRESS→RESOLVED`, `IN_PROGRESS→CANCELLED`, `RESOLVED→CLOSED` (`FR-23`)
- [ ] `[int]` `[ui]` **(brief)** Status changes only through valid transitions; invalid ones are rejected (`FR-23`, `FR-24`)
- [ ] `[insp]` `[ui]` UI only offers actions from `allowed_transitions`; does not hardcode the allow-list (`NFR-2`, `NFR-3`)
- [ ] `[int]` `CLOSED` and `CANCELLED` are terminal; no reopen path (`A-5`)

### Comments

- [ ] `[ui]` `[int]` **(brief)** User can add a comment to a ticket (`FR-27`)
- [ ] `[int]` Comment can be added in any status, including `CLOSED` and `CANCELLED` (`FR-27`, `A-6`)
- [ ] `[int]` Comment `created_by` is derived from the authenticated user (`FR-28`)
- [ ] `[insp]` `[int]` Comments are append-only (no edit or delete endpoints) (`FR-29`, `A-19`)

### CSV export

- [ ] `[ui]` `[int]` **(brief)** User can export as CSV all self-generated tickets (`created_by` = authenticated user) with details (`FR-30`, `A-4`)
- [ ] `[int]` Export includes ticket core fields plus a per-ticket comment count (`FR-31`, `A-15`)
- [ ] `[int]` Export for a user with no tickets returns header-only CSV (200), not an error (`FR-32`)
- [ ] `[int]` Export never includes other users' tickets, regardless of client query params (`FR-33`)

### Seed and ops

- [ ] `[cmd]` `[insp]` Seed data covers all five statuses, all priorities, and multiple `created_by` users (`NFR-7`)
- [ ] `[cmd]` Seed command is idempotent; running twice creates no duplicates (`NFR-8`)

---

## Validation

- [ ] `[int]` **(brief)** Backend validation prevents invalid records — missing or malformed required fields rejected with field-level detail (`FR-34`)
- [ ] `[int]` Empty or whitespace-only title is rejected with a field-level error (`Edge`)
- [ ] `[int]` Title over maximum length is rejected with a field-level error naming the limit (`Edge`)
- [ ] `[int]` Unknown priority value is rejected with valid choices listed (`Edge`)
- [ ] `[int]` Unknown / invalid status enum string on transition is rejected with **400** (malformed), not 409 (`Edge`)
- [ ] `[int]` Invalid filter status value returns 400 listing valid choices, not an unfiltered list (`Edge`)
- [ ] `[int]` Nonexistent assignee id on create/update returns 400 with a field-level error (`Edge`)
- [ ] `[int]` Client-supplied `created_by` is ignored; value always comes from `request.user` (`FR-9`)
- [ ] `[insp]` Backend is the sole authority on validation; frontend is not trusted to enforce it (`NFR-2`)
- [ ] `[insp]` Business rules live in a service layer, not only in serializers/views (`NFR-4`)

---

## Error Handling

- [ ] `[int]` Every API error uses one consistent envelope shape, including DRF validation errors (`FR-35`)
- [ ] `[int]` Invalid lifecycle transition returns **409**; ticket status in the DB is unchanged (`FR-24`, `FR-25`, `A-10`)
- [ ] `[int]` Transition rejection body names current status, attempted status, and legal alternatives (`FR-26`)
- [ ] `[int]` Same-status transition (e.g. `OPEN→OPEN`) returns 409 (`A-11`)
- [ ] `[int]` Skip / reopen / terminal-outgoing transitions return 409 (`Edge`)
- [ ] `[int]` Field update attempting to set `status` is rejected with a clear pointer to the transition endpoint (`FR-19`)
- [ ] `[int]` Field update on `CLOSED`/`CANCELLED` returns 409; no fields modified (`FR-20`)
- [ ] `[int]` Missing `Authorization` header returns 401 in the consistent envelope (`FR-2`)
- [ ] `[int]` Nonexistent ticket id returns 404 in the consistent envelope (`Edge`)
- [ ] `[ui]` UI shows field validation errors inline against the offending field (`FR-36`)
- [ ] `[ui]` UI shows a rejected transition as a human-readable sentence, not a raw code (`FR-37`)
- [ ] `[ui]` UI has distinct visible states for loading, empty results, and network failure (`FR-38`)
- [ ] `[ui]` On expired access token, frontend attempts one refresh + retry, then redirects to login (`Edge`, `A-21`)

---

## Testing

- [ ] `[cmd]` `[int]` **(brief)** State-machine integration tests pass — complete transition matrix: every valid edge succeeds (`FR-23`, `NFR-11`)
- [ ] `[int]` Integration tests prove every invalid transition is rejected with 409 and status unchanged (`FR-24`, `FR-25`, `NFR-11`)
- [ ] `[int]` Tests assert rejection payload includes current, attempted, and allowed transitions (`FR-26`)
- [ ] `[int]` Tests cover terminal field-freeze (PATCH on `CLOSED`/`CANCELLED` → 409) (`FR-20`)
- [ ] `[int]` Tests cover comment allowed on terminal tickets (`FR-27`)
- [ ] `[int]` Tests cover CSV scoped to authenticated creator only (`FR-30`, `FR-33`)
- [ ] `[int]` Tests cover unauthenticated access → 401 on protected endpoints (`FR-2`)
- [ ] `[int]` Tests cover pagination default page size 20 and page navigation (`A-16`)
- [ ] `[insp]` Transition allow-list has exactly one definition in the codebase (`NFR-3`)

---

## Documentation

- [ ] `[insp]` `requirements_analysis.md` is present at repository root and reflects locked decisions
- [ ] `[insp]` `acceptance_criteria.md` (this file) is present and cites `FR-*` / `NFR-*` for traceability
- [ ] `[insp]` Cursor rules exist under `.cursor/rules/` (`stack-and-conventions.mdc`, `ticket-lifecycle.mdc`)
- [ ] `[cmd]` `[insp]` README enables a clean clone → run on Linux/macOS without tribal knowledge (`NFR-5`)
- [ ] `[insp]` **(brief)** No secrets committed to the repo; `.env.example` documents required env vars with no real values (`NFR-6`)
- [ ] `[insp]` `[ui]` API is documented via OpenAPI generated from code (drf-spectacular) (`NFR-10`)
- [ ] `[cmd]` `[insp]` Docker Compose setup for PostgreSQL is documented and works from the README (`Stretch`)
- [ ] `[insp]` Known limitations called out where relevant (e.g. concurrent transition race; token storage trade-off)

---

## Brief coverage check (11/11)

| # | Brief criterion | Covered by |
|---|-----------------|------------|
| 1 | A user can create a ticket via the UI | Core → create |
| 2 | A user can view all tickets from the database | Core → list |
| 3 | A user can open a ticket detail view | Core → detail |
| 4 | A user can update ticket fields and reassign | Core → update |
| 5 | A user can add comments | Core → comments |
| 6 | Status changes only through valid transitions; invalid ones are rejected | Core → status transitions |
| 7 | Data remains available after restart | Core → persist |
| 8 | Backend validation prevents invalid records | Validation |
| 9 | No secrets committed to the repo | Documentation |
| 10 | User can export all self-generated tickets with details as csv | Core → CSV |
| 11 | State-machine integration tests pass | Testing |
