# `documents/game_data/` JSON structure (type canonical reference)

**Classification:** Documentation change  
**Dump version:** `manifest.json` → `dump_schema_version` `1.0.0`, `game_version` `unknown+1.0.3-rc3`  
**Related:** [game_data_coverage.md](game_data_coverage.md) · [ADR-004](../adr/ADR-004-game-data-snapshot-boundary.md) · import order `django_apps/game_data/importers/registry.py`

**Structure analysis goal:** Record types excluding values; **all 17 files regardless of duplication**; depth-first → §1–12 overview + **Appendix A full paths**.

This document describes **JSON field types and roles without values (examples)**.  
**§1–12 = concepts and importer mapping**; **field-level full catalog = [Appendix A](game_data_json_deep/README.md)** (each of 17 files: `*.paths.tsv` + `*.schema.txt` + `*.md`).

---

## Appendix A — Full structure for all 17 files (canonical reference)

Separate appendix per file **regardless of duplication or structural similarity**. Regenerate: `python scripts/analyze_game_data_json_deep.py`.

| file | rows | paths | detail |
| ---- | ---: | ----: | ------ |
| `manifest.json` | 0 | 227 | [manifest.md](game_data_json_deep/manifest.md) |
| `fluids.json` | 9 | 12 | [fluids.md](game_data_json_deep/fluids.md) |
| `materials.json` | 4 | 7 | [materials.md](game_data_json_deep/materials.md) |
| `sprites.json` | 61 | 7 | [sprites.md](game_data_json_deep/sprites.md) |
| `prefabs.json` | 764 | 7 | [prefabs.md](game_data_json_deep/prefabs.md) |
| `asset_references.json` | 829 | 8 | [asset_references.md](game_data_json_deep/asset_references.md) |
| `items.json` | 70 | 27 | [items.md](game_data_json_deep/items.md) |
| `shapes.json` | 1170 | 27 | [shapes.md](game_data_json_deep/shapes.md) |
| `building_variants.json` | 131 | 2859 | [building_variants.md](game_data_json_deep/building_variants.md) |
| `buildings.json` | 67 | 2285 | [buildings.md](game_data_json_deep/buildings.md) |
| `building_groups.json` | 67 | 2286 | [building_groups.md](game_data_json_deep/building_groups.md) |
| `belts_pipes_transport.json` | 9 | 1038 | [belts_pipes_transport.md](game_data_json_deep/belts_pipes_transport.md) |
| `research_unlocks.json` | 436 | 4709 | [research_unlocks.md](game_data_json_deep/research_unlocks.md) |
| `simulation_systems.json` | 180 | 47104 | [simulation_systems.md](game_data_json_deep/simulation_systems.md) |
| `toolbar_entries.json` | 204 | 2583 | [toolbar_entries.md](game_data_json_deep/toolbar_entries.md) |
| `translations.json` | 0 | 0 | [translations.md](game_data_json_deep/translations.md) |
| `raw_type_index.json` | 6497 | 8 | [raw_type_index.md](game_data_json_deep/raw_type_index.md) |

Each detail page → merged `*.schema.txt` + `*.paths.tsv`.  
Additional `simulation_systems` aggregate: [simulation_systems_paths_agg.tsv](game_data_json_deep/simulation_systems_paths_agg.tsv).

**Pruning (prevent path explosion):** Do not descend into `$cycle`; record schema/path nodes only for CLR reflection subtrees such as `DeclaredMembers`; pivot map keys → `{dynamic_key}`.

---

## 1. Notation

| Notation | Meaning |
| ---- | ---- |
| `string` / `integer` / `boolean` / `number` / `null` | JSON primitive |
| `object { "k": T; }` | Object with fixed keys |
| `array<T>` | Homogeneous array (`array<empty>` when empty) |
| `T \| U` | Union observed when merging samples |
| `required` | rate = 1.0 in **all-row** envelope table (appendix `*.md`) |
| `optional` | Present in only some rows |
| `CLR type name` | `"$type": "Fully.Qualified.Name"` when Newtonsoft-serialized |

**Unity / C# reflection dump conventions**

