---
linear_issue: SHA-53
title: solver_timeline graph modules are not mounted on any page; pytest still asserts production layout
priority: Low
labels:
  - ui
  - priority:mid
  - refactor
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Relocate TIMELINE_DEBOUNCE_MS out of solver_timeline

## Source Issue

- Linear: SHA-53
- Status at planning time: Todo
- Priority: Low

## Problem

`quick_solver_preview.js` is the only production consumer of `solver_timeline/` — it imports `TIMELINE_DEBOUNCE_MS` from `solver_timeline/constants.js`. If the Mid plan retires/archives the graph modules folder, keeping a live import from a deprecated directory creates confusing coupling and blocks clean archival.

## Scope

After Mid plan retires `solver_timeline/` graph modules (or if folder is otherwise archived):

1. Move `TIMELINE_DEBOUNCE_MS` to a neutral shared location (e.g. `django_apps/web/static/web/js/preview_constants.js` or colocate in `quick_solver_preview.js` if single-use).
2. Update `quick_solver_preview.js` import path.
3. Remove or slim `solver_timeline/constants.js` if no remaining exports.
4. Update any docs referencing the old path.

Skip this plan if Mid plan chooses **wire** path and `constants.js` remains part of an active solver_timeline package.

## Non-goals

- Changing debounce value (320 ms) or preview behavior
- Mounting graph modules
- Test quarantine (High plan)
- Product decision on solver_timeline fate (Mid plan)

## Implementation Plan

1. Confirm Mid plan completed with **retire/defer** path.
2. `rg 'solver_timeline/constants' django_apps/web/static/web/js` — expect only `quick_solver_preview.js`.
3. Create `django_apps/web/static/web/js/preview_constants.js`:
   ```javascript
   export const TIMELINE_DEBOUNCE_MS = 320;
   ```
4. Update `quick_solver_preview.js`:
   ```javascript
   import { TIMELINE_DEBOUNCE_MS } from "./preview_constants.js";
   ```
5. Delete `solver_timeline/constants.js` if empty; or leave stub re-export with deprecation comment if other solver_timeline files still reference it during transitional archive.
6. If entire `solver_timeline/` folder is removed, delete orphaned graph modules per separate cleanup PR (out of scope unless Mid plan already removed them).
7. Update `solver_timeline/README.md` or `frontend.md` import path note.
8. Smoke: load `/solver/` and `/` home preview — debounced input still works.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/preview_constants.js` (create)
- `django_apps/web/static/web/js/quick_solver_preview.js` (import path)
- `django_apps/web/static/web/js/solver_timeline/constants.js` (delete or deprecate)
- `documents/ai/manuals/frontend.md` (optional path note)

## Validation Plan

- lint: N/A (JS-only)
- typecheck: N/A
- tests: `pytest tests/integration/web/test_web_smoke.py -k shape_preview -v` (preview still works)
- build: N/A
- manual verification: type in solver/home shape preview input — requests debounced ~320 ms

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] No production import from deprecated `solver_timeline/` for preview debounce.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Blocked on Mid plan:** do not execute until retire path confirmed.
- If `constants.js` exports grow later, prefer `preview_constants.js` vs inline to keep single-responsibility.
- Template `type="module"` cache busting: Django static versioning should handle path change automatically.
