# JSON Path Mapping — `simulation_systems.json`

| JSON path | Observed meaning | Classification | Target table | Target column | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ----- |
| `[i].stable_id` | Row hash | source metadata | `simulation_system_entry` | `stable_id` | UNIQUE |
| `[i].source_type_name` | CLR generic type | runtime metadata | `simulation_system_entry` | `clr_type_audit` | parse kind |
| `(parsed)` | Short sim class | entity attribute | `simulation_system_entry` | `simulation_kind_key` | e.g. SpaceConveyorSimulation |
| `[i].display_name_key` | Weak label | source metadata | `simulation_system_entry` | `display_name_key` | |
| `[i].simulation_parameters.SimulationFactory` | Factory stub | unknown/audit | `simulation_factory_stub` | — | 143 rows |
| `[i].simulation_parameters.BeltSpeed` | Global belt config | entity attribute | `global_belt_speed_policy` | scalars | row 0 |
| `[i].simulation_parameters.ConnectableSimulations[]` | Attachments | ordered child | `connectable_simulation_attachment` | — | 6 rows |
| `…ConnectableSimulations[j].NumConnectors` | Connector count | entity attribute | `connectable_simulation_attachment` | `num_connectors` | |
| `…ConnectableSimulations[j].Building` | Building instance | relationship | audit / future FK | — | review |
| `[i].definition_snapshot.ISimulationSystem.*` | Delegates | runtime metadata | `simulation_runtime_audit` | — | never domain |
| `manifest.file_hashes.simulation_systems.json` | Digest | source metadata | artifact checksum | — | |
| `building_variants` names (textual) | Inferred link | relationship | `simulation_kind_key` | — | no FK in JSON |
