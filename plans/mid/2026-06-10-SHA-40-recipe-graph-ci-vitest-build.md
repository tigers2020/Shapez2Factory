---
linear_issue: SHA-40
title: CI never runs recipe graph editor Vitest or build:recipe-graph-editor; committed bundles can drift
priority: Mid
labels:
  - automation
  - infra
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: CI never runs recipe graph editor Vitest or build:recipe-graph-editor; committed bundles can drift

## Source Issue

- Linear: SHA-40
- Status at planning time: In Progress
- Priority: Mid

## Problem

The Recipe Graph editor source lives in `frontend/recipe_graph_editor/` (Vite + React Flow), but production staff graph pages load the committed bundle `django_apps/web/static/web/js/recipe_graph_editor/recipe-graph-editor.js` and `recipe-graph-editor.css`. GitHub Actions never installs Node dependencies, never runs `npm --prefix frontend/recipe_graph_editor test` (Vitest), and never runs `npm run build:recipe-graph-editor`. A PR can change TypeScript/React editor logic or break wire-rule fixture alignment while leaving stale static bundles in the repo and still pass CI.

## Scope

- Add a CI matrix task (or dedicated job) that installs root + `frontend/recipe_graph_editor` dependencies, runs Vitest, runs `npm run build:recipe-graph-editor`, and fails when committed bundles drift from source.
- Optionally extend `scripts/test_fast.ps1` / PR docs once the CI path is stable.
- Align `documents/ai/manuals/testing.md` and `documents/ai/manuals/frontend.md` with the new CI gate if workflow docs are updated.

## Non-goals

- Fixing graph-layout bundle drift (SHA-35).
- Changing recipe graph editor runtime behavior or validation rules.
- Adding unrelated frontend build targets (`build:css`) in the same card unless required for the Vitest/build job.

## Implementation Plan

1. Add `frontend-recipe-graph` to the CI matrix in `.github/workflows/ci.yml` (or a standalone job with the same `pull_request` / `push` triggers).
2. In that task, add `actions/setup-node@v4` with a pinned Node LTS version and npm cache for root `package-lock.json` and `frontend/recipe_graph_editor/package-lock.json`.
3. Run dependency install:
   - `npm ci` at repo root
   - `npm --prefix frontend/recipe_graph_editor ci`
4. Run Vitest: `npm --prefix frontend/recipe_graph_editor test`
5. Run bundle build: `npm run build:recipe-graph-editor`
6. Fail on drift: `git diff --exit-code django_apps/web/static/web/js/recipe_graph_editor/`
7. If the drift check fails in CI, document the operator fix (`npm run build:recipe-graph-editor` + commit) in the job log message or a short note in `structure.md` / `testing.md`.
8. Optionally add a local mirror step to `scripts/test_fast.ps1` after CI is green (Vitest only or Vitest + build diff — keep scope minimal).
9. Open PR; confirm matrix task runs on pull requests.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (read-only unless script wiring needed)
- `frontend/recipe_graph_editor/package.json`
- `frontend/recipe_graph_editor/vite.config.ts` (outDir reference only)
- `django_apps/web/static/web/js/recipe_graph_editor/` (drift-checked output)
- `documents/ai/manuals/testing.md`
- `documents/ai/manuals/frontend.md`
- `scripts/test_fast.ps1` (optional)
- `tests/fixtures/recipe_connection_rule_scenarios.json` (fixture parity context; no change unless tests fail)
- `tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py` (Python side; no change unless parity breaks)

## Validation Plan

- lint: `ruff check .` (unchanged; confirm no regressions)
- typecheck: `mypy django_apps config src` per AGENTS.md if touching Python (unlikely)
- tests: `npm --prefix frontend/recipe_graph_editor test`
- build: `npm run build:recipe-graph-editor` then `git diff --exit-code django_apps/web/static/web/js/recipe_graph_editor/`
- manual verification: open a staff recipe graph page locally and confirm `recipe-graph-editor.js` / `.css` load from `/static/web/js/recipe_graph_editor/`

## Acceptance Criteria

- [ ] CI runs `npm --prefix frontend/recipe_graph_editor test` on every PR.
- [ ] CI runs `npm run build:recipe-graph-editor` and fails when committed bundles drift from source.
- [ ] Manuals (`testing.md`, `frontend.md`) and CI stay aligned.
- [ ] No unrelated behavior is changed.
- [ ] Remaining frontend bundle gaps (e.g. `build:css`, graph-layout per SHA-35) are documented or tracked separately.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Node version mismatch between local dev and CI can cause spurious bundle diffs; pin Node in workflow.
- Vite/Tailwind output ordering may cause flaky diffs; if observed, document deterministic build env or add `.gitattributes` normalization (only if proven necessary).
- Root `npm ci` installs esbuild/tailwind used by other build targets; keep this job scoped to recipe-graph only (do not run `build:css` or `build:graph-layout` here per non-goals).
- Related drift cards SHA-35, SHA-44, SHA-42 remain separate; cross-link in PR description.
