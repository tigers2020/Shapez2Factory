---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Guard shape-preview fetch on non-2xx HTTP before trusting JSON

## Source Issue

- Linear: SHA-52
- Status at planning time: In Progress
- Priority: Mid

## Problem

`runPreview` parses JSON from `fetch` without checking `res.ok`. If the server returns a non-2xx body (e.g. HTTP 400 for empty code per current API), the client may mis-handle the response or leave stale viewers depending on payload shape.

## Scope

After `fetch`, check `res.ok` before `res.json()`. On failure: clear viewers, show error banner (reuse network-error messaging or surface JSON `error` when parseable), and return early — consistent with other failure paths.

## Non-goals

- Changing `/api/shape-preview/` status-code contract (SHA-26).
- Implementing High-priority `clearViewerHost` on `!data.ok` (separate plan; implement together in one PR if desired).

## Implementation Plan

1. In `runPreview`, after `const res = await fetch(...)`, branch on `!res.ok` before assigning `data = await res.json()`.
2. Attempt to read JSON error body when `Content-Type` is JSON; fall back to generic message (mirror catch block: `"Could not reach preview service."` or `"Invalid shape code."`).
3. Call `clearViewerHost(viewersHost)` and `setBanner(errEl, message, true)`; clear warnings banner.
4. Respect `seq !== panel._previewSeq` guard before mutating DOM.
5. Verify empty-code API still returns HTTP 400 with `ok: false` — client should clear viewers and show error without stale geometry.
6. Run `pytest tests/integration/web/test_web_smoke.py -k shape_preview -v`.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/shapez_core/services/preview_service.py` (read-only; response shapes)
- `tests/integration/web/test_web_smoke.py` (read-only)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: `pytest tests/integration/web/test_web_smoke.py -k shape_preview -v`
- build: N/A
- manual verification: empty code input clears viewers; parse-error still clears after High fix

## Acceptance Criteria

- [ ] Non-2xx preview responses clear viewers and show error.
- [ ] Empty-input and network-error paths unchanged in behavior.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Empty code currently HTTP 400 vs parse error HTTP 200 — guard improves 400 path; `!data.ok` fix still required for parse errors (SHA-26 tracks status alignment).
