# RTTP Confirmed Placement Footprint — Design Spec

**Status:** Approved for implementation planning 2026-05-25  
**Owner:** asteroid-lab / solver-runtime-pipeline  
**Track:** Regression fix + Lab replay/UI contract (read-only projection)  
**Decision:** **C** — footprint visibility first; full island blueprint export is a follow-up track.

**Related (CANON / ACTIVE):**

- [`2026-05-22-rttp-hybrid-c-layout-design.md`](2026-05-22-rttp-hybrid-c-layout-design.md)
- [`documents/Algorithm/asteroid_lab_mining_installation/04_installation_guide.md`](../../../documents/Algorithm/asteroid_lab_mining_installation/04_installation_guide.md)
- [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md)
- [`documents/ai/lab_map_rendering_contract.md`](../../../documents/ai/lab_map_rendering_contract.md)

**Follow-up tracks (out of scope here):**

- PR-2: Catalog-backed miner island materializer → export/copy_code (`documents/samples/miner_code/`)
- PR-3: `ReconstructedAsteroidMap` vs solver artifact persistence split

---

## Problem

After RTTP `incremental_commit` succeeds, Lab replay shows **belts only** on optimization/commit frames. Users cannot see committed **extractor / extension** footprints; stats and map disagree with the mental model in [`04_installation_guide.md`](../../../documents/Algorithm/asteroid_lab_mining_installation/04_installation_guide.md) (commit-time confirmed placement).

**Root cause (code):**

1. K2 `placement_network_materializer` was removed with strip-solver; commit records `occupied_cells` in memory but does not project equipment into replay overlay.
2. `build_commit_replay_payload` emits only `route.committed_path` cells.
3. `build_selection_replay_payload` / `build_candidates_replay_payload` tag occupied footprint coords with `transport=shape_belt` (or `fluid_pipe`), so Lab JS `inferTransportSpriteIdentifier` draws **belt sprites on miner cells**.

Replay remains **output/debug only** — not export SoT, not algorithm input ([`asteroid_lab_00`](../../../documents/Algorithm/asteroid_lab_00_overview.md)).

---

## Goal (PR-1)

```text
incremental_commit result (unchanged)
  → read-only placement overlay projection
  → commit / selection / candidate replay payloads
  → Lab renders miner + extension sprites; route as belt/pipe
  → committed_count metrics align with visible miner anchors
```

**Non-goals (PR-1):**

| Item | Rationale |
|------|-----------|
| Nested island blueprint (`balanced_shape_miner.txt` / `omni_shape_miner.txt` full `B.Entries`) | PR-2 materializer |
| `ReconstructedAsteroidMap` overwritten with solver layout | PR-3 persistence |
| Route turn / merger / splitter tile synthesis | PR-1b visual follow-up |
| Changes to `incremental_commit`, route probe, selection, validation logic | Projection-only fix |

---

## Approved architecture

### Module

**Path:** `django_apps/asteroid_lab/optimization/materialization/placement_overlay_projection.py`

Pure functions only — no replay DB reads, no solver branching, no I/O.

**Import boundary (MUST):** This module is UI/replay projection-owned. It must **not** be imported by `incremental_commit`, route probe, selection, evolution, or validation modules. Only `rttp_replay_diagnostics` (and tests) may import it.

| Function | Purpose |
|----------|---------|
| `build_confirmed_placement_overlay_rows(...)` | Commit-success frames |
| `build_candidate_placement_overlay_rows(...)` | Candidate pool preview |
| `build_selected_placement_overlay_rows(...)` | Genome selection preview |

Shared internal helpers decompose `BundleCandidate` → per-cell rows. **Semantic labels are caller-supplied** (confirmed vs selected vs candidate).

### Layer boundary

```text
incremental_commit          → unchanged (committed_ids, reserved_route_cells)
placement_overlay_projection → new (Lab wire rows)
rttp_replay_diagnostics     → calls projector; merges rows into payloads
lab_rttp_snapshot_compose   → unchanged interleave; consumes overlay_cells
asteroid_miner_layout_lab.js → unchanged if wire contract is correct
```

---

## Lab wire contract (rendering SoT)

### Field roles