- `"$type"`: Runtime CLR type (used by importer/coverage for path classification).
- `"$unity": "TypeName"`: UnityEngine `Object` reference (accompanied by `name`, `instance_id`).
- `"<Field>k__BackingField"`: Auto-property backing field (often paired with public property).
- `"$cycle"`: Circular reference placeholder (for graph reconstruction; resolved or ignored during domain normalization).
- `TileVector` / `LocalTilePivot` keys: Stringified coordinate/direction tuples (e.g. `"(TileVector(0, 0, 0);East)"`).

---

## 2. Common row envelope (Source row envelope)

Most artifact files have **root `array<object>`**, and each element shares the **common provenance fields** below.

```typescript
interface SourceRowEnvelope {
  stable_id: string;           // sha256 hex, row/object identity (used in UK combinations)
  source_type_name: string;    // CLR/Unity type label observed at dump time
  source_guid: string;         // Unity GUID or type name (often empty string)
  source_path: string;         // Asset/logical path (may be empty string)
  display_name_key: string;    // UI/tree path/display key (toolbar uses tree path)
  definition_snapshot?: object;  // Serialized definition body (schema varies by file)
  simulation_parameters?: object;// Simulation runtime capture (some building/simulation/toolbar)
  manager_snapshot?: object;     // Single-row manager (research, etc.)
  // File-specific extension fields — see §3 table
}
```

`stable_id` may **not be unique within a file** (same snapshot spread across multiple rows, e.g. `items.json` ShapeItem). Importer maintains row-level provenance via `(import_batch, source_file, source_row_index)`.

---

---

## Appendix A — Full paths and merged schema (required)

**Principle:** Separate appendix for each file even when content overlaps, e.g. `buildings.json` vs `building_groups.json`.  
All rows merged; list elements type-merged up to 64 per file (path catalog traverses both containers and sample elements).

Index: [`game_data_json_deep/README.md`](game_data_json_deep/README.md)

| file | paths | deep schema |
| ---- | ----: | ----------- |
| `asset_references.json` | 8 | [schema](game_data_json_deep/asset_references.schema.txt) · [paths](game_data_json_deep/asset_references.paths.tsv) |
| `belts_pipes_transport.json` | 873412 | [schema](game_data_json_deep/belts_pipes_transport.schema.txt) · [paths](game_data_json_deep/belts_pipes_transport.paths.tsv) |
| `building_groups.json` | 5098854 | [schema](game_data_json_deep/building_groups.schema.txt) · [paths](game_data_json_deep/building_groups.paths.tsv) |
| `building_variants.json` | 1228043 | [schema](game_data_json_deep/building_variants.schema.txt) · [paths](game_data_json_deep/building_variants.paths.tsv) |
| `buildings.json` | 5098853 | [schema](game_data_json_deep/buildings.schema.txt) · [paths](game_data_json_deep/buildings.paths.tsv) |
| `fluids.json` | 12 | [schema](game_data_json_deep/fluids.schema.txt) · [paths](game_data_json_deep/fluids.paths.tsv) |
| `items.json` | 8023 | [schema](game_data_json_deep/items.schema.txt) · [paths](game_data_json_deep/items.paths.tsv) |
| `manifest.json` | 319 | [schema](game_data_json_deep/manifest.schema.txt) · [paths](game_data_json_deep/manifest.paths.tsv) |
| `materials.json` | 7 | [schema](game_data_json_deep/materials.schema.txt) · [paths](game_data_json_deep/materials.paths.tsv) |
| `prefabs.json` | 7 | [schema](game_data_json_deep/prefabs.schema.txt) · [paths](game_data_json_deep/prefabs.paths.tsv) |
| `raw_type_index.json` | 8 | [schema](game_data_json_deep/raw_type_index.schema.txt) · [paths](game_data_json_deep/raw_type_index.paths.tsv) |
| `research_unlocks.json` | 695403 | [schema](game_data_json_deep/research_unlocks.schema.txt) · [paths](game_data_json_deep/research_unlocks.paths.tsv) |
| `shapes.json` | 8407 | [schema](game_data_json_deep/shapes.schema.txt) · [paths](game_data_json_deep/shapes.paths.tsv) |
| `simulation_systems.json` | 3328176 | [schema](game_data_json_deep/simulation_systems.schema.txt) · [paths](game_data_json_deep/simulation_systems.paths.tsv) |
| `sprites.json` | 7 | [schema](game_data_json_deep/sprites.schema.txt) · [paths](game_data_json_deep/sprites.paths.tsv) |
| `toolbar_entries.json` | 4142724 | [schema](game_data_json_deep/toolbar_entries.schema.txt) · [paths](game_data_json_deep/toolbar_entries.paths.tsv) |
| `translations.json` | 0 | [schema](game_data_json_deep/translations.schema.txt) · [paths](game_data_json_deep/translations.paths.tsv) |


