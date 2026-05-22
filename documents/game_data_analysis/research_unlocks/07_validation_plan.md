# Validation Plan — `research_unlocks.json`

> **pytest:** [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **금지**.

## Module

`tests/unit/game_data_import/test_research_unlocks_import.py`

## Checks

| # | Invariant |
| - | --------- |
| 1 | No orphan prerequisites or costs |
| 2 | UNIQUE `upgrade_key`; UNIQUE `node_key` per entity table |
| 3 | All `ShapeHash` resolve to `items.json` |
| 4 | Row kind enum valid (8 types) |
| 5 | Required fields per kind |
| 6 | `Lines` / `Costs` order preserved |
| 7 | Idempotent re-import |
| 8 | No domain PK from `stable_id` or CLR type names |
| 9 | No `research_unlocks_raw_json` |
| 10 | JSONField audit-only |
| 11 | Samples 32/207/231 traceable |
| 12 | Manifest hash gate |
| 13 | 168 duplicate stable_id pairs documented, not used as UK |
| 14 | Backing fields not imported |

## Fixtures

- Slice: milestone 32, upgrades 207/231 + minimal items hashes
- Slow: full 436 + manager layout

## CI

Run when `research_unlocks.json` or `items.json` changes.
