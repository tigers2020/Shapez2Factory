# Plan: SHA-6 - Honor LayerBudgetContext during candidate expansion and beam selection

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-6
- Priority: High
- Labels: performance, test, bug, solver, spec
- Status at planning time: Todo

## Problem

Layer 03 discards `LayerBudgetContext` and never checks remaining budget during candidate expansion or Phase C1/D selection. On large maps L3 can consume the entire stack time slice and leave L4/L5 starved, violating the shared L2–L5 budget contract.

## Scope

- Thread `budget_ctx` through L3 candidate generation and beam/commit selection hot paths.
- Enforce fail-closed behavior when budget exhausted mid-layer per spec M4.
- Stop L3 from starving downstream layers on large maps.

## Non-goals

- Changing global stack budget allocation in `stack_runner.py` beyond L3 intra-layer polling.
- Rewriting L3 placement heuristics unrelated to budget enforcement.
- Modifying L4/L5 budget behavior.

## Implementation Plan

1. Remove discarded `budget_ctx` binding in `run.py:66`; pass budget context into `generate_candidates` and `select_bundles`.
2. Poll `remaining_budget_ms()` at anchor/profile boundaries in `candidate_gen.py` and beam/commit loops.
3. Return best-effort partial or empty result with explicit skip reason when budget hits zero (fail-closed per M4).
4. Reference L5 pattern in `layer_05_inner_pattern_fill/greedy.py` for consistent polling approach.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/candidate_gen.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/beam_selector.py` (if selection loops need polling)
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_budget.py`

## Tests / Validation

- `python manage.py check`
- Targeted L3 pytest after implementation

## Acceptance Criteria

- [ ] L3 polls `remaining_budget_ms()` during candidate expansion and beam/commit selection
- [ ] Budget exhaustion mid-layer produces fail-closed behavior with explicit skip reason
- [ ] No unrelated L3 placement behavior changed

## Risks

- Over-aggressive polling may add overhead; poll at boundaries only (anchors/profiles/beam steps).
- Partial result semantics must match spec M4 — verify against normative spec before merging.

## Human Review Required

- no
- reason: Contract enforcement within existing L2–L5 budget design; no schema or auth change.

## Automation Notes

Generated from Linear Todo issue by planning automation.
