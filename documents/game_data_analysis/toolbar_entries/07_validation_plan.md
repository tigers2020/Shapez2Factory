# Validation Plan — `toolbar_entries.json`

`tests/unit/game_data_import/test_toolbar_entries_import.py`

| # | Invariant |
| - | --------- |
| 1 | 204 `toolbar_element` rows |
| 2 | UNIQUE `stable_id`, `tree_path` |
| 3 | 78 building + 63 island + 21 separator counts |
| 4 | `building_definition_key` present on building rows |
| 5 | Tree edges: single root, no cycles (path parse) |
| 6 | Icon names ⊆ `sprite_asset` when set |
| 7 | Idempotent re-import |
| 8 | No model named `BuildingBasedPlacementToolbarElementData` |
| 9 | No `toolbar_entries_raw_json` |
| 10 | Samples 16/103/115 traceable |
| 11 | Manifest hash gate |

## Slow test

Full 204 import marked `@pytest.mark.slow`.
