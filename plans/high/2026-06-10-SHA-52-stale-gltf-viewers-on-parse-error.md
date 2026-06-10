---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: High
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Clear stale GLTF viewers on shape-preview parse failure

## Source Issue

- Linear: SHA-52
- Status at planning time: In Progress
- Priority: High

## Problem

`quick_solver_preview.js` does not tear down mounted shape GLTF viewers when `/api/shape-preview/` returns `ok: false` (parse/validation errors). The error banner updates, but previously rendered 3D previews remain visible and their WebGL animation loops keep running — wasting GPU/CPU and showing contradictory UI (valid geometry + invalid-code error).

## Scope

Fix the `!data.ok` branch in `runPreview` so it disposes all `[data-shape-gltf-viewer]` instances and clears `[data-quick-preview-viewers]` before showing the error banner, matching empty-input and network-error paths.

## Non-goals

- Changing `/api/shape-preview/` HTTP status contract (SHA-26).
- Refactoring the full shape GLTF viewer stack.
- Recipe graph editor or Lab replay canvas work.

## Implementation Plan

1. Open `django_apps/web/static/web/js/quick_solver_preview.js` and locate `runPreview` `!data.ok` branch (lines 59–63).
2. Before `setBanner(errEl, ...)`, call `clearViewerHost(viewersHost)` — same helper used for empty code (line 33) and network catch (line 49).
3. Confirm `clearViewerHost` already calls `disposeShapeGltfViewer` per child and `host.replaceChildren()` (lines 4–8).
4. Manual repro: home or solver page with shape preview panel → enter valid code (e.g. `SuSuSuSu`) → wait for 3D preview → enter invalid code (e.g. `not_a_real_code!!!`) → viewers host empty, error banner visible, no WebGL canvas remains.
5. Confirm empty-input path (`!code` at line 32) and network-error catch (line 45) are unchanged.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/web/static/web/js/shape_gltf_viewer.js` (read-only; `disposeShapeGltfViewer`)

## Validation Plan

- lint: N/A (no Python change)
- typecheck: N/A
- tests: existing `pytest tests/integration/web/test_web_smoke.py -k shape_preview -v` (API contract unchanged)
- build: N/A
- manual verification: valid → invalid code sequence on page with `[data-shape-preview-panel]`; confirm viewers cleared and error visible

## Acceptance Criteria

- [ ] `ok: false` responses clear all mounted GLTF viewers.
- [ ] Error banner visible with no stale preview geometry.
- [ ] Empty-input and network-error paths unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Race: rapid typing may interleave previews; existing `seq` guard should still apply after fix.
- Client regression test deferred to Low-priority plan.