## 3. File catalog

| File | Root | Row count | Size (approx.) | Import | Notes |
| ---- | ---- | ----- | -------- | ------ | ---- |
| `manifest.json` | `object` | — | 24 KB | batch/checksum | Only non-array root |
| `fluids.json` | `array` | 9 | 3 KB | `FluidColor` | |
| `materials.json` | `array` | 4 | 1 KB | `GameContentAsset` | |
| `sprites.json` | `array` | 61 | 15 KB | `GameContentAsset` | |
| `prefabs.json` | `array` | 764 | 225 KB | `GameContentAsset` | |
| `asset_references.json` | `array` | 829 | 307 KB | meta→content link | |
| `items.json` | `array` | 70 | 83 KB | `ShapeRecipe` (ITEMS) | |
| `shapes.json` | `array` | 1170 | 1.7 MB | `ShapeRecipe` (FULL) | |
| `building_variants.json` | `array` | 131 | 3.8 MB | `BuildingVariant` | |
| `buildings.json` | `array` | 67 | 13 MB | building plain | `BuildingDefinitionGroup` rows |
| `building_groups.json` | `array` | 67 | 13 MB | `BuildingGroup` | adds `description_key` |
| `belts_pipes_transport.json` | `array` | 9 | 366 KB | transport registry | |
| `research_unlocks.json` | `array` | 436 | 1.7 MB | research ORM | |
| `simulation_systems.json` | `array` | 180 | **38 MB** | simulation C-lite | Deepest graph |
| `toolbar_entries.json` | `array` | 204 | 5.7 MB | toolbar tree | `display_name_key` = tree path |
| `translations.json` | `array` | **0** | 2 B | status only | `incomplete_sections` |
| `raw_type_index.json` | `array` | 6497 | 1.9 MB | CLR type index | |

Full paths and schema: **§Appendix A** or [`game_data_json_deep/README.md`](game_data_json_deep/README.md).

Import order: `registry.py` `IMPORT_ORDER` (manifest first).

---

## 4. `manifest.json`

```typescript
interface Manifest {
  game_version: string;
  unity_version: string;
  dump_mod_version: string;
  dump_schema_version: string;      // "1.0.0"
  dump_timestamp_utc: string;       // ISO-8601 Z
  source_method: string;            // "runtime_reflection"
  assembly_hashes: Record<string, string>;  // dll → "sha256:…"
  file_hashes: Record<string, string>;        // artifact → "sha256:…"
  warnings: string[];
  incomplete_sections: string[];    // e.g. "translations"
}
```

---

## 5. Simple asset rows (no snapshot or shallow)

### 5.1 `fluids.json`

- **Envelope:** common + `definition_snapshot` (required).
- **`definition_snapshot`:**

```typescript
interface ColorFluidSnapshot {
  $type: "ColorFluid";
  Color: UnityRefMetaShapeColor | empty;
}
interface UnityRefMetaShapeColor {
  $unity: "MetaShapeColor";
  name: string;
  instance_id: integer;
}
```

### 5.2 `materials.json`

```typescript
interface MaterialRow extends SourceRowEnvelope {
  material_path: string;  // required
  // no definition_snapshot
}
```

### 5.3 `sprites.json` / `prefabs.json`

```typescript
interface SpriteRow extends SourceRowEnvelope {
  sprite_path: string;
}
interface PrefabRow extends SourceRowEnvelope {
  prefab_path: string;
}
```

### 5.4 `asset_references.json`

