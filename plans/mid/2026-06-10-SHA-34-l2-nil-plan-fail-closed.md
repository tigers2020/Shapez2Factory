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

# Plan: L2 nil exterior plan fail-closed stack behavior

## Source Issue

- Linear: SHA-34
- Status at planning time: Todo
- Priority: Mid

## Problem

When L2 exterior transport cannot run (`capacity_envelope` missing), `run_layer_02_exterior_transport` returns `None`. Core `stack_runner` still records L2 as `COMPLETED` with stub metrics, passes `exterior_plan=None` to L3, and finishes with `StackRunStatus.SUCCESS`. Django `run_layers_02_to_05` omits `capacity_envelope` forwarding, making this easy to trigger.

## Scope

- Detect `None`/invalid L2 output in `stack_runner` and propagate failure instead of `COMPLETED` + `SUCCESS`.
- Fix Django `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent`.
- Add regression test for default L2 runner with missing `capacity_envelope`.

## Non-goals

- Implementing full L6 validation (SHA-15).
- Changing L2 EVTC shortfall semantics when plan object exists with `unmet_reason`.
- Rewriting layer skip-reason enums across all layers.

## Implementation Plan

1. In `stack_runner.py` after L2 run, if result is not `ExteriorConnectionPlan`, set `failed_layer_slug=LAYER_02_EXTERIOR_TRANSPORT` and stop stack.
2. Patch Django `run_layers_02_to_05` in `django_apps/asteroid_lab/layers/stack_runner.py` to forward envelope args like `run_layers_02_to_06`.
3. Add unit test: `run_layers_02_to_06` with default L2 runner and `capacity_envelope=None` does not return `SUCCESS`.
4. Run `pytest tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py -v` and core stack runner tests.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py`
- `django_apps/asteroid_lab/layers/stack_runner.py`
- `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/layers/ -v -k stack_runner`
- build: `python manage.py check`
- manual verification: Run stack without capacity envelope; confirm non-success status.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Fail-closed may change behavior for callers relying on silent L3 skip; document migration.
- Related SHA-33 manifest error_code propagation should align on stack failure.
