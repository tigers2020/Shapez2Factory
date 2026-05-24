# Phase 9 — Lab Replay Timeline

> **FIXTURE ENVELOPE SCHEMA ≠ RUNTIME PERSISTENCE SCHEMA**  
> Golden JSON (`tests/fixtures/shapez_asteroid/replay*`, `replay_summary`, top-level `truncation_reason`) is **regression and parser contract only**. Production persist and Lab UI use **frame `metrics` → track `metrics`** ([`asteroid_lab_12_runtime_replay_wiring.md`](asteroid_lab_12_runtime_replay_wiring.md) §6.1). Do not store `truncation_reason` at the top level of `SolverRun.config_json`.

**Status:** `ACTIVE` (product replay canonical)  
**Previous canonical:** [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md) — dual-track policy **deprecated**  
**Payload scale:** [`asteroid_lab_13_replay_payload_scalability.md`](asteroid_lab_13_replay_payload_scalability.md)  
**Runtime wiring:** [`asteroid_lab_12_runtime_replay_wiring.md`](asteroid_lab_12_runtime_replay_wiring.md)

---

## Naming (canonical terms)

| Layer | Canonical (EN) | Wire / identifier |
|------|-----------|----------------|
| Product | **Lab replay timeline** | `lab_replay_frames_json`, `lab-replay-frames-data`, single scrubber |
| Domain DTO | **Replay timeline frame** (`ReplayTimelineFrame`) | `frame_index`, `map_view`, `event_type`, `phase` |
| Composition | **Replay timeline composition** | `compose_replay_timeline` |
| Lab source | Lab ORM `ReplayTrack` / `ReplayFrame` | ORM as-is |
| Runtime source | Solver runtime replay segment | `solver_runtime_replay_frames` in `SolverRun.config_json` |
| **Deprecated** | dual-track, optimization replay (product), “unified replay” (UX/code prefix) | `optimization_replay*`, `optimizationReplayFrameIndex` |

Do **not** use **“unified replay” / `unified_*` symbols** in code, docs, or comments (migration complete).

---

## Purpose

Replays the **entire solver lifecycle** from blueprint import through final validation as **one 2D map replay timeline**.

```text
Blueprint Import
→ Decode
→ Reconstruction
→ Optimization Input
→ Candidate Generation
→ Route Probe
→ Genome / Fitness
→ Evolution
→ Incremental Commit / Rollback
→ Final Validation
→ Final Layout
```

All steps above register under the **same global `frame_index`**, and **every frame must render directly on the 2D map**.

---

## North Star

```text
There is exactly one product replay timeline.
Every solver lifecycle step that changes or observes the map must emit a 2D-renderable frame.
The replay timeline shows the complete story from blueprint decode to final validated layout.
```

---

## Deprecated (previous dual-track policy)

The statements and policies below are **no longer product goals.** Do **not** apply them in implementation, review, or test design.

```text
Deprecated:
The previous dual-track Lab replay / Optimization replay policy is obsolete.
The product replay model is now a single Lab replay timeline.
Optimization events must be projected into 2D map frames, not displayed as HUD-only metadata.
```

**Deprecated concrete policies:**

| Deprecated item | Reason |
|-----------|------|
| Lab replay authoritative / Optimization replay metadata only | Single timeline; optimization events promoted to map frames |
| Run Solver does not change Lab timeline | Entire lifecycle **appends to the same** timeline |
| Lab `frame_index` ↔ Optimization `frame_index` linking forbidden | **One** monotonic global index |
| Separate optimization play/scrubber/index | UI controller **one only** |
| 11A/11B as optional overlay | **Core** map projection · render pipeline (Sequence 9C–9E) |

Historical dual-track · 13A · 13B measurement detail: [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md) (archived · link preserved).

---

## Core Contract

| Invariant | Description |
|------|------|
| **One timeline** | Product UI owns **one** replay controller only |
| **2D-renderable frames** | Every frame has `map_view` (metadata-only frames forbidden) |
| **Phase, not track** | decode / route_probe / commit etc. are **`phase` markers**, not separate tracks |
| **Global monotonic index** | `frame_index` increases monotonically across the full lifecycle |
| **Output-only** | solver · GA · commit · validation **do not read** replay payload |
| **Inspector secondary** | HUD/inspector shows **selected frame description** only; map is primary |

