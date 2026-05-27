# Lab Replay Payload Lazy-load & Initial POST Slimming — Design Spec

**Date:** 2026-05-30  
**Status:** Approved (amendments 2026-05-30: run-scoped replay selection, terminology sync, transport-only scope)  
**Sequence:** 13C (POST slimming + GET endpoint + minimal frontend lazy-load)  
**Follow-up:** 13D-SSR (SSR `json_script` slimming, deferred)  
**Scope:** Run Solver POST JSON response transport only  
**Authority:** [`documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md`](../../../documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md) · [`documents/Algorithm/asteroid_lab_09_replay_timeline.md`](../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md)

---

## Problem

Run Solver POST responses currently inline the full product replay timeline as `lab_replay_frames_json`. Observed payloads reach **~22.6MB** (HAR evidence). Chrome DevTools may evict large response bodies from the inspector cache, blocking normal debugging.

The bottleneck is not SHAPEZ2-4 copy strings but repeated per-frame map snapshots (`full_map`, overlay cells, diff bodies) inside `lab_replay_frames_json`.

---

## Goal

**Primary:** Remove unnecessary full Lab replay payload from the initial Run Solver POST response.

**Target state:**

```text
POST (lazy mode):
  run summary / metrics
  preview frame (one)
  frame_count
  lazy replay handle (fetch URL)
  milestone HUD payload (unchanged, small)

GET (on demand):
  full product replay timeline frames
  semantically identical to historical inline lab_replay_frames_json
```

---

## Non-goals (13C)

```text
❌ Frontend SHAPEZ2-4 decode migration
❌ Solver / reconstruction / validation / algorithm changes
❌ Replay semantics changes (frame content, ordering, event types)
❌ Delta replay, cell interning, binary replay format
❌ WebSocket streaming, object-store artifact download
❌ SSR page load json_script slimming (deferred to 13D-SSR)
❌ Using replay payload as solver input
```

**This change does not move SHAPEZ2-4 decoding to the frontend.** The backend remains the canonical decode/reconstruction/solver owner. This change only separates initial POST response transport from full Lab replay transport. Replay remains output-only and must not become solver input.

---

## Canonical terminology

| Term | Wire key / note |
|------|-----------------|
| Product replay timeline | Single Lab replay timeline ([`asteroid_lab_09_replay_timeline.md`](../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md)) |
| Full timeline frames | `lab_replay_frames_json` (inline mode) or GET `frames` (lazy mode) |
| Milestone HUD track | `lab_optimization_milestone_frames_json` (small; stays inline in 13C) |

**Do not** describe this work as Optimization/Lab dual-track replay. Dual-track terminology is deprecated as of 2026-05-19.

### Terminology amendment (authority sync)

Earlier Sequence 13 documents used "Lab / Optimization dual-track" wording. As of [`asteroid_lab_09_replay_timeline.md`](../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md) canonical update on 2026-05-19, 13C uses **single product replay timeline** plus a separate **milestone HUD payload** (`lab_optimization_milestone_frames_json`). This spec supersedes the older dual-track wording for 13C transport work. Implementation PR must sync [`asteroid_lab_13_replay_payload_scalability.md`](../../../documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md) invariants accordingly.

---

## Transport vs composition cost (13C scope boundary)

13C optimizes **response transport size only**. It does **not** yet eliminate server-side frame composition cost during POST (full frames are still composed internally to select preview + metrics). A later sequence may defer composition until GET after semantic equivalence is stable.

---

## Approved scope decision (Option C)

```text
13C: Slim Run Solver POST JSON only.
13D-SSR (follow-up): Slim SSR lab_page_context() json_script embed using the same GET endpoint and frontend loader.
```

Rationale: POST is the direct HAR/DevTools bottleneck; SSR touches template hydration and initial page context; GET contract and semantic equivalence tests must land before SSR slimming.

---

## Approach selection

Three candidate strategies for serving full replay on GET:

| Approach | Mechanism | Pros | Cons |
|----------|-----------|------|------|
| **A-1 — Run-scoped DB recompose (approved)** | GET calls `build_lab_replay_frames_for_project(project_id, solver_run_id=run_id)`; builder filters runtime + RTTP segments to that run | Same serialization pipeline; `run_id` selects replay content; old runs stay addressable | Recompose cost on each GET (acceptable; display-only) |
| A-2 — Latest-run-only GET | Project-scoped builder; reject `run_id != latest_solver_run_id` with 404/409 | Minimal builder change | Breaks run history debugging; URL lies about content |
| B — Run snapshot blob | Persist full serialized frames in `SolverRun.config_json` at solve time | Fast GET read | Duplicates storage; drift risk vs live compose |
| C — Ephemeral cache | Redis/memory keyed by `run_id` with TTL | Fast GET | New infra; harder regression story |

