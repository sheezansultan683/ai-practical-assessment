# Tool Workflow

## 1. Primary AI tool used

Cursor (Agent / chat) for gap analysis, specs, phased implementation, tests, and local debugging.

## 2. How I provide project context to the tool

I point Cursor at the brief plus locked docs (`@requirements-analysis.md`, `@acceptance-criteria.md`, `@api-contract.md`, `@data-model.md`, `@implementation-plan.md`, `.cursor/rules/*`) and ask for one small milestone at a time.

## 3. How I use AI for requirement analysis

I use AI to draft `requirements-analysis.md` and `acceptance-criteria.md`, surface gaps (auth vs CSV “self”, terminal states), then keep or reject decisions myself.

## 4. How I use AI for planning and design

I use AI to write the phased `implementation-plan.md` and design artifacts (`api-contract.md`, `data-model.md`), with the state machine as an explicit single backend allow-list.

## 5. How I use AI for code generation

I generate one phase at a time (scaffold → models/seed → transition service + matrix tests → API/JWT), reviewing before the next step.

## 6. How I validate AI-generated code

I read the diffs, run `migrate`/`seed`/`runserver`, and run pytest after each milestone; I reject overbuilt or plan-breaking suggestions.

## 7. How I use AI for testing

I require full transition-matrix tests before views, then API integration tests for auth, filters, 409 transitions, terminal freeze, and CSV scope.

## 8. How I use AI for debugging

I paste the traceback (e.g. missing `DJANGO_SECRET_KEY`) and relevant files; I verify the fix locally and keep secrets out of the chat when possible.

## 9. How I use AI for code review

I ask for reviews against the plan and lifecycle rules—correctness of transitions, validation, service-layer authority, and simplicity—not style-only nits.

## 10. What information I avoid sharing unnecessarily with AI tools

Secrets, real `.env` values, private keys, production credentials, and unrelated personal data.

## 11. How I would reuse this workflow in a real project

Same phase order, Cursor rules as project specs, locked artifacts before code, small reviewable commits, and tests that prove the signature rules before UI polish.
