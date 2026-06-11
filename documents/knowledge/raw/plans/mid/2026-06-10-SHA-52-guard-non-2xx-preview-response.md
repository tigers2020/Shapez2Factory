---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: Mid
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Guard shape-preview fetch on HTTP status before trusting JSON

## Source Issue

- Linear: SHA-52
- Status at planning time: Todo
- Priority: Mid

## Problem

`runPreview` parses `res.json()` without checking `res.ok`. A non-2xx response (e.g. HTTP 400 for empty code per current API) may throw on JSON parse or return an unexpected body while leaving stale viewers mounted if parsing succeeds but `ok` is absent/false inconsistently.

## Scope

After `fetch` in `quick_solver_preview.js`, guard on `!res.ok` before trusting parsed JSON. On non-2xx: call `clearViewerHost(viewersHost)`, show a user-facing error banner, and return early — matching empty-input and network-error teardown semantics. Depends on High-priority `!data.ok` teardown landing first.

## Non-goals

- Changing `/api/shape-preview/` status-code contract (SHA-26).
- Refactoring the full shape GLTF viewer stack.
- Adding new API error shapes.

## Implementation Plan

1. Read `django_apps/shapez_core/services/preview_service.py` and `test_api_shape_preview_empty_code` / `test_api_shape_preview_parse_error` for current status codes (400 empty, 200 parse error).
2. In `runPreview`, after `const res = await fetch(...)` and before `data = await res.json()`, add:
   - If `!res.ok`: attempt `await res.json().catch(() => ({}))` for `error` message; call `clearViewerHost(viewersHost)`; `setBanner(errEl, data.error || "Could not load preview.", true)`; clear warnings; return (respect `_previewSeq`).
3. Keep existing `catch` block for network failures unchanged.
4. Verify empty-code input still clears viewers via existing early return (line 32–36) without hitting fetch.
5. Manual check: force or mock a 400/500 response and confirm viewers clear.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/shapez_core/services/preview_service.py` (read contract)
- `tests/integration/web/test_web_smoke.py` (read API status expectations)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: `pytest tests/integration/web/test_web_smoke.py -k shape_preview -v` (API contract unchanged)
- build: N/A
- manual verification: Optional — simulate non-2xx if feasible; confirm no stale viewers

## Acceptance Criteria

- [ ] Non-2xx preview fetch responses clear mounted viewers and show error banner.
- [ ] `ok: false` with HTTP 200 still handled by High-priority branch.
- [ ] Empty-input and network-error paths unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-26 tracks HTTP status inconsistency; this guard is defensive and should not depend on normalizing status codes.
- If `res.json()` on error pages returns HTML, parse may fail — handle via existing `catch` or empty-object fallback.
