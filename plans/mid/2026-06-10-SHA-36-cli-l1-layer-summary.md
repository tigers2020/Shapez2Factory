---
linear_issue: SHA-36
title: CLI RunStackUseCase omits layer_01_reconstruction from layer_summaries and replay_core
priority: Mid
labels:
  - bug
  - solver
  - reviewing
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: CLI L1 layer summary and replay_core wiring

## Source Issue

- Linear: SHA-36
- Status at planning time: Todo
- Priority: Mid

## Problem

The CLI-first `RunStackUseCase` runs Layer 01 reconstruction inline (decode → cleanup → topology → complete map) but never records `layer_01_reconstruction` in `solver_summary.layer_summaries` or `replay_core.jsonl`. Django's `run_full_from_cleanup_recon` treats L1 as a first-class layer and emits post-summary metrics via `build_layer01_post_summary_metrics`. CLI artifacts therefore ship an incomplete six-layer observability contract even though `layer01_complete_map.json` is written.

## Scope

- Add L1 summary record to CLI `solver_summary.layer_summaries` with metrics from `build_layer01_post_summary_metrics`.
- Prepend L1 `layer_done` frame to `replay_core.jsonl` output (preserve monotonic `frame_index`).
- Emit verbose CLI `layer_done` line for L1 when `--verbose` is set.
- Add regression tests asserting L1 presence in artifact `solver_summary` and `replay_core`.

## Non-goals

- Refactoring L1 into a separate `run_layer_01` runner unless required for metrics timing.
- Changing Django stack_runner behavior.
- Fixing `reconstruction_capacity.by_resource.authority` drift.
- Implementing L6 commit-validate (SHA-15).

## Implementation Plan

1. In `src/shapez2_factory/application/asteroid_lab/run_stack.py` (L177–184), after inline reconstruction, build a `Layer01ReconstructionOutput(complete_map, capacity_envelope)` wrapper for metrics.
2. Call `build_layer01_post_summary_metrics` from `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py` and prepend an L1 `LayerSummaryRecord` before L2–L6 summaries (currently built only from `core_result.layer_summaries` at L210–220).
3. Shift `replay_core_lines` enumeration (L222–231) so L1 is the first `layer_done` frame after header; verify monotonic `frame_index` in `tests/unit/shapez2_factory/test_replay_core_monotonic.py`.
4. Extend verbose CLI output in `run_stack.py` to emit L1 `layer_done` when `--verbose` is set; update `tests/unit/shapez2_factory/test_cli_run_artifact.py::test_cli_run_verbose_emits_layer_lines`.
5. Mirror Django reference behavior in `django_apps/asteroid_lab/layers/stack_runner.py` (L127–138) for metric field parity; confirm `layer_behavior_catalog.py` L1 formatter expectations.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/layer_behavior_catalog.py`
- `django_apps/asteroid_lab/layers/stack_runner.py` (reference only)
- `tests/unit/shapez2_factory/test_cli_run_artifact.py`
- `tests/unit/shapez2_factory/test_replay_core_monotonic.py`

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/run_stack.py`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/shapez2_factory/test_replay_core_monotonic.py -v`
- build: N/A
- manual verification: CLI run with `--verbose` shows L1 as first layer_done; artifact JSON has `layer_01_reconstruction` at index 0

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Shifting replay `frame_index` may affect consumers assuming L2 is frame 0 — check Lab replay compose paths (SHA-21, SHA-64).
- Lab UI heuristics in `solver_run_lab_summary._completed_layer_slugs_from_summary` may become redundant after artifact fix.
