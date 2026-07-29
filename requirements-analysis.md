# Requirement Analysis

**Source brief:** [project_requirement.txt]
**Stack:** Django 5 + Django REST Framework + SQLite (via `DATABASE_URL`) + SimpleJWT; React + Vite + TypeScript

---

## Selected Project Option

Support Ticket Management System (backend-heavy option). Mandatory Core, plus these Stretch
items: JWT authentication with protected routes and API authorization, OpenAPI documentation
via drf-spectacular, and reusable Cursor rules as project specs. Docker Compose / Postgres was
a Stretch option; it is **deferred on purpose as a time call**, not a technical rejection —
`DATABASE_URL` stays the single DB config point so Postgres is a later env-var swap.

---

## My Understanding

This is an internal tool for a support team. A problem becomes a ticket, and the ticket moves
through fixed stages until it is done or dropped. The users are colleagues, not customers, so
the brief seeds them and skips signup.

The status rules are enforced, not suggested. If any status could jump to any other, "Resolved"
stops meaning anything and no report built on it can be trusted. So I keep the transition rules
in one place on the backend and let the API tell the UI which moves are legal — the rules should
never exist in two codebases.

"Self-generated tickets" only works if the app knows who you are, so I added JWT even though
auth is optional. Without login, `created_by` is just something the client types in.

The hard part was what the brief leaves out. Five lines of transitions raised six questions they
do not answer, and I nearly missed search because it sits in the general requirements rather
than my project's feature list.

---

## Functional Requirements

Numbered for traceability. Each item maps to an entry in `acceptance-criteria.md` and, where
automated, to a named test in `tests/`.

### Authentication and identity

| ID | Requirement |
|----|-------------|
| FR-1 | A seeded user authenticates with **email + password** and receives an access token and a refresh token. |
| FR-2 | Every ticket and comment endpoint rejects unauthenticated requests with HTTP 401. |
| FR-3 | The API returns the authenticated user's own profile (id, name, email, role). |
| FR-4 | An expired access token can be exchanged for a new one using the refresh token, without re-entering credentials. |
| FR-5 | Logout invalidates the refresh token so it cannot be reused. |
| FR-6 | The API returns the list of seeded users, for use as an assignee picker in the UI. |

### Ticket creation

| ID | Requirement |
|----|-------------|
| FR-7 | An authenticated user creates a ticket with title, description, priority, and an optional assignee. |
| FR-8 | A newly created ticket always has status `OPEN`. |
| FR-9 | `created_by` is derived from the authenticated user and is ignored if supplied by the client. |

### Listing, filtering, search

| ID | Requirement |
|----|-------------|
| FR-10 | An authenticated user can list all tickets. |
| FR-11 | The ticket list can be filtered by status. |
| FR-12 | The ticket list can be filtered by priority. |
| FR-13 | The ticket list can be filtered by assignee. |
| FR-14 | The ticket list supports a free-text `q` search matching title **or** description, case-insensitively. |
| FR-15 | The ticket list is ordered by creation time, newest first, when no ordering is requested. |

### Ticket detail and field updates

| ID | Requirement |
|----|-------------|
| FR-16 | A user can view a single ticket with its full field set and its comments. |
| FR-17 | The ticket detail response includes `allowed_transitions` — the statuses this ticket may legally move to next. |
| FR-18 | A user can update title, description, priority, and assignee on a non-terminal ticket. |
| FR-19 | Status cannot be changed through the field-update endpoint; an attempt is rejected with a clear error. |
| FR-20 | Field updates on a `CLOSED` or `CANCELLED` ticket are rejected. |
| FR-21 | `updated_at` reflects the most recent modification to the ticket. |

### Status transitions

| ID | Requirement |
|----|-------------|
| FR-22 | Status changes happen through a dedicated transition endpoint, separate from field updates. |
| FR-23 | Exactly these transitions succeed: `OPEN→IN_PROGRESS`, `OPEN→CANCELLED`, `IN_PROGRESS→RESOLVED`, `IN_PROGRESS→CANCELLED`, `RESOLVED→CLOSED`. |
| FR-24 | Any other transition, including a same-status transition, is rejected with HTTP 409. |
| FR-25 | When a transition is rejected, the ticket's status in the database is unchanged. |
| FR-26 | The rejection response names the current status, the attempted status, and the legal alternatives. |

### Comments

| ID | Requirement |
|----|-------------|
| FR-27 | A user can add a comment to a ticket in **any** status, including `CLOSED` and `CANCELLED`. |
| FR-28 | Comment `created_by` is derived from the authenticated user. |
| FR-29 | Comments are append-only: there is no edit or delete. |

### CSV export

