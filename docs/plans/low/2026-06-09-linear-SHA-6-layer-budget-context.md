# Plan: SHA-6 - LayerBudgetContext (Low: L5 pattern alignment)

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-6
- Priority: Low
- Labels: performance, test, bug, solver, spec
- Status at planning time: Todo

## Problem

L3 budget polling should align with existing L5 reference implementation for consistency and maintainability.

## Scope

- Align L3 budget polling pattern with `layer_05_inner_pattern_fill/greedy.py` loop structure.

## Non-goals

- L5 behavior changes.

## Implementation Plan

1. Review L5 `greedy.py` budget polling pattern (`budget_ctx.remaining_budget_ms()` inside loop).
2. Refactor L3 polling call sites to mirror L5 structure (extract helper if duplication is significant, but avoid over-abstraction per YAGNI).
3. Preserve dedup signature `L3|layer_budget_ctx|run_layer_03|intra_layer_budget_ignored` in issue notes.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/candidate_gen.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/greedy.py` (reference only)

## Tests / Validation

- Existing budget tests from Mid plan must remain green.

## Acceptance Criteria

- [ ] L3 budget polling pattern consistent with L5 reference

## Risks

- Minimal; consistency refactor only.

## Human Review Required

- no
- reason: Pattern alignment after core fix lands.

## Automation Notes

Generated from Linear Todo issue by planning automation.

Depends on Mid-priority metrics and tests completing first.

Dedup signature: `L3|layer_budget_ctx|run_layer_03|intra_layer_budget_ignored`
