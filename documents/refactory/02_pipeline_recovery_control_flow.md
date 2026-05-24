# Goal: Pipeline·Recovery Control Flow Aligned with §4.3

## Background

- Canonical: `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` §4.1–§4.3, `11_step8_recovery.md` §13.2.
- Implementation: `recovery_orchestrator.run_solver_timeline_pipeline` repeats Pass3→P4→finalize on a **fixed `routing_snapshot`** after STEP4; on failure mainly loops through `validation_recovery`.

## Mini-Audit Deliverable (Pre-Implementation)

- **First-pass table and canonical citations:** [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) §5 (full GitHub `master` §4.3 table + implementation mapping + PR review A/B/Info).

## Current State

- Per-trigger recovery (e.g. `pass3_connectivity_break` → Pass3 rollback then **STEP 6 Reclaim**, etc.) may **not map 1:1** to the document table.
- Orchestrator docstring summarizes as "bounded Pass3→P4→finalize".

## Target State

- **Explicitly choose** one of the following and reflect in docs or code:
  - **A)** Align implementation to canonical table (recovery point, rollback order, re-entry conditions).
  - **B)** Document current implementation as "MVP simplification" as **official exception** in canonical (add "implementation mapping" column beside table).

## Work Items

1. Per-trigger **current code path** table: [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) **§5.3** (with canonical §5.2 citation). PR review **A/B/Info** finalized in **§5.4**.
2. Largest gaps first: §4.3.1 Reclaim recovery vs current loop — confirm intent then A or B.
3. Decide whether to record "document table row ID" in `recovery_contract_phases` / replay.

## Verification

- Unit test: for at least one trigger, fix "stage order after recovery" as snapshot assertion.

## Risk

- Control flow changes have heavy Pass3·P4·finalize interdependence — update **regression tests and NDJSON contract** together.

## Reference Code

- `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/recovery_orchestrator.py`
- `solver_pipeline/pass3.py`, `p4_reclaim.py`, `finalize.py`
