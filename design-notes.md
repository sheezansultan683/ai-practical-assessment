# Design Notes

## Architecture Overview (frontend, backend, database)

```text
Browser (React + Vite + TS)
    │  JSON (snake_case) + JWT Bearer
    ▼
Django / DRF API  (`src/backend/`)
    │  service layer (lifecycle rules)
    ▼
SQLite  (`database/tickets.db` via DATABASE_URL)
```

- **Frontend** (`src/frontend/`): login-gated UI; talks only to the API; does not own status rules.
- **Backend** (`src/backend/`): sole authority on validation and ticket lifecycle; JWT on protected routes.
- **Database**: SQLite file at repo-root `database/`; engine/location configured only through `DATABASE_URL` so a later Postgres switch is mostly config.

Supporting pieces: OpenAPI from drf-spectacular (`/api/docs/`), pytest suite under `tests/`, planning specs at repo root, Cursor rules under `.cursor/rules/`.

## Frontend Design

- React + Vite + TypeScript under `src/frontend/`
- Access token in memory; refresh token in `localStorage`; on `401` try one refresh + retry, then send to login
- Ticket routes are protected; assignee picker uses `/api/users/`
- List: filters (status, priority, assignee), `q` search, pagination, distinct loading / empty / error states
- Detail: show fields, comments, and **only** actions from `allowed_transitions` (never a hardcoded allow-list)
- Edit form disabled on `CLOSED` / `CANCELLED`; transition failures shown as a clear sentence
- CSV download calls `/api/tickets/export/`

## Backend Design

- Django 5 + DRF apps: `users`, `tickets`; settings `base` / `dev` / `test`
- Custom user: `USERNAME_FIELD = "email"`; seeded users only
- **Service layer** (`tickets/services.py`): single `ALLOWED_TRANSITIONS` table, `transition_ticket()`, `update_ticket_fields()`, create/comment helpers
- Views/serializers stay thin: validate input shape, call the service, return snake_case JSON
- Auth: SimpleJWT obtain / refresh / blacklist; `IsAuthenticated` on ticket, comment, profile, and user-list endpoints
- List filtering via django-filter; page size default 20 (max 100)
- CSV export always scoped to `created_by = request.user` (client query params cannot widen scope)

## Database Design

- Models: `User`, `Ticket`, `Comment` (see `data-model.md`)
- FKs: `created_by` PROTECT, `assigned_to` SET_NULL, comment→ticket CASCADE, comment author PROTECT
- Indexes: `status`, `priority`, `created_at` (+ FK indexes); no btree on title/description for `icontains`
- Check constraints for valid status, priority, and role values
- New tickets default to `OPEN`; status changes only through the transition path
- Migrations via Django; seed via `python manage.py seed` (idempotent)

## Validation Strategy

| Layer | Responsibility |
|-------|----------------|
| Serializers | Required fields, strip/whitespace, max lengths, enum choices, assignee exists |
| Service | Lifecycle: allow-list transitions, reject status on field update, freeze fields on terminal tickets |
| Database | Check constraints + FK `on_delete` as a last line of defence |

Client-supplied `created_by` / initial `status` on create are ignored. Unknown status strings on transition are validation errors (**400**); illegal edges are conflicts (**409**).

## Error Handling Strategy

One envelope for all API errors:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": { "title": ["This field may not be blank."] }
  }
}
```

| HTTP | Typical `error.code` |
|------|----------------------|
| 400 | `validation_error` (bad input / unknown enum) |
| 401 | `authentication_failed` |
| 404 | `not_found` |
| 409 | `invalid_transition`, `terminal_ticket_frozen` |

Transition `409` details include `current_status`, `attempted_status`, and `allowed_transitions`. The UI maps field `details` inline and shows lifecycle messages as readable text.

## Testing Strategy Link

See [`test-strategy.md`](test-strategy.md) for unit, service, API/integration, edge-case coverage, and intentional gaps.
