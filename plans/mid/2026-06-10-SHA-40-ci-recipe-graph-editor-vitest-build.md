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

# Plan: Add recipe graph editor Vitest and bundle drift gate to CI

## Source Issue

- Linear: SHA-40
- Status at planning time: Todo
- Priority: Mid

## Problem

The Recipe Graph editor source lives in `frontend/recipe_graph_editor/` (Vite + React Flow), but production staff graph pages load the committed bundle under `django_apps/web/static/web/js/recipe_graph_editor/`. GitHub Actions never installs Node dependencies, never runs Vitest, and never runs `npm run build:recipe-graph-editor`. PRs can change TypeScript/React editor logic or break wire-rule fixture alignment while leaving stale static bundles and still passing CI.

## Scope

Add CI job(s) that install root + `frontend/recipe_graph_editor` dependencies, run Vitest, and run `npm run build:recipe-graph-editor` with a clean-tree check (or equivalent bundle freshness gate). Optionally extend `scripts/test_fast.ps1` / PR docs once CI path is stable.

## Non-goals

- Fixing graph-layout bundle drift (SHA-35)
- Changing recipe graph editor runtime behavior or validation rules
- Adding unrelated frontend build targets (`build:css`) unless required for the Vitest/build job

## Implementation Plan

1. Read `frontend/recipe_graph_editor/vite.config.ts` outDir, root `package.json` scripts (`build:recipe-graph-editor`), and existing `ci.yml` matrix pattern.
2. Add `frontend-recipe-graph` CI matrix task (or dedicated job) with:
   - `actions/setup-node` (match repo Node version from `.nvmrc` or `package.json` engines if present)
   - `npm ci` at repo root
   - `npm --prefix frontend/recipe_graph_editor ci`
   - `npm --prefix frontend/recipe_graph_editor test`
   - `npm run build:recipe-graph-editor`
3. After build, fail if committed bundles drift:
   ```bash
   git diff --exit-code django_apps/web/static/web/js/recipe_graph_editor/
   ```
4. Verify locally: run Vitest + build + diff check on clean tree.
5. Cross-link SHA-35 in PR description for future unified frontend static-asset CI pattern.
6. Optionally update `documents/ai/manuals/testing.md` or `docs/agent-workflows/validation-routine.md` if CI matrix is documented there.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `frontend/recipe_graph_editor/` (reference)
- `package.json` (`build:recipe-graph-editor`)
- `django_apps/web/static/web/js/recipe_graph_editor/` (drift target)
- `tests/fixtures/recipe_connection_rule_scenarios.json` (Vitest alignment)
- `documents/ai/manuals/testing.md` (optional doc sync)
- `scripts/test_fast.ps1` (optional extension)

## Validation Plan

- lint: unchanged Python lint
- typecheck: unchanged
- tests: CI runs `npm --prefix frontend/recipe_graph_editor test`
- build: CI runs `npm run build:recipe-graph-editor` + git diff gate
- manual verification:
  - Local Vitest pass
  - Local build produces no diff on committed bundles

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Node version pinning:** CI Node version must match local dev; check `.nvmrc` / `engines`.
- **npm ci flakiness:** Lockfile drift between root and `frontend/recipe_graph_editor` may need documented install order.
- **SHA-35 pattern:** Graph-layout bundle CI is separate; unified frontend job is future work.
- **Pre-existing bundle drift:** If current committed bundles are stale, first CI run may fail until bundles are rebuilt in a separate PR (out of scope unless blocker).
