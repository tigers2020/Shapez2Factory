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

# Plan: Add Tailwind app.css drift gate to CI

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Mid

## Problem

Tailwind CSS is built from `assets/css/input.css` into committed `django_apps/web/static/web/css/app.css`. GitHub Actions never runs `npm run build:css`, so PRs can change template utilities or input rules while leaving stale `app.css` and still pass CI.

## Scope

Add a CI gate that runs `npm run build:css` (after `npm ci`) and fails when `django_apps/web/static/web/css/app.css` differs from the committed file.

## Non-goals

- Changing Tailwind token mapping or lab overlay styling
- Folding graph-layout, recipe-graph-editor, or locale gates into one job (SHA-35, SHA-40, SHA-42)
- Editing `auth-layout.css` (hand-maintained)

## Implementation Plan

1. Add `build-css-check` matrix task in `ci.yml`:
   - `actions/setup-node`
   - `npm ci`
   - `npm run build:css`
   - `git diff --exit-code django_apps/web/static/web/css/app.css`
2. Optionally add pytest contract test shelling out to build for local fast feedback.
3. Update `DESIGN.md` / `structure.md` if operator docs list CI gates.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (`build:css`)
- `assets/css/input.css`
- `django_apps/web/static/web/css/app.css`
- `DESIGN.md` (optional)
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (optional)

## Validation Plan

- build: CI `npm run build:css` + git diff
- manual verification: local build produces no diff on clean tree

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Pre-existing `app.css` drift may fail first CI run until rebuild committed.
- Node version must match local dev environment.
