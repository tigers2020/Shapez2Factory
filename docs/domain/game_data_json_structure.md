# `documents/game_data/` JSON 구조 (타입 정본)

**분류:** 문서 변경  
**덤프 버전:** `manifest.json` → `dump_schema_version` `1.0.0`, `game_version` `unknown+1.0.3-rc3`  
**연관:** [game_data_coverage.md](game_data_coverage.md) · [ADR-004](../adr/ADR-004-game-data-snapshot-boundary.md) · import 순서 `django_apps/game_data/importers/registry.py`

**구조 분석 목표:** 값 제외 타입 기록；**중복 여부 무관 17파일 전부**；깊이 우선 → §1–12 개요 + **부록 A 전 경로**.

이 문서는 **값(example) 없이 JSON 필드의 타입·역할**을 기술한다.  
**§1–12 = 개념·importer 매핑**；**필드 단위 전량 = [부록 A](game_data_json_deep/README.md)**（17파일 각각 `*.paths.tsv` + `*.schema.txt` + `*.md`）.

---

## 부록 A — 17파일 전량 구조（정본）

중복·동형 여부와 **무관하게 파일마다 별도 부록**. 재생성: `python scripts/analyze_game_data_json_deep.py`.

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

각 detail 페이지 → merged `*.schema.txt` + `*.paths.tsv`.  
`simulation_systems` 추가 aggregate: [simulation_systems_paths_agg.tsv](game_data_json_deep/simulation_systems_paths_agg.tsv).

**Pruning（경로 폭발 방지）:** `$cycle` 미하향；`DeclaredMembers` 등 CLR reflection subtree는 스키마/경로 노드만 기록；pivot map 키 → `{dynamic_key}`.

---

## 1. 표기법 (Notation)

| 표기 | 의미 |
| ---- | ---- |
| `string` / `integer` / `boolean` / `number` / `null` | JSON primitive |
| `object { "k": T; }` | 고정 키를 가진 객체 |
| `array<T>` | 동형 배열 (비어 있으면 `array<empty>`) |
| `T \| U` | 샘플 병합 시 관측된 union |
| `required` | **전 행** envelope 표에서 rate = 1.0（부록 `*.md`） |
| `optional` | 일부 행만 존재 |
| `CLR type name` | Newtonsoft 직렬화 시 `"$type": "Fully.Qualified.Name"` |

**Unity / C# reflection 덤프 관례**

- `"$type"`: 런타임 CLR 타입 (importer·coverage가 경로 분류에 사용).
- `"$unity": "TypeName"`: UnityEngine `Object` 참조 (`name`, `instance_id` 동반).
- `"<Field>k__BackingField"`: auto-property backing field (공개 프로퍼티와 쌍으로 자주 등장).
- `"$cycle"`: 순환 참조 placeholder (그래프 재구성용; 도메인 정규화 시 해소·무시 대상).
- `TileVector` / `LocalTilePivot` 키: 문자열화된 좌표·방향 튜플 (예: `"(TileVector(0, 0, 0);East)"`).

---

## 2. 공통 행 봉투 (Source row envelope)

대부분의 아티팩트 파일은 **루트가 `array<object>`** 이고, 각 요소가 아래 **공통 provenance 필드**를 공유한다.

```typescript
interface SourceRowEnvelope {
  stable_id: string;           // sha256 hex, 행·객체 식별 (UK 조합에 사용)
  source_type_name: string;    // 덤프 시 관측 CLR/Unity 타입 라벨
  source_guid: string;         // Unity GUID 또는 타입명 (종종 빈 문자열)
  source_path: string;         // 에셋/논리 경로 (빈 문자열 가능)
  display_name_key: string;    // UI/트리 경로·표시 키 (toolbar는 tree path)
  definition_snapshot?: object;  // 직렬화된 정의 본문 (파일별 스키마 상이)
  simulation_parameters?: object;// 시뮬 런타임 캡처 (building/simulation/toolbar 일부)
  manager_snapshot?: object;     // research 등 매니저 단일 행
  // 파일별 확장 필드 — §3 표 참조
}
```

`stable_id`는 파일 내 **유일하지 않을 수 있음** (동일 스냅샷이 여러 행으로 펼쳐짐, 예: `items.json` ShapeItem). Importer는 `(import_batch, source_file, source_row_index)`로 행 단위 provenance를 유지한다.

---

---

## 부록 A — 전량 경로·병합 스키마 (필수)

**원칙:** `buildings.json` vs `building_groups.json` 등 **내용이 겹쳐도 각각 별도 부록**.
모든 행을 병합했으며, 리스트 원소는 파일당 최대 64개까지 타입 병합(경로 카탈로그는 컨테이너·샘플 원소 모두 순회).

