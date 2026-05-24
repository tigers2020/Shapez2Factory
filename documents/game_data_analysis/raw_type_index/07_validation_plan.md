# Validation Plan — `raw_type_index.json`

> **pytest:** [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **forbidden**.

## Module

`tests/unit/game_data_import/test_raw_type_index_import.py`

## Checks

| # | Invariant |
| - | --------- |
| 1 | No orphan rows without batch |
| 2 | UNIQUE (`type_name`, `assembly_name`) — 6497 |
| 3 | `stable_id` not UNIQUE (expect duplicate count 114) |
| 4 | Required keys on every row |
| 5 | `source_type_name == type_name` always |
| 6 | Empty `source_path`, `source_guid`, `display_name_key` |
| 7 | Idempotent re-import |
| 8 | No table named after sampled CLR types |
| 9 | No `raw_type_index_raw_json` |
| 10 | JSONField audit-only |
| 11 | Samples 524/3325/3710 traceable |
| 12 | Manifest hash gate |
| 13 | `ShapeItem` lookup resolves ≥1 row |
| 14 | Compiler-generated flag on sample 3325 |

## Performance

- Bulk `bulk_create` / upsert in batches of 500 for CI slow test marker.

## CI

Run when `raw_type_index.json` changes; full hash required.
