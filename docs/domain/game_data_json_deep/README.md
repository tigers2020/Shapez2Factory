# game_data JSON — deep structure appendix

목표: **데이터 구조 분석** — 중복·importer 편의와 무관하게 모든 아티팩트를 **전 행·전 경로**로 기록.

생성: `python scripts/analyze_game_data_json_deep.py`

`*.paths.tsv`는 용량(최대 ~860MB) 때문에 Git에 올리지 않는다. 클론 후 위 스크립트로 로컬 생성.

| file | root | rows | paths | schema |
| ---- | ---- | ---: | ----: | ------ |
| `asset_references.json` | array[829] | 829 | 8 | [`asset_references.schema.txt`](asset_references.schema.txt) · [`asset_references.paths.tsv`](asset_references.paths.tsv) |
| `belts_pipes_transport.json` | array[9] | 9 | 873412 | [`belts_pipes_transport.schema.txt`](belts_pipes_transport.schema.txt) · [`belts_pipes_transport.paths.tsv`](belts_pipes_transport.paths.tsv) |
| `building_groups.json` | array[67] | 67 | 5098854 | [`building_groups.schema.txt`](building_groups.schema.txt) · [`building_groups.paths.tsv`](building_groups.paths.tsv) |
| `building_variants.json` | array[131] | 131 | 1228043 | [`building_variants.schema.txt`](building_variants.schema.txt) · [`building_variants.paths.tsv`](building_variants.paths.tsv) |
| `buildings.json` | array[67] | 67 | 5098853 | [`buildings.schema.txt`](buildings.schema.txt) · [`buildings.paths.tsv`](buildings.paths.tsv) |
| `fluids.json` | array[9] | 9 | 12 | [`fluids.schema.txt`](fluids.schema.txt) · [`fluids.paths.tsv`](fluids.paths.tsv) |
| `items.json` | array[70] | 70 | 8023 | [`items.schema.txt`](items.schema.txt) · [`items.paths.tsv`](items.paths.tsv) |
| `manifest.json` | object[10 keys] | 0 | 319 | [`manifest.schema.txt`](manifest.schema.txt) · [`manifest.paths.tsv`](manifest.paths.tsv) |
| `materials.json` | array[4] | 4 | 7 | [`materials.schema.txt`](materials.schema.txt) · [`materials.paths.tsv`](materials.paths.tsv) |
| `prefabs.json` | array[764] | 764 | 7 | [`prefabs.schema.txt`](prefabs.schema.txt) · [`prefabs.paths.tsv`](prefabs.paths.tsv) |
| `raw_type_index.json` | array[6497] | 6497 | 8 | [`raw_type_index.schema.txt`](raw_type_index.schema.txt) · [`raw_type_index.paths.tsv`](raw_type_index.paths.tsv) |
| `research_unlocks.json` | array[436] | 436 | 695403 | [`research_unlocks.schema.txt`](research_unlocks.schema.txt) · [`research_unlocks.paths.tsv`](research_unlocks.paths.tsv) |
| `shapes.json` | array[1170] | 1170 | 8407 | [`shapes.schema.txt`](shapes.schema.txt) · [`shapes.paths.tsv`](shapes.paths.tsv) |
| `simulation_systems.json` | array[180] | 180 | 3328176 | [`simulation_systems.schema.txt`](simulation_systems.schema.txt) · [`simulation_systems.paths.tsv`](simulation_systems.paths.tsv) |
| `sprites.json` | array[61] | 61 | 7 | [`sprites.schema.txt`](sprites.schema.txt) · [`sprites.paths.tsv`](sprites.paths.tsv) |
| `toolbar_entries.json` | array[204] | 204 | 4142724 | [`toolbar_entries.schema.txt`](toolbar_entries.schema.txt) · [`toolbar_entries.paths.tsv`](toolbar_entries.paths.tsv) |
| `translations.json` | array[0] | 0 | 0 | [`translations.schema.txt`](translations.schema.txt) · [`translations.paths.tsv`](translations.paths.tsv) |

## Path TSV columns

- `norm_path` — `[]` 인덱스 정규화
- `row_hits` — 해당 경로 prefix를 가진 **행** 수 (리스트 원소별 아님)
- `value_types` — 관측 JSON 값 종류
- `$type_top` / `$unity_top` — CLR/Unity 태그 빈도
