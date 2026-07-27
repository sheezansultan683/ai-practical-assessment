# API Contract — Support Ticket Management System

**Sources:** [`requirements-analysis.md`](requirements-analysis.md),
[`.cursor/rules/stack-and-conventions.mdc`](.cursor/rules/stack-and-conventions.mdc),
[`.cursor/rules/ticket-lifecycle.mdc`](.cursor/rules/ticket-lifecycle.mdc)

**Base URL:** `/api`  
**Auth:** JWT Bearer access token on every ticket, comment, user-list, and profile endpoint.
Token obtain / refresh do not require a Bearer header.

**Wire conventions:** All JSON keys are `snake_case`. Enum values are uppercase
`TextChoices` strings (`OPEN`, `IN_PROGRESS`, `LOW`, …).

---

## Shared error envelope

Every error response (including DRF validation failures) uses this shape.
Endpoint sections below reference it instead of repeating the full object.

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": {
      "title": ["This field may not be blank."]
    }
  }
}
```

| Field | Type | Meaning |
|-------|------|---------|
| `error.code` | string | Machine-readable code (`validation_error`, `authentication_failed`, `not_found`, `invalid_transition`, `terminal_ticket_frozen`, …) |
| `error.message` | string | Human-readable summary for toasts / banners |
| `error.details` | object \| null | Field-level map (`field` → string[]) when applicable; otherwise `null` or omitted |

**Common statuses**

| HTTP | When |
|------|------|
| 400 | Malformed / invalid input (unknown enum, blank title, bad filter value) |
| 401 | Missing / expired / blacklisted token |
| 404 | Unknown ticket id, or page beyond last page |
| 409 | Valid schema but lifecycle forbids the operation (bad transition, field edit on terminal ticket) |
| 500 | Unexpected server failure (no stack trace leaked) |

---

## Enums

| Enum | Values |
|------|--------|
| `status` | `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`, `CANCELLED` |
| `priority` | `LOW`, `MEDIUM`, `HIGH` |
| `role` | `AGENT`, `ADMIN` |

**Allowed transitions**

| From | To |
|------|----|
| `OPEN` | `IN_PROGRESS`, `CANCELLED` |
| `IN_PROGRESS` | `RESOLVED`, `CANCELLED` |
| `RESOLVED` | `CLOSED` |
| `CLOSED` | _(none — terminal)_ |
| `CANCELLED` | _(none — terminal)_ |

---

## Shared field limits

| Field | Limits |
|-------|--------|
| `title` | required on create; strip whitespace; min length 1 after strip; **max 200** |
| `description` | required on create; strip trailing whitespace; **max 5000**; empty string after strip rejected |
| `priority` | required on create; one of `LOW`, `MEDIUM`, `HIGH` |
| `assigned_to` | optional; `null` or existing user id; nonexistent id → 400 |
| `message` (comment) | required; strip whitespace; min length 1 after strip; **max 2000** |
| `email` | valid email; **max 254** |
| `password` | required on login; **max 128** |
| `q` | optional; empty/`omit` = no search; **max 200** |
| `page` | optional positive integer; default `1` |
| `page_size` | optional positive integer; default **20**; **max 100** |

`created_by` is never accepted from the client; it is always `request.user`.

---

## Endpoint index

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/token/` | Obtain access + refresh tokens |
| POST | `/api/token/refresh/` | Refresh access token |
| POST | `/api/token/blacklist/` | Logout — invalidate refresh token |
| GET | `/api/me/` | Current user profile |
| GET | `/api/users/` | List seeded users (assignee picker) |
| GET | `/api/tickets/` | List / filter / search tickets |
| POST | `/api/tickets/` | Create ticket |
| GET | `/api/tickets/{id}/` | Ticket detail (with comments) |
| PATCH | `/api/tickets/{id}/` | Update title, description, priority, assignee |
| POST | `/api/tickets/{id}/transition/` | Change status via allow-list |
| GET | `/api/tickets/export/` | CSV of self-generated tickets |
| POST | `/api/tickets/{id}/comments/` | Add comment |

---

## Auth

### Endpoint: Obtain tokens

- **Method:** `POST`
- **Path:** `/api/token/`
- **Purpose:** Authenticate a seeded user with email + password; return JWT access and refresh tokens (`FR-1`, `A-3`).

