# Ticket and user model tests
_Exported on 7/29/2026 at 21:33:09 GMT+5:30 from Cursor (3.13.10)_

---

**User**

@implementation-plan.md can we please work task 3 to add the test cases please check if the tests are not already there add the tests cases for the following 
ticket life cycle, ticket models CRUDS user models for more detail check the implemantation plan
 

---

**Cursor**

> Auto routed to grok-4.5



I'll check the implementation plan for task 3 and compare it against the existing tests so we only add what's missing.

Existing test files are present — I'll compare them to Task 3 requirements and the service layer.

Lifecycle coverage looks solid; I'll inspect the models and data model docs for gaps in ticket/user CRUD tests.

Lifecycle tests already cover the full matrix. I'll expand ticket and user model CRUD coverage, then run the suite.

Lifecycle suite is green. Expanding ticket and user model CRUD tests next.

**Verdict:** Task 3 lifecycle tests were already complete; ticket/user model CRUD coverage was thin and is now expanded. Full suite: **77 passed, 5 skipped**.

### Ticket lifecycle (`tests/test_ticket_lifecycle.py`)
Already present — no changes needed. Covers:
- Full valid transition matrix from `ALLOWED_TRANSITIONS`
- Full invalid matrix (same-status, skip, reopen, terminal-outgoing) with DB status unchanged
- Unknown status → `MalformedStatusError` (400 path)
- Status not via field update
- Terminal field freeze + non-terminal updates

### Ticket models (`tests/test_ticket_models.py`) — expanded
CRUD plus data-model rules:
- Create/read (all priorities/statuses, null assignee)
- Update fields / clear assignee
- Comment create/read, terminal comments, newest-first order, duplicates allowed
- FK: `assigned_to` SET_NULL, `created_by` PROTECT, comment author PROTECT, ticket→comments CASCADE
- CheckConstraints for invalid status/priority

### User models (`tests/test_user_model.py`) — expanded
- Create (email identity, password, superuser, role, normalize email, require email)
- Read by email / `__str__`
- Update name/role/password / deactivate
- Delete when no related records
- Unique email + invalid role CheckConstraint

### Files modified
- `tests/test_ticket_models.py`
- `tests/test_user_model.py`

`tests/test_ticket_lifecycle.py` left as-is (already Task 3 complete).

