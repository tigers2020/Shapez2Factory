# Reconstructed Schema — `simulation_systems.json`

**Implemented (C-lite):** Django `game_data` migrations `0005`–`0011`. Primary payload: `simulation_parameters` only. CLR strings → `SimulationClrProvenance` only (see [`10_clr_provenance.md`](10_clr_provenance.md)).

## Overview

| Table | Purpose | Source paths | Review status |
| ----- | ------- | ------------ | ------------- |
| `simulation_profile` | Extensible profile keys (no enum migration) | detected from `simulation_parameters` | **Implemented** |
| `simulation_system` | One row per dump element (180) | `[*]` envelope + parsed CLR | **Implemented** |
| `simulation_type` / `simulation_state_type` | CLR generic decomposition | `source_type_name` parse | **Implemented** |
| `simulation_clr_provenance` | CLR string + profile signature | `source_type_name` | **Implemented** (was `ImportAudit`) |
| `connectable_simulation` | `ConnectableSimulations[]` element | `simulation_parameters` | **Implemented** |
| `simulation_connector` + `simulation_connector_property` | Known scalars + typed extensions | `Connectors[]` | **Implemented** |
| `simulation_lane_definition` + `simulation_lane_runtime_state` | Lane def vs runtime | `_Lanes` / `InputLanes` | **Implemented** |
| `simulation_chunk_bounds` / `simulation_tile_bounds` | Bounds blocks | `ChunkBounds`, `TileBounds` | **Implemented** |
| `global_belt_speed_policy` | Batch-global belt tuning | `BeltSpeed` row 0 | **Implemented** (synced from buffable) |
| `simulation_buffable_speed` | `BuffableBeltSpeed` per param | `BeltSpeed`, `ConveyorSpeed`, `SpaceConveyorSpeed` | **Implemented** — shapes [`11_speed_dump_shapes.md`](11_speed_dump_shapes.md) |
| `simulation_multiple_belt_speed` | `MultipleBeltSpeed` | `JumpSpeed`; `cycle_ref_type` + FK buffable | **Implemented** |
| `simulation_runtime_audit` | Converter capture | heavy params only | **Implemented** |
| `simulation_system_parameter_key` | Top-level `simulation_parameters` key registry | key name + classification + `occurrence_count` | **Implemented** |
| `simulation_system_parameter_occurrence` | Per-row key presence | `simulation_parameters.<key>` path only; **no values** | **Implemented** |

**Removed (Phase A legacy):** `simulation_system_entry`, `simulation_factory_stub`, `clr_type_audit` on domain rows.

---

## `simulation_system`

| Column | Meaning | Constraints |
| ------ | ------- | ----------- |
| `import_batch_id` | FK | |
| `source_stable_id` | Dump hash | **UK** with `import_batch_id` (upsert key) |
| `source_row_index` | Array index | audit |
| `system_family` | Outer CLR / standalone name | |
| `profile_id` | FK → `simulation_profile` | |
| `canonical_id` | Grouping key (family+classes+profile) | **indexed, not unique** |
| `display_name_key` | Weak dump label | |

**Upsert:** `(import_batch_id, source_stable_id)` — never `canonical_id`.

**Grouping:** Many rows may share `canonical_id` (e.g. 38× `SpaceConveyorSimulation`).

---

## `connectable_simulation`

| Column | Meaning |
| ------ | ------- |
| `simulation_system_id` | FK |
| `connectable_key` | SHA1(variant\|connectors\|tiles\|connector_signature\|lane_signature) |
| `attachment_index` | Array order — **debug only** |
| `building_variant_id` | FK via `Building.Definition.Id` |
| `connector_signature` / `lane_signature` | Stored for audit |

**UK:** `(simulation_system_id, connectable_key)`.

---

## `simulation_connector_property`

Typed columns: `value_int`, `value_float`, `value_bool`, `value_text` (one populated per row).

---

## Anti-patterns rejected

| Rejected | Why |
| -------- | --- |
| `definition_snapshot` as domain source | Runtime wrapper |
| `canonical_id` as upsert key | Collapses 180 → ~61 rows |
| `canonical_id` UNIQUE | Same as above |
| `clr_type_audit` on `simulation_system` | → `simulation_clr_provenance` only |
| Domain JSONField | → `simulation_runtime_audit` only |
