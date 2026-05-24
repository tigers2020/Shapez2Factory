# Semantic Contract Violations

## Criteria

- canonical refs: `01_project_overview.md`, `03_data_schema_dto.md`, `13_step9_validation.md`, `14_step10_replay_ui.md`

## Violation / drift list

| File | Finding | Suspected root cause | Canonical refs | Severity | Confidence | Action |
|---|---|---|---|---|---|---|
| `django_apps/asteroid_lab/services/replay_pipeline_service.py` | creates `SolverRun`/`ReplayTrack` with `algorithm_label="inspection_only"`, appearing like solver pipeline | inspection replay scaffold forced into solver domain | `01_project_overview.md` §2, `02_pipeline_control_flow.md` | `P1` | High | `rewrite` |
| `django_apps/asteroid_lab/models.py` | `CandidateBundle`, `RoutingProbe`, `SolverMetricSnapshot` not connected to live flow | premature persistence of future solver schema | `03_data_schema_dto.md`, `02_pipeline_control_flow.md` | `P1` | High | `deprecate` |
| `django_apps/web/views/public_pages.py` | retries when `"force=True"` appears in error string | missing typed failure contract | `02_pipeline_control_flow.md` | `P1` | High | `rewrite` |
| `django_apps/asteroid_lab/services/input_service.py` | `persist_decoded_snapshot(...)` mutates “project’s latest map_input” | mutation contract without explicit target row | `03_data_schema_dto.md` §E | `P1` | Medium | `rewrite` |
| `django_apps/web/services/asteroid_lab_page_context.py` | serializer promotes `cell_overlay_json.cells` to full_map when `frame_payload.full_map` missing | output schema authority fragmented | `14_step10_replay_ui.md` §16.3 | `P1` | High | `isolate` |
| `django_apps/asteroid_lab/services/dto.py` | replay, decode, inspection, topology, orchestration meanings mixed in one DTO file | convenience over boundaries | `03_data_schema_dto.md` | `P1` | High | `split` |

## Absent items vs canonical

These are closer to “not defined in current live tree” than “wrongly implemented.”

| Missing contract | Live status | Canonical refs | Severity | Action |
|---|---|---|---|---|
| `PlacementCommitState` FSM | none | `03_data_schema_dto.md` §B | `P1` | `migrate` |
| `RecoveryTrigger / CommitReason / RollbackReason` separation | none | `03_data_schema_dto.md` §B, `11_step8_recovery.md` | `P1` | `migrate` |
| assertion-only final validation | no dedicated module | `13_step9_validation.md` | `P1` | `migrate` |
| cycle-based streaming trace | 5-frame snapshot replay only | `14_step10_replay_ui.md` §16.1 | `P1` | `migrate` |
| protected corridor lifecycle | no dedicated types/modules | `12_protected_corridor.md` | `P1` | `migrate` |

## Notes

Current live `asteroid_lab` reads correctly as an “initial decode/inspection/replay observation lab” for the canonical solver, but `SolverRun` and related model naming make a full solver easy to misread. Remove this semantic drift first or follow-up refactors will keep proceeding on the wrong contract.
