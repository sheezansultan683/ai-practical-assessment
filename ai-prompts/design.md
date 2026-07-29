# Frontend design overview
_Exported on 7/29/2026 at 22:06:33 GMT+5:30 from Cursor (3.13.10)_

---

**User**

@implementation-plan.md since the backend is done now, we can move forward with the FE implementation  you can check Next plan step: Task 6 — frontend under src/frontend/.  Before start to implementing can you give me overview of FE design

---

**Cursor**

> Auto routed to grok-4.5



I'll review Task 6 in the implementation plan and the existing frontend/docs so I can give you a clear FE design overview before we implement.

Here’s a concise FE design overview for **Task 6** before we scaffold `src/frontend/`.

## Goal

A thin React + Vite + TypeScript client under `src/frontend/` that talks to the live API. Backend owns validation and lifecycle; the UI only renders what the API returns and surfaces errors clearly.

## Screens & routes

| Route | Purpose |
|-------|---------|
| `/login` | Email + password → JWT |
| `/tickets` | List: filters, search, pagination, CSV export |
| `/tickets/new` | Create (title, description, priority, optional assignee) |
| `/tickets/:id` | Detail: fields, comments, transitions, edit |

All ticket routes are auth-gated. No registration, user CRUD, or role-based UI.

## Auth design (A-21)

```
Login → access token (memory) + refresh (localStorage)
         ↓
API call with Bearer
         ↓
401 → one refresh + retry
         ↓
still fail → clear tokens → /login
Logout → blacklist refresh + clear storage
```

## Suggested layout

```
src/frontend/
  src/
    api/          # thin typed client (snake_case as-is)
    auth/         # token store, refresh interceptor, AuthProvider
    pages/        # Login, TicketList, TicketCreate, TicketDetail
    components/   # filters, pagination, forms, transition buttons
    types/        # mirrors API contract
```

Keep it flat — no heavy state library unless needed. One API module + React Router is enough.

## Page behavior

**List**
- Filters: `status`, `priority`, `assigned_to`
- Search: `q` (title/description)
- Pagination: page size 20
- States: loading / empty / network error (FR-38)
- CSV: trigger `GET /api/tickets/export/` (download blob; scoped to current user by backend)

**Create**
- Fields only; no status picker (always `OPEN` on server)
- Assignee from `GET /api/users/`
- Inline field errors from envelope `details` (FR-36)

**Detail**
- Show full ticket + comments
- Edit form: title, description, priority, assignee — **disabled** when status is `CLOSED` or `CANCELLED`
- Transition buttons: **only** from `allowed_transitions` (empty array → no buttons)
- Comments: always allowed (including terminal)
- Rejected transition: human sentence from 409 payload (`current` / `attempted` / `allowed`) — not raw codes (FR-37)

## Hard rules (do not break)

1. **Never hardcode the transition matrix** — map buttons from `allowed_transitions` only  
2. **Never change status via PATCH** — only `POST …/transition/`  
3. **Consume `snake_case` as-is** — no camelCase API layer that invents a second contract  
4. **Backend is authority** — client-side checks are UX only; always handle 400/409 from the API  
5. **No delete** for tickets or comments  

## Error UX mapping

| API | UI |
|-----|-----|
| 400 + field `details` | Inline under the field |
| 409 transition | Banner/sentence: can’t go X→Y; allowed are … |
| 409 terminal PATCH | Disable form; show why if attempted |
| Network failure | Distinct failure state (not empty list) |
| 401 after refresh fail | Redirect to login |

## Visual approach

This is an **internal tool**, not a marketing page: clear hierarchy, readable forms/tables, status/priority labels (e.g. “In Progress” for `IN_PROGRESS`). Keep styling simple and consistent — Vite default + light CSS/modules is fine unless you want something more polished later.

## Build order (when we implement)

1. Scaffold Vite + React + TS  
2. Auth shell (login, token store, protected routes, 401 refresh)  
3. List + filters + pagination + empty/loading/error  
4. Create + detail + comments  
5. Edit (with terminal disable) + transitions from API  
6. CSV download  

---

If this matches what you want, say the word and we start with the Vite scaffold and auth shell.

---

**User**

yeah looks good we can proceed

---

**Cursor**

> Auto routed to grok-4.5



Starting Task 6: scaffolding the Vite + React + TS frontend, then building auth and the ticket flows against the live API.

Shell was skipped — retrying setup checks and reading backend CORS/config so we can scaffold correctly.

Installing Node via nvm (not on PATH yet), then scaffolding the frontend and enabling CORS on the backend.

Scaffold is ready. Using Vite’s `/api` proxy to avoid adding CORS deps, then building auth and pages.

Writing the API client, auth layer, pages, and styles.

Build passed. Starting the Vite server and smoke-testing against the API.

Task 6 frontend is in place and running against your live API.

### What’s running
- **Frontend:** http://localhost:5173/
- **Backend:** http://127.0.0.1:8000/ (already up)
- Vite proxies `/api` → Django (no CORS package needed)

### Demo login
Use a seeded user, e.g. `priya.nair@example.com` / `SeedPass!23` (from `.env` `SEED_PASSWORD`).

### What was built (`src/frontend/`)
| Area | Behavior |
|------|----------|
| Auth | Access token in memory, refresh in `localStorage`, one 401→refresh→retry, then login redirect |
| Routes | `/login`, `/tickets`, `/tickets/new`, `/tickets/:id` (protected) |
| List | Status/priority/assignee filters, `q` search, pagination, loading/empty/error, CSV export |
| Create / detail | Inline field errors; edit disabled on terminal; transitions from `allowed_transitions` only; comments always allowed |

### How to run again later
```bash
# terminal 1 — backend (from src/backend)
python manage.py runserver

# terminal 2 — frontend
cd src/frontend && npm run dev
```

`npm run build` already passes. Open http://localhost:5173/ and walk through create → list → detail → transition → comment → export when you’re ready to verify the brief UI criteria.

