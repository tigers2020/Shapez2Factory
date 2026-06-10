---
linear_issue: SHA-44
title: CI never runs build:css; committed app.css can drift from Tailwind source
priority: Mid
labels:
  - automation
  - infra
  - ui
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Add CI gate for committed Tailwind app.css freshness

## Source Issue

- Linear: SHA-44
- Status at planning time: In Progress
- Priority: Mid

## Problem

Tailwind CSS for the Django web app is built from `assets/css/input.css` (scanning `django_apps/web/templates` via `@source`) into the committed artifact `django_apps/web/static/web/css/app.css`. GitHub Actions never installs Node dependencies or runs `npm run build:css`, so a PR can change template utility classes or `input.css` component rules while leaving a stale committed `app.css` and still pass CI.

## Scope

Add a CI gate that regenerates `app.css` via `npm run build:css` (after `npm ci`) and fails when `django_apps/web/static/web/css/app.css` differs from the committed file. Document the gate beside existing frontend build notes if workflow docs are touched.

## Non-goals

- Do not change Tailwind token mapping or lab overlay styling.
- Do not fold graph-layout, recipe-graph-editor, or locale rebuild gates into this job (tracked separately: SHA-35, SHA-40, SHA-42).
- Do not edit `auth-layout.css` (hand-maintained plain CSS, not Tailwind output).

## Implementation Plan

1. Open `.github/workflows/ci.yml` and add a `build-css-check` matrix task (or a standalone job) alongside existing `lint`, `typecheck`, `format`, `test-fast`, and `test-integration` tasks.
2. In the new task steps, add `actions/setup-node@v4` with Node 20+ and npm cache keyed on `package-lock.json`.
3. Run `npm ci`, then `npm run build:css` (command from root `package.json`: `npx @tailwindcss/cli -i ./assets/css/input.css -o ./django_apps/web/static/web/css/app.css --minify`).
4. Fail the job when the rebuild dirties the tree: `git diff --exit-code django_apps/web/static/web/css/app.css` (or `git diff --quiet` with a clear failure message listing the drift).
5. If `app.css` is currently stale on `main`, run `npm run build:css` locally on a prep commit so the new gate is green before merge.
6. Update `DESIGN.md` § Tailwind CSS and/or `structure.md` build table with one line noting CI enforces `app.css` freshness after template/`input.css` changes.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (read-only unless script tweak needed)
- `assets/css/input.css`
- `django_apps/web/static/web/css/app.css`
- `DESIGN.md`
- `structure.md`

## Validation Plan

- build: `npm ci && npm run build:css && git diff --exit-code django_apps/web/static/web/css/app.css`
- lint: `ruff check .` (if workflow YAML only, optional)
- tests: existing CI matrix unchanged for Python gates
- manual verification: open a PR that changes a template class without rebuilding `app.css` and confirm the new CI task fails

## Acceptance Criteria

- [ ] CI fails when `app.css` is out of date relative to `assets/css/input.css` and scanned templates.
- [ ] The fix stays within CI/automation scope (no unrelated styling changes).
- [ ] Relevant docs mention the new gate if workflow docs are updated.
- [ ] No unrelated behavior is changed.
- [ ] Remaining frontend bundle drift risks (SHA-35, SHA-40) stay tracked separately.

## Risks / Open Questions

- Tailwind v4 rebuild output must be deterministic across Linux CI and local dev (watch for line-ending or minify ordering drift).
- First merge may require a one-time `app.css` refresh if `main` is already stale.
