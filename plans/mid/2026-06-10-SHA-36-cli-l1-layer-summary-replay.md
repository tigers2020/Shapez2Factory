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
- Status at planning time: In Progress
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
- Changing Django `stack_runner` behavior.
- Fixing `reconstruction_capacity.by_resource.authority` drift — tracked in low-priority plan / separate issue.
- Implementing L6 commit-validate (SHA-15).

## Implementation Plan

1. In `run_stack.py`, after inline reconstruction (lines 177–184), construct `Layer01ReconstructionOutput(complete_map=complete_map, capacity_envelope=capacity_envelope)`.
2. Import `LAYER_01_RECONSTRUCTION` from `layer_slugs` and `build_layer01_post_summary_metrics` from `post_summary_metrics`.
3. Build an L1 layer summary dict matching `_layer_summary_to_json` shape: `layer_slug`, `layer_index=1`, `outcome="completed"`, `elapsed_ms` (measure inline L1 block or use `0` if not yet timed — prefer monotonic timing around decode→complete_map), `remaining_budget_ms=None`, `metrics=build_layer01_post_summary_metrics(layer01)`.
4. Prepend the L1 summary before `core_result.layer_summaries` when building `layer_summaries` for `solver_summary`.
5. Update `replay_core_lines` enumeration so L1 is `frame_index=0` (first `layer_done` after header) and L2–L6 indices shift by +1; verify monotonic sequence still holds.
6. Trace verbose CLI output path (`interfaces/cli/asteroid_solve.py` or equivalent) and ensure L1 emits `asteroid_cli layer_done layer_slug=layer_01_reconstruction` when `--verbose` is set.
7. Extend `test_cli_run_artifact.py`:
   - Assert `solver_summary["layer_summaries"][0]["layer_slug"] == "layer_01_reconstruction"`.
   - Assert L1 metrics keys (`complete_map_cell_count`, `coord_frame`, etc.) are present.
   - Assert first `layer_done` replay line slug is `layer_01_reconstruction`.
   - Update `test_cli_run_verbose_emits_layer_lines` to assert L1 verbose line appears before L2.
8. Run `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/shapez2_factory/test_replay_core_monotonic.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py` (import only)
- `src/shapez2_factory/application/asteroid_lab/layers/layer_01_reconstruction/output.py` (import only)
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_slugs.py` (import only)
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (verbose layer_done emission, if separate from run_stack)
- `django_apps/asteroid_lab/layers/stack_runner.py` (reference only — do not change)
- `tests/unit/shapez2_factory/test_cli_run_artifact.py`
- `tests/unit/shapez2_factory/test_replay_core_monotonic.py` (verify fixture alignment)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/run_stack.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/shapez2_factory/test_replay_core_monotonic.py -v`
- build: `python manage.py check`
- manual verification: Run CLI `run --verbose` on reconstruction fixture; confirm `solver_summary.json` has six layer summaries starting with L1 and `replay_core.jsonl` first `layer_done` is L1.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- L1 `elapsed_ms` timing: Django path times `run_layer_01`; CLI inline path may need explicit timing for parity.
- `completed_layer_slugs` in `solver_summary` may still omit L1 unless also updated — confirm whether Lab UI reads `layer_summaries` only or also `completed_layer_slugs`.
- Frame index shift may affect consumers assuming L2 was frame 0; regression tests and replay monotonic contract should catch drift.