| Field | Role |
|-------|------|
| `cell_kind` | **Primary** Lab sprite source (`shape_miner`, `shape_miner_extension`, `space_belt`, `space_pipe`, field kinds unchanged) |
| `tile_type` | Sprite family / blueprint `T` (`Layout_ShapeMiner`, `SpaceBelt_Forward`, …) |
| `sprite_identifier` | Alias of `tile_type` when emitted (per [`lab_map_rendering_contract.md`](../../../documents/ai/lab_map_rendering_contract.md)) |
| `transport_kind` | Meaningful **only** for belt/pipe route channel cells |
| `overlay_semantic_kind` | Replay/debug semantics only — **not** renderer SoT |
| `placement_kind` | Optional metadata; renderer must not depend on it |

### Invariants (MUST)

```text
Miner / extension sprites must NEVER be inferred from transport_kind alone.
```

```text
Extractor and extension overlay rows MUST use transport_kind = "none".
```

```text
Candidate / selection frames MUST NOT use commit_state = "confirmed".
```

### Per-cell mapping

| Placement role | `cell_kind` | `tile_type` (v0) | `transport_kind` |
|----------------|-------------|------------------|------------------|
| Shape extractor | `shape_miner` | `Layout_ShapeMiner` | `none` |
| Shape extension | `shape_miner_extension` | `Layout_ShapeMinerExtension` | `none` |
| Fluid extractor | `fluid_miner` | `Layout_FluidMiner` | `none` |
| Fluid extension | `fluid_miner_extension` | `Layout_FluidMinerExtension` | `none` |
| Output stub | `space_belt` or `space_pipe` | `SpaceBelt_Forward` or `SpacePipe_Forward` | `shape_belt` or `fluid_pipe` |
| Committed route cell | `space_belt` or `space_pipe` | `SpaceBelt_Forward` or `SpacePipe_Forward` | channel from `TransportKind` |

### Rotation

Domain quarter-turn: **0 = East, 1 = South, 2 = West, 3 = North** ([`lab_map_rendering_contract.md`](../../../documents/ai/lab_map_rendering_contract.md)).

Map `CatalogPlacementRef.rotation` (`CardinalDirection`) → `rotation` int:

| Cardinal | `rotation` |
|----------|------------|
| E | 0 |
| S | 1 |
| W | 2 |
| N | 3 |

**Output stub** rows MUST include `rotation` derived from `candidate.output_dir` / catalog spec (not optional in v0).

Equipment (extractor + extensions) rows use the same bundle rotation as `catalog_placement_ref.rotation`.

### `overlay_semantic_kind` by frame (caller-assigned)

| Frame | Extractor | Extension | Fixed output transport | Output stub (probe start) | Route |
|-------|-----------|-----------|------------------------|---------------------------|-------|
| Candidate preview | `placement.candidate_extractor` | `placement.candidate_extension` | `placement.candidate_fixed_output_transport` | `placement.candidate_output_stub` | (existing probe kinds unchanged) |
| Genome selected | `placement.selected_extractor` | `placement.selected_extension` | `placement.selected_fixed_output_transport` | `placement.selected_output_stub` | — |
| Commit success | `placement.confirmed_extractor` | `placement.confirmed_extension` | `placement.confirmed_fixed_output_transport` | `placement.confirmed_output_stub` | `route.committed_path` |

See [`2026-05-27-rttp-miner-output-transport-topology-design.md`](2026-05-27-rttp-miner-output-transport-topology-design.md): FOT cell is belt/pipe only (transport priority), never extension equipment.

Optional wire fields: `candidate_id`, `commit_state`.

**`commit_state` policy (strict):**

```text
candidate / selection frames: MUST omit commit_state
commit-success placement rows: MAY set commit_state = "confirmed"
```

No other `commit_state` values in PR-1.

### Coordinate decomposition

Use `BundleCandidate.pattern`:

- `extractor_offset` translated by `anchor_coord` → extractor row
- Each `extension_offsets` entry → extension row
- `output_stub` → output stub row (not in `occupied_cells`)
- `reserved_route_cells` minus occupied ∪ {output_stub} → route rows

If `catalog_placement_ref` is missing, derive shape vs fluid from `candidate.transport_kind`.

---

## Visual v0 — transport tiles

