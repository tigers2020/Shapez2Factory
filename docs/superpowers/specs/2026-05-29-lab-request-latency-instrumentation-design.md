# Lab Request Latency Instrumentation (PR-13L) — Design Spec

**Date:** 2026-05-29  
**Status:** Approved  
**Sequence:** 13L (profiling-only; no payload or solver semantics changes)  
**Authority:** [`2026-05-29-replay-payload-network-optimization-design.md`](2026-05-29-replay-payload-network-optimization-design.md)

---

## Problem

After 13D-SSR, transfer sizes dropped (document ~569 kB, `lab-replay/` ~539 kB) but **Time** remains high (~8 s document, ~8.5 s `run-solver`, ~4.5 s `lab-replay`). Cause is unknown without server-side phase breakdown.

---

## Goal

Feature-flagged **structured JSONL** latency logs for three HTTP paths:

| `request_kind` | Handler |
|----------------|---------|
| `project_page` | `GET …/p/<slug>/` |
| `run_solver` | `POST …/run-solver/` |
| `lab_replay_get` | `GET …/solver-runs/<id>/lab-replay/` |

---

## Non-goals

- Payload contract changes (13D/13E/13G)
- Compose defer, delta, caching
- Solver or replay **input** use of perf data
- stdlib logging to stderr (JSONL file only, like `boundary_jsonl`)

---

## Feature flag

```python
# config/settings.py — default off
ASTEROID_LAB_PERF_TRACE = os.environ.get("ASTEROID_LAB_PERF_TRACE", "0") in ("1", "true", "yes")
```

Register in [`documents/ai/manuals/environment.md`](../../../documents/ai/manuals/environment.md).

---

## Output

Path: `var/log/asteroid_lab_perf/lab_perf.jsonl`

Example line:

```json
{
  "event": "asteroid_lab_perf",
  "ts": "2026-05-29T12:00:00Z",
  "request_kind": "project_page",
  "project_slug": "rttp-core-recovery-test-map",
  "total_ms": 8021.4,
  "lab_page_context_ms": 7980.0,
  "solver_runs_for_lab_project_ms": 12.0,
  "build_lab_replay_frames_for_project_ms": 6902.1,
  "frame_count": 86,
  "html_bytes": 569000
}
```

---

## Phase keys (minimum)

### `project_page`

- `lab_page_context_ms`
- `solver_runs_for_lab_project_ms`
- `get_latest_lab_replay_track_ms`
- `build_lab_replay_frames_for_project_ms`
- `html_bytes`, `frame_count`

### `run_solver`

- `game_data_snapshot_ms`
- `solver_runtime_ms`
- `layer_01_ms` … `layer_04_ms` (from layer02 when active)
- `replay_artifact_build_ms`, `db_persist_ms`, `replay_compose_once_ms` (13C2-lite; replaces `post_replay_compose_ms`)
- `lab_replay_cache_frames_bytes`, `lab_replay_manifest_summary_bytes` (on POST success)
- `response_json_build_ms`, `payload_bytes`, `solver_run_id`

### `lab_replay_get`

- `solver_run_lookup_ms`
- `replay_cache_load_ms`, `replay_cache_json_decode_ms`, `replay_cache_miss_compose_ms` (13C2-lite; `replay_compose_ms` on miss/fallback only)
- `lab_replay_cache_frames_bytes`, `lab_replay_manifest_summary_bytes`
- `json_response_build_ms`
- `frame_count`, `total_full_map_cells`, `payload_bytes`, `response_bytes`

See also [`2026-05-29-replay-compose-defer-artifact-reuse-design.md`](2026-05-29-replay-compose-defer-artifact-reuse-design.md) §4.9.

### `project_page` (lazy SSR, 13C2-lite)

- `replay_cache_json_decode_ms`, `lab_replay_manifest_summary_bytes` (cache-hit; KB-scale)
- `replay_cache_miss_compose_ms` (Policy A miss only)

### `project_page` (13F TTFB breakdown — extends 13L)

See [`2026-05-29-lab-page-ttfb-breakdown-shell-only-design.md`](2026-05-29-lab-page-ttfb-breakdown-shell-only-design.md) §6 for `template_render_ms`, SQL meta, `json_script_bytes_by_id`, runs/track sub-phases, and cache-hit label split.

---

## Invariants

```text
Perf trace is output-only.
No solver / replay algorithm reads perf JSONL.
Default off: zero file writes, no timing overhead beyond branch checks.
```

---

## Tests

- `ASTEROID_LAB_PERF_TRACE=False` → no log file
- `ASTEROID_LAB_PERF_TRACE=True` → one JSONL line with `event`, `request_kind`, phase keys

---

## Next steps (after profiling)

Interpret logs → choose one:

- High `build_lab_replay_frames_for_project_ms` on `project_page` → compose defer
- High `json_response_build_ms` / `total_full_map_cells` on `lab_replay_get` → 13E delta
- High `layer_0N_ms` on `run_solver` → layer runtime optimization
