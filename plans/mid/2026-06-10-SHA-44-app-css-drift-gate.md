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

# Plan: Tailwind app.css committed-artifact drift gate

## Source Issue

- Linear: SHA-44
- Status at planning time: In Progress (moved before plan land)
- Priority: Mid

## Problem

Tailwind CSS for the Django web app is built from `assets/css/input.css` (scanning `django_apps/web/templates` via `@source`) into committed `django_apps/web/static/web/css/app.css`. GitHub Actions never runs `npm ci` / `npm run build:css`, so PRs can change template utilities or `input.css` rules while leaving stale `app.css` and still pass CI.

## Scope

Add a CI gate that regenerates `app.css` via `npm run build:css` (after `npm ci`) and fails when `django_apps/web/static/web/css/app.css` differs from committed output. Document the gate in `DESIGN.md` / `structure.md` if operator docs need updating.

## Non-goals

- Do not change Tailwind token mapping or lab overlay styling.
- Do not fold graph-layout, recipe-graph-editor, or locale rebuild gates into one umbrella CI job (SHA-35, SHA-40, SHA-42).
- Do not edit `auth-layout.css` (hand-maintained, not Tailwind output).

## Implementation Plan

1. **Add CI matrix task `build-css-check`**
   - Edit `.github/workflows/ci.yml` matrix to include `build-css-check` (or standalone job with same `ubuntu-latest` + checkout pattern).
   - Steps for the task:
     - `actions/setup-node` with version from `package.json` engines or repo convention.
     - `npm ci`
     - `npm run build:css` (`npx @tailwindcss/cli -i ./assets/css/input.css -o ./django_apps/web/static/web/css/app.css --minify`)
     - `git diff --exit-code django_apps/web/static/web/css/app.css`
   - Failure message: instruct dev to run `npm run build:css` and commit `app.css`.

2. **Optional local contract test**
   - If fast local feedback is desired, add `tests/unit/test_app_css_freshness.py` shelling out to `npm run build:css` and asserting clean diff (skip if `node`/`npm` unavailable via `pytest.importorskip` or env marker).
   - Keep separate from `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` substring guards — those are partial class checks, not full rebuild gate.

3. **Regenerate `app.css` if currently drifted**
   - Run `npm ci && npm run build:css` locally.
   - If diff exists, commit `django_apps/web/static/web/css/app.css` in the same PR as the CI gate.

4. **Document operator workflow**
   - Update `DESIGN.md` § Tailwind CSS and/or `structure.md` build table to note CI enforces committed `app.css` freshness.
   - Cross-reference SHA-35/SHA-40/SHA-42 as sibling drift gates.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (read `build:css` script)
- `assets/css/input.css`
- `django_apps/web/static/web/css/app.css`
- `DESIGN.md`
- `structure.md`
- `tests/unit/test_app_css_freshness.py` (optional)
- `django_apps/web/templates/web/base.html` (reference only)

## Validation Plan

- lint: `ruff check .`
- typecheck: per AGENTS.md canon
- tests: `pytest -m "unit and not slow"` (existing); optional new CSS freshness test
- build: `npm ci && npm run build:css` then `git diff --exit-code django_apps/web/static/web/css/app.css`
- manual verification: add a Tailwind utility class to a template, rebuild, confirm CI/local gate fails without commit

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- CI must install Node — first frontend step in Python-centric workflow; cache `npm` for speed.
- Tailwind CLI output should be deterministic across Linux CI; verify minified output stable.
- Optional pytest that requires Node may be skipped locally on machines without npm — CI job is authoritative.
