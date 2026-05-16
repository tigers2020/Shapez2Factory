# Asteroid Solver Refactor Audit — Global Summary

## 감사 범위

- live code: `django_apps/asteroid_lab/`, `django_apps/web/services/asteroid_lab_page_context.py`, `django_apps/web/views/public_pages.py`, `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`, `tests/unit/asteroid_lab/`, `tests/integration/web/test_asteroid_miner_layout_solver.py`
- canonical authority: `documents/Algorithm/mining_solver_cursor_sessions/README.md`, `01_project_overview.md`, `02_pipeline_control_flow.md`, `03_data_schema_dto.md`, `13_step9_validation.md`, `14_step10_replay_ui.md`

## 최상위 결론

현재 체크아웃의 live surface는 prompt가 가정한 `django_apps/shapez_asteroid/.../asteroid_mining_layout(_v2)` 계열이 아니라 `django_apps/asteroid_lab` 기반의 decode + inspection + replay lab shell이다. canonical 문서가 정의한 Pass1/Pass2/STEP4 routing/Pass3/recovery/final validation/protected corridor solver는 live tree에 구현되어 있지 않거나, 일부 개념만 이름으로 선반영되어 있다.

즉, 이번 감사의 핵심 위험은 "나쁜 구현"보다 먼저 "잘못된 대상에 대한 리팩터링"이다. canonical 문서는 full solver를 전제로 하지만, live code는 inspection replay generator와 UI shell이 중심이다.

## Drift Severity

- 전체 drift severity: `심각`
- canonical 대비 상태: `부분 구현 + 명명 선점 + 출력 계층 과결합`
- 안정화 난이도: `높음`

## 주요 corruption vector

| 벡터 | live evidence | canonical conflict | severity |
|---|---|---|---|
| canonical/live namespace 불일치 | live tree는 `django_apps/asteroid_lab/`; prompt 기대 경로 부재 | `README.md`, `01_project_overview.md`, `02_pipeline_control_flow.md`는 full mining solver 정본 | `P0` |
| replay 계층이 reconstruction 실행을 소유 | `django_apps/asteroid_lab/replay/snapshot_map_replay.py` | `14_step10_replay_ui.md` §16, `13_step9_validation.md`는 replay를 output-only로 둠 | `P1` |
| orchestration 과결합 | `django_apps/asteroid_lab/services/replay_pipeline_service.py` | `02_pipeline_control_flow.md`의 단계 분리와 불일치 | `P1` |
| solver semantic 명명 드리프트 | `SolverRun`, `CandidateBundle`, `RoutingProbe`, `SolverMetricSnapshot`가 있으나 실제 파이프라인은 inspection-only | `01_project_overview.md`, `03_data_schema_dto.md`의 solver 단계 계약과 불일치 | `P1` |
| validation/recovery/protected corridor 부재 | `asteroid_lab` 내부에 대응 모듈 없음 | `11_step8_recovery.md`, `12_protected_corridor.md`, `13_step9_validation.md` | `P1` |
| UI contract가 canonical trace가 아니라 ad hoc replay JSON에 종속 | `django_apps/web/services/asteroid_lab_page_context.py`, `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | `14_step10_replay_ui.md`의 `trace_event`, cycle streaming 정본과 불일치 | `P1` |

## 추천 리팩터 순서

1. canonical/live mapping을 먼저 고정한다.
2. replay/output 계층에서 reconstruction 계산을 분리한다.
3. `build_initial_replay_for_map_input(...)`를 단계별 orchestration service로 분해한다.
4. live tree에서 실제 미구현인 solver 명명 모델을 freeze 또는 deprecate 한다.
5. DTO를 replay/decode/inspection/topology로 분리한다.
6. validation/recovery/protected corridor를 "부재"로 명확히 선언하고 후속 migration plan으로 이동한다.
7. web replay contract를 canonical trace schema로 재정렬한다.
8. import-boundary/SCC/canonical-alignment 테스트를 보강한다.

## Recommended Freeze Zones

초기 단계에서 손대지 말아야 할 구간:

- `django_apps/asteroid_lab/reconstruction/pipeline.py`
- `django_apps/asteroid_lab/reconstruction/fill.py`
- `django_apps/asteroid_lab/snapshots/transport_components.py`
- `django_apps/asteroid_lab/snapshots/server_coords.py`
- `django_apps/asteroid_lab/adapters/decode_adapter.py`

이 구간들은 현재 live tree에서 비교적 순수 함수 성격이 강하고, 가장 큰 드리프트 원인인 orchestration/replay 결합을 풀기 전에는 수정 효율이 낮다.

## Dangerous Central Orchestrators

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/web/views/public_pages.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/web/services/asteroid_lab_page_context.py`

## Immutable DTO Layer 후보

- 현재 후보: `django_apps/asteroid_lab/services/dto.py`
- 목표 상태: 아래처럼 분리
  - `dto/replay.py`
  - `dto/decode.py`
  - `dto/existing_layout.py`
  - `dto/topology.py`
  - `dto/orchestration.py`

## 구조 검증 요약

- internal SCC scan: `django_apps/asteroid_lab` 내부 다중 파일 SCC 없음
- targeted structural pytest: `147 passed`
- existing import guard: `tests/unit/asteroid_lab/test_service_import_boundaries.py`

## Stabilization Difficulty

- phase 1: `중간` — 문서/경계 재정렬
- phase 2: `높음` — replay/runtime 분리
- phase 3: `높음` — semantic model cleanup와 canonical solver migration
