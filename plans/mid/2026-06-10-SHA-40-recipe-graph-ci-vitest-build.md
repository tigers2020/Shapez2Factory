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

# Plan: Gate recipe graph editor Vitest and bundle freshness in CI

## Source Issue

- Linear: SHA-40
- Status at planning time: Todo
- Priority: Mid

## Problem

Recipe Graph editor source lives in `frontend/recipe_graph_editor/` but staff pages load committed bundles under `django_apps/web/static/web/js/recipe_graph_editor/`. GitHub Actions never runs Vitest or `npm run build:recipe-graph-editor`, so PRs can change TypeScript/React logic or break wire-rule fixture alignment while leaving stale static bundles and still passing CI.

## Scope

Add CI job(s) that install Node dependencies, run `npm --prefix frontend/recipe_graph_editor test`, run `npm run build:recipe-graph-editor`, and fail when committed bundles drift from source. Optionally extend `scripts/test_fast.ps1` / docs once CI path is stable.

## Non-goals

- Fixing graph-layout bundle drift (SHA-35).
- Changing recipe graph editor runtime behavior or validation rules.
- Adding unrelated frontend build targets (`build:css`) unless required for the Vitest/build job.

## Implementation Plan

1. Add `frontend-recipe-graph` matrix task to `.github/workflows/ci.yml` (or dedicated job) with `actions/setup-node`, cache for `node_modules`.
2. Run `npm ci` at repo root and `npm --prefix frontend/recipe_graph_editor ci`.
3. Run `npm --prefix frontend/recipe_graph_editor test` (Vitest).
4. Run `npm run build:recipe-graph-editor` and `git diff --exit-code django_apps/web/static/web/js/recipe_graph_editor/` to fail on bundle drift.
5. Cross-link SHA-35 in PR description for future unified frontend static-asset CI pattern.
6. Update `documents/ai/manuals/testing.md` and/or `documents/ai/manuals/frontend.md` if CI invocation differs from documented local steps.
7. Optionally add a note to `scripts/test_fast.ps1` README or comment pointing to CI job (non-blocking local gate unless explicitly requested).

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `frontend/recipe_graph_editor/` (test invocation only)
- `package.json` (`build:recipe-graph-editor` script)
- `django_apps/web/static/web/js/recipe_graph_editor/` (drift check target)
- `documents/ai/manuals/testing.md`
- `documents/ai/manuals/frontend.md`

## Validation Plan

- lint: N/A (workflow YAML)
- typecheck: N/A
- tests: CI job runs Vitest; local `npm --prefix frontend/recipe_graph_editor test`
- build: `npm run build:recipe-graph-editor` + clean tree check
- manual verification: Open PR with intentional TS change without rebuild; CI should fail on drift

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- First CI run may fail if committed bundles already drift; may need one-time bundle rebuild PR separate from CI wiring.
- Node version pin should match local dev (`package.json` engines or existing CI Node version).
- SHA-35 graph-layout and SHA-44 `build:css` remain separate tracked gaps.
