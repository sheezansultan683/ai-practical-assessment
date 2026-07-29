# Test Results

**Command:** `pytest` (from repo root, venv active)  
**Date:** 2026-07-29  
**Result:** **77 passed, 5 skipped** (exit code 0)  
**Duration:** ~3s  

Settings: `config.settings.test` — separate test DB; does not touch `database/tickets.db`.

## Suite breakdown

| File | What it covers |
|------|----------------|
| `tests/test_user_model.py` | Custom email user, password, role constraint |
| `tests/test_ticket_models.py` | Ticket/comment fields, FK on_delete, check constraints |
| `tests/test_ticket_lifecycle.py` | Full status transition matrix + terminal field freeze |
| `tests/test_api.py` | JWT auth, tickets API, comments, CSV export, OpenAPI |

## Skips (expected)

5 cases in `test_ticket_lifecycle.py` are skipped with reason **“valid edge covered elsewhere”** — the invalid-matrix parametrize skips the 5 legal transitions, which are already asserted in `test_valid_transitions_succeed`.

## How to re-run

```bash
source .venv/bin/activate
pytest
# or quieter:
pytest -q
```
