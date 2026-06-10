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

# Plan: CI build:css drift gate for committed app.css

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Mid

## Problem

Tailwind CSS for the Django web app is built from `assets/css/input.css` into committed `django_apps/web/static/web/css/app.css`. GitHub Actions never runs `npm run build:css`, so PRs can change template utility classes while leaving stale `app.css` and still pass CI.

## Scope

Add a CI gate that regenerates `app.css` via `npm run build:css` (after `npm ci`) and fails when the committed file drifts from builder output.

## Non-goals

- Changing Tailwind token mapping or lab overlay styling.
- Folding graph-layout, recipe-graph-editor, or locale rebuild gates into one job (SHA-35, SHA-40, SHA-42).
- Editing `auth-layout.css` (hand-maintained, not Tailwind output).

## Implementation Plan

1. Add `build-css-check` matrix task in `.github/workflows/ci.yml`: `actions/setup-node`, `npm ci`, `npm run build:css`, `git diff --exit-code django_apps/web/static/web/css/app.css`.
2. Optionally add a pytest contract test shelling out to `npm run build:css` and asserting clean diff for local fast feedback.
3. Update `DESIGN.md` / `structure.md` if operators need visibility on the new gate.
4. Regenerate and commit `app.css` if current tree is stale when gate lands.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (`build:css` script)
- `assets/css/input.css`
- `django_apps/web/static/web/css/app.css`
- `DESIGN.md`
- `structure.md`
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (optional contract extension)

## Validation Plan

- lint: N/A (CI/infra change)
- typecheck: N/A
- tests: CI matrix `build-css-check` passes on clean tree; fails when `app.css` intentionally left stale
- build: `npm run build:css` locally succeeds
- manual verification: Change a template utility class without rebuilding; confirm CI fails

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Node version pin in CI must match local dev (`package.json` engines if any).
- First gate landing may require a one-time `app.css` regen commit if drift already exists on master.
