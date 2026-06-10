# Lab-Replay First Compose Profiling Report (Issue #176)

**Date:** 2026-06-11  
**Context:** PR #175 merged. `status/` hot path fixed (~50.38s → ~236ms). C2 not triggered.  
**Observed:** first `GET lab-replay/` ~45.45s (Run #464, 37 frames, ~237 kB).  
**Issue:** https://github.com/tigers2020/Shapez2Factory/issues/176

---

## Scope (fixed)

Investigate only:

- `build_lab_replay_frames_for_project`
- `compose_lab_replay_frames_from_artifact_run`
- `build_solver_runtime_replay_frames_from_artifact_run`
- `compose_replay_timeline`
- projection enrichments (terrain / pattern / connector)
- cache miss vs cache hit on `lab-replay/`

Forbidden: move compose to `status/`, reintroduce status cache warm, replay as solver input, UI/layer assembly authority, SSE/progress.jsonl/live replay.

---

## 1. Existing `perf_span` coverage

### `GET lab-replay/` (`public_pages.asteroid_miner_layout_project_solver_run_lab_replay`)

Enabled when `ASTEROID_LAB_PERF_TRACE=1` → `var/log/asteroid_lab_perf/lab_perf.jsonl`.

| Span / meta | Present | Notes |
|-------------|---------|-------|
| `solver_run_lookup_ms` | ✓ | ORM lookup |
| `replay_cache_load_ms` | ✓ | `load_composed_frames_for_run_id` + summary |
| `replay_cache_json_decode_ms` | ✓ | manual `record_perf_ms` |
| `replay_cache_miss_compose_ms` | ✓ | wraps entire `build_lab_replay_frames_for_project` + `persist_composed_replay_for_run_id` |
| `json_response_build_ms` | ✓ | `JsonResponse` + payload size meta |
| `frame_count`, `payload_bytes`, `response_bytes` | ✓ | meta |
| **Inside compose chain** | ✗ | single opaque bucket |

### Gap

`replay_cache_miss_compose_ms` is one ~45s bucket. It does **not** split artifact load, layer re-execution, timeline merge, enrichments, or cache persist.

`build_lab_replay_frames_for_project` has **no** `perf_span` calls.

---

## 2. Compose call chain (cache miss)

```text
GET lab-replay/
├─ replay_cache_load_ms          → miss (C1 removed status warm)
├─ replay_cache_miss_compose_ms
│  ├─ build_lab_replay_frames_for_project
│  │  ├─ _lab_timeline_frames_for_project
│  │  ├─ compose_lab_replay_frames_from_artifact_run
│  │  │  ├─ read manifest + complete_map + replay_core paths
│  │  │  ├─ build_solver_runtime_replay_frames_from_artifact_run  ← HEAVY
│  │  │  │     re-executes L2 → L3 → L4 → L5 on artifact inputs
│  │  │  └─ fallback: iter_replay_core_frames + map_view per record
│  │  ├─ compose_replay_timeline (lab + runtime frames)
│  │  ├─ enrich_lab_timeline_frames_with_terrain_rim
│  │  ├─ enrich_lab_timeline_frames_with_pattern_bundle_highlights
│  │  └─ enrich_lab_timeline_frames_with_exterior_connector_plan
│  └─ persist_composed_replay_for_run_id
└─ json_response_build_ms
```

### Critical code path

`compose_lab_replay_frames_from_artifact_run` **prefers** runtime recompose:

```python
runtime_frames = build_solver_runtime_replay_frames_from_artifact_run(run)
if runtime_frames and lab_replay_frames_are_renderable(runtime_frames):
    return runtime_frames  # early return — replay_core path skipped
```

`build_solver_runtime_replay_frames_from_artifact_run` docstring (normative in code):

```text
Re-execute L2→L3→L4→L5 on artifact inputs and emit overlay-capable runtime replay frames.
```

Files:

- `django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py`
- `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py`
- `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`

**Inference (high confidence):** ~45s first `lab-replay/` is dominated by **solver layer re-execution during viewer compose**, not JSONL tail parse alone. C1 moved this cost from `status/` to `lab-replay/` intentionally.

`replay_core.jsonl` fallback runs only when runtime recompose fails or is not renderable.

---

## 3. Cache miss vs hit (expected)

| Case | Path | Expected |
|------|------|----------|
| First `lab-replay/` after run | cache miss → full compose + persist | slow (~45s observed) |
| Second `lab-replay/` same run | `load_composed_frames_for_run_id` hit | fast (ms–low s) |
| After cache purge / stale thin L3 | miss again | slow |

`persist_composed_replay_for_run_id` runs at end of first miss inside `replay_cache_miss_compose_ms`.

**Manual verification (recommended):**

1. Run solver → first `lab-replay/` (note Network time).
2. Refresh / second `lab-replay/` same `run_id` (should be cache hit).
3. Optional: `ASTEROID_LAB_PERF_TRACE=1` and compare JSONL lines for `replay_cache_miss_compose_ms` vs absent on hit.

---

## 4. Frame / payload attributes (Run #464 reference)

From browser capture + UI:

| Field | Value |
|-------|-------|
| `frame_count` | 37 |
| UI timeline | 37 / 37 |
| first `lab-replay/` payload | ~237 kB |
| before C1 first `lab-replay/` | ~255 kB, ~892 ms (cache may have been warm from status ingest) |

Record on next traced run via perf meta: `replay_core.jsonl` bytes, `event_count`, cache blob bytes, `serialization time`.

---

## 5. Dominant bottleneck classification

| Option | Verdict | Evidence |
|--------|---------|----------|
| A) JSONL parse | Unlikely primary | Runtime recompose path returns before core iteration when renderable |
| **B) timeline compose** | **Partial** | `compose_replay_timeline` + serialization — smaller than layer stack |
| **C) terrain/rim projection** | Secondary | `enrich_lab_timeline_frames_with_terrain_rim` after compose |
| D) transport projection | Secondary | connector enrichment |
| E) cache persist | Minor vs 45s | DB write inside same miss span |
| F) response serialization | Minor–moderate | `json_response_build_ms` on 237 kB |
| G) frontend canvas | Out of HTTP scope | 45s is server Network time |

