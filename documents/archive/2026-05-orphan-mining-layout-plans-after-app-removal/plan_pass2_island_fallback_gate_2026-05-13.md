# Pass2 island fallback gate reduction plan (2026-05-13)

## Background

Per `latest.ndjson`, STEP4 telemetry alias issues are resolved; remaining failures are Pass2 `fluid_pipe` placement rollbacks when STEP4 cannot reach an existing same-kind trunk goal.

Observed core pattern:

- Pass2 probe: `transport_cells_before_island_fallback` produces `final_goal_count`.
- STEP4 failure: `existing_trunk_goal_count > 0`, `reachable_existing_trunk_count == 0`.
- `exterior_margin_cell_count == 0`, `trunk_seed_candidate_count == 0`.
- Same nine placements recorded twice due to STEP4 re-entry.

## Scope

1. When Pass2 probe has `existing_layout_analysis` and canonical STEP4 goal is empty but only `transport_cells_before_island_fallback` created goals, reject placement commit.
2. Do not rename existing telemetry keys.
3. Add only `step4_reentry_index` for STEP4 re-entry interpretation.
4. Do not change Dijkstra behavior or STEP4 route cost.

## Minimal implementation

- `pass12_bundle_commit.py`
  - Inspect `goal_trace` immediately after Pass2 probe.
  - Reject when `fallback_goal_source == "transport_cells_before_island_fallback"`, `raw_goal_count == 0`, `trunk_reaching_probe_count == 0`, `exterior_margin_cell_count == 0`, and `existing_layout_analysis` is present.
- `solver_pipeline/recovery_orchestrator.py`, `solver_pipeline/step4.py`, `step4/step4_merge_routing.py`
  - First STEP4 passes `step4_reentry_index=0`, recovery re-entry passes `1`.
  - Attach same value to `step4_completed` and `step4_route_failure_detail`.

## Tests

- Pass2 fluid fixture unit test:
  - Preserve existing fallback-allowed case with `existing_layout_analysis=None`.
  - Reject when `existing_layout_analysis` present and only fallback goals without canonical goal.
- STEP4 telemetry unit test:
  - Confirm forced failure path exposes `step4_reentry_index` in failure detail.
