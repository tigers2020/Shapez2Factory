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

# Plan: CI gate for Tailwind app.css freshness

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Mid

## Problem

Tailwind CSS builds from `assets/css/input.css` into committed `django_apps/web/static/web/css/app.css`, but CI never runs `npm run build:css`. PRs can change template utilities while leaving stale `app.css`.

## Scope

Add CI gate: `npm ci`, `npm run build:css`, `git diff --exit-code django_apps/web/static/web/css/app.css`.

## Non-goals

- Changing Tailwind tokens or lab overlay styling.
- Folding graph-layout, recipe-graph-editor, or locale gates into one job.
- Editing `auth-layout.css`.

## Implementation Plan

1. Add `build-css-check` matrix task in `.github/workflows/ci.yml`.
2. Optionally add pytest contract test shelling out to `npm run build:css` for local fast feedback.
3. Document gate in `DESIGN.md` / `structure.md` if operators need visibility.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json`
- `assets/css/input.css`
- `django_apps/web/static/web/css/app.css`
- `DESIGN.md`
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (optional)

## Validation Plan

- lint: N/A for CI-only
- typecheck: N/A
- tests: optional contract test
- build: verify CI job passes on clean tree
- manual verification: Change template class without rebuild; confirm gate fails.

## Acceptance Criteria

- [ ] CI fails when `app.css` is out of date.
- [ ] Fix stays within CI/automation scope.
- [ ] Docs updated if workflow docs change.
- [ ] No unrelated behavior changed.
- [ ] Other bundle drift risks (SHA-35, SHA-40, SHA-42) tracked separately.

## Risks / Open Questions

- Gate may fail until `app.css` regenerated if currently drifted.
- Node version in CI must match local Tailwind CLI expectations.
