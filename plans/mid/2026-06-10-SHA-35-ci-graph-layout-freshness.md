---
linear_issue: SHA-35
title: CI never runs build:graph-layout; committed graph layout bundles can drift from TypeScript source
priority: Mid
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: CI freshness gate for graph-layout static bundles

## Source Issue

- Linear: SHA-35
- Status at planning time: Todo
- Priority: Mid

## Problem

GitHub Actions never runs `npm run build:graph-layout`, so PRs can change TypeScript layout logic while leaving stale `solver_graph_layout.js` and `editor_graph_layout.js` bundles committed.

## Scope

Add CI enforcement that committed bundles match `npm run build:graph-layout` output.

## Non-goals

- Rewriting the graph layout engine.
- Changing layout algorithm behavior.
- Bundling recipe graph editor assets (SHA-40).

## Implementation Plan

1. Add CI job or matrix task: `npm ci` then `npm run build:graph-layout`.
2. Fail on `git diff` for `django_apps/web/static/web/js/solver_graph_layout.js` and `editor_graph_layout.js`.
3. Verify current `master` rebuild produces no unexpected diff; commit sync if needed.
4. Document gate in `documents/ai/manuals/frontend.md` or `docs/agent-workflows/validation-routine.md`.
5. Confirm existing pytest (`test_solver_graph_layout.py`, `test_editor_graph_layout.py`) still pass.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (read-only — `build:graph-layout` script)
- `frontend/graph_layout/src/*.ts`
- `django_apps/web/static/web/js/solver_graph_layout.js`
- `django_apps/web/static/web/js/editor_graph_layout.js`
- `documents/ai/manuals/frontend.md`

## Validation Plan

- lint: N/A (CI change)
- typecheck: N/A
- tests: `pytest tests/unit/web/test_solver_graph_layout.py tests/unit/web/test_editor_graph_layout.py -v`
- build: `npm run build:graph-layout` in CI
- manual verification: PR changing TS without bundle regen fails CI

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Node version pin in CI must match local dev.
- SHA-40 recipe graph editor bundle drift tracked separately.
