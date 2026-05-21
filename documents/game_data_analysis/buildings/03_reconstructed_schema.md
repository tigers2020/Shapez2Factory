# Reconstructed Relational Schema — `buildings.json`

**Principle:** `building` is the canonical player-facing group (from this file). Variant geometry imported from `building_variants.json`. i18n overlay optional from `building_groups.json`.

---

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `building` | Buildable group | What can the player build/select as a family? | `[*].{stable_id,source_guid,snapshot flags}` | → members, rules | Observed |
| `building_simulation_setting` | Sim/UI flags | Which stats/overview apply? | `[*].simulation_parameters` | → building 1:1 | Observed |
| `building_group_member` | Variant membership | Which internal variants implement the group? | `Definitions[]` | → `building_variant` | Observed |
| `building_placement_rule` | Placement constraints | What rules govern placement? | `PlacementRequirements[]` | → building | Observed |
| `building_variant` | Internal geometry | Connector/tile facts | `building_variants.json` | ← members | Sibling (canonical) |
| `building_localization_overlay` | i18n extension | LazyText title/description? | `building_groups.json` only | → building | Sibling optional |
| `game_data_import_batch` | Provenance | Which dump? | manifest | → all | Observed |

---

## Table: `building`

**Domain question:** “What buildable group exists, how is it placed, and is it a transport family?”

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | Surrogate PK | — | yes | NO | PK |
| `stable_id` | Buildings-file hash | `[*].stable_id` | observed | NO | UNIQUE |
| `group_key` | Business id | `[*].source_guid` | observed | NO | UNIQUE |
| `display_name_key` | Plain display/i18n seed | `[*].display_name_key` | observed | NO | |
| `is_transport_building` | Transport flag | snapshot / simulation | observed | NO | |
| `placement_mode` | Enum | `DefaultPreferredPlacementMode` | observed | NO | |
| `player_buildable` | bool | snapshot | observed | NO | |
| `selectable` | bool | snapshot | observed | NO | |
| `removable` | bool | snapshot | observed | NO | |
| `auto_connect` | bool | snapshot | observed | NO | |
| `snapshot_content_hash` | Dedup | hash(`definition_snapshot`) | inferred | NO | |
| `import_batch_id` | FK | manifest | inferred | NO | FK |
| `source_row_index` | Array index | `[i]` | inferred | NO | UNIQUE(batch,index) |

**Human review:** Expose `group_key` to planner UI; keep `stable_id` internal unless required.

---

## Table: `building_simulation_setting`

1:1 with `building`. Strip all `k__BackingField` keys on import.

| Column | Source field |
| ------ | ------------ |
| `is_transport_building` | `IsTransportBuilding` |
| `pipette_override_id` | `PipetteOverrideId.Id` |
| `show_stat_belt_processing_time` | `ShowStatBeltProcessingTime` |
| `show_stat_buildings_per_full_belt` | `ShowStatBuildingsPerFullBelt` |
| `show_in_speed_overview` | `ShowInSpeedOverview` |

---

## Table: `building_group_member`

| Column | Source |
| ------ | ------ |
| `building_id` | FK |
| `ordinal` | `Definitions[]` index |
| `member_resolution` | `embedded` / `cycle_ref` |
| `internal_variant_name` | `Id.Name` when present |
| `building_variant_id` | FK |
| `cycle_label` | `$cycle` value |

**Unique:** `(building_id, ordinal)`

---

## Table: `building_placement_rule`

| Column | Source |
| ------ | ------ |
| `building_id` | FK |
| `ordinal` | array index |
| `rule_kind` | mapped from `$type` |

---

## Table: `building_localization_overlay` (optional — from `building_groups.json`)

| Column | Source |
| ------ | ------ |
| `building_id` | FK by `group_key` |
| `title_lazy_key` | LazyText display |
| `description_lazy_key` | `description_key` |

Import **after** `building` rows exist; not populated from `buildings.json` alone.

---

## Anti-patterns rejected

| Rejected | Reason |
| -------- | ------ |
| `buildings_raw` JSON table | Forbidden |
| Model `BuildingDefinitionGroup` | Dump label |
| Storing 13 MB snapshot per row as JSONField | Dedupe + parse children |
| Importing geometry from partial embed only | Use `building_variants.json` |
