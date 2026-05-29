# PR-13F — Lab Page TTFB Breakdown + Shell-Only SSR (C-lite) — Design Spec

**Date:** 2026-05-29  
**Status:** Approved (2026-05-29, minor amendments: Approach 1, runs limit 10, no run-count TTFB shortcut)  
**Sequence:** 13F (extends 13L; follows 13C2-lite compose defer + 13D lazy SSR)  
**Official approach:** **Approach 1 — Fix + explain**

**Depends on:** [13L lab request latency instrumentation](2026-05-29-lab-request-latency-instrumentation-design.md) · [13C2-lite compose defer](2026-05-29-replay-compose-defer-artifact-reuse-design.md) · [13D SSR slim](2026-05-29-replay-payload-network-optimization-design.md)  
**Implementation plan:** [`docs/superpowers/plans/2026-05-29-lab-page-ttfb-breakdown-shell-only.md`](../plans/2026-05-29-lab-page-ttfb-breakdown-shell-only.md)

> **13F makes project page TTFB explainable in one request log and removes provably unnecessary SSR-heavy reads. It is not a full replay payload optimization PR, not a UX redesign, and does not hard-gate `<700 ms` closure in this PR.**

---

## Primary goal

```text
13F primary goal:
Make project page TTFB explainable in one request log,
and remove known SSR-heavy reads that are provably unnecessary for initial page shell rendering.

13F is not a full replay payload optimization PR.
13F is not a full UX redesign PR.
13F does not promise final <700 ms closure, but it must make <700 ms mechanically plausible.
```

**Delivery (Approach 1 — Fix + explain):**

```text
13L instrumentation extension (project_page TTFB breakdown)
+ solver_runs partial-read (no full config_json materialization)
+ replay track shell lookup (no frame prefetch on page GET)
```

---

## 1. Problem

After 13D-SSR and 13C2-lite, **document size** is acceptable (~369 kB vs ~16 MB inline replay) but **`project_page` TTFB remains ~3.2–4.0 s** on cache-warm local runs. Network **Waiting/TTFB** aligns with server `lab_perf.jsonl` `total_ms`, so the bottleneck is **SSR / DB materialization / template serialization**, not browser download of a 369 kB HTML document.

A single coarse `lab_page_context_ms` span (13L) is insufficient to choose the next optimization (runs JSON, SQL, template render, or residual compose).

---

## 2. Evidence

### Observed (representative, post–13D/13C2)

| Signal | Value | Interpretation |
|--------|-------|----------------|
| `project_page` Network time | ~3.23 s | Server-bound TTFB |
| `lab_perf.jsonl` `total_ms` | ~3,203 ms | Matches Network Waiting |
| `html_bytes` | ~369 kB | Payload slimming succeeded |
| “cache-hit” (informal) | replay manifest cache | Does **not** imply page shell or DB cache |

### Code-backed suspects (pre-13F)

| Location | Pattern | Risk if composed replay cached on run |
|----------|---------|--------------------------------------|
| `solver_run_lab_summary.lab_run_summary_from_orm` | `dict(run.config_json)` per run | Loads **entire** `config_json` including `lab_replay_composed_frames` |
| `solver_runs_for_lab_project` | Up to **10** ORM rows → full config each | **High** — N × large JSON decode |
| `get_latest_lab_replay_track_for_project` | `prefetch_related("frames")` | **High** — all `ReplayFrame` rows on page GET |
| `lab_page_context` lazy cache-hit | Manifest from summary; no compose | **Low** on cache-hit (13C2-lite) |
| Template `runs\|json_script` | Full run DTOs in HTML | **Medium** — serialize cost; not fixed by row-count reduction |

---

## 3. Current suspects (ranked)

1. **`solver_runs_for_lab_project` full `config_json` materialization** (even when UI only needs `solver_summary`-derived fields).
2. **`get_latest_lab_replay_track_for_project` frame prefetch** (page shell only needs track id/key/count).
3. **Template / `json_script` serialization** of `runs`, manifest, sprite map (size unknown without per-script bytes).
4. **Residual replay compose** on manifest cache-miss (Policy A — acceptable; must remain absent on cache-hit).
5. **SQL volume / slow queries** (unknown without `sql_*` meta).

13F addresses **(1)** and **(2)** directly and adds instrumentation for **(3)–(5)**.

---

## 4. Page shell contract

**Handler:** `GET …/p/<slug>/` → `asteroid_miner_layout_project` → `lab_page_context` + template render.

### 4.1 MUST provide on initial HTML (shell)