인덱스: [`game_data_json_deep/README.md`](game_data_json_deep/README.md)

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


## 3. 파일 카탈로그

| 파일 | 루트 | 행 수 | 크기(약) | Import | 비고 |
| ---- | ---- | ----- | -------- | ------ | ---- |
| `manifest.json` | `object` | — | 24 KB | 배치·체크섬 | 유일한 비배열 루트 |
| `fluids.json` | `array` | 9 | 3 KB | `FluidColor` | |
| `materials.json` | `array` | 4 | 1 KB | `GameContentAsset` | |
| `sprites.json` | `array` | 61 | 15 KB | `GameContentAsset` | |
| `prefabs.json` | `array` | 764 | 225 KB | `GameContentAsset` | |
| `asset_references.json` | `array` | 829 | 307 KB | meta→content 링크 | |
| `items.json` | `array` | 70 | 83 KB | `ShapeRecipe` (ITEMS) | |
| `shapes.json` | `array` | 1170 | 1.7 MB | `ShapeRecipe` (FULL) | |
| `building_variants.json` | `array` | 131 | 3.8 MB | `BuildingVariant` | |
| `buildings.json` | `array` | 67 | 13 MB | building plain | `BuildingDefinitionGroup` 행 |
| `building_groups.json` | `array` | 67 | 13 MB | `BuildingGroup` | `description_key` 추가 |
| `belts_pipes_transport.json` | `array` | 9 | 366 KB | transport registry | |
| `research_unlocks.json` | `array` | 436 | 1.7 MB | research ORM | |
| `simulation_systems.json` | `array` | 180 | **38 MB** | simulation C-lite | 가장 깊은 그래프 |
| `toolbar_entries.json` | `array` | 204 | 5.7 MB | toolbar tree | `display_name_key` = tree path |
| `translations.json` | `array` | **0** | 2 B | status only | `incomplete_sections` |
| `raw_type_index.json` | `array` | 6497 | 1.9 MB | CLR type index | |

전량 경로·스키마: **§부록 A** 또는 [`game_data_json_deep/README.md`](game_data_json_deep/README.md).

Import 순서: `registry.py` `IMPORT_ORDER` (manifest 선행).

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

## 5. 단순 자산 행 (snapshot 없음 또는 얕음)

### 5.1 `fluids.json`

