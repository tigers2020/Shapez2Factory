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

Add a CI gate that regenerates `app.css` via `npm run build:css` (after `npm ci`) and fails when `django_apps/web/static/web/css/app.css` differs from the committed file. Optionally reference a small check script if that improves local/CI parity.

## Non-goals

- Do not change Tailwind token mapping or lab overlay styling.
- Do not fold graph-layout, recipe-graph-editor, or locale rebuild gates into this job (SHA-35, SHA-40, SHA-42).
- Do not edit `auth-layout.css` (hand-maintained plain CSS, not Tailwind output).

## Implementation Plan

1. Read `.github/workflows/ci.yml` matrix and follow the pattern used by other CI infra cards (e.g. SHA-19 `django-check` task addition).
2. Add a `build-css-check` matrix task (or standalone job) with Node setup:
   - `actions/setup-node@v4` with `cache: npm`
   - `npm ci`
   - `npm run build:css`
   - `git diff --exit-code django_apps/web/static/web/css/app.css`
3. Confirm the diff gate only targets `app.css` (not `auth-layout.css` or other static CSS).
4. Run locally to verify current tree is clean: `npm ci && npm run build:css && git diff --exit-code django_apps/web/static/web/css/app.css`.
5. If drift exists on the branch, commit regenerated `app.css` in the implementation PR (not this planning automation).
6. Update `DESIGN.md` § Tailwind CSS and `structure.md` build table to note the CI drift gate.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (read-only reference for `build:css` script)
- `assets/css/input.css`
- `django_apps/web/static/web/css/app.css`
- `django_apps/web/templates/web/base.html`
- `DESIGN.md`
- `structure.md`

## Validation Plan

- lint: N/A (workflow-only change)
- typecheck: N/A
- tests: `pytest -m "unit and not slow"` (ensure no regressions from workflow edit)
- build: `npm ci && npm run build:css && git diff --exit-code django_apps/web/static/web/css/app.css`
- manual verification: Temporarily edit a template utility class without rebuilding; confirm CI step would fail

## Acceptance Criteria

- [ ] CI fails when `app.css` is out of date relative to `assets/css/input.css` and scanned templates.
- [ ] The fix stays within CI/automation scope (no unrelated styling changes).
- [ ] Relevant docs mention the new gate if workflow docs are updated.
- [ ] No unrelated behavior is changed.
- [ ] Remaining frontend bundle drift risks (SHA-35, SHA-40) stay tracked separately.

## Risks / Open Questions

- Tailwind CLI output must be deterministic across Node/OS versions; pin Node version in workflow (e.g. 20 LTS) to match local dev.
- `@tailwindcss/cli` minor updates could change minified output; lockfile (`package-lock.json`) must be installed via `npm ci`.
- Current tree reports no drift (md5 `450986bed220fc6a44cda342682a81af` per triage notes); first CI run should pass on clean main.
