# Dead / Duplicate / Shadow Code

## Criteria

- live evidence only
- canonical refs: `03_data_schema_dto.md`, `14_step10_replay_ui.md`

## 1. Dead / shadow persistence models

| File | Shadow code | Evidence | Severity | Confidence | Action |
|---|---|---|---|---|---|
| `django_apps/asteroid_lab/models.py` | `CandidateBundle` | no live usage outside admin/tests | `P1` | High | `deprecate` |
| `django_apps/asteroid_lab/models.py` | `RoutingProbe` | no live usage outside admin/tests | `P1` | High | `deprecate` |
| `django_apps/asteroid_lab/models.py` | `SolverMetricSnapshot` | no live usage outside admin/tests | `P1` | High | `deprecate` |
| `django_apps/asteroid_lab/models.py` | `PatternTemplate` / `PatternVariant` | not connected to live lab page, replay pipeline, or topology modal | `P2` | Medium | `investigate-further` |
| `django_apps/asteroid_lab/services/topology_service.py` | topology modal subsystem | service/tests exist but web flow connection is weak | `P2` | Medium | `investigate-further` |

## 2. Duplicate helpers

| Files | Duplicate logic | Root cause | Severity | Confidence | Action |
|---|---|---|---|---|---|
| `django_apps/asteroid_lab/services/cell_snapshot_service.py` + `django_apps/asteroid_lab/replay/snapshot_map_replay.py` + `django_apps/asteroid_lab/snapshots/existing_layout_inspection.py` | cell → row dict serializer | per-layer local helpers proliferated | `P2` | High | `extract` |
| `django_apps/asteroid_lab/services/input_service.py` (`persist_decoded_snapshot_for_map_input`, `persist_decoded_snapshot`) | decoded snapshot persistence | id-target vs newest-target policies coexist | `P2` | High | `rewrite` |
| `django_apps/asteroid_lab/services/cell_snapshot_service.py` + `django_apps/asteroid_lab/services/existing_layout_service.py` | snapshot persist + replay frame record pattern | copy/paste expansion rather than phase-specific service split | `P2` | High | `extract` |

## 3. Hidden alternate implementation risk

| File | Hidden shadow logic | Risk | Severity | Confidence | Action |
|---|---|---|---|---|---|
| `django_apps/web/services/asteroid_lab_page_context.py` | serializer fallback compensates for missing `frame_payload.full_map` in UI | backend contract can break while UI hides it | `P1` | High | `freeze` |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | replay render path interprets full_map / overlay / diff itself | frontend builds shadow schema without backend canonical schema | `P1` | High | `split` |

## Deletion priority

1. Mark `CandidateBundle`, `RoutingProbe`, `SolverMetricSnapshot` as `deprecate` targets until live solver migration
2. `extract` duplicate serializer helpers
3. Do not remove serializer fallback in early phase; fix backend canonical payload first, then clean up
