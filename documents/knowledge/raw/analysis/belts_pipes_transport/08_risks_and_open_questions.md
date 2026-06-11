# Risks and Open Questions — `belts_pipes_transport.json`

## Fields with uncertain meaning

| Field / area | Risk |
| ------------ | ---- |
| `CustomData.All[]` | Deep simulation (conveyor speed, fluid ports, wire rendering) — 60+ `$type` nodes |
| `LegacyBuildingIOMap` + `$cycle` | May be required for parity or ignorable legacy graph |
| `_IOType` vs `IOType` | Duplicate on some fluid connectors |
| `Seperators` | Dump typo — preserve as `has_seperators` or normalize? |
| Empty `source_path` | May break path-based tooling expecting Unity paths |

---

## Inferred entities requiring human review

| Entity | Question |
| ------ | -------- |
| `transport_building_registry` | Is this first-class for Shapez2 Factory Planner or can sim use `building_variant` only? |
| `transport_category` | Is inferred taxonomy correct for UI grouping? |
| `building_variant_custom_config` | Which `$type` configs are planner-critical vs rendering-only? |
| Crosswalk to `buildings.json` | How does `ForwardBelt` relate to `BeltDefaultVariant` group? |

---

## Runtime metadata mistaken for domain data

| Signal | Risk | Mitigation |
| ------ | ---- | ---------- |
| `source_type_name: BuildingDefinition` | Model named `BuildingDefinition` | Rename to `dump_capture_type` |
| 60 `$type` strings (`Game.Content.*`, `System.Reflection.*`) | 60 Django models | Map to enums + deferred config parser |
| `IEntityConnectorData<...>.AllConnectors` | Duplicate connector import | Strip on ingest |
| `<*k__BackingField>` (731 instances) | Columns like `Location_k__BackingField` | Strip |
| `BeltMetaBuildingDefinition+DrawData` | Table name from nested `$type` | Custom config audit only |

---

## Ambiguous IDs

| ID | Issue |
| -- | ----- |
| Transport `stable_id` vs variant `stable_id` | Same snapshot, different hash — **do not merge** without algorithm proof |
| `transport_kind` vs `Id.Name` | Two naming schemes (player vs internal) — planner must pick canonical |
| `source_guid` | Equals `transport_kind`, not buildings.json GUID |

---

## Dynamic schemas

| Scenario | Impact |
| -------- | ------ |
| New transport kind (10th row) | Count guard + enum migration |
| New connector `$type` | `connector_role` enum extension |
| Dump adds envelope fields | `unknown_property` capture |
| Schema drift between transport and variants file | Hash equality test fails — **critical alarm** |

Current dump: **low structural variance**, **high nested blob variance**.

---

## Possible version drift

- `manifest.game_version`: `unknown+1.0.3-rc3`
- `dump_schema_version`: `1.0.0`
- v2 export warning mentions transport captures — expect row count / snapshot size changes

---

## Missing cross-reference targets

| Consumer | Status |
| -------- | ------ |
| `buildings.json` transport groups | No direct FK (12 transport buildings, different naming) |
| `building_variant.building_stable_id` | Empty for all 9 linked variants |
| `toolbar_entries.json` | Textual references only |
| Application Python/JS | No in-repo importer yet |
| Merger/splitter transport | Not in this file (only 9 kinds) |

---

## Tables that should not be implemented yet

| Table | Reason |
| ----- | ------ |
| `legacy_building_io_graph` | `$cycle` serialization; unclear domain use |
| Per-`$type` simulation tables (60+) | Reflection explosion |
| `belts_pipes_transport_raw` | Forbidden |
| Full `custom_data` relational decomposition | Needs simulation domain spec |

**Implement first:** `transport_building_registry` + reuse `building_variant` / `building_connector` from variant import with **hash dedupe**.

---

## Redundancy / duplication risk (high)

Entire `definition_snapshot` duplicates `building_variants.json`. Storing twice guarantees drift.

**Recommendation:** Transport file imports **only envelope**; verify `snapshot_content_hash` against variant.

---

## Summary risk level

| Area | Level |
| ---- | ----- |
| Envelope schema | **Low** (9 flat rows) |
| Nested snapshot | **High** (reflection graph) |
| FK to variants | **Low** (9/9 resolved by name) |
| FK to buildings | **High** (unresolved naming) |
| Planner integration | **Medium** (sim references `transport_kind`) |
