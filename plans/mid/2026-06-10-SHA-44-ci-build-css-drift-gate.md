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

Tailwind CSS for the Django web app is built from `assets/css/input.css` (scanning `django_apps/web/templates` via `@source`) into the committed artifact `django_apps/web/static/web/css/app.css`. GitHub Actions never installs Node dependencies or runs `npm run build:css`, so a PR can change template utility classes or `input.css` component rules while leaving a stale committed `app.css` and still pass CI.

## Scope

Add a CI gate that regenerates `app.css` via `npm run build:css` (after `npm ci`) and fails when `django_apps/web/static/web/css/app.css` differs from the committed file, or add an equivalent deterministic check script referenced from `ci.yml`.

## Non-goals

- Changing Tailwind token mapping or lab overlay styling.
- Folding graph-layout, recipe-graph-editor, or locale rebuild gates into one umbrella CI job (SHA-35, SHA-40, SHA-42).
- Editing `auth-layout.css` (hand-maintained plain CSS, not Tailwind output).

## Implementation Plan

1. **Add CI matrix task in `.github/workflows/ci.yml`**
   - New task e.g. `build-css-check` with `actions/setup-node`, `npm ci` at repo root, `npm run build:css`.
   - Run `git diff --exit-code django_apps/web/static/web/css/app.css` after build; fail job on non-empty diff.
   - Pin Node version to match local dev (check existing workflows or `package.json` engines if present).

2. **Optional local contract test**
   - If fast local feedback is desired, add pytest in `tests/unit/` that shells out to `npm run build:css` and asserts clean diff for `app.css` only.
   - Skip if CI-only gate is sufficient to avoid Node dependency in every `test_fast` run.

3. **Baseline committed artifact**
   - On first gate landing, run `npm run build:css` locally and commit any resulting `app.css` diff so CI starts green.

4. **Document the gate**
   - Add one line to `DESIGN.md` § Tailwind CSS and/or `structure.md` build table noting CI enforces `app.css` freshness.
   - Cross-reference SHA-35/SHA-40/SHA-42 for other committed-artifact drift gates.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (`build:css` script — read-only unless script fix needed)
- `assets/css/input.css` (read-only)
- `django_apps/web/static/web/css/app.css` (may need regen commit on landing)
- `DESIGN.md`, `structure.md` (optional doc update)
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (optional extension)

## Validation Plan

- lint: N/A for workflow-only change
- typecheck: N/A
- tests: CI `build-css-check` job passes on clean tree; intentionally stale `app.css` fails job in dry run
- build: `npm run build:css` locally produces no diff when sources are current
- manual verification: Confirm `django_apps/web/templates/web/base.html` still loads committed `app.css`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] CI fails when `app.css` is out of date relative to `assets/css/input.css` and scanned templates.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining frontend bundle drift risks (SHA-35, SHA-40) stay tracked separately.

## Risks / Open Questions

- Node version mismatch between CI and local dev can cause false-positive diffs; pin Node in workflow.
- Minified CSS output may vary slightly across Tailwind CLI versions; lock `@tailwindcss/cli` version in `package-lock.json`.
- First landing may require a large `app.css` regen commit if current committed file is already stale.
