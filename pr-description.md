# PR Description

## Summary

This PR adds a Support Ticket Management System. People can log in, create and update tickets, leave comments, move tickets through fixed statuses, search and filter the list, and download their own tickets as CSV. The backend is Django + DRF with SQLite. The frontend is React + Vite + TypeScript. Status rules live in one place on the backend.

## Features Implemented

- Login with email and password (JWT access + refresh tokens)
- List, create, view, and update tickets
- Filter by status, priority, and assignee; search title/description
- Status changes only through allowed transitions (invalid ones are rejected)
- Comments on any ticket, including closed or cancelled ones
- CSV export of tickets the logged-in user created
- Seeded demo users (no signup / user-management UI)
- OpenAPI docs at `/api/docs/`
- Cursor rules and planning docs for how the app should behave

## Technical Changes

- Backend under `src/backend/` (Django apps `users` and `tickets`)
- Custom user model that logs in with email
- Service layer for status transitions and field-update rules
- Shared API error shape for all failures
- JWT auth on ticket and user endpoints; token blacklist for logout
- Frontend under `src/frontend/` with protected routes
- Access token kept in memory; refresh token in `localStorage`
- UI uses `allowed_transitions` from the API (does not hardcode the state machine)

## Database Changes

- SQLite file at `database/tickets.db`, configured only via `DATABASE_URL`
- Tables for users, tickets, comments, and JWT blacklist
- Indexes on status, priority, and created_at
- Check constraints for valid status, priority, and role values
- Idempotent seed command: `python manage.py seed`
- No Docker / Postgres in this delivery (on purpose, as a time call)

## Testing Done

- Full status transition matrix tests (valid succeed, invalid rejected, status unchanged)
- Tests for frozen fields on closed/cancelled tickets
- API tests for login, 401 without token, create/list/detail, bad transitions (409), comments, and CSV scope
- Local checks: migrate, seed twice (no duplicates), runserver, OpenAPI docs
- Frontend exercised against the running API for login and ticket flows

## AI Usage Summary

Cursor was used to turn the brief into requirements, acceptance criteria, API contract, data model, and implementation plan, then to build the app in small steps (scaffold → models/seed → transition service → API/JWT → frontend). I reviewed diffs, ran migrate/seed/tests locally, and kept or rejected AI suggestions against the locked rules.

## Screenshots / Demo Notes

- Backend: `python manage.py runserver` → http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/api/docs/
- Frontend: run the Vite app under `src/frontend/` (see README)
- Demo login after seed: `priya.nair@example.com` / `SeedPass!23` (also james and sara with the same password)
- Try: create a ticket → move Open → In Progress → try an invalid jump (should fail clearly) → add a comment → export CSV

## Known Limitations

- Docker Compose / Postgres Stretch was skipped on purpose for time; switching later should be mostly a `DATABASE_URL` change
- Under SQLite, heavy concurrent writes can show `database is locked` instead of a silent lost update
- No reopen path from Closed or Cancelled (follows the brief allow-list)
- No status history table; only the current status is stored
- Refresh token in `localStorage` is a known trade-off for this exercise
- Roles are stored and returned but do not gate Core endpoints

## Future Improvements

- Add Docker Compose + Postgres when time allows
- Use `select_for_update()` on transitions after moving to Postgres
- Optional reopen / status history if product asks for it
- Stronger search (full-text) if the ticket volume grows
- Move refresh tokens to httpOnly cookies for better security
