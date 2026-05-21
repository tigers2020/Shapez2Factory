# Validation Plan — `sprites.json`

`tests/unit/game_data_import/test_sprites_import.py`

| # | Invariant |
| - | --------- |
| 1 | 61 rows |
| 2 | UNIQUE `stable_id`, `sprite_path` |
| 3 | 61 meta sprite refs resolve |
| 4 | Required envelope keys |
| 5 | Idempotent re-import |
| 6 | No `UnityEngineObject` PK |
| 7 | No `sprites_raw_json` |
| 8 | Samples 4/25/28 traceable |
| 9 | Manifest hash gate |
| 10 | Import before asset_references |

## CI

Run when `sprites.json` or `asset_references.json` changes.
