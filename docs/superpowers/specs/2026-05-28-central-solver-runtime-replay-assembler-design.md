# Central Solver Runtime Replay Assembler — Authority Reunification — Design Spec

**Document type:** Asteroid Lab replay / timeline contract  
**Status:** **APPROVED (2026-05-28)** — Replay Contract Architect; blocking authority-reunification amendment  
**Work classification:** contract change · implementation change  
**Scope:** `django_apps/asteroid_lab/replay/` · `services/solver_runtime_layer02.py` · `services/lab_layer02_timeline.py` · `layers/layer_03_rim_mining_bundles/` · `layers/layer_04_rim_bundle_placement/` · `replay/event_types.py`  
**Extends:** [`asteroid_lab_09_replay_timeline.md`](../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md) · [`asteroid_lab_12_runtime_replay_wiring.md`](../../../documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md) · [`2026-05-28-layer-03-rim-mining-bundles-design.md`](2026-05-28-layer-03-rim-mining-bundles-design.md) · [`2026-05-28-layer-04-rim-bundle-placement-design.md`](2026-05-28-layer-04-rim-bundle-placement-design.md)

**Korean title (reference):** L2/L3/L4 분산 replay 권위 회수 · 중앙 `solver_runtime_replay_frames` 조립

**Supersedes (replay ownership only):** L4 design §4 “layer-local replay materialization” as **split authority** — frames MUST be emitted only via this spec’s central assembler after migration.

---

## §1 — Purpose and blocking contract

### 1.1 Problem statement

Lab product replay is a **single monotonic timeline** ([`asteroid_lab_09_replay_timeline.md`](../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md)). Today, solver-runtime segment authority is **split**:

| Split authority | Symptom |
|-----------------|--------|
| `services/lab_layer02_timeline.py` + `build_layer02_runtime_replay_frames()` | Runtime segment is **L2-only**; L3 progress never appears on timeline |
| `layers/layer_04_rim_bundle_placement/replay.py` | Layer package owns frame schema + `ReplayFrameAppendDTO` emission |
| `Layer04RimPlacementResult.replay_frames` | Implies layer owns runtime frame list (never wired to `config_json` in PR-3c, but contract encourages a third path) |

Layer 03 has no observability hook for the assembler; users see `algorithm_steps` / metrics in summary but **no L3 replay frames**.

### 1.2 Outcome (normative)

```text
This change REUNIFIES replay authority.

The existing L2-only runtime replay path and L4-local replay builder are split authority.
They MUST be migrated into django_apps/asteroid_lab/replay/ or reduced to compatibility wrappers
that delegate to the central package without duplicating frame logic.

Layer 03 MUST NOT introduce a third authority.
Layer 03 exposes observability snapshots only; the central assembler converts them to timeline frames.
```

### 1.3 Blocking contract — authority reunification (not forward-only)

```text
Blocking contract:

If replay authority is already split across services, layer packages, or runtime helpers,
this work MUST actively reunify it under django_apps/asteroid_lab/replay/.

This is NOT only a forward-looking prohibition.
Existing split authorities MUST be migrated, wrapped, deprecated, or deleted.
```

### 1.4 Single source of authority

```text
Authoritative package:
  django_apps/asteroid_lab/replay/

The replay package owns:
  - runtime replay assembly order (L2 → L3 → L4)
  - event type allowlist (SNAPSHOT_EVENT_TYPES)
  - ReplayTimelineFrame wire schema and JSON serialization for solver_runtime_replay_frames
  - layer segment projection (pure map/overlay builders)
  - JSON-serializable solver_runtime_replay_frames output

Layers own only:
  - algorithm result DTOs
  - Layer03ExpansionMetrics / Layer04 placement counts
  - observability snapshots (no ReplayTimelineFrame, no event_type strings as public layer API)

Layers MUST NOT own:
  - ReplayTimelineFrame construction in layers/**
  - event type registration outside replay/event_types.py
  - config_json["solver_runtime_replay_frames"] writes
  - runtime frame append order or per-layer parallel frame lists merged ad hoc in services
```

### 1.5 Forbidden (normative)

```text
MUST NOT add layers/layer_03/**/replay.py that persists or defines runtime frame schema
MUST NOT let layer_03/run.py or layer_04/run.py mutate SolverRun.config_json replay keys
MUST NOT let each layer append its own solver_runtime_replay_frames list
MUST NOT use replay / NDJSON / solver_summary as algorithm input (unchanged)
MUST NOT register event_type allowlist members outside replay/event_types.py
MUST NOT use ReplayFrameAppendDTO as the solver runtime frame schema owner
  (Lab ORM ReplayTrack append only)
```

