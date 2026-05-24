---
status: ARCHIVED
last_reviewed: 2026-05-16
superseded_by: []
---

> **Archive premise (2026-05-16)**: The `documents/Algorithm/mining_solver_cursor_sessions/` tree cited by this audit was removed from the repository. **Do not use deleted canonical paths as current implementation authority.** At audit time the live surface was the `django_apps/asteroid_lab` family. For later state see [`documents/index/document_inventory.md`](../../index/document_inventory.md), [`documents/ai/current_plan.md`](../../ai/current_plan.md).

# Asteroid Solver Refactor Audit — Global Summary

## Audit scope

- live code: `django_apps/asteroid_lab/`, `django_apps/web/services/asteroid_lab_page_context.py`, `django_apps/web/views/public_pages.py`, `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`, `tests/unit/asteroid_lab/`, `tests/integration/web/test_asteroid_miner_layout_solver.py`
- canonical authority: `documents/Algorithm/mining_solver_cursor_sessions/README.md`, `01_project_overview.md`, `02_pipeline_control_flow.md`, `03_data_schema_dto.md`, `13_step9_validation.md`, `14_step10_replay_ui.md`

## Top-level conclusion

The live surface in the current checkout is not the `django_apps/shapez_asteroid/.../asteroid_mining_layout(_v2)` family assumed by the prompt, but a decode + inspection + replay lab shell based on `django_apps/asteroid_lab`. The Pass1/Pass2/STEP4 routing/Pass3/recovery/final validation/protected corridor solver defined in canonical docs is not implemented in the live tree, or only partially reflected in naming.

In other words, the core risk of this audit is “refactoring the wrong target” before “bad implementation.” Canonical docs assume a full solver, but live code centers on an inspection replay generator and UI shell.

## Drift Severity

- Overall drift severity: `severe`
- Status vs canonical: `partial implementation + naming preemption + output-layer over-coupling`
- Stabilization difficulty: `high`

## Major corruption vectors

| Vector | live evidence | canonical conflict | severity |
|---|---|---|---|
| canonical/live namespace mismatch | live tree is `django_apps/asteroid_lab/`; expected prompt paths absent | `README.md`, `01_project_overview.md`, `02_pipeline_control_flow.md` are full mining solver canon | `P0` |
| replay layer owns reconstruction execution | `django_apps/asteroid_lab/replay/snapshot_map_replay.py` | `14_step10_replay_ui.md` §16, `13_step9_validation.md` treat replay as output-only | `P1` |
| orchestration over-coupling | `django_apps/asteroid_lab/services/replay_pipeline_service.py` | Misaligned with step separation in `02_pipeline_control_flow.md` | `P1` |
| solver semantic naming drift | `SolverRun`, `CandidateBundle`, `RoutingProbe`, `SolverMetricSnapshot` exist but pipeline is inspection-only | Misaligned with solver step contracts in `01_project_overview.md`, `03_data_schema_dto.md` | `P1` |
| validation/recovery/protected corridor absent | no corresponding modules inside `asteroid_lab` | `11_step8_recovery.md`, `12_protected_corridor.md`, `13_step9_validation.md` | `P1` |
| UI contract tied to ad hoc replay JSON, not canonical trace | `django_apps/web/services/asteroid_lab_page_context.py`, `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Misaligned with `trace_event`, cycle streaming canon in `14_step10_replay_ui.md` | `P1` |

## Recommended refactor order

1. Fix canonical/live mapping first.
2. Separate reconstruction computation from replay/output layer.
3. Decompose `build_initial_replay_for_map_input(...)` into step-wise orchestration services.
4. Freeze or deprecate solver naming models not actually implemented in the live tree.
5. Split DTOs into replay/decode/inspection/topology.
6. Declare validation/recovery/protected corridor as “absent” and move to a follow-up migration plan.
7. Realign web replay contract to canonical trace schema.
8. Strengthen import-boundary/SCC/canonical-alignment tests.

## Recommended Freeze Zones

Do not touch these areas in early phases:

- `django_apps/asteroid_lab/reconstruction/pipeline.py`
- `django_apps/asteroid_lab/reconstruction/fill.py`
- `django_apps/asteroid_lab/snapshots/transport_components.py`
- `django_apps/asteroid_lab/snapshots/server_coords.py`
- `django_apps/asteroid_lab/adapters/decode_adapter.py`

These are relatively pure-function areas in the current live tree; modifying them before decoupling orchestration/replay coupling yields low payoff.

## Dangerous Central Orchestrators

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/web/views/public_pages.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/web/services/asteroid_lab_page_context.py`

## Immutable DTO layer candidates

- Current candidate: `django_apps/asteroid_lab/services/dto.py`
- Target state: split as below
  - `dto/replay.py`
  - `dto/decode.py`
  - `dto/existing_layout.py`
  - `dto/topology.py`
  - `dto/orchestration.py`

## Structural verification summary

- internal SCC scan: no multi-file SCC inside `django_apps/asteroid_lab`
- targeted structural pytest: `147 passed`
- existing import guard: `tests/unit/asteroid_lab/test_service_import_boundaries.py`

## Stabilization Difficulty

- phase 1: `medium` — document/boundary realignment
- phase 2: `high` — replay/runtime separation
- phase 3: `high` — semantic model cleanup and canonical solver migration
