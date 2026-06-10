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

Tailwind CSS for the Django web app is built from `assets/css/input.css` (scanning `django_apps/web/templates` via `@source`) into the committed artifact `django_apps/web/static/web/css/app.css`. GitHub Actions never installs Node dependencies or runs `npm run build:css`, so a PR can change template utility classes or `input.css` component rules while leaving a stale committed `app.css` and still pass CI.

## Scope

Add a CI gate that regenerates `app.css` via `npm run build:css` (after `npm ci`) and fails when `django_apps/web/static/web/css/app.css` differs from the committed file.

## Non-goals

- Do not change Tailwind token mapping or lab overlay styling.
- Do not fold graph-layout, recipe-graph-editor, or locale rebuild gates into this job (SHA-35, SHA-40, SHA-42).
- Do not edit `auth-layout.css` (hand-maintained plain CSS, not Tailwind output).

## Implementation Plan

1. Open `.github/workflows/ci.yml` and add a `build-css-check` matrix task (or standalone job) alongside existing `lint`, `typecheck`, `format`, `test-fast`, `test-integration`.
2. For the new task, add Node setup (`actions/setup-node@v4` with npm cache), run `npm ci`, then `npm run build:css`.
3. After rebuild, run `git diff --exit-code django_apps/web/static/web/css/app.css` so CI fails when the committed artifact is stale.
4. If the current committed `app.css` is already out of date, regenerate locally with `npm run build:css` and commit the refreshed artifact in the same PR (no styling intent changes — drift correction only).
5. Verify the workflow step names and matrix case block mirror the pattern used for other frontend drift gates once SHA-35/SHA-40 land; until then, keep this gate scoped to `app.css` only.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (read-only — `build:css` script already defined)
- `assets/css/input.css` (read-only unless drift fix required)
- `django_apps/web/static/web/css/app.css` (only if regenerating stale output)
- `django_apps/web/templates/web/base.html` (read-only — confirms `app.css` load path)

## Validation Plan

- lint: N/A (workflow-only change)
- typecheck: N/A
- tests: `powershell -File scripts/test_fast.ps1` (ensure no regressions)
- build: Run `npm ci && npm run build:css && git diff --exit-code django_apps/web/static/web/css/app.css` locally; confirm exit 0 on clean tree
- manual verification: Open a PR that changes a template utility class without rebuilding `app.css`; confirm CI `build-css-check` fails

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] CI fails when `app.css` is out of date relative to `assets/css/input.css` and scanned templates.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining frontend bundle drift risks (SHA-35, SHA-40) stay tracked separately.

## Risks / Open Questions

- Tailwind v4 rebuild output may differ slightly across `@tailwindcss/cli` patch versions; pin versions in `package-lock.json` if drift flakes appear.
- Minified output ordering could cause noisy diffs if CLI version changes; document lockfile discipline in PR notes.
