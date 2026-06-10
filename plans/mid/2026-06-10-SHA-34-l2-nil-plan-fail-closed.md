---
linear_issue: SHA-34
title: stack_runner marks L2 COMPLETED and returns SUCCESS when exterior transport returns None
priority: Mid
labels:
  - bug
  - solver
status: planned
created_by: todo-plan-automation
---

# Plan: Fail-closed when L2 exterior transport returns None

## Source Issue

- Linear: SHA-34
- Status at planning time: Todo
- Priority: Mid

## Problem

When `run_layer_02_exterior_transport` returns `None` (missing `capacity_envelope` or `throughput_target_percent`), `stack_runner` still records L2 as `COMPLETED` with stub metrics, passes `exterior_plan=None` to L3, and finishes with `StackRunStatus.SUCCESS`. Downstream layers skip silently while CLI/Django report success.

## Scope

- Detect `None` / invalid L2 output in core `stack_runner` and propagate failure instead of `COMPLETED` + `SUCCESS`.
- Fix Django `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent`.
- Add regression test for default L2 runner with missing `capacity_envelope`.

## Non-goals

- Full L6 validation (SHA-15).
- Changing L2 EVTC shortfall semantics when a plan object exists with `unmet_reason`.
- Rewriting layer skip-reason enums across all layers.

## Implementation Plan

1. In `src/shapez2_factory/application/asteroid_lab/stack_runner.py`, after L2 `entry.run(...)`, if result is not `ExteriorConnectionPlan`, set `failed_layer_slug` to L2 and stop the stack (or emit explicit skipped outcome per existing contract patterns).
2. Ensure `RunStackUseCase` maps the failure to `run_success=false` / non-success stack status.
3. In `django_apps/asteroid_lab/layers/stack_runner.py`, patch `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent` like `run_layers_02_to_06`.
4. Add unit test: `run_layers_02_to_06` with default L2 runner and `capacity_envelope=None` must not return `SUCCESS`.
5. Extend or add test in `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py` or dedicated L2 nil-return module.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py`
- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `django_apps/asteroid_lab/layers/stack_runner.py`
- `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py` (or new regression file)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/ django_apps/asteroid_lab/layers/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/layers/ -k stack_runner -v`
- build: `python manage.py check`
- manual verification: Trigger Django `run_layers_02_to_05` without envelope; confirm non-success outcome

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Contract choice: `failed_layer_slug` vs new `SKIPPED_INPUT` outcome — align with existing `LayerPostSummaryOutcome` enums.
- SHA-33 (manifest `error_code` on stack failure) is related but distinct; coordinate error surfacing if both land together.
