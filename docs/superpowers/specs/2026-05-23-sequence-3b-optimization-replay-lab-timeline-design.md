# Sequence 3B — RTTP Optimization Milestones in Lab Timeline (Design Spec)

**Status:** Approved 2026-05-23 (design review)  
**Owner:** asteroid-lab / RTTP Roadmap  
**Predecessors (merged):** PR-A/B RTTP v0.2 replay parity · H1 track isolation · H2 docs/test contract · UI frame counter 1-based display  
**Related:** [`2026-05-23-rttp-v0.2-replay-parity-design.md`](2026-05-23-rttp-v0.2-replay-parity-design.md) · [`asteroid_lab_09_replay_timeline.md`](../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md) · [`asteroid_lab_12_runtime_replay_wiring.md`](../../../documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md) · H1 integration `test_run_solver_lab_json_uses_inspection_not_rttp_optimization_track`

> **Naming:** `asteroid_lab_10` “Sequence 3B — Replay 최소 골격” is an **older** development-sequence label. **This document** is the **RTTP roadmap Sequence 3B** after v0.2: expose DB `{run_key}:rttp` milestone frames in Lab UI without breaking map replay.

---

## Purpose

After RTTP v0.2, four RTTP pipeline milestones are persisted on a dedicated ORM track (`{run_key}:rttp`). Lab JSON today exposes **decode/reconstruction map frames only** in `lab_replay_frames_json` (H1). Sequence 3B defines the **product contract** to show those milestones in Lab **UI-safely**:

```text
DB ReplayTrack {run_key}:rttp  →  read adapter  →  Lab Section B (metrics milestones)
Lab map timeline (Section A)   ←  unchanged compose path (inspection + runtime segment)
```

**Not in scope:** implementation PRs, map projection of milestones into Section A, per-candidate/per-probe dense frames, `rttp.*` wire types, or using replay rows as solver input.

---

## Current state (post v0.2)

| Layer | Behavior |
|-------|----------|
| **Write** | `DbRttpReplaySink` → `ReplayRecorder` on `track_key = rttp_optimization_track_key(run_key)` (`{run_key}:rttp`) |
| **Milestones (v0.2)** | `routing.probe_started`, `candidate.generated`, `ga.best_updated`, `routing.committed` — registered in `event_types.py` / `SNAPSHOT_EVENT_TYPES` |
| **Payload** | `cell_overlay_json` / `full_map` **empty** by design (orchestration-only recording) |
| **Lab compose** | `build_lab_replay_frames_for_project` skips RTTP tracks; `get_latest_lab_replay_track_for_project` excludes `:rttp` keys |
| **Run Solver JSON** | `lab_replay_frames_json` disjoint from RTTP milestone `event_type` set (H1 test) |
| **Phase 9 north star** | Single product replay timeline; every lifecycle step **eventually** 2D-renderable — **deferred** for RTTP v0.2 metrics-only milestones |

---

## Problem statement

```text
- Merging RTTP milestones into lab_replay_frames_json breaks map scrubber (no renderable map_view).
- Pretending milestones are reconstruction.map_complete poisons analytics and violates H1.
- Copying full_map onto RTTP frames hides the metrics-only nature and invites solver-input mistakes.
- Leaving milestones DB-only gives operators no Lab visibility after Run Solver.
```

Sequence 3B must add **visibility** without reviving **dual-track** (two map scrubbers, implicit index sync, HUD-only optimization track as a second replay product).

---

## Approach comparison

### A — Append RTTP milestones into `lab_replay_frames_json`

Append serialized RTTP `ReplayFrame` rows after reconstruction frames in the same array consumed by the map scrubber.

| Pros | Cons |
|------|------|
| One JSON field; no new UI entry point | **Breaks H1** (`lab_event_types` must stay disjoint from RTTP milestones) |
| Reuses `compose_replay_timeline` | Violates **2D-renderable** contract unless every milestone gets synthetic `map_view` |
| | Scrubber advances onto non-map frames → blank/broken grid |
| | Conflates `reconstruction.*` map semantics with solver orchestration events |
| | Regresses `test_build_lab_replay_diagnostic_when_only_rttp_orm_frames` expectations |

