# Implementation Plan — Support Ticket Management System

**Sources:** [`requirements-analysis.md`](requirements-analysis.md),
[`acceptance-criteria.md`](acceptance-criteria.md),
[`api-contract.md`](api-contract.md),
[`data-model.md`](data-model.md),
[`.cursor/rules/stack-and-conventions.mdc`](.cursor/rules/stack-and-conventions.mdc),
[`.cursor/rules/ticket-lifecycle.mdc`](.cursor/rules/ticket-lifecycle.mdc)

**Stack:** Django 5 + DRF + SQLite (via `DATABASE_URL`) + SimpleJWT +
drf-spectacular; React + Vite + TypeScript.

**DB:** `DATABASE_URL` is the only place the database engine/location is
configured. For SQLite, settings resolve the file against the **repository
root** (`REPO_ROOT / "database" / "tickets.db"`), not Django’s `BASE_DIR`
inside `src/` and not the process cwd. Switching to Postgres later is one env
var — no code change. Docker Compose / Postgres Stretch is **dropped on purpose
as a time call**, not a technical rejection (see
[`pr-description.md`](pr-description.md) Future Improvements).

---

## Repository structure

Target layout (brief Required Repository Structure). Application code lives
under `src/`; tests and the SQLite file stay at the repo root — never under
`src/`.

```text
ai-practical-assessment/
  README.md
  candidate-info.md
  tool-workflow.md
  requirements-analysis.md
  acceptance-criteria.md
  implementation-plan.md
  design-notes.md
  api-contract.md
  data-model.md
  ui-flow.md
  test-strategy.md
  src/
    backend/                 # Django project (manage.py, apps, settings)
      manage.py
      config/                # or project package — settings base/dev/test
      users/
      tickets/
    frontend/                # React + Vite + TypeScript
      package.json
      …
  tests/                     # pytest suite (separate from app DB)
  database/
    .gitkeep
    setup-notes.md
    schema.sql               # optional dump via sqlite3 .schema
    seed-data/               # optional fixtures / notes for seed
  test-results.md
  debugging-notes.md
  code-review-notes.md
  review-fixes.md
  pr-description.md
  reflection.md
  final-ai-usage-summary.md
  ai-prompts/
    planning.md
    design.md
    implementation.md
    testing.md
    debugging.md
    code-review.md
    documentation.md
  tool-specific/
    cursor-workflow/
```

**Path rules**

| Path | Role |
|------|------|
| `src/backend/` | Django only — created in Task 1 |
| `src/frontend/` | Vite + React + TS — created in Task 6 (not Task 1) |
| `tests/` | Integration/unit tests; Django test DB, not `database/tickets.db` |
| `database/tickets.db` | App SQLite file at **repo root** `database/` (gitignored) |
| `REPO_ROOT` | Parent of `src/`. SQLite `NAME` = `REPO_ROOT / "database" / "tickets.db"` |

Lifecycle docs use hyphenated filenames matching the brief (`requirements-analysis.md`,
`acceptance-criteria.md`, `api-contract.md`, `data-model.md`,
`implementation-plan.md`, …). Prompt history lives under `ai-prompts/`.

---

## Overview

Build an internal Support Ticket Management System: seeded users authenticate
with email/password (JWT), create and progress tickets through a fixed
lifecycle, comment on any status, filter/search the queue, and export their
own tickets as CSV.

The signature constraint is the status state machine. Exactly five transitions
are allowed; everything else is rejected with HTTP 409 and an unchanged DB
status. That allow-list has **one** definition in a backend service layer.
Detail responses expose `allowed_transitions`; the frontend never hardcodes
them. Field updates are separate from transitions; terminal tickets
(`CLOSED`, `CANCELLED`) freeze editable fields but still accept comments.

Work order is deliberate: scaffold and identity first (custom user before any
migrate), then models and seed, then the transition service **and its full-matrix
tests before any views**, then the API surface, auth wiring, frontend, and
finally assessment artifacts. Backend is the sole authority on validation and
lifecycle; the UI consumes the contract and renders errors clearly.