```text
Replay is output-only.
The Lab replay timeline is an output-only artifact.
The solver must never read replay to decide the next step.
```

**Preserved:** replay on/off and recording must **not** affect best genome · best fitness · final layout under **identical input · identical seed**.

---

## DTO (canonical)

### `ReplayTimelineFrame`

```python
@dataclass(frozen=True)
class ReplayTimelineFrame:
    frame_index: int
    phase: ReplayPhase
    event_type: ReplayEventType
    title: str
    description: str
    map_view: ReplayMapView
    inspector: Mapping[str, Any]
    metrics: Mapping[str, Any]
```

- `inspector`: candidate id, cost, reject reason, fitness summary, etc. — **UI description** (algorithm input forbidden).
- `metrics`: scalar snapshots · truncation flags (display · log only).

### `ReplayMapView`

Every frame must represent the map via **at least one** of the following.

```text
base_ref (snapshot keyframe reference)
full_cells (full snapshot)
cell_delta (materialized cell changes)
overlay_cells (probe path, candidate bundle, highlight, etc.)
annotations (labels · failure reasons · goal markers)
bbox (camera / clip)
```

```python
@dataclass(frozen=True)
class ReplayMapView:
    base_ref: str | None
    full_cells: tuple[ReplayCell, ...]
    cell_delta: tuple[ReplayCellDelta, ...]
    overlay_cells: tuple[ReplayOverlayCell, ...]
    annotations: tuple[ReplayAnnotation, ...]
    bbox: BBox
```

**Insufficient example (not a product frame — HUD event only; must not register alone on timeline):**

```json
{
  "event_type": "genome.evaluated",
  "metrics": {"fitness_total": 12.5}
}
```

**Canonical frame example:**

```json
{
  "frame_index": 42,
  "phase": "route_probe",
  "event_type": "route_probe.succeeded",
  "title": "Route probe succeeded",
  "description": "Candidate cand_017 reached external margin.",
  "map_view": {
    "base_ref": "reconstruction_complete",
    "full_cells": [],
    "cell_delta": [],
    "overlay_cells": [
      {"x": 12, "y": 5, "kind": "route_probe_path", "transport": "shape_belt"},
      {"x": 13, "y": 5, "kind": "route_probe_path", "transport": "shape_belt"}
    ],
    "annotations": [
      {"x": 12, "y": 5, "label": "stub"},
      {"x": 20, "y": 5, "label": "external goal"}
    ],
    "bbox": {"min_x": 10, "min_y": 4, "max_x": 22, "max_y": 7}
  },
  "inspector": {
    "candidate_id": "cand_017",
    "cost": 8,
    "reached_goal_kind": "external_margin"
  },
  "metrics": {
    "reached_goal_kind": "external_margin",
    "goal_priority": 2
  }
}
```

### `ReplayPhase`

```python
class ReplayPhase(StrEnum):
    DECODE = "decode"
    RECONSTRUCTION = "reconstruction"
    OPTIMIZATION_INPUT = "optimization_input"
    PATTERN_GENERATION = "pattern_generation"
    CANDIDATE_GENERATION = "candidate_generation"
    ROUTE_PROBE = "route_probe"
    GENOME_FITNESS = "genome_fitness"
    EVOLUTION = "evolution"
    INCREMENTAL_COMMIT = "incremental_commit"
    ROLLBACK = "rollback"
    VALIDATION = "validation"
    RESULT = "result"
```

### `ReplayEventType`

`event_type` must **not** be a free-form string. Update enum · const and tests together.

**Lifecycle (decode ~ reconstruction):**

```text
decode.started | decode.completed
reconstruction.started | reconstruction.completed
optimization.input_loaded
```

**Optimization (existing optimization replay events — promoted to map frames):**