**Verdict:** Reject for 3B v0.

---

### B — Separate optimization milestone payload (recommended)

Keep `lab_replay_frames_json` as **Section A** (map timeline). Add a second read-only field **Section B** built only from `{run_key}:rttp` (and future optimization tracks using the same adapter).

| Pros | Cons |
|------|------|
| Preserves H1 and map scrubber invariants | Two arrays in page / Run Solver JSON |
| Metrics-only cards are **explicit** (no fake `map_view`) | Phase 9 wording needs a **documented amendment** (see § North star alignment) |
| Matches persistence split already shipped in PR-B | Lab JS must add a milestone panel (not a second scrubber) |
| Reuses output-only read patterns from 12G (lenient skip, diagnostics) | |
| Clear migration path to map projection later (Section A only) | |

**Verdict:** **Recommend** for 3B v0.

---

### C — Unified envelope with typed sections

Single top-level object, e.g. `lab_replay_timeline_json: { schema_version, sections: [{ kind: "map", frames: [...] }, { kind: "optimization_milestones", frames: [...] }] }`.

| Pros | Cons |
|------|------|
| One script tag / one contract version | Larger breaking change to SSR, Run Solver JSON, and tests |
| Extensible for future sections (validation, export) | Every consumer must understand `section.kind` |
| Avoids “two top-level keys” sprawl | Higher design/implementation cost than B for the same v0 UX |

**Verdict:** Good **3C+** evolution once Section B is stable; **not** 3B v0 unless we must version the whole timeline at once.

---

## Recommendation

**Adopt approach B** for Sequence 3B v0:

```text
Lab replay UX (one page, one map scrubber):
  Section A — lab_replay_frames_json          (map / decode / reconstruction)
  Section B — lab_optimization_milestone_frames_json   (RTTP milestones, metrics-only)

Persistence (unchanged):
  ORM ReplayTrack inspection/*  +  ORM ReplayTrack {run_key}:rttp
```

Optional later: wrap A+B in approach **C** envelope without changing section semantics.

---

## North star alignment (Phase 9 amendment)

[`asteroid_lab_09_replay_timeline.md`](../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md) remains the long-term target: **one monotonic `frame_index` story with 2D-renderable frames**.

**3B v0 amendment (explicit):**

| Rule | 3B v0 |
|------|--------|
| Product has **one Lab replay experience** | Yes — single page, **one map scrubber** |
| All lifecycle steps in **one JSON array** | **No** for RTTP milestones in v0 — Section B is separate |
| Metadata-only frames in **map** timeline | **Forbidden** (unchanged) |
| RTTP milestones visible in Lab | **Allowed** in Section B as **milestone cards** (metrics + inspector), not map frames |
| Future map projection | Milestones may later emit real `ReplayTimelineFrame` into Section A only; Section B may shrink or become inspector-only |

This is **not** a return to deprecated dual-track: no second scrubber, no `optimizationReplayFrameIndex`, no `replaceOptimizationReplayPayload` / `#lab-optimization-replay-status` revival.

---

## Decisions (3B v0)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Timeline merge | **Separate Section B field** | UI-safe; honors H1 |
| Payload | **Metrics-only milestone cards** | Matches v0.2 empty map recording |
| `event_type` | **Keep existing registered types** | `assert_registered_event_type`; no `rttp.*` in 3B v0 |
| UI | **“Optimization Milestones” panel** + inspector detail; map scrubber drives Section A only | Avoids dual-track sync |
| `map_view` on milestones | **Omit** (or explicit `render_mode: "none"` if schema requires the key) | Never empty object pretending to be renderable |
| Replay → solver | **Forbidden** | INV-OUTPUT-ONLY |
| `SolverRun.config_json["optimization_replay_frames"]` | **Unchanged** | Legacy shapez_asteroid path; not the RTTP ORM track |
| Track selection | Read `{run_key}:rttp` for **same** `run_key` as latest solver run (or explicit run picker later) | Matches PR-B persistence |

---

## Wire contract

### Section A (unchanged)

