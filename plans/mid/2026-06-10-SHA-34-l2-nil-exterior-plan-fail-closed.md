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

# Plan: Fail-closed stack when L2 exterior transport returns None

## Source Issue

- Linear: SHA-34
- Status at planning time: Todo
- Priority: Mid

## Problem

When Layer 02 exterior transport cannot run because `capacity_envelope` is missing, `run_layer_02_exterior_transport` returns `None`. Core `stack_runner` still records L2 as `COMPLETED` with stub metrics, passes `exterior_plan=None` to L3, and finishes with `StackRunStatus.SUCCESS`. Downstream layers skip silently while `RunStackUseCase` reports `run_success=true`.

## Scope

- Detect invalid/`None` L2 output in `stack_runner` and propagate failure instead of `COMPLETED` + `SUCCESS`.
- Fix Django `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent`.
- Add regression test for missing `capacity_envelope` with default L2 runner.

## Non-goals

- Full L6 validation (SHA-15).
- Changing L2 EVTC shortfall semantics when a plan object exists with `unmet_reason`.
- Rewriting layer skip-reason enums across all layers.

## Implementation Plan

1. In `stack_runner.py`, after L2 `entry.run(...)`, if result is not `ExteriorConnectionPlan`, set `failed_layer_slug` to L2 slug and break stack loop (mirror timeout/budget failure path).
2. Ensure `post_metrics` records explicit failure/skipped reason instead of `{"stub": True}` alone.
3. Patch `django_apps/asteroid_lab/layers/stack_runner.py` `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent` like `run_layers_02_to_06`.
4. Add unit test: `run_layers_02_to_06` with default L2 runner and `capacity_envelope=None` must not return `StackRunStatus.SUCCESS`.
5. Run `pytest tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py tests/unit/asteroid_lab/layers/test_stack_runner_core_boundary.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py`
- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `django_apps/asteroid_lab/layers/stack_runner.py`
- `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py`

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/stack_runner.py django_apps/asteroid_lab/layers/stack_runner.py`
- typecheck: `mypy django_apps config src` (spot-check)
- tests: `pytest tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py tests/unit/asteroid_lab/layers/test_stack_runner_core_boundary.py -v`
- build: N/A
- manual verification: Django `run_layers_02_to_05` with real map and missing envelope should not report success

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Coordinate with SHA-33 (manifest `error_code` on stack failure) so fail-closed L2 sets consistent artifact error codes.
- Stub L2 runners in skeleton tests may need envelope fixtures updated after behavior change.