**Approved: Approach A-1.** `solver_run_id` is part of the **replay selection contract**, not auth-only metadata.

```text
GET must return the product replay timeline for the requested solver_run_id.
If the existing builder is project-scoped, 13C adds a run-scoped builder parameter.
Run-scoped selection:
  - Lab ORM timeline segments: project-scoped (inspection / reconstruction track)
  - Solver runtime frames: from SolverRun.config_json for that run_id
  - RTTP interleave rows: load_rttp_compose_rows_for_project(project_id, run_key=run.run_key)
When solver_run_id is omitted (SSR / legacy callers): preserve current latest-run behavior.
```

---

## Invariants

```text
1. Replay is output-only.
2. One product replay timeline (dual-track policy deprecated 2026-05-19).
3. Product replay timeline and milestone HUD payload remain separate. No implicit sync or index coupling between them.
4. No solver / algorithm reads replay payload.
5. Replay semantic equivalence must be preserved (inline ≡ lazy GET).
6. UI / overlay ownership must not drift.
7. Lazy-load failure must not corrupt current UI state (preview frame preserved).
8. Every frame must remain 2D-renderable (map_view) when transport shape changes.
```

---

## Architecture

### Current flow

```text
POST /asteroid-miner-layout/p/<slug>/run-solver/
  → run_solver_runtime_for_project
  → build_lab_replay_frames_for_project (after persist)
  → entry_result_to_json_dict (full lab_replay_frames_json inline)
  → frontend replaceLabReplayPayload (full frames immediately)
```

### Target flow (lazy mode)

```text
POST /asteroid-miner-layout/p/<slug>/run-solver/
  → run_solver_runtime_for_project (unchanged solver path)
  → build_lab_replay_frames_for_project (still runs; frames not inlined)
  → entry_result_to_json_dict (slim: lab_replay handle + preview only)
  → frontend renders preview; full frames unloaded

GET /asteroid-miner-layout/p/<slug>/solver-runs/<run_id>/lab-replay/
  → verify project slug + solver_run_id belong together
  → build_lab_replay_frames_for_project(project_id, solver_run_id=run_id)
  → return frames[] (same serialization as inline for that run)
  → frontend ensureLabReplayFramesLoaded → inject into existing replay controller
```

### Deferred (13D-SSR)

```text
GET project page (SSR)
  → lab_page_context() currently embeds full lab_replay_frames_json in json_script
  → follow-up PR switches to preview-only embed + same lazy GET loader
```

---

## API contract

### Feature flag

Register in [`documents/ai/manuals/environment.md`](../../../documents/ai/manuals/environment.md) with implementation PR (not pre-added to `.env`):

```python
# config/settings.py
ASTEROID_LAB_REPLAY_PAYLOAD_MODE = "lazy"  # "inline" | "lazy"
```

| Mode | POST behavior |
|------|---------------|
| `inline` | Current behavior (full `lab_replay_frames_json`); for CI comparison and rollback |
| `lazy` | Default after 13C; omits full inline array |

### POST response (lazy mode)

**Removed from POST body (lazy mode):** full `lab_replay_frames_json` array.

**Added:**

```json
{
  "lab_replay": {
    "mode": "lazy",
    "frame_count": 123,
    "preview_frame_index": 122,
    "preview_frame": { "...": "same semantic as inline frame at preview_frame_index" },
    "fetch_url": "/asteroid-miner-layout/p/my-project/solver-runs/456/lab-replay/",
    "replay_payload_version": 1
  },
  "lab_replay_frame_count": 123,
  "replay_track_metrics": { "...": "unchanged shape" },
  "lab_optimization_milestone_frames_json": [ "...": "unchanged; stays inline" ],
  "metrics": {
    "post_payload_slimmed": true,
    "lab_replay_inline_omitted": true,
    "lab_replay_frame_count": 123
  }
}
```

**Preview frame policy (POST Run Solver):** `preview_frame_index = frame_count - 1` (last frame). Matches current frontend behavior (`replaceLabReplayPayload(data, { seekLastFrame: true })`). `preview_frame` is the serialized frame at that index.

