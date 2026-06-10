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

# Plan: CI graph-layout bundle freshness gate

## Source Issue

- Linear: SHA-35
- Status at planning time: Todo
- Priority: Mid

## Problem

Graph layout TypeScript source in `frontend/graph_layout/src/` is built to committed static bundles, but CI never runs `npm run build:graph-layout`. PRs can change TS logic while leaving stale `solver_graph_layout.js` / `editor_graph_layout.js` and still pass CI.

## Scope

- Add CI enforcement that committed bundles match `npm run build:graph-layout` output.
- Document gate in frontend/validation docs if needed.

## Non-goals

- Rewriting graph layout engine.
- Changing layout algorithm behavior.
- Recipe graph editor bundles (SHA-40).

## Implementation Plan

1. Add CI job or matrix task: `npm ci` + `npm run build:graph-layout`.
2. Fail on `git diff` for `django_apps/web/static/web/js/solver_graph_layout.js` and `editor_graph_layout.js`.
3. Verify fresh rebuild on current master produces no unexpected diff.
4. Update `documents/ai/manuals/frontend.md` or `docs/agent-workflows/validation-routine.md` with gate reference.
5. Keep pytest importing committed bundles; CI freshness is the regression guard.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (`build:graph-layout` script)
- `django_apps/web/static/web/js/solver_graph_layout.js`
- `django_apps/web/static/web/js/editor_graph_layout.js`
- `documents/ai/manuals/frontend.md`

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: `pytest tests/unit/web/test_solver_graph_layout.py tests/unit/web/test_editor_graph_layout.py -v`
- build: CI workflow dry-run locally if possible
- manual verification: Change TS source without rebuild; confirm CI fails.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-40 recipe graph editor bundle drift tracked separately.
- Node version pin must match local dev environment.