| ID | Requirement |
|----|-------------|
| FR-30 | A user can export, as CSV, all tickets where `created_by` is the authenticated user. |
| FR-31 | The export contains ticket core fields plus a comment count per ticket. |
| FR-32 | An export requested by a user who has created no tickets returns a CSV containing only the header row, not an error. |
| FR-33 | The export never includes tickets created by other users, regardless of any client-supplied parameter. |

### Validation and error handling

| ID | Requirement |
|----|-------------|
| FR-34 | Missing or malformed required fields are rejected by the backend with field-level error detail. |
| FR-35 | Every error response across the API uses one consistent envelope shape, including DRF's own validation errors. |
| FR-36 | The UI renders field validation errors inline against the offending field. |
| FR-37 | The UI renders a rejected transition as a human-readable sentence, not a raw error code. |
| FR-38 | The UI has a distinct visible state for loading, empty results, and network failure. |

---

## Non-Functional Requirements

None of these are stated in the brief; all are inferred from it or from the "What Good Looks
Like" criteria.

| ID | Requirement |
|----|-------------|
| NFR-1 | All data persists in SQLite at `REPO_ROOT / "database" / "tickets.db"` (engine/location from `DATABASE_URL` only; path resolved against repository root, not `src/` / cwd) and survives an application restart. |
| NFR-2 | The backend is the sole authority on validation and on the transition rules. The frontend may not be trusted to enforce either. |
| NFR-3 | The transition table has exactly **one** definition in the codebase. The frontend receives legal transitions from the API and never hardcodes them. |
| NFR-4 | Business rules live in a service layer, not in serializers or views, so a second caller (management command, test) gets the same enforcement. |
| NFR-5 | The project runs from a clean `git clone` by following the README only, on Linux and macOS. |
| NFR-6 | No secrets are committed. Every secret is read from the environment with no fallback default, so a missing value fails loudly. |
| NFR-7 | Seed data covers all five statuses, all priorities, and multiple `created_by` users, so every code path is demonstrable without manual setup. |
| NFR-8 | The seed command is idempotent and transactional — running it twice is safe. |
| NFR-9 | Filtered and searched list queries are backed by indexes on the columns they filter. |
| NFR-10 | API endpoints are documented via OpenAPI, generated from the code rather than maintained by hand. |
| NFR-11 | The state-machine rules are covered by integration tests over the complete transition matrix, not a sampled subset. |

---

## Assumptions

Decisions taken where the brief is silent. Each is a choice, not a requirement — recorded so
that a reviewer can disagree with the reasoning rather than guess at it.

