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

# Plan: CI gate recipe graph editor Vitest and committed bundle freshness

## Source Issue

- Linear: SHA-40
- Status at planning time: In Progress (triggered from Todo)
- Priority: Mid

## Problem

The Recipe Graph editor source lives in `frontend/recipe_graph_editor/` (Vite + React Flow), but production staff graph pages load committed bundles under `django_apps/web/static/web/js/recipe_graph_editor/`. GitHub Actions never installs Node dependencies, never runs Vitest (`npm --prefix frontend/recipe_graph_editor test`), and never runs `npm run build:recipe-graph-editor`. A PR can change TypeScript/React editor logic or break wire-rule fixture alignment while leaving stale static bundles in the repo and still pass CI.

## Scope

- Add a CI job or matrix task that installs root and `frontend/recipe_graph_editor` dependencies, runs Vitest, runs `npm run build:recipe-graph-editor`, and fails when committed bundles drift from source.
- Optionally extend `scripts/test_fast.ps1` and operator docs once the CI path is stable and green.
- Align `documents/ai/manuals/testing.md` and `documents/ai/manuals/frontend.md` with the new CI gate.

## Non-goals

- Fixing graph-layout bundle drift ([SHA-35](https://linear.app/zkaufman/issue/SHA-35)).
- Changing recipe graph editor runtime behavior or validation rules.
- Adding unrelated frontend build targets (`build:css`, locale catalogs) in the same card.

## Implementation Plan

1. Add `frontend-recipe-graph` to `.github/workflows/ci.yml` matrix (or a dedicated job) with `actions/setup-node`, `npm ci` at repo root, `npm --prefix frontend/recipe_graph_editor ci`, `npm --prefix frontend/recipe_graph_editor test`, then `npm run build:recipe-graph-editor`.
2. After build, run `git diff --exit-code django_apps/web/static/web/js/recipe_graph_editor/`; fail the job on any diff so stale `recipe-graph-editor.js` / `recipe-graph-editor.css` cannot merge.
3. Pin Node version consistently with other frontend work (check existing repo convention or use LTS `20.x` if none).
4. Update `documents/ai/manuals/testing.md` § Recipe Graph editor and `documents/ai/manuals/frontend.md` to state CI runs Vitest and bundle freshness on every PR.
5. Optionally add a local mirror step to `scripts/test_fast.ps1` (Vitest only or Vitest + build diff) after CI is stable; document in `docs/agent-workflows/validation-routine.md` if added.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (`build:recipe-graph-editor` script — verify only, no change expected)
- `frontend/recipe_graph_editor/package.json`
- `frontend/recipe_graph_editor/vite.config.ts` (outDir → `django_apps/web/static/web/js/recipe_graph_editor/`)
- `django_apps/web/static/web/js/recipe_graph_editor/recipe-graph-editor.js`
- `django_apps/web/static/web/js/recipe_graph_editor/recipe-graph-editor.css`
- `tests/fixtures/recipe_connection_rule_scenarios.json` (fixture parity context)
- `tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py` (Python side; unchanged unless docs cross-link)
- `documents/ai/manuals/testing.md`
- `documents/ai/manuals/frontend.md`
- `scripts/test_fast.ps1` (optional)

## Validation Plan

- lint: N/A for this card (CI workflow YAML only)
- typecheck: N/A unless editor source touched
- tests: `npm --prefix frontend/recipe_graph_editor test`
- build: `npm run build:recipe-graph-editor` then `git diff --exit-code django_apps/web/static/web/js/recipe_graph_editor/`
- manual verification: Open PR with intentional bundle drift; confirm CI fails. Open PR with source-only change and rebuilt bundles; confirm CI passes.

## Acceptance Criteria

- [ ] CI runs `npm --prefix frontend/recipe_graph_editor test` on every PR.
- [ ] CI runs `npm run build:recipe-graph-editor` and fails when committed bundles drift from source.
- [ ] Manuals (`testing.md`, `frontend.md`) and CI stay aligned.
- [ ] No unrelated behavior is changed.
- [ ] Remaining frontend bundle gaps (`build:css`, graph-layout per SHA-35) are documented or tracked separately.

## Risks / Open Questions

- Vitest or Vite build may need Node cache keys for both root and `frontend/recipe_graph_editor` lockfiles.
- First green CI run may require committing regenerated bundles if current committed artifacts are stale.
- Cross-link [SHA-35](https://linear.app/zkaufman/issue/SHA-35) for future unified frontend static-asset CI pattern (see Low plan).
