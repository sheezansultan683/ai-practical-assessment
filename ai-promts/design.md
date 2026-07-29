# API contract endpoint specs
_Exported on 7/27/2026 at 21:01:10 GMT+5:30 from Cursor (3.13.10)_

---

**User**

since we have now created @acceptance_criteria.md  can we now please create api-contract.md @requirements-analysis.md @.cursor/rules/10-domain.mdc

Write api-contract.md using the brief's template , Endpoint / Method / Path / 
Purpose, then Request, Response, Validation Rules, Error Responses for each.

Cover the endpoint list in 10-domain.mdc. Requirements:
- Concrete JSON examples with realistic values, not placeholders
- snake_case everywhere, including allowed_transitions
- Show the single error envelope shape once at the top, then reference it
- Every validation rule with its exact limit (max lengths, required fields)
- For the transition endpoint, show both the 200 and the 409 body
- Note that the CSV export returns text/csv, not JSON

Then tell me which endpoints you had to invent details for because the 
requirements don't specify them.

---

**Cursor**

> Auto routed to grok-4.5



I'll read the brief template and the domain/requirements docs so the API contract matches what's already defined.

The domain rules file path failed; I'll locate it and the brief's API-contract template next.

There's a mismatch between grep and the file read — checking `ai-promts/planning.md` and the on-disk requirements for the endpoint list and brief template.

On-disk `requirements-analysis.md` differs from what the editor showed — reading the real file and hunting for the brief's API-contract template.

---

**User**

using @requirements-analysis.md @.cursor/rules/ files 

Write api_contract.md using the brief's template,  Endpoint / Method / Path / 
Purpose, then Request, Response, Validation Rules, Error Responses for each.

Cover the endpoint list in  Requirements:
- Concrete JSON examples with realistic values, not placeholders
- snake_case everywhere, including allowed_transitions
- Show the single error envelope shape once at the top, then reference it
- Every validation rule with its exact limit (max lengths, required fields)
- For the transition endpoint, show both the 200 and the 409 body
- Note that the CSV export returns text/csv, not JSON

Then tell me which endpoints you had to invent details for because the 
requirements don't specify them.

---

**Cursor**

> Auto routed to grok-4.5



I'll re-read the requirements and Cursor rules, then write `api_contract.md` from the endpoint list and locked decisions.

Writing `api_contract.md` from the locked FR/assumptions and Cursor rules, with invented field limits and shapes called out at the end.

Created [`api_contract.md`](api_contract.md) covering all 12 endpoints from the requirements/Cursor rules, with the shared error envelope at the top, snake_case throughout (including `allowed_transitions`), concrete JSON examples, and both 200 + 409 for transitions. CSV is documented as `text/csv`.

### Invented because requirements don’t specify them

| Area | What I had to invent |
|------|----------------------|
| **Error envelope fields** | Exact shape (`error.code` / `message` / `details`) — FR-35 requires one envelope, not the fields |
| **Field max lengths** | `title` 200, `description` 5000, `message` 2000, `q` 200, `page_size` max 100 — edge cases mention “maximum length” without numbers |
| **Priority / role enums** | `LOW`/`MEDIUM`/`HIGH` and `AGENT`/`ADMIN` — A-14 says uppercase TextChoices, not the values |
| **Logout path** | `POST /api/token/blacklist/` + `205` — FR-5 requires blacklist, not the path/status |
| **Pagination response** | `{ count, page, page_size, results }` — A-16 only sets default page size 20 |
| **Nested user objects** | Full `{ id, name, email, role }` on `assigned_to` / `created_by` vs bare ids |
| **`allowed_transitions` on list** | Included on list items (requirements only require it on detail, FR-17) |
| **CSV columns + headers** | Exact column set and `Content-Disposition` filename — A-15 says “core fields + comment count” only |
| **Token obtain body key** | `email` (not SimpleJWT’s default `username`) — follows A-3, path still `/api/token/` |
| **409 detail field names** | `current_status`, `attempted_status`, `allowed_transitions` — FR-26 requires the three facts, not the keys |
| **Users list shape** | Unpaginated JSON array — FR-6 doesn’t specify pagination or response wrapper |

Paths for token/tickets/comments themselves come from the locked analysis + lifecycle rules; the gaps above are the wire-level details that weren’t written down.

---

**User**

before we move forward update the all files o use snakecase

---

**Cursor**

> Auto routed to grok-4.5



I'll scan the docs and Cursor rules for camelCase identifiers and update them to snake_case consistently.

Checking current file contents for remaining camelCase field names.

Updating camelCase field names to snake_case across the project docs and Cursor rules. Leaving `localStorage` alone — it's a browser API name, not a domain field.

Updating `ai-promts/planning.md` and aligning A-14 now that the brief uses snake_case.

All project docs now use snake_case for domain/API fields.

