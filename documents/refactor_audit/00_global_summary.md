# Asteroid Mining Solver 리팩터링 감사 요약

## 범위

- 대상: `django_apps/shapez_asteroid/`, `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/`, `django_apps/web/templates/web/asteroid_optimizer.html`, `tests/unit/shapez_asteroid_v2/`, `tests/unit/web/`
- 정본: `documents/Algorithm/mining_solver_cursor_sessions/README.md` 및 `01`~`14`
- 감사 방식: 정본 대조, 정적 import 탐색, 순환 의존 분석, 구조 테스트 실행, UI/adapter 경로 점검

## 최상위 위험

1. `v2` 파이프라인의 핵심 단계가 아직 skeleton 상태다.
   - `routing/merge_aware_router.py`
   - `routing/trunk_seed.py`
   - `solver.py`
   - `replay/snapshots.py`
   - 정본 기준: `08_step4_routing.md`, `13_step9_validation.md`, `14_step10_replay_ui.md`
   - 분류: `P0`, `rewrite`, `freeze`

2. 도메인 DTO 계층이 runtime/placement와 실제 순환 의존을 형성한다.
   - 정적 SCC: `domain` ↔ `domain.dto` ↔ `placement.placement_fsm` ↔ `runtime` ↔ `runtime.trace_events`
   - 핵심 증거:
     - `domain/__init__.py`
     - `domain/dto.py`
     - `placement/placement_fsm.py`
     - `runtime/__init__.py`
     - `runtime/trace_events.py`
   - 정본 기준: `03_data_schema_dto.md`
   - 분류: `P1`, `split`, `isolate`

3. replay/output concern이 알고리즘 내부에 직접 섞여 있다.
   - `placement/pass1_outer.py`가 `replay_events` dict를 직접 적재
   - `placement/corridor_opening.py`가 recovery 중 `TraceEvent`를 직접 생성
   - `reconstruction/diagnostics.py`가 preview builder를 호출
   - 정본 기준: `14_step10_replay_ui.md`, `02_pipeline_control_flow.md`
   - 분류: `P1`, `split`, `isolate`

4. STEP 4/Recovery 책임 경계가 placement 패키지로 새어 있다.
   - `routing/step4_corridor_recovery.py`가 사실상 `placement/corridor_opening.py` 래퍼
   - `routing/corridor_probe.py`가 placement 내부 helper에 의존
   - 정본 기준: `08_step4_routing.md`, `11_step8_recovery.md`, `12_protected_corridor.md`
   - 분류: `P1`, `split`, `migrate`

5. UI는 여전히 legacy replay/timeline 계약을 크게 전제하지만, 백엔드는 copy-preview partial pipeline만 제공한다.
   - 프론트: `django_apps/web/templates/web/asteroid_optimizer.html`
   - 백엔드: `django_apps/shapez_asteroid/views.py`, `solver.py`
   - 정본 기준: `14_step10_replay_ui.md`
   - 분류: `P1`, `isolate`, `deprecate`, `investigate-further`

6. non-v2 support service와 v2 구현이 STEP 1 / preview 역할을 이중으로 가진다.
   - `services/asteroid_reconstruction.py` vs `services/asteroid_mining_layout_v2/reconstruction/asteroid_reconstruction.py`
   - `services/asteroid_patch_interior.py` vs `services/asteroid_mining_layout_v2/reconstruction/patch_interior.py`
   - `services/blueprint_map_summary.py` vs `services/asteroid_mining_layout_v2/preview_reconstruction_timeline.py`
   - 분류: `P1`, `migrate`, `deprecate`, `delete`

## Drift 심각도

- 전체 심각도: `높음`
- 이유:
  - 정본 문서는 STEP 4/8/9/10의 책임이 명확하지만, 현 코드는 아직 partial preview 중심으로 묶여 있다.
  - semantic namespace 자체는 `domain/enums.py`, `domain/trace_semantics.py`, `placement/placement_fsm.py`에서 비교적 잘 분리됐지만, 실제 end-to-end 실행 계층이 비어 있다.
  - “테스트가 green”인 영역 상당수가 “미구현 skeleton의 경계”를 확인하는 수준이라 canonical behavior 안정성과는 다르다.

## 주요 corruption vector

- DTO/Runtime 순환 의존이 커지면 trace schema 변경이 domain import graph 전체를 흔든다.
- STEP 4 routing/recovery를 placement helper에 얹은 현재 구조가 유지되면 pass 경계가 흐려진다.
- validation stub의 관대함이 장기화되면 `assertion-only gate` 대신 “부분 생략 허용” 단계로 굳어진다.
- UI가 `solver_replay`, `solver_timeline`, `ui_frames`, `protected_corridors`를 계속 요구하면, partial preview 백엔드와의 계약 drift가 누적된다.
- old support service를 남긴 채 v2를 확장하면 shadow logic와 의미 중복이 계속 늘어난다.

## 권장 리팩터 순서

1. DTO/domain/runtime 순환 의존 해소
2. STEP 4 boundary 재정의: routing/recovery를 placement에서 분리
3. replay/output emission adapter 분리
4. duplicate reconstruction/preview stack 정리
5. skeleton STEP 4 / trunk seed / replay adapter / final validation의 구현 슬롯 확정
6. UI replay 계약과 backend partial pipeline 정렬
7. semantic/FSM/import boundary 회귀 테스트 확장

## 안정화 난이도

- 예상 난이도: `높음`
- 이유:
  - 현재 코드는 “의미 계약을 잘 정의한 enum/test 층”과 “미완성 orchestration 층”이 강하게 엇갈린다.
  - import graph, UI contract, duplicate helper 정리를 동시에 건드리면 넓은 영향 범위가 생긴다.

## 초기 freeze zone

- 초기 단계에서 수정 최소화 권장:
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py`
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py`
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/placement_fsm.py`
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/existing_layout_analysis.py`
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/connectivity.py`

## 실행한 구조 검증

- `python -m pytest tests/unit/shapez_asteroid_v2/test_import_boundaries.py tests/unit/shapez_asteroid_v2/test_domain_import_boundaries.py tests/unit/shapez_asteroid_v2/test_runtime_trace_import_boundaries.py tests/unit/shapez_asteroid_v2/test_step4_routing_contract.py tests/unit/shapez_asteroid_v2/test_final_validation_contract.py tests/unit/shapez_asteroid_v2/test_replay_trace_is_output_only.py -q`
- 결과: `29 passed`
- 해석: 경계 테스트는 통과하지만, 여러 테스트가 skeleton/미구현 상태를 계약으로 고정하고 있어 구조 완성도를 증명하지는 않는다.