**Inline mode fallback (migration):** When `lab_replay.mode == "inline"`, POST continues to include full `lab_replay_frames_json` and may omit `lab_replay` handle fields. Frontend keeps existing path.

**Top-level keys preserved:** `ok`, `solver_run_id`, `solver_summary`, `validation_passed`, `run_summary`, `replay_track_metrics`, `lab_optimization_milestone_*`, `gene_template_source`, error fields — unchanged semantics.

### GET endpoint

```http
GET /asteroid-miner-layout/p/<slug>/solver-runs/<run_id>/lab-replay/
Accept: application/json
```

**Response (200):**

```json
{
  "schema_version": 1,
  "run_id": 456,
  "project_slug": "my-project",
  "frame_count": 123,
  "frames": [
    { "...": "same semantic as historical inline lab_replay_frames_json[i]" }
  ],
  "replay_track_metrics": { "...": "same shape as POST replay_track_metrics" },
  "metrics": {
    "source": "lazy_load",
    "semantic_equivalent_to_inline": true
  }
}
```

**Equivalence requirement:**

```text
GET frames == inline lab_replay_frames_json for the same solver_run_id
(same builder: build_lab_replay_frames_for_project(project_id, solver_run_id=run_id))
same frame_count
same frame_index order
same frame keys / event metadata
same full_map / diff / map_view / overlay semantics
same cell detail compatibility (inspector.replay_frame_id on Lab ORM frames)
```

### Error policy

| Situation | Response |
|-----------|----------|
| Unknown slug / project | 404 |
| `run_id` not found or not owned by project | 404 |
| No replay frames after compose | **200** with `frames: []` + `replay_track_metrics.diagnostic_reason` (consistent with empty product timeline) |
| Malformed persisted replay | 200 with diagnostic; **no 500** from display path |
| Auth failure (if auth added later) | 403 |

Frontend on GET failure: keep preview frame; show explicit error HUD; allow retry; do not enter broken partial timeline state.

---

## Backend components

### 1. `LabReplayLazyHandle` DTO

Location: `django_apps/asteroid_lab/services/` (or `contracts/` if existing replay DTO pattern prefers it).

```python
@dataclass(frozen=True)
class LabReplayLazyHandle:
    mode: Literal["inline", "lazy"]
    frame_count: int
    preview_frame_index: int
    preview_frame: Mapping[str, Any] | None
    fetch_url: str | None
    replay_payload_version: int  # = 1
```

Built inside `entry_result_to_json_dict` when mode is `lazy`. `fetch_url` from `django.urls.reverse` with slug + `solver_run_id`.

### 2. `entry_result_to_json_dict` slim branch

When `ASTEROID_LAB_REPLAY_PAYLOAD_MODE == "lazy"`:

- Still compute full frames internally (for preview selection + metrics).
- Omit `lab_replay_frames_json` from response dict (or omit key entirely; tests assert absence).
- Emit `lab_replay` handle + `metrics` attribution flags.
- Do **not** change solver result generation or frame serialization.

### 3. GET view

New view in `django_apps/web/views/public_pages.py`, URL in `django_apps/web/urls.py`:

- Resolve project by slug.
- Verify `SolverRun` exists with `pk=run_id` and `project_id=project.pk`.
- Call `build_lab_replay_frames_for_project(project.pk, solver_run_id=int(run_id))`.
- Return JSON as specified.

No new ORM fields. No config_json blob for replay snapshot in 13C.

### 4. Payload attribution (13A/13B extension)

Keep / extend `tests/support/measure_json_sections.py` usage:

- Measure POST response dict bytes before/after lazy mode.
- Assert lazy POST does not contain full inline lab replay array.
- Regression command:

```bash
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k "payload or replay or json_size"
```

**Size threshold policy:** Implementation PR must record measured `inline_bytes` and `lazy_bytes` for the selected regression fixture and store the threshold as a **named constant** (e.g. `LAB_REPLAY_LAZY_POST_MAX_BYTES`) derived from that measurement. Do not hard-code guessed percentages in the spec; the fixture table in the plan/PR body is the source of truth.

---

## Frontend components (13C minimal)

Scope: POST lazy payload only. SSR still embeds full frames until 13D-SSR.

### 1. Payload normalizer extension

Extend `replaceLabReplayPayload()` in `asteroid_miner_layout_lab.js`:

| Input | Behavior |
|-------|----------|
| `lab_replay_frames_json` array (inline) | Existing path unchanged |
| `lab_replay.mode === "lazy"` | Initialize with `preview_frame` only; `replayFrames` partial; store `fetch_url`, `frame_count`; status `not loaded` |

