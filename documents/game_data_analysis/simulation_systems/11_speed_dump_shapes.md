# Speed dump shapes — `BuffableBeltSpeed` vs `MultipleBeltSpeed`

Verified against `documents/game_data/simulation_systems.json` (180 rows, **10** speed blobs).

## Inventory

| Parameter key | Count | `$type` | Table |
| ------------- | ----: | ------- | ----- |
| `BeltSpeed` | 1 | `BuffableBeltSpeed` | `simulation_buffable_speed` + `global_belt_speed_policy` |
| `ConveyorSpeed` | 4 | `BuffableBeltSpeed` | `simulation_buffable_speed` |
| `SpaceConveyorSpeed` | 3 | `BuffableBeltSpeed` | `simulation_buffable_speed` |
| `JumpSpeed` | 2 | `MultipleBeltSpeed` | `simulation_multiple_belt_speed` |

No row mixes `$type` with the wrong parameter name (e.g. no `JumpSpeed` + `BuffableBeltSpeed`).

## `BuffableBeltSpeed` shape

Keys only: `BaseSpeed`, `ResearchId`, `StepsPerTick`, `$type`.

| Field | Type in dump | Imported column |
| ----- | ------------ | --------------- |
| `BaseSpeed` | string enum (`OneSecondPerTile`, `QuarterSecondPerTile`, …) | `base_speed` |
| `ResearchId.Id` | string (`BeltSpeed`) | `research_upgrade` FK |
| `StepsPerTick.Value` | int | `steps_per_tick` |
| `$type` | `BuffableBeltSpeed` | `dump_type` |

## `MultipleBeltSpeed` shape

Keys only: `BaseSpeed`, `Multiplier`, `StepsPerTick`, `$type`.

| Field | Type in dump | Imported column |
| ----- | ------------ | --------------- |
| `BaseSpeed.$cycle` | always `BuffableBeltSpeed` | `cycle_ref_type` + `buffable_base` FK |
| `Multiplier` | int (`4`) | `multiplier` |
| `StepsPerTick.Value` | int (`100800`) | `steps_per_tick` |
| `$type` | `MultipleBeltSpeed` | `dump_type` |

Rows with both speeds (e.g. index 169): `ConveyorSpeed` buffable imported first; `JumpSpeed` links `buffable_base` to same-system buffable matching `cycle_ref_type`.

## Import routing (P2)

1. Classify by `$type`, then parameter name.
2. Reject param/`$type` mismatch → `UnknownProperty` (`sim_param_speed_shape_mismatch`).
3. Reject invalid field shapes → `UnknownProperty` (`sim_param_speed_shape_invalid`).
4. Never store raw blob on domain tables.

Tests: `tests/unit/game_data/test_speed_dump_shapes.py`, `test_simulation_speed_import.py`.
