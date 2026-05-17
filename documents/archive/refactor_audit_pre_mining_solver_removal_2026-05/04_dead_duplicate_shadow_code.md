# Dead / Duplicate / Shadow Code

## 기준

- live evidence only
- canonical refs: `03_data_schema_dto.md`, `14_step10_replay_ui.md`

## 1. Dead / shadow persistence models

| File | Shadow code | Evidence | Severity | Confidence | Action |
|---|---|---|---|---|---|
| `django_apps/asteroid_lab/models.py` | `CandidateBundle` | admin/tests 외 live usage 없음 | `P1` | High | `deprecate` |
| `django_apps/asteroid_lab/models.py` | `RoutingProbe` | admin/tests 외 live usage 없음 | `P1` | High | `deprecate` |
| `django_apps/asteroid_lab/models.py` | `SolverMetricSnapshot` | admin/tests 외 live usage 없음 | `P1` | High | `deprecate` |
| `django_apps/asteroid_lab/models.py` | `PatternTemplate` / `PatternVariant` | live lab page, replay pipeline, topology modal 어디에도 미연결 | `P2` | Medium | `investigate-further` |
| `django_apps/asteroid_lab/services/topology_service.py` | topology modal subsystem | service/tests는 존재하지만 web flow 연결이 약함 | `P2` | Medium | `investigate-further` |

## 2. Duplicate helpers

| Files | Duplicate logic | Root cause | Severity | Confidence | Action |
|---|---|---|---|---|---|
| `django_apps/asteroid_lab/services/cell_snapshot_service.py` + `django_apps/asteroid_lab/replay/snapshot_map_replay.py` + `django_apps/asteroid_lab/snapshots/existing_layout_inspection.py` | cell → row dict serializer | 계층별 로컬 helper 남발 | `P2` | High | `extract` |
| `django_apps/asteroid_lab/services/input_service.py` (`persist_decoded_snapshot_for_map_input`, `persist_decoded_snapshot`) | decoded snapshot persistence | id-target vs newest-target 정책 공존 | `P2` | High | `rewrite` |
| `django_apps/asteroid_lab/services/cell_snapshot_service.py` + `django_apps/asteroid_lab/services/existing_layout_service.py` | snapshot persist + replay frame record 패턴 | phase-specific service split이 아니라 copy/paste 확장 | `P2` | High | `extract` |

## 3. Hidden alternate implementation risk

| File | Hidden shadow logic | Risk | Severity | Confidence | Action |
|---|---|---|---|---|---|
| `django_apps/web/services/asteroid_lab_page_context.py` | serializer fallback이 `frame_payload.full_map` 부재를 UI에서 보정 | backend contract가 깨져도 UI가 묵살 가능 | `P1` | High | `freeze` |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | replay render path가 full_map / overlay / diff를 모두 자체 해석 | backend canonical schema 없이 프론트가 shadow schema를 만듦 | `P1` | High | `split` |

## 삭제 우선순위

1. `CandidateBundle`, `RoutingProbe`, `SolverMetricSnapshot`는 live solver migration 전까지 `deprecate` 대상으로 표시
2. duplicate serializer helper는 `extract`
3. serializer fallback은 early phase에서 제거하지 말고 먼저 backend canonical payload를 고정한 뒤 정리
