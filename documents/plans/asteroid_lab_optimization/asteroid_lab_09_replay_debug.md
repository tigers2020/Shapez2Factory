# Phase 9 — Replay and Debug Artifact


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_09_replay_debug.md`](../../Algorithm/asteroid_lab_09_replay_debug.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

> **Superseded narrative (dual-track):** If this doc treated **Lab replay and Optimization replay as separate tracks·independent `optimizationReplayFrameIndex`**, implementation authority is **Unified Lab Replay Timeline**. Optimization events append to `ReplayFrame` on the same `ReplayTrack`; front uses `lab-replay-frames-data` and single scrub index only. Details·forbidden symbol list: `rollback_baseline_lab_replay_timeline.md`.

## Purpose

Enable frame-by-frame viewing of the optimization process in the UI.

## Principles

Replay/debug artifact is output only.

```text
Not algorithm input.
```

## v0 scale·payload policy

Under Overview premise **「active coords roughly ≤50」**, keeping `visible_cells`·`overlay_cells` as **full snapshot** per frame is acceptable. In this range **delta frame compression·cell reference table·shared immutable snapshot** are **not required** (consider when scaling up v1+).

Instead prevent runaway via **document constants (override allowed in implementation but default fixed)**:

```text
MAX_REPLAY_CELLS_PER_FRAME = 128
MAX_REPLAY_FRAMES = 500
```

When `len(visible_cells)+len(overlay_cells) > MAX_REPLAY_CELLS_PER_FRAME`, truncate or summarize frame; when cumulative frames exceed `MAX_REPLAY_FRAMES`, stop recording subsequent events. Then put **`replay_truncated: true`** (and optionally `replay_omit_reason`) in `metrics`.

## Replay Event types

`event_type`: **free strings forbidden**. Fixed as `OptimizationReplayEventType` enum.

Strings below match **member value** or member name 1:1 (project picks one).

```python
class OptimizationReplayEventType(Enum):
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
```

## Frame Payload

```python
@dataclass(frozen=True)
class OptimizationReplayFrame:
    frame_index: int
    event_type: OptimizationReplayEventType
    title: str
    description: str
    visible_cells: tuple[CellDTO, ...]
    overlay_cells: tuple[OverlayCellDTO, ...]
    metrics: dict[str, Any]
