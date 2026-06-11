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

# Plan: Harden quick_solver_preview failure handling

## Source Issue

- Linear: SHA-52
- Status at planning time: In Progress
- Priority: Mid

## Problem

The `!data.ok` branch in `runPreview` skips `clearViewerHost`. Empty-input and network-error paths already clear viewers. Non-2xx HTTP responses may still parse JSON without clearing viewers if `data.ok` is absent/truthy.

## Scope

Align all failure paths in `runPreview` to clear viewers; optionally guard on `res.ok` before trusting JSON.

## Non-goals

- API status-code changes (SHA-26).

## Implementation Plan

1. Add `clearViewerHost(viewersHost)` to `!data.ok` branch (primary fix).
2. Optionally refactor fetch block: if `!res.ok`, clear viewers, set generic error banner, return before parsing JSON.
3. Confirm `seq !== panel._previewSeq` early returns do not leave stale viewers from superseded requests (existing behavior; document if unchanged).
4. Keep empty-input and network-error paths behavior identical aside from shared helper extraction if desired.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/shapez_core/services/preview_service.py` (reference for `ok: false` shapes)

## Validation Plan

- tests: see Low plan
- manual verification: network offline + parse error + empty input paths

## Acceptance Criteria

- [ ] `clearViewerHost` called in `!data.ok` branch.
- [ ] Empty-input and network-error paths unchanged.
- [ ] Optional `res.ok` guard documented if implemented.

## Risks / Open Questions

- `res.ok` guard may change behavior for future non-200 JSON error bodies; coordinate with SHA-26 if added.
