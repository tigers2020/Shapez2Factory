# Asteroid Lab — `game_data` consumer snapshot

**Owner:** Dominic (domain) · **Consumers:** `asteroid_lab.contracts.game_data_snapshot`, `web.services.asteroid_game_data_snapshot`  
**Status:** Phase 0 domain contract (v0)  
**ADR:** [ADR-004: game_data snapshot boundary](../adr/ADR-004-game-data-snapshot-boundary.md)

## Purpose

`AsteroidGameDataSnapshot` is the immutable, revision-pinned contract between normalized `game_data` ORM rows and the Asteroid Lab solver adapter. It carries **solver-relevant** building geometry and transport registry facts only. Presentation metadata (sprites, display keys, toolbar icons) stays out of this snapshot until a separate `PresentationSnapshot` is specified (see ADR-004 consequences).

Build path (v0):

1. `game_data` selectors + `snapshots/builder` materialize ordered row tuples (ORM stays here).
2. `web/services/asteroid_game_data_snapshot.py` assembles frozen consumer DTOs.
3. `asteroid_lab/adapters/game_data_snapshot_adapter.py` maps DTOs to solver enums (no `game_data` import).

## Top-level shape

```python
@dataclass(frozen=True, slots=True)
class AsteroidGameDataSnapshot:
    meta: SnapshotMeta
    buildings: tuple[BuildingSnapshot, ...]
    transport_registry: tuple[TransportRegistryEntry, ...]
```

| Field | Type | Role |
|-------|------|------|
| `meta` | `SnapshotMeta` | Revision pin, provenance, deterministic `content_hash` |
| `buildings` | `tuple[BuildingSnapshot, ...]` | Per-variant footprint + connectors (canonical order) |
| `transport_registry` | `tuple[TransportRegistryEntry, ...]` | Transport kind → building variant mapping |

Nested collections inside each `BuildingSnapshot` are also **`tuple`**, never `list`, `set`, or `frozenset` (see **Collection policy** below).

## Canonical ordering (total order)

Every collection below is sorted by its sort key **before** the snapshot is considered valid. Sort keys define a **total order**; ties are broken by the next key in the tuple. No placeholder keys — these are the v0 contract.

| Collection | Sort key (total order) |
|------------|------------------------|
| `buildings` | `(internal_name, canonical_id)` |
| `footprint_cells` per building | `(y, x, order_index)` — **game-local** Y/X, not server/world coords |
| `connectors` per building | `(order_index,)` |
| `transport_registry` rows | `(transport_kind,)` |

### Footprint coordinates

- `x`, `y` on `BuildingFootprintCell` are **building-local** offsets (same frame as `game_data` footprint import).
- Server/world placement applies later in the adapter via `coord_transform` (see [`asteroid_coord_transform_spec.md`](asteroid_coord_transform_spec.md)).
- `order_index` is the tie-breaker when two cells share the same `(y, x)`; it must remain stable across imports for a given variant.

### Validation

- `asteroid_lab.contracts.game_data_snapshot` validation may reorder nested tuples to match the keys above; the returned snapshot must already satisfy these orders at the assembler boundary.
- Input order of buildings or child rows must **not** affect `content_hash` after canonicalization.

## `SnapshotMeta` (minimum fields)

Frozen dataclass spec for provenance and solver-run pinning. Implement in `django_apps/asteroid_lab/contracts/game_data_snapshot.py`.

```python
@dataclass(frozen=True, slots=True)
class SnapshotMeta:
    schema_version: str          # "game_data_snapshot_v1"
    data_revision: str           # ImportBatch.manifest_self_hash
    db_alias: str                # "default"
    built_at_utc: str            # ISO-8601 Z
    content_hash: str            # sha256 canonical JSON of solver subset
    game_version: str            # from ImportBatch
    rule_version: str            # "asteroid_v0" — throughput allowlist gate
```

| Field | Source / constraint |
|-------|---------------------|
| `schema_version` | Constant `game_data_snapshot_v1` |
| `data_revision` | `ImportBatch.manifest_self_hash` of the pinned batch used for the build |
| `db_alias` | v0: `"default"` only; replica reads forbidden until ADR-004 is extended |
| `built_at_utc` | UTC build timestamp, ISO-8601 with `Z` suffix (e.g. `2026-05-21T12:00:00Z`) |
| `content_hash` | SHA-256 hex of canonical JSON over the **solver subset** (see below) |
| `game_version` | `ImportBatch.game_version` |
| `rule_version` | Constant `asteroid_v0` (throughput / transport allowlist gate for adapter) |

Constants (implementation):

- `SCHEMA_VERSION = "game_data_snapshot_v1"`
- `RULE_VERSION = "asteroid_v0"`

v0 note: snapshot **body** must not become algorithm input until a separate PatternLibrary / solver-input ADR approves it. Run **provenance** (below) is required on every RTTP `SolverRun`.

## `GameDataSnapshotProvenance` (Track A)

