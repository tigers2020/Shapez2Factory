# PR-13C2-lite — Replay Compose Defer + Persisted Artifact Reuse Design

**Date:** 2026-05-29  
**Status:** Approved (2026-05-29, blocking amendments §4.7–4.10 incorporated). **Implementation complete locally (2026-05-29):** lazy SSR and lab-replay GET reuse persisted composed replay cache on cache-hit paths; GET payload shape unchanged; 13E/13G remain follow-up work.  
**Sequence label:** `13C2-lite` / `13F-lite` (compose defer). **Not** PR-13F cell interning ([network optimization § PR sequence](2026-05-29-replay-payload-network-optimization-design.md)).

> **This PR removes repeated full replay composition. It does not change replay payload shape.**

**Depends on:** PR-13D-SSR (manifest-only document), PR-13L (latency JSONL instrumentation)  
**Related:** [13C lazy-load](2026-05-30-lab-replay-lazy-load-post-slimming-design.md) · [network optimization umbrella](2026-05-29-replay-payload-network-optimization-design.md) · [`documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md`](../../../documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md)

**Out of scope:** PR-13E delta encoding · PR-13G gzip · PR-13F cell interning · solver placement/routing · UI timeline controller rewrite · `solver_runs_for_lab_project` query optimization (~2.3s, separate follow-up)

---

## 1. Problem

After 13D+13L merge, **document transfer** is fixed (`html_bytes` ~366 KB vs ~16 MB), but **server latency** remains dominated by the same full timeline composition repeated on three request paths.

### Observed (2026-05-29, `rttp-core-recovery-test-map`, 88 frames)

| `request_kind` | Dominant phase | `total_ms` | Notes |
|----------------|----------------|------------|--------|
| `project_page` | `build_lab_replay_frames_for_project_ms` | ~4,641 | Still called in lazy SSR (13D only removed embed) |
| `project_page` | `solver_runs_for_lab_project_ms` | ~2,328 | Separate DB/summary cost |
| `project_page` | `html_bytes` | 366,374 | 13D success |
| `run_solver` | `post_replay_compose_ms` | ~4,031 | After `replay_artifact_build_ms` (~578) |
| `run_solver` | `solver_runtime_ms` | ~8,047 | Includes compose |
| `lab_replay_get` | `replay_compose_ms` | ~4,000 | `response_bytes` ~15.8 MB unchanged |

```text
Same full compose path today:
  lab_page_context (lazy)  → build_lab_replay_frames_for_project()
  run_layer02 POST finish  → build_lab_replay_frames_for_project(solver_run_id=…)
  lab_replay GET           → build_lab_replay_frames_for_project(solver_run_id=…)
```

### What already exists (inventory)

| Storage | Key / location | Contents | Used by |
|---------|----------------|----------|---------|
| Partial runtime segment | `SolverRun.config_json["solver_runtime_replay_frames"]` | Assembler output for L2–L4 wire | `_solver_runtime_timeline_frames_for_run` inside composer |
| Lab ORM timeline | `ReplayTrack` / `ReplayFrame` | Inspection / legacy lab rows | `_lab_timeline_frames_for_project` inside composer |
| **Composed product timeline** | **Not persisted** | Full enriched JSON frames | Built on every request |

There is **no** `LabReplayArtifact` model today. “Artifact reuse” means **persisting the composed timeline (and manifest summary) on the `SolverRun` row** (or an approved equivalent store), not introducing a new wire contract.

---

## 2. Goal

Eliminate **unnecessary** calls to `build_lab_replay_frames_for_project()` on hot paths while preserving **semantic equivalence** with today’s inline/lazy behavior.

| Path | Target |
|------|--------|
| `project_page` lazy SSR | Manifest from **persisted summary**; **no** full compose |
| `run_solver` POST (lazy) | **One** compose after solve; persist; return lazy handle from persisted summary |
| `lab_replay` GET | Return **persisted composed frames** when available |
| Inline rollback | May still compose (legacy) |
| Old runs / missing cache | Path-specific policy (§4.10); lazy SSR cache miss: compose once + backfill |

