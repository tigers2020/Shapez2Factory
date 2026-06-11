# File Inventory — `buildings.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/buildings.json` |
| File name | `buildings.json` |
| Manifest hash | `sha256:907bfcf145e0a86fb28cb3905af7806edd05a377b0f96ed1850bc4dcd528fe7e` |
| Approx. size | **13,025,486 bytes** (~13 MB) |
| Dump context | `manifest.json` → `source_method: runtime_reflection`, v2 export |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **67** |
| Element type | **object** (homogeneous envelope + large nested snapshot) |
| Max nesting depth | **~8+** under `definition_snapshot` |

Root is an array; no top-level object keys.

## Major object groups

Each element = one **building definition group** (player-selectable build family):

| Partition | Count |
| --------- | ----- |
| Building groups (`source_guid` / `Id.Id`) | **67** |
| Transport families (`IsTransportBuilding: true`) | **12** |
| `Definitions[]` members (total slots) | **131** |
| — Named embedded variants (`Id.Name`) | **97** |
| — `$cycle` placeholder members | **34** |

### `Definitions[]` length per group

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
| `stable_id` | 64-char hex | **Buildings-file** registry hash |
| `source_guid` | string | Group key, e.g. `CutterDefaultVariant` |
| `source_path` | string | Always `""` |
| `source_type_name` | string | Always `BuildingDefinitionGroup` (dump label) |
| `display_name_key` | string | **Plain** group key (equals `source_guid`, 67/67) |
| `simulation_parameters` | object | 5 logical flags + backing-field duplicates |
| `definition_snapshot` | object | Full group graph (placement, icons, `Definitions[]`, …) |

**Not in this file (vs `building_groups.json`):** `description_key`, LazyText-style `display_name_key`.

## Repeated structures

| Structure | Occurrence |
| --------- | ---------- |
| Group envelope | 67× |
| `definition_snapshot` group metadata | 67× |
| `Definitions[]` variant membership | 67 lists / 131 members |
| `PlacementRequirements[]` | 9 groups non-empty |
| `PlacementIndicatorTypes[]` | 18 groups non-empty |
| `Title` / `Description` / `Icon` localization objects | 67× |
| `simulation_parameters` + mirrored `<>k__BackingField` | 67× |

## Arrays detected

| Path | Notes |
| ---- | ----- |
| `$` | 67 elements |
| `[*].definition_snapshot.Definitions` | 1–13 per group |
| `[*].definition_snapshot.PlacementRequirements` | 0–2+ |
| `[*].definition_snapshot.ConnectorData` (inside embedded defs) | per named member |

## Candidate IDs

| Field | Uniqueness | Role |
| ----- | ---------- | ---- |
| `stable_id` | 67 unique | Buildings-registry PK |
| `source_guid` | 67 unique | **Canonical planner group key** |
| `definition_snapshot.Id.Id` | 67 unique | Equals `source_guid` |
| `Definitions[].Id.Name` | 97 unique names | FK to `building_variant.internal_name` |

## Runtime / reflection / debug strings

| Pattern | Presence |
| ------- | -------- |
| `source_type_name: BuildingDefinitionGroup` | 67 — source metadata |
| `<*k__BackingField>` | ~5,564 instances |
| `$type` (152 distinct) | Serializer metadata |
| `$cycle` in Title/Description/Definitions | Graph serialization |
| `$unity` + `instance_id` on `Icon` | Engine refs |
| `Core.Localization.LazyLocalizedText` | In snapshot Title/Description (not envelope) |

## Cross-file inventory

| File | Relationship |
| ---- | ------------ |
| `building_groups.json` | **67/67** identical `definition_snapshot`; **67/67** identical `simulation_parameters`; **different** `stable_id` and display keys (LazyText there) |
| `building_variants.json` | 97/97 named `Definitions[].Id.Name` resolve; 34 cycle → mirrored variants |
| `research_unlocks.json` | 67/67 `source_guid` text hits |
| `toolbar_entries.json` | 57/67 text hits |
| `simulation_systems.json` | 0/67 `source_guid` hits (uses transport_kind names) |
| `belts_pipes_transport.json` | Indirect via variants |

## Design implication

`buildings.json` is the **canonical group snapshot + plain display key** source for the bundle (~13 MB). Pair with `building_groups.json` only for i18n (`description_key`, LazyText titles). Normalize to `building` + children; **do not** duplicate snapshot in a JSON blob table.
