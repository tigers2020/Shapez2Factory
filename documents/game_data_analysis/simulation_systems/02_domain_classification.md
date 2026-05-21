# Domain Classification — `simulation_systems.json`

## Envelope

| Path | Classification |
| ---- | -------------- |
| `stable_id` | source metadata (unique; correlate import) |
| `source_type_name` | **runtime / reflection / debug metadata** |
| `display_name_key` | source metadata (often generic) |
| `source_guid`, `source_path` | source metadata (frequently empty) |
| `definition_snapshot` | source metadata wrapper (runtime state) |
| `simulation_parameters` | **domain-relevant extract** (selective) |

## Extractable domain fields

| Path | Classification |
| ---- | -------------- |
| Parsed simulation class name | **entity attribute** (`simulation_kind_key`) |
| `simulation_parameters.BeltSpeed.*` | entity attribute → `global_belt_speed_policy` |
| `ConnectableSimulations[]` | ordered child record |
| `ConnectableSimulations[].Building` | relationship → building definition (review) |
| `ConnectableSimulations[].NumConnectors` | entity attribute |
| `SimulationFactory` | unknown / audit — opaque object |

## Runtime-only (reject for domain tables)

| Path | Classification |
| ---- | -------------- |
| `ISimulationSystem.*` delegate paths | runtime metadata |
| `ILogger`, `Interlock`, `ShapeRegistry` instance fields | runtime metadata |
| `<*k__BackingField>` | runtime metadata |
| Full `AtomicStateful*System`2[[…]]` string | runtime metadata |
| `$type` | source metadata |

## Inferred entities

| Entity | Count |
| ------ | ----- |
| Simulation system registration | 180 |
| Global belt speed policy | 1 |
| Connectable attachment | sum of list lengths (6 graphs) |
| Factory stub reference | 143 |
