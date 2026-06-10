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
- Status at planning time: In Progress (triggered from Todo)
- Priority: Mid

## Problem

The graph layout engine source lives in `frontend/graph_layout/src/*.ts`, but production UI and pytest load the committed esbuild outputs `django_apps/web/static/web/js/solver_graph_layout.js` and `editor_graph_layout.js`. GitHub Actions never installs Node dependencies or runs `npm run build:graph-layout`, so a PR can change TypeScript layout logic while leaving stale static bundles in the repo and still pass CI.

## Scope

Add CI enforcement that committed `solver_graph_layout.js` and `editor_graph_layout.js` match `npm run build:graph-layout` output. Optionally document the gate in `documents/ai/manuals/frontend.md` and/or `docs/agent-workflows/validation-routine.md`.

## Non-goals

- Rewriting the graph layout engine.
- Changing layout algorithm behavior.
- Bundling recipe graph editor assets (tracked separately in SHA-40).
- Adding unrelated CI matrix tasks (lint/typecheck/format/test changes).

## Implementation Plan

1. **Baseline freshness check on current `master`**
   - Run `npm ci` then `npm run build:graph-layout` locally.
   - Run `git diff -- django_apps/web/static/web/js/solver_graph_layout.js django_apps/web/static/web/js/editor_graph_layout.js`.
   - If diff exists, commit regenerated bundles in a separate prep commit or as first task output so the CI gate starts green.

2. **Add CI matrix task `graph-layout-freshness` (or dedicated job)**
   - In `.github/workflows/ci.yml`, add Node setup alongside existing Python setup for the new task only (or a separate job to avoid slowing every matrix cell).
   - Steps:
     - `actions/setup-node@v4` with `node-version: "20"` (or match local dev; confirm LTS used elsewhere).
     - `npm ci` at repo root.
     - `npm run build:graph-layout`.
     - Fail if bundles drift:
       ```bash
       git diff --exit-code -- \
         django_apps/web/static/web/js/solver_graph_layout.js \
         django_apps/web/static/web/js/editor_graph_layout.js
       ```
   - On failure, print remediation: `npm run build:graph-layout` and commit the two files.

3. **Keep pytest contract unchanged**
   - `tests/unit/web/test_solver_graph_layout.py` and `tests/unit/web/test_editor_graph_layout.py` continue importing committed bundles via Node subprocess.
   - Do not switch tests to rebuild on the fly; CI freshness is the regression guard.

4. **Document the gate**
   - Add a short note to `documents/ai/manuals/frontend.md` § Graph layout engine: CI rebuilds and fails on drift.
   - Optionally add one line to `docs/agent-workflows/validation-routine.md` Tier 4 (before PR) mentioning `npm run build:graph-layout` when touching `frontend/graph_layout/`.

5. **Verify locally before PR**
   - Touch a no-op comment in a `frontend/graph_layout/src/*.ts` file without rebuilding; confirm local `git diff` shows bundle drift.
   - Rebuild and confirm diff clears.
   - Run `pytest tests/unit/web/test_solver_graph_layout.py tests/unit/web/test_editor_graph_layout.py`.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json` (reference only; `build:graph-layout` script already exists)
- `frontend/graph_layout/src/solverStaticBundle.ts`
- `frontend/graph_layout/src/editorStaticBundle.ts`
- `django_apps/web/static/web/js/solver_graph_layout.js`
- `django_apps/web/static/web/js/editor_graph_layout.js`
- `documents/ai/manuals/frontend.md`
- `docs/agent-workflows/validation-routine.md` (optional)
- `tests/unit/web/test_solver_graph_layout.py` (no change expected)
- `tests/unit/web/test_editor_graph_layout.py` (no change expected)

## Validation Plan

- lint: `ruff check .` (unchanged)
- typecheck: `mypy django_apps config src` (unchanged)
- tests: `pytest tests/unit/web/test_solver_graph_layout.py tests/unit/web/test_editor_graph_layout.py`
- build: `npm ci && npm run build:graph-layout && git diff --exit-code` on the two JS bundles
- manual verification: open a page that loads solver/editor graph layout JS; confirm no runtime import errors after rebuild

## Acceptance Criteria

- [ ] CI fails when `frontend/graph_layout/src` changes without regenerated static bundles.
- [ ] Fresh rebuild on current `master` produces no unexpected diff.
- [ ] Gate is documented in frontend/validation docs if needed.
- [ ] No unrelated workflow behavior changes.
- [ ] Remaining risks (e.g. recipe graph editor bundle drift per SHA-40) are noted if out of scope.

## Risks / Open Questions

- esbuild output may differ slightly across Node/esbuild versions — pin Node version in CI.
- If bundles are currently stale on `master`, first PR must include regeneration or CI will fail immediately (expected).
- Related drift issues (SHA-44 `build:css`, SHA-42 locale) remain separate; unified pattern deferred to low-priority follow-up.
