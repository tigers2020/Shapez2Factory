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

# Plan: Emit L1 reconstruction in CLI layer_summaries and replay_core

## Source Issue

- Linear: SHA-36
- Status at planning time: In Progress (moved from Todo by prior automation run)
- Priority: Mid

## Problem

The CLI-first `RunStackUseCase` runs Layer 01 reconstruction inline (decode → cleanup → topology → complete map) but never records `layer_01_reconstruction` in `solver_summary.layer_summaries` or `replay_core.jsonl`. Django's `run_full_from_cleanup_recon` treats L1 as a first-class layer and emits post-summary metrics via `build_layer01_post_summary_metrics`. CLI artifacts therefore ship an incomplete six-layer observability contract even though `layer01_complete_map.json` is written.

## Scope

- Add L1 summary record to CLI `solver_summary.layer_summaries` with metrics from `build_layer01_post_summary_metrics`.
- Prepend L1 `layer_done` frame to `replay_core.jsonl` output (preserve monotonic `frame_index`).
- Emit verbose CLI `layer_done` line for L1 when `--verbose` is set (automatic once L1 is in `layer_summaries`).
- Add regression tests asserting L1 presence in artifact `solver_summary` and `replay_core`.

## Non-goals

- Refactoring L1 into a separate `run_layer_01` runner unless required for metrics timing.
- Changing Django `stack_runner.py` behavior.
- Fixing `reconstruction_capacity.by_resource.authority` drift — see low-priority deferred plan.
- Implementing L6 commit-validate — tracked in SHA-15.

## Implementation Plan

1. In `RunStackUseCase.run`, after inline reconstruction (lines 177–184), wrap results in `Layer01ReconstructionOutput(complete_map=complete_map, capacity_envelope=capacity_envelope)`.
2. Import `LAYER_01_RECONSTRUCTION`, `LayerPostSummaryRecord`, `LayerPostSummaryOutcome`, and `build_layer01_post_summary_metrics`.
3. Time L1 inline work with `time.monotonic()` (match Django `stack_runner.py` lines 127–129) and build:
   ```python
   LayerPostSummaryRecord(
       layer_slug=LAYER_01_RECONSTRUCTION,
       layer_index=1,
       outcome=LayerPostSummaryOutcome.COMPLETED,
       elapsed_ms=l1_elapsed_ms,
       remaining_budget_ms=None,
       metrics=build_layer01_post_summary_metrics(layer01),
   )
   ```
4. Prepend `_layer_summary_to_json(l1_record)` before L2–L6 summaries in `layer_summaries`.
5. Rebuild `replay_core_lines` from the full six-layer list so `frame_index` stays `0..5` monotonic; first `layer_done` slug is `layer_01_reconstruction`.
6. Update `completed_layer_slugs` in `solver_summary` / `stack_result_json` if the six-layer contract expects L1 listed (verify against Django artifact shape; do not change stack runner status semantics).
7. Extend `test_cli_run_artifact.py`:
   - Assert `solver_summary.layer_summaries[0]["layer_slug"] == "layer_01_reconstruction"` and `layer_index == 1`.
   - Assert L1 metrics keys: `complete_map_cell_count`, `shape_field_cell_count`, `fluid_field_cell_count`, `coord_frame`.
   - Assert first replay `layer_done` frame slug is L1.
   - Update `test_cli_run_verbose_emits_layer_lines` to assert L1 verbose line appears before L2.
8. Run focused tests and canonical gates.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py` (import only)
- `src/shapez2_factory/application/asteroid_lab/layers/layer_01_reconstruction/output.py` (import only)
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (verbose path reads `layer_summaries`; no change expected if L1 prepended)
- `tests/unit/shapez2_factory/test_cli_run_artifact.py`
- `tests/unit/shapez2_factory/test_replay_core_monotonic.py` (reference fixture only)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/run_stack.py tests/unit/shapez2_factory/test_cli_run_artifact.py`
- typecheck: `mypy django_apps config src` (touched modules)
- tests: `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/shapez2_factory/test_replay_core_monotonic.py -v`
- build: N/A
- manual verification: `python -m shapez2_factory.interfaces.cli.asteroid_solve run ... --verbose` and inspect `solver_summary.json` + `replay_core.jsonl` first `layer_done`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Whether `completed_layer_slugs` in CLI `stack_result_json` should include L1 (Django path may differ); align with artifact consumers / Lab UI heuristics without expanding scope.
- L1 `elapsed_ms` covers inline decode+cleanup+topology only; acceptable parity with Django timing model.
