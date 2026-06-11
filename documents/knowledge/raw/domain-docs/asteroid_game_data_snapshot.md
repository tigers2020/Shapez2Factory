# Asteroid Lab `game_data` Consumer Snapshot

**Owner:** domain
**Consumers:** `asteroid_lab.contracts.game_data_snapshot`,
`web.services.asteroid_game_data_snapshot`
**Status:** Current domain contract
**ADR:** [ADR-004: game_data snapshot boundary](../adr/ADR-004-game-data-snapshot-boundary.md)

## Purpose

`AsteroidGameDataSnapshot` is the immutable, revision-pinned contract between
normalized `game_data` ORM rows and Asteroid Lab consumer code. It carries only
solver-relevant building geometry and transport registry facts. Presentation
metadata stays outside this snapshot.

Build path:

1. `game_data` selectors and snapshot builders materialize ordered row tuples.
2. `web/services/asteroid_game_data_snapshot.py` assembles frozen consumer DTOs.
3. `asteroid_lab/adapters/game_data_snapshot_adapter.py` maps DTOs to Asteroid
   Lab enums without importing `game_data`.

## Top-level Shape

```python
@dataclass(frozen=True, slots=True)
class AsteroidGameDataSnapshot:
    meta: SnapshotMeta
    buildings: tuple[BuildingSnapshot, ...]
    transport_registry: tuple[TransportRegistryEntry, ...]
```

| Field | Role |
|---|---|
| `meta` | Revision pin, provenance, deterministic `content_hash` |
| `buildings` | Per-variant footprint and connectors in canonical order |
| `transport_registry` | Transport kind to building variant mapping |

Nested collections are tuples only. Lists, sets, frozensets, and nested dicts are
not valid consumer DTO collections.

## Canonical Ordering

| Collection | Sort key |
|---|---|
| `buildings` | `(internal_name, canonical_id)` |
| `footprint_cells` per building | `(y, x, order_index)` |
| `connectors` per building | `(order_index,)` |
| `transport_registry` rows | `(transport_kind,)` |

Input row order must not affect `content_hash` after canonicalization.

## SnapshotMeta

```python
@dataclass(frozen=True, slots=True)
class SnapshotMeta:
    schema_version: str
    data_revision: str
    db_alias: str
    built_at_utc: str
    content_hash: str
    game_version: str
    rule_version: str
```

| Field | Source / constraint |
|---|---|
| `schema_version` | `game_data_snapshot_v1` |
| `data_revision` | Pinned `ImportBatch.manifest_self_hash` |
| `db_alias` | `default` |
| `built_at_utc` | UTC audit timestamp; excluded from `content_hash` |
| `content_hash` | SHA-256 of canonical JSON over the solver-relevant subset |
| `game_version` | Pinned import batch |
| `rule_version` | `asteroid_v0` |

## Content Hash Scope

Included:

- `buildings`: `canonical_id`, `internal_name`, footprint cells, and connector
  fields carried by `BuildingConnectorSnapshot`.
- `transport_registry`: `transport_kind`, `transport_category`, and
  `building_variant_canonical_id`.

Excluded:

- Presentation fields such as display names, icons, sprites, and toolbar labels.
- `SnapshotMeta` itself, including `built_at_utc`, `data_revision`, and
  `content_hash`.
- Import audit blobs and source row indexes.

## Malformed Row Policy

Snapshot builds are fail-fast. The first invalid or inconsistent row aborts the
build. Do not emit partial snapshots, do not hydrate missing normalized fields
from raw import JSON, and surface stable error codes.

## Invariants

| ID | Invariant |
|---|---|
| INV-SNP-01 | `data_revision` equals the pinned batch manifest hash |
| INV-SNP-02 | Consumer DTO collections are tuples |
| INV-SNP-03 | Child collections satisfy canonical ordering |
| INV-SNP-04 | `content_hash` excludes presentation data and build timestamps |
| INV-SNP-05 | Same pinned batch and code version yields the same `content_hash` |
| INV-SNP-06 | `asteroid_lab` does not import `game_data` |

## References

- [ADR-004: game_data snapshot boundary](../adr/ADR-004-game-data-snapshot-boundary.md)
- Import boundary test: `tests/unit/architecture/test_django_app_import_boundaries.py`
- Asteroid Lab invariants: `.cursor/rules/asteroid-lab-invariants.mdc`