### 1.6 Split-authority inventory and disposition

| Current location | Disposition |
|------------------|-------------|
| `services/lab_layer02_timeline.py` | Move L2 segment projection to `replay/layer02_segment.py`; services module becomes thin re-export or deleted after migration |
| `build_layer02_runtime_replay_frames()` | Deprecated wrapper → `build_solver_runtime_replay_frames(...)` |
| `layers/layer_04_rim_bundle_placement/replay.py` | Move logic to `replay/layer04_segment.py`; delete layer `replay.py` after tests migrate |
| `Layer04RimPlacementResult.replay_frames` | Deprecate in v1; remove field in v1.1; assembler reads placements + rejections only |
| `services/lab_replay_timeline_payload.py` | **Canonical composition entry** (unchanged role): Lab track + runtime segment → product timeline |
| `ReplayFrameAppendDTO` | **Lab ORM** append only; not solver runtime wire owner |

---

## §2 — Layer observability contracts (not frames)

### 2.1 Layer 03 — `Layer03Observability`

Path: `layers/contracts/layer03_observability.py` (or nested under `candidates.py` if small).

```python
@dataclass(frozen=True, slots=True)
class Layer03Observability:
    layer_slug: Literal["layer_03_rim_mining_bundles"]
    skip_reason: Layer03SkipReason
    rim_anchor_count: int
    route_probe_attempt_count: int
    route_probe_succeeded_count: int
    normal_candidate_count: int
    diagnostic_rejected_count: int
    reject_reason_counts: tuple[tuple[str, int], ...]
    top_normal_candidates: tuple[RouteProbedBundleCandidate, ...]
```

| Field | Rule |
|-------|------|
| `top_normal_candidates` | Deterministic top-N by pool ordering (same sort as normal pool display: intrinsic rank, anchor `(y,x)`, equivalence_key, candidate_id). **N = `LAYER03_REPLAY_TOP_N` = 8** (const in `replay/replay_limits.py`). |
| Metrics SoT | `Layer03ExpansionMetrics` remains authoritative for counts; observability duplicates only what the assembler needs for map projection without re-running expand. |

`RimBundleCandidateSet` gains:

```python
observability: Layer03Observability
```

Factory `build_rim_bundle_candidate_set(...)` MUST populate observability from expand results. **`replay_frames` field MUST NOT be added.**

### 2.2 Layer 04 — migration off `replay_frames`

v1 assembler reads:

- `selected_placements`
- `rejected_candidates` (overlap-only frames, same filter as today’s layer `replay.py`)
- `selected_count`, `rejected_overlap_count`

`replay_frames` on `Layer04RimPlacementResult` is **deprecated** (documented); callers MUST NOT append those DTOs to runtime config. Field removal is v1.1.

### 2.3 Layer 03 algorithm boundary (unchanged)

```text
Layer 3 MUST NOT use replay / NDJSON / solver_summary as algorithm input.
Observability is output-only and produced during expand, not read back from timeline.
```

---

## §3 — Runtime frame sequence (v1: milestone A + composite D)

Slug correction: Layer 4 is `layer_04_rim_bundle_placement` (not inner pattern fill).

### 3.1 Event types (register in `replay/event_types.py` + `ReplayEventType` where product wire requires)

**New Layer 03 (underscore wire, consistent with Layer 04):**

| Constant | Wire `event_type` |
|----------|-------------------|
| `EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_BEGIN` | `layer03_rim_bundle_scan_begin` |
| `EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_COMPLETE` | `layer03_rim_bundle_scan_complete` |
| `EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY` | `layer03_rim_bundle_pool_summary` |

**Existing Layer 02:** `exterior_transport.completed` (via `ReplayEventType.EXTERIOR_TRANSPORT_COMPLETED`)

**Existing Layer 04:** `layer04_rim_placement_begin`, `layer04_rim_candidate_selected`, `layer04_rim_candidate_rejected_overlap`, `layer04_rim_placement_complete`

All MUST appear in `SNAPSHOT_EVENT_TYPES`.

### 3.2 Ordered runtime segment (after Lab reconstruction track; monotonic append)

**L2 precondition:** Frame 1 is emitted **only when** `exterior_plan_wire` is a non-empty planning wire dict (solver produced an `ExteriorConnectionPlan`). See §3.3.

