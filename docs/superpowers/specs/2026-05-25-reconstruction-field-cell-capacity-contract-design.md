# Reconstruction Field Cell Capacity Contract — Design Spec

**Date:** 2026-05-25  
**Status:** Approved (brainstorming 2026-05-25); **SoT amended 2026-05-26** — [`2026-05-26-reconstruction-complete-map-dto-design.md`](2026-05-26-reconstruction-complete-map-dto-design.md) is authoritative for map DTO and data flow; § Architecture / Data flow below **supersede** pre-2026-05-26 text  
**Implementation plan note:** [`2026-05-25-reconstruction-field-cell-capacity-contract.md`](../plans/2026-05-25-reconstruction-field-cell-capacity-contract.md) is **stale** until rewritten from the 2026-05-26 spec — do not implement `recon.cells` SoT steps from that plan without amendment  
**Supersedes (partial):** [`2026-05-24-reconstruction-max-throughput-pr2a-design.md`](2026-05-24-reconstruction-max-throughput-pr2a-design.md) — platform count and mineable definition only  
**Depends on:** PR-1 `MiningExtractionRule` · PR-2a Lab capacity envelope · PR-2b committed throughput · PR-2c/2d throughput target  
**Non-goals:** Route-feasible proof that all field cells can host simultaneous fully boosted bundles; replay-as-solver-input; changing CANON ×16 per logical bundle reference rates

---

## Problem

Reconstruction-complete product rule: **every reconstructed asteroid field cell is mineable and an installation slot** (one cell → one ×4 `throughput_factor` slot). Interior cells filled after void mis-detection (former pipes/buildings) are **asteroid fields**, not permanent void.

Current implementation splits three incompatible sets:

| Set | How computed today | Used for |
|-----|-------------------|----------|
| `display_cell_count` | Merged structural + recon map tiles | Lab footprint denominator |
| `mineable_cell_count` (legacy) | overlay / mask paths on `ReconstructionResult.cells` | **Withdrawn** for cap — see 2026-05-26 |
| `confirmed_cells` (mask) | Mask A/B on overlay fields | **Diagnostic only** — not cap SoT |

Result: e.g. **628** field tiles on the map but **32** in capacity `(N)` and theoretical max — rules appear tangled and contradict reconstruction-complete semantics.

**User decisions (locked):**

- **B:** Mineable = **asteroid field tiles only** (`asteroid_shape_field` / `asteroid_fluid_field`), **transport excluded** (belts, pipes, etc.).
- **A:** **Remove** `confirmed_cells` from capacity, placement domain, and theoretical max paths; mask/confidence are **quality/diagnostic only**.

---

## Canonical contract (single source of truth)

### Definition

> **Amendment (2026-05-26):** `asteroid_field_cell` must be taken from **`ReconstructionCompleteMap.cells`** (merged cleanup + overlay), **not** `ReconstructionResult.cells` (overlay only). See [2026-05-26 spec](2026-05-26-reconstruction-complete-map-dto-design.md).

```text
asteroid_field_cell :=
  coord in ReconstructionCompleteMap.cells where
  cell_kind ∈ { asteroid_shape_field, asteroid_fluid_field }

Includes:
  - decode-original fields
  - topology fill / inferred interior fill
  - synthetic reconstructed fields (_replay_synthetic)

Excludes:
  - shape_belt, fluid_pipe, space_pipe, and other transport tiles
  - walls, shell evidence-only cells not stamped as asteroid_*_field
  - external_void (not occupied field cells)
  - miners/extensions on overlay unless merged complete map stamps them as asteroid_*_field (via structural synthetic fields + overlay)
```

### Derived equalities (normative)

```text
asteroid_field_cells       := ReconstructionCompleteMap.field_cells
mineable_cells             := asteroid_field_cells
installation_slots         := asteroid_field_cells   # theoretical; one slot per cell at ×4
confirmed_cells (solver)   := asteroid_field_cells   # same coords; mask no longer shrinks solver set
ambiguous_cells (solver)   := ∅ for capacity/placement (mask may still populate for diagnostics)
```

### Throughput upper bound (per resource)

```text
max_throughput_per_min(resource) =
    count(asteroid_field_cells for resource)
    × output_per_min(active MiningExtractionRule, throughput_factor=4)

output_per_min(rule, 4) = rule.mini_unit_output_per_min × 4   # DB CANON row, not a literal constant

shape example (current seed): N_shape × get_active_rule("shape").mini_unit_output_per_min × 4
fluid example (current seed): N_fluid × get_active_rule("fluid").mini_unit_output_per_min × 4
```

