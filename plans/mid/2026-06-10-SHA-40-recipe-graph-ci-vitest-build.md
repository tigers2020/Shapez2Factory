---
linear_issue: SHA-40
title: CI never runs recipe graph editor Vitest or build:recipe-graph-editor
priority: Mid
labels:
  - automation
  - infra
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: CI gate recipe graph editor Vitest and bundle freshness

## Source Issue

- Linear: SHA-40
- Status at planning time: Todo
- Priority: Mid

## Problem

GitHub Actions never runs Vitest or `npm run build:recipe-graph-editor`. PRs can change TypeScript/React editor logic while committed static bundles in `django_apps/web/static/web/js/recipe_graph_editor/` drift undetected.

## Scope

- Add CI job installing Node deps, running Vitest, running build, failing on dirty bundle tree.
- Optionally extend `test_fast.ps1` / docs once CI path is stable.

## Non-goals

- Graph-layout bundle drift (SHA-35).
- Changing recipe graph editor runtime behavior.
- Unrelated frontend targets (`build:css`) unless required.

## Implementation Plan

1. Add `frontend-recipe-graph` CI matrix task with `setup-node`, root `npm ci`, `npm --prefix frontend/recipe_graph_editor ci`.
2. Run `npm --prefix frontend/recipe_graph_editor test`.
3. Run `npm run build:recipe-graph-editor`.
4. Fail if `git diff --exit-code django_apps/web/static/web/js/recipe_graph_editor/` is non-empty.
5. Cross-link SHA-35 for unified frontend static-asset pattern.
6. Update `documents/ai/manuals/testing.md` if CI invocation differs from local docs.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `frontend/recipe_graph_editor/`
- `package.json`
- `documents/ai/manuals/testing.md`

## Validation Plan

- tests: Vitest in CI job
- build: `npm run build:recipe-graph-editor` + clean tree check
- manual verification: PR changing TS without rebuild fails CI

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Node version pin must match local dev; align with existing frontend jobs if any.
