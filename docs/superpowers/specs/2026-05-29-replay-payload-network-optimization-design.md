# Replay Payload Network Optimization — Design Spec

**Date:** 2026-05-29  
**Status:** Approved (§1 amendments 2026-05-29)  
**Authority:** [`documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md`](../../../documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md) · [`docs/superpowers/specs/2026-05-30-lab-replay-lazy-load-post-slimming-design.md`](2026-05-30-lab-replay-lazy-load-post-slimming-design.md)

---

## Problem (observed)

HAR / DevTools evidence on a project page with ~86 replay frames:

| Request | Size (observed) | Role |
|---------|-----------------|------|
| Project page document | ~16 MB | SSR embeds full `lab_replay_frames_json` |
| `GET …/lab-replay/` | ~15 MB | Lazy full timeline fetch |
| `POST …/run-solver/` | ~265 KB | 13C lazy POST — healthy |

**Root cause:** Per-frame `full_map` (and related bodies) repeated across the timeline. Lazy POST split transport but did not reduce semantic payload size on SSR or GET.

**One-line summary:**

```text
13D fixes SSR document bloat.
13G mitigates transport size.
13E fixes replay payload structure.
```

---

## Non-negotiable invariants

```text
1. Replay is output-only; no solver / algorithm reads replay payload.
2. One product replay timeline; milestone HUD payload stays separate.
3. Semantic equivalence: lazy GET frames ≡ historical inline lab_replay_frames_json (per solver_run_id).
4. Lazy-load failure must not corrupt preview / base grid state.
5. UI uses a single replay timeline controller (existing asteroid_miner_layout_lab.js).
```

---

## PR sequence

| PR | Sequence | Goal |
|----|----------|------|
| **PR-13D-SSR** | 13D | Manifest-only SSR; remove ~16 MB document embed |
| **PR-13G** | 13G | `GZipMiddleware`; compress large JSON/HTML responses |
| **PR-13E** | 13E | `base_map` + per-frame `delta` on GET; client reconstructs legacy-shaped frames |
| **PR-13F** | 13F | Cell interning / compact coord encoding (after 13E measurement) |
| **PR-13UI-guard** | — | Run Solver duplicate request guard (separate from payload work) |

**Recommended rollout:** 13D → 13G → 13E → 13F.

---

## PR-13D-SSR — Manifest-only SSR

### Goal

```text
Initial document must not embed full replay frames.
Initial page may embed only:
  - manifest (includes preview_frame + replay_track_metrics)
  - no separate preview / metrics scripts (SoT consolidation)
```

### Approved amendments (2026-05-29)

| # | Rule |
|---|------|
| 1 | Do **not** leave `lab-replay-frames-data` as an empty array — **remove the script** in lazy default mode |
| 2 | Remove `lab-initial-replay-frame-data`; preview lives only in `manifest.preview_frame` |
| 3 | Remove `lab-replay-track-metrics-data`; metrics live only in `manifest.replay_track_metrics` |
| 4 | When `fetch_url` is `null`, JS must enter an explicit idle/no-timeline state (no fetch, scrub disabled) |
| 5 | Inline SSR embed (`lab-replay-frames-data`) only when `ASTEROID_LAB_REPLAY_PAYLOAD_MODE=inline` (settings + test override) |
| 6 | Regression: fixture-based HTML byte cap **and** absence of bulk timeline frame strings (gzip-independent) |

### SSR wire contract — `lab-replay-manifest-data`

Same shape as 13C POST `lab_replay` lazy handle, plus metrics:

```json
{
  "mode": "lazy",
  "frame_count": 86,
  "preview_frame_index": 85,
  "preview_frame": { "frame_index": 85, "full_map": [], "map_view": {}, "diff": {} },
  "fetch_url": "/asteroid-miner-layout/p/{slug}/solver-runs/{run_id}/lab-replay/",
  "replay_payload_version": 1,
  "replay_track_metrics": {
    "frame_count": 86,
    "replay_truncated": false,
    "truncation_reason": null,
    "dropped_frame_count": null,
    "diagnostic_reason": null
  }
}
```

