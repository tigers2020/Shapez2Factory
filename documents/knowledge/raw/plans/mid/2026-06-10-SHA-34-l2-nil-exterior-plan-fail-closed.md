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

When Layer 02 exterior transport cannot run because `capacity_envelope` or `throughput_target_percent` is missing, `run_layer_02_exterior_transport` returns `None`. Core `stack_runner` still records L2 as `COMPLETED` with stub metrics (`{"stub": True}`), passes `exterior_plan=None` to downstream layers, and finishes with `StackRunStatus.SUCCESS`. L3 and later layers silently skip (e.g. `MISSING_EXTERIOR_CONNECTION_PLAN`) while `RunStackUseCase` reports `run_success=true` and `validation_passed=true`.

The Django deprecated alias `run_layers_02_to_05` forwards to `run_layers_02_to_06` without `capacity_envelope` or `throughput_target_percent`, making the no-op L2 path easy to trigger from Django callers.

## Scope

- Detect invalid L2 output (`None` or not `ExteriorConnectionPlan`) in core `stack_runner` and fail-closed instead of recording `COMPLETED` + `SUCCESS`.
- Set `failed_layer_slug` to `LAYER_02_EXTERIOR_TRANSPORT`, use non-success stack status (prefer existing `StackRunStatus.LAYER_FAILED_CLOSED`), and stop the stack before L3+ run.
- Fix Django `run_layers_02_to_05` to accept and forward `capacity_envelope` and `throughput_target_percent` like `run_layers_02_to_06`.
- Add regression test: default L2 runner with `capacity_envelope=None` must not return `StackRunStatus.SUCCESS`.

## Non-goals

- Full L6 validation semantics ([SHA-15](https://linear.app/zkaufman/issue/SHA-15)).
- Changing L2 EVTC shortfall semantics when a plan object exists with `unmet_reason`.
- Rewriting layer skip-reason enums across all layers.
- Adding new `LayerPostSummaryOutcome` values unless contract review requires it (prefer fail-closed with existing outcomes first).

## Implementation Plan

1. **Reproduce with failing test (TDD)**
   - Add test in `tests/unit/asteroid_lab/layers/` (new file or extend skeleton tests) calling core `run_layers_02_to_06` with default L2 runner, valid `complete_map` fixture, `capacity_envelope=None`.
   - Assert `stack_result.status != StackRunStatus.SUCCESS`.
   - Assert `stack_result.failed_layer_slug == LAYER_02_EXTERIOR_TRANSPORT`.
   - Assert L2 summary is not `COMPLETED` with stub-only metrics (or stack stops before L3 summaries).

2. **Core stack_runner fail-closed on L2 nil/invalid result**
   - In `src/shapez2_factory/application/asteroid_lab/stack_runner.py`, after L2 `entry.run(...)`, check `isinstance(last_exterior_plan, ExteriorConnectionPlan)`.
   - If false: append L2 summary with appropriate outcome (failed/skipped — align with existing `LayerPostSummaryOutcome` or document new outcome if added), return `CoreStackRunResult` with `StackRunStatus.LAYER_FAILED_CLOSED`, `failed_layer_slug=LAYER_02_EXTERIOR_TRANSPORT`, and partial `completed_layer_slugs`.
   - Include diagnostic snapshot consistent with existing timeout fail-closed path.

3. **Django wrapper forwarding fix**
   - In `django_apps/asteroid_lab/layers/stack_runner.py`, add `capacity_envelope` and `throughput_target_percent` parameters to `run_layers_02_to_05` signature.
   - Forward both to `run_layers_02_to_06` call (mirror `run_layers_02_to_06` defaults: `throughput_target_percent=80`).
   - Search callers of `run_layers_02_to_05`; update only if signature change breaks them (optional kwargs should be backward compatible).

4. **RunStackUseCase propagation check**
   - Confirm `run_stack.py` already sets `run_ok = failed_layer_slug is None` — no change expected if stack_runner sets failure correctly.
   - Verify CLI artifact / solver summary reflects failure in existing tests or add assertion in new regression test.

5. **Document remaining risks**
   - Note interaction with [SHA-15](https://linear.app/zkaufman/issue/SHA-15) (validation_passed still tracks stack success, not L6).
   - Note stub L2 runners in skeleton tests may need adjustment if they intentionally return non-plan values.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py` (read-only reference; likely no change)
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/stack_status.py` (read-only; use `LAYER_FAILED_CLOSED`)
- `src/shapez2_factory/application/asteroid_lab/run_stack.py` (verify only)
- `django_apps/asteroid_lab/layers/stack_runner.py`
- `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py` (may need stub runner review)
- New or extended test file for L2 nil-return regression

## Validation Plan

- lint: `ruff check .` on touched files
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/layers/ -v -k "l2 or exterior or stack_runner"`
- build: `python manage.py check`
- manual verification: Run stack via CLI or Django path without `capacity_envelope`; confirm non-success status and `failed_layer_slug=layer_02_exterior_transport` in artifacts

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Outcome enum:** Spec allows `failed_layer_slug` or new `SKIPPED_INPUT` outcome. Prefer `LAYER_FAILED_CLOSED` + existing outcomes unless product wants explicit skip semantics for missing inputs vs runtime failure.
- **Stub L2 runners:** Skeleton tests use stub runners that may not return `ExteriorConnectionPlan`; ensure test doubles still pass while real L2 nil path fails closed.
- **SHA-15 overlap:** Fixing L2 failure improves `validation_passed` accuracy for this path but does not resolve L6 stub false positives.
- **Deprecated alias callers:** `run_layers_02_to_05` callers that relied on silent L2 skip will now see stack failure — intended behavior per spec.
