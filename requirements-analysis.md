# Requirements Analysis — Support Ticket Management System

## Source

- Spec: [`project_requirement.txt`](project_requirement.txt)
- Stack: Django 5 + DRF + Postgres + SimpleJWT; React + Vite frontend

---

## Spec gaps identified

### Status state machine

The spec lists five allowed transitions and requires invalid ones to be rejected. It does **not** say:

| Gap | Implication |
|-----|-------------|
| Are Closed / Cancelled final? | No outgoing edges are listed; reopen is not specified |
| Can you comment on Closed / Cancelled? | Comments are a separate feature from status |
| Can you edit fields after Closed / Cancelled? | Field updates vs status are separate |
| How is status set on create? | Only transitions are listed; initial status is implied |
| Who may transition? | No role-based rules in core |

### CSV export vs auth

Acceptance requires: *“User can export all self-generated tickets with details as csv.”*

Auth is listed as stretch/optional in the original spec. Without identity, “self-generated” (`createdBy = current user`) is undefined.

### Other unspecified items

- Priority allowed values
- Exact CSV columns / what “details” means
- Whether list is all tickets vs own tickets only
- Soft-delete / delete ticket (not in features)
- Search (mentioned in business context, not in mandatory features)
- Error response shape (only “meaningful” UI errors required)

---

## Locked decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Auth | **Full-app JWT (SimpleJWT)** — login required for all ticket/comment APIs | Makes `createdBy` and CSV “self” well-defined; keeps create/comment honest |
| Users | Seeded only; login against seeded users; no user-management UI / no register | Matches core: “seeded only — no user-management UI required” |
| CSV “self” | Export tickets where `created_by = request.user` | Direct reading of “self-generated” once auth exists |
| Status graph | Exactly the 5 allowed transitions; **Closed** and **Cancelled** are terminal (no reopen) | Follow the allow-list literally; reopen would invent edges |
| Comments on terminal | **Allowed** | Append-only history; does not mutate the state machine |
| Field edits on terminal | **Rejected** (title, description, priority, assignee frozen) | Terminal status should be a stable record without reopen |
| Status on create | Always `Open`; status changes only via dedicated transition | Keeps create vs lifecycle separate; easier to test |
| List vs export | List = all tickets; export = current user’s tickets only | Acceptance: “view all tickets” vs “self-generated” export |

### Status state machine (enforced)

```text
Open        → In Progress
Open        → Cancelled
In Progress → Resolved
In Progress → Cancelled
Resolved    → Closed
```

- Closed and Cancelled have **no** outgoing transitions.
- Invalid transitions return **400** with a clear message; frontend surfaces them.

---

## Out of scope / pick-and-move-on defaults

| Item | Default |
|------|---------|
| Priority | `low` \| `medium` \| `high` |
| Roles | Stored on User; **not** used for RBAC in core |
| CSV columns | Ticket core fields + comment count (and/or concatenated messages as “details”) |
| Delete / soft-delete | Not implemented |
| Search | Not required for core (list is enough) |
| Swagger / Docker / user CRUD | Stretch only; not in this build |
| Registration | Not implemented; seeded users only |

---

## API surface sketch

All endpoints below (except token obtain/refresh) require `Authorization: Bearer <access>`.

### Auth

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/token/` | Obtain access + refresh (username/password of seeded user) |
| POST | `/api/token/refresh/` | Refresh access token |

### Users (read helpers)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/users/` | List seeded users (for assignee picker); authenticated |
| GET | `/api/me/` | Current user profile |

### Tickets

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/tickets/` | List all tickets |
| POST | `/api/tickets/` | Create; `status` forced to `Open`; `created_by` = `request.user` |
| GET | `/api/tickets/{id}/` | Detail (includes comments) |
| PATCH | `/api/tickets/{id}/` | Update title, description, priority, assignee only; **rejected** if status is Closed or Cancelled |
| POST | `/api/tickets/{id}/transition/` | Body: `{ "status": "<next>" }`; enforce allow-list |
| GET | `/api/tickets/export/` | CSV of tickets where `created_by = request.user` |

### Comments

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/tickets/{id}/comments/` | Add comment; allowed on any status including Closed/Cancelled; `created_by` = `request.user` |

---

## Domain rules summary

1. **Create** → status is always `Open`.
2. **Transition** → only the five edges above; otherwise 400.
3. **Update fields** → allowed only when status is not Closed/Cancelled.
4. **Comments** → allowed in all statuses.
5. **Export** → only tickets created by the authenticated user.
6. **List** → all tickets (authenticated users).

---

## Frontend expectations

- App-wide auth gate: login required; ticket routes need a valid access token.
- Store access/refresh; send `Authorization: Bearer`; refresh on expiry.
- Ticket list, create, detail (edit fields, legal next-status actions, comments).
- Disable field edit form when Closed/Cancelled; keep comment form.
- Export CSV button (authenticated download of own tickets).
- Show backend validation and invalid-transition errors clearly.

---

## Mandatory tests

Integration tests must prove:

- Valid transitions succeed.
- Invalid transitions are rejected.

---

## Implementation order

1. Scaffold Django + Vite + Postgres + env (no secrets in repo).
2. Models, migrations, user seed.
3. Auth (SimpleJWT) + protected CRUD + transition + comments + CSV.
4. State-machine integration tests.
5. React UI wired to API.
6. Manual acceptance pass against core criteria in `project_requirement.txt`.
