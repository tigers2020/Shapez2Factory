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
- Status at planning time: In Progress
- Priority: Mid

## Problem

The graph layout engine source lives in `frontend/graph_layout/src/*.ts`, but production UI and pytest load committed esbuild outputs `django_apps/web/static/web/js/solver_graph_layout.js` and `editor_graph_layout.js`. GitHub Actions never installs Node dependencies or runs `npm run build:graph-layout`, so a PR can change TypeScript layout logic while leaving stale static bundles in the repo and still pass CI.

## Scope

Add CI enforcement that committed `solver_graph_layout.js` and `editor_graph_layout.js` match `npm run build:graph-layout` output. Optionally document the gate in `documents/ai/manuals/frontend.md` and `docs/agent-workflows/validation-routine.md`.

## Non-goals

- Rewriting the graph layout engine.
- Changing layout algorithm behavior.
- Bundling recipe graph editor assets (tracked separately in SHA-40).
- Adding a unified frontend static-asset CI pattern for all bundles (deferred; see low-priority plan).

## Implementation Plan

1. Read `.github/workflows/ci.yml` matrix structure and confirm no existing Node/npm steps.
2. Add a CI matrix task (e.g. `graph-layout-freshness`) or dedicated job that:
   - checks out the repo
   - runs `actions/setup-node` with a pinned Node version matching local dev (check root `package.json` engines if present)
   - runs `npm ci` at repo root
   - runs `npm run build:graph-layout`
   - runs `git diff --exit-code django_apps/web/static/web/js/solver_graph_layout.js django_apps/web/static/web/js/editor_graph_layout.js`
3. Verify on current `master`: `npm ci && npm run build:graph-layout` produces no diff; if drift exists, commit regenerated bundles in a separate commit or note in PR.
4. Add a short CI gate note to `documents/ai/manuals/frontend.md` § Graph layout engine (after regenerate instructions).
5. Optionally add Tier-4 / PR-gate bullet in `docs/agent-workflows/validation-routine.md` referencing the CI task name.
6. Keep pytest importing committed bundles (`tests/unit/web/test_solver_graph_layout.py`, `tests/unit/web/test_editor_graph_layout.py`); no pytest change required unless a dedicated freshness test is preferred over git-diff (git-diff in CI is sufficient per issue spec).

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (`build:graph-layout` script — read-only unless output paths change)
- `django_apps/web/static/web/js/solver_graph_layout.js` (verify only; regenerate if drift on master)
- `django_apps/web/static/web/js/editor_graph_layout.js` (verify only)
- `frontend/graph_layout/src/solverStaticBundle.ts`
- `frontend/graph_layout/src/editorStaticBundle.ts`
- `documents/ai/manuals/frontend.md`
- `docs/agent-workflows/validation-routine.md` (optional)

## Validation Plan

- lint: unchanged (Python-only gates unaffected)
- typecheck: unchanged
- tests: `pytest tests/unit/web/test_solver_graph_layout.py tests/unit/web/test_editor_graph_layout.py`
- build: `npm ci && npm run build:graph-layout && git diff --exit-code` on the two JS files
- manual verification: change a comment in `frontend/graph_layout/src/*.ts`, run build, confirm CI task would fail without committing bundles

## Acceptance Criteria

- [ ] CI fails when `frontend/graph_layout/src` changes without regenerated static bundles.
- [ ] Fresh rebuild on current `master` produces no unexpected diff.
- [ ] Gate is documented in frontend/validation docs if needed.
- [ ] No unrelated workflow behavior changes.
- [ ] Remaining risks (e.g. recipe graph editor bundle drift SHA-40) are noted if out of scope.

## Risks / Open Questions

- Node version mismatch between local dev and CI could cause false-positive diffs — pin Node in workflow.
- esbuild banner whitespace may differ across platforms; confirm diff is content-stable on ubuntu-latest.
- Related drift issues: SHA-44 (CSS), SHA-40 (recipe graph editor), SHA-42 (locale) — unified pattern deferred.