```typescript
interface AssetReferenceRow extends SourceRowEnvelope {
  asset_type: string;      // observed: "asset.meta"
  ref_stable_id: string;   // linked content stable_id
}
```

### 5.5 `raw_type_index.json`

CLR reflection index (game logic type list). **Envelope extension:**

```typescript
interface RawTypeIndexRow extends SourceRowEnvelope {
  type_name: string;       // required — CLR name
  assembly_name: string;   // required
}
```

`source_type_name` has 6497+ variants (mix of game and compiler-generated types). Importer links to `SimulationClrProvenance`, etc.

### 5.6 `translations.json`

- **Root:** `array<empty>` — dump failed/not included (`manifest.incomplete_sections`).

---

## 6. Shape family

### 6.1 `items.json` — `ShapeItem` wrapper

- `source_type_name`: `"ShapeItem"` (70 rows).
- **`definition_snapshot`:** wrapper + inner `Definition`.

```typescript
interface ShapeItemSnapshot {
  $type: "ShapeItem";
  Definition: ShapeDefinitionBody;
}
```

### 6.2 `shapes.json` — flat `ShapeDefinition`

- `source_type_name`: `"ShapeDefinition"` (1170 rows).
- **`definition_snapshot`:** **body is directly** `ShapeDefinition` without wrapper (`$type` key present).

### 6.3 `ShapeDefinitionBody` (common geometry)

Fields read by importer (`shape_recipes._shape_definition`):

```typescript
interface ShapeDefinitionBody {
  $type?: "ShapeDefinition";
  UniqueOperationId: integer;
  PartCount: integer;              // observed 4
  Hash: string;                    // quadrant compression hash (e.g. "CuWuSuRu")
  Id: { Uid: integer } | { Name?: string };
  Layers: ShapeLayer[];
}
interface ShapeLayer {
  Parts: ShapePart[];              // length = PartCount
}
interface ShapePart {
  Shape: UnityRefMetaShapeSubPart | string;  // empty string = empty slot
  Color: UnityRefMetaShapeColor | string;
}
interface UnityRefMetaShapeSubPart {
  $unity: "MetaShapeSubPart";
  name: string;                    // CircleQuad, PinQuad, …
  instance_id: integer;
}
```

- `simulation_parameters`: **not optional (required)** on `shapes.json` rows — additional parameters bundled with shape dump.

---

## 7. Building family

### 7.1 `buildings.json` vs `building_groups.json` (separate appendix — ignore duplication)

| | `buildings.json` | `building_groups.json` |
| --- | --- | --- |
| Deep doc | [buildings.md](game_data_json_deep/buildings.md) | [building_groups.md](game_data_json_deep/building_groups.md) |
| Norm paths | 2285 | 2286 |
| Path diff | — | **+1** envelope: `description_key` |
| `definition_snapshot` paths | identical (merged schema/TSV basis) | identical |

Same row count (67), same `source_type_name` `"BuildingDefinitionGroup"`. Snapshot trees are effectively isomorphic; file difference is **row envelope `description_key` only** (groups-only).

### 7.2 `BuildingDefinitionGroup` snapshot (summary)

Group meta + `Definitions[]` array at top of `definition_snapshot`.

| Path (concept) | Type | Importer use |
| ----------- | ---- | ------------- |
| `Id` / `Id.Name` | string \| object | internal name |
| `Title` / `Description` | lazy localized + `PlaceholderResolver` | localization keys |
| `Definitions[]` | `BuildingDefinition[]` | member building |
| `Definitions[].ConnectorData` | connector graph | footprint, IO |
| `Definitions[].ConnectorData.TileDimensions` | `{x,y,z: integer}` | |
| `Definitions[].ConnectorData.AllBuildingConnectors[]` | connector | |
| `Definitions[].ConnectorData.Tiles[]` | tile coords | |
| `IsTransportBuilding` | boolean | transport flag |
| `PlayerBuildable` / `Selectable` / `Removable` | boolean | |
| `DefaultPreferredPlacementMode` | string | |
| `simulation_parameters` | object | optional keys → simulation settings |

**ConnectorData** (common pattern for building / transport):