#### Request

```http
POST /api/token/
Content-Type: application/json
```

```json
{
  "email": "priya.nair@example.com",
  "password": "SeedPass!23"
}
```

#### Response

`200 OK`

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzIyMDk2MDAwLCJ1c2VyX2lkIjoxfQ.example",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyMjY5OTIwMCwidXNlcl9pZCI6MX0.example"
}
```

#### Validation Rules

| Field | Rules |
|-------|-------|
| `email` | required; valid email; max 254 |
| `password` | required; max 128 |

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 400 | Missing / malformed fields | `validation_error` |
| 401 | Unknown email or wrong password | `authentication_failed` |

---

### Endpoint: Refresh access token

- **Method:** `POST`
- **Path:** `/api/token/refresh/`
- **Purpose:** Exchange a valid refresh token for a new access token without re-entering credentials (`FR-4`).

#### Request

```http
POST /api/token/refresh/
Content-Type: application/json
```

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyMjY5OTIwMCwidXNlcl9pZCI6MX0.example"
}
```

#### Response

`200 OK`

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzIyMDk2MzAwLCJ1c2VyX2lkIjoxfQ.example"
}
```

#### Validation Rules

| Field | Rules |
|-------|-------|
| `refresh` | required; non-empty string |

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 400 | Missing `refresh` | `validation_error` |
| 401 | Expired, invalid, or blacklisted refresh token | `authentication_failed` |

---

### Endpoint: Logout (blacklist refresh)

- **Method:** `POST`
- **Path:** `/api/token/blacklist/`
- **Purpose:** Invalidate the refresh token so it cannot be reused (`FR-5`).

#### Request

```http
POST /api/token/blacklist/
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyMjY5OTIwMCwidXNlcl9pZCI6MX0.example"
}
```

#### Response

`205 Reset Content` (empty body)

#### Validation Rules

| Field | Rules |
|-------|-------|
| `refresh` | required; non-empty string |

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 400 | Missing `refresh` | `validation_error` |
| 401 | Missing Bearer, or refresh already invalid / blacklisted | `authentication_failed` |

---

## Users

### Endpoint: Current user profile

- **Method:** `GET`
- **Path:** `/api/me/`
- **Purpose:** Return the authenticated user's id, name, email, and role (`FR-3`).

#### Request

```http
GET /api/me/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

No body.

#### Response

`200 OK`

```json
{
  "id": 1,
  "name": "Priya Nair",
  "email": "priya.nair@example.com",
  "role": "AGENT"
}
```

#### Validation Rules

None beyond authentication.

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 401 | Missing / invalid access token | `authentication_failed` |

---

### Endpoint: List seeded users

- **Method:** `GET`
- **Path:** `/api/users/`
- **Purpose:** Return seeded users for the assignee picker (`FR-6`). No pagination (seed set is small).

#### Request

```http
GET /api/users/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

No body.

#### Response

`200 OK`

```json
[
  {
    "id": 1,
    "name": "Priya Nair",
    "email": "priya.nair@example.com",
    "role": "AGENT"
  },
  {
    "id": 2,
    "name": "James Okonkwo",
    "email": "james.okonkwo@example.com",
    "role": "AGENT"
  },
  {
    "id": 3,
    "name": "Sara Chen",
    "email": "sara.chen@example.com",
    "role": "ADMIN"
  }
]
```

#### Validation Rules

None beyond authentication.

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 401 | Missing / invalid access token | `authentication_failed` |

---

## Tickets

### Endpoint: List tickets

- **Method:** `GET`
- **Path:** `/api/tickets/`
- **Purpose:** List all tickets with optional filters, free-text search, and page-number pagination (`FR-10`–`FR-15`, `A-16`, `A-17`, `A-18`).

#### Request

```http
GET /api/tickets/?status=OPEN&priority=HIGH&assigned_to=2&q=vpn&page=1&page_size=20
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

| Query param | Required | Rules |
|-------------|----------|-------|
| `status` | no | one of status enum; invalid → 400 |
| `priority` | no | one of priority enum; invalid → 400 |
| `assigned_to` | no | positive integer user id |
| `q` | no | case-insensitive substring on title **or** description; empty = no filter; max 200 |
| `page` | no | positive integer; default 1 |
| `page_size` | no | positive integer; default 20; max 100 |