**Non-goals:** Change GET JSON shape (still legacy `frames[]` until 13E) · Reduce `response_bytes` on GET (13E/13G) · Use replay as solver input.

---

## 3. Approaches considered

### A — Persist composed timeline on `SolverRun.config_json` (recommended)

At end of successful Layer 02 run (single compose):

1. Run `build_lab_replay_frames_for_project(project_id, solver_run_id=run_id)` **once**.
2. Write:
   - `lab_replay_composed_frames` — full serialized frames (GET source of truth for that run).
   - `lab_replay_manifest_summary` — `frame_count`, `preview_frame_index`, `preview_frame`, `replay_track_metrics`, `replay_payload_version`.
3. SSR / GET / POST read manifest or frames from these keys.

| Pros | Cons |
|------|------|
| Matches existing `solver_runtime_replay_frames` persistence pattern | Large JSON in `config_json` (acceptable until 13E; same bytes as today’s GET) |
| No migration; run-scoped correctness for 13C GET | Old runs need fallback compose |
| Clear perf win on repeat access | DB row size growth (monitor) |

### B — In-process cache only (rejected)

LRU keyed by `(project_id, solver_run_id)` avoids repeat CPU but not cold `project_page` or multi-worker deploys.

### C — Denormalize to `ReplayTrack` rows (deferred)

Strong durability and queryability, but ORM write amplification and adapter churn — out of scope for lite PR.

**Recommendation:** **A** with explicit config keys and version field.

---

## 4. Contract

### 4.1 Config keys (new)

Add to [`solver_run_config_keys.py`](../../../django_apps/asteroid_lab/services/solver_run_config_keys.py):

```text
SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY = "lab_replay_composed_frames"
SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY = "lab_replay_manifest_summary"
```

**`lab_replay_manifest_summary` shape** (manifest SSR + POST lazy handle, no full frames):

```json
{
  "replay_payload_version": 1,
  "lab_replay_cache_schema_version": 1,
  "frame_count": 88,
  "preview_frame_index": 87,
  "preview_frame": { "...": "single legacy-shaped frame dict" },
  "replay_track_metrics": {
    "frame_count": 88,
    "replay_truncated": false,
    "truncation_reason": null,
    "dropped_frame_count": null,
    "diagnostic_reason": null
  }
}
```

**`lab_replay_composed_frames`:** `list[dict]` — same serialization as `build_lab_replay_frames_for_project` return value today (enriched, legacy-shaped). **Not** 13E delta.

**Versioning (two fields, do not conflate):**

| Field | Role |
|-------|------|
| `replay_payload_version` | Wire contract for manifest / GET (unchanged meaning from 13C) |
| `lab_replay_cache_schema_version` | **Persisted cache invalidation only** — bump when compose/enrichment storage shape changes |

Cache miss when summary or composed frames absent **or**:

```text
lab_replay_cache_schema_version != CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION
```

(`CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION = 1` in `lab_replay_persisted_cache.py`.)

Do **not** use `replay_payload_version` alone to invalidate stored frames.

### 4.2 Project page — lazy SSR

When `ASTEROID_LAB_REPLAY_PAYLOAD_MODE=lazy`:

```text
MUST NOT call build_lab_replay_frames_for_project() on success path.

lab_page_context():
  → solver_runs_for_lab_project()
  → resolve latest run id (existing _solver_run_id_from_lab_summary)
  → load lab_replay_manifest_summary via partial JSON read (§4.7)
  → build_lab_replay_manifest_from_artifact(...) → template lab_replay_manifest_json
```

**Cache-hit path (required for acceptance):** summary present + valid `lab_replay_cache_schema_version` → **no** `build_lab_replay_frames_for_project()`.

