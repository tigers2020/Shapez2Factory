# Sequence 3B-S — RTTP Full-Snapshot Interleaved Lab Replay (Design Spec)

**Status:** Approved 2026-05-23 (Replay Contract Architect review)  
**Owner:** asteroid-lab / RTTP replay contract  
**Supersedes:** [Sequence 3B-R inherited_snapshot tail append](../plans/2026-05-23-sequence-3b-r-unified-rttp-replay.md) (product behavior)  
**Predecessors (retained):** [RTTP v0.2 replay parity](2026-05-23-rttp-v0.2-replay-parity-design.md) · [asteroid_lab_09_replay_timeline.md](../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md)  
**Implementation plan:** [2026-05-23-sequence-3b-s-rttp-full-snapshot-replay.md](../plans/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay.md)

---

## Purpose

RTTP diagnostics must appear on the **single Lab product replay timeline** as **full `map_view` snapshot frames** interleaved with lifecycle frames — not as a second track, not as HUD-only milestones, and not via `render_mode: inherited_snapshot`.

This spec locks **Sequence 3B-S**: compose-time projection from the internal `{run_key}:rttp` write buffer into `lab_replay_frames_json`, preserving **RTTP-G8** (solver output unchanged when recording is on/off).

---

## Canonical product contract

```text
There is exactly one Lab replay timeline.
There is exactly one global frame_index sequence (0 .. N-1).
Every RTTP product frame is a full map_view snapshot frame.
RTTP frames are interleaved in the main replay (not tail-appended after reconstruction only).
render_mode: inherited_snapshot is invalid for RTTP product frames.
There is no second scrubber and no separate product replay track for RTTP.
RTTP frames use the same renderReplayFrame(frame) path as all other Lab replay frames.
```

**Final approval wording (2026-05-23):**

```text
Approved:
- A / compose-only projection for 3B-S-1
- :rttp remains internal write buffer only
- product output is one Lab timeline
- every RTTP product frame has concrete map_view.full_cells + overlay_cells
- no inherited_snapshot
- no tail-only milestone append
- no second scrubber
- PR-1 may derive full_cells from nearest prior renderable frame
```

---

## Persistence model: Product-single, storage-dual (transitional)

RTTP may be recorded into the existing `{run_key}:rttp` ORM `ReplayTrack` path as an **internal write buffer**. This storage path is **not** a product replay track and must not be exposed to the UI as a separate timeline.

**Hard rule:**

```text
The :rttp ReplayTrack is persistence plumbing only; it has no product semantics after compose.
```

| Allowed | Forbidden |
|---------|-----------|
| `run_rttp_pipeline` / solver runtime writes RTTP diagnostic rows to `:rttp` | UI exposes `:rttp` as a second scrubber or authoritative timeline |
| Compose projects `:rttp` rows into `lab_replay_frames_json` | RTTP product frame has empty `map_view` |
| `lab_optimization_milestone_frames_json` remains **diagnostic-only** (API compat) | UI reads milestone JSON as primary replay |
| | `render_mode: inherited_snapshot` on RTTP product frames |
| | Client-side map inheritance or sticky overlay layers |
| | Solver reads replay / `:rttp` rows as algorithm input |

**Why not strict single-track (B) now:** mixing recorder/storage refactor with replay-contract correction risks v0.2 parity regressions.

**Why not compose-only buffer (C) now:** heavier than needed; obscures audit trail while stabilizing post-3B-R behavior.

---

## Architecture

```text
run_rttp_pipeline ──writes──► ReplayTrack {run_key}:rttp  (write buffer)
                                      │
build_lab_replay_frames_for_project   │
  ├─ compose lab + runtime → base_timeline (serialized dicts)
  └─ interleave_rttp_snapshot_frames()  ──► lab_replay_frames_json
                                              │
Lab UI ◄── one scrubber, one frame_index ─────┘
         renderReplayFrame(frame)  (no RTTP-specific renderer)
```

During Lab replay composition, each `:rttp` row **MUST** be projected into the canonical Lab replay timeline as a normal frame dict with:

- globally assigned `frame_index` after interleave + renumber
- `map_view.full_cells` populated (concrete cells; see transitional PR-1 rule)
- `map_view.overlay_cells` populated for RTTP diagnostics when available
- `title` / `description` carrying human-readable debug explanation
- `metrics` carrying scalar inspection data only

