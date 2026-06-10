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

When `/api/shape-preview/` returns `ok: false` (parse/validation errors with HTTP 200), `quick_solver_preview.js` updates the error banner but leaves previously mounted `[data-shape-gltf-viewer]` instances visible. WebGL animation loops continue, wasting GPU/CPU, while the UI reports invalid code.

## Scope

Ensure any failed preview response clears/disposes all mounted viewers before showing the error banner.

## Non-goals

- Changing `/api/shape-preview/` HTTP status contract (SHA-26).
- Refactoring the full shape GLTF viewer stack.
- Recipe graph editor or Lab replay canvas work.

## Implementation Plan

1. In `django_apps/web/static/web/js/quick_solver_preview.js`, update the `!data.ok` branch in `runPreview` (lines 59–62) to call `clearViewerHost(viewersHost)` before `setBanner(errEl, ...)`.
2. Mirror the empty-input path (lines 32–36) and network-error path (lines 49–52) ordering: clear viewers → set error banner → clear warnings.
3. Verify `clearViewerHost` disposes via `disposeShapeGltfViewer` and `host.replaceChildren()` (lines 4–8).
4. Manual repro: enter valid shape code (viewers mount) → enter invalid code → viewers host empty, error visible, no WebGL canvas remains.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/web/static/web/js/shape_gltf_viewer.js` (dispose API, verify only)

## Validation Plan

- lint: fallow or existing JS lint if configured for static files
- tests: client regression (see Low plan)
- build: N/A
- manual verification: valid → invalid code sequence in browser

## Acceptance Criteria

- [ ] `ok: false` responses clear all mounted GLTF viewers.
- [ ] Error banner visible with no stale preview geometry.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- None blocking; fix is a one-line symmetry with existing clear paths.
