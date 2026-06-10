---
linear_issue: SHA-17
title: Graph preview renderer permanently disables PNG generation after first failure
priority: Mid
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fix Playwright PNG renderer permanent disable latch

## Source Issue

- Linear: SHA-17
- Status at planning time: Todo
- Priority: Mid

## Problem

`PlaywrightPngGraphPreviewRenderer` sets `_generation_disabled` after first failure; subsequent renders return `image_url=None` without retry, breaking macro recipe graph loops.

## Scope

Scope latch to per-render or per-scene failure; do not permanently disable instance for unrelated scenes.

## Non-goals

- Do not implement deferred PNG warm queue (`plan_deferred_png_warm_queue.md`) unless required.

## Implementation Plan

1. Read `graph_preview.py` `PlaywrightPngGraphPreviewRenderer.render()`.
2. Identify latch set on first exception.
3. Replace instance-permanent flag with per-call failure handling or reset latch per `render()` invocation.
4. Verify `macro_recipe_graph_visual.py` loop gets independent retries per node.
5. Add unit test: first render fails, second succeeds on same renderer instance.
6. Run `pytest tests/unit/web/test_graph_preview.py -v`.

## Files / Areas Likely Affected

- `django_apps/web/services/graph_preview.py`
- `django_apps/shapez_solver/services/macro_recipe_graph_visual.py`
- `django_apps/shapez_solver/view_graph_serialization.py`
- `tests/unit/web/test_graph_preview.py`

## Validation Plan

- tests: `pytest tests/unit/web/test_graph_preview.py -v`
- lint: `ruff check django_apps/web/services/graph_preview.py`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Transient Playwright failures may still need circuit-breaker at process level (Low).
