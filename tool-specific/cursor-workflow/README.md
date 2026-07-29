# Cursor workflow

Primary AI tool for this assessment: **Cursor** (Agent / chat).

## What lives where

| Location | Role |
|----------|------|
| [`.cursor/rules/`](../../.cursor/rules/) | Reusable project rules applied while coding |
| [`ai-prompts/`](../../ai-prompts/) | Exported prompt / chat history by phase |
| [`tool-workflow.md`](../../tool-workflow.md) | Short answers on how AI was used end-to-end |

### Cursor rules (Stretch evidence)

- [`stack-and-conventions.mdc`](../../.cursor/rules/stack-and-conventions.mdc) — stack, JWT, service layer, secrets, snake_case API
- [`ticket-lifecycle.mdc`](../../.cursor/rules/ticket-lifecycle.mdc) — status allow-list, 409 vs 400, terminal freeze, CSV scope

### Prompt history

- `planning.md` — gaps, requirements, acceptance criteria
- `design.md` — API contract / data model / frontend design
- `testing.md` — lifecycle and API tests
- `debugging.md` — local env / server issues
- `documentation.md` — OpenAPI / drf-spectacular

(`implementation.md` and `code-review.md` can be added if those chat exports are saved later.)

## How Cursor was used on this project

1. Point Agent at locked docs (`@requirements-analysis.md`, `@api-contract.md`, `@implementation-plan.md`, rules).
2. Build one milestone at a time (scaffold → models/seed → transition service + matrix tests → API/JWT → frontend).
3. Review diffs against the rules; run `migrate` / `seed` / `pytest` / local UI.
4. Reject suggestions that break locked decisions (hardcoded FE transitions, deletes, role gates on Core, secrets in git).

## Day-to-day habits

- Prefer small prompts over “build everything”
- Keep secrets in `.env` only (never paste production credentials into chat)
- Treat the backend allow-list as the single source of truth for status transitions