| # | Topic | Decision | Reasoning |
|---|-------|----------|-----------|
| A-1 | Authentication | Implement JWT auth (SimpleJWT) across the whole API, even though the brief marks auth optional. | The CSV requirement says "self-generated tickets". Without an authenticated identity, "self" has no definition and `created_by` would be a client-supplied claim. Auth is what makes that requirement honest. |
| A-2 | User management | Seeded users only. No registration, no user CRUD, no user-management UI. | The brief states `User (seeded only — no user-management UI required)`. |
| A-3 | Login credential | Email, not username. Custom user model with `USERNAME_FIELD = "email"`. | The brief's `User` entity is id/name/email/role — there is no username field to log in with. |
| A-4 | "self-generated" | `created_by = request.user`. Not created-or-assigned. | Plainest reading of "self-generated": the user generated the ticket. Assignment is someone else's action. |
| A-5 | Terminal states | `CLOSED` and `CANCELLED` are terminal. No reopen path exists. | The brief's transition list is an allow-list with no outgoing edges from either. Adding a reopen path would be inventing a transition the brief does not grant. Flagged as a product question — see C-1. |
| A-6 | Comments on terminal tickets | Allowed. | Comments are append-only history and do not mutate ticket state. Blocking them would destroy the ability to annotate a closed ticket after the fact, which is a normal support workflow. |
| A-7 | Field edits on terminal tickets | Rejected. Title, description, priority, and assignee are frozen once a ticket is `CLOSED` or `CANCELLED`. | A terminal ticket is a settled record; silently editable history undermines the point of enforcing a lifecycle. **This rule goes beyond the brief**, which says "A user can update ticket fields and reassign" with no lifecycle condition. Flagged as C-2. |
| A-8 | Initial status | Always `OPEN` on create. The client cannot choose a starting status. | Every allowed transition path in the brief originates at `OPEN`, so any other starting status would be unreachable and untransitionable. |
| A-9 | Status change mechanism | A dedicated transition endpoint, separate from the generic field-update endpoint. | A lifecycle transition is a different operation from a field edit: different validation, different authority, different audit meaning. Sharing one code path would blur both. |
| A-10 | Invalid transition status code | HTTP **409 Conflict**. | DRF already returns 400 for schema validation failures. Reusing 400 would leave the frontend string-matching message bodies to distinguish "your input is malformed" from "your input is valid but the lifecycle forbids it". 409 states that the resource's current state is the obstacle. |
| A-11 | Same-status transition | `OPEN → OPEN` is rejected as an invalid transition (409), not treated as a no-op. | It is not in the allow-list. Treating it as a success would mean the API sometimes reports a state change that did not occur. |
| A-12 | Ticket visibility | All authenticated users can list and view all tickets. | The brief's acceptance criterion is "A user can view **all** tickets from the database". Ownership scoping applies only to the export. Flagged as C-3. |
| A-13 | Roles | `role` is stored on the user and returned by the API, but Core does not gate any endpoint on it. | The brief lists role-based access under Stretch, and gating Core features on roles would risk making acceptance criteria unreachable for a seeded user of the wrong role. |
| A-14 | Wire format | All JSON keys are `snake_case` (`created_by`, `assigned_to`, `allowed_transitions`, `created_at`, `updated_at`, `ticket_id`). Status and priority are Django `TextChoices` with uppercase stored values (`IN_PROGRESS`) and human display labels ("In Progress"). Stored values are what the API sends and receives. | Snake_case matches Django/DRF and keeps one naming style across docs, API, and models. Uppercase enum constants are unambiguous over the wire; labels belong in the UI. |
| A-15 | CSV contents | Ticket core fields plus a per-ticket comment count. Comment text is not flattened into the export. | "Details" is undefined in the brief. Concatenating multi-line comment bodies into a single CSV cell produces a file that is awkward to read and fragile to parse. A count conveys activity without that cost. |
| A-16 | Pagination | Page-number pagination on the ticket list, default page size 20. | "View all tickets" is satisfiable with pagination, and an unbounded list endpoint is a habit worth not forming. Small enough seed data that it is visible either way. |
| A-17 | Default sort | Newest first (`-created_at`). | Not specified in the brief. Most recent activity is the useful default for a ticket queue. |
| A-18 | Search scope | `q` matches title **or** description, case-insensitive substring (`icontains`), with no special index. | The brief requires "one working search or filter capability". At seed scale a sequential scan is irrelevant. Full-text / trigram (e.g. after a Postgres switch) is the upgrade path, not built now. |
| A-19 | Deletes | No ticket or comment deletion, hard or soft. | Not in the brief's feature list, and deletion interacts awkwardly with an audit-bearing lifecycle. |
| A-20 | Repository layout | Brief Required Repository Structure at repo root: lifecycle docs, `src/backend` + `src/frontend`, `tests/`, `database/`, `ai-prompts/`, `tool-specific/`. Application code only under `src/`. | The brief contradicts itself on `/artifacts` vs root; the structure diagram is the more specific instruction. Flagged as C-7. |
| A-21 | Token storage | Access token held in memory; refresh token in `localStorage`. | A refresh token in an `httpOnly` cookie is more secure but requires custom views and CSRF handling. Accepted trade-off for an internal exercise, recorded as a known limitation rather than left unexamined. |
| A-22 | Database | SQLite file at `REPO_ROOT / "database" / "tickets.db"`, configured through `DATABASE_URL` with the SQLite path resolved against **repository root** (parent of `src/`), not Django `BASE_DIR` under `src/backend/` and not cwd. `database/.gitkeep` is committed so the folder exists after clone. No Docker Compose / Postgres in this delivery. | Brief asks for a `database/` folder at repo root. One env var keeps a later Postgres move as config-only. If resolved against `BASE_DIR` inside `src/`, the file would land under `src/`. Docker Stretch dropped as a **time call**, not because Compose is unfit. SQLite locks the whole DB on write, so the documented concurrent-transition race surfaces as `database is locked` rather than a silent lost update. Tests under `tests/` use a separate Django test DB and must not wipe the app file. |

---

## Clarifications (questions for a product owner)

Questions where the decision is genuinely not the developer's to make. Each has been resolved
provisionally so that work could continue; each would be confirmed before a real release.

**C-1 — Should a Closed ticket ever be reopenable?**
The transition list gives `CLOSED` and `CANCELLED` no outgoing edges. Every ticket system I
have used has some reopen path, so this reads as plausibly an omission rather than a rule.
*Proceeding on:* strictly terminal (A-5). *Impact if wrong:* two new transitions, plus a UI
affordance, plus tests — a small change, but it changes what "resolved" means to the business.