```text
1. exterior_transport.completed              # L2 — map + connector overlay (migrated from lab_layer02_timeline); OPTIONAL — see §3.3
2. layer03_rim_bundle_scan_begin           # L3 — renderable base (L1 complete or post-L2 source)
3. layer03_rim_bundle_scan_complete        # L3 — metrics + skip_reason
4. layer03_rim_bundle_pool_summary         # L3 — full map + top-N candidate overlay (mining, stub, path)
5. layer04_rim_placement_begin
6. layer04_rim_candidate_selected          # one per selected placement, stable sort order
7. layer04_rim_candidate_rejected_overlap  # overlap rejections only
8. layer04_rim_placement_complete
```

### 3.3 Hold / skip behavior

**L2 missing plan (normative):**

```text
If exterior_plan_wire is None, the assembler MUST NOT emit exterior_transport.completed.
It MAY still emit L3 begin/complete (and optional pool summary) frames against the
ReconstructionCompleteMap base with skip_reason=missing_exterior_connection_plan.
```

This prevents a “completed exterior transport” milestone when no L2 plan was produced.

| Condition | Frames emitted |
|-----------|----------------|
| `exterior_plan_wire is None` | **No** frame 1; 2–3 with `skip_reason=missing_exterior_connection_plan`; skip 4 or emit 4 with empty overlay + annotation |
| Empty seed catalog / no route goals | 2–3 with corresponding `Layer03SkipReason`; 4 optional empty summary |
| `budget_exhausted` | 3 reports `budget_exhausted`; 4 includes partial pool if `normal_candidates` non-empty |
| L4 hold (no plan or empty normal pool) | 5–8 with zero selections (same as current empty L4 result) |

### 3.4 Renderability (North Star)

Every frame in the runtime segment MUST satisfy `replay_map_view_is_renderable(map_view)` ([`timeline_dtos.py`](../../../django_apps/asteroid_lab/replay/timeline_dtos.py)): retain `full_cells` from reconstruction complete source for metadata-only milestones.

### 3.5 Deferred (not v1)

| Option | Status |
|--------|--------|
| B — one frame per normal candidate | **Deferred** — requires debug flag + hard cap |
| C — per-anchor × direction aggregates | **Deferred** — diagnostic follow-up |

### 3.6 Payload caps

| Cap | Value | Location |
|-----|-------|----------|
| L3 top-N candidates | 8 | `LAYER03_REPLAY_TOP_N` |
| Cells per frame | 2000 | `MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME` |
| L4 selected frames | all selected in v1; if count > `MAX_LAYER04_REPLAY_SELECTED` (32), truncate with `metrics.truncated_selected_replay=true` |
| Total composed timeline | 500 | `MAX_LAB_REPLAY_TIMELINE_FRAMES` via `compose_replay_timeline` |

---

## §4 — Central assembler API and file map

### 4.1 Entry point

Path: `django_apps/asteroid_lab/replay/solver_runtime_assembler.py`

```python
def build_solver_runtime_replay_frames(
    *,
    complete_map: ReconstructionCompleteMap,
    lab_frames_before_append: Sequence[Mapping[str, Any]],
    exterior_plan_wire: Mapping[str, Any] | None,
    layer03: RimBundleCandidateSet | None,
    layer04: Layer04RimPlacementResult | None,
) -> list[dict[str, Any]]:
    """JSON-serializable dicts for SolverRun.config_json[solver_runtime_replay_frames] only."""
```

**Ordering:** delegate to segment builders in fixed order; no layer package calls.

### 4.2 Segment modules (pure projection; no I/O)

| Module | Responsibility |
|--------|----------------|
| `replay/layer02_segment.py` | `exterior_transport.completed` frame (logic from `lab_layer02_timeline.py`) |
| `replay/layer03_segment.py` | L3 begin / complete / pool summary overlays |
| `replay/layer04_segment.py` | L4 begin / selected / overlap rejected / complete (logic from `layer_04/.../replay.py`) |

### 4.3 Runtime write path (single write)

```text
run_layer02_solver_for_project:
  layer03 = run_layer_03_rim_mining_bundles(...)
  layer04 = run_layer_04_rim_bundle_placement(...)
  runtime = build_solver_runtime_replay_frames(
      complete_map=layer01.complete_map,
      lab_frames_before_append=lab_serialized,
      exterior_plan_wire=plan_wire,
      layer03=layer03,
      layer04=layer04,
  )
  config_json[SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY] = runtime   # once

build_lab_replay_frames_for_project:
  lab_track frames + _solver_runtime_timeline_frames_for_run(run)   # unchanged entry
  compose_replay_timeline(...)
```

### 4.4 Compatibility wrapper

