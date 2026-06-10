---
linear_issue: SHA-44
title: CI never runs build:css; committed app.css can drift from Tailwind source
priority: Low
labels:
  - ui
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Optional local pytest contract for app.css freshness (SHA-44 Low)

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Low

## Problem

`tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` checks substring presence for a few lab overlay CSS classes but does not assert full Tailwind rebuild freshness. Operators lack fast local feedback before CI.

## Scope

- Optionally extend pytest with a repo-level contract test that shells out to `npm run build:css` and asserts a clean diff under `django_apps/web/static/web/css/app.css`.
- Only if duplicating the CI step locally is desired for fast feedback (defer if Mid CI gate alone is sufficient).

## Non-goals

- Replacing the CI `build-css-check` job (Mid plan owns primary gate).
- Covering graph-layout, recipe-graph-editor, or locale catalog drift (SHA-35, SHA-40, SHA-42).

## Implementation Plan

1. After Mid CI gate merges, evaluate whether local pytest duplication adds value vs `npm run build:css && git diff`.
2. If yes: add `tests/unit/web/test_app_css_freshness.py` (or extend existing UI string test module) that runs builder and asserts zero diff.
3. Gate test behind Node availability or skip with explicit reason in environments without `npm`.
4. Reference new test in `documents/ai/manuals/testing.md` if added.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (existing substring guards)
- TBD — `tests/unit/web/test_app_css_freshness.py` if created
- `documents/ai/manuals/testing.md`

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/unit/web/test_app_css_freshness.py -v` if implemented
- build: N/A
- manual verification: test fails when `app.css` is stale

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Pytest + Node coupling may slow `test_fast`; consider marking slow/integration if runtime is high.
- May be redundant with CI-only gate — acceptable to close as "won't do" after Mid lands if team prefers CI-only enforcement.
