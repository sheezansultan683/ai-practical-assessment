# Candidate Information

| Field | Value |
|-------|-------|
| **Name** | Sheezan Sultan |
| **Role** | Senior Python Developer |
| **Primary technology stack** | Django 5, DRF, SimpleJWT, SQLite, React + Vite + TypeScript |
| **Primary AI tool** | Cursor |
| **Project option** | Support Ticket Management System (backend-heavy / Core + Stretch: JWT, OpenAPI, Cursor rules) |
| **Assessment start date** | 2026-07-26 |
| **Submission date** | 2026-07-26 |

## Project summary

Internal support ticket system: seeded users authenticate with JWT (email + password), then create, list, filter/search, view, update, comment on, and progress tickets through an enforced status state machine, plus CSV export of self-generated tickets. No user-registration or user-management UI. Business rules live in a backend service layer, the frontend consumes `allowed_transitions` from the API.

## Tools used

- **Cursor** — requirement analysis, planning, design docs, phased code generation, tests, debugging, and review
- **Python venv + pip** — Django 5, DRF, SimpleJWT, drf-spectacular, django-filter, pytest-django (`requirements.txt`)
- **SQLite** — persistence via `DATABASE_URL` → `database/tickets.db` (Django migrations)
- **pytest / pytest-django** — lifecycle matrix tests and API integration tests under `tests/`
- **npm / Vite** — frontend toolchain under `src/frontend/` (when present)

## Setup summary

Clone the repo, copy `.env.example` → `.env`, create a venv, and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd src/backend
python manage.py migrate
python manage.py seed
python manage.py runserver
```

API docs (when the server is running): [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)

Full run instructions: [README.md](README.md).
