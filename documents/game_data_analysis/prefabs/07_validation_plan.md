# Validation Plan — `prefabs.json`

> **pytest:** [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **금지**.

## Module

`tests/unit/game_data_import/test_prefabs_import.py`

## Checks

| # | Invariant |
| - | --------- |
| 1 | No orphan meta prefab FKs |
| 2 | 764 unique `stable_id` and `prefab_path` |
| 3 | All prefab `ref_stable_id` resolve |
| 4 | Required envelope keys |
| 5 | `source_row_index` preserves array order |
| 6 | Idempotent re-import |
| 7 | No domain PK from `UnityEngine.Object` |
| 8 | No `prefabs_raw_json` table |
| 9 | JSONField audit-only |
| 10 | Samples 65/415/463 traceable |
| 11 | Manifest hash gate |
| 12 | `prefab_path == source_path` for all |
| 13 | Import before `asset_references` |

## Fixtures

- Slice: indices 65, 415, 463 + golden stable_ids
- Slow: full 764 integration

## CI

Run when `prefabs.json` or `asset_references.json` changes.
