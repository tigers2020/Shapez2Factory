# File Inventory — `building_variants.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/building_variants.json` |
| File name | `building_variants.json` |
| Manifest hash | `sha256:e2a4a6b0b911dbdbff9635cc296ba53dd50906de2ddc1a00bf1555a08225a872` |
| Approx. size | **3,798,143 bytes** (~3.8 MB) |
| Dump context | `manifest.json` → `source_method: runtime_reflection`, v2 export |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **131** |
| Element type | **object** (homogeneous envelope + nested snapshot) |
| Max nesting depth | **~8+** under `definition_snapshot` |

Root is an array; no top-level object keys.

## Major object groups

Each element = one **internal building variant** (simulation/placement geometry for a specific rotated/mirrored implementation):

| Partition | Count | Notes |
| --------- | ----- | ----- |
| Internal variants (name suffix `InternalVariant`) | **128** | Primary family |
| Other naming (`Mirrored`, special labels) | **3** | Includes mirrored set labels |
| Mirrored-only variants (`*Mirrored` suffix) | **34** | Not embedded by name in `building_groups.json` |
| Variants embedded in groups (by `Id.Name`) | **97** | Subset also appears in group `Definitions[]` |
| Zero connectors | **1** | `LabelDefaultInternalVariant` |

### Connector count distribution (per variant)

| Connectors | Variants |
| ---------- | -------- |
| 0 | 1 |
| 1 | 16 |
| 2 | 62 |
| 3 | 40 |
| 4 | 10 |
| 7 | 2 |

## Envelope fields (131/131)

| Field | Type | Notes |
| ----- | ---- | ----- |
| `stable_id` | 64-char hex | Variant registry PK |
| `source_guid` | string | **Always equals** `definition_snapshot.Id.Name` |
| `source_path` | string | Always `""` |
| `source_type_name` | string | Always `BuildingDefinition` (dump label) |
| `display_name_key` | string | Equals internal name (131/131) |
| `building_stable_id` | string | **Always empty** `""` (131/131) |
| `definition_snapshot` | object | Connectors, tiles, custom data graph |

## Snapshot shape (uniform)

All 131 snapshots share the same key set:

`Id`, `ConnectorData`, `CustomData`, `IEntityDefinition.CustomData`, `IEntityDefinition.Id`, `<Id>k__BackingField`, `<ConnectorData>k__BackingField`, `$type`

## Repeated structures

| Structure | Notes |
| --------- | ----- |
| `ConnectorData.AllBuildingConnectors[]` | Primary IO model |
| `ConnectorData.Tiles[]` | Footprint (1–N tiles) |
| `ConnectorData.TileDimensions` | Bounding size |
| `ConnectorData.LegacyBuildingIOMap` | Legacy graph (often non-empty) |
| `CustomData` | Often `{"$cycle": ...}` at root — graph pointer |
| Generic `IEntityConnectorData<...>.AllConnectors` | Duplicate connector list (runtime) |

## Arrays detected

| Path | Typical size |
| ---- | -------------- |
| `$` | 131 |
| `[*].definition_snapshot.ConnectorData.AllBuildingConnectors` | 0–7 |
| `[*].definition_snapshot.ConnectorData.Tiles` | 1–? |
| `CustomData.All` / nested lists | varies (often cyclic) |

## Candidate IDs

| Field | Uniqueness | Role |
| ----- | ---------- | ---- |
| `stable_id` | 131 unique | Variant registry hash |
| `Id.Name` | 131 unique | **Canonical business key** (`internal_variant_name`) |
| `source_guid` | 131 unique | Duplicate of `Id.Name` in this dump |
| `building_stable_id` | empty | Reserved parent FK — **unresolved in bundle** |

## Runtime / reflection / debug strings

| Pattern | Count / presence |
| ------- | ---------------- |
| `source_type_name: BuildingDefinition` | 131 — source metadata |
| `<*k__BackingField>` | ~11,787 key instances |
| `$type` discriminators | **156** distinct values |
| `$cycle` in CustomData / legacy maps | Common |
| `IEntityConnectorData<Game.Core.Coordinates...>` keys | Per variant |
| `_IOType` duplicate field | Some fluid/signal connectors |

No `Game.Content.*` **values** as primary IDs; generic names appear as JSON keys.

## Possible source metadata

- Empty `source_path`, empty `building_stable_id`
- Unity mesh references inside deeper CustomData (when expanded)
- `manifest.file_hashes`

## Cross-file inventory

| File | Relationship |
| ---- | ------------ |
| `building_groups.json` | 97 embedded `Definitions[].Id.Name` match; snapshots often **smaller** than variant file (partial embed) |
| `belts_pipes_transport.json` | 9 transport rows reference internal variant **names**; snapshots **byte-equal** to variant file for those 9 |
| `buildings.json` | **0** `stable_id` overlap (different registry) |
| `research_unlocks.json` | 128/131 internal names appear in text |
| `simulation_systems.json` | 131/131 names/guids appear in text |
| `prefabs.json` | Linked via transport meta layer, not variant `stable_id` directly |

## Design implication

`building_variants.json` is the **canonical geometry/simulation source** for 131 internal variants. Normalize to `building_variant` + `building_connector` + `building_footprint_tile` (+ deferred custom config). Do **not** mirror 156 `$type` classes or store 3.8 MB as `raw_json`.
