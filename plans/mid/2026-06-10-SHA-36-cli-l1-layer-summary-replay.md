---
linear_issue: SHA-36
title: CLI RunStackUseCase omits layer_01_reconstruction from layer_summaries and replay_core
priority: Mid
labels:
  - bug
  - solver
status: planned
created_by: todo-plan-automation
---

# Plan: Add L1 reconstruction to CLI solver_summary and replay_core

## Source Issue

- Linear: SHA-36
- Status at planning time: Todo
- Priority: Mid

## Problem

CLI `RunStackUseCase` runs Layer 01 reconstruction inline but never records `layer_01_reconstruction` in `solver_summary.layer_summaries` or `replay_core.jsonl`. Django path emits L1 via `build_layer01_post_summary_metrics`; CLI artifacts omit L1 observability despite writing `layer01_complete_map.json`.

## Scope

- Add L1 summary record to CLI `solver_summary.layer_summaries` using `build_layer01_post_summary_metrics`.
- Prepend L1 `layer_done` frame to `replay_core.jsonl` with monotonic `frame_index`.
- Emit verbose CLI `layer_done` line for L1 when `--verbose`.
- Add regression tests for L1 presence in artifact outputs.

## Non-goals

- Refactoring L1 into a separate `run_layer_01` runner unless required for metrics timing.
- Changing Django `stack_runner` behavior.
- Fixing `reconstruction_capacity.by_resource.authority` drift.
- L6 commit-validate (SHA-15).

## Implementation Plan

1. After inline reconstruction in `src/shapez2_factory/application/asteroid_lab/run_stack.py`, build `Layer01ReconstructionOutput(complete_map, capacity_envelope)`.
2. Call `build_layer01_post_summary_metrics` from `post_summary_metrics.py` and prepend L1 `LayerSummaryRecord` before L2–L6 summaries.
3. Shift `replay_core` `frame_index` so L1 is the first `layer_done` after header.
4. Extend verbose output to include L1 `layer_done` when `--verbose`.
5. Update `tests/unit/shapez2_factory/test_cli_run_artifact.py` to assert `layer_01_reconstruction` at index 0 in `solver_summary.layer_summaries` and first replay `layer_done` slug.
6. Verify `tests/unit/shapez2_factory/test_replay_core_monotonic.py` fixture alignment.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/layer_behavior_catalog.py`
- `tests/unit/shapez2_factory/test_cli_run_artifact.py`
- `tests/unit/shapez2_factory/test_replay_core_monotonic.py`

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/shapez2_factory/test_replay_core_monotonic.py -v`
- build: N/A
- manual verification: Run CLI solve with `--verbose`; confirm L1 appears before L2 in stdout and artifact JSON

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Frame index shift may affect consumers assuming L2 is frame 0 — check replay compose tests.
- Lab UI heuristics on `reconstruction_capacity` may become redundant; do not remove without separate UX review.
