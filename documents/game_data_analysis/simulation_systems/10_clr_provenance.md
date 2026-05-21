# Simulation CLR Provenance (`SimulationClrProvenance`)

**Former name:** `ImportAudit` (misleading — removed in migration `0011`).

## Purpose

One row per `simulation_systems.json` element stores the **raw Unity CLR generic string** from `source_type_name`, plus a **debug-only** `profile_signature` from `simulation_parameters` detection.

This table answers: *“What exact CLR type did the dump attach to this stable_id?”*

It does **not** answer: *“What happened during import?”* or *“What is the simulation domain config?”*

## What belongs here

| Column | Source | Role |
| ------ | ------ | ---- |
| `clr_type_string` | `source_type_name` | Full CLR string (audit / re-parse) |
| `profile_signature` | `detect_simulation_profile_key()` | Coarse params shape label |
| `source_stable_id`, `source_row_index`, `source_file` | Row provenance | Upsert + traceability |
| `import_batch` | Import run | Batch scope |

Parsed fields live elsewhere:

- `SimulationSystem.system_family`, `SimulationType`, `SimulationStateType` ← parsed CLR
- `SimulationSystem.profile` ← domain profile FK
- `SimulationSystemParameterKey` / `Occurrence` ← params **key** registry (no values)
- `UnknownProperty` ← non-domain params (preview + hash)
- `SimulationRuntimeAudit` ← converter capture only (only JSONField in simulation layer)

## What must NOT be stored here

- `simulation_parameters` JSON (whole or partial)
- `definition_snapshot`
- Delegate / reflection dumps (`OnSimulationCreated`, `Method`, `Logger`, …)
- Import warnings, checksum failures, or manifest metadata

Put those in `UnknownProperty`, `SimulationRuntimeAudit`, or `ImportBatch` children — not CLR provenance.

## Upsert keys

- ORM: `(import_batch_id, source_stable_id, source_file)` — UK `uq_sim_clr_prov_batch_stable_file`
- `canonical_id`: `sim-clr-prov:{batch_id}:{stable_id}` (legacy slug `import-audit:` rewritten in `0011`)

## Anti-patterns

| Wrong | Right |
| ----- | ----- |
| Rename back to `ImportAudit` | Implies blob / run audit |
| Add `audit_blob` JSONField | Use `SimulationRuntimeAudit` for converter-only capture |
| Query belt speed from this table | `GlobalBeltSpeedPolicy` |
| Use as domain registry | `SimulationSystem` + typed children |