- **Envelope:** 공통 + `definition_snapshot` (required).
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
  // definition_snapshot 없음
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
  asset_type: string;      // 관측: "asset.meta"
  ref_stable_id: string;   // 연결 대상 content stable_id
}
```

### 5.5 `raw_type_index.json`

CLR 리플렉션 인덱스 (게임 로직 타입 목록). **Envelope 확장:**

```typescript
interface RawTypeIndexRow extends SourceRowEnvelope {
  type_name: string;       // required — CLR 이름
  assembly_name: string;   // required
}
```

`source_type_name`은 6497종 이상 (게임·컴파일러 생성 타입 혼재). Importer는 `SimulationClrProvenance` 등에 연결.

### 5.6 `translations.json`

- **루트:** `array<empty>` — 덤프 실패/미포함 (`manifest.incomplete_sections`).

---

## 6. Shape 계열

### 6.1 `items.json` — `ShapeItem` 래퍼

- `source_type_name`: `"ShapeItem"` (70행).
- **`definition_snapshot`:** 래퍼 + 내부 `Definition`.

```typescript
interface ShapeItemSnapshot {
  $type: "ShapeItem";
  Definition: ShapeDefinitionBody;
}
```

### 6.2 `shapes.json` — 평탄 `ShapeDefinition`

- `source_type_name`: `"ShapeDefinition"` (1170행).
- **`definition_snapshot`:** 래퍼 없이 **본문이 곧** `ShapeDefinition` (`$type` 키는 존재).

### 6.3 `ShapeDefinitionBody` (공통 geometry)

Importer (`shape_recipes._shape_definition`)가 읽는 필드:

```typescript
interface ShapeDefinitionBody {
  $type?: "ShapeDefinition";
  UniqueOperationId: integer;
  PartCount: integer;              // 관측 4
  Hash: string;                    // quadrant 압축 해시 (예: "CuWuSuRu")
  Id: { Uid: integer } | { Name?: string };
  Layers: ShapeLayer[];
}
interface ShapeLayer {
  Parts: ShapePart[];              // 길이 = PartCount
}
interface ShapePart {
  Shape: UnityRefMetaShapeSubPart | string;  // 빈 문자열 = empty slot
  Color: UnityRefMetaShapeColor | string;
}
interface UnityRefMetaShapeSubPart {
  $unity: "MetaShapeSubPart";
  name: string;                    // CircleQuad, PinQuad, …
  instance_id: integer;
}
```

- `simulation_parameters`: `shapes.json` 행에 **optional 아님(required)** — shape 덤프에 부가 파라미터 동봉.

---

## 7. Building 계열

### 7.1 `buildings.json` vs `building_groups.json`（별도 부록 — 중복 무시）

| | `buildings.json` | `building_groups.json` |
| --- | --- | --- |
| Deep doc | [buildings.md](game_data_json_deep/buildings.md) | [building_groups.md](game_data_json_deep/building_groups.md) |
| Norm paths | 2285 | 2286 |
| Path diff | — | **+1** envelope: `description_key` |
| `definition_snapshot` paths | 동일（병합 스키마·TSV 기준） | 동일 |

동일 행 수(67)·동일 `source_type_name` `"BuildingDefinitionGroup"`. 스냅샷 트리는 사실상 동형；파일 차이는 **행 봉투 `description_key`** 뿐（groups 전용）.

### 7.2 `BuildingDefinitionGroup` snapshot (요약)

`definition_snapshot` 최상위에 그룹 메타 + `Definitions[]` 배열.

| 경로 (개념) | 타입 | Importer 사용 |
| ----------- | ---- | ------------- |
| `Id` / `Id.Name` | string \| object | internal name |
| `Title` / `Description` | lazy localized + `PlaceholderResolver` | localization keys |
| `Definitions[]` | `BuildingDefinition[]` | 멤버 building |
| `Definitions[].ConnectorData` | connector graph | footprint, IO |
| `Definitions[].ConnectorData.TileDimensions` | `{x,y,z: integer}` | |
| `Definitions[].ConnectorData.AllBuildingConnectors[]` | connector | |
| `Definitions[].ConnectorData.Tiles[]` | tile coords | |
| `IsTransportBuilding` | boolean | transport flag |
| `PlayerBuildable` / `Selectable` / `Removable` | boolean | |
| `DefaultPreferredPlacementMode` | string | |
| `simulation_parameters` | object | optional keys → simulation settings |

**ConnectorData** (building / transport 공통 패턴):

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

`PlacementIndicatorTypes[]` 등에 **CLR reflection 메타** (`Module.Assembly`, `DeclaredMembers`)가 깊게 중첩 — coverage manifest에서 `promoted` / `ignore_audit` 분류.

### 7.3 `building_variants.json`

```typescript
interface BuildingVariantRow extends SourceRowEnvelope {
  building_stable_id: string;  // required — 부모 building 행 stable_id
  definition_snapshot: BuildingDefinition;  // 단일 정의 스냅샷
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

9행, 벨트·파이프·와이어 등 transport building 정의.

---

## 8. `research_unlocks.json`

- **436행**, `source_type_name` 분포 (상위):
  - `ResearchSideQuest` (188)
  - `Game.Core.Research.ResearchUpgradeId` (168)
  - `ResearchSideUpgrade` (51)
  - `ResearchLevel` (13)
  - 매니저/설정 단일 행: `ResearchUnlockManager`, `ResearchConfig`, `ResearchProgression`, …

**Envelope 확장 (optional):**

| 필드 | 출현률(샘플) | 용도 |
| ---- | ------------- | ---- |
| `definition_snapshot` | 98% | 퀘스트/레벨/보상 그래프 |
| `manager_snapshot` | 2% | 진행 매니저 |
| `progression_layout` | 2% | 레이아웃 |
| `research_config` | 2% | 설정 |
| `simulation_parameters` | 32% | 부가 시뮬 캡처 |

**전형적 nested `$type` 경로:** `Lines[].Costs[]`, `Rewards[]`, `Title`/`Description.PlaceholderResolver`, `Levels[].Lines[]`.

---

## 9. `simulation_systems.json` (Phase 2 핵심)

- **180행**, **~38 MB** — 행당 `definition_snapshot` + 거의 항상 `simulation_parameters`.
- `source_type_name`: 제네릭 시뮬 시스템 CLR 이름 (예: `AtomicStatefulIslandSimulationSystem\`2[...]`).

### 9.1 행 구조

```typescript
interface SimulationSystemRow extends SourceRowEnvelope {
  definition_snapshot: SimulationSystemSnapshot;  // required
  simulation_parameters: SimulationRuntimeCapture;  // ~98% required
}
```

### 9.2 `simulation_parameters` (런타임 캡처, importer 주 경로)

샘플 최상위 키: `ConnectableSimulations`, `BeltSpeed` (행별 상이).

| 영역 | 대표 `$type` / 키 | Importer 프로필 |
| ---- | ----------------- | ---------------- |
| `SimulationFactory` | BeltSpeed, ConveyorSpeed, Configuration | `belt_policy`, factory |
| `ConnectableSimulations[]` | `Simulation`, `_Lanes[]`, `Connectors[]` | `connectable_graph` |
| Converter/building state | 제네릭 `AtomicStateful*` | `converter_runtime` |

**Connectable 그래프 (개념):**

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

행마다 시스템 타입과 동일한 `$type`이거나 `SimulationFactory` 하위 트리.  
`nested_$type` 상위 경로: `ConnectableSimulations[].Simulation._Lanes[]`, `SimulationFactory.Configuration.BeltSpeed`.

**Deep (47,104 norm paths):** [simulation_systems.md](game_data_json_deep/simulation_systems.md) · [simulation_systems.schema.txt](game_data_json_deep/simulation_systems.schema.txt) · [simulation_systems.paths.tsv](game_data_json_deep/simulation_systems.paths.tsv)  
**Aggregate hits:** [simulation_systems_paths_agg.tsv](game_data_json_deep/simulation_systems_paths_agg.tsv)（5,358 paths, `--normalized` 전 행）  
Legacy: `documents/game_data_analysis/simulation_systems/_nested_path_audit*.tsv`

---

## 10. `toolbar_entries.json`

- **204행**, `display_name_key` = **트리 경로** (예: `Root/.../Children[3]`).
- `source_type_name` 분포:
  - `BuildingBasedPlacementToolbarElementData` (78)
  - `IslandBasedPlacementToolbarElementData` (63)
  - `GroupToolbarElementData` (33)
  - `ToolbarSlotSeparator` (21)
  - 기타 카테고리/루트 (7)

```typescript
interface ToolbarRow extends SourceRowEnvelope {
  definition_snapshot: ToolbarElementSnapshot;
  simulation_parameters?: object;  // ~6% only
}
```

**스냅샷 패턴 (종류별):**

| Element kind | snapshot 핵심 |
| ------------ | ------------- |
| Island | `IslandGroup.Id.Name`, `IPlacementToolbarElementData.PlacerId` |
| Building | `BuildingDefinition` (+ `Definitions[]`, ConnectorData) |
| Group | `Children[]` (중첩 toolbar 노드) |
| Separator | 최소 필드 |

Importer: `toolbar_tree.import_toolbar_tree` — 4-pass, `tree_path` → `ToolbarTreeNode` 계층.

---

## 11. 부록 재생성（전량）

```bash
python scripts/analyze_game_data_json_deep.py
# → docs/domain/game_data_json_deep/{artifact}.{md,schema.txt,paths.tsv}

python scripts/audit_simulation_nested_paths.py --normalized \
  > docs/domain/game_data_json_deep/simulation_systems_paths_agg.tsv
```

| 산출물 | 내용 |
| ------ | ---- |
| `game_data_json_deep/*.paths.tsv` | **전 행** 순회 정규화 경로（47k+ for simulation） |
| `game_data_json_deep/*.schema.txt` | **전 행 병합** 중첩 타입 트리 |
| `simulation_systems_paths_agg.tsv` | simulation 전용 path×hits×max_list_len |

---

## 12. Importer 매핑 요약

| JSON | Django 정규화 (요약) |
| ---- | -------------------- |
| `manifest.json` | `ImportBatch`, `ArtifactChecksum`, `ExportWarning` |
| `fluids.json` | `FluidColor` |
| `shapes.json` / `items.json` | `ShapeRecipe`, `ShapeRecipeLayer`, `ShapeQuadrantSlot`, `ShapeRecipeSourceAppearance` |
| `building_*` | `BuildingGroup`, `BuildingVariant`, connectors, footprints, … |
| `prefabs` / `sprites` / `materials` | `GameContentAsset` |
| `asset_references.json` | `AssetMetaReference` |
| `research_unlocks.json` | Research* 모델군 |
| `simulation_systems.json` | `SimulationSystem`, `ConnectableSimulation`, lanes, connectors, audit |
| `toolbar_entries.json` | `ToolbarTreeNode`, `ToolbarElement`, placements |
| `belts_pipes_transport.json` | `TransportBuildingRegistry` |
| `raw_type_index.json` | CLR provenance |
| `translations.json` | `LocalizationExportStatus` (empty → incomplete) |

원시 `definition_snapshot` 전체는 ORM `JSONField`에 저장하지 않음 ([ADR-004](../adr/ADR-004-game-data-snapshot-boundary.md)).

---

## 13. 변경 이력

| 날짜 | 내용 |
| ---- | ---- |
| 2026-05-22 | 초판 — 17개 JSON 타입 구조·통계·importer 매핑 |
| 2026-05-22 | 심층 부록 A — 전 행 path/schema（`game_data_json_deep/`） |