- **Key:** `lab_replay_frames_json`
- **Element:** `ReplayTimelineFrame` JSON (`map_view` required and renderable per `replay_map_view_is_renderable`)
- **Source:** `build_lab_replay_frames_for_project` — Lab inspection track + optional `solver_runtime_replay_frames` segment; **never** `:rttp` track

### Section B (new)

- **Key:** `lab_optimization_milestone_frames_json` (distinct from config_json `optimization_replay_frames`)
- **Track metrics key:** `lab_optimization_milestone_track_metrics` (parallel to `replay_track_metrics`)

**Per-frame shape (`OptimizationMilestoneFrame` v0):**

```json
{
  "frame_index": 0,
  "phase": "candidate_generation",
  "event_type": "candidate.generated",
  "title": "RTTP candidates generated",
  "description": "",
  "inspector": {},
  "metrics": {
    "normal_count": 3,
    "validation_passed": true
  }
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `frame_index` | yes | **Local** 0..n-1 within Section B for v0 (no global merge with Section A) |
| `phase` | yes | string; may include `rttp_pipeline` etc. from `SnapshotEventDTO` |
| `event_type` | yes | Must be registered; RTTP v0.2 set ⊆ `SNAPSHOT_EVENT_TYPES` |
| `title` | yes | Display |
| `description` | no | |
| `inspector` | yes | object; scalar summaries only |
| `metrics` | yes | object; includes commit/validation scalars on final milestone |
| `map_view` | **no** | Must not appear in v0 (or must not be renderable if present) |

**Section metadata (alongside array):**

```json
{
  "lab_optimization_milestone_frames_json": [ "... frames ..." ],
  "lab_optimization_milestone_track_metrics": {
    "track_key": "my-run:rttp",
    "frame_count": 4,
    "event_types": [
      "routing.probe_started",
      "candidate.generated",
      "ga.best_updated",
      "routing.committed"
    ],
    "replay_truncated": false,
    "truncation_reason": null,
    "dropped_frame_count": null,
    "diagnostic_reason": null,
    "source_solver_run_id": 123
  }
}
```

**Diagnostic codes (Section B only, mirror 12G style):**

| Code | When |
|------|------|
| `missing_optimization_milestone_track` | No `:rttp` track for run |
| `empty_optimization_milestone_frames` | Track exists, zero frames |
| `invalid_optimization_milestone_payload` | All frames failed validation |
| `optimization_milestone_track_filtered` | Reserved; lenient per-frame skip counts toward `dropped_frame_count` |

Empty Section B is **non-fatal** — Section A map replay still works.

---

## Read path (implementation sketch — not 3B scope)

```text
build_lab_optimization_milestone_frames_for_project(project_id, *, run_key=None)
  → resolve SolverRun + run_key
  → ReplayTrack.objects.get(track_key=rttp_optimization_track_key(run_key))
  → ordered ReplayFrame rows
  → map ORM payload → OptimizationMilestoneFrame
  → validate event_type ∈ SNAPSHOT_EVENT_TYPES (strict write already guaranteed)
  → return (frames_json, track_metrics)
```

**Call sites (future PRs):**

- `lab_page_context` / `asteroid_lab_page_context`
- `_lab_json_bundle_for_track_id` / Run Solver `entry_result_to_json_dict`
- Do **not** call from `compose_replay_timeline` or `run_rttp_pipeline`

---

## UI contract (3B v0)

| UI region | Data | Behavior |
|-----------|------|----------|
| Map + scrubber | Section A only | Existing `replaceLabReplayPayload` / frame index 1-based display |
| Optimization Milestones panel | Section B | Vertical step list or compact table: `title`, `event_type`, key `metrics` |
| Inspector | Selected milestone | Scalars from `inspector` + `metrics`; **no** map mutation |
| HUD truncation | Section A `replay_track_metrics` | Unchanged; Section B truncation independent |

**Forbidden UI behaviors:**

```text
- Second map scrubber for optimization
- Advancing map frame index when user selects a milestone
- Injecting milestone frames into lab_replay_frames_json on the client
- Reading milestone JSON in solver / Run Solver request body as algorithm input
```

---

## Invariants (v0 — normative)

```text
Sequence 3B v0 does not merge RTTP milestone frames into lab_replay_frames_json.
The map scrubber remains bound only to lab_replay_frames_json.

