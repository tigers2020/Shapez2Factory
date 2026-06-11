# Reconstructed Relational Schema — `building_groups.json`

**Principle:** Persist **group registry envelope** and **normalized children**; dedupe `definition_snapshot` body with `buildings.json` (identical hash). Parse `Definitions[]` into membership rows pointing at `building_variant`. No 13 MB JSON blob table.

---

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `building_group` | Player-facing build family | What buildable group exists and how is it placed? | `[*].{stable_id,source_guid,...}` + group snapshot attrs | → members, rules, buildings dedupe | Observed |
| `building_group_simulation_setting` | UI/sim stats flags | Which stats/overview apply to this group? | `[*].simulation_parameters` | → `building_group` 1:1 | Observed |
| `building_group_localization_ref` | i18n keys | What translation keys label this group? | `display_name_key`, `description_key` | → `building_group` | Observed |
| `building_group_member` | Variant membership | Which internal variants belong to this group, in order? | `[*].definition_snapshot.Definitions[]` | → `building_variant` | Observed |
| `building_placement_rule` | Placement constraints | What must hold to place this group? | `PlacementRequirements[]` | → `building_group` | Observed |
| `building_variant` | Internal variant defs | Connector geometry for variant X? | embedded `Definitions[]` / `building_variants.json` | ← group members | Sibling dedupe |
| `building_connector` | IO endpoints | (shared variant child table) | variant snapshot | → `building_variant` | Sibling |
| `building` (canonical snapshot) | Shared group body | Same as `buildings.json` import | deduped snapshot | ↔ `building_group` by `group_key` | Observed |
| `game_data_import_batch` | Provenance | Which dump? | `manifest.json` | → all | Observed |
| `unknown_property` | Extensions | Unexpected keys | any | audit | Planned |

---

## Table: `building_group`

**Domain question:** “What is the canonical buildable family the player selects (belt default, cutter, virtual painter), and what placement/sim behavior applies at the group level?”

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | Surrogate PK | — | yes | NO | PK |
| `registry_stable_id` | Hash from groups file | `[*].stable_id` | observed | NO | UNIQUE |
| `group_key` | Business id | `[*].source_guid` or `Id.Id` | observed | NO | UNIQUE |
| `is_transport_building` | Belt/pipe/wire family | snapshot / `simulation_parameters` | observed | NO | bool |
| `placement_mode` | Placement enum | `DefaultPreferredPlacementMode` | observed | NO | CHECK |
| `player_buildable` | Can player build | snapshot flags | observed | NO | |
| `selectable` | | snapshot | observed | NO | |
| `removable` | | snapshot | observed | NO | |
| `auto_connect` | | snapshot | observed | NO | |
| `snapshot_content_hash` | Dedup vs buildings | hash(snapshot) | inferred | NO | |
| `building_canonical_id` | FK to shared building row | match `buildings.json` by `group_key` | inferred | YES | FK |
| `import_batch_id` | | manifest | inferred | NO | FK |
| `source_row_index` | Array index | `[i]` | inferred | NO | UNIQUE(batch,index) |

**Human review:** Use `group_key` for planner APIs, not `registry_stable_id`, unless dump contract requires hash.

---

## Table: `building_group_simulation_setting`

1:1 with `building_group`.

| Column | Source (`simulation_parameters`) |
| ------ | -------------------------------- |
| `building_group_id` | FK |
| `is_transport_building` | `IsTransportBuilding` |
| `pipette_override_id` | `PipetteOverrideId.Id` |
| `show_stat_belt_processing_time` | `ShowStatBeltProcessingTime` |
| `show_stat_buildings_per_full_belt` | `ShowStatBuildingsPerFullBelt` |
| `show_in_speed_overview` | `ShowInSpeedOverview` |

**Exclude** all `<*k__BackingField>` keys on import.

---

## Table: `building_group_localization_ref`

| Column | Source |
| ------ | ------ |
| `building_group_id` | FK |
| `title_key` | parsed from `display_name_key` |
| `description_key` | parsed from `description_key` |
| `lazy_text_namespace` | constant `building-variant` | inferred |

Parse: `LazyText[building-variant.{group_key}.title]`.

---

## Table: `building_group_member`

**Domain question:** “Which internal variants implement this group, and in what order?”

| Column | Meaning | Source |
| ------ | ------- | ------ |
| `building_group_id` | FK | parent |
| `ordinal` | Order | `Definitions[]` index |
| `member_resolution` | `embedded` \| `cycle_ref` | inferred from shape |
| `internal_variant_name` | Variant FK | `Definitions[i].Id.Name` |
| `building_variant_id` | FK | resolve via `building_variants` |
| `cycle_label` | Cycle target string | `$cycle` value | nullable |

**Unique:** `(building_group_id, ordinal)`

**Rules:**

- If `Id.Name` present → `member_resolution=embedded`, require `building_variant` row.
- If only `$cycle` → resolve `building_variant_id` from prior ordinal per dump graph rules (audit if ambiguous).

---

## Table: `building_placement_rule`

| Column | Source |
| ------ | ------ |
| `building_group_id` | FK |
| `ordinal` | `PlacementRequirements[]` index |
| `rule_kind` | mapped from `$type` |
| `rule_payload` | minimal scalar extraction | **review** — avoid JSONField on domain; use typed columns where possible |

---

## Table: `building_variant` / `building_connector`

Import from `building_variants.json` (131 rows). Group file embeds 97 full copies; **do not duplicate** variant geometry if variant hash already imported.

---

## Anti-patterns rejected

| Rejected | Reason |
| -------- | ------ |
| `building_groups_raw` JSON table | Forbidden |
| Model `BuildingDefinitionGroup` | Runtime dump label |
| 67 tables for 67 `$type` strings | Serializer mirror |
| Storing full 13 MB snapshot per group row | Dedupe via `buildings.json` hash |
| Using `instance_id` as canonical FK | Unity debug ref |