### Template (lazy default)

**Include:**

```html
{{ lab_replay_manifest_json|json_script:"lab-replay-manifest-data" }}
```

**Exclude (lazy default):**

```html
{{ lab_replay_frames_json|json_script:"lab-replay-frames-data" }}
{{ lab_initial_replay_frame_json|json_script:"lab-initial-replay-frame-data" }}
{{ replay_track_metrics|json_script:"lab-replay-track-metrics-data" }}
```

### Inline rollback (settings only)

When `ASTEROID_LAB_REPLAY_PAYLOAD_MODE=inline`:

```html
{{ lab_replay_frames_json|json_script:"lab-replay-frames-data" }}
{{ replay_track_metrics|json_script:"lab-replay-track-metrics-data" }}
```

No manifest script in inline mode. Inline keeps a separate metrics script because `init()` / `updateReplayTruncationHud` read `lab-replay-track-metrics-data` on first paint.

### Edge cases

| Case | Manifest |
|------|----------|
| Latest solver run exists, frames composed | `mode: "lazy"`, `fetch_url: string`, `frame_count > 0`, `preview_frame` set |
| No solver run | `fetch_url: null`, `frame_count: 0`, `preview_frame: null` |
| Empty composed timeline | `fetch_url: null` or run without artifact — `frame_count: 0`, `preview_frame: null` |
| Failed run with replay artifact | Lazy handle with `fetch_url` when `solver_run_id` valid |
| Failed run without replay artifact | `fetch_url: null` |

`run_id` for `fetch_url`: `initial_lab_run.id` when present; else `null`.

### Backend

- `lab_page_context()`: compose frames once for preview + metrics; expose `lab_replay_manifest_json` via `build_lab_replay_lazy_handle()` + `replay_track_metrics`; do **not** put full `frames_json` in template context when mode is lazy.
- Reuse existing GET `asteroid_miner_layout_project_solver_run_lab_replay` (13C).
- **Out of scope:** `reset_map` / import JSON bundles still inline until a follow-up; this PR is **SSR page only**.

### Frontend

- `init()`: read `lab-replay-manifest-data` first; hydrate `labReplayLoadState` like `replaceLabReplayPayload` lazy branch.
- `fetch_url === null`: `status: "idle"`, `fetchUrl: null`, no auto-fetch; scrub/play no-op or disabled; HUD shows preview-only or empty state.
- Legacy: if `lab-replay-frames-data` exists (inline SSR), existing inline path.
- `ensureLabReplayFramesLoaded` unchanged for timeline interaction.

### Tests

```text
test_project_page_lazy_ssr_document_bytes_under_cap
test_project_page_lazy_ssr_has_manifest_not_frames_script
test_project_page_lazy_ssr_no_bulk_timeline_frame_markers_in_html
test_project_page_inline_ssr_still_has_lab_replay_frames_data_script
test_ssr_manifest_fetch_url_matches_latest_solver_run
test_ssr_manifest_metrics_match_composed_track_metrics
```

Constants: `LAB_REPLAY_SSR_DOCUMENT_MAX_BYTES` — measured after fixture run; `max(measured_lazy_ssr * 2, 512_000)`.

Bulk-frame guard (example): assert `id="lab-replay-frames-data"` absent; assert `html.count('"frame_index"')` below fixture-derived ceiling (e.g. `< 25` for single-preview SSR).

### Exit criteria

```text
[x] Document HTML no longer embeds full lab_replay_frames_json (lazy default)
[x] Preview + metrics render on first paint
[x] Full timeline via GET + ensureLabReplayFramesLoaded
[x] Inline SSR rollback behind ASTEROID_LAB_REPLAY_PAYLOAD_MODE=inline only
[x] Size + bulk-frame regression tests in CI
```