**Dominant bottleneck (attribution):**

```text
B′) build_solver_runtime_replay_frames_from_artifact_run
    = L2 + L3 + L4 + L5 re-execution on artifact inputs (~tens of seconds)
```

Secondary: enrichments + JSON response build.  
Not: status path (fixed in #175).

---

## 6. Instrumentation PR (in progress)

Branch: `pr-176-lab-replay-compose-instrumentation`

Spans added under `ASTEROID_LAB_PERF_TRACE=1` (no behavior change). See
`tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py` for phase names.

## 7. Recommended next steps (after instrumentation merge)

### Step A — Measurement pass

Add `perf_span` inside `build_lab_replay_frames_for_project` and `compose_lab_replay_frames_from_artifact_run`:

```text
compose_artifact_runtime_replay_ms
compose_replay_core_fallback_ms
compose_replay_timeline_ms
enrich_terrain_rim_ms
enrich_pattern_bundle_ms
enrich_exterior_connector_ms
replay_cache_persist_ms
```

Per-layer spans inside `build_solver_runtime_replay_frames_from_artifact_run` (optional): `layer02_ms` … `layer05_ms`.

Re-run with `ASTEROID_LAB_PERF_TRACE=1` on Run #464-class artifact. Confirm B′ split.

### Step B — One optimization PR (after measurement confirms B′)

**Recommended direction (contract-safe):**

Prefer **replay_core + complete_map** viewer path when `replay_core.jsonl` and `layer01_complete_map` exist and validate — **do not re-run L2–L5** unless a documented renderability gap requires it.

Rationale:

- BA-4: core is deterministic output; Django enriches only.
- Current code re-runs algorithms for overlay-capable frames even when finalized artifact already contains `replay_core`.
- Aligns with #175: compose stays on `lab-replay/`, but work should be **projection/enrichment**, not second solver pass.

Alternative (if re-execution is contract-required): optimize/cache layer outputs per `run_key` — larger scope; needs grill/ADR.

**Do not:** move compose back to `status/`.

---

## 7. Enable tracing

```powershell
$env:ASTEROID_LAB_PERF_TRACE = "1"
python manage.py runserver
# trigger lab-replay GET
Get-Content var/log/asteroid_lab_perf/lab_perf.jsonl -Tail 5
```

Look for `request_kind: lab_replay_get` and phase keys.

---

## Conclusion

| Item | Status |
|------|--------|
| C2 | Still not triggered |
| #176 scope | Investigation — this report |
| Dominant bottleneck | **L2–L5 re-execution in viewer compose** (inferred; confirm with spans) |
| Next PR | Instrumentation, then bounded “prefer replay_core path” optimization |
