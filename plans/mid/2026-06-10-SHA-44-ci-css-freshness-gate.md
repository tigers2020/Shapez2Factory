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

# Plan: CI Tailwind app.css freshness gate

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Mid

## Problem

Tailwind CSS is built from `assets/css/input.css` into committed `django_apps/web/static/web/css/app.css`. CI never runs `npm run build:css`, so template utility changes can ship with stale CSS.

## Scope

Add CI gate: `npm ci`, `npm run build:css`, `git diff --exit-code django_apps/web/static/web/css/app.css`.

## Non-goals

- Changing Tailwind token mapping or lab overlay styling
- Folding other frontend bundle gates (SHA-35, SHA-40, SHA-42)
- Editing `auth-layout.css` (hand-maintained)

## Implementation Plan

1. Add `build-css-check` matrix task in `.github/workflows/ci.yml` with `setup-node`, `npm ci`, `npm run build:css`, git diff on `app.css`.
2. Verify master produces clean diff after build.
3. Optionally extend `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` with shell-out freshness test for local fast feedback.
4. Document gate in `DESIGN.md` § Tailwind CSS and/or `structure.md` build table.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (`build:css`)
- `assets/css/input.css`
- `django_apps/web/static/web/css/app.css`
- `DESIGN.md`
- `structure.md`

## Validation Plan

- tests: optional pytest contract; existing UI string tests unchanged
- build: `npm ci && npm run build:css && git diff --exit-code django_apps/web/static/web/css/app.css`
- manual verification: add utility class to template, confirm CI fails without rebuild

## Acceptance Criteria

- [ ] CI fails when `app.css` is out of date relative to sources.
- [ ] Fix stays within CI/automation scope.
- [ ] Relevant docs mention the gate if updated.
- [ ] No unrelated behavior changed.
- [ ] Remaining frontend bundle drift risks tracked separately.

## Risks / Open Questions

- Tailwind CLI version drift between local and CI — pin Node/npm lockfile.
- Related: SHA-35, SHA-40, SHA-42 bundle gates remain separate.
