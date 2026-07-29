# Support Ticket Management System

Internal support ticket app: log in, create and update tickets, comment, filter/search, move tickets through enforced status transitions, and export your own tickets as CSV.

**Stack:** Django 5 + DRF + SimpleJWT + SQLite · React + Vite + TypeScript · pytest  
**Layout:** backend `src/backend/` · frontend `src/frontend/` · tests `tests/` · DB file `database/tickets.db`

---

## Prerequisites

- Python 3.12+
- Node.js 20+ (for the frontend)
- Git

No Docker required. Persistence is SQLite via `DATABASE_URL`.

---

## Quick start

### 1. Clone and configure env

```bash
git clone <repo-url>
cd ai-practical-assesment   # or your clone directory name

cp .env.example .env
# Edit .env: set a long DJANGO_SECRET_KEY (32+ characters recommended)
```

`.env` is gitignored. Required keys are documented in `.env.example`.

### 2. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd src/backend
python manage.py migrate
python manage.py seed
python manage.py runserver
```

- API: http://127.0.0.1:8000/
- OpenAPI / Swagger: http://127.0.0.1:8000/api/docs/
- Django admin: http://127.0.0.1:8000/admin/

The SQLite file is created at repo-root `database/tickets.db` (not under `src/`).

### 3. Frontend (second terminal)

```bash
cd src/frontend
npm install
npm run dev
```

App: http://127.0.0.1:5173/  

Vite proxies `/api` to Django on port 8000, so keep the backend running.

---

## Demo users (after `seed`)

| Email | Password | Role |
|-------|----------|------|
| `priya.nair@example.com` | `SeedPass!23` | AGENT |
| `james.okonkwo@example.com` | `SeedPass!23` | AGENT |
| `sara.chen@example.com` | `SeedPass!23` | ADMIN |

Password comes from `SEED_PASSWORD` in `.env`. Re-running `python manage.py seed` is safe (idempotent).

Optional admin user:

```bash
cd src/backend
python manage.py createsuperuser   # use an email, not a username
```

---

## Tests

From the repo root, with the venv active and `.env` present:

```bash
source .venv/bin/activate
pytest
```

Tests use Django’s separate test database (`config.settings.test`). They do **not** wipe `database/tickets.db`.

---

## Main API routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/token/` | Login (email + password) |
| POST | `/api/token/refresh/` | Refresh access token |
| POST | `/api/token/blacklist/` | Logout (blacklist refresh) |
| GET | `/api/me/` | Current user |
| GET | `/api/users/` | Assignee picker |
| GET/POST | `/api/tickets/` | List / create |
| GET/PATCH | `/api/tickets/{id}/` | Detail / update fields |
| POST | `/api/tickets/{id}/transition/` | Status change |
| POST | `/api/tickets/{id}/comments/` | Add comment |
| GET | `/api/tickets/export/` | CSV of self-generated tickets |

Full contract: [`api-contract.md`](api-contract.md).

---

## Project docs

| Doc | Purpose |
|-----|---------|
| [`requirements-analysis.md`](requirements-analysis.md) | Locked product decisions |
| [`acceptance-criteria.md`](acceptance-criteria.md) | Verification checklist |
| [`implementation-plan.md`](implementation-plan.md) | Phased build plan |
| [`design-notes.md`](design-notes.md) | Architecture overview |
| [`data-model.md`](data-model.md) | Schema / FKs / indexes |
| [`test-strategy.md`](test-strategy.md) | What we test and why |
| [`database/setup-notes.md`](database/setup-notes.md) | DB path and seed notes |
| [`candidate-info.md`](candidate-info.md) | Candidate / stack summary |

Cursor project rules live under [`.cursor/rules/`](.cursor/rules/).

---

## Known limitations

- Docker Compose / Postgres Stretch was deferred on purpose (time call). Switch later by changing `DATABASE_URL` and adding a Postgres driver.
- Under SQLite, concurrent writes may surface as `database is locked`.
- `CLOSED` / `CANCELLED` have no reopen path (brief allow-list).
- Refresh token is stored in `localStorage` (documented trade-off).
- `role` is stored and returned but does not gate Core endpoints.

---

## License / assessment

Built as a practical assessment project. Demo credentials are for local evaluation only — do not use them in production.