**Updated**
- `requirements-analysis.md` — `allowed_transitions`; A-14 expanded to lock snake_case wire keys
- `acceptance-criteria.md` — `allowed_transitions`
- `.cursor/rules/ticket-lifecycle.mdc` — `allowed_transitions`
- `.cursor/rules/stack-and-conventions.mdc` — explicit snake_case wire rule
- `project_requirement.txt` — entity fields (`assigned_to`, `created_by`, `created_at`, `updated_at`, `ticket_id`)
- `ai-promts/planning.md` — same renames for consistency

**Already snake_case:** `api-contract.md`

**Left as-is:** `localStorage` (browser API name, not a domain field)

---

**User**

have updated all the files to use snake case I still see file @api-contract.md  acceptance_criteria.md and other files not using snake case

---

**Cursor**

> Auto routed to grok-4.5



Checking whether the issue is file *names* (kebab vs snake) or remaining camelCase in the contents.

You're right — the issue is the filenames: they're kebab-case (`api-contract.md`) instead of snake_case (`api_contract.md`). Renaming them and updating cross-references.

You were right — that was about **filenames**, not field names. Content was already snake_case; the docs were still kebab-case (`api-contract.md`).

**Renamed**
| Old (kebab-case) | New (snake_case) |
|------------------|------------------|
| `api-contract.md` | `api_contract.md` |
| `acceptance-criteria.md` | `acceptance_criteria.md` |
| `requirements-analysis.md` | `requirements_analysis.md` |

Cross-references in the rules, docs, and `ai-promts/planning.md` were updated to match.

---

**User**