**Out of scope for Core:** user registration/CRUD UI, role-gated endpoints,
ticket/comment delete, status history, reopen paths, Docker/Postgres (deferred
time call), concurrent row-level locking (documented limitation — under SQLite
this race shows up as `database is locked` rather than a silent lost update).

**Done when:** all 11 brief acceptance criteria pass, `acceptance-criteria.md`
checkboxes are verifiable against FR/NFR IDs, and a clean clone follows the
README on Linux/macOS.

---

## Task Breakdown

### 1. Scaffold: settings split, custom user model, env

Backend scaffold only under `src/backend/` — no frontend in this task (that is
Task 6 → `src/frontend/`).

- Create Django project and apps (`users`, `tickets`) under **`src/backend/`**
  (`manage.py`, settings package, apps all live there).
- Split settings into `base` / `dev` / `test` (no `production` module). `test`
  is what pytest-django / `DJANGO_SETTINGS_MODULE` points at. Secrets and DB
  config come from the environment with **no fallback defaults** (NFR-6).
- Configure the database **only** from `DATABASE_URL` (e.g. via
  `dj-database-url` or equivalent). For SQLite, resolve the file against
  **`REPO_ROOT`** (repository root = parent of `src/`), always
  `REPO_ROOT / "database" / "tickets.db"`. Do **not** use Django `BASE_DIR`
  alone (that sits under `src/backend/` and would put the DB inside `src/`).
  Do not rely on cwd-relative `sqlite:///./…`.
- Commit `database/.gitkeep` so the folder exists after a clean clone (the
  `.db` file is gitignored; without the directory SQLite fails with
  “unable to open database file”). Ignore `database/tickets.db` in git.
- Define custom `User` (`AbstractBaseUser` + `PermissionsMixin`,
  `USERNAME_FIELD = "email"`, no `username`) and custom `UserManager`
  **before** the first `migrate` (`AUTH_USER_MODEL = "users.User"` — see
  `data-model.md` §2).
- `.env.example` at repo root with placeholder keys only; `.gitignore` excludes
  `.env`, secrets, build artifacts, and `database/tickets.db`.
- Install/pin: Django 5, DRF, SimpleJWT (+ blacklist), drf-spectacular,
  django-filter (or equivalent for list filters), pytest-django as needed.
  **No psycopg** — SQLite is stdlib. Do not add Compose files for Core.
- Confirm: `migrate` creates `users_user`, not `auth_user`; DB file appears at
  repo-root `database/tickets.db` even when `manage.py` is run from
  `src/backend/`; missing env vars fail loudly.

**Exit criteria:** empty backend under `src/backend/` boots against SQLite via
`DATABASE_URL` + `REPO_ROOT` resolution; `database/.gitkeep` committed; no
secrets in the repo.

---

### 2. Models, migrations, seed command

- Implement `Ticket` and `Comment` exactly per [`data-model.md`](data-model.md):
  TextChoices, FKs/`on_delete` (PROTECT / SET_NULL / CASCADE), indexes on
  status, priority, created_at (plus FK defaults), CheckConstraints for
  status/priority/role, Meta ordering `-created_at`.
- Migration order: `users` → builtins → `tickets` → SimpleJWT blacklist tables.
- Idempotent, transactional management command `seed` (`python manage.py seed`)
  covering all five statuses, all priorities, and multiple `created_by` users
  (NFR-7, NFR-8). Seed passwords only via env / documented demo values — never
  committed as production secrets.
- Smoke: migrate → `seed` → `seed` again (no duplicates) → **restart the app**
  and confirm data is still there (NFR-1).

**Exit criteria:** schema matches the data model; seed is safe to re-run;
persistence survives an application restart.

---

### 3. Transition service and its tests — before any views

Build the lifecycle in isolation so views never become the source of truth
(NFR-4, NFR-3).

- Single allow-list constant / table in the tickets service layer:

  | From | To |
  |------|-----|
  | `OPEN` | `IN_PROGRESS`, `CANCELLED` |
  | `IN_PROGRESS` | `RESOLVED`, `CANCELLED` |
  | `RESOLVED` | `CLOSED` |
  | `CLOSED` / `CANCELLED` | _(none)_ |

