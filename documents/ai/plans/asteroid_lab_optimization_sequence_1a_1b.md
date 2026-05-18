# Asteroid Lab — Optimization Sequence 1A·1B 스코프

**상태:** `ACTIVE` (구현 범위 고정용)  
**기준 문서:** [`documents/Algorithm/asteroid_lab_10_development_sequence.md`](../../Algorithm/asteroid_lab_10_development_sequence.md) Sequence 1A·1B, [`asteroid_lab_01_optimization_input.md`](../../Algorithm/asteroid_lab_01_optimization_input.md)

## 승인된 범위

1. **Sequence 1A — Domain DTO contracts**  
   - `Coord` = Server X/Y, `neighbors4_server`, `cardinal_unit_toward`  
   - `OptimizationInput` 및 Phase 1·4·6·7·8·9 문서에 나열된 enum·보조 DTO(진화·리커버리·검증·리플레이 타입 자리)  
   - `TopologyGraph` 무방향 계약(저장: 양방향 엣지)  
   - `RouteDomainSnapshotBuilder.build_snapshot` / `build_seed_snapshot` 시그니처(Phase 7·1과 동기)

2. **Sequence 1B — Reconstruction → OptimizationInput + 시드 route_domain**  
   - `ReconstructionResult` + `DecodedCellDTO.server_x`/`server_y` 필수  
   - rim·interior·mineable·blocked·transport·빈 trunk/greenfield 동일 경로  
   - 시드 스냅샷에서 `hard_blocked`·`transport_mask`·`RouteClass`가 `blocked_cells`와 모순 없게 구성

## 패키지 경로 (고정)

- **코드:** `django_apps/asteroid_lab/optimization/` (Django ORM 미사용, `DecodedCellDTO` 등 기존 DTO만 참조)  
- **좌표:** `ReconstructionResult.server_xy_params`가 있으면 `DecodedCellDTO`에 `server_x`/`server_y`가 없어도 `server_xy_for_raw_xy`로 Server 좌표를 복원한다.  
- **테스트:** `tests/unit/asteroid_lab/test_optimization_input.py`

과거 문서의 `django_apps.shapez_asteroid`·`tests/unit/shapez_asteroid/` 경로는 사용하지 않는다.

## 사람 승인

본 문서에 적힌 범위·경로로 구현을 진행한다. 범위 변경 시 본 플랜을 개정한 뒤 다시 승인한다.