I have reviewed  the api_contract.md it looks good enough to move to the next of creating 
data_model.md
@requirements_analysis.md @api_contract.md @.cursor/rules/*.mdc

This is the last doc before I run , so it needs 
to pin down everything that ends up in a migration.

Cover these three tables: User, Ticket, Comment.

For each table give me a row per column with:
- field name and Django field type
- null / blank
- max_length where it applies
- default
- choices, using the exact TextChoices values from my rules files
- one short note on why, where it isn't obvious

Then these, which matter most:

1. Every ForeignKey with its on_delete and the reason. Specifically:
   - Ticket.created_by should be PROTECT — deleting a user must not destroy 
     ticket history
   - Ticket.assigned_to should be SET_NULL and nullable — a ticket can sit 
     untriaged, and a departing user shouldn't delete tickets
   - Comment.ticket should be CASCADE
   - Comment.created_by — tell me which and argue it
   If you disagree with any of my choices, say so.

2. The custom user model. I'm using email as USERNAME_FIELD with no username 
   field. Explain the order of operations for the first migration and why 
   AUTH_USER_MODEL can't be changed later. I want to understand this, not just 
   copy it.

3. Indexes. One per line with the exact query it serves — my filters are status, 
   priority, assigned_to, and a q search on title/description, sorted by 
   -created_at. Don't add indexes that no query uses.

4. Any CheckConstraint or UniqueConstraint worth having.

5. A simple text or mermaid diagram of the relationships.

6. Migration order — which app's migrations must be generated first and why.

7. A short section on what I considered and rejected: native Postgres enum types, 
   and a ticket_status_history table. Both were deliberate decisions, not 
   oversights.

We do not need to write any code as of now create  this markdown file first


---

**Cursor**

> Auto routed to grok-4.5



I'll pull the locked field limits, enums, and FK rules from the requirements, API contract, and Cursor rules, then write `data_model.md`.

Created [`data_model.md`](data_model.md).

**Pinned for migrations:** `User`, `Ticket`, `Comment` column tables with types, null/blank, max lengths (200 / 5000 / 2000 / 254), defaults, and exact `TextChoices` values.

**FKs — agree with yours.** For `Comment.created_by` I recommend **`PROTECT`**: same reasoning as `Ticket.created_by` — authorship is durable history; `CASCADE` would erase comments on user delete; `SET_NULL` leaves “unknown author” and breaks consistency with ticket creators.

**Also covered:** custom-user first-migrate order and why `AUTH_USER_MODEL` freezes; indexes only for status / priority / assignee / `created_by` / `-created_at` (no btree for `icontains` on title/description); unique email + check constraints on enums; mermaid ER; app migration order (`accounts` → builtins → `tickets`); rejected Postgres enums and `ticket_status_history`.

---

**User**

I reviewed the document it need some fix
1. description is CharField(5000) and message is CharField(2000). Make both 
   TextField instead. Your reason was "so the max length is in the migration" but 
   that's not worth it — in Postgres varchar(5000) and text are the same thing 
   with the same speed, and CharField makes Django admin show a one-line input 
   instead of a textarea. Enforce the length limits in the serializer, not the 
   model.

---

**Cursor**

> Auto routed to grok-4.5



Updating `data_model.md` so `description` and `message` are `TextField`, with length limits enforced in serializers.

Updated [`data_model.md`](data_model.md):

- `Ticket.description` → `TextField` (5000 enforced in serializer)
- `Comment.message` → `TextField` (2000 enforced in serializer)
- Checklist note added so implementation follows the same rule

---

**User**

can you explain in really simple term why we need role with example

---

**Cursor**

> Auto routed to grok-4.5



`role` is a label on the user that says **what kind of person they are** — e.g. `AGENT` or `ADMIN`.

**In this project (Core):** we store it and return it on `/api/me/` and `/api/users/`, but we **do not** use it to allow or block actions. Any logged-in user can create tickets, transition status, comment, etc. That was a deliberate choice so seeded users aren’t locked out of acceptance criteria.

**Why keep it anyway?**

1. The brief’s `User` entity includes `role`.
2. The UI can show it (e.g. “Priya — Agent” in the assignee picker).
3. Stretch / later work can turn it into real permissions without a new migration.

**Simple example**

| User | role | Today (Core) | Later (if you add RBAC) |
|------|------|--------------|-------------------------|
| Priya | `AGENT` | Can do everything after login | Maybe only work assigned tickets |
| Sara | `ADMIN` | Same — everything after login | Maybe manage users / see all exports |

So right now `role` is **data about the user**, not a **gate on the API**. It’s like writing “Agent” on their badge before the building has locked doors that check the badge.

---

**User**

Ok I think we have another role as well right requester who requested for the ticket

---

**Cursor**

> Auto routed to grok-4.5



Not as a `role` value — we only defined `AGENT` and `ADMIN`.

**Requester** here is not a user type. It’s **who created that ticket**: `Ticket.created_by`.

Example:

| User | `role` | On ticket #12 |
|------|--------|----------------|
| Priya | `AGENT` | `created_by` → she requested it |
| James | `AGENT` | `assigned_to` → he’s working it |
| Sara | `ADMIN` | neither on this ticket |

Same person can request one ticket and be assignee on another. That’s why requester lives on the **ticket** (`created_by`), not as a third value on `User.role`.

If you want a third role like `REQUESTER` (end-user who can only create/view own tickets), that would be a new product decision — Core doesn’t have it today.

---

**User**

yeah right make sense

---

**Cursor**

> Auto routed to grok-4.5



Good. Ready to start scaffolding whenever you want.

---

**User**

I also noted comment does not have default odering I think we can keep created_at as Descending

---

**Cursor**

> Auto routed to grok-4.5



Updating `data_model.md` to set Comment default ordering to `-created_at`.

Done. `Comment` now has `Meta.ordering = ["-created_at"]` in [`data_model.md`](data_model.md), and ticket detail in [`api_contract.md`](api_contract.md) notes comments come newest first. Also locked the same default on `Ticket` for the list.

---

**User**

should the app name be users instead of accounts in migration order

---

**Cursor**

> Auto routed to grok-4.5



Either works. Prefer **`users`** for this project.

| Name | Fit |
|------|-----|
| `users` | Matches the brief entity, `/api/users/`, and `AUTH_USER_MODEL = "users.User"` |
| `accounts` | Fine if you later put login/profile/password-reset in the same app; a bit more “auth package” than “User table” |

`accounts` was only a placeholder in `data_model.md`, not a locked requirement. If you want it renamed there (`users` first in migration order, `AUTH_USER_MODEL = "users.User"`), say the word and I’ll update the doc.

---

**User**

yes please update use users

---

**Cursor**

> Auto routed to grok-4.5



Updated [`data_model.md`](data_model.md): app is `users`, table `users_user`, and `AUTH_USER_MODEL = "users.User"`. Migration order is now `users` → builtins → `tickets`.

---

**User**

You wrote "filters are applied one-at-a-time in the contract". That's wrong — 
   my API contract example is ?status=OPEN&priority=HIGH&assigned_to=2&q=vpn and 
   my acceptance criteria say filters must combine. Fix that sentence. The 
   conclusion (no composite index at this scale) is fine, but add a line saying 
   the one place a composite index would help is the export query 
   (created_by_id + created_at).

---

**Cursor**

> Auto routed to grok-4.5



Fixed. Filters are described as combinable; still no composite at seed scale, with `(created_by_id, created_at)` noted as the export upgrade path.

---

**User**

 Your reasoning contradicts itself. You reject native Postgres enums because 
   changing them needs painful ALTER TYPE migrations, then add three 
   CheckConstraints which also need a drop-and-recreate migration when a value 
   changes. Keep the constraints — they do add real protection since choices 
   creates no DB constraint — but say honestly that they carry the same migration 
   cost, instead of implying they're free.


---

**Cursor**

> Auto routed to grok-4.5



Updated. Constraints stay; the doc now says plainly that changing their value set needs a drop-and-recreate migration — same cost class as `ALTER TYPE` — and that enums were rejected for plain string columns + Django `TextChoices`, not because checks are “free.”

---

**User**

You wrote Descending('created_at') for the index. That isn't a real Django API. 
   The correct form is models.Index(fields=["-created_at"]). Also — your own note 
   says Postgres can scan a btree backwards, so a plain created_at index already 
   handles ORDER BY created_at DESC. Just drop the descending index.

---

**Cursor**

> Auto routed to grok-4.5



Fixed. It’s a plain `models.Index(fields=["created_at"])` now — no descending index.