**C-2 — Should ticket fields be editable after a ticket reaches a terminal state?**
The brief says "A user can update ticket fields and reassign" with no lifecycle condition
attached. I have chosen to freeze fields on terminal tickets (A-7), which is stricter than
what was asked. *Proceeding on:* frozen. *Impact if wrong:* remove one guard clause.

**C-3 — Should the ticket list show all tickets, or only the requesting user's?**
The acceptance criterion says "view all tickets", but the export is explicitly scoped to the
user's own. That asymmetry may be deliberate or may be an oversight. *Proceeding on:* list is
global, export is scoped (A-12).

**C-4 — Who is permitted to transition a ticket, and who may reassign it?**
The brief specifies no authority rules for either. Realistically, a requester probably should
not be able to mark their own ticket Resolved. *Proceeding on:* any authenticated user may do
both (A-13). *Impact if wrong:* role checks on two endpoints.

**C-5 — Should the history of status changes be retained, or only the current status?**
The `Ticket` entity has a single `status` field and no history is requested. For a lifecycle
that is being deliberately enforced, not recording who moved a ticket and when seems like a
gap. *Proceeding on:* current status only, with status history recorded as a future improvement.

**C-6 — Is an assignee required at creation time, or is a ticket allowed to sit untriaged?**
The brief lists assignee without stating whether it is nullable. *Proceeding on:* optional
at creation, assignable later (`assigned_to` may be null).

**C-7 — Where should the lifecycle documents live?**
The brief specifies both `/artifacts` and repository root in different places. *Proceeding on:*
repository root, per the Required Repository Structure (A-20).

---

## Edge Cases

| Case | Expected behaviour |
|------|--------------------|
| Transition to the same status (`OPEN → OPEN`) | 409. Not in the allow-list. |
| Transition from a terminal status (`CLOSED → OPEN`) | 409, status unchanged. |
| Transition skipping a step (`OPEN → RESOLVED`) | 409, status unchanged. |
| Transition to a status string that is not a valid enum value | 400 — this is malformed input, not a lifecycle conflict. |
| Two concurrent requests transitioning the same ticket | Under SQLite, writers take a DB-wide lock — contending transitions typically fail with `database is locked` rather than a silent lost update. Still documented as a known limitation (not row-level locking / `select_for_update`). Fix path when on Postgres: `select_for_update()` inside the transaction. Decided deliberately, not overlooked. |
| `PATCH` attempting to set `status` | Rejected with a clear message pointing at the transition endpoint. |
| Field update on a `CLOSED` ticket | 409, no fields modified. |
| Comment added to a `CANCELLED` ticket | Succeeds (A-6). |
| Ticket created with an empty or whitespace-only title | 400 with a field-level error. Whitespace is stripped before the length check. |
| Ticket created with a title over the maximum length | 400 with a field-level error naming the limit. |
| Ticket created with an unknown priority value | 400 with a field-level error listing the valid choices. |
| Client supplies `created_by` in the request body | Ignored. The value is taken from the authenticated user (FR-9). |
| Client supplies `assigned_to` pointing at a nonexistent user id | 400 with a field-level error. |
| Export requested by a user who has created no tickets | 200 with a CSV containing only the header row (FR-32). |
| Export requested with a query parameter attempting to widen the scope | Ignored. Scope is always the authenticated user (FR-33). |
| Ticket title containing a comma, quote, or newline in the CSV export | Correctly quoted and escaped by the CSV writer, so the file stays parseable. |
| Any request with no `Authorization` header | 401, consistent envelope. |
| Request with an expired access token | 401; the frontend attempts one refresh and retries, then redirects to login if that fails. |
| Refresh token reused after logout | 401 — the token is blacklisted. |
| Requesting a ticket id that does not exist | 404, consistent envelope. |
| Requesting a ticket id that is not an integer | 404 from URL resolution, in the same envelope. |
| Search with an empty `q` parameter | Treated as no search filter, not as a search for the empty string. |
| Search string containing SQL metacharacters (`%`, `_`, `'`) | Treated as literal text. The ORM parameterises the query; no injection and no accidental wildcard. |
| Filter with an invalid status value | 400 listing the valid choices, rather than silently returning everything. |
| Page number beyond the last page | 404 from the paginator, in the consistent envelope. |
| Database unavailable | 500 in the consistent envelope, no stack trace leaked to the client, `DEBUG=False` verified in the non-dev settings. |
| Seed command run twice | Succeeds with no duplicates (NFR-8). |
| A user is deleted while owning tickets | Blocked. `on_delete=PROTECT` on `created_by` — deleting a user must not destroy ticket history. |

---

## Traceability

`FR-*` and `NFR-*` identifiers carry forward: `acceptance-criteria.md` cites them per checklist
item, and test names reference them, so any single requirement can be traced from brief →
analysis → criteria → test.
