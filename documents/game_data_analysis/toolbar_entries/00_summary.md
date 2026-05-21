# File Inventory — `toolbar_entries.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/toolbar_entries.json` |
| File name | `toolbar_entries.json` |
| File size | **~5,707,237 bytes** |
| Manifest hash | `sha256:a54116a469b45178fd80fb835b41f07fafa1fe28a309ae6309e69c68fbf7cd50` |
| Dump context | `manifest.json` → `runtime_reflection`, v2 export (toolbar capture) |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **204** |
| Envelope keys | `stable_id`, `source_type_name`, `source_guid`, `source_path`, `display_name_key`, `definition_snapshot`, `simulation_parameters` |

## Row kinds (`source_type_name`)

| Kind | Count | Role |
| ---- | ----- | ---- |
| `BuildingBasedPlacementToolbarElementData` | 78 | Place building from toolbar (`BuildingDefinition` nested) |
| `IslandBasedPlacementToolbarElementData` | 63 | Place island/group structures (`IslandGroup` nested) |
| `GroupToolbarElementData` | 33 | Folder/group node (`Children[]`) |
| `ToolbarSlotSeparator` | 21 | Visual separator |
| `CategoryToolbarElementData` | 3 | Category + mechanic gate |
| `CustomRequirementBasedUnlockableCategoryToolbarElementData` | 3 | Gated category |
| `RootToolbarElementData` | 1 | Tree root (9 top-level children) |
| `HiddenCustomRequirementBasedUnlockableCategoryToolbarElementData` | 1 | Hidden category |
| `PlacementToolbarElementData` | 1 | Generic placement row |

## Repeated structures

| Pattern | Where |
| ------- | ----- |
| `Children[]` / `IParentToolbarElementData.Children` | Groups, categories, root |
| `BuildingDefinition` object | 78 building placement rows (~large) |
| `IslandGroup` object | 63 island placement rows |
| `IPresentableToolbarElementData.*` / `IPlacementToolbarElementData.*` | Presentational + placement interface fields |
| `$type`, `$unity`, `instance_id` | Serializer / Unity metadata |

## Arrays / nesting

- Deep trees flattened into **204 rows**, each with unique `display_name_key` path (e.g. `root/Children[3]/Children[2]/Children[2]`).
- `source_path` empty on sampled rows — **tree path is `display_name_key`**.

## Candidate IDs

| Field | Canonical use |
| ----- | ------------- |
| `display_name_key` | **Tree path** (204 unique) — ordering & parent inference |
| `stable_id` | **Unique** per row — import correlation |
| `BuildingDefinition.Id.Id` | **Building variant/group key** (57 distinct in 78 rows) |
| `IPlacementToolbarElementData.PlacerId.Id` | Placer numeric id |
| `MechanicRequiredToUnlock.Id` | Research mechanic key (`RUFluids`, …) |
| `IslandGroup.Id.Name` | Island group name (e.g. `SpaceBeltsGroup`) |
| `source_type_name` | **Element kind discriminator** — shorten for enum, not as table name |

## Runtime / reflection / debug

- Interface-prefixed keys: `IPresentableToolbarElementData.Icon`
- `Core.Localization.LazyLocalizedText` cycles in Title/Description
- `UnityEngine.Sprite` + `instance_id` on icons
- Full type names: `BuildingBasedPlacementToolbarElementData` — **not** Django models

## Cross-file references

| File | Relationship |
| ---- | ------------ |
| `building_groups.json` | `BuildingDefinition.Id.Id` strings (e.g. `BeltDefaultVariant`) |
| `sprites.json` | `Icon.name` (e.g. `BeltIcon`) |
| `research_unlocks.json` | `MechanicRequiredToUnlock` / mechanic ids |
| `simulation_systems.json` | Textual / transport naming |
| `asset_references.json` | **No** direct stable_id bridge (not a prefab/sprite registry file) |

## Design implication

Normalize **`toolbar_element`** (204) + kind-specific extension tables + **`toolbar_tree_edge`** (parent/child from path) + scalar extracts from `BuildingDefinition` — **never** mirror 5.7 MB of nested JSON or 204 tables named after dump types.
