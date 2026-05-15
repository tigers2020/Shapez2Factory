# Refactor Execution Order

## 원칙

- 구현 전면 교체가 아니라 **권한 경계 정리 -> 중복 제거 -> skeleton 치환** 순서로 간다.
- early phase에서는 semantic vocabulary와 read-only decode contract를 건드리지 않는다.

## Phase 0 — Freeze / 기준선 확보

- freeze:
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py`
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py`
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/placement_fsm.py`
  - `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/existing_layout_analysis.py`
- 이유:
  - semantic drift보다 구조 drift가 현재 더 크다.

## Phase 1 — DTO / Runtime / Placement cycle 절단

- 대상:
  - `domain/__init__.py`
  - `domain/dto.py`
  - `runtime/__init__.py`
  - `runtime/trace_events.py`
  - `domain/corridor.py`
- 목표:
  - `domain` public surface에서 placement/runtime 재export 제거
  - `TraceEvent`를 DTO alias에서 분리
  - SCC 해소

## Phase 2 — Routing authority 수복

- 대상:
  - `routing/corridor_probe.py`
  - `routing/step4_corridor_recovery.py`
  - `placement/corridor_opening.py`
  - `placement/pass2_route_probe.py`
- 목표:
  - STEP 4 / recovery helper ownership을 `routing/`으로 이동
  - placement helper 의존 제거
  - trunk goal / exterior predicate 공통 seam 정리

## Phase 3 — Replay / output adapter 분리

- 대상:
  - `placement/pass1_outer.py`
  - `placement/corridor_opening.py`
  - `reconstruction/diagnostics.py`
  - `runtime/`
  - `serialization/`
- 목표:
  - core algorithm에서 replay dict 생성 제거
  - trace/output emitter를 adapter layer로 이동
  - diagnostics의 preview import 제거

## Phase 4 — Duplicate stack 수렴

- 대상:
  - `services/blueprint_map_summary.py`
  - `services/asteroid_reconstruction.py`
  - `services/asteroid_patch_interior.py`
  - `v2/reconstruction/asteroid_reconstruction.py`
  - `v2/reconstruction/patch_interior.py`
  - `v2/preview_reconstruction_timeline.py`
- 목표:
  - canonical implementation 1개만 남기고 나머지는 adapter/deprecated로 전환

## Phase 5 — Skeleton 해체

- 대상:
  - `solver.py`
  - `routing/merge_aware_router.py`
  - `routing/trunk_seed.py`
  - `validation/final_validation.py`
  - `replay/snapshots.py`
- 목표:
  - canonical STEP 4 / 8 / 9 / 10 최소 구현을 넣을 자리 확보

## Phase 6 — UI contract 정렬

- 대상:
  - `django_apps/web/templates/web/asteroid_optimizer.html`
  - `django_apps/shapez_asteroid/views.py`
  - `tests/unit/web/test_asteroid_optimizer_page.py`
- 목표:
  - partial preview와 solver replay contract를 분리
  - stale `solver_timeline`/`solver_replay` 기대치 축소 또는 별도 endpoint로 격리

## Phase 7 — 테스트 보강

- 추가할 테스트 축:
  - import boundary 확장
  - trunk seed golden path
  - merge-aware routing contract
  - final validation invariant matrix
  - protected corridor lifecycle
  - replay isolation and UI/backend payload sync

## 위험도가 높은 central orchestrator

- 현재:
  - `solver.py`는 비어 있지만 앞으로 가장 위험한 중심점이 될 예정
  - `views.py`는 이미 여러 output/debug adapter를 한 경로에 모으고 있다
  - `preview_reconstruction_timeline.py`는 giant adapter로 UI coupling이 높다

## 초기에 손대지 말아야 할 영역

- `domain/enums.py`
- `domain/trace_semantics.py`
- `placement/placement_fsm.py`
- `decode/existing_layout_analysis.py`
- `routing/connectivity.py`
