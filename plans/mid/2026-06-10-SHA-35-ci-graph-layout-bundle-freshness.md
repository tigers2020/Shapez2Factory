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

# Plan: CI never runs build:graph-layout; committed graph layout bundles can drift from TypeScript source

## Source Issue

- Linear: SHA-35
- Status at planning time: Todo
- Priority: Mid

## Problem

Graph layout engine source lives in `frontend/graph_layout/src/*.ts`, but production UI and pytest load committed esbuild outputs under `django_apps/web/static/web/js/`. GitHub Actions never runs `npm run build:graph-layout`, so a PR can change TypeScript layout logic while leaving stale static bundles and still pass CI.

## Scope

Add CI enforcement that committed `solver_graph_layout.js` and `editor_graph_layout.js` match `npm run build:graph-layout` output, or equivalent freshness gate documented in `frontend.md`.

## Non-goals

- Rewriting the graph layout engine.
- Changing layout algorithm behavior.
- Bundling recipe graph editor assets (SHA-40 tracks separately).

## Implementation Plan

1. Confirm `package.json` `build:graph-layout` script emits `django_apps/web/static/web/js/solver_graph_layout.js` and `editor_graph_layout.js` with `GENERATED — do not edit by hand` banner.
2. Add CI matrix task or standalone job in `.github/workflows/ci.yml`: `npm ci`, `npm run build:graph-layout`, then `git diff --exit-code` on the two static JS files.
3. Run build locally on current `master`; commit any one-time drift fix if bundles are stale before adding the gate.
4. Document the gate in `documents/ai/manuals/frontend.md` and optionally `docs/agent-workflows/validation-routine.md`.
5. Verify existing pytest (`tests/unit/web/test_solver_graph_layout.py`, `test_editor_graph_layout.py`) still import committed bundles — CI freshness check is the regression guard, not pytest rebuild.
6. Note related SHA-40/SHA-44/SHA-42 pattern in PR description only; do not unify all frontend asset gates in this change.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (read-only unless script path fix needed)
- `frontend/graph_layout/src/solverStaticBundle.ts`
- `frontend/graph_layout/src/editorStaticBundle.ts`
- `django_apps/web/static/web/js/solver_graph_layout.js`
- `django_apps/web/static/web/js/editor_graph_layout.js`
- `documents/ai/manuals/frontend.md`
- `docs/agent-workflows/validation-routine.md` (optional)

## Validation Plan

- lint: `ruff check .` (workflow YAML only)
- typecheck: N/A for CI-only change
- tests: `powershell -File scripts/test_fast.ps1`; locally simulate CI: `npm ci && npm run build:graph-layout && git diff --exit-code django_apps/web/static/web/js/solver_graph_layout.js django_apps/web/static/web/js/editor_graph_layout.js`
- build: CI workflow dry-run or push to branch and confirm gate fails on intentional TS edit without rebuild
- manual verification: Edit a TS comment in `frontend/graph_layout/src/` without rebuilding; confirm CI fails

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Node version in CI must match local dev (`package.json` engines or `.nvmrc` if present).
- Recipe graph editor bundle drift (SHA-40) and CSS/locale gates (SHA-44, SHA-42) deferred — document as follow-ups.
