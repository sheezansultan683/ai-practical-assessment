# Review Fixes

Fixes made after reviewing the plan and code:

1. Switched Core from Postgres/Docker to SQLite via `DATABASE_URL` (time call, not a tech rejection).
2. Locked app name to `users` (not `accounts`) and seed command to `python manage.py seed`.
3. SQLite path resolved from repo root so the DB file always lands in `database/tickets.db`.
4. Tests use a separate Django test DB — they do not wipe seed data.
5. Settings split: `base` / `dev` / `test`; local `.env` loaded with dotenv.
6. Transition rules live only in the service layer; UI uses `allowed_transitions` from the API.
7. Renamed docs to hyphenated names and `ai-promts/` → `ai-prompts/`.

Rejected on purpose: frontend hardcoding transitions, role gates on Core, ticket/comment delete, reopen from Closed/Cancelled.