**Cache-miss path (approved policy A):** summary absent or schema mismatch → fallback compose once, persist summary + composed frames, emit `replay_cache_miss_compose_ms` in perf trace. Subsequent page loads are cache-hit.

Allowed reads:

- `solver_runs_for_lab_project()` summary list (no full `config_json` on each run)
- `lab_replay_manifest_summary` via **partial JSON fetch only** (§4.7)
- `get_latest_lab_replay_track_for_project` for `lab_replay_track_id` / `track_key` display only (no frame scan)

Forbidden:

- Full compose on **cache-hit** path
- Embedding `lab-replay-frames-data` (unchanged 13D rule)
- Deserializing `lab_replay_composed_frames` while building SSR manifest (§4.7)

### 4.3 Project page — inline rollback

When `ASTEROID_LAB_REPLAY_PAYLOAD_MODE=inline`:

```text
MAY call build_lab_replay_frames_for_project() (or load composed cache if present — optional optimization).
MUST render lab-replay-frames-data + lab-replay-track-metrics-data per 13D inline rollback.
```

### 4.4 Run Solver POST

Target pipeline (Layer 02 success):

```text
solver layers + replay_artifact_build_ms (runtime segment — keep or fold per implementation plan)
→ db_persist_ms (config includes solver_runtime_replay_frames)
→ compose_once_ms:
      frames, metrics = build_lab_replay_frames_for_project(pid, solver_run_id=run_id)
      persist lab_replay_composed_frames + lab_replay_manifest_summary on run.config_json
→ entry_result_to_json_dict:
      lazy handle from manifest summary only (no second compose)
```

**Remove** the current separate `post_replay_compose_ms` block that recomposes without persisting for reuse.

Fail-closed / error paths in `solver_runtime_entry.py` may still compose for diagnostics where no new run exists — document as explicit exceptions.

### 4.5 Lab replay GET

```text
GET …/solver-runs/<run_id>/lab-replay/

if lab_replay_composed_frames on run:
    frames = load from config_json
    metrics = manifest summary replay_track_metrics (or recompute metrics from frames — prefer stored metrics)
else:
    frames, metrics = build_lab_replay_frames_for_project(project_id, solver_run_id=run_id)  # fallback
    optionally backfill persist (feature-flag or always-on for forward fix)

return legacy JSON:
  { schema_version, run_id, project_slug, frame_count, frames, replay_track_metrics, metrics }
```

Wire shape **unchanged** from 13C GET contract.

### 4.6 Helper API

```python
def build_lab_replay_manifest_from_artifact(
    *,
    project_slug: str,
    solver_run_id: int | None,
    manifest_summary: dict[str, Any] | None,
    fetch_url_builder: Callable[..., str | None],  # or inline reverse() in service
) -> dict[str, Any]:
    """Build lab-replay-manifest-data dict without full frame list."""
```

Responsibilities:

- Map summary → `lab_replay_manifest_json_dict`-compatible dict (`mode`, `frame_count`, `preview_*`, `fetch_url`, `replay_track_metrics`, `replay_payload_version`)
- `fetch_url: null` when `solver_run_id` missing or `frame_count == 0` (13D idle state)

Loaders (module: `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`):

```python
CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION = 1

def load_manifest_summary_for_run_id(run_id: int) -> dict[str, Any] | None: ...
def load_composed_frames_for_run_id(run_id: int) -> list[dict[str, Any]] | None: ...
def persist_composed_replay_for_run_id(
    run_id: int, *, frames: list[dict[str, Any]], metrics: dict[str, Any]
) -> None: ...
def build_manifest_summary_from_compose(
    *, frames: list[dict[str, Any]], metrics: dict[str, Any]
) -> dict[str, Any]: ...
```

### 4.7 Blocking invariant — no `config_json` read amplification on lazy SSR

Storing full composed frames in the same `config_json` JSONField as the manifest summary creates a **read amplification** risk: loading the row for SSR can deserialize **~15.8 MB** of `lab_replay_composed_frames` even when only the small summary is needed.

