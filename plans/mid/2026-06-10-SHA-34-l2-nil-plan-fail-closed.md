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

# Plan: Fail-closed L2 nil exterior plan in stack_runner

## Source Issue

- Linear: SHA-34
- Status at planning time: In Progress
- Priority: Mid

## Problem

When `run_layer_02_exterior_transport` returns `None` because `capacity_envelope` or `throughput_target_percent` is missing, core `stack_runner` still records L2 as `COMPLETED` with `{"stub": True}` metrics, passes `exterior_plan=None` to downstream layers, and finishes with `StackRunStatus.SUCCESS`. `RunStackUseCase` then reports `run_success=true` and `validation_passed=true` while L3+ silently skip (e.g. `MISSING_EXTERIOR_CONNECTION_PLAN`).

The Django deprecated alias `run_layers_02_to_05` makes this easy to trigger: it calls `run_layers_02_to_06` without forwarding `capacity_envelope` or `throughput_target_percent`.

## Scope

- Detect invalid/nil L2 output in core `stack_runner` and stop the stack with a non-success status and `failed_layer_slug=LAYER_02_EXTERIOR_TRANSPORT`.
- Fix Django `run_layers_02_to_05` to forward `capacity_envelope` and `throughput_target_percent` like `run_layers_02_to_06`.
- Add regression test for default L2 runner with `capacity_envelope=None`.

## Non-goals

- Full L6 validation semantics ([SHA-15](https://linear.app/zkaufman/issue/SHA-15)).
- Changing L2 EVTC shortfall semantics when a plan object exists with `unmet_reason`.
- Rewriting layer skip-reason enums across all layers (deferred to Low plan).

## Implementation Plan

1. **Reproduce fail-open path in a failing test**
   - Add `test_run_layers_02_to_06_fails_closed_when_l2_returns_none` in `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py` (or new focused file under `tests/unit/shapez2_factory/application/asteroid_lab/`).
   - Call core `run_layers_02_to_06` with `_DEFAULT_RUNNERS` (real L2), `capacity_envelope=None`, valid `complete_map` fixture.
   - Assert `stack_result.status != StackRunStatus.SUCCESS`, `failed_layer_slug == LAYER_02_EXTERIOR_TRANSPORT`, and `run_success` path via `RunStackUseCase` is false when wired.

2. **Fail-closed branch after L2 run in core stack_runner**
   - In `src/shapez2_factory/application/asteroid_lab/stack_runner.py`, after L2 `entry.run(...)` when `canonical_slug == LAYER_02_EXTERIOR_TRANSPORT`:
     - If result is not `ExteriorConnectionPlan`, append a layer summary with a non-completed outcome (prefer reusing `LayerPostSummaryOutcome.SKIPPED_BUDGET` pattern or add `SKIPPED_INPUT` only if contract requires new enum — issue proposes `failed_layer_slug` + stop, not enum refactor).
     - Return `CoreStackRunResult` with `status=StackRunStatus.LAYER_FAILED_CLOSED`, `failed_layer_slug=entry.slug`, `completed_layer_slugs` excluding failed layer.
   - Include diagnostic metrics: `{"reason": "missing_exterior_plan", "stub_inputs": True}`.

3. **Confirm RunStackUseCase propagates failure**
   - Verify `src/shapez2_factory/application/asteroid_lab/run_stack.py` sets `run_ok = failed_layer_slug is None` — no change expected if stack_result already sets `failed_layer_slug`.
   - Add/adjust unit assertion that `validation_passed` is false when L2 fails closed.

4. **Fix Django deprecated alias forwarding**
   - Update `django_apps/asteroid_lab/layers/stack_runner.py` `run_layers_02_to_05` signature to accept optional `capacity_envelope` and `throughput_target_percent` (defaults matching `run_layers_02_to_06`).
   - Forward both kwargs to `run_layers_02_to_06`.
   - Add test that `run_layers_02_to_05(..., capacity_envelope={...})` reaches L2 planning (not nil-return stub).

5. **Regression gate**
   - Run `pytest tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py -v` plus any new test module.
   - Run `ruff check` / `mypy` on touched modules per `AGENTS.md`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py` (read-only unless contract tweak needed)
- `src/shapez2_factory/application/asteroid_lab/run_stack.py` (verify only)
- `django_apps/asteroid_lab/layers/stack_runner.py`
- `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py`
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/stack_status.py` (existing `LAYER_FAILED_CLOSED`)
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_post_summary.py` (only if new outcome enum approved)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/ django_apps/asteroid_lab/layers/stack_runner.py`
- typecheck: `mypy django_apps config src` (touched paths)
- tests: `pytest tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py -v` + new regression test
- build: `python manage.py check`
- manual verification: invoke `run_layers_02_to_05` without envelope via Django test or CLI smoke; confirm non-SUCCESS stack status in artifact/summary

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Outcome enum vs failed_layer_slug only:** Issue allows either `failed_layer_slug` stop or new `SKIPPED_INPUT` outcome. Prefer `LAYER_FAILED_CLOSED` + `failed_layer_slug` to avoid cross-layer enum refactor (see Low plan).
- **Stub L2 runners in existing skeleton tests:** Tests using fake `_Layer02To05Runner` must remain green; only default/real L2 path changes.
- **Related issues:** [SHA-15](https://linear.app/zkaufman/issue/SHA-15) (validation_passed), [SHA-33](https://linear.app/zkaufman/issue/SHA-33) (manifest error_code), [SHA-54](https://linear.app/zkaufman/issue/SHA-54) (L5 empty plan) — distinct contracts; do not conflate fixes.
