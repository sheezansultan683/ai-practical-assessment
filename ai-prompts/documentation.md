# DRF spectacular ticket docs
_Exported on 7/29/2026 at 21:25:07 GMT+5:30 from Cursor (3.13.10)_

---

**User**

@implementation_paln can you please create the Documentation for the  endpoints what we have created  ticket management system using drf_spectacular

---

**Cursor**

> Auto routed to grok-4.5



I'll inspect the existing API endpoints and drf-spectacular setup so we can document them properly.

Checking views, serializers, and the API contract so we can wire complete OpenAPI annotations.

Reviewing serializers and the exception envelope so annotations match the live API.

Implementing OpenAPI docs: shared schemas, Swagger UI, and `@extend_schema` on all endpoints.

Verifying schema generation and fixing the token response documentation.

OpenAPI docs are wired via **drf-spectacular** for all ticket-management endpoints.

### How to view
With the backend running:
- **Swagger UI:** [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Raw schema:** [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)

In Swagger, use **Authorize** with `Bearer <access_token>` (JWT).

### What changed
| File | Why |
|------|-----|
| `src/backend/config/urls.py` | Added `/api/docs/` (Swagger UI) alongside `/api/schema/` |
| `src/backend/config/settings/base.py` | Expanded `SPECTACULAR_SETTINGS` (description, tags) |
| `src/backend/config/schema.py` | Shared error-envelope + paginated list OpenAPI helpers |
| `src/backend/tickets/views.py` | `@extend_schema` on list/create/detail/patch/transition/comment/export |
| `src/backend/users/views.py` + `urls.py` | Auth + users docs; token refresh/blacklist wrappers |
| `src/backend/users/serializers.py` | Token request/response serializers for the schema |
| `tests/test_api.py` | Asserts schema includes all core paths |

Documented endpoints: token obtain/refresh/blacklist, `/me/`, `/users/`, ticket list/create/detail/patch/transition/comments/export — with summaries, request/response shapes, and the shared `{error: {code, message, details}}` envelope.

---

**User**

I have reviewed it looks good

---

**Cursor**

> Auto routed to grok-4.5



Good to hear. The Swagger UI at `/api/docs/` is ready whenever you need it for the assessment or frontend work.

