# Cross-Reference Analysis — `simulation_systems.json`

## Diagram

```text
game_data_import_batch
  └─ has many → simulation_system_entry (180)
        ├─ optional 1:1 → simulation_factory_stub (143)
        ├─ optional 1:1 → simulation_runtime_audit (converter rows)
        ├─ has many → connectable_simulation_attachment (6 graphs)
        └─ (kind key) inferred → building_variant / transport_kind (textual)

global_belt_speed_policy
  └─ research_upgrade_key → research_upgrade (BeltSpeed)

simulation_system_entry (SpaceConveyorSimulation)
  └─ inferred → belts_pipes_transport / wire belt kinds
```

## FK relationships

| From | To | Status |
| ---- | -- | ------ |
| `simulation_factory_stub` | `simulation_system_entry` | 1:1 |
| `connectable_simulation_attachment` | `simulation_system_entry` | N:1 |
| `global_belt_speed_policy` | `research_upgrade` | key `BeltSpeed` — **resolved** in research dump |
| `Building.Definition` | `building_variant` | **unresolved** — nested snapshot, no stable_id |

## M2M

None explicit; connectable list is ordered children, not M2M table.

## Inferred references

| Reference | Status |
| --------- | ------ |
| `BeltSpeed` research id | **resolved** |
| Transport kinds in text | **inferred** (9/9) |
| Building variant names in text | **inferred** (131/131) |
| `raw_type_index` type names | name-only |

## Unresolved

- Converter row object graphs (18) — no stable cross-ids
- Which of 38 `SpaceConveyorSimulation` rows differ only by factory instance

## Source metadata

- Full CLR `source_type_name` strings on every row
- Delegate and backing-field keys in snapshots