- Service API (shape illustrative): `allowed_transitions(status)`,
  `transition_ticket(ticket, to_status)` — success updates status and
  `updated_at`; failure raises a domain error carrying current, attempted, and
  legal alternatives (maps to 409 + `invalid_transition` later).
- Also encode terminal field-freeze and “status not via field update” as
  service rules so serializers/views stay thin (FR-19, FR-20, A-7).
- **Integration / unit tests for the complete matrix before any HTTP views**
  (NFR-11): every valid edge succeeds; every invalid pair (same-status, skip,
  reopen, terminal-outgoing) is rejected and leaves DB status unchanged;
  unknown enum string is treated as malformed (400 path) vs lifecycle conflict
  (409). Tests live under repo-root **`tests/`** and use Django’s **separate
  test database** (created/torn down by the runner / pytest-django via
  `settings.test`) — never the app’s `database/tickets.db`, so running the
  suite does not wipe seed data.

**Exit criteria:** full transition matrix green with **zero** view/URL code;
allow-list exists in exactly one place.

---

### 4. API endpoints, filters, CSV export

Implement [`api-contract.md`](api-contract.md) against the service layer.

- Shared error envelope for all failures including DRF validation (FR-35).
- Tickets: list (page size 20, max 100; default `-created_at`), create (always
  `OPEN`; `created_by = request.user`), detail (nested comments +
  `allowed_transitions`), PATCH fields only (reject `status`; freeze on
  terminal → 409), `POST …/transition/`, `POST …/comments/` (any status),
  `GET …/export/` CSV scoped to `created_by = request.user` (core fields +
  comment count; header-only if empty).
- Filters: `status`, `priority`, `assigned_to`; search `q` on title **or**
  description (`icontains`); invalid filter enum → 400 with choices.
- Users: `GET /api/me/`, `GET /api/users/` for assignee picker (no user CRUD).
- Wire OpenAPI via drf-spectacular annotations on the views (NFR-10).
- Integration tests for create/list/detail/update/comment/export, pagination,
  filters/search, envelope shape, 401/404/409 paths cited in
  `acceptance-criteria.md` (views may use temporary auth stubs / force_authenticate
  until step 5 is complete, or land JWT URLs in the same PR as long as service
  tests already own the matrix).

**Exit criteria:** contract endpoints behave as documented; CSV never leaks
other users’ tickets; OpenAPI generates from code.

---

### 5. Auth wiring

- SimpleJWT: `POST /api/token/` (email + password), `POST /api/token/refresh/`,
  `POST /api/token/blacklist/` (logout) — FR-1, FR-4, FR-5.
- `IsAuthenticated` (or equivalent) on every ticket, comment, profile, and
  user-list endpoint (FR-2). Token obtain/refresh remain public.
- Confirm blacklist app migrations; expired/blacklisted refresh → 401 in the
  shared envelope.
- Tests: unauthenticated → 401; login; refresh; logout then reuse refresh →
  401; profile returns id/name/email/role.

**Exit criteria:** full-app JWT matches assumptions A-1/A-3/A-21 backend half;
CSV “self” is always `request.user`.

---

### 6. Frontend

Scaffold and build under **`src/frontend/`** (React + Vite + TypeScript). Do
not place the UI at the repo root or inside `src/backend/`.

- Auth: login form; access token in memory; refresh in `localStorage`; on 401
  one refresh + retry then redirect to login (A-21). Protected ticket routes.
- Ticket list: filters (status, priority, assignee), `q` search, pagination,
  loading / empty / network-failure states (FR-38).
- Create ticket; detail with comments; edit form disabled on terminal tickets;
  transition actions rendered **only** from `allowed_transitions` (NFR-3).
- Inline field validation (FR-36); human-readable sentence for rejected
  transitions (FR-37); CSV download trigger for self-generated export.
- Consume `snake_case` JSON as-is (or a thin typed client) — do not invent a
  second transition table in the UI.

**Exit criteria:** all brief UI criteria (create, list, detail, update,
comment, transition rejection UX, CSV) work against the real API from
`src/frontend/`.