```

`metrics` holds **scalar snapshots** needed for UI·debug. Recommended keys (doc contract, fixed as constants in implementation):

```text
reached_goal_kind (RouteGoalKind value)
goal_priority (int | null)
route_probe_failure_reason (RouteProbeFailureReason value | null)
candidate_reject_reason (CandidateRejectReason value | null)
fitness_total (float)
fitness_breakdown (FitnessBreakdown serialization or summary dict)
commit_conflict_reason (CommitConflictReason value | null)
evolution_convergence_reason (EvolutionConvergenceReason value | null)
route_reservation_id (str | null, same as Phase 7 reservation_id)
reservation_state (ReservationState value | null)
replay_truncated (bool, true when constant exceeded)
replay_omit_reason (str | null, optional)
```

**metrics are display·log only**; search loop must not read them as algorithm input.

## UI display goals

```text
candidate pool count
rejected candidate count
route probe success/failure (+ failure_reason / reached_goal_kind / goal_priority)
current generation
best fitness (+ fitness_breakdown summary)
selected bundle count
committed route count (+ reservation_id / reservation_state when applicable)
validation issue count (+ issue_code)
```

## Invariant

```text
[ ] replay frame is serializable
[ ] replay frame does not affect algorithm result
[ ] frame index is monotonic
[ ] event_type is OptimizationReplayEventType (free strings forbidden)
[ ] v0 constants MAX_REPLAY_* and replay_truncated behavior
[ ] same input·same seed: best genome·best fitness identical regardless of replay recording on/off (no side effects)
```

## Sequence 13A — POST JSON payload measurement·scale research (replay scalability research)

**Status:** measurement helpers·regression tests·this section recording complete. **Not immediate delta compression implementation stage.**

### Field evidence (browser / HAR)

```text
POST /asteroid-miner-layout/projects/ (Accept: application/json)
Response JSON body approx 22.6MB (Content-Length, HAR)
Chrome DevTools Response tab: "Request content was evicted from inspector cache"
```

UI lifecycle (11D)·HUD (12I) were normal; **center of problem is observable single JSON response size** and DevTools cache limit.

### Measurement (code)

- Test-only: ``measure_json_sections`` in ``tests/support/measure_json_sections.py`` — top-level key UTF-8 bytes (values only ``json.dumps``), ``lab_replay_frames_json`` / ``optimization_replay.frames`` frame counts·bytes per frame·``full_map`` length sum·optimization ``visible_cells``+``overlay_cells`` caps etc.
- Integration: ``test_post_projects_json_size_attribution_and_optimization_replay_hard_caps`` — Django test client analyzes POST response dict directly (does not depend on DevTools cache).

### Hard cap verification vs gap

| Policy | Applied at | Expected in POST response |
|------|-------------|---------------------|
| ``MAX_REPLAY_FRAMES`` = 500, ``MAX_REPLAY_CELLS_PER_FRAME`` = 128 | ``OptimizationReplayRecorder`` (optimization track recording) | ``optimization_replay.frames`` — frame count·cell sum caps verified by regression test |
| Same constants | Lab inspection ``ReplayFrame`` serialization path | **Not applied**. ``serialize_replay_frame`` / ``full_map`` are inspection pipeline output, separate from v0 optimization caps |

So **22MB-class bulk primary candidate is ``lab_replay_frames_json`` (large ``full_map`` per frame etc.)** plus **``optimization_replay``** in same POST. Optimization side has recorder caps; Lab side **grows linearly without separate truncation policy** on large maps.

### Reduction strategy candidates (priority·semantic risk)

1. **Lab replay frame truncation / sampling / summary mode** — semantic: full snapshot equivalence may weaken. Tests: existing inspection step contracts + UI timeline minimum set.
2. **Repeated full snapshot dedupe** — keyframes full·intermediate diff only etc. Semantic: client reconstruction rules must be documented. Tests: serialize·deserialize roundtrip.
3. **visible_cells / overlay_cells delta frame (optimization-side prototype)** — keep separate from Lab track. Semantic: shrink optimization only while maintaining dual-track·no implicit sync. Tests: cap·truncation metadata.
4. **gzip/Brotli transport** — body semantics unchanged; verify infra·client negotiation. Tests: Accept-Encoding + decode then existing JSON contract.
5. **Debug-only replay download endpoint separation** — lightweight POST body; semantic: separate PRG/form path and permissions. Tests: route·CSRF·size.

### Forbidden (13A scope)

```text
immediate delta replay implementation
binary replay format
solver / GA / commit / validation behavior change
implicit Lab vs optimization sync
using replay metrics as algorithm input
```

## Sequence 13B — Lab replay payload attribution / reduction design (not implementation)

**Status:** measurement extension·duplicate profile·cap gap documentation·13C candidate priority·regression key existence verification complete. **Does not reduce runtime POST payload or change semantics.**

### Measurement extension (test-only)

``measure_json_sections`` in ``tests/support/measure_json_sections.py`` adds Lab-only below (all deterministic on JSON ``sort_keys=True, separators=(",", ":")`` basis).

- **Size:** ``lab_total_bytes`` = UTF-8 bytes serializing only top-level key ``lab_replay_frames_json`` value (same as ``top_level_key_bytes["lab_replay_frames_json"]``). Distinct from per-frame sum ``sum_frame_bytes`` (bracket·comma overhead inclusion).
- **Cell counts:** ``lab_full_map_cell_count_{sum,max,avg}`` — aggregate ``len(full_map)`` per frame.
- **Top frames:** ``largest_lab_frames`` — top N by full frame dict serialization bytes descending (default 8); ``list_index``, ``frame_index``, ``frame_key``, ``bytes``.
- **Duplicate estimate (``redundancy``):**
  - ``adjacent_identical_full_map_count`` — count of adjacent frame pairs with identical sorted·normalized ``full_map`` serialization fingerprint.
  - ``cell_row_duplicate_instance_estimate`` — all frame ``full_map`` row instances − global unique row fingerprints (rises when same row payload repeats across frames).
  - ``coordinate_slots_with_multiple_instances`` — count of (x, y, layer) slots with two or more instances.
  - ``sum_full_map_json_bytes`` / ``sum_diff_body_json_bytes`` / ``sum_diff_added_len`` / ``sum_diff_removed_len`` — per-frame ``full_map``·``diff`` (top-level or ``frame_payload.diff``) size·length sums (observation only).

### Optimization hard caps vs Lab uncapped (gap reconfirmed)

| Policy | Optimization track | Lab ``lab_replay_frames_json`` |
|------|-------------------|-------------------------------|
| ``MAX_REPLAY_*`` | Applied at recorder·serialization path | **Not applied** (inspection / ``serialize_replay_frame`` path) |
| POST pressure | Frame·cell caps provide upper bound | **May grow linearly** with map·frame count |

Field observation (13A): single POST JSON ~22.6MB, DevTools response body eviction — this 13B measurement enables **Lab vs optimization contribution decomposition** repeatable in tests (no large golden file required).

### 13C implementation candidates (semantic risk·test hints, suggested priority)

1. **Debug-only full replay download / POST summary+current frame** — lightweight POST; permission·CSRF·PRG separation tests. Semantic: document which path UI treats as “authority source”.
2. **Lab frame truncation·sampling + explicit metrics** — semantic weakening risk; inspection step contract·timeline minimum set regression.
3. **Delta frames (document reconstruction rules)** — client restore invariant; frame N full snapshot equivalence tests.
4. **Cell row intern / dictionary** — if serialization-only change, UI identity·deserialize roundtrip tests.
5. **HTTP compression (Accept-Encoding)** — same body semantics; negotiation·decode then existing JSON contract tests.

### 13C (planned) semantic equivalence test design (checklist)

Verification to fix when implementing delta/compression later (maintain algorithm input forbidden principle):

```text
- reconstruct frame N == current full snapshot serialization result (or same DOM input hash)
- frame_index / event metadata order unchanged
- cell detail view·Lab timeline scrub behavior regression
- optimization input path does not read compressed replay
```

### Forbidden (13B scope)

```text
actual payload reduction (without cap bug proof)
binary format
solver / optimization behavior change
implicit Lab vs optimization sync
converting replay to algorithm input
committing large golden JSON
```

## Tests

```text
test_replay_frame_serializable
test_replay_frame_indices_monotonic
test_replay_events_do_not_affect_algorithm_result
test_replay_same_seed_on_off_identical_best_genome
test_replay_large_payload_truncation
test_replay_event_type_is_enum
```

## Completion criteria

```text
[ ] OptimizationReplayEventType enum + OptimizationReplayFrame implemented
[ ] optimization events recorded
[ ] timeline playback possible in UI
[ ] artifact/debug only invariant tests pass
```
