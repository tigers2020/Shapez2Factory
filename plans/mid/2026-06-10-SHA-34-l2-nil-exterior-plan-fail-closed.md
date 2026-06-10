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

# Plan: stack_runner marks L2 COMPLETED and returns SUCCESS when exterior transport returns None

## Source Issue

- Linear: SHA-34
- Status at planning time: Todo
- Priority: Mid

## Problem

When Layer 02 exterior transport cannot run because `capacity_envelope` is missing, `run_layer_02_exterior_transport` returns `None`. Core `stack_runner` still records L2 as `completed` with stub metrics, passes `exterior_plan=None` to L3, and finishes with `StackRunStatus.SUCCESS`. Downstream layers silently skip while `RunStackUseCase` reports `run_success=true` and `validation_passed=true`. Django alias `run_layers_02_to_05` omits `capacity_envelope` forwarding, making the fail-open path easy to trigger.

## Scope

- Detect `None` / invalid L2 output in `stack_runner` and propagate failure (or explicit skipped outcome) instead of `COMPLETED` + `SUCCESS`.
- Fix Django `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent` like `run_layers_02_to_06`.
- Add regression test for default L2 runner with missing `capacity_envelope`.

## Non-goals

- Implementing full L6 validation (SHA-15).
- Changing L2 EVTC shortfall semantics when a plan object exists with `unmet_reason`.
- Rewriting layer skip-reason enums across all layers.

## Implementation Plan

1. Read `stack_runner.py` L2 branch (lines ~165–234) and `run_layer_02_exterior_transport` nil-return guard (`layer_02_exterior_transport/run.py` L84–85); confirm current `COMPLETED` + stub metrics behavior.
2. After L2 `entry.run(...)`, if result is not `ExteriorConnectionPlan`, set `failed_layer_slug=LAYER_02_EXTERIOR_TRANSPORT`, append a failed/skipped summary (not `COMPLETED` with `stub: True`), and return early with non-success `StackRunStatus` (e.g. `FAILED` or existing fail-closed status used elsewhere).
3. Verify `RunStackUseCase` (`run_stack.py`) derives `run_success` / `validation_passed` from `failed_layer_slug` — no change expected if stack result propagates correctly.
4. Patch `django_apps/asteroid_lab/layers/stack_runner.py` `run_layers_02_to_05` to accept and forward `capacity_envelope` and `throughput_target_percent` to `run_layers_02_to_06`.
5. Add unit test in `tests/unit/asteroid_lab/layers/` asserting `run_layers_02_to_06` with default L2 runner and `capacity_envelope=None` does not return `StackRunStatus.SUCCESS` and sets `failed_layer_slug` to L2.
6. Extend or add test covering Django `run_layers_02_to_05` forwarding if callers pass envelope args.
7. Grep for `run_layers_02_to_05` call sites; confirm no caller relies on silent success with missing envelope.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py` (read-only unless contract comment)
- `src/shapez2_factory/application/asteroid_lab/run_stack.py` (verify propagation)
- `django_apps/asteroid_lab/layers/stack_runner.py`
- `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py`
- `tests/unit/asteroid_lab/layers/test_stack_runner_core_boundary.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/layers/test_stack_runner_core_boundary.py tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py -v`
- build: N/A
- manual verification: Run solver smoke with missing envelope inputs; confirm CLI/Lab artifacts show non-success, not stub L2 completion

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Whether to use `FAILED` vs new `SKIPPED_INPUT` outcome — issue allows either; prefer existing enum values unless catalog lacks a fit.
- Related SHA-15 (L6 validation stub) and SHA-33 (manifest error_code) remain separate; do not expand scope.
- Stub L2 runners in skeleton tests may need fixture updates if they intentionally return non-plan values.
