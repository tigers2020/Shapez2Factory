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

# Plan: L3 Phase B budget polling for route probe expansion

## Source Issue

- Linear: SHA-31
- Status at planning time: Todo
- Priority: Mid

## Problem

`run_layer_03_rim_greedy_placement` accepts `LayerBudgetContext` from `stack_runner` but discards it at `run.py:66`. Phase B candidate generation (`generate_candidates` → `generate_candidates_for_profile`) runs nested weighted A* route probes (anchors × gene entries × D4 variants × cardinal output sides) with no `remaining_budget_ms()` polling. Large maps with many rim anchors and gene seeds can exhaust the shared 60s stack budget inside L3 and starve L4–L6.

## Scope

- Thread `LayerBudgetContext` from `run.py` into Phase B (`generate_candidates` / `generate_candidates_for_profile`).
- Poll `remaining_budget_ms()` during Phase B expansion; stop route-probe work when budget is exhausted.
- Return best-effort partial candidate pool (deterministic ordering preserved for work completed).
- Increment `Layer03ExpansionMetrics.budget_skipped_count` for truncated expansions (currently hardcoded `0` at `candidate_gen.py:624`).
- Add regression test proving downstream layers still receive budget under tight stack constraints with many rim anchors.

## Non-goals

- Changing rim placement algorithm logic beyond budget enforcement.
- Altering global stack budget allocation policy in `stack_runner.py`.
- Phase C1 beam selection or Phase D commit-time re-probe budget polling (separate issues; see SHA-6 overlap).
- Rewriting route probe heuristics or probe limit constants.

## Implementation Plan

1. **Remove discard in `run.py`:** Delete `_ = (budget_ctx, ...)` binding; pass `budget_ctx` into `generate_candidates(...)`.
2. **Extend `generate_candidates` signature:** Add optional `budget_ctx: LayerBudgetContext | None = None`. When `None`, preserve current unbounded behavior for direct unit callers; when provided, enforce polling.
3. **Poll at Phase B inner-loop boundaries in `generate_candidates_for_profile`:**
   - Before each `anchor` iteration (outer loop at ~line 426).
   - Before each `weighted_route_probe` call (inner hot path at ~line 513) OR at anchor×entry boundary if per-probe overhead is too high — prefer anchor boundary first, add inner poll only if stack tests still show starvation.
   - On `remaining_budget_ms() <= 0`: break out of nested loops, return partial `accum`.
4. **Propagate budget skip metrics:** Track skipped route-probe attempts / truncated anchor expansions; set `budget_skipped_count` in `Layer03ExpansionMetrics` instead of hardcoded `0`.
5. **Graceful degradation in `run.py`:** If Phase B returns empty/partial pool due to budget, continue to Phase C1/D with available candidates (fail-closed per partial pool, not layer abort) unless spec M4 requires explicit `layer_skip_reason` — verify against `2026-05-31-layer-03-rim-placement-v2-design.md` before choosing skip reason enum.
6. **Regression test — unit:** Mock `now_fn` advancing monotonic clock; assert `generate_candidates` stops mid-expansion and `budget_skipped_count > 0` when budget is tiny relative to anchor×gene product.
7. **Regression test — stack:** Tight `LayerBudgetContext.from_budget_ms(...)` through `run_layer_03_rim_greedy_placement` on `large_fluid_map` fixture; assert `stack_runner` records non-zero `remaining_budget_ms` for L4+ when L3 budget polling is active. Reference pattern: `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py::test_remaining_budget_zero_skips_layer_without_call` and SHA-6 mid plan stack test notes.
8. **Preserve determinism:** Partial pools must remain D1-sorted; no reordering of completed probes.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/candidate_gen.py`
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/candidates.py` (if new skip reason needed — verify before adding)
- `tests/unit/asteroid_lab/layers/test_layer03_route_probe_map_budget.py` (extend or sibling test module)
- `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py` or new `test_layer_03_budget_polling.py`
- `src/shapez2_factory/application/asteroid_lab/stack_runner.py` (read-only reference for budget contract)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/`
- typecheck: `mypy django_apps config src` (touched modules)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer03_route_probe_map_budget.py tests/unit/asteroid_lab/layers/ -k "budget or layer_03" -q`
- build: `python manage.py check`
- manual verification: run solver smoke on large fluid map with tight `LAYER_STACK_BUDGET_MS`; confirm L4 layer record shows `remaining_budget_ms > 0` in layer post summary log

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Overlap with SHA-6 (broader L3 budget threading including beam selection): implement Phase B only per SHA-31 scope; coordinate to avoid duplicate/conflicting edits.
- Related issues SHA-32 (L4 inner fill) and SHA-14 (L5 A*) have parallel budget gaps — fixing SHA-31 alone may not fully eliminate stack starvation on all maps.
- Polling granularity tradeoff: per-anchor vs per-route-probe — start coarse; tighten only if integration tests fail.
- `test_layer03_route_probe_map_budget.py` currently uses frozen `now_fn=lambda: 0.0` (infinite budget illusion); new tests must use advancing clock to exercise real polling.