---

### 7. Remaining artifacts, debugging notes, code review, reflection

- README: clone → env from `.env.example` → migrate/seed from `src/backend/` →
  run API + `src/frontend/` → run `tests/` (NFR-5). No Compose step. Document
  demo users without real production secrets.
- Align repo with the structure above: lifecycle docs at root (brief hyphen
  names), `src/backend` + `src/frontend`, `tests/`, `database/setup-notes.md` +
  `.gitkeep`, `ai-prompts/`, `tool-specific/cursor-workflow/`, plus close-out
  files (`debugging-notes.md`, `code-review-notes.md`, `review-fixes.md`,
  `pr-description.md`, `reflection.md`, `final-ai-usage-summary.md`,
  `test-results.md`, etc.).
- Debugging notes: known limitations — SQLite write lock means concurrent
  transitions surface as `database is locked` (not a silent lost update);
  refresh token in `localStorage`; no status history / reopen (C-1/C-5);
  Docker/Postgres Stretch deferred as a time call.
- Walk `acceptance-criteria.md` end-to-end; tick items with
  `[int]` / `[ui]` / `[cmd]` / `[insp]` evidence.
- Code review pass: service-layer boundaries, no duplicated allow-list, no
  secrets, no delete endpoints, OpenAPI accurate, no `psycopg` / Compose;
  code only under `src/`.
- Short reflection (assessment write-up): what AI helped vs what required human
  judgment (lifecycle gaps, CSV-vs-auth, terminal freeze, SQLite time call).

**Exit criteria:** reviewer can verify Core + Stretch evidence from README and
artifacts alone; checklist complete; tree matches the brief structure.

---

## Milestones

| Milestone | Scope | Primary evidence |
|-----------|--------|------------------|
| **M1 — Foundation** | Tasks 1–2 | `src/backend/` live; `DATABASE_URL` + `REPO_ROOT` → `database/tickets.db`; `database/.gitkeep`; custom user; migrations; `manage.py seed`; data still there after app restart |
| **M2 — Lifecycle proven** | Task 3 | Full transition-matrix tests green under `tests/`; single allow-list in service layer |
| **M3 — API complete** | Tasks 4–5 | Contract endpoints + JWT + CSV + OpenAPI; acceptance `[int]` items for Core API |
| **M4 — Product usable** | Task 6 | `src/frontend/` satisfies brief’s 11 criteria against live backend |
| **M5 — Assessment ready** | Task 7 | README, full brief tree, debugging notes, review, reflection; checklist signed off |

Suggested sequencing: do not start M3 views until M2 is green; do not polish UI
beyond auth shell until list/detail/transition APIs exist. Frontend can track
M3 in parallel once create/list/detail stabilize, but transition buttons must
wait on `allowed_transitions`.

---

## AI Usage Plan

| Phase | Use AI for | Keep human-owned |
|-------|------------|------------------|
| Planning / specs | Drafting and tightening analysis, acceptance criteria, API contract, data model, Cursor rules from locked decisions | Product calls (terminal freeze, full-app JWT, list vs export scope, 409 vs 400, SQLite time call) |
| Scaffold (1) | `src/backend/` settings `base`/`dev`/`test`, `.env.example`, `database/.gitkeep` | Env fail-loud; `AUTH_USER_MODEL` before first migrate; `DATABASE_URL` + `REPO_ROOT` (not `BASE_DIR` alone) |
| Models / seed (2) | Model field scaffolding from data-model; seed data variety | FK/`on_delete`, indexes vs non-indexes, CheckConstraints, seed idempotency |
| Transition service (3) | Generating the full valid/invalid matrix test table under `tests/` | Single allow-list definition; asserting DB unchanged on failure |
| API (4–5) | View/serializer stubs, spectacular annotations, filter wiring | Error envelope consistency; CSV scope always `request.user`; no status on PATCH |
| Frontend (6) | Scaffold + pages under `src/frontend/` | Never hardcoding transitions; terminal form disable; error copy for 409 |
| Close-out (7) | README outline, brief tree alignment, reflection draft | Manual verification of brief’s 11 criteria; secret scan; final review |