RTTP milestone frames are UI cards, not map frames.
They MUST NOT provide full_map, map_view, or reconstruction-compatible overlays in v0.
```

| ID | Rule |
|----|------|
| INV-3B-1 | `lab_replay_frames_json` event types ∩ RTTP milestone set = ∅ (H1 preserved) |
| INV-3B-2 | Section B frames must not be passed to map render pipeline |
| INV-3B-3 | Replay rows (Section A or B) are **output-only** — no reads in `optimization/`, candidate, commit, validation |
| INV-3B-4 | Do not copy `full_map` from reconstruction into RTTP ORM frames for display |
| INV-3B-5 | Do not register fake `reconstruction.map_complete` for RTTP milestones |
| INV-3B-6 | `event_type` strings remain registered constants; no free-text |
| INV-3B-7 | RTTP G8 parity unchanged — recording milestones must not alter `PipelineResult` |

---

## Phased delivery (post-spec)

| Phase | Scope | Gate |
|-------|--------|------|
| **3B-PR1** | Read adapter + page/Run Solver JSON fields + contract unit/integration tests | H1 test still green; new Section B populated when `:rttp` track exists |
| **3B-PR2** | Lab template + `asteroid_miner_layout_lab.js` milestone panel | Manual: map scrubber unaffected; milestones visible |
| **3B-future** | Map projection of selected milestones into Section A (`ReplayMapView` with `base_ref`) | Phase 9 long-term; separate spec |

---

## Test plan (contract-level)

| Test | Assert |
|------|--------|
| Extend H1 integration | `lab_optimization_milestone_frames_json` contains ≥4 frames; types ⊇ RTTP milestone set |
| H1 preserved | `lab_replay_frames_json` still disjoint from RTTP milestone types |
| `test_build_lab_replay_diagnostic_when_only_rttp_orm_frames` | Section A still empty + diagnostic; Section B non-empty when adapter wired |
| Malformed ORM row | Lenient skip; diagnostic only if all skipped |
| Architecture | `rg` — optimization pipeline does not read Section B builder |
| Static | Section B JSON schema rejects `map_view` with renderable cells in v0 |

---

## Non-goals (3B)

```text
- Append milestones into lab_replay_frames_json (approach A)
- rttp.* event_type namespace
- Per-candidate replay density
- NDJSON export
- Unifying with SolverRun.config_json optimization_replay_frames legacy list
- Reviving dual-track HUD/scrubber (12 deprecated paths)
- Changing RTTP pipeline hooks or DbRttpReplaySink write semantics
```

---

## Risks

| Risk | Mitigation |
|------|------------|
| Phase 9 doc reads as “one array only” | § North star alignment amendment; link from `asteroid_lab_09` in follow-up doc PR |
| Operators expect milestones on map | Panel copy + future projection track |
| `lab_optimization_milestone_frames_json` vs `optimization_replay_frames` name collision | Distinct key; document in `asteroid_lab_12` §2 cross-link |
| Two truncation stories | Independent `optimization_milestone_track_metrics` |
| `ga.best_updated` semantics | `title` + `metrics_json` document RTTP meaning (v0.2 precedent) |

---

## Open questions (defer to implementation plan)

1. Run picker: latest run only vs UI select prior `SolverRun` (default: **latest with `:rttp` track**).
2. Whether Run Solver POST returns Section B on validation failure (recommend: **yes**, same as Section A today).
3. i18n for milestone panel labels (v0: fixed EN/KO strings in JS const table).

---

## Approval gate

After review of this spec:

1. User approves design (or requests edits).
2. Invoke **writing-plans** → `docs/superpowers/plans/2026-05-23-sequence-3b-optimization-replay-lab-timeline.md`.
3. No implementation until plan + AGENTS.md workflow sign-off.

---

## References

- RTTP v0.2 milestones table: [`2026-05-23-rttp-v0.2-replay-parity-design.md`](2026-05-23-rttp-v0.2-replay-parity-design.md) §2  
- Track key: `django_apps/asteroid_lab/optimization/replay_track_keys.py`  
- Lab compose: `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`  
- H1 test: `tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py`
