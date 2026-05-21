# Reconstructed Schema — `simulation_systems.json`

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `simulation_system_entry` | Registry row | What simulation implementations appear in dump? | `[*]` envelope + parsed kind | buildings (name), transport | Observed |
| `simulation_factory_stub` | Minimal systems | Which kinds are factory-only shells? | `SimulationFactory` rows | entry FK | Observed |
| `global_belt_speed_policy` | Belt tuning | Global belt speed research/buff? | row 0 `BeltSpeed` | research_upgrade | Observed |
| `connectable_simulation_attachment` | Graph slots | Which buildings attach to connectable sim? | `ConnectableSimulations[]` | building defs | Review |
| `simulation_runtime_audit` | Heavy captures | Opaque converter/runtime state | converter snapshots | — | Audit only |
| `game_data_import_batch` | Provenance | Which dump? | manifest | → all | Observed |
| `unknown_property` | Extensions | Unmapped keys | any | audit | Planned |

---

## `simulation_system_entry`

**Domain question:** “Which simulation system kinds are registered for this export?”

| Column | Meaning | Source | Inferred? | Constraints |
| ------ | ------- | ------ | --------- | ----------- |
| `id` | PK | surrogate | yes | PK |
| `stable_id` | Dump hash | `[*].stable_id` | observed | UNIQUE |
| `simulation_kind_key` | Short kind name | parse `source_type_name` | inferred | INDEX |
| `system_family` | island / building / converter / other | parse rules | inferred | enum |
| `parameter_profile` | factory / connectable / converter / belt | shape detection | inferred | enum |
| `clr_type_audit` | Full CLR string | `source_type_name` | observed | TEXT |
| `display_name_key` | Dump label | envelope | observed | |
| `import_batch_id` | FK | manifest | inferred | FK |
| `source_row_index` | Array index | `i` | inferred | UNIQUE/batch |

**Unique:** `stable_id`; optional UNIQUE (`import_batch_id`, `simulation_kind_key`, `source_row_index`) if kinds repeat per row.

**Human review:** Whether `simulation_kind_key` alone is enough for planner (38 conveyor rows share kind).

---

## `global_belt_speed_policy`

| Column | Source (`BeltSpeed`) |
| ------ | -------------------- |
| `base_speed` | `BaseSpeed` (e.g. `OneSecondPerTile`) |
| `research_upgrade_key` | `ResearchId.Id` |
| `steps_per_tick` | `StepsPerTick.Value` |
| `import_batch_id` | FK |

**Cardinality:** one row per import batch (singleton in this dump).

---

## `connectable_simulation_attachment`

| Column | Meaning |
| ------ | ------- |
| `simulation_system_entry_id` | FK |
| `attachment_index` | array order |
| `num_connectors` | scalar |
| `num_occupied_tiles` | scalar |
| `building_ref_json` | **audit only** if Definition too large — or extract `building_kind_key` |

**Do not** mirror full `Building.Definition` tree into dozens of tables.

---

## `simulation_factory_stub`

| Column | Meaning |
| ------ | ------- |
| `simulation_system_entry_id` | FK 1:1 |
| `factory_type_name` | from `$type` or factory object |

For 143 rows with only `SimulationFactory`.

---

## `simulation_runtime_audit`

| Column | Meaning |
| ------ | ------- |
| `simulation_system_entry_id` | FK |
| `audit_blob` | JSON **only here** for converter rows |

Allowed JSONField **only** in audit table, not domain logic tables.

---

## Anti-patterns rejected

| Rejected | Why |
| -------- | --- |
| `simulation_systems_raw_json` | 38 MB forbidden |
| Table `AtomicStatefulIslandSimulationSystem` | CLR generic name |
| PK = full `source_type_name` | Runtime string |
| 180 JSONField blobs | Normalize extracts |
