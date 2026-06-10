---
linear_issue: SHA-36
title: CLI RunStackUseCase omits layer_01_reconstruction from layer_summaries and replay_core
priority: Mid
labels:
  - bug
  - solver
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: CLI RunStackUseCase omits layer_01_reconstruction from layer_summaries and replay_core

## Source Issue

- Linear: SHA-36
- Status at planning time: Todo
- Priority: Mid

## Problem

CLI-first `RunStackUseCase` runs Layer 01 reconstruction inline but never records `layer_01_reconstruction` in `solver_summary.layer_summaries` or `replay_core.jsonl`. Django `run_full_from_cleanup_recon` treats L1 as first-class and emits post-summary metrics via `build_layer01_post_summary_metrics`. CLI artifacts ship an incomplete six-layer observability contract even though `layer01_complete_map.json` is written.

## Scope

- Add L1 summary record to CLI `solver_summary.layer_summaries` with metrics from `build_layer01_post_summary_metrics`.
- Prepend L1 `layer_done` frame to `replay_core.jsonl` output (preserve monotonic `frame_index`).
- Emit verbose CLI `layer_done` line for L1 when `--verbose` is set.
- Add regression tests asserting L1 presence in artifact `solver_summary` and `replay_core`.

## Non-goals

- Refactoring L1 into a separate `run_layer_01` runner unless required for metrics timing.
- Changing Django `stack_runner` behavior.
- Fixing `reconstruction_capacity.by_resource.authority` drift.
- Implementing L6 commit-validate (SHA-15).

## Implementation Plan

1. Read `run_stack.py` L1 inline reconstruction block (~L177–184) and summary assembly (~L210–231); read Django reference in `django_apps/asteroid_lab/layers/stack_runner.py` L127–138 for parity target.
2. After inline reconstruction, build `Layer01ReconstructionOutput(complete_map, capacity_envelope)` (or reuse existing struct if present).
3. Call `build_layer01_post_summary_metrics` from `post_summary_metrics.py` and prepend L1 `LayerSummaryRecord` (index 1) before L2–L6 summaries in `solver_summary.layer_summaries`.
4. Prepend L1 `layer_done` event as first frame after replay header in `replay_core.jsonl`; renumber subsequent `frame_index` values to stay monotonic.
5. When `--verbose`, emit `layer_done` line for `layer_01_reconstruction` consistent with L2+ verbose output in `test_cli_run_verbose_emits_layer_lines`.
6. Extend `tests/unit/shapez2_factory/test_cli_run_artifact.py` to assert `layer_01_reconstruction` is `layer_summaries[0]` with expected metric keys.
7. Update `tests/unit/shapez2_factory/test_replay_core_monotonic.py` if frame indices shift; confirm fixture still valid.
8. Verify `layer_behavior_catalog.py` L1 formatter receives expected metrics shape.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/layer_behavior_catalog.py` (verify only)
- `django_apps/asteroid_lab/layers/stack_runner.py` (read-only reference)
- `tests/unit/shapez2_factory/test_cli_run_artifact.py`
- `tests/unit/shapez2_factory/test_replay_core_monotonic.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/shapez2_factory/test_replay_core_monotonic.py -v`
- build: `python manage.py run_solver --slug <slug>` smoke optional
- manual verification: Inspect CLI artifact `solver_summary.json` and `replay_core.jsonl` for L1 as first layer

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `reconstruction_capacity.by_resource.authority` drift is out of scope — note if tests surface mismatch.
- Lab UI heuristics in `solver_run_lab_summary` may still work; artifact truth becomes authoritative after fix.
- Coordinate with SHA-21 replay compose guard if frame shape changes affect deserialization.