Default order: `-created_at` (newest first).

#### Response

`200 OK`

```json
{
  "count": 47,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 12,
      "title": "VPN disconnects every hour",
      "description": "Since the Friday firewall change, remote staff lose VPN after about 60 minutes.",
      "priority": "HIGH",
      "status": "OPEN",
      "assigned_to": {
        "id": 2,
        "name": "James Okonkwo",
        "email": "james.okonkwo@example.com",
        "role": "AGENT"
      },
      "created_by": {
        "id": 1,
        "name": "Priya Nair",
        "email": "priya.nair@example.com",
        "role": "AGENT"
      },
      "created_at": "2026-07-27T10:14:22.481Z",
      "updated_at": "2026-07-27T10:14:22.481Z",
      "allowed_transitions": ["IN_PROGRESS", "CANCELLED"]
    }
  ]
}
```

List items do **not** embed comments.

#### Validation Rules

See query-param table above. Invalid `status` / `priority` return 400 listing valid choices.

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 400 | Invalid filter enum / non-integer `page` | `validation_error` |
| 401 | Missing / invalid access token | `authentication_failed` |
| 404 | `page` beyond last page | `not_found` |

---

### Endpoint: Create ticket

- **Method:** `POST`
- **Path:** `/api/tickets/`
- **Purpose:** Create a ticket; status forced to `OPEN`; `created_by` from the authenticated user (`FR-7`, `FR-8`, `FR-9`, `A-8`).

#### Request

```http
POST /api/tickets/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

```json
{
  "title": "VPN disconnects every hour",
  "description": "Since the Friday firewall change, remote staff lose VPN after about 60 minutes.",
  "priority": "HIGH",
  "assigned_to": 2
}
```

Client-supplied `status` or `created_by` are ignored (not applied).

#### Response

`201 Created`

```json
{
  "id": 12,
  "title": "VPN disconnects every hour",
  "description": "Since the Friday firewall change, remote staff lose VPN after about 60 minutes.",
  "priority": "HIGH",
  "status": "OPEN",
  "assigned_to": {
    "id": 2,
    "name": "James Okonkwo",
    "email": "james.okonkwo@example.com",
    "role": "AGENT"
  },
  "created_by": {
    "id": 1,
    "name": "Priya Nair",
    "email": "priya.nair@example.com",
    "role": "AGENT"
  },
  "created_at": "2026-07-27T10:14:22.481Z",
  "updated_at": "2026-07-27T10:14:22.481Z",
  "allowed_transitions": ["IN_PROGRESS", "CANCELLED"],
  "comments": []
}
```

#### Validation Rules

| Field | Rules |
|-------|-------|
| `title` | required; strip whitespace; min 1; **max 200** |
| `description` | required; strip; min 1 after strip; **max 5000** |
| `priority` | required; `LOW` \| `MEDIUM` \| `HIGH` |
| `assigned_to` | optional; `null` or existing user id |

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 400 | Missing/blank title, over-length, unknown priority, nonexistent assignee | `validation_error` |
| 401 | Missing / invalid access token | `authentication_failed` |

Example `400` body (title blank):

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": {
      "title": ["This field may not be blank."]
    }
  }
}
```

---

### Endpoint: Ticket detail

- **Method:** `GET`
- **Path:** `/api/tickets/{id}/`
- **Purpose:** Full ticket fields, nested comments, and `allowed_transitions` for the current status (`FR-16`, `FR-17`, `NFR-3`).

#### Request

