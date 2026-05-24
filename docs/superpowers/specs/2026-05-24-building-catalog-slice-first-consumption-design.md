# Track B2 — Building Catalog Slice First Consumption

**Status:** Approved 2026-05-24 (Principal Solver §1 + edits; T1 first swap)  
**Predecessor:** Track A — `GameDataSnapshotProvenance` ([`2026-05-24-game-data-snapshot-provenance-gate.md`](../plans/2026-05-24-game-data-snapshot-provenance-gate.md), PR #57)  
**Plan:** [`2026-05-24-building-catalog-slice-first-consumption.md`](../plans/2026-05-24-building-catalog-slice-first-consumption.md)  
**ADR:** [ADR-004](../../adr/ADR-004-game-data-snapshot-boundary.md) (B2 allowlist subsection required before B2-3 merge)

## Problem

`AsteroidGameDataSnapshot` v1 already carries `buildings` and `transport_registry`, but RTTP does not consume the snapshot body. Transport defaults come from reconstruction heuristics (`_default_transport_kind`). Track B2 introduces a **narrow allowlist slice** and the **first catalog consumption** without granting topology, placement geometry, throughput, or route-domain authority (Track D remains separate).

## Success criterion

```text
RTTP consumes BuildingCatalogSlice only for transport/variant identity lookup.
The first consumption is empty-map default TransportKind resolution from the catalog registry.
Reconstruction remains topology authority.
No footprint, connector, throughput, route-domain, macro, or candidate geometry authority is granted to catalog in B2.
```

## Non-goals (this track)

- T3: footprint / macro / candidate validation from catalog (deferred → Track D)
- Snapshot body as full algorithm input
- `SolverRun` DB columns for catalog fields
- Changing `content_hash` solver-subset scope (full snapshot hash unchanged)

## Architecture

```text
game_data ORM
  → web/services/asteroid_game_data_snapshot.py  (sole builder)
       → AsteroidGameDataSnapshot (full v1)
       → BuildingCatalogSlice (allowlist extract)
       → GameDataSnapshotProvenance v2 (10 wire keys incl. catalog_*)
  → solver_runtime_entry
       → validate provenance + catalog_slice_hash match
       → optimization_input_from_reconstruction(..., catalog_slice=...)
       → run_rttp_pipeline(OptimizationInput)   # topology still from reconstruction
```

## `BuildingCatalogSlice` (v1)

Frozen dataclass in `django_apps/asteroid_lab/contracts/building_catalog_slice.py`.

```python
SLICE_VERSION = "building_catalog_slice_v1"

@dataclass(frozen=True, slots=True)
class VariantIdentity:
    canonical_id: str
    internal_name: str

@dataclass(frozen=True, slots=True)
class BuildingCatalogSlice:
    slice_version: str  # SLICE_VERSION
    transport_registry: tuple[TransportRegistryEntry, ...]  # from game_data_snapshot contract
    variants: tuple[VariantIdentity, ...]
```

**Excluded from slice (by type):** footprint cells, connectors, placement metadata, presentation fields.

**Canonical ordering:**

| Collection | Sort key |
|------------|----------|
| `transport_registry` | `(transport_kind,)` |
| `variants` | `(internal_name, canonical_id)` |

**Extraction:** `catalog_slice_from_snapshot(snapshot: AsteroidGameDataSnapshot) -> BuildingCatalogSlice` — sole function that may read footprint/connectors on the full snapshot; output must not contain them.

## `catalog_slice_hash`

SHA-256 hex over canonical JSON (`sort_keys=True`, compact separators):

```json
{
  "slice_version": "building_catalog_slice_v1",
  "transport_registry": [ ... ],
  "variants": [ {"canonical_id": "...", "internal_name": "..."}, ... ]
}
```

- **`slice_version` is included** in the hash payload.
- Provenance/meta fields (`built_at_utc`, `import_batch_id`, `game_version`) are **excluded**.

Implementation: `catalog_slice_hash(slice: BuildingCatalogSlice) -> str` in `building_catalog_slice_hash.py` (or same module).

## Provenance wire v1 / v2

### v1 (historical — read-only)

Eight keys (Track A). Parser: `parse_provenance_config_v1` — exact key set, unknown keys rejected. Used only when reading **existing** `SolverRun` rows created before B2.

### v2 (required for new RTTP runs)

Ten keys — all v1 fields plus:

| Field | Constraint |
|-------|------------|
| `catalog_slice_version` | Must equal `building_catalog_slice_v1` |
| `catalog_slice_hash` | 64 lowercase hex chars |

Parser: `parse_provenance_config` (v2 strict) — **exactly** ten keys; unknown keys rejected.

**Writer:** `provenance_from_snapshot(snapshot, *, import_batch_id, catalog_slice)` computes v2 provenance. `provenance_to_config_dict` emits all ten keys.

**RTTP fail-closed:** New runs MUST persist v2. Missing `catalog_slice_*` → `PROVENANCE_INCOMPLETE` (or dedicated mismatch code below). v1 parse is **not** accepted for new writes or post-persist readback on B2-era entry.

### Reproducibility key (B2)

```text
(import_batch_id, snapshot_schema_version, content_hash, catalog_slice_version, catalog_slice_hash)
```

`built_at_utc` MUST NOT participate.

### Mismatch gates (entry, before pipeline)

| Condition | Error |
|-----------|--------|
| `provenance.catalog_slice_hash != catalog_slice_hash(slice)` | `CATALOG_SLICE_HASH_MISMATCH` |
| `provenance.content_hash != snapshot.meta.content_hash` | existing `ValueError` / `PROVENANCE_INCOMPLETE` |
| v2 fields missing on new run | `PROVENANCE_INCOMPLETE` |

## ADR-004 B2 allowlist (insert before B2-3 merge)

```text
Track B2 permits RTTP to consume the BuildingCatalogSlice only for transport registry
and building/variant identity lookup. This does not grant topology, placement geometry,
throughput, route-domain, or candidate-validation authority to the snapshot body.
Any expansion beyond this allowlist requires a new ADR or Track D approval.
```

## T1 — `resolve_default_asteroid_transport_kind`

Location: `django_apps/asteroid_lab/adapters/catalog_transport_policy.py` (no `game_data` import).

```python
class CatalogTransportUnresolvedError(Exception):
    code: CatalogTransportErrorCode  # StrEnum

class CatalogTransportErrorCode(StrEnum):
    CATALOG_TRANSPORT_UNRESOLVED = "catalog_transport_unresolved"
    AMBIGUOUS_DEFAULT = "ambiguous_default"
```

**Policy (documented, not tuple order):**

1. Classify each `TransportRegistryEntry.transport_category` via frozen map `TRANSPORT_CATEGORY_TO_KIND` (e.g. `"belt"` → `TransportKind.SHAPE_BELT`, `"pipe"` → `TransportKind.FLUID_PIPE`). Unknown category → entry skipped for default resolution.
2. Collect distinct `TransportKind` candidates among classified rows.
3. If `TransportKind.SHAPE_BELT` is among candidates → return `SHAPE_BELT` (asteroid greenfield default).
4. Else if exactly one distinct kind among candidates → return that kind.
5. Else → raise `CatalogTransportUnresolvedError(CATALOG_TRANSPORT_UNRESOLVED)`.

**RTTP path:** `optimization_input_from_reconstruction(..., catalog_slice=...)` when `existing_transport` is empty MUST call `resolve_default_asteroid_transport_kind(catalog_slice)` — **no** `_default_transport_kind` heuristic.

**Non-RTTP / unit tests:** When `catalog_slice is None`, legacy heuristic remains (documented test-only path); RTTP entry MUST NOT call adapter without slice.

## T2 — Per-cell transport resolution

RTTP resolves each reconstruction transport cell through `catalog_transport_policy.resolve_cell_transport_kind` (registry wire → `TransportKind`; domain enums pass through; fail-closed when unresolved). Duplicate registry keys with conflicting resolved kinds fail closed at lookup build; same-kind duplicates use deterministic last-wins. Policy API accepts optional `coord` for error messages (no adapter try/except re-wrap).

**Normative spec:** [`2026-05-24-b2-t2-per-cell-transport-resolution-design.md`](2026-05-24-b2-t2-per-cell-transport-resolution-design.md)

**Implementation plan:** [`2026-05-24-b2-t2-per-cell-transport-resolution.md`](../plans/2026-05-24-b2-t2-per-cell-transport-resolution.md)

**Next track:** [B2-T3 transport-aware route domain](2026-05-24-b2-t3-transport-aware-route-domain-design.md) — on `master` (distinct from footprint / Track D geometry).

## `OptimizationInput` extension

```python
catalog_slice: BuildingCatalogSlice | None = None
```

RTTP entry sets non-None slice after validation.

## Invariants

| ID | Rule |
|----|------|
| INV-CAT-01 | RTTP run: provenance v2 with both catalog fields |
| INV-CAT-02 | `catalog_slice_hash` includes `slice_version` |
| INV-CAT-03 | Entry verifies `catalog_slice_hash` before `create_solver_run` |
| INV-CAT-04 | `asteroid_lab` does not import `game_data` |
| INV-CAT-05 | `optimization/*` must not import `BuildingFootprintCell`, `BuildingConnectorSnapshot`, or `BuildingSnapshot` |
| INV-CAT-06 | No catalog read in macro/candidate/skeleton footprint modules (arch test) |

## Testing (summary)

| Test | Intent |
|------|--------|
| Slice hash stable across registry/variant order | determinism |
| v2 provenance round-trip + rejects v1 on strict parser | wire contract |
| `parse_provenance_config_v1` still parses historical fixtures | read path |
| T1 parity: empty map + fixture registry → `SHAPE_BELT` | matches old heuristic on imported batch |
| Unresolved registry → `CatalogTransportUnresolvedError` | fail-closed |
| Entry integration: hash mismatch → `CATALOG_SLICE_HASH_MISMATCH` | gate |
| Arch: optimization forbidden footprint imports | INV-CAT-05 |

## Phases (implementation)

| Phase | Deliverable |
|-------|-------------|
| B2-1 | Slice + hash + extract + v2 provenance + ADR draft |
| B2-2 | Entry wiring, `catalog_slice` on `OptimizationInput`, no behavior change |
| B2-3 | T1 consumption + error enums + fail-closed |
| B2-4 | ADR merge + domain docs + arch guards |

## References

- [`docs/domain/asteroid_game_data_snapshot.md`](../../domain/asteroid_game_data_snapshot.md)
- [`django_apps/asteroid_lab/optimization/reconstruction_adapter.py`](../../../django_apps/asteroid_lab/optimization/reconstruction_adapter.py)
- [`django_apps/asteroid_lab/adapters/game_data_snapshot_adapter.py`](../../../django_apps/asteroid_lab/adapters/game_data_snapshot_adapter.py)