| Area | Allowed | Notes |
|------|---------|--------|
| Project | slug, blueprint code, map input code | Existing |
| Runs panel | Up to **`limit=10`** run list DTOs (wire unchanged; see §7.1) | Same fields JS expects today (`layer_summaries`, etc.) |
| Replay shell | Lazy manifest handle, `frame_count`, preview stub, `fetch_url` | No full `frames[]` in HTML (13D) |
| Track shell | `track_id`, `track_key`, `frame_count` | From shell lookup only |
| URLs | Lazy replay fetch URL in manifest | Client loads frames after paint |

### 4.2 MUST NOT on page GET (shell)

| Forbidden | Rationale |
|-----------|-----------|
| `build_lab_replay_frames_for_project()` on **manifest cache-hit** | 13C2-lite invariant |
| Full `SolverRun.config_json` materialization for runs list | Composed frames blob must not be read for panel |
| `prefetch_related("frames")` / `ReplayFrame` row load for page shell | Frames belong on lazy replay GET only |
| Reading `lab_replay_composed_frames` for SSR | GET/lazy endpoint only |

### 4.3 Runs list limit (fixed)

```text
runs list limit = 10  (current default; unchanged in 13F)
```

**Rationale:** 13F performance gains must come from **eliminating full `config_json` per row**, not from reducing displayed run count. Shrinking the limit (e.g. to 5) would mix UX change with TTFB work and obscure root-cause analysis.

### 4.4 Cache-hit semantics (separate labels)

| Meta key | Meaning in 13F |
|----------|----------------|
| `replay_manifest_cache_hit` | `ASTEROID_LAB_REPLAY_PAYLOAD_MODE=lazy` and `is_cache_summary_valid(manifest_summary)` |
| `page_shell_cache_hit` | Always **`false`** in 13F (schema reserved; implementation in follow-up) |

Do not use a single ambiguous “cache-hit” label in docs or logs.

---

## 5. Forbidden SSR reads (enforcement)

### 5.1 Runs list — partial read only

**Forbidden on `project_page` path:**

```python
# Anti-pattern: full JSON column materialization per run
config = dict(run.config_json or {})
```

**Allowed:**

```text
ORM values()/annotate query returning:
  pk, status, created_at
  KeyTransform(SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY, "config_json")  # solver_summary only
```

Then build the existing wire DTO via `lab_run_summary_from_solver_summary(...)`.

**Wire contract:** `lab-runs-data` JSON shape **unchanged** (including `layer_summaries`). This is **not** a new slim DTO v2; it is the same list item built from a smaller DB read.

**Conceptual separation:**

```text
SolverRunListItem wire payload != full SolverRun.config_json
```

### 5.2 Replay track — shell lookup only

**Forbidden on page shell path:**

```python
prefetch_related("frames")  # or any ReplayFrame queryset evaluation for page GET
```

**Required:** `get_latest_lab_replay_track_shell_for_project(project_id)` (new) returning only:

```text
id (track pk)
track_key
frame_count (annotate Count("frames"))
```

`lab_page_context` uses the shell helper; `get_latest_lab_replay_track_for_project` remains for compose / lab-replay GET paths that need frame rows.

### 5.3 JSON blob keys — page GET deny list

Page GET MUST NOT read or deserialize these `config_json` keys:

```text
lab_replay_composed_frames
solver_runtime_replay_frames   # unless a future shell requirement appears (none today)
```

Allowed key for runs panel: `solver_summary` only (via partial read).

---

## 6. Instrumentation contract (13L extension)

**Flag:** existing `ASTEROID_LAB_PERF_TRACE=1` ([13L](2026-05-29-lab-request-latency-instrumentation-design.md)).  
**Output:** `var/log/asteroid_lab_perf/lab_perf.jsonl` — one line per request.

### 6.1 Scope in 13F

Extend **`request_kind=project_page`** only. Do not change `run_solver` / `lab_replay_get` phase sets except cross-references in docs.

### 6.2 Additional phase keys (`project_page`)

| Phase key | Description |
|-----------|-------------|
| `template_render_ms` | `render()` only (excludes `lab_page_context_ms`) |
| `runs_query_ms` | DB fetch for runs list (partial read) |
| `runs_materialize_ms` | DTO build from `solver_summary` rows |
| `track_lookup_ms` | Shell track query |

Existing 13L / 13C2 keys remain: `lab_page_context_ms`, `solver_runs_for_lab_project_ms` (may alias or subdivide — implementation may nest `runs_*` inside legacy span for backward-compatible logs), `get_latest_lab_replay_track_ms` → prefer **`track_lookup_ms`** on shell path, `replay_cache_json_decode_ms`, `replay_cache_miss_compose_ms`, `build_lab_replay_frames_for_project_ms` (absent on cache-hit).

