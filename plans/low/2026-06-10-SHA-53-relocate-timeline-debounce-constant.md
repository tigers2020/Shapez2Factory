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
- Status at planning time: In Progress
- Priority: Low

## Problem

If `solver_timeline/` graph modules are retired/archived, `quick_solver_preview.js` remains the sole production consumer — and it imports only `TIMELINE_DEBOUNCE_MS` from `solver_timeline/constants.js`. Keeping the `solver_timeline/` folder name for one constant is misleading after graph UI retirement.

## Scope

Move `TIMELINE_DEBOUNCE_MS` to a neutral shared location and update the single import in `quick_solver_preview.js`. Optional cleanup of empty or archived `solver_timeline/` folder structure after Mid plan retires graph modules.

## Non-goals

- Changing debounce behavior or value
- Rewriting `quick_solver_preview.js` beyond import path
- Graph module restoration or React Flow editor changes

## Implementation Plan

1. Wait for Mid plan fate decision (retire recommended).
2. Create `django_apps/web/static/web/js/shared/timing_constants.js` (or colocate in `quick_solver_preview.js` if project prefers no new file) exporting `TIMELINE_DEBOUNCE_MS`.
3. Update `quick_solver_preview.js` import path.
4. Remove or archive `solver_timeline/constants.js` if no other references remain (grep `solver_timeline/` and `TIMELINE_DEBOUNCE_MS`).
5. Update `documents/ai/manuals/frontend.md` import path note if constants doc exists.
6. Run `powershell -File scripts/test_fast.ps1`.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/solver_timeline/constants.js`
- `django_apps/web/static/web/js/quick_solver_preview.js`
- `django_apps/web/static/web/js/shared/timing_constants.js` (new, if created)
- `documents/ai/manuals/frontend.md` (optional)

## Validation Plan

- lint: N/A (JS unless ESLint gate added)
- typecheck: `mypy django_apps config src`
- tests: `powershell -File scripts/test_fast.ps1`
- build: N/A
- manual verification: `/solver/` shape preview debounce still works (type in code input, preview does not spam requests)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] No misleading `solver_timeline/` folder dependency for production preview-only path.

## Risks / Open Questions

- Defer until Mid plan confirms retire path; skip if legacy UI is wired back.
- If `constants.js` holds other exports later, split carefully rather than delete wholesale.