`max_output_per_miner` (×16 fully boosted **logical bundle**) remains a **reference** field in JSON only; **must not** multiply platform count for terrain upper bound.

### What this does **not** mean

```text
installation_slots = mineable_cells
⇒ theoretical field capacity over all reconstructed field cells

does NOT imply:
⇒ N independent fully boosted extractor bundles are route-feasible or commit-valid
```

Committed throughput stays **RTTP route-confirmed** (PR-2b). Placement still subject to footprint overlap, output stub, trunk, transport separation, incremental commit conflicts.

### UI copy (English msgids; localize via gettext)

| Msgid | Meaning |
|-------|---------|
| `Theoretical field capacity: all reconstructed asteroid field cells × base extractor unit (×4)` | Cap card / disclaimer |
| `Committed throughput: route-confirmed extractor bundles only` | Unchanged PR-2a split |
| `Mineable footprint: {field_count} field cells / {display_cell_count} map cells` | Footprint card |

---

## Architecture (2026-05-26 — supersedes pre-amendment § below)

> **Withdrawn:** `ReconstructionResult.cells` → `asteroid_field_cells_from_reconstruction` → capacity / topology / `OptimizationInput`. That path counted **overlay only** and caused 32 vs hundreds field-cell drift.

### Factory + DTO (authoritative)

See [`2026-05-26-reconstruction-complete-map-dto-design.md`](2026-05-26-reconstruction-complete-map-dto-design.md).

```text
cleanup base map + ReconstructionResult overlay (ReconstructionResult.cells)
  → build_reconstruction_complete_map(cleanup, recon)
  → ReconstructionCompleteMap
       .cells          # complete merged map
       .field_cells    # asteroid_*_field coords
       .shape_field_cell_count / .fluid_field_cell_count
```

### `field_cells.py` public API

```python
def asteroid_field_cells_from_complete_map(
    complete_map: ReconstructionCompleteMap,
) -> frozenset[Coord]: ...

def count_asteroid_field_cells_by_resource(
    complete_map: ReconstructionCompleteMap,
) -> dict[str, int]: ...
```

**Rules:**

- **Never** pass `ReconstructionResult` to public field-count APIs for terrain SoT.
- Count by `cell_kind` on **`complete_map.cells`**, not `mineable_field_kind` miner inference.
- One coord per cell at `(x, y)` island-local frame.

### `ReconstructionResult.cells` (overlay only)

```text
ReconstructionResult.cells is reconstruction overlay, not complete terrain.
It must not be consumed as the terrain source for capacity, topology mineable cells,
or OptimizationInput.mineable_cells.
```

**Follow-up PR:** rename to `overlay_cells`. **Forbidden this PR:** assign merged complete map into `recon.cells` without migration.

### Consumers (must use `ReconstructionCompleteMap`)

| Consumer | Change |
|----------|--------|
| `solver_runtime_entry` | `complete_map = build_reconstruction_complete_map(cleanup, recon)` once |
| `reconstruction_capacity_summary` | `count_asteroid_field_cells_by_resource(complete_map)` |
| `build_reconstruction_observability` | `complete_map` field counts; `display_cell_count = len(complete_map.cells)` |
| `optimization_input_from_reconstruction` | `cleanup` required → `mineable_cells = complete_map.field_cells` |
| `acceptance_topology` | mineable / bbox from **`complete_map.cells`** (via factory-internal builder) |
| `apply_confidence_to_result` | diagnostic masks only; solver `confirmed_cells` aligned to **complete** field set at adapter boundary |
| Replay `reconstruction_final` / `step4_10` | same merge as factory (output-only; not read back as solver input) |
| Lab JS stat cards / detail | reads persisted summary built from **complete_map** |

### Forbidden

- Using `ReconstructionResult.cells` as complete map or cap numerator.
- Public `field_cells` / capacity / topology APIs taking `ReconstructionResult` for terrain SoT.
- Using `recon.confirmed_cells` (mask) for capacity or `OptimizationInput.mineable_cells`.
- Using `display_cell_count` alone as cap numerator (denominator / footprint only).
- Using `max_output_per_miner` (×16) for terrain upper bound totals.
- Reading replay `full_map` JSON into RTTP / optimization pipeline.

---

## Data flow (2026-05-26)

