---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: High
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Clear stale GLTF viewers on shape-preview failure (SHA-52 High)

## Source Issue

- Linear: SHA-52
- Status at planning time: In Progress
- Priority: High

## Problem

When `/api/shape-preview/` returns `ok: false` (parse/validation errors with HTTP 200), `quick_solver_preview.js` updates the error banner but leaves previously mounted `[data-shape-gltf-viewer]` instances visible. Users see valid 3D geometry while the banner reports an invalid code, and WebGL animation loops continue wasting GPU/CPU.

## Scope

Ensure any failed preview path disposes existing viewers and clears `[data-quick-preview-viewers]` before showing error state. This High plan covers the user-visible failure mode; Mid plan covers the concrete code edits.

## Non-goals

- Do not change `/api/shape-preview/` HTTP status contract (SHA-26).
- Do not refactor the full shape GLTF viewer stack.
- Do not touch recipe graph editor or Lab replay canvas.

## Implementation Plan

1. Reproduce in browser: enter a valid shape code, wait for GLTF mount, then enter invalid code and confirm stale viewers remain (current bug).
2. After Mid plan lands, verify invalid-code path shows error banner with zero `[data-shape-gltf-viewer]` children under `[data-quick-preview-viewers]`.
3. Confirm WebGL contexts are disposed via `disposeShapeGltfViewer` (no lingering animation frames in devtools performance panel).

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/web/static/web/js/shape_gltf_viewer.js`
- Home/solver templates hosting `[data-quick-preview-panel]`

## Validation Plan

- manual verification: valid code → invalid code → viewers host empty, error visible, no stale geometry
- tests: covered by Low plan regression

## Acceptance Criteria

- [ ] `ok: false` responses clear all mounted GLTF viewers.
- [ ] Error banner visible with no stale preview geometry.
- [ ] Empty-input and network-error paths unchanged.
- [ ] Client regression test added (Low plan).

## Risks / Open Questions

- Race with in-flight `mountShapeGltfViewer` promises if user types quickly; existing `seq` guard should still apply after clear.
