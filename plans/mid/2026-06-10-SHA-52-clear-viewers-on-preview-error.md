---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: Mid
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Call clearViewerHost on shape-preview ok:false (SHA-52 Mid)

## Source Issue

- Linear: SHA-52
- Status at planning time: In Progress
- Priority: Mid

## Problem

In `runPreview`, the `!data.ok` branch (lines 59–63) sets `[data-quick-preview-error]` and returns without calling `clearViewerHost(viewersHost)`. Empty-input and network-error paths already call `clearViewerHost`.

## Scope

Update `quick_solver_preview.js` so failed previews always dispose/clear mounted viewers. Optionally guard on `res.ok` before trusting JSON for non-2xx responses.

## Non-goals

- Changing preview API status codes (SHA-26).
- Refactoring `shape_gltf_viewer.js` beyond existing `disposeShapeGltfViewer` usage.

## Implementation Plan

1. In `django_apps/web/static/web/js/quick_solver_preview.js`, inside the `!data.ok` branch before `return`, call `clearViewerHost(viewersHost)` (mirror the empty-code branch at lines 32–36).
2. Optionally after `fetch`, if `!res.ok`, call `clearViewerHost(viewersHost)`, set network-style error banner, and return before `res.json()` — only if non-2xx responses can reach this panel today without breaking empty-code HTTP 400 behavior.
3. Keep `seq !== panel._previewSeq` early returns unchanged.
4. Run existing integration smoke: `pytest tests/integration/web/test_web_smoke.py::test_api_shape_preview_parse_error -v`.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/shapez_core/services/preview_service.py` (read-only reference)
- `tests/integration/web/test_web_smoke.py`

## Validation Plan

- tests: `pytest tests/integration/web/test_web_smoke.py -v` (API contract unchanged)
- manual verification: home/solver quick preview valid → invalid code flow
- lint: N/A for static JS unless project adds JS lint gate

## Acceptance Criteria

- [ ] `ok: false` responses clear all mounted GLTF viewers.
- [ ] Error banner visible with no stale preview geometry.
- [ ] Empty-input and network-error paths unchanged.
- [ ] Client regression test added (Low plan).

## Risks / Open Questions

- Optional `res.ok` guard must not regress empty-code path if API returns HTTP 400 with JSON body.
