# Priority Matrix

| Priority | File | System | Issue | Risk | Recommended Action |
|---|---|---|---|---|---|
| P0 | `django_apps/asteroid_lab/` | namespace / architecture | live tree가 canonical solver 경로와 다름 | 잘못된 대상 리팩터링, 문서-구현 오판 | `freeze` |
| P1 | `django_apps/asteroid_lab/replay/snapshot_map_replay.py` | replay vs runtime | output-only 모듈이 `run_reconstruction(...)` 실행 | replay/runtime contamination, 계층 붕괴 | `split` |
| P1 | `django_apps/asteroid_lab/services/replay_pipeline_service.py` | orchestration | decode, normalize, persist, run-row, replay, snapshot 저장이 한 함수에 집중 | side effect cascade, 테스트 어려움 | `split` |
| P1 | `django_apps/asteroid_lab/services/existing_layout_service.py` | inspection / replay | inspection service가 snapshot 재로딩 + reconstruction replay 생성까지 수행 | read-only 분석 경계 약화 | `split` |
| P1 | `django_apps/web/views/public_pages.py` | web integration | `"force=True"` 문자열로 분기 재시도 | stringly control flow, 숨은 contract | `rewrite` |
| P1 | `django_apps/asteroid_lab/models.py` | semantic model | `SolverRun`/`CandidateBundle`/`RoutingProbe`/`SolverMetricSnapshot`가 실 solver 없이 선점 | domain drift, dead schema 확산 | `deprecate` |
| P1 | `django_apps/web/services/asteroid_lab_page_context.py` | replay UI adapter | canonical trace가 아니라 ad hoc `lab_replay_frames_json` contract를 정본처럼 사용 | UI contract drift | `isolate` |
| P1 | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | replay UI | 1278-line monolith JS가 replay render, fetch, modal, frame control 모두 소유 | 변경 리스크, 회귀 범위 확대 | `split` |
| P1 | `django_apps/asteroid_lab/services/dto.py` | DTO | replay/decode/inspection/topology/orchestration DTO가 한 파일에 혼재 | semantic leakage | `split` |
| P1 | `django_apps/asteroid_lab/services/input_service.py` | persistence | `persist_decoded_snapshot(...)`가 "최신 row"를 암묵 수정 | 숨은 write target, 재현성 저하 | `rewrite` |
| P2 | `django_apps/asteroid_lab/services/cell_snapshot_service.py` | duplication | `_overlay_cell_dict(...)`가 replay/snapshot 계층과 중복 | helper drift | `extract` |
| P2 | `django_apps/asteroid_lab/snapshots/existing_layout_inspection.py` | complexity | 394-line 단일 파일에 component index, issue detection, hint generation 결합 | 변경 난이도 증가 | `split` |
| P2 | `tests/unit/asteroid_lab/test_service_import_boundaries.py` | testing | substring 스캔만 있고 layer-direction/SCC 검증 없음 | 경계 회귀 탐지 약함 | `test-only` |
| P2 | `django_apps/asteroid_lab/services/topology_service.py` + `models.py` | topology help | modal payload service가 web flow와 약하게 연결됨 | shadow subsystem 유지비 | `investigate-further` |
| P3 | `django_apps/asteroid_lab/services/project_service.py` | naming | project import와 solver run 생성 책임이 넓게 퍼짐 | 장기 유지보수 비용 | `split` |

## 분류 메모

- `P0`: 현재 레포에서 "무엇이 canonical solver surface인가"부터 다시 정해야 하는 문제
- `P1`: 구조 drift, semantic drift, 계층 결합
- `P2`: 유지보수성, helper 분리, 테스트 강화
- `P3`: naming / cosmetic 정리
