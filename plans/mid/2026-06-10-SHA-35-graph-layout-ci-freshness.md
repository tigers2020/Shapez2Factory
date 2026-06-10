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

Graph layout source is `frontend/graph_layout/src/*.ts` but production loads committed `solver_graph_layout.js` and `editor_graph_layout.js`. CI never runs `npm run build:graph-layout`, so TypeScript changes can merge with stale bundles and still pass tests.

## Scope

Add CI enforcement that committed bundles match `npm run build:graph-layout` output.

## Non-goals

- Rewriting graph layout engine.
- Changing layout algorithm behavior.
- Recipe graph editor bundles (SHA-40).

## Implementation Plan

1. Add CI matrix task or job step: `npm ci` → `npm run build:graph-layout`.
2. Fail on `git diff --exit-code` for:
   - `django_apps/web/static/web/js/solver_graph_layout.js`
   - `django_apps/web/static/web/js/editor_graph_layout.js`
3. Verify clean `master` produces no diff after rebuild locally.
4. Document gate in `documents/ai/manuals/frontend.md` or `docs/agent-workflows/validation-routine.md`.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (read `build:graph-layout` script)
- `frontend/graph_layout/src/*.ts`
- `django_apps/web/static/web/js/solver_graph_layout.js`
- `django_apps/web/static/web/js/editor_graph_layout.js`
- `documents/ai/manuals/frontend.md`

## Validation Plan

- CI: new job passes on current branch after any needed bundle regen commit
- tests: existing `tests/unit/web/test_solver_graph_layout.py`, `test_editor_graph_layout.py`

## Acceptance Criteria

- [ ] CI fails when TS source changes without regenerated bundles.
- [ ] Fresh rebuild on master produces no unexpected diff.
- [ ] Gate documented if needed.
- [ ] No unrelated workflow changes.
- [ ] Remaining risks noted (SHA-40).

## Risks / Open Questions

- Node version pin in CI must match local esbuild output for deterministic diff.
