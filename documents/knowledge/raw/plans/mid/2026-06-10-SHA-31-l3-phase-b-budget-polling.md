---
linear_issue: SHA-31
title: L3 rim greedy placement ignores LayerBudgetContext during Phase B route probe expansion
priority: Mid
labels:
  - bug
  - performance
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Wire LayerBudgetContext into L3 Phase B route probe expansion

## Source Issue

- Linear: SHA-31
- Status at planning time: Todo
- Priority: Mid

## Problem

Layer 03 rim greedy placement (`layer_03_rim_greedy_placement`) accepts `LayerBudgetContext` from `stack_runner` but discards it. Phase B candidate generation runs nested weighted A* route probes (anchors × gene entries × D4 variants × cardinal output sides) with no remaining-budget polling, so a map with many rim anchors and gene seeds can consume the entire shared 60s stack budget inside L3 and starve L4–L6.

## Scope

- Add budget polling to Phase B route probe expansion in L3 rim greedy placement.
- Ensure early exit or graceful degradation when budget is exhausted.

## Non-goals

- Changing rim placement algorithm logic beyond budget enforcement.
- Altering global stack budget allocation policy.

## Implementation Plan

1. Trace `LayerBudgetContext` from `stack_runner` into `layer_03_rim_greedy_placement/run.py` Phase B loops (candidate generation and route probe expansion).
2. Before each route probe expansion iteration, call `remaining_budget_ms()`; break or degrade when budget is exhausted (mirror patterns from SHA-14 / inner-fill budget interruption).
3. Propagate partial Phase B results with explicit budget-exhausted metadata so downstream layers can still run.
4. Add regression test with many rim anchors / gene seeds verifying L4+ layers still receive budget (fake `now_fn` or capped budget fixture).
5. Run targeted tests under `tests/unit/asteroid_lab/layers/` for L3 rim placement.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/beam_selector.py`
- `src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py`
- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `tests/unit/asteroid_lab/layers/` (L3 rim placement tests — TBD exact module)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/asteroid_lab/layers/ -k rim -v` (or targeted new test module)
- build: N/A
- manual verification: Large-map stack run shows L4+ layers execute when L3 budget capped

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Phase B probe budget scaling in `route_probe.py` may interact with stack budget polling — verify no double-counting.
- Related SHA-32/SHA-14 budget fixes should stay consistent but out of scope for this plan.