```http
GET /api/tickets/12/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

No body. `{id}` must be a positive integer.

#### Response

`200 OK`

```json
{
  "id": 12,
  "title": "VPN disconnects every hour",
  "description": "Since the Friday firewall change, remote staff lose VPN after about 60 minutes.",
  "priority": "HIGH",
  "status": "IN_PROGRESS",
  "assigned_to": {
    "id": 2,
    "name": "James Okonkwo",
    "email": "james.okonkwo@example.com",
    "role": "AGENT"
  },
  "created_by": {
    "id": 1,
    "name": "Priya Nair",
    "email": "priya.nair@example.com",
    "role": "AGENT"
  },
  "created_at": "2026-07-27T10:14:22.481Z",
  "updated_at": "2026-07-27T11:02:09.115Z",
  "allowed_transitions": ["RESOLVED", "CANCELLED"],
  "comments": [
    {
      "id": 31,
      "ticket_id": 12,
      "message": "Reproduced on macOS 14 with Cisco AnyConnect 5.1.",
      "created_by": {
        "id": 2,
        "name": "James Okonkwo",
        "email": "james.okonkwo@example.com",
        "role": "AGENT"
      },
      "created_at": "2026-07-27T10:45:01.002Z"
    }
  ]
}
```

For `CLOSED` / `CANCELLED`, `allowed_transitions` is `[]`.

#### Validation Rules

`{id}` must resolve to an existing ticket.

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 401 | Missing / invalid access token | `authentication_failed` |
| 404 | Unknown or non-integer id | `not_found` |

---

### Endpoint: Update ticket fields

- **Method:** `PATCH`
- **Path:** `/api/tickets/{id}/`
- **Purpose:** Update title, description, priority, and/or assignee on a non-terminal ticket (`FR-18`–`FR-21`, `A-7`). Status is never changed here.

#### Request

```http
PATCH /api/tickets/12/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

```json
{
  "title": "VPN drops hourly after firewall change",
  "priority": "MEDIUM",
  "assigned_to": 3
}
```

Partial updates allowed. Omitting a field leaves it unchanged. `assigned_to: null` clears the assignee.

#### Response

`200 OK` — same shape as ticket detail (including current `comments` and `allowed_transitions`).

#### Validation Rules

| Field | Rules |
|-------|-------|
| `title` | if present: strip; min 1; **max 200** |
| `description` | if present: strip; min 1; **max 5000** |
| `priority` | if present: `LOW` \| `MEDIUM` \| `HIGH` |
| `assigned_to` | if present: `null` or existing user id |
| `status` | **not allowed** — reject with pointer to transition endpoint |
| `created_by` | ignored if supplied |

Ticket must not be `CLOSED` or `CANCELLED`.

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 400 | Field validation failure, or `status` present in body | `validation_error` |
| 401 | Missing / invalid access token | `authentication_failed` |
| 404 | Unknown ticket | `not_found` |
| 409 | Ticket is `CLOSED` or `CANCELLED` | `terminal_ticket_frozen` |

Example `400` when `status` is sent:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Status cannot be changed via this endpoint. Use POST /api/tickets/{id}/transition/.",
    "details": {
      "status": ["Use POST /api/tickets/{id}/transition/ to change status."]
    }
  }
}
```

Example `409` on terminal ticket:

```json
{
  "error": {
    "code": "terminal_ticket_frozen",
    "message": "Fields on a CLOSED ticket cannot be updated.",
    "details": {
      "status": ["CLOSED"]
    }
  }
}
```

---

### Endpoint: Transition ticket status

- **Method:** `POST`
- **Path:** `/api/tickets/{id}/transition/`
- **Purpose:** Move the ticket to the next status if the edge is in the allow-list (`FR-22`–`FR-26`, `A-9`–`A-11`).

#### Request

```http
POST /api/tickets/12/transition/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

```json
{
  "status": "IN_PROGRESS"
}
```

#### Response — success

`200 OK`

```json
{
  "id": 12,
  "title": "VPN disconnects every hour",
  "description": "Since the Friday firewall change, remote staff lose VPN after about 60 minutes.",
  "priority": "HIGH",
  "status": "IN_PROGRESS",
  "assigned_to": {
    "id": 2,
    "name": "James Okonkwo",
    "email": "james.okonkwo@example.com",
    "role": "AGENT"
  },
  "created_by": {
    "id": 1,
    "name": "Priya Nair",
    "email": "priya.nair@example.com",
    "role": "AGENT"
  },
  "created_at": "2026-07-27T10:14:22.481Z",
  "updated_at": "2026-07-27T11:02:09.115Z",
  "allowed_transitions": ["RESOLVED", "CANCELLED"],
  "comments": [
    {
      "id": 31,
      "ticket_id": 12,
      "message": "Reproduced on macOS 14 with Cisco AnyConnect 5.1.",
      "created_by": {
        "id": 2,
        "name": "James Okonkwo",
        "email": "james.okonkwo@example.com",
        "role": "AGENT"
      },
      "created_at": "2026-07-27T10:45:01.002Z"
    }
  ]
}
```

