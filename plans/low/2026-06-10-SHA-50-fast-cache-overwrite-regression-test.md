---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: Low
labels:
  - bug
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Add regression test for fast-cache column reset on inspection overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Low

## Problem

No unit test asserts that `resolve_inspection_solver_run(..., overwrite=True)` clears stale fast-cache columns and resets status after a prior completed solver state. Existing `test_build_initial_replay_overwrite_keeps_run_key` only checks `run_key` / `solver_run_id` stability.

## Scope

Add regression test(s) covering seeded completed `SolverRun` with populated fast-cache → overwrite → empty cache and pending status. Extend existing overwrite test or add focused test in `test_experiment_service.py`.

## Non-goals

- Changing production overwrite behavior (covered by High/Mid plans).
- Testing SHA-37/SHA-38 read-path validity.
- Testing no-overwrite idempotent short-circuit.

## Implementation Plan

1. Add `test_resolve_inspection_solver_run_overwrite_clears_fast_cache` in `tests/unit/asteroid_lab/test_experiment_service.py` (new file section if file exists, else create imports mirroring sibling tests).
2. Arrange: create `AsteroidProject`, seed `SolverRun` with `run_key="inspection-main"`, `status=SolverRun.RunStatus.COMPLETED`, `algorithm_label="old_label"`, `solver_summary_json={"stale": True}`, `lab_replay_payload_json={"composed_frames": [{"frame_index": 0}]}`, non-empty `lab_replay_manifest_summary_json` and `solver_runtime_replay_frames_json`, plus matching `ReplayTrack` with optional stale frames.
3. Act: call `resolve_inspection_solver_run(project_id, run_key=..., algorithm_label="inspection", config={"seed": "new"}, overwrite=True)`.
4. Assert on refreshed ORM row:
   - `status == SolverRun.RunStatus.PENDING`
   - `algorithm_label == "inspection"`
   - `config_json == {"seed": "new"}`
   - `solver_summary_json == {}`
   - `lab_replay_payload_json` has empty `composed_frames` (or `{}` per `empty_solver_run_fast_cache_kwargs`)
   - `lab_replay_manifest_summary_json["frame_count"] == 0`
   - `solver_runtime_replay_frames_json == []`
   - `artifact_root == ""` and `started_at`/`finished_at` are `None`
5. Optionally extend `test_build_initial_replay_overwrite_keeps_run_key` in `test_replay_pipeline_service.py`: after first build, manually poison fast-cache on the run, call overwrite rebuild, assert cache cleared while `solver_run_id` unchanged.
6. Run: `pytest tests/unit/asteroid_lab/test_experiment_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py -v -k "overwrite or fast_cache"`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_experiment_service.py` (primary)
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py` (optional extension of `test_build_initial_replay_overwrite_keeps_run_key`)
- `tests/unit/asteroid_lab/test_solver_run_fast_cache.py` (reference for empty-cache helpers)

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/`
- typecheck: N/A for test-only change
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py::test_resolve_inspection_solver_run_overwrite_clears_fast_cache -v` (expect FAIL before fix, PASS after)
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Test must run against implementation from High/Mid plans; write test first (TDD) or alongside fix in same PR.
- Confirm `test_experiment_service.py` exists or create with standard `@pytest.mark.django_db` fixtures used by sibling asteroid_lab tests.