```python
class ReplayEventType(StrEnum):
    OPTIMIZATION_INPUT_LOADED = "optimization.input_loaded"
    PATTERN_GENERATED = "pattern.generated"
    CANDIDATE_GENERATED = "candidate.generated"
    CANDIDATE_REJECTED = "candidate.rejected"
    ROUTE_PROBE_SUCCEEDED = "route_probe.succeeded"
    ROUTE_PROBE_FAILED = "route_probe.failed"
    GENOME_GENERATED = "genome.generated"
    GENOME_EVALUATED = "genome.evaluated"
    GENERATION_COMPLETED = "generation.completed"
    BEST_GENOME_SELECTED = "best_genome.selected"
    ROUTE_COMMIT_ATTEMPTED = "route.commit_attempted"
    ROUTE_COMMITTED = "route.committed"
    ROUTE_ROLLED_BACK = "route.rolled_back"
    VALIDATION_COMPLETED = "validation.completed"
    VALIDATION_FAILED = "validation.failed"
    RESULT_LAYOUT = "result.layout"
```

**Backward compatibility:** During implementation transition, `OptimizationReplayEventType` value strings may keep the **same values** as above. Product DTO names unify as `ReplayEventType` / `ReplayTimelineFrame`.

---

## Frame Types

| Type | `map_view` pattern | Purpose |
|------|-----------------|------|
| **snapshot** | `full_cells` or `base_ref` + empty delta | decode/reconstruction complete, post-commit materialized state |
| **delta** | `cell_delta` | transport cell materialization, rollback removal |
| **overlay** | `base_ref` + `overlay_cells` | probe path, candidate bundle, genome highlight |
| **annotation** | overlay + `annotations` | reject reason, goal, validation issue |
| **synthetic checkpoint** | named `base_ref` only | keyframe on large maps; later delta/overlay references it |

---

## Solver Event → 2D Frame (promotion contract)

Optimization · solver internal events are recorded as `ReplayTimelineFrame`, **not** as observation-only logs.

| `event_type` | `phase` | `map_view` requirement |
|--------------|---------|-----------------|
| `candidate.generated` | `candidate_generation` | bundle occupied cells + output stub overlay |
| `candidate.rejected` | `candidate_generation` | failure location + `candidate_reject_reason` annotation |
| `route_probe.succeeded` | `route_probe` | probe path + reached goal marker |
| `route_probe.failed` | `route_probe` | expanded frontier / blocked area + failure annotation |
| `genome.evaluated` | `genome_fitness` | selected candidate set overlay; fitness in inspector/metrics |
| `best_genome.selected` | `genome_fitness` | best bundle set highlight |
| `route.commit_attempted` | `incremental_commit` | candidate + planned route preview overlay |
| `route.committed` | `incremental_commit` | `cell_delta` materializes transport cells |
| `route.rolled_back` | `rollback` | remove rollback target path or red-flash overlay |
| `validation.completed` | `validation` | final issues / passed markers |
| `validation.failed` | `validation` | issue cells + `issue_code` annotations |
| `result.layout` | `result` | final validated layout snapshot |

**Coordinates:** Server X/Y dense → Lab world projection runs **only** in Sequence 9C adapter. Algorithm layer does not read replay.

---

## UI Contract

**Single controller (Lab page):**

```text
#lab-timeline-play
#lab-timeline-slider
#lab-timeline-current-frame
```

| MUST | Description |
|------|------|
| One play / pause | Play full lifecycle |
| One scrubber | Move global `frame_index` only |
| One current frame label | `frame_index` + `phase` (+ optional `event_type`) |
| Map updates every frame | 2D grid **always** derived from `map_view` |
| Inspector / HUD | Show current frame `inspector` · `metrics` only |
| No second optimization timeline | Remove independent indices such as `optimizationReplayFrameIndex` (migration goal) |

**Phase UI:** Do not split the timeline; show segments via **phase markers** above the scrubber or in frame metadata.

---

## v0 scale · payload policy

Overview **「active coordinates ≤50 or so」** allows full snapshot per frame. Large maps follow [`asteroid_lab_13`](asteroid_lab_13_replay_payload_scalability.md) roadmap.

**Code constants (per track; canonical: `django_apps/asteroid_lab/replay/replay_limits.py`):**

| Constant | Value | Applies to |
|------|-----|------|
| `MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME` | 128 | optimization in-memory recorder (`visible_cells` + `overlay_cells`) |
| `MAX_OPTIMIZATION_REPLAY_FRAMES` | 500 | optimization recorder frame count |
| `MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME` | 2000 | Lab / unified adapter · composer (9B does not apply truncate) |
| `MAX_LAB_REPLAY_TIMELINE_FRAMES` | 500 | unified timeline target cap (9D composer) |

