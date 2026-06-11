# Reconstructed Relational Schema — `belts_pipes_transport.json`

**Principle:** Import the **9-row transport envelope** from this file. Import connector/tile/custom config **once** from `building_variants.json` (identical snapshots). No `raw_json` domain tables.

---

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `transport_building_registry` | Transport kind registry | Which belt/pipe/wire/port kinds exist for placement/simulation? | `[*].{stable_id,transport_kind,...}` | → `building_variant` | Observed |
| `building_variant` | Internal building definition | What is the simulation geometry for variant X? | `building_variants.json` (deduped snapshot) | ← transport registry | Observed (sibling) |
| `building_connector` | IO endpoints | Where can items/fluids/signals enter/exit? | `[*].definition_snapshot.ConnectorData.AllBuildingConnectors[]` | → `building_variant` | Observed |
| `building_footprint_tile` | Occupied tiles | Which tiles does the building cover? | `[*].definition_snapshot.ConnectorData.Tiles[]` | → `building_variant` | Observed |
| `building_variant_custom_config` | Extension configs | What simulation/rendering config applies? | `CustomData.All[]` | → `building_variant` | **Needs review** |
| `game_data_import_batch` | Provenance | Which dump produced rows? | `manifest.json` | → all | Observed |
| `unknown_property` | Unexpected keys | What extra dump fields appeared? | any new key | audit | Planned |

---

## Table: `transport_building_registry`

**Domain question:** “What transport-facing building kinds does the planner need (belt forward, pipe forward, wire port, etc.) and which internal variant implements them?”

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | Surrogate PK | — | yes | NO | PK |
| `stable_id` | Transport registry hash | `[*].stable_id` | observed | NO | UNIQUE |
| `transport_kind` | Planner/sim key | `[*].transport_kind` | observed | NO | UNIQUE |
| `transport_category` | belt / pipe / wire / port | derived from `transport_kind` | inferred | NO | CHECK enum |
| `display_name_key` | i18n key | `[*].display_name_key` | observed | NO | |
| `player_facing_key` | Short GUID label | `[*].source_guid` | observed | NO | |
| `building_variant_id` | FK | `[*].definition_snapshot.Id.Name` | observed | NO | FK |
| `snapshot_content_hash` | Dedup guard | hash(`definition_snapshot`) | inferred | NO | |
| `import_batch_id` | FK | manifest | inferred | NO | FK |
| `source_row_index` | Array index | `[i]` | inferred | NO | UNIQUE(batch, index) |

**FK:** `building_variant_id` → `building_variant.id` (resolve via `internal_name = Id.Name`).

**Do not store** full `definition_snapshot` JSON here if variant row already has parsed children.

**Human review:** Confirm planners key off `transport_kind` vs `building_variant.internal_name`.

---

## Table: `building_variant` (sibling — shared snapshot)

| Column | Meaning | Source |
| ------ | ------- | ------ |
| `stable_id` | Variant hash | `building_variants.json[*].stable_id` |
| `internal_name` | `Id.Name` | snapshot |
| `display_name_key` | variant display | sibling envelope |

**Link:** `transport_building_registry.building_variant_id` where `internal_name` matches.

---

## Table: `building_connector`

**Domain question:** “For this variant, what directional connectors exist and what IO channel type do they use?”

| Column | Meaning | Source path |
| ------ | ------- | ----------- |
| `building_variant_id` | FK | parent variant |
| `ordinal` | Array order | `[].AllBuildingConnectors` index |
| `connector_role` | Domain enum | `[].$type` mapped |
| `tile_direction` | Enum | `[].TileDirection.Value` |
| `io_channel_type` | Enum | `[].IOType` |
| `stand_type` | Enum/null | `[].StandType` |
| `has_seperators` | bool | `[].Seperators` |
| `position_x/y/z` | int | `[].Position_L.{x,y,z}` |

**Unique:** `(building_variant_id, ordinal)`

**Exclude:** `$type` string as column value in reports/UI — use `connector_role` only.

---

## Table: `building_footprint_tile`

| Column | Source |
| ------ | ------ |
| `building_variant_id` | FK |
| `ordinal` | `Tiles[]` index |
| `x`, `y`, `z` | tile coords |

---

## Table: `building_variant_custom_config` (defer parsing)

| Column | Notes |
| ------ | ----- |
| `building_variant_id` | FK |
| `config_kind` | Mapped from safe subset of `$type` |
| `config_key` | `Name` field when present |
| `audit_blob` | Only if parsing deferred — prefer structured extraction over JSONField on domain |

**Review status:** Defer until simulation import requirements clear.

---

## Anti-patterns rejected

| Rejected | Reason |
| -------- | ------ |
| `belts_pipes_transport_dump` JSON table | Forbidden raw dump |
| Table per `$type` (60 tables) | Mirrors serializer, not domain |
| Model `BuildingDefinition` | Runtime dump label |
| Model `IEntityConnectorData_Game_Core_Coordinates` | Reflection generic name |
| Storing 9 duplicate 20–54KB snapshots | Use variant FK + content hash |
