# Risks and Open Questions — `simulation_systems.json`

## Uncertain meaning

| Item | Risk |
| ---- | ---- |
| 38 MB payload | Memory/timeouts if parsed naïvely |
| 143 identical-looking factory rows | Redundant registry vs distinct instances |
| `Building.Definition` in connectable | Huge nested graphs — scope creep |
| 18 converter runtime dumps | Little planner value |

## Human review

| Question |
| -------- |
| Import converter rows into audit only? |
| Collapse 38 `SpaceConveyorSimulation` rows to one kind + count? |
| Extract `building_kind_key` from nested Definition? |

## Runtime traps

- Django model `AtomicStatefulIslandSimulationSystem`
- PK = full generic CLR string
- Promoting `ISimulationSystem.OnSimulationCreated` to columns

## Ambiguous IDs

- `simulation_kind_key` repeats across rows (38 conveyors) — need `stable_id` or `source_row_index` as surrogate
- `display_name_key` useless for disambiguation

## Dynamic schema

- 16 snapshot signatures — importer must branch by profile

## Version drift

- Manifest hash + file size watchdog in CI

## Missing targets

| Target | Status |
| ------ | ------ |
| FK to `building_variant.stable_id` | Not in JSON |
| FK to `source_guid` | Empty / no hits |

## Deferred tables

| Table | Reason |
| ----- | ------ |
| `simulation_delegate_binding` | Runtime hooks |
| `island_config_blob` | Converter Config |

## Highest risk

**Storing `definition_snapshot` / `simulation_parameters` wholesale in domain JSONField** — reproduces 38 MB anti-pattern. **Mitigation:** profile-based extraction + audit-only blob for converter captures.