`MAX_REPLAY_*` in `optimization/replay_frame.py` is an **optimization track alias** (deprecated name).

On exceed: frame summarization · recording stop; `metrics.replay_truncated = true`, optional `replay_omit_reason`.

**Unified timeline (9D+):** When composer merges Lab · Optimization frames, apply the above caps **per track**. Per dual-track caps deprecated.

---

## Development Sequence (Phase 9)

Former Sequence 11A/11B (optional overlay) is **renumbered as core pipeline**.

| ID | Goal | Deliverable |
|----|------|------|
| **9A** | `ReplayTimelineFrame` DTO + enum + JSON serialization + contract unit tests | `django_apps/asteroid_lab/replay/timeline_*.py`, `replay_enums.py` |
| **9B** | Lab `ReplayFrame` / snapshot events → `ReplayTimelineFrame` adapter | `phase=decode` / `reconstruction`; 9D baseline |
| **9C** | Optimization events → 2D `map_view` adapter | **Done** — `optimization_unified_adapter.py` |
| **9D** | Timeline composer | **Done** — `timeline_composer.py` |
| **9E** | Single controller UI | **Done** — feature flag + `currentUnifiedFrameIndex` |
| **9F** | Commit frame materialization | `route.committed` → `cell_delta` |
| **9G** | Validation/result keyframes | `validation.*`, `result.layout` snapshots |
| **9H** | Payload scale strategy | Align with 13 series; lazy-load · delta under **same semantics** |

### 9A start conditions / forbidden

**Scope (9A only):**

```text
ReplayTimelineFrame, ReplayMapView, ReplayCell, ReplayCellDelta,
ReplayOverlayCell, ReplayAnnotation, ReplayPhase, ReplayEventType
+ JSON-safe serialization + invariant unit tests
```

**Forbidden (9A):**

```text
- JS controller changes (asteroid_miner_layout_lab.js)
- ReplayFrame ORM / migration changes
- Solver algorithm changes
- optimization_replay_persist structure changes
- payload lazy-load changes
- timeline composer (9D)
- using replay as algorithm input
- dual-track runtime removal (legacy code retained)
```

**Forbidden (9A–9H common):**

```text
using replay as solver / GA / commit / validation input
registering metadata-only frames alone on timeline
keeping a second optimization timeline controller (target state)
implicit Lab↔Optimization index sync (deprecated policy reintroduction)
```

### 9B — Lab adapter (implementation complete)

**Deliverables:** `django_apps/asteroid_lab/replay/lab_timeline_adapter.py`, `replay_event_coverage.py`, `replay_limits.py`

**Checklist:**

```text
[x] lab frame adapter (`lab_snapshot_event_to_timeline_frame`, `lab_replay_row_to_timeline_frame`)
[x] Lab frame_index → unified frame_index preserved (before 9D composer)
[x] phase mapping: decode → DECODE; reconstruction·layout_cleanup → RECONSTRUCTION
[x] event_type fixed mapping table (`LAB_EVENT_TYPE_TO_TIMELINE`)
[x] full_map → ReplayCell; bbox min_x/min_y/max_x/max_y
[x] inspector/metrics output-only passthrough (preserve `lab_event_type`, etc.)
[x] malformed / unsupported Lab frame → LabTimelineAdapterError
[x] no source mutation (unit tests)
[x] deterministic JSON round-trip
[x] ReplayEventType coverage matrix (9B / 9C / post-9B partition)
```

**Forbidden (9B):** optimization projection, delta compression, lazy-load, JS, ORM, persist, solver changes.

#### 9B Lab `event_type` → unified `ReplayEventType` (output)

| Lab `event_type` | Unified |
|------------------|---------|
| `decode.raw_loaded` | `decode.started` |
| `decode.normalized` | `decode.completed` |
| `reconstruction.begin` … `reconstruction.mineable_finalized` | `reconstruction.started` |
| `reconstruction.map_complete` | `reconstruction.completed` |
| `replay.snapshot.cleanup_*` / `replay.snapshot.reconstruction` | `reconstruction.started` (includes `layout_cleanup` phase) |

**9B rejects:** `candidate.*`, `routing.*`, `ga.*`, `existing_layout.*`

