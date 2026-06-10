---
linear_issue: SHA-35
title: CI never runs build:graph-layout; committed graph layout bundles can drift from TypeScript source
priority: Mid
labels:
  - automation
  - infra
status: planned
created_by: todo-plan-automation
---

# Plan: CI freshness gate for graph-layout static bundles

## Source Issue

- Linear: SHA-35
- Status at planning time: Todo
- Priority: Mid

## Problem

Graph layout TypeScript source lives in `frontend/graph_layout/src/`, but production UI and pytest load committed esbuild outputs under `django_apps/web/static/web/js/`. CI never runs `npm run build:graph-layout`, so stale bundles can ship while tests pass.

## Scope

Add CI enforcement that committed `solver_graph_layout.js` and `editor_graph_layout.js` match `npm run build:graph-layout` output.

## Non-goals

- Rewriting the graph layout engine.
- Changing layout algorithm behavior.
- Recipe graph editor bundle drift (SHA-40).

## Implementation Plan

1. Add CI job or matrix step: `npm ci` + `npm run build:graph-layout`.
2. Fail on `git diff` for `django_apps/web/static/web/js/solver_graph_layout.js` and `editor_graph_layout.js`.
3. Run gate on current `master` first; commit any one-time sync if bundles are already stale.
4. Document gate in `documents/ai/manuals/frontend.md` and/or `docs/agent-workflows/validation-routine.md`.
5. Keep pytest importing committed bundles; CI freshness check is the regression guard.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (`build:graph-layout` script)
- `frontend/graph_layout/src/solverStaticBundle.ts`
- `frontend/graph_layout/src/editorStaticBundle.ts`
- `django_apps/web/static/web/js/solver_graph_layout.js`
- `django_apps/web/static/web/js/editor_graph_layout.js`
- `documents/ai/manuals/frontend.md`
- `tests/unit/web/test_solver_graph_layout.py`
- `tests/unit/web/test_editor_graph_layout.py`

## Validation Plan

- lint: existing CI lint matrix
- typecheck: existing CI typecheck matrix
- tests: `pytest tests/unit/web/test_solver_graph_layout.py tests/unit/web/test_editor_graph_layout.py -v`
- build: `npm ci && npm run build:graph-layout && git diff --exit-code django_apps/web/static/web/js/solver_graph_layout.js django_apps/web/static/web/js/editor_graph_layout.js`
- manual verification: Change a TS source line without rebuilding; confirm CI step fails

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- One-time bundle regen may produce a large diff if master is already stale.
- Node version in CI must match local esbuild output (pin in workflow or `.nvmrc` if drift occurs).