#### Response — invalid transition

`409 Conflict` — ticket status in the database is **unchanged**.

```json
{
  "error": {
    "code": "invalid_transition",
    "message": "Cannot transition ticket from OPEN to RESOLVED.",
    "details": {
      "current_status": "OPEN",
      "attempted_status": "RESOLVED",
      "allowed_transitions": ["IN_PROGRESS", "CANCELLED"]
    }
  }
}
```

Same-status (`OPEN` → `OPEN`), skips, and terminal outgoing edges also return this `409` shape.

#### Validation Rules

| Field | Rules |
|-------|-------|
| `status` | required; must be a known status enum value |

Unknown enum string (e.g. `"DONE"`) → **400**, not 409.

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 400 | Missing `status`, or value not in status enum | `validation_error` |
| 401 | Missing / invalid access token | `authentication_failed` |
| 404 | Unknown ticket | `not_found` |
| 409 | Known status but not an allowed edge (incl. same-status) | `invalid_transition` |

---

### Endpoint: Export self-generated tickets (CSV)

- **Method:** `GET`
- **Path:** `/api/tickets/export/`
- **Purpose:** Download a CSV of tickets where `created_by` is the authenticated user, including a per-ticket comment count (`FR-30`–`FR-33`, `A-4`, `A-15`).

**Content-Type is `text/csv`, not JSON.**

#### Request

```http
GET /api/tickets/export/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: text/csv
```

No body. Any client query params that attempt to widen scope are **ignored**; filter is always `created_by = request.user`.

#### Response

`200 OK`  
`Content-Type: text/csv; charset=utf-8`  
`Content-Disposition: attachment; filename="my_tickets.csv"`

```csv
id,title,description,priority,status,assigned_to_id,assigned_to_email,created_by_id,created_by_email,created_at,updated_at,comment_count
12,"VPN disconnects every hour","Since the Friday firewall change, remote staff lose VPN after about 60 minutes.",HIGH,OPEN,2,james.okonkwo@example.com,1,priya.nair@example.com,2026-07-27T10:14:22.481Z,2026-07-27T10:14:22.481Z,1
```

If the user has created no tickets, response is still `200` with **header row only**.

Cells containing commas, quotes, or newlines are CSV-escaped by the writer.

#### Validation Rules

None beyond authentication. Scope is server-enforced.

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 401 | Missing / invalid access token | `authentication_failed` (JSON envelope; not CSV) |

---

## Comments

### Endpoint: Add comment

- **Method:** `POST`
- **Path:** `/api/tickets/{id}/comments/`
- **Purpose:** Append a comment to a ticket in any status, including `CLOSED` and `CANCELLED` (`FR-27`–`FR-29`, `A-6`). No edit or delete endpoints exist.

#### Request

```http
POST /api/tickets/12/comments/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

```json
{
  "message": "Customer confirmed the drop still happens on the new AnyConnect build."
}
```

`created_by` is taken from `request.user`; client-supplied values are ignored.

#### Response

`201 Created`

```json
{
  "id": 32,
  "ticket_id": 12,
  "message": "Customer confirmed the drop still happens on the new AnyConnect build.",
  "created_by": {
    "id": 1,
    "name": "Priya Nair",
    "email": "priya.nair@example.com",
    "role": "AGENT"
  },
  "created_at": "2026-07-27T12:18:44.770Z"
}
```

#### Validation Rules

| Field | Rules |
|-------|-------|
| `message` | required; strip whitespace; min 1 after strip; **max 2000** |

#### Error Responses

| HTTP | Condition | Envelope `error.code` |
|------|-----------|------------------------|
| 400 | Blank / over-length message | `validation_error` |
| 401 | Missing / invalid access token | `authentication_failed` |
| 404 | Unknown ticket | `not_found` |

---

## Out of scope (no endpoints)

- Registration / user CRUD
- Ticket or comment delete (hard or soft)
- Comment edit
- Reopen from `CLOSED` / `CANCELLED`
- Role-gated authorization on Core endpoints