### 2. Lazy-load controller

```javascript
const labReplayLoadState = {
  mode: "lazy" | "inline",
  status: "idle" | "loading" | "loaded" | "error",
  frames: null,
  frameCount: 0,
  fetchUrl: null,
  errorMessage: null,
};
```

Functions:

- `ensureLabReplayFramesLoaded(reason)` — dedupe in-flight fetch; GET `fetch_url`; on success call existing replay init path.
- `applyLoadedLabReplayPayload(payload)` — inject full `frames` into `replayFrames`; preserve current index when possible.
- `renderLabReplayLoadStatus()` — HUD: preview only / loading / loaded N frames / failed (retry).

### 3. Timeline gating

Trigger `ensureLabReplayFramesLoaded()` on:

- Play button
- Scrubber move beyond preview index
- Replay panel expand (if applicable)

While loading: disable duplicate fetches; keep preview visible.

On error: preview unchanged; explicit error HUD; retry available.

### 4. Run Solver success path

After POST success with lazy payload:

- Render preview (last frame).
- Do **not** auto-fetch full replay until user interacts with timeline.
- On validation failure with partial inline fallback (error responses may still include frames array in inline mode only): preserve existing error path.

---

## Testing strategy

### Backend

```text
test_post_projects_lazy_mode_omits_full_lab_replay_frames
test_post_projects_lazy_mode_includes_preview_frame_and_fetch_handle
test_post_projects_inline_mode_still_returns_full_lab_replay_frames
test_lab_replay_endpoint_returns_full_frames
test_lab_replay_endpoint_matches_legacy_inline_frames_semantically
test_lab_replay_endpoint_requires_valid_project_run_access
test_lab_replay_endpoint_handles_empty_timeline_without_500
test_post_payload_reports_lab_replay_inline_bytes (attribution)
test_post_projects_json_size_attribution_and_optimization_replay_hard_caps
```

### Semantic equivalence (required)

```python
inline_body = post_run_solver(mode="inline")  # captures solver_run_id
run_id = inline_body["solver_run_id"]
lazy_get_frames = get_lab_replay(slug, run_id)

assert len(lazy_get_frames) == len(inline_body["lab_replay_frames_json"])
# second run on same project: GET old run_id != GET new run_id when RTTP segments differ
# per-frame deep equality on frame_index, keys, map_view, full_map, diff, metrics, event_type
```

### Frontend (JS or integration)

```text
test_lazy_payload_initializes_preview_only
test_scrub_triggers_lazy_load_once
test_play_triggers_lazy_load_once
test_lazy_load_success_reuses_existing_replay_controller
test_lazy_load_failure_preserves_preview_state
test_inline_mode_fallback_still_works
test_product_timeline_and_milestone_hud_indices_do_not_implicitly_sync
```

---

## PR plan

| PR | Scope |
|----|-------|
| **PR-13C-1** | This spec + `current_plan.md` queue entry |
| **PR-13C-2** | Backend DTO + GET endpoint + POST slim + backend tests |
| **PR-13C-3** | Frontend lazy-load controller + minimal HUD + frontend tests |
| **PR-13C-4** | Payload size gates + CI hardening |
| **PR-13D-SSR** | SSR `lab_page_context` preview-only + template changes (deferred) |
| **PR-13E+** | Delta / interning / compression (separate sequences) |

---

## Exit criteria (Sequence 13C)

```text
[x] Initial POST no longer carries full lab_replay_frames_json by default (lazy mode)
[x] Full replay fetchable via GET endpoint
[x] GET frames semantically equivalent to inline lab_replay_frames_json
[x] UI renders preview immediately after Run Solver
[x] Timeline interaction triggers lazy-load
[x] Lazy-load failure does not corrupt preview / base grid state
[x] Milestone HUD track unchanged and not conflated with product timeline
[x] Replay remains output-only; no solver/reconstruction changes
[x] Payload size regression tests added
```

Sequence 13 overall exit (with 13D-SSR): large response DevTools eviction avoided for normal Run Solver **and** project page revisit flows.

---

## Document history

| Date | Change |
|------|--------|
| 2026-05-30 | Initial draft (Option C approved; Approach A DB recompose; canonical terminology) |
| 2026-05-30 | Approved amendments: A-1 run-scoped builder, terminology sync, transport-only note, measured fixture threshold |