**Tests:** `tests/unit/asteroid_lab/test_lab_timeline_adapter.py`, `test_replay_event_coverage_matrix.py`, `test_replay_limits.py`

### 9C — Optimization adapter (implementation complete)

**Deliverables:** `django_apps/asteroid_lab/replay/optimization_unified_adapter.py`, `projection_context.py`, `replay_recording_cells.py`, `replay_event_coverage.SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER`

**Checklist:**

```text
[x] optimization frame adapter (`optimization_replay_frame_to_unified`)
[x] Island-local replay cells → Lab grid (`lab_xy_from_replay_cell`; PR-F: no `server_xy_params`)
[x] `visible_cells` → `map_view.full_cells`; `overlay_cells` → `overlay_cells`
[x] `REPLAY_EVENT_TYPE_TO_PHASE` (21 optimization event types)
[x] inspector `optimization_event_type` / `source_frame_index` preserved
[x] metrics annotation keys (`candidate_reject_reason`, `route_probe_failure_reason`, `reached_goal_kind` + coordinates)
[x] conservative renderable wrapping via `fallback_full_cells` / `base_ref`
[x] non-renderable → `OptimizationUnifiedAdapterError`
[x] no source mutation (unit tests)
[x] Runtime recorder: `visible_cell_dicts_from_loaded` / materialization overlay (output-only)
[x] coverage matrix: `SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER` (21)
[x] metadata-only frame: `fallback_full_cells_used` / `fallback_full_cells_reason` (presentation metrics)
```

**Projection ambiguity (9C, 9E implementers must read):**

```text
dense_x == 0 → raw_x == 0 is projection/intermediate display contract only;
do not equate with original blueprint raw X==0.
projection raw_x != original blueprint raw X
```

**Forbidden (9C):** timeline composer (9D), JS, ORM, `optimization_replay_persist` key changes, using replay as solver · GA · commit · validation input.

#### 9C `ReplayEventType` → `ReplayPhase` (summary)

| Group | `ReplayPhase` |
|------|----------------|
| `optimization.input_loaded`, `capacity.plan_created`, `route_goal.generated` | `optimization_input` |
| `pattern.generated` | `pattern_generation` |
| `candidate.*`, `candidate_pool.completed`, `candidate_selection.completed` | `candidate_generation` |
| `route_probe.*` | `route_probe` |
| `genome.*`, `best_genome.selected` | `genome_fitness` |
| `generation.completed` | `evolution` |
| `route.commit_*`, `route.materialized` | `incremental_commit` |
| `route.rolled_back` | `rollback` |
| `validation.*` | `validation` |
| `result.layout` | `result` |

**Tests:** `test_unified_replay_optimization_adapter.py`, `test_lab_rttp_snapshot_compose.py`, `test_solver_runtime_pipeline.py` (visible_cells)

**import:** `optimization_unified_adapter` is not re-exported from `replay/__init__.py` (avoids circular import with `optimization.replay_frame`). Callers import the submodule directly.

### 9D — Timeline composer (implementation complete)

**Deliverable:** `django_apps/asteroid_lab/replay/timeline_composer.py` — `compose_replay_timeline`

**Checklist:**

```text
[x] concat Lab unified frames → optimization unified frames in order
[x] reassign global `frame_index` 0..n-1
[x] preserve per-track original index in `inspector.source_frame_index`
[x] on `MAX_LAB_REPLAY_TIMELINE_FRAMES` exceed: keyframe+tail truncate + last frame `replay_truncated` / `truncation_reason` / `dropped_frame_count`
    - always retain: first RECONSTRUCTION_COMPLETED, last RESULT_LAYOUT
    - remaining slots: tail priority (most recent frames)
    - preserve chronological order
[x] no per-frame cell re-truncate (adapter responsibility)
```

**Forbidden (9D):** page context, JS, persist, dual-track removal (9E), algorithm input.

**Tests:** `test_timeline_composer.py` (includes `test_replay_head_truncate_retains_result_layout`, `test_replay_truncation_retains_first_reconstruction_keyframe`)

### 9E — Product replay single timeline (implementation complete)

**Deliverables:** `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`, `asteroid_lab_page_context.py`, `asteroid_miner_layout_solver.html`, `asteroid_miner_layout_lab.js`, `solver_runtime_entry.py`

