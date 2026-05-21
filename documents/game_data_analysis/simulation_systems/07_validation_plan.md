# Validation Plan — `simulation_systems.json`

## Module

`tests/unit/game_data_import/test_simulation_systems_import.py`

## Checks

| # | Invariant |
| - | --------- |
| 1 | 180 `simulation_system_entry` rows |
| 2 | UNIQUE `stable_id` |
| 3 | `simulation_kind_key` parsed for all rows |
| 4 | 143 factory profile rows |
| 5 | 1 global belt policy row with `research_upgrade_key=BeltSpeed` |
| 6 | Connectable attachments preserve order |
| 7 | No domain table named `AtomicStateful*` |
| 8 | No `simulation_systems_raw_json` |
| 9 | JSONField only on `simulation_runtime_audit` / `unknown_property` |
| 10 | Idempotent re-import |
| 11 | Samples 16/103/115 traceable |
| 12 | Manifest hash gate |
| 13 | CLR type stored only in `clr_type_audit` |
| 14 | Backing-field keys not imported as columns |

## Fixtures

- Minimal: 3 sampled rows + synthetic factory stub
- Slow: full 180 (CI optional)

## CI

Run when `simulation_systems.json` or `building_variants.json` changes.
