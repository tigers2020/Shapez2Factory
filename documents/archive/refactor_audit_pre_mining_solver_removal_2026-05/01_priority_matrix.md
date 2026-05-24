# Priority Matrix

| Priority | File | System | Issue | Risk | Recommended Action |
|---|---|---|---|---|---|
| P0 | `django_apps/asteroid_lab/` | namespace / architecture | live tree differs from canonical solver path | refactoring wrong target, doc–implementation misjudgment | `freeze` |
| P1 | `django_apps/asteroid_lab/replay/snapshot_map_replay.py` | replay vs runtime | output-only module runs `run_reconstruction(...)` | replay/runtime contamination, layer collapse | `split` |
| P1 | `django_apps/asteroid_lab/services/replay_pipeline_service.py` | orchestration | decode, normalize, persist, run-row, replay, snapshot save in one function | side effect cascade, hard to test | `split` |
| P1 | `django_apps/asteroid_lab/services/existing_layout_service.py` | inspection / replay | inspection service performs snapshot reload + reconstruction replay generation | weakened read-only analysis boundary | `split` |
| P1 | `django_apps/web/views/public_pages.py` | web integration | retry branch via `"force=True"` string | stringly control flow, hidden contract | `rewrite` |
| P1 | `django_apps/asteroid_lab/models.py` | semantic model | `SolverRun`/`CandidateBundle`/`RoutingProbe`/`SolverMetricSnapshot` preempted without real solver | domain drift, dead schema spread | `deprecate` |
| P1 | `django_apps/web/services/asteroid_lab_page_context.py` | replay UI adapter | treats ad hoc `lab_replay_frames_json` contract as canonical, not canonical trace | UI contract drift | `isolate` |
| P1 | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | replay UI | 1278-line monolith JS owns replay render, fetch, modal, frame control | change risk, wider regression surface | `split` |
| P1 | `django_apps/asteroid_lab/services/dto.py` | DTO | replay/decode/inspection/topology/orchestration DTOs mixed in one file | semantic leakage | `split` |
| P1 | `django_apps/asteroid_lab/services/input_service.py` | persistence | `persist_decoded_snapshot(...)` implicitly mutates “latest row” | hidden write target, reduced reproducibility | `rewrite` |
| P2 | `django_apps/asteroid_lab/services/cell_snapshot_service.py` | duplication | `_overlay_cell_dict(...)` duplicated across replay/snapshot layers | helper drift | `extract` |
| P2 | `django_apps/asteroid_lab/snapshots/existing_layout_inspection.py` | complexity | 394-line single file combines component index, issue detection, hint generation | increased change difficulty | `split` |
| P2 | `tests/unit/asteroid_lab/test_service_import_boundaries.py` | testing | substring scan only; no layer-direction/SCC verification | weak boundary regression detection | `test-only` |
| P2 | `django_apps/asteroid_lab/services/topology_service.py` + `models.py` | topology help | modal payload service weakly tied to web flow | shadow subsystem maintenance cost | `investigate-further` |
| P3 | `django_apps/asteroid_lab/services/project_service.py` | naming | project import and solver run creation responsibilities spread wide | long-term maintenance cost | `split` |

## Classification notes

- `P0`: must redefine “what is the canonical solver surface” in the current repo
- `P1`: structural drift, semantic drift, layer coupling
- `P2`: maintainability, helper extraction, test strengthening
- `P3`: naming / cosmetic cleanup