```text
reconstruct_snapshot / pipeline
  → ReconstructionResult (overlay in .cells; confidence diagnostics)
  → cleanup (structural base)
  → build_reconstruction_complete_map(cleanup, recon)
       → ReconstructionCompleteMap
            ├→ count_asteroid_field_cells_by_resource(complete_map)
            │     └→ build_reconstruction_capacity_envelope
            ├→ asteroid_field_cells_from_complete_map(complete_map)
            │     └→ optimization_input_from_reconstruction
            └→ build_reconstruction_observability(complete_map=...)

replay (output-only, same merge at reconstruction_final)
  → step4_10 full_map  (parity with complete_map.cells — not solver input)

solver run (persist)
  → reconstruction_capacity + observability in solver_summary
  → Lab stat cards / throughput_target percent (PR-2c uses recon max from complete map)
```

---

## JSON / Lab DTO changes

Per-resource capacity row (additive clarity):

```json
{
  "resource_kind": "shape",
  "capacity_upper_bound_platform_count": 628,
  "mini_units_per_confirmed_cell": 4,
  "capacity_upper_bound_mini_units": 2512,
  "output_per_confirmed_cell": "120.0000",
  "max_throughput_per_min": "75360.0000",
  "max_output_per_miner": "480.0000",
  "capacity_basis": "terrain_upper_bound",
  "authority": "MiningExtractionRule"
}
```

**Semantics:** `capacity_upper_bound_platform_count` means **field cell count** (installation slot count at ×4), not mask-confirmed subset. Prefer documenting in spec; optional follow-up rename to `capacity_upper_bound_field_cell_count` in a dedicated contract PR.

Observability (2026-05-26 keys):

```json
{
  "asteroid_field_cell_count": 628,
  "shape_field_cell_count": 628,
  "fluid_field_cell_count": 0,
  "ambiguous_cell_count": 0,
  "display_cell_count": 700
}
```

When `display_cell_count` includes transport tiles, footprint shows `628 / 700` style — **numerator is always field cells**.

---

## Confidence / quality (diagnostic only)

Keep `build_candidate_masks` / `merge_mask_agreement` **optional** for:

- `quality_tier`, `confidence_score`, `ambiguous_ratio` in `summary_json`
- Detail panel warnings

Do **not** write mask-derived subsets back into solver-facing `confirmed_cells` unless they equal `asteroid_field_cells` (normative: set equal at end of `apply_confidence_to_result`).

`reconstruction_acceptance_ok` may continue to use ambiguous ratio thresholds on diagnostics; failing acceptance must not shrink mineable set.

---

## Testing

| Test file | Coverage |
|-----------|----------|
| `test_complete_map.py` (new) | factory parity with merge + replay field_count; overlay ≪ complete on canon fixture |
| `test_field_cells.py` | **complete_map-only** public API; overlay count test-only |
| `test_reconstruction_capacity_summary.py` | N fields from **complete_map** → N×rate×4 |
| `test_reconstruction_topology.py` | external void from complete cells |
| `test_optimization_input_adapter.py` | `mineable_cells == complete_map.field_cells` |
| `test_reconstruction_fixture_contract.py` | update overlap assertions (field vs solved mineable) |
| `test_solver_run_lab_summary.py` | fixture throughput strings |
| integration Lab template smoke | footprint copy ids |

**Regression slug (manual):** after Run Solver, Resource Capacity `(N)` matches field tile count; Theoretical Max = N×120 for shape-primary island.

---

## Migration / compatibility

- Persisted `solver_summary` from old runs keeps stale 32-based caps until re-run — expected.
- PR-2c `target_throughput_per_min` rises when `reconstruction_max_throughput_per_min` rises — intentional.
- PR-2d `bundles_needed_for_target` may increase — intentional.

---

## PR-2a spec amendment

Replace platform-count paragraph in [`2026-05-24-reconstruction-max-throughput-pr2a-design.md`](2026-05-24-reconstruction-max-throughput-pr2a-design.md) § CANON rates with:

> **Superseded by** [`2026-05-25-reconstruction-field-cell-capacity-contract-design.md`](2026-05-25-reconstruction-field-cell-capacity-contract-design.md): platform count = asteroid field cell count; ×4 per cell; confirmed mask not used for cap.

---

## Implementation handoff

After **2026-05-26** spec approval: invoke **writing-plans** → new plan `docs/superpowers/plans/2026-05-26-reconstruction-complete-map-dto.md` (do **not** execute stale overlay-based steps in `2026-05-25-reconstruction-field-cell-capacity-contract.md` without rewriting).
