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

The graph layout engine source lives in `frontend/graph_layout/src/*.ts`, but production UI and pytest load the committed esbuild outputs `django_apps/web/static/web/js/solver_graph_layout.js` and `editor_graph_layout.js`. GitHub Actions never installs Node dependencies or runs `npm run build:graph-layout`, so a PR can change TypeScript layout logic while leaving stale static bundles in the repo and still pass CI.

## Scope

Add CI enforcement that committed `solver_graph_layout.js` and `editor_graph_layout.js` match `npm run build:graph-layout` output, or equivalent freshness gate documented in `frontend.md`.

## Non-goals

- Rewriting the graph layout engine.
- Changing layout algorithm behavior.
- Bundling recipe graph editor assets (SHA-40).

## Implementation Plan

1. Add a CI matrix task in `.github/workflows/ci.yml` that runs `npm ci` and `npm run build:graph-layout` (defined in root `package.json`).
2. Fail the job when `git diff --exit-code django_apps/web/static/web/js/solver_graph_layout.js django_apps/web/static/web/js/editor_graph_layout.js` is non-empty after rebuild.
3. Verify source entrypoints `frontend/graph_layout/src/solverStaticBundle.ts` and `frontend/graph_layout/src/editorStaticBundle.ts` are covered by the build script.
4. Document the gate in `documents/ai/manuals/frontend.md` and optionally `docs/agent-workflows/validation-routine.md`.
5. Confirm existing pytest guards still pass: `tests/unit/web/test_solver_graph_layout.py`, `tests/unit/web/test_editor_graph_layout.py`.

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

- lint: `ruff check .` (if workflow/docs touched)
- typecheck: N/A for CI-only change unless TS config edited
- tests: `pytest tests/unit/web/test_solver_graph_layout.py tests/unit/web/test_editor_graph_layout.py -v`
- build: `npm ci && npm run build:graph-layout` then verify clean git diff on bundle paths
- manual verification: CI job fails when TS source changes without regenerated bundles

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Fresh rebuild on current `master` may produce unexpected diff — run locally before merging CI gate.
- Recipe graph editor bundle drift (SHA-40) and CSS locale gates (SHA-44, SHA-42) remain separate.
