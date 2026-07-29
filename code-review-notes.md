# Code Review Notes

## AI-Assisted Review Summary

Asked Cursor to review against the plan and lifecycle rules: one transition allow-list on the backend, service-layer authority, JWT + consistent errors, CSV scoped to the logged-in user, no hardcoded transitions in the UI, and no secrets in the repo. AI was useful for spotting doc/code drift (Postgres vs SQLite, app naming, test DB vs seed DB) and for checking that invalid transitions leave status unchanged.

## My Review Observations

- Transition rules belong in `tickets/services.py` only; views should call the service, not re-encode the graph.
- Custom user must exist before the first migrate (`users_user`, not `auth_user`).
- SQLite path must resolve from repo root (`REPO_ROOT / database / tickets.db`), not from `src/backend` or the shell cwd.
- Tests must use Django’s separate test database so `pytest` does not wipe seed data.
- Frontend must render actions from `allowed_transitions`; duplicating the allow-list in React would be a fail.
- Env vars should fail loudly when missing; loading `.env` for local run is fine, hardcoding secrets is not.
- Seed command should be idempotent (`seed` twice → no duplicate tickets/users).

## Changes Made After Review

- Dropped Docker/Postgres from Core docs and plan; kept `DATABASE_URL` as the only DB config.
- Standardised on app name `users` (not `accounts`) and `python manage.py seed`.
- Settings split to `base` / `dev` / `test`; pytest points at `test`.
- Resolved SQLite against `REPO_ROOT`; committed `database/.gitkeep`.
- Added `python-dotenv` so local `runserver` works without manually exporting every variable.
- Built lifecycle service + full matrix tests before ticket API views.
- Confirmed CSV export only includes `created_by = request.user`.

## Suggestions Rejected (and why)

- **Keep Postgres + Compose in Core** — rejected as a time call; SQLite + `DATABASE_URL` still allows a later switch.
- **Hardcode transition buttons in the frontend** — rejected; breaks NFR that the API is the source of truth.
- **Run tests against the app’s `tickets.db`** — rejected; would wipe seed data on every suite run.
- **Gate Core endpoints on `role`** — rejected; Stretch RBAC must not block seeded agents from Core flows.
- **Add ticket/comment delete** — rejected; not in the brief and clashes with append-only history.
- **Add reopen from Closed/Cancelled** — rejected; not in the allow-list; would invent product rules.
- **Put secrets or real passwords in committed files** — rejected; demo password only via `.env` / `.env.example` placeholders.
