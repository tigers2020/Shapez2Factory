---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: Mid
labels:
  - ui
  - priority:mid
  - test
  - reviewing
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: clearViewerHost on ok:false branch

## Source Issue

- Linear: SHA-52
- Status at planning time: Todo
- Priority: Mid

## Problem

Call `clearViewerHost` in `!data.ok` branch; optionally guard on `res.ok` before parsing JSON.

## Scope

Minimal JS fix in `quick_solver_preview.js`: dispose mounted viewers when the shape-preview API returns `ok: false`, matching empty-input and network-error teardown behavior.

## Non-goals

- Changing `/api/shape-preview/` status-code contract (SHA-26).
- Refactoring the full shape GLTF viewer stack.
- Recipe graph editor or Lab replay canvas work.

## Implementation Plan

1. In `runPreview`, locate the `!data.ok` branch (lines 59–63) that sets `[data-quick-preview-error]` and returns early.
2. Insert `clearViewerHost(viewersHost)` before setting the error banner (mirror empty-code path).
3. Optionally add `if (!res.ok)` guard before `res.json()` to route non-2xx through the same teardown path.
4. Confirm empty-input and network-error paths remain unchanged.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/web/static/web/js/shape_gltf_viewer.js` (`disposeShapeGltfViewer`)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: N/A (automated regression in Low plan)
- build: N/A
- manual verification: valid code → invalid parse-error code → viewers host empty, error visible

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Overlaps High plan — implement together in one PR if practical.
- Low plan adds Playwright/JS unit regression.
