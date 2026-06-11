# Validation Plan — `shapes.json`

> **pytest:** [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **forbidden**.

## Module

`tests/unit/game_data_import/test_shapes_import.py`

## Checks

| # | Invariant |
| - | --------- |
| 1 | No orphan layers/slots |
| 2 | 1170 UNIQUE `shape_hash` and `operation_uid` |
| 3 | All 70 `items.json` hashes present |
| 4 | All 253 research `ShapeHash` present |
| 5 | `PartCount == 4` |
| 6 | Layer/hash segment alignment |
| 7 | Idempotent re-import |
| 8 | No PK `ShapeDefinition` or `#N` display key |
| 9 | No `shapes_raw_json` |
| 10 | JSONField audit-only |
| 11 | Samples 131/831/927 traceable |
| 12 | Manifest hash gate |
| 13 | `items` row byte-equal to shapes row for shared hash (optional golden) |

## Performance

Bulk insert batches; mark slow test for full 1170.

## CI

Run when `shapes.json`, `items.json`, or `research_unlocks.json` changes.