### Output stub

`SpaceBelt_Forward` / `SpacePipe_Forward` with required `rotation` from output direction is **acceptable for PR-1**.

### Committed route

Using `Forward` for all committed route cells is **acceptable for PR-1** with this explicit limitation:

```text
Route tile_type synthesis is visual-v0 only.
PR-1 does not attempt turn / merger / splitter / junction reconstruction.
```

PR-1 goal:

```text
Belt path refinement: NO
Miner / extension footprint visibility: YES
```

**Follow-up:** PR-1b route segment tile synthesis (`prev` / `current` / `next` direction → Forward / Turn / Junction).

---

## Overlap handling

Invariants: extractor/extension coords should not overlap `output_stub` or route cells. Defensive rule for projection merge:

```text
On duplicate (x, y), keep higher-priority row:
  placement (extractor / extension) > output_stub > route
```

If extractor/extension coord overlaps `route.committed_path`, emit a **diagnostic warning** in `metrics_json` (do not fail-fast in PR-1). Do not silently drop placement rows.

**Overlap diagnostics (fixed location):**

```text
metrics_json.placement_route_overlap_warning_count
metrics_json.placement_route_overlap_warning_coords  # list of [x, y]
```

Human-readable summary may appear in payload `description` as supplementary text only.

---

## Integration points

### `rttp_replay_diagnostics.py`

- `build_commit_replay_payload`: merge `build_confirmed_placement_overlay_rows` for `commit_result.committed_ids` + existing route rows.
- `build_selection_replay_payload`: replace `genome.selected` + `transport=shape_belt` occupied overlay with `build_selected_placement_overlay_rows`.
- `build_candidates_replay_payload`: replace `candidate.bundle` transport-tagged occupied with `build_candidate_placement_overlay_rows` for normal candidates.

Stop using `overlay_cells_from_coords(..., transport=_transport_wire(...))` for equipment footprints.

### Metrics (observability)

Commit step `metrics_json` adds (from projector diagnostics):

```text
visible_miner_cell_count
visible_extension_cell_count
placement_route_overlap_warning_count
placement_route_overlap_warning_coords
```

Must not change throughput or `committed_ids` semantics.

---

## Verification (PR-1 tests)

| Test | Assert |
|------|--------|
| `test_commit_replay_includes_extractor_overlay_cells` | Committed bundle → `cell_kind=shape_miner`, `tile_type=Layout_ShapeMiner`, `transport_kind=none` |
| `test_commit_replay_includes_extension_overlay_cells` | Pattern with extensions → `shape_miner_extension` rows |
| `test_route_only_overlay_not_sole_confirmed_bundle_view` | Commit overlay has placement rows count ≥ committed extractor count |
| `test_selection_overlay_uses_miner_cell_kind_not_belt_transport` | Selected footprint: no `transport_kind=shape_belt` on miner coords |
| `test_candidate_overlay_semantic_not_confirmed` | Candidate/selection rows lack `commit_state=confirmed` |
| Extend `test_commit_payload_reports_validation_and_overlays_routes` | Still asserts `route.committed_path`; adds placement kinds |

Narrow gate:

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/optimization/materialization django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py
```

---

## PR roadmap

| PR | Scope |
|----|--------|
| **PR-1** (this spec) | `placement_overlay_projection.py` + replay payload wiring + unit tests |
| **PR-1b** (optional) | Route segment `tile_type` from path geometry |
| **PR-2** | Island blueprint materializer; variant policy (`shape_balance` / `shape_omni` / `fluid_default`) |
| **PR-3** | `SolverMaterializedLayout` / run artifact vs `ReconstructedAsteroidMap` |

---

## Approval record

```text
Approved for implementation planning (2026-05-25). Spec polish: import boundary, commit_state policy, overlap metrics_json location.

Scope:
- Add read-only placement overlay projection module.
- Wire commit / selection / candidate replay payloads to miner/extension cell_kind.
- Keep incremental_commit, export/copy_code, ReconstructedAsteroidMap unchanged.
- cell_kind + tile_type = Lab rendering contract; overlay_semantic_kind = replay metadata.
- SpaceBelt_Forward / SpacePipe_Forward visual-v0 with rotation; route synthesis deferred.
```
