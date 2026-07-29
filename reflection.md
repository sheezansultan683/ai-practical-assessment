# Reflection

## What I Built

A Support Ticket Management System with Django 5 + DRF + SQLite and a React + Vite + TypeScript frontend. Seeded users log in with JWT, then create, list, filter/search, update, comment on, and progress tickets through a fixed status machine. Self-generated tickets can be exported as CSV. Status rules live in one backend service layer; the UI only shows transitions the API returns. Stretch items included JWT auth, OpenAPI (drf-spectacular), and Cursor rules as project specs. Docker/Postgres was skipped on purpose as a time call.

## How I Used AI (across the lifecycle)

I used Cursor from start to finish: clarifying gaps in the brief, drafting requirements and acceptance criteria, designing the API and data model, writing the implementation plan, building in small milestones (scaffold → models/seed → transition service + tests → API/JWT → frontend), debugging local issues (for example missing env vars), and drafting workflow/PR/reflection docs. I gave context with `@file` references and Cursor rules so suggestions matched locked decisions.

## What AI Helped With Most

AI was strongest at turning a short brief into clear artifacts (requirements, acceptance criteria, API contract, data model, plan) and at generating the full transition-matrix tests and boilerplate settings/serializers quickly. It also helped keep the “one allow-list on the backend” rule consistent across docs and code.

## What AI Got Wrong

Early plans assumed Postgres + Docker Compose; we had to reverse that to SQLite via `DATABASE_URL`. Some drafts mixed app names (`accounts` vs `users`), used cwd-relative DB paths, or suggested running tests against the same DB file as seed data. Scaffolding also failed loudly when env vars were missing until we loaded a local `.env`. I had to push back on overbuilding and on anything that duplicated the lifecycle in the frontend.

## How I Validated AI Output

I read diffs against the plan and Cursor rules, ran `migrate` / `seed` (twice for idempotency), started the local server, and ran pytest after each milestone. I checked OpenAPI at `/api/docs/` and exercised login and ticket flows in the UI. Suggestions that broke locked decisions (hardcoded transitions, deletes, role gates on Core) were rejected.

## What I Would Improve Next

Add Docker/Postgres when time allows, strengthen concurrent transition handling on Postgres, consider status history or reopen if product asks, improve search beyond `icontains`, and move refresh tokens to httpOnly cookies. I would also finish renaming docs to the brief’s exact filenames earlier to avoid underscore/hyphen drift.

## Reusable Workflow (prompts, rules, specs, templates)

Keep a short loop: brief → requirements + acceptance criteria → Cursor rules → API contract + data model → phased plan → build one milestone → tests → review. Store prompts under `ai-prompts/`, lock product rules in `.cursor/rules/`, and keep specs at the repo root so every coding session starts from the same source of truth. Prefer small, reviewable steps over “build the whole app.”
