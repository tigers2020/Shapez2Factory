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

# Plan: Add CI gate for Tailwind app.css drift

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Mid

## Problem

Tailwind CSS is built from `assets/css/input.css` (scanning `django_apps/web/templates` via `@source`) into committed `django_apps/web/static/web/css/app.css`. GitHub Actions never runs `npm ci` or `npm run build:css`, so PRs can change template utilities or `input.css` while leaving stale `app.css` and still pass CI.

## Scope

Add a CI gate that runs `npm ci`, `npm run build:css`, and fails when `django_apps/web/static/web/css/app.css` differs from the committed file.

## Non-goals

- Changing Tailwind token mapping or lab overlay styling.
- Folding graph-layout, recipe-graph-editor, or locale rebuild gates into one job (SHA-35, SHA-40, SHA-42).
- Editing `auth-layout.css` (hand-maintained, not Tailwind output).

## Implementation Plan

1. Open `.github/workflows/ci.yml` and locate the matrix jobs (`lint`, `typecheck`, `format`, `test-fast`, `test-integration`).
2. Add a `build-css-check` job (or matrix entry):

```yaml
build-css-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: "20"
        cache: npm
    - run: npm ci
    - run: npm run build:css
    - run: git diff --exit-code django_apps/web/static/web/css/app.css
```

3. Align Node version with existing frontend jobs if any (check `package.json` engines).
4. Optionally add repo-level contract test in `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` or new `tests/unit/web/test_app_css_drift.py` that shells `npm run build:css` and asserts clean diff — only if local fast feedback is desired (mirror SHA-35 pattern if present).
5. Update `DESIGN.md` § Tailwind CSS and/or `structure.md` build table to mention the new CI gate.
6. Verify locally: `npm ci && npm run build:css && git diff --exit-code django_apps/web/static/web/css/app.css`.
7. Commit workflow + doc updates.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (reference `build:css` script)
- `assets/css/input.css`
- `django_apps/web/static/web/css/app.css`
- `DESIGN.md`
- `structure.md`
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (optional)

## Validation Plan

- lint: N/A (workflow YAML)
- typecheck: N/A
- tests: optional local drift test; CI job is primary gate
- build: `npm run build:css` succeeds on clean tree
- manual verification: intentional `input.css` change without rebuild fails `git diff --exit-code`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Node/npm version drift between local dev and CI — pin in workflow.
- Related bundle drift gates remain separate (SHA-35, SHA-40, SHA-42).
