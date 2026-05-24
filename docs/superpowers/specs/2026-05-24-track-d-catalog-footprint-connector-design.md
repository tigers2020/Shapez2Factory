# Track D — Catalog Footprint & Connector Slice (v2)

**Status:** Approved 2026-05-24 (post B2-T2/T3 on `master`)  
**Parent:** [`2026-05-24-building-catalog-slice-first-consumption-design.md`](2026-05-24-building-catalog-slice-first-consumption-design.md)  
**Plan:** [`2026-05-24-track-d-catalog-footprint-connector.md`](../plans/2026-05-24-track-d-catalog-footprint-connector.md)

## 1. Problem

`BuildingCatalogSlice` v1 carries transport registry and variant identity only. Game-data footprints and connectors exist on `BuildingSnapshot` but are invisible to RTTP. Track D adds **read-only catalog geometry** to the allowlist slice so later tracks can validate placement; this PR does **not** change candidate generation, macro, selection, or validation rules.

## 2. Success criterion

```text
catalog_slice_from_snapshot emits building_catalog_slice_v2 with per-variant footprint_cells and connectors.
catalog_slice_hash and provenance catalog_slice_version reflect v2.
RTTP runs fail-closed on hash/version mismatch (existing gates).
First consumption: output-only catalog footprint metrics on solver summary (no algorithm input from replay).
optimization/* still must not import BuildingSnapshot / raw game_data.
```

## 3. Scope

| In scope (D-v1) | Out of scope |
|-----------------|--------------|
| `SLICE_VERSION = building_catalog_slice_v2` | Macro compiler / macro E2E |
| `VariantGeometryCatalog` on slice | Candidate placement validation |
| `catalog_footprint_policy` lookup by `canonical_id` | Selection / fitness / regret |
| Hash + provenance version bump | Route-domain / probe changes |
| RTTP `algorithm_steps` metrics (counts only) | Replay → solver input |
| Domain docs + arch guards update | Connector-driven routing logic |

## 4. Slice shape

```python
SLICE_VERSION = "building_catalog_slice_v2"

@dataclass(frozen=True, slots=True)
class VariantGeometryCatalog:
    canonical_id: str
    internal_name: str
    footprint_cells: tuple[BuildingFootprintCell, ...]
    connectors: tuple[BuildingConnectorSnapshot, ...]

@dataclass(frozen=True, slots=True)
class BuildingCatalogSlice:
    slice_version: str
    transport_registry: tuple[TransportRegistryEntry, ...]
    variants: tuple[VariantIdentity, ...]
    variant_geometries: tuple[VariantGeometryCatalog, ...]
```

**Extraction:** `catalog_slice_from_snapshot` is the **only** function that reads `BuildingSnapshot.footprint_cells` / `connectors` for the slice. Footprint/connectors are copied with the same sort keys as `validate_building_snapshot` (`y, x, order_index` and `order_index`).

**Hash payload:** v1 fields plus `variant_geometries` array of `{canonical_id, internal_name, footprint_cells, connectors}` sorted by `(internal_name, canonical_id)`.

## 5. First consumption (output-only)

`catalog_footprint_policy.summarize_footprint_catalog(slice) -> dict[str, int]`:

- `catalog_variant_geometry_count`
- `catalog_footprint_cell_count` (sum of footprint cell counts)
- `catalog_connector_count`

Attached to existing RTTP pipeline summary under step `rttp.catalog_slice` (new step id) or merged into first pipeline step metrics — **metrics only**, not `OptimizationInput` fields.

## 6. Invariants

| ID | Rule |
|----|------|
| INV-D-01 | `catalog_slice_version` on new runs must be `building_catalog_slice_v2` |
| INV-D-02 | `catalog_slice_hash` includes geometry payload |
| INV-D-03 | `catalog_footprint_policy` does not import `game_data` |
| INV-D-04 | `optimization/*` must not import `BuildingFootprintCell`, `BuildingConnectorSnapshot`, `BuildingSnapshot` |
| INV-D-05 | No catalog geometry read inside macro/candidate/skeleton modules (arch test unchanged intent) |
| INV-D-06 | Reconstruction remains topology authority |

## 7. Self-review

| Check | Status |
|-------|--------|
| Narrow v1 (slice + policy + metrics only) | Pass |
| No macro/selection/validation changes | Pass |
| Provenance/hash contract bump explicit | Pass |
| Connectors stored but not consumed for routing | Pass (v1) |
