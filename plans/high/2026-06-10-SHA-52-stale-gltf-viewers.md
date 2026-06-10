---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: High
labels:
  - ui
  - priority:mid
  - test
  - reviewing
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Clear stale GLTF viewers on preview failure

## Source Issue

- Linear: SHA-52
- Status at planning time: Todo
- Priority: High

## Problem

Valid shape remains visible while error banner reports invalid code; active WebGL loops waste GPU/CPU.

## Scope

Ensure any failed shape-preview response (`ok: false` with HTTP 200, and non-2xx fetch failures) tears down mounted `[data-shape-gltf-viewer]` instances and clears `[data-quick-preview-viewers]` before showing the error banner.

## Non-goals

- Changing `/api/shape-preview/` status-code contract (SHA-26).
- Refactoring the full shape GLTF viewer stack.
- Recipe graph editor or Lab replay canvas work.

## Implementation Plan

1. Audit `runPreview` in `quick_solver_preview.js` for all failure branches (empty input, network error, `!data.ok`, non-2xx).
2. Call `clearViewerHost(viewersHost)` in the `!data.ok` branch to mirror empty-code handling.
3. Optionally guard on `res.ok` before trusting JSON on non-2xx responses.
4. Manually verify: valid code → invalid code → viewers host empty, error banner visible, no active WebGL loops.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/web/static/web/js/shape_gltf_viewer.js` (`disposeShapeGltfViewer`)
- `django_apps/shapez_core/services/preview_service.py` (API contract reference)
- `tests/integration/web/test_web_smoke.py` (API contract only today)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: N/A (client regression deferred to Low plan)
- build: N/A
- manual verification: home/solver quick preview — enter valid shape code, then invalid code; confirm viewers cleared and error banner shown with no stale geometry

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- HTTP 200 + `ok: false` contract (SHA-26) means client must key off JSON `ok`, not status alone.
- Mid/Low plans add `res.ok` guard and automated regression respectively.