`render_mode: inherited_snapshot` is **not valid** for RTTP frames after this sequence. Tail-appended RTTP milestone frames (3B-R) are superseded by interleaved full-snapshot RTTP frames.

---

## Frame contract (wire mapping)

| Conceptual | Repo canonical (`ReplayTimelineFrame` JSON) |
|------------|-----------------------------------------------|
| Base map snapshot | `map_view.full_cells` |
| RTTP diagnostic overlay | `map_view.overlay_cells` |
| Human debug prose | `description` (primary); `title` for scrubber label |
| Scalars | `metrics` only (not primary UI surface) |

### Invariants (H1-S)

```text
∀ frames in lab_replay_frames_json after compose:
  frame_index is continuous 0 .. N-1

∀ RTTP product frames (projected from :rttp):
  render_mode must not be "inherited_snapshot" (prefer absent)
  map_view.full_cells is non-empty (concrete snapshot materialized at compose)
  map_view.overlay_cells is a complete per-frame overlay snapshot
  overlay_cells must not inherit, persist, or carry forward from previous frames
  frame is renderable by renderReplayFrame(frame) — same path as all Lab frames
```

### Overlay cells (v0)

Use existing `ReplayOverlayCell` wire shape (`x`, `y`, `kind`, `transport`, …). Encode RTTP semantics in `kind` (e.g. `route_domain.blocked`, `probe.path`) until a dedicated `OverlayKind` StrEnum is added in 3B-S-3.

**Forbidden:**

```text
render_mode: inherited_snapshot
empty map_view with client-side base lookup
sticky / live overlay layer
RTTP-specific renderer or second scrubber
```

### Transitional PR-1 rule (compose-time projection, not inheritance)

```text
3B-S-1 may materialize RTTP full_cells from the nearest prior renderable Lab/runtime frame.
This is compose-time projection, not inherited_snapshot render mode.
The resulting RTTP product frame must contain concrete map_view.full_cells.
```

| Allowed | Forbidden |
|---------|-----------|
| Copy `full_cells` from nearest prior renderable frame into new RTTP frame during compose | `render_mode: inherited_snapshot` |
| Copy `overlay_cells` from `:rttp` `cell_overlay_json` when present | Empty `map_view` on product frame |
| | Client-side inheritance of map or overlay |

---

## Event types and interleave anchors

### PR-1 (3B-S-1): no new `RTTP_*` enum values

Keep existing milestone wire `event_type` strings on projected product frames:

| Write-buffer `event_type` | Typical `phase` |
|---------------------------|-----------------|
| `routing.probe_started` | `rttp_pipeline` |
| `candidate.generated` | `candidate_generation` |
| `ga.best_updated` | `genome_fitness` |
| `routing.committed` | `incremental_commit` |

Registered in `django_apps/asteroid_lab/replay/event_types.py` / `RTTP_MILESTONE_EVENT_TYPES`. Projected frames **must** still satisfy H1-S (full `map_view`).

### PR-2 / PR-3 (later)

- **3B-S-2:** enrich `:rttp` rows with real `cell_overlay_json`, `description`, finer lifecycle anchors at record time where parity-safe.
- **3B-S-3 (optional):** add canonical `rttp.*` values to `ReplayEventType` StrEnum; migrate projected frames and tests.

### Interleave anchor resolution (v0)

For each `:rttp` row (same `run_key` / solver run scope), insert after:

```text
1. nearest prior renderable lifecycle frame in the same run scope
2. fallback: after last reconstruction.completed in scope
3. final fallback: after last non-RTTP renderable frame before tail
```

**Renderable frame:** has non-empty `map_view.full_cells`, non-empty `cell_delta`, or non-empty `overlay_cells` (same predicate as `last_renderable_map_frame_index` today).

Within a run scope, multiple `:rttp` rows keep **monotonic order** by source `frame_index` on the `:rttp` track.

**Not valid after 3B-S:** append all RTTP milestones only after reconstruction prefix (3B-R tail).

---

## UI contract

- One scrubber: `#lab-timeline-scrub` over `lab_replay_frames_json` only.
- Map grid always derived from current frame’s `map_view` via `renderReplayFrame`.
- Inspector / description panel shows current frame `title`, `description`, `metrics`.
- No `rttp_replay_frames_json` (or equivalent) in page context as a product timeline.
- `lab_optimization_milestone_frames_json` may exist for diagnostics; Lab JS **must not** treat it as a second replay timeline (existing 3B Section B compat).

---

## Solver and parity gates

