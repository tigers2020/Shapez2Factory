# Validation Plan — `simulation_systems.json`

> **pytest:** [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **금지**.

## Module

`tests/unit/game_data/test_simulation_systems_import.py`

## Checks

| # | Invariant |
| - | --------- |
| 1 | 180 `simulation_system` rows per batch |
| 2 | UK `(import_batch, source_stable_id)` |
| 3 | `canonical_id` indexed, **not** UNIQUE |
| 4 | CLR only on `simulation_clr_provenance` (not `ImportAudit`) |
| 5 | Belt policy from `simulation_parameters.BeltSpeed` |
| 13 | Typed speeds: buffable (Belt/Conveyor/SpaceConveyor) + multiple (Jump) counts match dump |
| 6 | `connectable_key` includes connector/lane signatures |
| 7 | `SimulationConnectorProperty.value_int` filterable |
| 8 | JSONField only on `simulation_runtime_audit` |
| 9 | Idempotent re-import |
| 10 | Migration 0007 gates 0008 |
| 11 | Parameter key registry: occurrences without JSON values; stable `occurrence_count` on re-import |
| 12 | Ignored sim params: `UnknownProperty` with `reason_code` / `classification`; idempotent re-import |

## Fixtures

- Minimal: 3 sampled rows + synthetic factory stub
- Slow: full 180 (CI optional)

## CI

Run when `simulation_systems.json` or `building_variants.json` changes.