**Blocking invariant:**

```text
Lazy SSR must not deserialize lab_replay_composed_frames while loading lab_replay_manifest_summary.
```

A plain `SolverRun.objects.get(pk=…)` followed by `run.config_json[...]` is **forbidden** on the lazy `project_page` path when `lab_replay_composed_frames` may be present.

**Implementation must satisfy one of:**

| Option | Requirement |
|--------|-------------|
| **A (recommended)** | Fetch summary via Django JSON key transform / DB JSON operator so the ORM does **not** load the full `config_json` blob into Python for SSR. Example: `KeyTransform(SOLVER_RUN_CONFIG_LAB_REPLAY_MANIFEST_SUMMARY_KEY, "config_json")` with `.values_list(..., flat=True)` on a filtered queryset. |
| **B** | Store `lab_replay_manifest_summary` in a separate small column/store (migration — only if A is infeasible on supported DB backends). |
| **C** | Store composed frames outside `config_json` while summary remains in `config_json` (follow-up / larger scope). |

**This PR implements A** unless Task 0 proves the project DB backend cannot support partial JSON reads (document in plan; then escalate to B).

**GET `lab-replay/`** may load only `lab_replay_composed_frames` via the same partial-read pattern (not the full row dict via `.config_json` on a materialized instance unless frames key alone is extracted).

### 4.8 Blocking invariant — `config_json` merge/write atomicity

POST persists `solver_runtime_replay_frames` first, then composed cache keys. Stale in-memory `config_json` must not overwrite unrelated keys.

**Rules:**

```text
Persist helpers must perform fresh read-merge-write of SolverRun.config_json.
They must not overwrite unrelated config_json keys (e.g. solver_runtime_replay_frames, solver_summary).
```

Required pattern:

```text
transaction.atomic()
  run = SolverRun.objects.select_for_update().get(pk=run_id)
  config = copy.deepcopy(dict(run.config_json or {}))
  set only lab_replay_composed_frames and lab_replay_manifest_summary (+ bump lab_replay_cache_schema_version inside summary)
  run.config_json = config
  run.save(update_fields=["config_json"])
```

### 4.9 Perf trace extensions (13L)

When `ASTEROID_LAB_PERF_TRACE=1`, record:

```text
lab_replay_cache_frames_bytes
lab_replay_manifest_summary_bytes
replay_cache_load_ms
replay_cache_json_decode_ms
replay_cache_miss_compose_ms   # lazy SSR or GET miss only
replay_compose_once_ms         # single compose on POST (replaces post_replay_compose_ms naming)
```

Acceptance: after cache warm, `lab_replay_cache_frames_bytes` may be large on GET but **`lab_replay_manifest_summary_bytes`** on `project_page` stays small (order KB, not MB).

### 4.10 Cache-miss policy by path

| Path | Cache hit | Cache miss |
|------|-----------|------------|
| **`project_page` lazy SSR** | Partial-read summary → manifest; **no compose** | **Policy A:** `build_lab_replay_frames_for_project()` once → persist → manifest; span `replay_cache_miss_compose_ms` |
| **`lab_replay` GET** | Partial-read composed frames → response | Fallback compose once → optional backfill persist → response |
| **`run_solver` POST** | N/A (always compose once after solve) | N/A |

Do **not** return an idle manifest on SSR cache miss without compose (Policy B rejected for this PR).

---

## 5. Call graph (target)

```text
                    ┌─────────────────────────────┐
                    │ build_lab_replay_frames_*   │  ← single compose (solve / fallback)
                    └──────────────┬──────────────┘
                                   │ persist
                    ┌──────────────▼──────────────┐
                    │ SolverRun.config_json       │
                    │  lab_replay_composed_frames │
                    │  lab_replay_manifest_summary│
                    └──────────────┬──────────────┘
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
   lab_page_context          entry_result_to_json    lab_replay GET
   (lazy: manifest only)     (lazy: handle only)     (frames load)
```

