# File Inventory — `building_groups.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/building_groups.json` |
| File name | `building_groups.json` |
| Manifest hash | `sha256:c39e4b186a9957d59daba275536964e95e64819d90e89c6a4ea3b7a3dff8206d` |
| Approx. size | **13,033,263 bytes** (~13 MB) |
| Dump context | `manifest.json` → `source_method: runtime_reflection`, v2 export |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **67** |
| Element type | **object** (homogeneous envelope + large nested snapshot) |
| Max nesting depth | **~8+** under `definition_snapshot` |

Root is not an object; there are no top-level keys.

## Major object groups

Each array element = one **building definition group** (player-facing buildable family):

| Partition | Count | Key |
| --------- | ----- | --- |
| Building groups | **67** | `source_guid` / `definition_snapshot.Id.Id` |
| Embedded member definitions | **131** total | `definition_snapshot.Definitions[]` |
| — Full embedded variants | **97** | `Definitions[i].Id.Name` present |
| — Cycle placeholder members | **34** | `Definitions[i]` = `{"$cycle": "..."}` only |
| Transport groups | **12** | `IsTransportBuilding: true` |

### `Definitions[]` length distribution (per group)

| Members | Groups |
| ------- | ------ |
| 1 | 37 |
| 2 | 23 |
| 3 | 1 |
| 4 | 2 |
| 8 | 3 |
| 13 | 1 |

## Envelope fields (67/67)

| Field | Type | Notes |
| ----- | ---- | ----- |
| `stable_id` | 64-char hex | Group registry ID (≠ `buildings.json` `stable_id`) |
| `source_guid` | string | Group key, e.g. `BeltDefaultVariant` |
| `source_path` | string | Always `""` |
| `source_type_name` | string | Always `BuildingDefinitionGroup` |
| `display_name_key` | string | `LazyText[building-variant.<Id>.title]` |
| `description_key` | string | `LazyText[building-variant.<Id>.description]` |
| `simulation_parameters` | object | 5 logical fields + 5 backing-field duplicates |
| `definition_snapshot` | object | Group metadata + `Definitions[]` |

## Repeated structures

| Structure | Scope |
| --------- | ----- |
| Group envelope (8 fields) | 67× |
| `definition_snapshot` group metadata | 67× (placement, flags, Icon, Title, …) |
| `Definitions[]` | 67 lists (1–13 members) |
| `Definitions[].ConnectorData` | Per embedded variant |
| `PlacementRequirements[]` | 9 groups non-empty |
| `PlacementIndicatorTypes[]` | 18 groups non-empty |
| `simulation_parameters` + `<>k__BackingField` mirrors | 67× |

## Arrays detected

| Path | Notes |
| ---- | ----- |
| `$` | 67 groups |
| `[*].definition_snapshot.Definitions` | 131 members total |
| `[*].definition_snapshot.PlacementRequirements` | 0–2+ |
| `[*].definition_snapshot.PlacementIndicatorTypes` | 0–1+ |
| `[*].definition_snapshot.Definitions[].ConnectorData.AllBuildingConnectors` | Per member |

## Nested objects

Deep reflection graph under `definition_snapshot` (localization lazy text, Unity icon refs, structure overview, custom data, embedded building definitions).

## Candidate IDs

| Field | Uniqueness | Role |
| ----- | ---------- | ---- |
| `stable_id` | 67 unique | Group registry PK (groups file namespace) |
| `source_guid` | 67 unique | Natural business key; matches `buildings.json` |
| `definition_snapshot.Id.Id` | 67 unique | Group definition id (equals `source_guid`) |
| `Definitions[].Id.Name` | 97 unique across file | Internal variant name → FK to `building_variants` |
| `Definitions[]` with `$cycle` only | 34 | Graph back-reference, not a new ID |

## Runtime / reflection / debug strings

| Pattern | Presence | Classification |
| ------- | -------- | -------------- |
| `source_type_name: BuildingDefinitionGroup` | 67 | Source metadata |
| `<*k__BackingField>` | ~5,564 key instances | Runtime/reflection |
| `$type` (152 distinct) | Throughout | Serializer metadata → enums, not ORM names |
| `$cycle` | Title/Description/StructureOverview + 34 Definitions | Graph serialization |
| `$unity` + `instance_id` on Icon | 67 | Engine object refs (audit only) |
| `Core.Localization.LazyLocalizedText` | Title/Description | Localization wiring |
| `Game.Content.*` / generic interface property names | Nested keys | Runtime/reflection |

## Possible source metadata

- Empty `source_path`
- `LazyText[...]` string keys (not yet resolved via `translations.json` — manifest marks translations incomplete)
- Duplicate `simulation_parameters` backing fields
- `manifest.file_hashes`, `dump_schema_version`

## Cross-file inventory (full corpus)

| File | Relationship |
| ---- | ------------ |
| `buildings.json` | **67/67** same `source_guid`; **67/67** identical `definition_snapshot` JSON |
| `building_variants.json` | **131** variant rows; **97** embedded by `Id.Name`; **34** `$cycle` aliases |
| `research_unlocks.json` | All 67 `source_guid` strings appear in file text |
| `toolbar_entries.json` | 57/67 `source_guid` text hits |
| `belts_pipes_transport.json` | No direct overlap (transport kinds ≠ group guids) |

## Design implication

This file is a **group registry envelope** (unique `stable_id`, LazyText keys, `simulation_parameters`) wrapped around the **same group snapshot as `buildings.json`**, with **ordered variant membership** in `Definitions[]`. Do **not** store 13 MB duplicated twice in domain tables — normalize to `building_group`, `building_group_member`, and FK to `building_variant` / shared group attributes imported once from deduped snapshot hash.
