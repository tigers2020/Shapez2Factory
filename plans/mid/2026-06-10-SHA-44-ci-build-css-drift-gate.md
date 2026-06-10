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

# Plan: CI gate for committed app.css Tailwind drift

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Mid

## Problem

Tailwind CSS for the Django web app is built from `assets/css/input.css` into committed `django_apps/web/static/web/css/app.css`. GitHub Actions never runs `npm run build:css`, so PRs can change template utility classes or `input.css` rules while leaving a stale committed `app.css` and still pass CI.

## Scope

- Add a CI gate that regenerates `app.css` via `npm run build:css` (after `npm ci`) and fails when `django_apps/web/static/web/css/app.css` differs from the committed file.
- Document the gate in operator docs if workflow docs are updated.

## Non-goals

- Changing Tailwind token mapping or lab overlay styling.
- Folding graph-layout, recipe-graph-editor, or locale rebuild gates into one umbrella job (SHA-35, SHA-40, SHA-42 remain separate).
- Editing `auth-layout.css` (hand-maintained, not Tailwind output).

## Implementation Plan

1. Read `.github/workflows/ci.yml` matrix structure and existing Node setup patterns from SHA-35/SHA-40 drift gates if present.
2. Add a `build-css-check` matrix task (or standalone job): `npm ci`, `npm run build:css`, `git diff --exit-code django_apps/web/static/web/css/app.css`.
3. Run locally: `npm ci && npm run build:css` and confirm clean diff on current `master`.
4. If catalogs are out of date on branch, regenerate and commit `app.css` once the gate lands.
5. Update `DESIGN.md` § Tailwind CSS and/or `structure.md` build table with the new CI gate reference.
6. Open PR; confirm CI fails when `app.css` is intentionally stale (negative test on branch).

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (`build:css` script)
- `assets/css/input.css`
- `django_apps/web/static/web/css/app.css`
- `DESIGN.md`
- `structure.md`
- `django_apps/web/templates/web/base.html` (loads `app.css`)

## Validation Plan

- lint: `ruff check .` (unchanged)
- typecheck: N/A for CSS gate
- tests: existing `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` unchanged unless Low follow-up adds contract test
- build: `npm run build:css` succeeds locally and in CI
- manual verification: CI fails when `app.css` is stale relative to templates/`input.css`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- CI Node version must match local Tailwind CLI output; pin via `.nvmrc` or existing CI Node matrix.
- Related bundle drift (SHA-35, SHA-40, SHA-42) remains open — document cross-links in PR description.
