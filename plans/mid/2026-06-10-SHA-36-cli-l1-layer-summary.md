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

# Plan: CLI L1 layer summary and replay_core emission

## Source Issue

- Linear: SHA-36
- Status at planning time: Todo
- Priority: Mid

## Problem

CLI `RunStackUseCase` runs L1 reconstruction inline but never records `layer_01_reconstruction` in `solver_summary.layer_summaries` or `replay_core.jsonl`. Django path emits L1 via `build_layer01_post_summary_metrics`. CLI artifacts ship incomplete six-layer observability contract.

## Scope

- Add L1 summary to CLI `solver_summary.layer_summaries` using `build_layer01_post_summary_metrics`.
- Prepend L1 `layer_done` frame to `replay_core.jsonl` with monotonic `frame_index`.
- Emit verbose CLI `layer_done` for L1 when `--verbose`.
- Add regression tests for L1 presence in artifacts.

## Non-goals

- Refactoring L1 into separate `run_layer_01` runner unless required.
- Changing Django stack_runner behavior.
- L6 commit-validate (SHA-15).

## Implementation Plan

1. After inline reconstruction in `run_stack.py`, build `Layer01ReconstructionOutput(complete_map, capacity_envelope)`.
2. Call `build_layer01_post_summary_metrics`; prepend L1 `LayerSummaryRecord` before L2–L6.
3. Shift `replay_core` `frame_index` so L1 is first `layer_done` after header.
4. Extend `test_cli_run_artifact.py`: assert `layer_01_reconstruction` in `solver_summary.layer_summaries[0]` and first replay slug.
5. Run `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/shapez2_factory/test_replay_core_monotonic.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py`
- `tests/unit/shapez2_factory/test_cli_run_artifact.py`
- `tests/unit/shapez2_factory/test_replay_core_monotonic.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/shapez2_factory/test_replay_core_monotonic.py -v`
- build: `python manage.py check`
- manual verification: CLI run artifact; inspect `solver_summary` and `replay_core.jsonl` for L1 frame.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `frame_index` shift may affect replay compose tests; coordinate with SHA-64 artifact viewer path.
- `reconstruction_capacity.by_resource.authority` drift is Low follow-up.
