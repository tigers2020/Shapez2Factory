---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: High
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Tear down stale GLTF viewers on shape-preview failure

## Source Issue

- Linear: SHA-52
- Status at planning time: Todo
- Priority: High

## Problem

When `/api/shape-preview/` returns `ok: false` (parse/validation errors with HTTP 200), `quick_solver_preview.js` updates the error banner but leaves previously mounted `[data-shape-gltf-viewer]` nodes in `[data-quick-preview-viewers]`. Users see a valid-looking 3D preview while the banner reports invalid code, and disposed viewers' WebGL animation loops may keep consuming GPU/CPU.

## Scope

Fix `runPreview` in `quick_solver_preview.js` so any `!data.ok` response disposes mounted viewers and clears the viewers host before showing the error banner. Mirror the existing empty-input and network-error teardown behavior.

## Non-goals

- Changing `/api/shape-preview/` HTTP status contract (SHA-26).
- Refactoring `shape_gltf_viewer.js` or the full GLTF stack.
- Recipe graph editor or Lab replay canvas work.

## Implementation Plan

1. Open `django_apps/web/static/web/js/quick_solver_preview.js` and locate `runPreview` `!data.ok` branch (lines 59–63).
2. Before `setBanner(errEl, ...)`, call `clearViewerHost(viewersHost)` — same helper used for empty code (line 33) and network errors (line 49).
3. Confirm `clearViewerHost` already calls `disposeShapeGltfViewer` on each `[data-shape-gltf-viewer]` and `host.replaceChildren()` (lines 4–8).
4. Manual repro: home or solver page → enter valid code `SuSuSuSu` → wait for preview → enter `not_a_real_code!!!` → viewers host empty, error banner visible, no stale geometry.
5. Re-run empty-input and network-error paths to confirm unchanged behavior.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/web/static/web/js/shape_gltf_viewer.js` (read-only; `disposeShapeGltfViewer`)
- `django_apps/web/templates/web/home.html` (manual repro surface)
- `django_apps/web/templates/web/solver.html` (manual repro surface)

## Validation Plan

- lint: N/A (plain JS module; no dedicated JS linter in AGENTS.md gates)
- typecheck: N/A
- tests: Covered in Low-priority plan; manual repro required for this slice
- build: N/A
- manual verification: Valid code → invalid code → `[data-quick-preview-viewers]` has zero `[data-shape-gltf-viewer]` children; `[data-quick-preview-error]` visible

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

- Debounce race: rapid valid→invalid typing may still mount viewers if a later `ok: true` response arrives after error handling; existing `_previewSeq` guard should cancel stale mounts — verify during manual repro.
- Non-2xx HTTP responses without `ok: false` JSON are handled in Mid-priority plan.
