---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Client regression for viewer teardown on parse error

## Source Issue

- Linear: SHA-52
- Priority: Low

## Scope

Add JS unit test or Playwright check for viewer clear on parse-error input.

## Implementation Plan

1. Extend `tests/integration/web/test_web_smoke.py` or add Playwright flow: valid → invalid code.
2. Assert `[data-quick-preview-viewers]` empty and `[data-quick-preview-error]` visible.

## Files / Areas Likely Affected

- `tests/integration/web/test_web_smoke.py` or `output/playwright/` artifact test

## Acceptance Criteria

- [ ] Regression test added per issue spec.
