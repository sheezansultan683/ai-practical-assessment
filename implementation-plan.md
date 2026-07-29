# Implementation Plan — Support Ticket Management System

**Sources:** [`requirements_analysis.md`](requirements_analysis.md),
[`acceptance_criteria.md`](acceptance_criteria.md),
[`api_contract.md`](api_contract.md),
[`data_model.md`](data_model.md),
[`.cursor/rules/stack-and-conventions.mdc`](.cursor/rules/stack-and-conventions.mdc),
[`.cursor/rules/ticket-lifecycle.mdc`](.cursor/rules/ticket-lifecycle.mdc)

**Stack:** Django 5 + DRF + PostgreSQL 16 (Docker Compose) + SimpleJWT +
drf-spectacular; React + Vite + TypeScript.

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
ticket/comment delete, status history, reopen paths, concurrent
`select_for_update` locking (documented limitation).

**Done when:** all 11 brief acceptance criteria pass, `acceptance_criteria.md`
checkboxes are verifiable against FR/NFR IDs, and a clean clone follows the
README on Linux/macOS.

---

## Task Breakdown

### 1. Scaffold: settings split, custom user model, Compose, env

- Create Django project and apps (`users`, `tickets`); Vite + React + TypeScript
  frontend skeleton (login-gated shell only — no ticket UI yet).
- Split settings (`base` / `local` / `production` or equivalent) so secrets and
  DB config come from the environment with **no fallback defaults** (NFR-6).
- Define custom `User` (`AbstractBaseUser` + `PermissionsMixin`,
  `USERNAME_FIELD = "email"`, no `username`) and custom `UserManager`
  **before** the first `migrate` (`AUTH_USER_MODEL = "users.User"` — see
  `data_model.md` §2).
- Docker Compose for PostgreSQL 16; `.env.example` with placeholder keys only;
  `.gitignore` excludes `.env`, secrets, and build artifacts.
- Install/pin: Django 5, DRF, SimpleJWT (+ blacklist), drf-spectacular,
  psycopg, django-filter (or equivalent for list filters).
- Confirm: `migrate` creates `users_user`, not `auth_user`; Compose DB is
  reachable; missing env vars fail loudly.

**Exit criteria:** empty project boots against Compose Postgres with custom
user model live; no secrets in the repo.

---

### 2. Models, migrations, seed command

- Implement `Ticket` and `Comment` exactly per [`data_model.md`](data_model.md):
  TextChoices, FKs/`on_delete` (PROTECT / SET_NULL / CASCADE), indexes on
  status, priority, created_at (plus FK defaults), CheckConstraints for
  status/priority/role, Meta ordering `-created_at`.
- Migration order: `users` → builtins → `tickets` → SimpleJWT blacklist tables.
- Idempotent, transactional management command `seed_demo` (or equivalent)
  covering all five statuses, all priorities, and multiple `created_by` users
  (NFR-7, NFR-8). Seed passwords only via env / documented demo values — never
  committed as production secrets.
- Smoke: migrate → seed → seed again (no duplicates) → restart container and
  confirm data persists (NFR-1).

**Exit criteria:** schema matches the data model; seed is safe to re-run;
persistence survives restart.

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
  (409).

**Exit criteria:** full transition matrix green with **zero** view/URL code;
allow-list exists in exactly one place.

---

### 4. API endpoints, filters, CSV export

Implement [`api_contract.md`](api_contract.md) against the service layer.

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
  `acceptance_criteria.md` (views may use temporary auth stubs / force_authenticate
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
comment, transition rejection UX, CSV) work against the real API.

---

### 7. Remaining artifacts, debugging notes, code review, reflection

- README: clone → env from `.env.example` → Compose up → migrate → seed →
  run API + frontend → run tests (NFR-5). Document demo users without real
  production secrets.
- Confirm root artifacts present:
  `requirements_analysis.md`, `acceptance_criteria.md`, `api_contract.md`,
  `data_model.md`, `implementation-plan.md`, Cursor rules under
  `.cursor/rules/`.
- Debugging notes: known limitations (concurrent transition race without
  `select_for_update`; refresh token in `localStorage`; no status history /
  reopen — C-1/C-5).
- Walk `acceptance_criteria.md` end-to-end; tick items with
  `[int]` / `[ui]` / `[cmd]` / `[insp]` evidence.
- Code review pass: service-layer boundaries, no duplicated allow-list, no
  secrets, no delete endpoints, OpenAPI accurate.