**Files expected to change:**

| File | Change |
|------|--------|
| `solver_run_config_keys.py` | New keys |
| `lab_replay_persisted_cache.py` (new) | Load/persist/summary builders |
| `solver_runtime_layer02.py` | Compose once + persist; remove duplicate post compose |
| `asteroid_lab_page_context.py` | Lazy path: manifest from summary |
| `public_pages.py` | GET: load composed frames |
| `lab_replay_lazy_handle.py` | Optional: build handle from summary without `frames` list |
| `lab_perf_trace.py` | Spans: `replay_compose_once_ms`, `replay_cache_load_ms`, `replay_cache_miss_compose_ms` |

---

## 6. Tests

**Patch rule (plan Task 0 inventory):** Patch `build_lab_replay_frames_for_project` **as imported at the call site** — e.g. `django_apps.web.services.asteroid_lab_page_context`, `django_apps.web.views.public_pages`, `django_apps.asteroid_lab.services.solver_runtime_layer02` — not only the defining module `lab_replay_timeline_payload`.

Use `unittest.mock.patch` unless testing fallback / miss paths explicitly.

| Test | Expectation |
|------|-------------|
| `test_project_page_lazy_ssr_does_not_call_full_replay_composer` | Lazy mode, fixture with valid persisted summary → compose call count **0** on **cache-hit** path; manifest present; no `lab-replay-frames-data` |
| `test_project_page_lazy_ssr_does_not_load_composed_frames_blob` | Sentinel: oversized `lab_replay_composed_frames` in DB; page SSR loads summary without accessing/deserializing frames value (mock `load_composed_frames_for_run_id` or instrument partial loader) |
| `test_project_page_lazy_cache_miss_backfills_summary` | Run without cache keys → page triggers compose once, persists summary, manifest populated |
| `test_project_page_inline_ssr_still_uses_full_replay_frames` | inline mode → frames script present; metrics script per 13D |
| `test_lab_replay_get_uses_persisted_artifact_when_available` | Run with composed frames in config → GET returns same frames; compose **not** called |
| `test_lab_replay_get_falls_back_to_compose_without_artifact` | Old run without keys → compose **once**; legacy shape |
| `test_run_solver_does_not_recompose_replay_after_artifact_build` | Layer 02 integration: compose call count **1** per POST; `post_replay_compose` span absent or merged |
| `test_persisted_manifest_matches_composed_preview` | After solve, summary `preview_frame` equals last frame of composed list |
| `test_lazy_get_semantic_equivalence_persisted_vs_compose` | Persisted GET ≡ fallback compose for same `solver_run_id` (fixture) |

Regression: existing 13D manifest tests updated to **seed manifest summary** on fixture `SolverRun` instead of relying on compose during page render.

---

## 7. Perf acceptance criteria

After implementation (same fixture project, `ASTEROID_LAB_PERF_TRACE=1`):

| Metric | Target |
|--------|--------|
| `project_page` `html_bytes` | Remains ~366 KB / under `LAB_REPLAY_SSR_DOCUMENT_MAX_BYTES` |
| `project_page` `build_lab_replay_frames_for_project_ms` | **0** or absent on lazy **cache-hit** path |
| `project_page` `lab_replay_manifest_summary_bytes` | Small (KB); not ~15 MB |
| `project_page` `replay_cache_json_decode_ms` | Low on cache-hit vs full config decode |
| `project_page` `total_ms` | Drop ~4 s vs 7.3 s baseline if compose was dominant (solver_runs cost may remain) |
| `run_solver` `post_replay_compose_ms` | **Removed** or ≈ compose-once (single span) |
| `lab_replay_get` `replay_compose_ms` | Near `replay_cache_load_ms` when cache hit |
| `lab_replay_get` `response_bytes` | **Unchanged** until 13E/13G |

### 7.1 Perf verification (`lab_perf.jsonl`, 2026-05-29, `rttp-core-recovery-test-map`, cache warm)