**Scope:** replay **presentation only** — solver runtime A→M · candidate · commit · validation · `optimization_replay_persist` semantics **unchanged**.

**Product contract:**

```text
[x] product replay = `lab_replay_frames_json` (Lab ORM + persisted optimization, `ReplayTimelineFrame` JSON, includes `map_view`)
[x] `replay_track_metrics` — truncation · diagnostic (template `lab-replay-track-metrics-data`)
[x] Run Solver POST — `lab_replay_frames_json` + `replay_track_metrics` (`optimization_replay` removed)
[x] Replay Timeline single scrubber · `replayArrayIndex`
[x] `map_view` → Lab grid; truncation HUD · `lab-replay-run-status`
[x] Optimization Replay panel · `ASTEROID_LAB_UNIFIED_REPLAY_ENABLED` · dual-track page keys removed
```

**Forbidden (9E):** solver · persist writer · A→M changes, separate optimization scrubber, 9F/9G/13 lazy-load.

**Tests:** `test_lab_replay_timeline_payload.py`, `test_asteroid_lab_page_context.py`, `test_asteroid_run_solver.py`, `test_lab_js_replay_wiring_smoke`, `test_asteroid_lab_replay_timeline_smoke.py`

---

## Metrics (inspector secondary)

Recommended `metrics` keys (display · log only; not referenced by search loops):

```text
reached_goal_kind
goal_priority
route_probe_failure_reason
candidate_reject_reason
fitness_total
fitness_breakdown
commit_conflict_reason
evolution_convergence_reason
route_reservation_id
reservation_state
replay_truncated
truncation_reason
dropped_frame_count
replay_omit_reason
fallback_full_cells_used
fallback_full_cells_reason
```

---

## Invariants (checklist)

```text
[ ] ReplayTimelineFrame serializable
[ ] every frame has renderable map_view (≥1 of full_cells | cell_delta | overlay_cells or base_ref keyframe)
[ ] frame_index monotonic across full lifecycle
[ ] event_type ∈ ReplayEventType (free strings forbidden)
[ ] phase ∈ ReplayPhase
[ ] replay record on/off same seed → same best genome · fitness · final layout
[ ] scrubber controls replay timeline only (no second optimization controller)
[ ] HUD/inspector does not replace map render
[ ] v0 MAX_REPLAY_* and replay_truncated behavior
```

---

## Test Plan

| Test | Verifies |
|--------|------|
| `test_unified_replay_frame_serializable` | DTO round-trip |
| `test_unified_replay_frame_indices_monotonic` | global index |
| `test_every_frame_has_renderable_map_view` | map_view not empty (contract helper) |
| `test_replay_events_do_not_affect_algorithm_result` | output-only |
| `test_replay_same_seed_on_off_identical_best_genome` | no side effects |
| `test_unified_timeline_single_controller` | DOM/JS: no optimization-only scrubber (target) |
| `test_replay_large_payload_truncation` | MAX_REPLAY_* |
| `test_replay_event_type_is_enum` | rejects free strings |

Existing regression: `test_manual_snapshot_replay_not_used_as_algorithm_input_doc`, `test_lab_js_replay_wiring_smoke` — to be updated for **replay timeline** baseline.

---

## Related Documents

| Document | Relationship |
|------|------|
| [`asteroid_lab_13_replay_payload_scalability.md`](asteroid_lab_13_replay_payload_scalability.md) | POST size · lazy-load · delta (timeline **semantics** preserved) |
| [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md) | implementation order table — needs 9A–9H reflection |
| [`asteroid_lab_12_runtime_replay_wiring.md`](asteroid_lab_12_runtime_replay_wiring.md) | attach · diagnostic · runtime wiring |
| [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md) | **Deprecated** dual-track · 13A · 13B history |

---

## Completion criteria (product)

```text
[ ] ReplayTimelineFrame + ReplayMapView + ReplayPhase + ReplayEventType
[ ] Timeline composer emits single frames[] from decode → result
[ ] every optimization event has 2D map_view
[ ] UI single play/scrubber/current-frame
[ ] output-only invariant tests pass
[ ] asteroid_lab_09_replay_debug dual-track policy removed from code · docs or feature-flag off
```
