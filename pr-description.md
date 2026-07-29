# PR description (draft)

## Summary

Support Ticket Management System: Django 5 + DRF + SQLite (`DATABASE_URL`) +
SimpleJWT + drf-spectacular; React + Vite + TypeScript. Enforced ticket
lifecycle in a single backend service layer; JWT-gated Core API; CSV export of
self-generated tickets; OpenAPI from code; Cursor rules as project specs.

## Test plan

- [ ] `migrate` + idempotent `python manage.py seed` (app DB under `BASE_DIR / "database" / "tickets.db"`)
- [ ] Restart the app — data still present
- [ ] Test suite uses separate Django test DB; does not wipe seed data
- [ ] Full transition-matrix tests green
- [ ] Contract endpoints + JWT + CSV scoped to `request.user`
- [ ] UI: create / list / detail / update / comment / transitions from `allowed_transitions` / export
- [ ] Walk `acceptance_criteria.md` (brief 11/11)

## Future improvements

- **Docker Compose / Postgres** — Stretch item **dropped on purpose as a time
  call**, not a technical rejection. `DATABASE_URL` is already the single DB
  config point; pointing it at Postgres (and adding a driver) should need no
  application-code change. Models, migrations, CheckConstraints, and indexes
  stay engine-portable.
- Concurrent transitions: under SQLite, writers take a DB-wide lock, so the race
  shows up as `database is locked` rather than a silent lost update. On
  Postgres, consider `select_for_update()` inside the transition transaction.
- Status history / reopen path / role-gated endpoints — product clarifications
  C-1, C-4, C-5 if the brief expands.
- Stronger search (FTS / trigram) once volume outgrows `icontains`.
- Refresh token in `httpOnly` cookie instead of `localStorage` (A-21 trade-off).
