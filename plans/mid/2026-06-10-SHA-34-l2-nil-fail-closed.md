---
linear_issue: SHA-34
title: stack_runner marks L2 COMPLETED and returns SUCCESS when exterior transport returns None
priority: Mid
labels:
  - bug
  - solver
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fail-closed when L2 exterior transport returns None

## Source Issue

- Linear: SHA-34
- Status at planning time: Todo
- Priority: Mid

## Problem

When `capacity_envelope` is missing, `run_layer_02_exterior_transport` returns `None`. `stack_runner` still records L2 as `COMPLETED` with stub metrics, passes `exterior_plan=None` to L3, and finishes with `StackRunStatus.SUCCESS`. Downstream layers skip silently while `RunStackUseCase` reports `run_success=true`.

## Scope

- Detect `None` / invalid L2 output in `stack_runner` and propagate failure instead of `COMPLETED` + `SUCCESS`.
- Fix Django `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent`.
- Add regression test for missing `capacity_envelope`.

## Non-goals

- Full L6 validation (SHA-15).
- Changing L2 EVTC shortfall semantics when plan object exists.
- Rewriting layer skip-reason enums across all layers.

## Implementation Plan

1. After L2 `entry.run(...)`, if result is not `ExteriorConnectionPlan`, set `failed_layer_slug=LAYER_02_EXTERIOR_TRANSPORT` and break stack loop.
2. Avoid appending `LayerPostSummaryOutcome.COMPLETED` for nil L2 result; use failed/skipped outcome per existing enum.
3. Patch `django_apps/asteroid_lab/layers/stack_runner.py` `run_layers_02_to_05` to forward envelope params like `run_layers_02_to_06`.
4. Add test: `run_layers_02_to_06` with default L2 runner and `capacity_envelope=None` → not `SUCCESS`.
5. Verify `RunStackUseCase` sets `run_success=false` when `failed_layer_slug` set.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py`
- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `django_apps/asteroid_lab/layers/stack_runner.py`
- `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py` (extend)

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/layers/ -v -k stack`
- typecheck: `mypy django_apps config src`
- lint: `ruff check .`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Distinguish intentional skip vs input failure — confirm contract with layer_02 docs before choosing SKIPPED vs FAILED outcome.
