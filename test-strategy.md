# Test Strategy

## Test Scope

Automated tests live under repo-root `tests/` and run with **pytest + pytest-django** against a **separate test database** (`config.settings.test`). They never write to `database/tickets.db`, so seed data stays intact.

Focus areas:

1. Custom user model behaviour
2. Ticket / comment model rules and FK behaviour
3. Status state machine (full transition matrix) in the service layer
4. HTTP API: auth, tickets, comments, CSV, error envelope, OpenAPI

Frontend UI checks are mostly manual against the running API (loading/empty/error states, transition buttons from `allowed_transitions`).

## Unit Tests

- **User model** (`tests/test_user_model.py`): email as identity, password hashing, superuser flags, unique email, role check constraint, activate/deactivate
- **Ticket / comment models** (`tests/test_ticket_models.py`): default `OPEN`, ordering, priorities/statuses, null assignee, PROTECT/SET_NULL/CASCADE deletes, status/priority check constraints
- **Lifecycle service** (`tests/test_ticket_lifecycle.py`): `allowed_transitions()`, successful edges, `update_ticket_fields()` on non-terminal tickets

These call models/services directly — no HTTP.

## Component Tests

No separate React component test runner in this delivery. UI behaviour is checked manually:

- Login and protected routes
- List filters / search / empty and error states
- Detail actions driven by `allowed_transitions`
- Edit form disabled on terminal tickets
- CSV download

Backend “components” under test are the **service layer** and **serializers** exercised via API tests rather than isolated frontend unit tests.

## API / Integration Tests

`tests/test_api.py` hits real URL routes with DRF’s `APIClient` and JWT:

- Login with email/password → access + refresh
- Unauthenticated ticket list → `401` with shared error envelope
- `/api/me/` and `/api/users/`
- Create ticket (ignores client `created_by` / `status`; always `OPEN`)
- List + filter + invalid filter → `400`
- Invalid transition → `409`, status unchanged; valid transition → `200`
- PATCH `status` → `400`; field PATCH on `CLOSED` → `409`
- Comment on terminal ticket → `201`
- CSV export scoped to current user; header-only when none; OpenAPI schema present

`tests/test_ticket_lifecycle.py` is the signature integration suite for the state machine **before** views existed, and still guards the service.

## Edge Case Tests

Covered explicitly:

| Edge case | Where |
|-----------|--------|
| Same-status / skip / reopen / terminal-outgoing transitions | Full 5×5 matrix in lifecycle tests |
| Unknown status string → validation path, not 409 | `test_unknown_status_string_is_malformed_not_conflict` |
| Status via field update | Service + API |
| Field freeze on `CLOSED` / `CANCELLED` | Service + API |
| Comment on terminal ticket | Model + API |
| CSV never includes other users’ tickets | API |
| Export with zero tickets → header only | API |
| Refresh reuse after logout/blacklist | API |
| Invalid role/status/priority at DB constraint | Model tests |
| Delete protections (creator/comment author PROTECT) | Model tests |

## Tests Not Covered (and why)

| Gap | Why |
|-----|-----|
| Full frontend E2E (Playwright/Cypress) | Time; Core acceptance for UI is satisfied by manual checks against a live API |
| Concurrent double-transition race | Documented limitation under SQLite (`database is locked`); not claimed as solved |
| Pagination beyond last page / every filter combination | Defaults and basic filter/search covered; exhaustive page matrix is low value at seed scale |
| Every OpenAPI field annotation | Schema smoke test only; contract lives in `api-contract.md` |
| Load / security penetration tests | Out of scope for this assessment |
| Role-based access matrix | Core does not gate on `role` (Stretch RBAC deferred) |
