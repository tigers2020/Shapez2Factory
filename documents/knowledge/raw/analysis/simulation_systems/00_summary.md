# File Inventory — `simulation_systems.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/simulation_systems.json` |
| File name | `simulation_systems.json` |
| File size | **~38,111,900 bytes** |
| Manifest hash | `sha256:37f0cf1a93e0002669ed9db18b6242eac5d79bdc164b0694cf4e7f4fab5d57d3` |
| Dump context | `manifest.json` → `runtime_reflection`, v2 export |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **180** |
| Envelope keys | `stable_id`, `source_type_name`, `source_guid`, `source_path`, `display_name_key`, `definition_snapshot`, `simulation_parameters` |

## Row shape clusters (by `simulation_parameters` signature)

| Profile | Count (approx.) | Meaning |
| ------- | --------------- | ------- |
| `SimulationFactory` only | **143** | Generic atomic system shell — minimal factory stub |
| Converter runtime graph | **18** | `SpaceConverterSystem` — large captured instance state |
| `ConnectableSimulations` list | **6** | Island/tenant graphs with building attachments |
| `BeltSpeed` + connectables | **1** | Global belt speed policy (`TrashSimulationSystem` row) |
| Other mixed signatures | **12** | Small island/hub/specialized variants |

**`definition_snapshot` ≠ `simulation_parameters`** on all 180 rows (separate capture channels).

## `source_type_name` (runtime labels — not domain PK)

| Pattern | Count | Parsed kind (examples) |
| ------- | ----- | ------------------------ |
| `AtomicStatefulIslandSimulationSystem`2[[…]]` | 62+ | `SpaceConveyorSimulation`, `SpaceSplitterSimulation`, … |
| `Game.Content.AtomicIslands.Converters.SpaceConverterSystem` | 18 | `SpaceConverterSystem` |
| `AtomicStatefulBuildingSimulationSystem`2[[…]]` | 60+ | `RotatorSimulation`, `StackerSimulation`, … |
| Standalone CLR types | few | `TrashSimulationSystem`, etc. |

**180 unique `stable_id`** — usable for import correlation, not as human-facing domain id.

## Nested structures (selected)

| Path | Where | Notes |
| ---- | ----- | ----- |
| `simulation_parameters.ConnectableSimulations[]` | 6 rows | Building + Simulation + connector/tile bounds |
| `simulation_parameters.BeltSpeed` | 1 row | `BaseSpeed`, `ResearchId`, `StepsPerTick` |
| `simulation_parameters.SimulationFactory` | 143 rows | opaque factory object |
| `definition_snapshot` delegate keys | converter rows | `ISimulationSystem.*` — **audit only** |
| `ConnectableSimulations[].Building.Definition` | connectable rows | nested building snapshot — **normalize, do not mirror** |

## Arrays / nested objects

- Heavy nesting in 18 converter rows and 6 connectable-graph rows drive file size (~38 MB).
- 143 minimal rows contribute little payload each.

## Candidate IDs

| Field | Role |
| ----- | ---- |
| Parsed **simulation_kind_key** (short CLR simulation class name) | **Canonical business key** (+ row disambiguation) |
| `stable_id` | Unique per row — audit / import batch |
| `source_type_name` | Full generic CLR string — **runtime metadata only** |
| `display_name_key` | Often generic (`AtomicStatefulIslandSimulationSystem`2`) — weak |
| `Building` in connectable entries | Relationship to building definitions — **review** |

## Runtime / reflection / debug (must not become models)

- `AtomicStatefulIslandSimulationSystem`2[[Game.Content…, Version=0.0.0.0, PublicKeyToken=null], …]`
- `ISimulationSystem.OnSimulationCreated`, `<*k__BackingField>`, `$type`
- `Game.Content.AtomicIslands.*` assembly-qualified strings

## Cross-file references

| File | Relationship |
| ---- | ------------ |
| `building_variants.json` | **131/131** variant names appear in file text (no stable FK) |
| `belts_pipes_transport.json` | All 9 `transport_kind` strings referenced in text |
| `raw_type_index.json` | CLR types (e.g. `SpaceConveyorSimulationRenderer`) name-aligned only |
| `buildings.json` | **0** `source_guid` hits — linkage by name/kind only |

## Design implication

Extract **`simulation_system_entry`** (180 rows) with parsed **`simulation_kind_key`**, optional **`global_belt_speed_policy`**, **`connectable_simulation_attachment`** children, and **`simulation_factory_stub`** for minimal rows — store delegate graphs and 38 MB blobs only in audit/`unknown_property`, never as primary domain JSON.
