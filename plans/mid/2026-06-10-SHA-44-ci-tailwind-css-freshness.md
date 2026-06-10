---
linear_issue: SHA-44
title: CI never runs build:css; committed app.css can drift from Tailwind source
priority: Mid
labels:
  - ui
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: CI never runs build:css; committed app.css can drift from Tailwind source

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Mid

## Problem

Tailwind CSS is built from `assets/css/input.css` into committed `django_apps/web/static/web/css/app.css`. GitHub Actions never runs `npm run build:css`, so template or input CSS changes can ship with stale `app.css` while CI passes.

## Scope

Add a CI gate that regenerates `app.css` via `npm run build:css` (after `npm ci`) and fails when the committed file differs.

## Non-goals

- Changing Tailwind token mapping or lab overlay styling.
- Folding graph-layout, recipe-graph-editor, or locale gates into one job.
- Editing `auth-layout.css` (hand-maintained).

## Implementation Plan

1. Add `build-css-check` task in `.github/workflows/ci.yml`: `npm ci`, `npm run build:css`, `git diff --exit-code django_apps/web/static/web/css/app.css`.
2. Optionally add repo-level contract test in `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` or new file for local fast feedback.
3. Run `npm run build:css` on current branch; commit any one-time drift before enabling gate.
4. Document gate in `DESIGN.md` § Tailwind CSS and/or `structure.md` build table.
5. Do not touch `auth-layout.css` or unrelated static assets.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (read-only)
- `assets/css/input.css`
- `django_apps/web/static/web/css/app.css`
- `DESIGN.md`
- `structure.md`
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (optional)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A for CI-only
- tests: `powershell -File scripts/test_fast.ps1`; local: `npm ci && npm run build:css && git diff --exit-code django_apps/web/static/web/css/app.css`
- build: CI workflow on branch
- manual verification: Change a template utility class without rebuild; confirm CI fails

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Node version alignment with other frontend gates (SHA-35, SHA-40).
- Pytest substring checks in `test_asteroid_lab_ui_strings.py` are partial; CI diff is authoritative.
