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

# Plan: L2 nil-plan fail-closed in stack_runner

## Source Issue

- Linear: SHA-34
- Status at planning time: Todo
- Priority: Mid

## Problem

When Layer 02 exterior transport cannot run because `capacity_envelope` is missing, `run_layer_02_exterior_transport` returns `None`. Core `stack_runner` still records L2 as `completed` with stub metrics, passes `exterior_plan=None` to L3, and finishes the stack with `StackRunStatus.SUCCESS`. Downstream layers silently skip (e.g. L3 `MISSING_EXTERIOR_CONNECTION_PLAN`) while `RunStackUseCase` reports `run_success=true` and `validation_passed=true`. The Django deprecated alias `run_layers_02_to_05` forwards to `run_layers_02_to_06` without `capacity_envelope`, so default L2 runners always no-op.

## Scope

- Detect `None` / invalid L2 output in `stack_runner` and propagate failure (or explicit skipped outcome) instead of `COMPLETED` + `SUCCESS`.
- Fix Django `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent` like `run_layers_02_to_06`.
- Add regression test for default L2 runner with missing `capacity_envelope`.

## Non-goals

- Implementing full L6 validation (SHA-15).
- Changing L2 EVTC shortfall semantics when a plan object exists with `unmet_reason`.
- Rewriting layer skip-reason enums across all layers.

## Implementation Plan

1. In `src/shapez2_factory/application/asteroid_lab/stack_runner.py` (L165–234), after L2 run, if result is not `ExteriorConnectionPlan`, set `failed_layer_slug=LAYER_02_EXTERIOR_TRANSPORT` (or explicit skipped outcome) and stop the stack instead of appending `LayerPostSummaryOutcome.COMPLETED` with stub metrics.
2. In `src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py` (L84–85), confirm `capacity_envelope is None` path remains the trigger; document expected stack behavior when inputs are missing.
3. In `src/shapez2_factory/application/asteroid_lab/run_stack.py` (L211–214), verify `run_ok` / `validation_passed` reflect stack failure when L2 nil-plan is fail-closed.
4. In `django_apps/asteroid_lab/layers/stack_runner.py` (L100–105), patch `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent` to `run_layers_02_to_06`.
5. Add unit test in `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py` (or new focused module) asserting `run_layers_02_to_06` with default L2 runner and `capacity_envelope=None` does not return `SUCCESS`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py`
- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `django_apps/asteroid_lab/layers/stack_runner.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py` (downstream skip behavior reference only)
- `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py`

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/stack_runner.py django_apps/asteroid_lab/layers/stack_runner.py`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/asteroid_lab/layers/ -k stack_runner -v`
- build: N/A
- manual verification: Django `run_layers_02_to_05` with missing envelope yields non-success stack status in Lab/CLI artifacts

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Choosing `failed_layer_slug` vs new `SKIPPED_INPUT` outcome affects manifest/error_code semantics (see SHA-33).
- Related SHA-15 / SHA-13 issues remain distinct; do not conflate L6 validation stub with L2 nil-plan fail-open.