```typescript
interface ConnectorData {
  $type: string;
  TileDimensions: Vector3Int;
  TileBounds: { Min: Vector3Int; Max: Vector3Int };
  TileBoundsCenter: Vector3Int;
  Tiles: Vector3Int[];
  AllBuildingConnectors: BuildingConnector[];
  BuildingIOMap: object;
  ConnectionsByPivot: Record<string, object>;  // pivot key → $cycle or connector
  LegacyBuildingIOMap: Record<string, array>;
}
interface BuildingConnector {
  IOType: string;
  StandType: string;
  Seperators: boolean;
  TileDirection: { Value: string };
  Position_L: Vector3Int;
}
```

**CLR reflection meta** (`Module.Assembly`, `DeclaredMembers`) deeply nested under `PlacementIndicatorTypes[]`, etc. — classified as `promoted` / `ignore_audit` in coverage manifest.

### 7.3 `building_variants.json`

```typescript
interface BuildingVariantRow extends SourceRowEnvelope {
  building_stable_id: string;  // required — parent building row stable_id
  definition_snapshot: BuildingDefinition;  // single definition snapshot
}
```

- `source_type_name`: `"BuildingDefinition"` (131).

### 7.4 `belts_pipes_transport.json`

```typescript
interface TransportRow extends SourceRowEnvelope {
  transport_kind: string;  // required
  definition_snapshot: BuildingDefinition;  // $type BuildingDefinition
}
```

9 rows; transport building definitions for belts, pipes, wires, etc.

---

## 8. `research_unlocks.json`

- **436 rows**, `source_type_name` distribution (top):
  - `ResearchSideQuest` (188)
  - `Game.Core.Research.ResearchUpgradeId` (168)
  - `ResearchSideUpgrade` (51)
  - `ResearchLevel` (13)
  - Single-row manager/config: `ResearchUnlockManager`, `ResearchConfig`, `ResearchProgression`, …

**Envelope extensions (optional):**

| Field | Occurrence (sample) | Purpose |
| ---- | ------------- | ---- |
| `definition_snapshot` | 98% | quest/level/reward graph |
| `manager_snapshot` | 2% | progression manager |
| `progression_layout` | 2% | layout |
| `research_config` | 2% | configuration |
| `simulation_parameters` | 32% | additional simulation capture |

**Typical nested `$type` paths:** `Lines[].Costs[]`, `Rewards[]`, `Title`/`Description.PlaceholderResolver`, `Levels[].Lines[]`.

---

## 9. `simulation_systems.json` (Phase 2 core)

- **180 rows**, **~38 MB** — per row `definition_snapshot` + almost always `simulation_parameters`.
- `source_type_name`: generic simulation system CLR name (e.g. `AtomicStatefulIslandSimulationSystem\`2[...]`).

### 9.1 Row structure

```typescript
interface SimulationSystemRow extends SourceRowEnvelope {
  definition_snapshot: SimulationSystemSnapshot;  // required
  simulation_parameters: SimulationRuntimeCapture;  // ~98% required
}
```

### 9.2 `simulation_parameters` (runtime capture, primary importer path)

Sample top-level keys: `ConnectableSimulations`, `BeltSpeed` (varies by row).

| Area | Representative `$type` / key | Importer profile |
| ---- | ----------------- | ---------------- |
| `SimulationFactory` | BeltSpeed, ConveyorSpeed, Configuration | `belt_policy`, factory |
| `ConnectableSimulations[]` | `Simulation`, `_Lanes[]`, `Connectors[]` | `connectable_graph` |
| Converter/building state | generic `AtomicStateful*` | `converter_runtime` |

**Connectable graph (concept):**

```typescript
interface ConnectableSimulationEntry {
  Simulation: {
    _Lanes: LaneDefinition[];
    // AcceptHook, State on lanes
  };
  Connectors: ConnectorDefinition[];
}
interface LaneDefinition {
  $type: string;
  // pivot, direction, transport slug — see simulation_clr_parser
}
```

### 9.3 `definition_snapshot`