**Guardrails (always):** feed agents the Cursor rules and contract docs; reject
suggestions that duplicate the allow-list in the frontend, add delete endpoints,
gate Core on `role`, commit `.env` or `database/tickets.db`, reintroduce
Compose/`psycopg` without an explicit decision, or put secrets in seed/README as
if production-ready. Prefer smallest diffs; run the matrix tests after any
lifecycle touch.

---

## Risks

| ID | Risk | Impact if ignored |
|----|------|-------------------|
| R-1 | Migrating before `AUTH_USER_MODEL` is set | Painful user-table swap or DB reset mid-project |
| R-2 | Transition rules copied into views, serializers, **and** React | Divergent lifecycle; NFR-3 fail; UI offers illegal moves |
| R-3 | Writing views before service + matrix tests | Lifecycle bugs found late; tests sample edges instead of covering all |
| R-4 | Softening “self-generated” CSV (query param / client `created_by`) | Brief criterion fails; export leaks other users’ tickets |
| R-5 | Treating invalid enum and invalid transition the same (both 400 or both 409) | Frontend cannot distinguish validation vs lifecycle conflict |
| R-6 | Secrets or real passwords committed; env defaults that hide misconfig | NFR-6 / brief “no secrets” fail |
| R-7 | Frontend hardcodes transitions for “better UX” | Breaks when API is source of truth; assessment ding on NFR-2/3 |
| R-8 | Scope creep (reopen, RBAC, status history, deletes, premature Docker) | Misses Core deadline; invents rules the brief does not grant |
| R-9 | Concurrent double-transition under SQLite | Writers hit DB-wide lock → `database is locked` (not a silent lost update). Still a known limitation if presented as “solved concurrency” |
| R-10 | Search/`q` over-engineered (trigram) or list unbounded | Wasted time / poor defaults vs A-16/A-18 |
| R-11 | Resolving SQLite against cwd or Django `BASE_DIR` under `src/` instead of `REPO_ROOT` | DB created under `src/…/database/`; clone fails without root `database/`; Postgres switch stops being “one env var” |
| R-12 | Putting backend/frontend at repo root instead of `src/` | Misses brief Required Repository Structure |

---

## Mitigation

| Risk | Mitigation |
|------|------------|
| R-1 | Task 1 explicitly sets custom user + `AUTH_USER_MODEL` before any migrate; follow `data-model.md` §2 order |
| R-2 | Task 3 owns the only allow-list; API returns `allowed_transitions`; Cursor `ticket-lifecycle` rule forbids FE hardcoding |
| R-3 | Hard gate: no ticket views until matrix tests pass (Task Breakdown order) |
| R-4 | Export queryset filters solely on `request.user`; ignore client scope params; integration test FR-33 |
| R-5 | Contract + lifecycle rule: unknown status string → 400; allow-list miss → 409 with current/attempted/allowed |
| R-6 | No defaults for secrets; `.env.example` placeholders only; `.gitignore` includes `database/tickets.db`; seed docs use clearly demo credentials |
| R-7 | UI maps buttons from response field only; code review checklist item in Task 7 |
| R-8 | Clarifications C-1…C-7 already locked in analysis; Stretch is auth, OpenAPI, Cursor rules — Docker deferred as time call |
| R-9 | Document in debugging notes / pr-description: SQLite lock behaviour; optional future `select_for_update` on Postgres — do not claim fixed in Core |
| R-10 | Page size 20; `icontains` on title/description; no title/description btree (data model §3) |
| R-11 | Parse `DATABASE_URL` in one settings module; resolve SQLite `NAME` to `REPO_ROOT / "database" / "tickets.db"`; commit `database/.gitkeep` |
| R-12 | Task 1 → `src/backend/` only; Task 6 → `src/frontend/`; tests → repo-root `tests/` |

Cross-check before calling the project done: walk
[`acceptance-criteria.md`](acceptance-criteria.md) (including the brief’s
11/11 table) and confirm every `(brief)` item has evidence from M1–M5.