### 6.3 Additional meta keys (`project_page`)

| Meta key | Type | Description |
|----------|------|-------------|
| `sql_query_count` | int | Queries during request (trace-active only) |
| `sql_total_ms` | float | Sum of DB time in wrapper |
| `largest_query_ms` | float | Slowest single query |
| `largest_json_bytes_read` | int | Heuristic: max result size where measurable (optional; document method in plan) |
| `json_script_bytes_total` | int | Sum of measured script payloads |
| `json_script_bytes_by_id` | object | Map script id → UTF-8 bytes (e.g. `lab-runs-data`, `lab-replay-manifest-data`, …) |
| `runs_json_bytes` | int | `serialized_json_utf8_bytes(runs)` |
| `track_frames_loaded_count` | int | **Must be 0** on page GET after remediation |
| `track_frames_prefetched` | bool | **Must be false** on page GET |
| `replay_manifest_cache_hit` | bool | See §4.4 |
| `page_shell_cache_hit` | bool | **false** in 13F |
| `html_bytes`, `frame_count`, `has_replay_frames` | existing | unchanged |

**Script ids to measure** (minimum):

```text
lab-cell-overlay-matrix-data
lab-runs-data
lab-ui-initial-state
lab-replay-frames-data
lab-replay-track-metrics-data
lab-replay-manifest-data
lab-identifier-sprite-paths-data
```

### 6.4 Example log line (illustrative)

```json
{
  "event": "asteroid_lab_perf",
  "ts": "2026-05-29T18:00:00Z",
  "request_kind": "project_page",
  "project_slug": "rttp-core-recovery-test-map",
  "total_ms": 820.5,
  "lab_page_context_ms": 610.2,
  "template_render_ms": 45.1,
  "runs_query_ms": 28.0,
  "runs_materialize_ms": 120.4,
  "runs_json_bytes": 185000,
  "track_lookup_ms": 6.2,
  "track_frames_loaded_count": 0,
  "track_frames_prefetched": false,
  "replay_cache_json_decode_ms": 2.1,
  "replay_manifest_cache_hit": true,
  "page_shell_cache_hit": false,
  "sql_query_count": 14,
  "sql_total_ms": 95.0,
  "largest_query_ms": 40.2,
  "json_script_bytes_total": 240000,
  "json_script_bytes_by_id": {
    "lab-runs-data": 180000,
    "lab-replay-manifest-data": 1200
  },
  "html_bytes": 369000,
  "frame_count": 86
}
```

### 6.5 Invariants

```text
Perf trace is output-only.
No solver / replay algorithm reads perf JSONL.
Default off: no file writes; SQL wrapper only when trace active.
```

**Hard requirement when soft target missed:** if `total_ms` ≥ 1000 on cache-hit local run, the log MUST still expose at least one phase or meta field **> 250 ms** so follow-up (13G/13H) is actionable.

### 6.6 Implementation notes (non-normative)

- SQL: Django 5.2+ `connection.execute_wrapper` for the active request collector.
- `json_script_bytes_by_id`: measure template-bound context values with `serialized_json_utf8_bytes` immediately before `render()`.

---

## 7. Minimal remediation contract

### 7.1 `solver_runs_for_lab_project` (partial read)

- Keep **`limit=10`** (default parameter unchanged).
- Replace ORM full-model iteration with `.values(...)` + `KeyTransform` on `solver_summary` only.
- Preserve `lab_run_summary_from_solver_summary` output shape for `lab-runs-data`.

### 7.2 `get_latest_lab_replay_track_shell_for_project` (new)

- Add in `lab_replay_timeline_payload.py` (or adjacent service module).
- Use `annotate(_frame_count=Count("frames"))`; **no** `prefetch_related`.
- `asteroid_lab_page_context` calls shell helper only.

### 7.3 `asteroid_miner_layout_project` / `public_pages.py`

- Split `perf_span`: `lab_page_context_ms` vs `template_render_ms`.
- Emit `json_script_bytes_*` and SQL meta before/after render as specified.

### 7.4 13C2-lite regression (no behavior change)

- Lazy manifest **cache-hit:** no `build_lab_replay_frames_for_project_ms` in log; no compose call.
- Cache-miss: Policy A compose-once + backfill unchanged.

---

## 8. Acceptance criteria

### 8.1 Instrumentation

- [ ] `project_page` log includes `sql_query_count`, `sql_total_ms`, `template_render_ms`
- [ ] `project_page` log includes `json_script_bytes_total` and `json_script_bytes_by_id`
- [ ] `replay_manifest_cache_hit` and `page_shell_cache_hit` are separate booleans
- [ ] If soft target missed, log identifies a remaining phase/meta **> 250 ms**

