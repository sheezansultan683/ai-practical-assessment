# Local server paths error
_Exported on 7/29/2026 at 21:47:02 GMT+5:30 from Cursor (3.13.10)_

---

**User**

I am trying the run  local server but getting paths is not defined

---

**Cursor**

> Auto routed to grok-4.5



I'll check the server error and the URL config that's likely causing `paths is not defined`.

Typo in `config/urls.py`: `paths` should be `path`. Checking the intended API prefix next.

Fixing the typo: `paths` → `path`, and correcting the prefix from `apiii/` to `api/`.

The crash came from a typo in `src/backend/config/urls.py`:

- `paths(...)` → `path(...)` (`paths` is not imported)
- `"apiii/"` → `"api/"` so tickets mount under `/api/` like the rest of the API

Restart (or let autoreload pick it up) and the server should start cleanly. Ticket routes will be at `/api/tickets/`, etc.

---

**User**

@views.py (129-133)  is there a specific reason why use generics.ListCreateAPIView instead od model view sets

---

**Cursor**

> Auto routed to grok-4.5



I'll check how ticket views are structured and what the project docs say about that choice.

Yes — it fits this API better than a `ModelViewSet`.

**What this surface actually needs**
- List + create on one URL
- Retrieve + field update on another
- Status changes only via `/transition/` (not PATCH)
- Comments and CSV export as separate endpoints
- **No** delete (hard or soft)

A `ModelViewSet` is built for full CRUD (`list/create/retrieve/update/destroy`). You’d turn off `destroy`, override update so `status` isn’t patched, and still bolt on custom `@action`s for transition/comments/export. That fights the default rather than using it.

**Why generics fit**
- One class per URL group, matching the explicit `path(...)` wiring
- Different serializers per operation (`TicketListSerializer` vs create/detail/update) without ViewSet `get_serializer_class` branching
- Service-layer calls stay obvious in `create` / `update` / custom `APIView`s
- Same pattern as `users` (`ListAPIView` / `APIView`) — no routers

A ViewSet isn’t wrong in DRF generally; for this contract (partial CRUD + lifecycle actions + no delete), explicit generic/API views are the clearer, smaller fit.

---

**User**

We have the functionality to overide inbuilt methods right

---

**Cursor**

> Auto routed to grok-4.5



Yes. Both generics and ViewSets let you override the built-ins.

On something like `ListCreateAPIView` / `RetrieveUpdateAPIView` you commonly override:

- `get_queryset()`, `get_serializer_class()`
- `create()`, `perform_create()`
- `update()`, `partial_update()`, `perform_update()`
- `list()`, `retrieve()`

On a `ModelViewSet` you’d do the same, plus things like omitting `destroy` or overriding `get_serializer_class` / custom `@action` methods.

So the choice isn’t “can we customize?” — both can. It’s whether the default ViewSet shape (full CRUD + router) matches the API, or whether explicit generic/API views already map 1:1 to the routes you need.

---

**User**

We have the functionality to overide inbuilt methods on ModelViewSet right

---

**Cursor**

> Auto routed to grok-4.5



Yes. `ModelViewSet` methods are meant to be overridden. Common ones:

- `get_queryset()`, `get_serializer_class()`, `get_permissions()`
- `list()`, `create()`, `retrieve()`, `update()`, `partial_update()`, `destroy()`
- `perform_create()`, `perform_update()`, `perform_destroy()`

You can also add custom endpoints with `@action`. So you *could* build this ticket API on a ViewSet by overriding/disabling what doesn’t fit — the project just chose explicit generics instead.