### RTTP-G8 (mandatory, unchanged)

```text
run_rttp_pipeline(..., replay_sink=on) must produce identical PipelineResult and
solver_summary scalars as replay_sink=off.
```

Recording and compose projection changes **must not** alter optimization outcomes.

### H1-S (new shape gate)

```text
lab_replay_frames_json:
  - no frame with render_mode == inherited_snapshot
  - every projected RTTP milestone frame has non-empty map_view.full_cells
  - RTTP milestone event_types are interleaved (not exclusively at tail after map-only prefix)
  - frame_index continuous 0 .. N-1
```

### Product exposure gate

```text
test_rttp_track_not_exposed_as_product_timeline:
  page context has one lab_replay_frames_json timeline
  no rttp_replay_frames_json
  no secondary replay payload exposed to UI as authoritative
```

---

## Module boundaries

| Module | Layer | Role |
|--------|-------|------|
| `optimization/replay_sink.py`, `pipeline.py` | write | Append to `:rttp` via `SnapshotEventDTO` (PR-1: minimal change) |
| `services/lab_rttp_snapshot_compose.py` (new) | compose | `project_rttp_row_to_timeline_frame`, `interleave_rttp_snapshot_frames` |
| `services/lab_replay_timeline_payload.py` | compose | Call interleave instead of `append_algorithm_frames_to_unified_lab_replay` |
| `services/lab_unified_replay_append.py` | deprecated path | Remove inherited_snapshot tail append for product RTTP |
| `services/lab_optimization_milestone_payload.py` | read | Diagnostic milestone cards only |
| `web/static/.../asteroid_miner_layout_lab.js` | UI | Remove inherited_snapshot render branch for product frames |

**Import boundary (unchanged):** `optimization/` must not import `lab_rttp_snapshot_compose`, `lab_replay_timeline_payload`, or ORM `ReplayFrame` for algorithm decisions.

---

## PR sequence

| PR | Scope |
|----|--------|
| **Spec** | This document; supersedes 3B-R inherited_snapshot **product** behavior |
| **3B-S-1** | Compose interleave, full map projection, H1-S + exposure tests, remove inherited_snapshot product path |
| **3B-S-2** | Enrich `:rttp` rows (overlays, descriptions, finer anchors at record time) | **Implemented** on `feat/sequence-3b-s-2-rttp-replay-enrichment` |
| **3B-S-3** | Optional: canonical `rttp.*` `ReplayEventType` values + migration |

---

## Supersedes (3B-R)

| 3B-R (obsolete product behavior) | 3B-S (canonical) |
|----------------------------------|------------------|
| Tail append via `append_algorithm_frames_to_unified_lab_replay` | Interleaved full-snapshot frames |
| `render_mode: inherited_snapshot` + empty `map_view` | Concrete `full_cells` + per-frame `overlay_cells` |
| H1-R “milestones only at tail with inherited_snapshot” | H1-S interleaved full frames |
| Milestones as non-map tail | Same `renderReplayFrame` as map frames |

ORM persistence on `{run_key}:rttp` **remains** as write buffer; only **product compose semantics** change.

---

## Non-goals (3B-S-1)

- Per-candidate dense probe frames on every commit attempt (3B-S-2+)
- New `rttp.*` enum values (3B-S-3)
- Merging `:rttp` track into inspection ORM track (future B)
- Using replay rows as solver input
- RTTP-specific CSS/renderer (only `overlay_kind` → class mapping extensions allowed)

---

## References

- [asteroid_lab_09_replay_timeline.md](../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md) — single timeline north star
- [2026-05-23-rttp-v0.2-replay-parity-design.md](2026-05-23-rttp-v0.2-replay-parity-design.md) — G8 parity
- [2026-05-23-sequence-3b-optimization-replay-lab-timeline-design.md](2026-05-23-sequence-3b-optimization-replay-lab-timeline-design.md) — Section B diagnostic (retained, not primary UI)

---

## Self-review

| Check | Status |
|-------|--------|
| Placeholder scan | No TBD |
| `:rttp` has no product semantics after compose | § Persistence |
| overlay snapshot non-sticky | § Frame contract |
| PR-1 full_cells transitional rule | § Frame contract |
| Anchor fallbacks (3-tier) | § Event types |
| No new enums in PR-1 | § Event types |
| RTTP-G8 + H1-S + exposure test | § Gates |
| Supersedes 3B-R clearly | § Supersedes |