### 8.2 Shell-only remediation

- [ ] Runs list uses partial read; no full `config_json` materialization on page path
- [ ] Page GET does not prefetch replay frames; `track_frames_loaded_count == 0`, `track_frames_prefetched == false`
- [ ] Page GET does not call replay compose on manifest cache-hit (13C2-lite)
- [ ] **Runs list limit remains current default 10; 13F must not rely on reducing displayed run count for TTFB improvement**

### 8.3 Payload / HTML

- [ ] `html_bytes` remains **< 500 kB** on reference project (no regression vs ~369 kB baseline)

### 8.4 Tests (regression)

- [ ] `test_solver_runs_list_uses_partial_config_read` — sentinel/large `lab_replay_composed_frames` not loaded on page path
- [ ] `test_project_page_shell_does_not_prefetch_replay_frames`
- [ ] `test_project_page_lazy_cache_hit_skips_compose` (13C2-lite; existing or extended)
- [ ] `test_lab_perf_trace_project_page_emits_13f_keys`

### 8.5 Performance gates

| Gate | Criterion |
|------|-----------|
| **Soft target** | `project_page` `total_ms` **< 1000** on cache-hit local run (manifest warm, `ASTEROID_LAB_REPLAY_PAYLOAD_MODE=lazy`) |
| **Hard requirement** | Explainability: dominant remaining cost visible in JSONL if soft target missed |
| **Final product goal (not 13F hard gate)** | **< 700 ms** cache-hit page shell — follow-up 13G/13H |

---

## 9. Non-goals

```text
gzip / compression tuning (13G)
delta replay format (13E)
full replay frame schema changes
UI layout redesign
page shell response caching implementation (page_shell_cache_hit stays false)
solver / runtime algorithm changes
Lazy runs API (13H — follow-up only)
Runs panel slim DTO v2 (13H — only if runs_json_bytes still dominant)
Reducing runs list limit below 10 for performance
```

---

## 10. Follow-up decisions (post-13F log)

Interpret one warm `project_page` line:

| Dominant signal | Likely follow-up |
|-----------------|------------------|
| `runs_json_bytes` still large | **13H:** deferred runs API **or** runs panel slim DTO v2 |
| `json_script_bytes_by_id["lab-replay-manifest-data"]` large | Slim `preview_frame` in manifest summary |
| `template_render_ms` high | Template split / defer non-critical scripts |
| `sql_*` high | Query/index/partial-read expansion |
| `replay_cache_miss_compose_ms` on repeat loads | Cache persistence / warm workflow docs |
| `total_ms` still > 1000 after 13F fixes | **13G** compression + above |

**13H (explicitly out of 13F):** `GET /lab-runs/?project_id=…` or equivalent lazy runs panel — do not implement in 13F.

---

## Approaches considered

| Approach | Summary | 13F decision |
|----------|---------|--------------|
| **1 — Fix + explain** | 13L extension + partial runs read + track shell lookup | **Selected (official)** |
| 2 — Instrument-first | Metrics only; fixes in 13G | Rejected — suspects already code-proven |
| 3 — Lazy runs API | Move `lab-runs-data` off HTML | **Deferred to 13H** |

---

## File touch list (implementation planning)

| File | Change |
|------|--------|
| `django_apps/asteroid_lab/observability/lab_perf_trace.py` | SQL wrapper helper; optional nested meta |
| `django_apps/asteroid_lab/services/solver_run_lab_summary.py` | Partial-read runs query |
| `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py` | Shell track lookup |
| `django_apps/web/services/asteroid_lab_page_context.py` | Shell track; cache-hit meta |
| `django_apps/web/views/public_pages.py` | `template_render_ms`, json_script bytes |
| `tests/unit/asteroid_lab/test_lab_perf_trace.py` | 13F keys |
| `tests/integration/web/test_lab_page_shell_perf.py` (new) | Partial read + no prefetch |
| `docs/superpowers/specs/2026-05-29-lab-request-latency-instrumentation-design.md` | Cross-ref §6 `project_page` 13F keys |

---

## Spec self-review (2026-05-29)

| Check | Result |
|-------|--------|
| Placeholder scan | No TBD/TODO in normative sections |
| Internal consistency | Approach 1 = instrumentation + two remediations; 13H deferred; limit 10 fixed |
| Scope | Single PR-sized; no lazy API in 13F |
| Ambiguity | `page_shell_cache_hit` false in 13F; run-count AC explicit; cache labels split |
