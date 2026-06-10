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

When Layer 02 exterior transport cannot run because `capacity_envelope` is missing, `run_layer_02_exterior_transport` returns `None`. The core `stack_runner` still records L2 as `completed` with stub metrics, passes `exterior_plan=None` to L3, and finishes the stack with `StackRunStatus.SUCCESS`.

## Scope

- Detect `None` / invalid L2 output in `stack_runner` and propagate failure instead of `COMPLETED` + `SUCCESS`.
- Fix Django `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent`.
- Add regression test for default L2 runner with missing `capacity_envelope`.

## Non-goals

- Implementing full L6 validation (SHA-15).
- Changing L2 EVTC shortfall semantics when a plan object exists with `unmet_reason`.
- Rewriting layer skip-reason enums across all layers.

## Implementation Plan

1. Read `stack_runner.py` L2 run loop and `run_layer_02_exterior_transport` nil-return path.
2. After L2 run, if result is not `ExteriorConnectionPlan`, set `failed_layer_slug=LAYER_02_EXTERIOR_TRANSPORT` and stop stack (fail-closed).
3. Patch `django_apps/asteroid_lab/layers/stack_runner.py` `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent`.
4. Add unit test: `run_layers_02_to_06` with default L2 runner and `capacity_envelope=None` does not return `SUCCESS`.
5. Run `pytest tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py -v` and new regression test.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py`
- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `django_apps/asteroid_lab/layers/stack_runner.py`
- `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py`

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/ django_apps/asteroid_lab/layers/`
- typecheck: `mypy django_apps config src`
- tests: stack runner unit tests
- build: N/A
- manual verification: Missing envelope path reports non-success in CLI verbose output

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SKIPPED vs FAILED outcome semantics — issue allows either; prefer fail-closed per spec.
- Related SHA-33 manifest error_code on different failure mode.
