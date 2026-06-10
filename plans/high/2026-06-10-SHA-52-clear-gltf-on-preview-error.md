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

# Plan: Clear GLTF viewers on shape-preview ok:false

## Source Issue

- Linear: SHA-52
- Priority: High

## Problem

`quick_solver_preview.js` `!data.ok` branch shows error but leaves prior GLTF viewers mounted with active WebGL loops.

## Scope

Dispose/clear viewers on failed preview responses including `ok: false` with HTTP 200.

## Implementation Plan

1. In `runPreview` `!data.ok` branch (~59–63), call `clearViewerHost(viewersHost)` before return.
2. Mirror empty-code and network-error paths.
3. Manual: valid code → invalid code → viewers host empty, error visible.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/web/static/web/js/shape_gltf_viewer.js`

## Validation Plan

- manual: browser repro on home/solver page

## Acceptance Criteria

- [ ] `ok: false` clears all mounted GLTF viewers.
- [ ] Error banner visible with no stale geometry.

## Risks / Open Questions

- SHA-26 HTTP status contract unchanged.
