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

# Plan: Add L1 reconstruction to CLI layer_summaries and replay_core

## Source Issue

- Linear: SHA-36
- Status at planning time: In Progress
- Priority: Mid

## Problem

CLI `RunStackUseCase` runs Layer 01 reconstruction inline but never records `layer_01_reconstruction` in `solver_summary.layer_summaries` or `replay_core.jsonl`. Django path emits L1 via `build_layer01_post_summary_metrics`; CLI artifacts omit L1 despite writing `layer01_complete_map.json`.

## Scope

- Add L1 summary record to CLI `solver_summary.layer_summaries` with metrics from `build_layer01_post_summary_metrics`.
- Prepend L1 `layer_done` frame to `replay_core.jsonl` (preserve monotonic `frame_index`).
- Emit verbose CLI `layer_done` line for L1 when `--verbose` is set.
- Add regression tests for L1 presence in artifact summary and replay core.

## Non-goals

- Refactoring L1 into separate `run_layer_01` runner unless required.
- Changing Django `stack_runner` behavior.
- Fixing `reconstruction_capacity.by_resource.authority` drift.
- L6 commit-validate (SHA-15).

## Implementation Plan

1. After inline reconstruction in `RunStackUseCase.run`, build `Layer01ReconstructionOutput(complete_map, capacity_envelope)`.
2. Call `build_layer01_post_summary_metrics`; prepend L1 `LayerSummaryRecord` before L2–L6 summaries.
3. Shift `replay_core` `frame_index` so L1 is first `layer_done` after header.
4. Extend verbose CLI output for L1 when `--verbose`.
5. Update `test_cli_run_artifact.py`: assert `layer_01_reconstruction` at `layer_summaries[0]` and first replay `layer_done` slug.
6. Run `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/shapez2_factory/test_replay_core_monotonic.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py`
- `tests/unit/shapez2_factory/test_cli_run_artifact.py`
- `tests/unit/shapez2_factory/test_replay_core_monotonic.py`

## Validation Plan

- tests: `python -m pytest tests/unit/shapez2_factory/test_cli_run_artifact.py -v`
- lint: `ruff check src/shapez2_factory/application/asteroid_lab/run_stack.py`
- typecheck: `mypy django_apps config src` (spot-check)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Frame index shift may affect consumers assuming L2-first replay — verify `test_replay_core_monotonic` fixtures.