Per row, same `$type` as system type or `SimulationFactory` subtree.  
Top `nested_$type` paths: `ConnectableSimulations[].Simulation._Lanes[]`, `SimulationFactory.Configuration.BeltSpeed`.

**Deep (47,104 norm paths):** [simulation_systems.md](game_data_json_deep/simulation_systems.md) · [simulation_systems.schema.txt](game_data_json_deep/simulation_systems.schema.txt) · [simulation_systems.paths.tsv](game_data_json_deep/simulation_systems.paths.tsv)  
**Aggregate hits:** [simulation_systems_paths_agg.tsv](game_data_json_deep/simulation_systems_paths_agg.tsv) (5,358 paths, `--normalized` all rows)  
Legacy: `documents/game_data_analysis/simulation_systems/_nested_path_audit*.tsv`

---

## 10. `toolbar_entries.json`

- **204 rows**, `display_name_key` = **tree path** (e.g. `Root/.../Children[3]`).
- `source_type_name` distribution:
  - `BuildingBasedPlacementToolbarElementData` (78)
  - `IslandBasedPlacementToolbarElementData` (63)
  - `GroupToolbarElementData` (33)
  - `ToolbarSlotSeparator` (21)
  - Other category/root (7)

```typescript
interface ToolbarRow extends SourceRowEnvelope {
  definition_snapshot: ToolbarElementSnapshot;
  simulation_parameters?: object;  // ~6% only
}
```

**Snapshot patterns (by kind):**

| Element kind | snapshot core |
| ------------ | ------------- |
| Island | `IslandGroup.Id.Name`, `IPlacementToolbarElementData.PlacerId` |
| Building | `BuildingDefinition` (+ `Definitions[]`, ConnectorData) |
| Group | `Children[]` (nested toolbar nodes) |
| Separator | minimal fields |

Importer: `toolbar_tree.import_toolbar_tree` — 4-pass, `tree_path` → `ToolbarTreeNode` hierarchy.

---

## 11. Appendix regeneration (full catalog)

```bash
python scripts/analyze_game_data_json_deep.py
# → docs/domain/game_data_json_deep/{artifact}.{md,schema.txt,paths.tsv}

python scripts/audit_simulation_nested_paths.py --normalized \
  > docs/domain/game_data_json_deep/simulation_systems_paths_agg.tsv
```

| Output | Content |
| ------ | ---- |
| `game_data_json_deep/*.paths.tsv` | Normalized paths traversing **all rows** (47k+ for simulation) |
| `game_data_json_deep/*.schema.txt` | Nested type tree **merged across all rows** |
| `simulation_systems_paths_agg.tsv` | Simulation-only path×hits×max_list_len |

---

## 12. Importer mapping summary

| JSON | Django normalization (summary) |
| ---- | -------------------- |
| `manifest.json` | `ImportBatch`, `ArtifactChecksum`, `ExportWarning` |
| `fluids.json` | `FluidColor` |
| `shapes.json` / `items.json` | `ShapeRecipe`, `ShapeRecipeLayer`, `ShapeQuadrantSlot`, `ShapeRecipeSourceAppearance` |
| `building_*` | `BuildingGroup`, `BuildingVariant`, connectors, footprints, … |
| `prefabs` / `sprites` / `materials` | `GameContentAsset` |
| `asset_references.json` | `AssetMetaReference` |
| `research_unlocks.json` | Research* model family |
| `simulation_systems.json` | `SimulationSystem`, `ConnectableSimulation`, lanes, connectors, audit |
| `toolbar_entries.json` | `ToolbarTreeNode`, `ToolbarElement`, placements |
| `belts_pipes_transport.json` | `TransportBuildingRegistry` |
| `raw_type_index.json` | CLR provenance |
| `translations.json` | `LocalizationExportStatus` (empty → incomplete) |

Raw full `definition_snapshot` is **not** stored in ORM `JSONField` ([ADR-004](../adr/ADR-004-game-data-snapshot-boundary.md)).

---

## 13. Change history

| Date | Content |
| ---- | ---- |
| 2026-05-22 | Initial edition — structure, statistics, and importer mapping for 17 JSON types |
| 2026-05-22 | Deep Appendix A — all-row path/schema (`game_data_json_deep/`) |