**Implementation plan:** [`docs/superpowers/plans/2026-05-29-replay-payload-13d-ssr-slim.md`](../plans/2026-05-29-replay-payload-13d-ssr-slim.md)

---

## PR-13G — Transport compression

### Goal

Reduce **wire** bytes for large JSON/HTML without changing JSON semantics.

### Backend

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.gzip.GZipMiddleware",  # after WhiteNoise, before CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    ...
]
```

Django `GZipMiddleware` compresses responses when body length ≥ 200 bytes and client sends `Accept-Encoding: gzip`.

### Targets

| Response | Priority |
|----------|----------|
| `GET …/lab-replay/` | High (~15 MB JSON) |
| Project page document | Medium (post-13D smaller) |
| `POST …/run-solver/` | Low (already ~265 KB) |

### Tests

```text
test_lab_replay_get_content_encoding_gzip_when_accepted
test_lab_replay_get_json_semantically_unchanged_after_gzip
test_lab_replay_get_no_gzip_required_for_tiny_fixture
test_project_page_gzip_when_large_enough
```

Use `HTTP_ACCEPT_ENCODING="gzip"` on Django test client; assert `response.get("Content-Encoding") == "gzip"` and decoded JSON equals uncompressed fixture.

### Exit criteria

```text
[x] lab-replay/ returns Content-Encoding: gzip for capable clients
[x] JSON semantic equivalence preserved
[x] Clients without gzip Accept-Encoding still work
```

**Implementation plan:** [`docs/superpowers/plans/2026-05-29-replay-payload-13g-compression.md`](../plans/2026-05-29-replay-payload-13g-compression.md)

---

## PR-13E — Delta timeline contract (overview)

### Problem

13G shrinks wire size; **semantic** payload on GET remains ~15 MB due to repeated `full_map` per frame.

### Target wire shape

```json
{
  "schema": "lab_replay_timeline.delta.v1",
  "run_id": 295,
  "project_slug": "http-core-recovery-test-map",
  "frame_count": 86,
  "base_map": [ "... rows ..." ],
  "frames": [
    {
      "frame_index": 0,
      "delta": [],
      "phase": "...",
      "event_type": "...",
      "map_view": {},
      "inspector": {},
      "metrics": {},
      "cell_overlay_json": {}
    },
    {
      "frame_index": 1,
      "delta": [
        { "coord": [3, -10], "cell": { "x": 3, "y": -10, "...": "..." } }
      ]
    }
  ],
  "replay_track_metrics": { "...": "..." }
}
```

### Principles

```text
base_map once per timeline
+ per-frame delta (added/changed/removed cells — align with existing diff semantics where possible)
+ overlay / event metadata unchanged at frame level
```

### Compatibility layer

```text
Server emits delta timeline on GET (feature flag or Accept header v2)
↓
Client loader reconstructs legacy frame objects (full_map per frame in memory)
↓
Existing renderer / scrub / cell lookup unchanged
```

### Equivalence tests

```text
test_delta_get_reconstructs_same_frames_as_legacy_inline
test_delta_payload_smaller_than_legacy_for_fixture
test_scrub_each_index_visible_cells_match_legacy
test_overlay_and_inspector_metadata_unchanged
test_empty_timeline_delta_valid
```

**Implementation plan:** deferred until 13D + 13G land; separate spec amendment `2026-05-XX-lab-replay-delta-timeline-design.md` before coding.

---

## PR-13UI-guard — Run Solver single request (out of scope)

Observed duplicate `run-solver/` rows in Network tab (~265 KB each). Separate PR:

```text
test_run_solver_click_sends_single_request
test_run_solver_button_disabled_while_pending
```

Verify no form submit + fetch double path; guard already sets `disabled` — audit listeners and macro-only toggle.

---

## Document history

| Date | Change |
|------|--------|
| 2026-05-29 | Initial spec: 13D (approved + 6 amendments), 13G, 13E overview, PR order |
