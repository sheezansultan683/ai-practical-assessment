# Debugging Notes

## Issue 1 — Missing `DJANGO_SECRET_KEY` on local `runserver`

### Problem

Running `python manage.py runserver` from `src/backend/` crashed with:

`KeyError: 'DJANGO_SECRET_KEY'`

Settings read secrets from the environment with no code defaults, so a bare terminal session had no values set.

### How I Investigated

Read the traceback → `config/settings/dev.py` imports `base.py` → `os.environ["DJANGO_SECRET_KEY"]`. Confirmed `.env.example` listed the keys but there was no loaded `.env` for the shell, and Django was not reading a dotenv file yet.

### How AI Helped

Cursor pointed at the exact settings line, suggested loading a repo-root `.env` with `python-dotenv`, and keeping “no fallback defaults” so missing keys still fail loudly.

### What I Validated

- Created a gitignored `.env` from `.env.example`
- Installed `python-dotenv` and confirmed `manage.py check` works from `src/backend/` without manual `export`
- Restarted the server and opened `/admin/`

### Final Fix

- `load_dotenv(REPO_ROOT / ".env")` at the top of `config/settings/base.py`
- Local `.env` with `DJANGO_SECRET_KEY`, `DATABASE_URL`, and `SEED_PASSWORD`
- `python-dotenv` added to `requirements.txt`

---

## Issue 2 — Server reload failed after dotenv change (`No module named 'dotenv'`)

### Problem

An already-running `runserver` auto-reloaded when `base.py` gained `from dotenv import load_dotenv`, then crashed because the package was not installed in the venv yet.

### How I Investigated

Checked the terminal traceback after the settings change; confirmed `pip` had not installed `python-dotenv` before the reload.

### How AI Helped

Installed the dependency into `.venv` and re-checked that settings import cleanly.

### What I Validated

`pip install python-dotenv` / `pip install -r requirements.txt`, then `manage.py check` succeeded.

### Final Fix

Install dependencies before relying on the new import; keep `python-dotenv` pinned in `requirements.txt`.

---

## Issue 3 — Port 8000 already in use

### Problem

A second `runserver` failed with `Error: That port is already in use` because an earlier process (or the user’s own terminal server) was still bound to 8000.

### How I Investigated

Tried starting another server; checked that something was listening on `127.0.0.1:8000`.

### How AI Helped

Identified the conflict and suggested stopping the existing process (Ctrl+C) or using another port.

### What I Validated

Used the existing healthy server, or restarted after freeing the port.

### Final Fix

Only one `runserver` at a time on 8000; otherwise `python manage.py runserver 8001`.