Frozen contract: `django_apps/asteroid_lab/contracts/game_data_snapshot_provenance.py`.

| Field | Role |
|-------|------|
| `snapshot_schema_version` | DTO wire schema (`game_data_snapshot_v1`) |
| `rule_version` | Adapter gate (`asteroid_v0`) |
| `data_revision` | `ImportBatch.manifest_self_hash` (content identity across DB rebuilds) |
| `import_batch_id` | DB join key (positive int; wire as decimal string in JSON) |
| `content_hash` | Solver-subset SHA-256 hex (64 chars) — see **`content_hash` scope** |
| `game_version` | From pinned import batch |
| `db_alias` | v0 `"default"` |
| `built_at_utc` | Audit timestamp only — **excluded** from reproducibility key |

**Wire key:** `SolverRun.config_json["game_data_snapshot_provenance"]`. Unknown keys inside the object are rejected at parse time.

**Writer ownership:** Only `web/services/asteroid_game_data_snapshot.py` builds snapshot+provenance (single `pin_latest_import_batch` per build). `solver_runtime_entry` persists and validates; optimization code must not import `game_data`.

**Reproducibility key:** `(import_batch_id, snapshot_schema_version, content_hash)`.

## Collection policy — `tuple` only

| Allowed | Forbidden on consumer DTO path |
|---------|--------------------------------|
| `tuple[...]` | `list`, `dict` (nested), `set`, **`frozenset`** |

**`frozenset` must not be used** as the canonical collection type for snapshot data. Unordered sets cannot define a stable total order for hashing or replay. Use sorted `tuple` everywhere a collection is needed.

## `content_hash` scope

`content_hash` is the SHA-256 digest (hex) of **canonical JSON** (`sort_keys=True`, compact separators) over the **solver-relevant subset** of the snapshot body. It is **not** `ImportBatch.manifest_self_hash` (`data_revision`) and **not** a full `game_data` dump hash.

### Included (solver subset)

- **`buildings`:** `canonical_id`, `internal_name`, `footprint_cells` (`x`, `y`, `order_index`), `connectors` (all connector fields carried in `BuildingConnectorSnapshot`: role, directions, IO channel, local positions).
- **`transport_registry`:** `transport_kind`, `transport_category`, `building_variant_canonical_id`.

Rows must appear in the canonical orders defined above before hashing.

### Excluded (presentation and non-solver)

- Any field not mapped into the consumer DTOs (e.g. `display_name_key`, `icon_sprite_name`, sprite/static asset paths, toolbar labels, `source_row_index`, import audit blobs).
- **`SnapshotMeta` itself** is not part of the hash payload (including `content_hash`, `built_at_utc`, and `data_revision` — revision is carried explicitly in `data_revision`).
- Presentation-only ORM columns on `BuildingVariant`, groups, assets, and toolbar tables.

Implementation: `game_data_snapshot_hash.snapshot_content_hash` walks explicit tuples (no `dataclasses.asdict` deep copy). Same logical DB rows → same `content_hash` after canonical ordering.

## Malformed row policy — fail-fast

At **snapshot build** time (selector row fetch, row tuple materialization, and web assembly):

| Policy | Detail |
|--------|--------|
| **Fail-fast** | First invalid or inconsistent row aborts the entire build |
| **No partial snapshot** | Do not emit a snapshot with some buildings omitted |
| **No `raw_json` fallback** | Never hydrate missing normalized fields from raw import JSON |
| **Error surface** | Raise `SnapshotBuildError` (or equivalent) with a stable issue code; no silent skip |

Examples of build-time failures: missing import batch, orphan footprint/connector row, duplicate sort-key collision after normalization, type mismatch (e.g. `list` instead of `tuple`), unknown transport kind when adapter policy requires exhaustive mapping.

## Invariants

| ID | Invariant |
|----|-----------|
| INV-SNP-01 | `data_revision` equals the pinned batch’s `manifest_self_hash` |
| INV-SNP-02 | All collection fields on `AsteroidGameDataSnapshot` and nested DTOs are `tuple` |
| INV-SNP-03 | Child collections satisfy the sort keys in **Canonical ordering** |
| INV-SNP-04 | `content_hash` depends only on the solver subset, not presentation or `built_at_utc` |
| INV-SNP-05 | Rebuild with the same pinned batch and code version yields identical `content_hash` |
| INV-SNP-06 | `asteroid_lab` does not import `game_data` (ADR-004 / import matrix) |

## References

- [ADR-004: game_data snapshot boundary](../adr/ADR-004-game-data-snapshot-boundary.md)
- Implementation plan: [`docs/superpowers/plans/2026-05-21-asteroid-lab-game-data-integration.md`](../superpowers/plans/2026-05-21-asteroid-lab-game-data-integration.md)
- Asteroid Lab invariants: `.cursor/rules/asteroid-lab-invariants.mdc`
- Django layering: `documents/ai/manuals/django.md`
