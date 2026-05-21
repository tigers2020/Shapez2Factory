# Reconstructed Relational Schema — `building_variants.json`

**Principle:** `building_variant` is the root for internal placement geometry. Children normalize connectors and tiles. Custom simulation config deferred. No `raw_json` table.

---

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `building_variant` | Internal variant registry | What implementable variant exists and how big is its footprint? | `[*].{stable_id,Id.Name,...}` | ← group members, transport | Observed |
| `building_connector` | IO endpoints | Where can items/fluids/signals connect? | `ConnectorData.AllBuildingConnectors[]` | → variant | Observed |
| `building_footprint_tile` | Occupied tiles | Which tiles does variant occupy? | `ConnectorData.Tiles[]` | → variant | Observed |
| `building_variant_legacy_io` | Legacy IO graph | (optional) Legacy slot mapping | `LegacyBuildingIOMap` | → variant | Defer |
| `building_variant_custom_config` | Simulation extras | What simulation config applies? | `CustomData` tree | → variant | **Needs review** |
| `building_group_member` | Group membership | Which group includes this variant? | `building_groups.json` | → variant | Sibling |
| `game_data_import_batch` | Provenance | Which dump? | `manifest.json` | → all | Observed |
| `unknown_property` | Extensions | Unexpected keys | any | audit | Planned |

---

## Table: `building_variant`

**Domain question:** “What is the canonical internal building variant for simulation/placement (including rotation/mirror forms), and how is it identified?”

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | Surrogate PK | — | yes | NO | PK |
| `stable_id` | Dump hash ID | `[*].stable_id` | observed | NO | UNIQUE |
| `internal_name` | Business key | `[*].definition_snapshot.Id.Name` | observed | NO | UNIQUE |
| `display_name_key` | Display/i18n | `[*].display_name_key` | observed | NO | |
| `is_mirrored` | Mirrored clone | name suffix `Mirrored` | inferred | NO | bool |
| `size_x`, `size_y`, `size_z` | Footprint dims | `TileDimensions` | observed | NO | |
| `connector_count` | Denormalized count | `AllBuildingConnectors` length | inferred | NO | |
| `building_group_id` | Parent group FK | `building_stable_id` or membership import | inferred | YES | FK — **empty in dump** |
| `snapshot_content_hash` | Integrity | hash(snapshot) | inferred | NO | |
| `import_batch_id` | | manifest | inferred | NO | FK |
| `source_row_index` | Array index | `[i]` | inferred | NO | UNIQUE(batch,index) |

**Human review:** Prefer `internal_name` for planner APIs over `stable_id` unless hash contract required.

---

## Table: `building_connector`

| Column | Meaning | Source |
| ------ | ------- | ------ |
| `building_variant_id` | FK | parent |
| `ordinal` | Order | array index |
| `connector_role` | Domain enum | `$type` mapped |
| `tile_direction` | Enum | `TileDirection.Value` |
| `io_channel_type` | Enum | `IOType` |
| `stand_type` | Enum/null | `StandType` |
| `has_seperators` | bool | `Seperators` |
| `position_x`, `position_y`, `position_z` | int | `Position_L` |

**Unique:** `(building_variant_id, ordinal)`

---

## Table: `building_footprint_tile`

| Column | Source |
| ------ | ------ |
| `building_variant_id` | FK |
| `ordinal` | `Tiles[]` index |
| `x`, `y`, `z` | tile coords |

**Unique:** `(building_variant_id, x, y, z)` or `(building_variant_id, ordinal)`

---

## Table: `building_variant_legacy_io` (optional / defer)

Capture only if legacy map needed for simulation parity.

| Column | Notes |
| ------ | ----- |
| `building_variant_id` | FK |
| `slot_kind` | map key name |
| `ordinal` | list index |
| `cycle_ref` | `$cycle` label | audit, not domain FK |

---

## Table: `building_variant_custom_config` (defer)

Parse selected `$type` nodes into typed rows in a later phase; until then use `unknown_property` for unexplored branches.

---

## Anti-patterns rejected

| Rejected | Reason |
| -------- | ------ |
| 131 tables per variant | Not domain |
| 156 tables per `$type` | Serializer mirror |
| Model `BuildingDefinition` | Dump label |
| `building_variants_raw` JSON blob | Forbidden |
| JSONField array of connectors | Use `building_connector` rows |