```text
Perf verification:
- project_page cache-hit:
  total_ms ≈ 3,203
  html_bytes ≈ 369 KB
  build_lab_replay_frames_for_project_ms absent
  replay_cache_miss_compose_ms absent
  remaining bottleneck: solver_runs_for_lab_project_ms ≈ 2,922

- lab_replay_get cache-hit:
  total_ms ≈ 1,297
  replay_cache_load_ms ≈ 515
  json_response_build_ms ≈ 391
  replay_compose_ms absent
  response_bytes unchanged ≈ 15.8 MB

- run_solver:
  total_ms ≈ 10,469
  replay_compose_once_ms ≈ 5,562
  layer_03_ms ≈ 2,344
  compose_once remains by design
```

---

## 8. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Old runs lack composed cache | GET fallback compose; optional backfill on miss |
| Stale manifest if compose logic changes | Bump `lab_replay_cache_schema_version`; miss → recompose |
| `config_json` read amplification on SSR | Partial JSON read for summary only (§4.7); regression test §6 |
| `config_json` size limits (DB/JSONField) | Same payload as today’s GET; monitor `lab_replay_cache_frames_bytes`; 13E later |
| Stale `config_json` overwrite | Fresh read-merge-write + `select_for_update` (§4.8) |
| Preview/metrics drift from composed frames | Write summary in same transaction immediately after compose |
| Inline rollback regression | Keep inline branch; dedicated test |
| 13L span misread (nested compose) | Rename spans: `replay_compose_once_ms` vs `replay_cache_load_ms` |
| `solver_runs_for_lab_project_ms` still ~2.3 s | Out of scope; track separately |

---

## 9. Implementation plan outline

(Task-level plan — detail in `docs/superpowers/plans/2026-05-29-replay-compose-defer-artifact-reuse.md` after spec approval.)

```text
Task 0 — Inventory: confirm all build_lab_replay_frames_for_project call sites
Task 1 — Config keys + persist/load helpers + unit tests
Task 2 — Layer 02: compose once, persist, remove duplicate post_replay_compose
Task 3 — entry_result_to_json_dict: handle from manifest summary
Task 4 — lab_page_context lazy path: manifest from summary, no compose
Task 5 — lab_replay GET: load composed frames + fallback
Task 6 — Integration tests (mock compose counts + equivalence)
Task 7 — Perf verification + documents/ai/current_plan.md + asteroid_lab_13 roadmap note
```

---

## 10. Rollout / flags

```text
ASTEROID_LAB_REPLAY_COMPOSE_CACHE=1   # default on after PR; inline "0" forces legacy compose-everywhere (debug)
```

Optional: separate flag only if rollback risk warrants; prefer single flag default-on with inline mode still composing.

---

## 11. Relationship to 13E / 13G / PR-13F

| PR | Relationship |
|----|----------------|
| **13G** | Compresses persisted GET bytes; independent of compose defer |
| **13E** | Replaces `lab_replay_composed_frames` **representation**; defer makes 13E a encoding swap on stored artifact |
| **PR-13F (interning)** | After 13E measurement; not this PR |

---

## 12. Exit criteria

```text
[x] Lazy project_page cache-hit: no build_lab_replay_frames_for_project; no composed-frames blob decode
[x] Lazy project_page cache-miss: compose once + backfill (Policy A)
[x] run_solver: at most one compose per successful Layer 02 run; atomic config_json merge
[x] lab_replay GET: partial load composed frames on cache hit
[x] Fallback compose preserves legacy JSON equivalence
[x] Perf trace: cache-hit page near zero compose; summary_bytes small (§7.1)
[x] No change to GET frame object shape (13E deferred)
```

**Implementation plan:** [`docs/superpowers/plans/2026-05-29-replay-compose-defer-artifact-reuse.md`](../plans/2026-05-29-replay-compose-defer-artifact-reuse.md)
