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
- Status at planning time: Todo
- Priority: Mid

## Problem

The CLI-first `RunStackUseCase` runs Layer 01 reconstruction inline but never records `layer_01_reconstruction` in `solver_summary.layer_summaries` or `replay_core.jsonl`, unlike Django's `run_full_from_cleanup_recon`.

## Scope

- Add L1 summary record to CLI `solver_summary.layer_summaries` via `build_layer01_post_summary_metrics`.
- Prepend L1 `layer_done` frame to `replay_core.jsonl` (preserve monotonic `frame_index`).
- Emit verbose CLI `layer_done` line for L1 when `--verbose` is set.
- Add regression tests for L1 presence in artifacts.

## Non-goals

- Refactoring L1 into separate `run_layer_01` runner unless required.
- Changing Django stack_runner behavior.
- Fixing `reconstruction_capacity.by_resource.authority` drift.
- Implementing L6 commit-validate (SHA-15).

## Implementation Plan

1. Read `run_stack.py` L1 inline reconstruction block and `layer_summaries` / `replay_core_lines` assembly.
2. After reconstruction, build `Layer01ReconstructionOutput(complete_map, capacity_envelope)`.
3. Call `build_layer01_post_summary_metrics` from `post_summary_metrics.py`; prepend L1 `LayerSummaryRecord` before L2–L6.
4. Shift `replay_core` `frame_index` so L1 is first `layer_done` after header.
5. Extend `test_cli_run_artifact.py` and `test_replay_core_monotonic.py` to assert L1 in summary and replay.
6. Add verbose output test for L1 `layer_done` line when `--verbose`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/layer_behavior_catalog.py`
- `tests/unit/shapez2_factory/test_cli_run_artifact.py`
- `tests/unit/shapez2_factory/test_replay_core_monotonic.py`

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/`
- typecheck: `mypy django_apps config src`
- tests: CLI run artifact + replay core tests
- build: N/A
- manual verification: CLI run artifact JSON has `layer_summaries[0].slug == layer_01_reconstruction`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Frame index shift may affect consumers assuming L2-first — check replay compose tests (SHA-21).