```python
def build_layer02_runtime_replay_frames(...) -> list[dict[str, Any]]:
    """Deprecated: use build_solver_runtime_replay_frames."""
    return build_solver_runtime_replay_frames(
        layer03=None,
        layer04=None,
        ...
    )
```

### 4.5 `ReplayFrameAppendDTO`

Remains in `services/dto.py` for **Lab ORM** `append_replay_frame`. Central assembler outputs **`ReplayTimelineFrame` → `replay_timeline_frame_to_json_dict`**, not `ReplayFrameAppendDTO`.

---

## §5 — Implementation tasks (normative order)

### Task 0 — Replay authority inventory

Grep and classify each hit:

- `solver_runtime_replay_frames`
- `replay_frames`
- `ReplayFrameAppendDTO`
- `build_*runtime_replay_frames`
- `layers/**/replay.py`
- `event_type` constants outside `replay/event_types.py`

Labels: `canonical_owner` | `segment_projection` | `deprecated_wrapper` | `forbidden_split_authority`

Deliverable: table in implementation plan (not necessarily committed as code).

### Task 1 — Central assembler first

- Create `replay/solver_runtime_assembler.py`
- Define L2→L3→L4 ordering
- Wire `solver_runtime_layer02.py` to single config write
- Register L3 event types

### Task 2 — Migrate split authority

- Move L2 construction → `replay/layer02_segment.py`
- Move L4 construction → `replay/layer04_segment.py`
- Delete `layers/layer_04_rim_bundle_placement/replay.py`
- Thin or remove duplicated logic in `lab_layer02_timeline.py` (re-export only if needed)

### Task 3 — Layer 03 observability

- Add `Layer03Observability` + factory population in `expand.py` / `build_rim_bundle_candidate_set`
- Implement `replay/layer03_segment.py`

### Task 4 — Forbidden import / authority gates (tests)

| Test | Assertion |
|------|-----------|
| `test_replay_authority_layers_no_timeline_frame_import` | `layers/**` does not import `ReplayTimelineFrame` |
| `test_replay_authority_layers_no_runtime_config_write` | AST or grep gate: no `solver_runtime_replay_frames` in `layers/**` |
| `test_replay_event_types_single_registry` | New L3/L4 runtime types ⊆ `SNAPSHOT_EVENT_TYPES` |
| `test_solver_runtime_replay_assembler_sequence` | Composed order includes L3 begin after L2 complete |
| `test_lab_replay_timeline_includes_layer03_after_solver_run` | Integration: `build_lab_replay_frames_for_project(..., solver_run_id=)` contains `layer03_rim_bundle_scan_begin` |

Migrate `test_build_layer04_replay_frames_*` → `test_layer04_segment_*` under `tests/unit/asteroid_lab/replay/`.

### Task 5 — Parent doc patches

- Amend [`2026-05-28-layer-04-rim-bundle-placement-design.md`](2026-05-28-layer-04-rim-bundle-placement-design.md) §1.1 / §4: replay emission is **central assembler**, not layer package
- Cross-link this spec from [`2026-05-28-layer-03-rim-mining-bundles-design.md`](2026-05-28-layer-03-rim-mining-bundles-design.md) §1.3

---

## §6 — Gates and risks

| Gate | Command (narrow first) |
|------|-------------------------|
| Replay unit | `python -m pytest tests/unit/asteroid_lab/replay/ -v` |
| Layer + runtime | `python -m pytest tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py -v` |
| Authority | `python -m pytest tests/unit/asteroid_lab/test_replay_authority_gates.py -v` |

| Risk | Mitigation |
|------|------------|
| Payload size (pool summary) | top-N=8 + cell cap + truncation metrics on frame |
| L4 test breakage | Move tests with segment module; keep wire metadata identical |
| Dual metrics drift | Counts in `Layer03ExpansionMetrics`; observability for projection only |
| PR size | Allowed split: Task 1–2 (reunify + L2/L4 migrate) then Task 3 (L3 observability) in one spec, two PRs optional |

---

## §7 — Approval record

| Item | Value |
|------|-------|
| Approach | **A** — central `replay/` assembler + layer observability |
| L3 replay unit v1 | **A + D** — begin/complete/summary + top-N composite overlay |
| Authority | **Reunification required** — not forward-only |
| L3 top-N | **8** |
| L4 selected cap | **32** then truncate with metric flag |

**Next step:** Implementation plan via `writing-plans` skill → `docs/superpowers/plans/2026-05-28-central-solver-runtime-replay-assembler.md`
