---
linear_issue: SHA-40
title: CI never runs recipe graph editor Vitest or build:recipe-graph-editor; committed bundles can drift
priority: Mid
labels:
  - automation
  - infra
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: CI recipe graph editor Vitest and bundle freshness

## Source Issue

- Linear: SHA-40
- Status at planning time: Todo
- Priority: Mid

## Problem

The Recipe Graph editor source lives in `frontend/recipe_graph_editor/` (Vite + React Flow), but production staff graph pages load the committed bundle `django_apps/web/static/web/js/recipe_graph_editor/recipe-graph-editor.js` and `recipe-graph-editor.css`. GitHub Actions never installs Node dependencies, never runs `npm --prefix frontend/recipe_graph_editor test` (Vitest), and never runs `npm run build:recipe-graph-editor`. A PR can change TypeScript/React editor logic or break wire-rule fixture alignment while leaving stale static bundles in the repo and still pass CI.

## Scope

- Add CI job(s) that install root + `frontend/recipe_graph_editor` dependencies, run Vitest, and run `npm run build:recipe-graph-editor` with a clean-tree check (or equivalent bundle freshness gate).
- Optionally extend `scripts/test_fast.ps1` / PR docs once CI path is stable.

## Non-goals

- Fixing graph-layout bundle drift (SHA-35).
- Changing recipe graph editor runtime behavior or validation rules.
- Adding unrelated frontend build targets (`build:css`) in the same card.

## Implementation Plan

1. Add a `frontend-recipe-graph` CI matrix task in `.github/workflows/ci.yml` with `actions/setup-node`, `npm ci` at repo root, `npm --prefix frontend/recipe_graph_editor ci`.
2. Run `npm --prefix frontend/recipe_graph_editor test` (Vitest) per `documents/ai/manuals/testing.md` § Recipe Graph editor.
3. Run `npm run build:recipe-graph-editor` from root `package.json`; confirm `frontend/recipe_graph_editor/vite.config.ts` outDir → `django_apps/web/static/web/js/recipe_graph_editor/`.
4. Fail if `git diff --exit-code django_apps/web/static/web/js/recipe_graph_editor/` is non-empty after build.
5. Cross-check Python fixture alignment test `tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py` and Vitest mirror against `tests/fixtures/recipe_connection_rule_scenarios.json`.
6. Update `documents/ai/manuals/frontend.md` and `documents/ai/manuals/testing.md` if CI invocation differs from local docs.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (`build:recipe-graph-editor`)
- `frontend/recipe_graph_editor/vite.config.ts`
- `frontend/recipe_graph_editor/` (Vitest config and tests)
- `django_apps/web/static/web/js/recipe_graph_editor/recipe-graph-editor.js`
- `django_apps/web/static/web/js/recipe_graph_editor/recipe-graph-editor.css`
- `tests/fixtures/recipe_connection_rule_scenarios.json`
- `tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py`
- `documents/ai/manuals/testing.md`
- `documents/ai/manuals/frontend.md`

## Validation Plan

- lint: N/A unless workflow/docs only
- typecheck: N/A unless TS config edited
- tests: `npm --prefix frontend/recipe_graph_editor test` locally; `pytest tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py -v`
- build: `npm run build:recipe-graph-editor` then verify clean git diff on `django_apps/web/static/web/js/recipe_graph_editor/`
- manual verification: CI fails when editor source changes without regenerated bundles

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Dual `npm ci` (root + prefix) may slow CI — consider caching strategy.
- SHA-56 (Django wiring missing) is separate — Vitest/build gate does not require staff page to exist.
