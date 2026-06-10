---
linear_issue: SHA-14
title: L5 transport routing ignores LayerBudgetContext during sequential A* routing
priority: Mid
labels:
  - bug
  - solver
  - performance
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Wire LayerBudgetContext into L5 sequential transport routing

## Source Issue

- Linear: SHA-14
- Status at planning time: Todo
- Priority: Mid

## Problem

Layer 05 transport routing discards `LayerBudgetContext` (`_ = budget_ctx`). Sequential per-source A* can exhaust entire stack time slice, skipping L6 or causing timeout.

## Scope

Thread `budget_ctx` into sequential router; poll `remaining_budget_ms()` per source; return partial plan + explicit failure on budget exhaustion.

## Non-goals

- No `stack_runner` global allocation change beyond L5 polling.
- No A* heuristic rewrite.
- No SHA-6 L3 changes.

## Implementation Plan

1. Remove `_ = budget_ctx` discard in `layer_04_transport_routing/run.py`.
2. Pass budget into `route_layer04_sequential`.
3. Before each source A*, check `remaining_budget_ms()`; mirror inner-fill `budget_interrupted` pattern.
4. On exhaustion: partial route plan + explicit layer failure metadata.
5. Add unit test with fake `now_fn` forcing budget exhaustion mid-loop.
6. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_sequential_router.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/`
- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `tests/unit/asteroid_lab/layers/test_layer04_sequential_router.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_sequential_router.py -v`
- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/`
- typecheck: `mypy django_apps config src` (spot-check)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- L5 slug vs directory `layer_04_transport_routing` naming — follow canon renumber spec.