- Short reflection (assessment write-up): what AI helped vs what required human
  judgment (lifecycle gaps, CSV-vs-auth, terminal freeze).

**Exit criteria:** reviewer can verify Core + Stretch evidence from README and
artifacts alone; checklist complete.

---

## Milestones

| Milestone | Scope | Primary evidence |
|-----------|--------|------------------|
| **M1 — Foundation** | Tasks 1–2 | Compose Postgres up; custom user; migrations; idempotent seed; data survives restart |
| **M2 — Lifecycle proven** | Task 3 | Full transition-matrix tests green; single allow-list in service layer |
| **M3 — API complete** | Tasks 4–5 | Contract endpoints + JWT + CSV + OpenAPI; acceptance `[int]` items for Core API |
| **M4 — Product usable** | Task 6 | UI satisfies brief’s 11 criteria against live backend |
| **M5 — Assessment ready** | Task 7 | README, artifacts, debugging notes, review, reflection; checklist signed off |

Suggested sequencing: do not start M3 views until M2 is green; do not polish UI
beyond auth shell until list/detail/transition APIs exist. Frontend can track
M3 in parallel once create/list/detail stabilize, but transition buttons must
wait on `allowed_transitions`.

---

## AI Usage Plan

| Phase | Use AI for | Keep human-owned |
|-------|------------|------------------|
| Planning / specs | Drafting and tightening analysis, acceptance criteria, API contract, data model, Cursor rules from locked decisions | Product calls (terminal freeze, full-app JWT, list vs export scope, 409 vs 400) |
| Scaffold (1) | Boilerplate settings split, Compose file, `.env.example`, project layout | Env fail-loud policy; `AUTH_USER_MODEL` before first migrate |
| Models / seed (2) | Model field scaffolding from `data_model.md`; seed data variety | FK/`on_delete`, indexes vs non-indexes, CheckConstraints, seed idempotency |
| Transition service (3) | Generating the full valid/invalid matrix test table | Single allow-list definition; asserting DB unchanged on failure |
| API (4–5) | View/serializer stubs, spectacular annotations, filter wiring | Error envelope consistency; CSV scope always `request.user`; no status on PATCH |
| Frontend (6) | Page structure, form wiring, fetch client with refresh-retry | Never hardcoding transitions; terminal form disable; error copy for 409 |
| Close-out (7) | README outline, checklist crosswalk, reflection draft | Manual verification of brief’s 11 criteria; secret scan; final review |

**Guardrails (always):** feed agents the Cursor rules and contract docs; reject
suggestions that duplicate the allow-list in the frontend, add delete endpoints,
gate Core on `role`, commit `.env`, or put secrets in seed/README as if
production-ready. Prefer smallest diffs; run the matrix tests after any
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
| R-8 | Scope creep (reopen, RBAC, status history, deletes) | Misses Core deadline; invents rules the brief does not grant |
| R-9 | Concurrent double-transition race (known limitation) | Rare lost update; only a problem if presented as solved |
| R-10 | Search/`q` over-engineered (trigram) or list unbounded | Wasted time / poor defaults vs A-16/A-18 |

---

## Mitigation

| Risk | Mitigation |
|------|------------|
| R-1 | Task 1 explicitly sets custom user + `AUTH_USER_MODEL` before any migrate; follow `data_model.md` §2 order |
| R-2 | Task 3 owns the only allow-list; API returns `allowed_transitions`; Cursor `ticket-lifecycle` rule forbids FE hardcoding |
| R-3 | Hard gate: no ticket views until matrix tests pass (Task Breakdown order) |
| R-4 | Export queryset filters solely on `request.user`; ignore client scope params; integration test FR-33 |
| R-5 | Contract + lifecycle rule: unknown status string → 400; allow-list miss → 409 with current/attempted/allowed |
| R-6 | No defaults for secrets; `.env.example` placeholders only; `.gitignore`; seed docs use clearly demo credentials |
| R-7 | UI maps buttons from response field only; code review checklist item in Task 7 |
| R-8 | Clarifications C-1…C-7 already locked in analysis; Stretch only auth, OpenAPI, Compose, Cursor rules |
| R-9 | Document in debugging notes; optional future `select_for_update` — do not claim fixed in Core |
| R-10 | Page size 20; `icontains` on title/description; no title/description btree (data model §3) |

Cross-check before calling the project done: walk
[`acceptance_criteria.md`](acceptance_criteria.md) (including the brief’s
11/11 table) and confirm every `(brief)` item has evidence from M1–M5.
