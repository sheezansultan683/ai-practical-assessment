# Database setup notes

## Engine

Core uses **SQLite**. The only configuration point is `DATABASE_URL` (see
repo-root `.env.example`).

Django settings must:

1. Read the engine/location from `DATABASE_URL` only (no second hard-coded DB
   block).
2. For SQLite, resolve the file path against **`BASE_DIR`**, not the process
   cwd — always `BASE_DIR / "database" / "tickets.db"`. A relative
   `sqlite:///./database/tickets.db` would otherwise create
   `src/database/tickets.db` if you run `manage.py` from `src/`.

Switching to Postgres later is a URL change only (plus installing a Postgres
driver) — no model or query-code rewrite.

This folder is kept in git via `.gitkeep` because the `.db` file is ignored;
without the directory, SQLite fails with “unable to open database file” after
a clean clone.

## Create / migrate

From the project root, with the venv active and `.env` loaded:

```bash
python manage.py migrate
python manage.py seed
```

After migrate, `database/tickets.db` should exist under the repo (via
`BASE_DIR`). Restart the app process and confirm seeded data is still present.

## Dump schema (SQLite)

Do **not** use `pg_dump`. Capture the schema with:

```bash
sqlite3 database/tickets.db .schema > database/schema.sql
```

Optional: include indexes and other objects the same way (`.schema` already
emits `CREATE TABLE` / `CREATE INDEX` / etc.).

To inspect interactively:

```bash
sqlite3 database/tickets.db
sqlite> .tables
sqlite> .schema tickets_ticket
```

## Tests vs app DB

The test suite must **not** point at `database/tickets.db`. Django / pytest-django
create and tear down a separate test database (`settings.test`). Running tests
must leave seeded app data intact.

## Docker / Postgres

Docker Compose for Postgres is a Stretch item that was **deferred on purpose
as a time call**, not because it is unfit. When revisited:

1. Point `DATABASE_URL` at a Postgres URL.
2. Add a Postgres driver (e.g. `psycopg`) to requirements.
3. Optionally add Compose for local Postgres only — models/migrations stay as-is.

## Concurrent writes

SQLite locks the whole database on write. Contending ticket transitions are
more likely to raise `database is locked` than to silently lose an update.
That is the documented concurrency limitation for this delivery; row-level
`select_for_update()` belongs with a later Postgres move.
