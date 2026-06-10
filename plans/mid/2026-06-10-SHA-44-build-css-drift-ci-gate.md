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

# Plan: CI build:css drift gate

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Mid

## Problem

Tailwind CSS for the Django web app is built from `assets/css/input.css` into committed `django_apps/web/static/web/css/app.css`. GitHub Actions never runs `npm run build:css`, so PRs can change template utility classes or `input.css` rules while leaving a stale committed `app.css` and still pass CI.

## Scope

Add a CI gate that runs `npm ci` + `npm run build:css` and fails when `django_apps/web/static/web/css/app.css` differs from the committed file.

## Non-goals

- Changing Tailwind token mapping or lab overlay styling
- Folding graph-layout, recipe-graph-editor, or locale rebuild gates into one job (SHA-35, SHA-40, SHA-42)
- Editing `auth-layout.css` (hand-maintained, not Tailwind output)

## Implementation Plan

1. Add `build-css-check` matrix task in `.github/workflows/ci.yml`: `npm ci`, `npm run build:css`, `git diff --exit-code django_apps/web/static/web/css/app.css`.
2. Optionally add `tests/unit/test_app_css_freshness.py` shelling out to `npm run build:css` for local fast feedback.
3. Update `DESIGN.md` / `structure.md` frontend build notes if operators need visibility.
4. Regenerate and commit `app.css` if current sources produce drift on `master`.

## Files / Areas Likely Affected

- `assets/css/input.css`
- `django_apps/web/static/web/css/app.css`
- `django_apps/web/templates/web/base.html`
- `package.json`
- `.github/workflows/ci.yml`
- `DESIGN.md`
- `structure.md`
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (reference)
- `tests/unit/test_app_css_freshness.py` (optional new)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: optional pytest contract test
- build: `npm ci && npm run build:css`
- manual verification: `git diff --exit-code django_apps/web/static/web/css/app.css`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- CI needs Node setup alongside Python matrix jobs.
- Related bundle drift cards (SHA-35, SHA-40, SHA-42) remain separate.
