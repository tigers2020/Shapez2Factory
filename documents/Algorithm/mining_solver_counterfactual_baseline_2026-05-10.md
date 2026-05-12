# 채굴 솔버 counterfactual routing baseline (2026-05-10)

## 목적

`optimization_baseline_internal_transport`(Pass1·Pass2 직후 **실제 배치된** 내부 belt/pipe 타일 수)와 별도로, **운송을 제거한 가상 맵**에서 STEP4와 동일한 Dijkstra(가중 비용)·목표 판정으로 job별 최단 경로를 그린 뒤, 최종 합집합에 대한 내부 transport 타일 수를 산출한다. Pass3/실험의 **품질 비교·reclaim 정량화**를 위한 보조 기준선이다.

## 정의 두 가지 (문서상 모두 유효, 구현 v1은 하나만)

| 이름 | 요약 | 해석 |
|------|------|------|
| **독립 합산(independent)** | 각 routing job을 **빈 trunk·다른 job 경로 무시**로 단독 Dijkstra. 내부 타일 수를 job마다 세어 합산(겹침이 있으면 합이 실제 배치 가능량을 **과소** 반영할 수 있음). | 낙관적 하한에 가깝다. |
| **순차 trunk 누적(sequential trunk v1)** | job을 **고정 순서**로 처리. 각 단계에서 현재 맵으로 trunk를 재계산한 뒤 Dijkstra → 경로를 paint. 이후 job은 앞선 경로를 trunk로 활용할 수 있다. | STEP4 루프와 동형에 가깝다. **job 순서 의존**이 있다. |

**코드 v1**: `sequential_trunk_v1`만 구현한다. (`django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/baseline_routing.py`)

## 한계(보고용 메트릭)

- **“하한” 보장은 없다.** 순차 처리·가중 Dijkstra(내부 타일 수와 비선형)·지역 최적 등으로, 값은 “동일 규칙 아래의 counterfactual 참고치”로만 쓴다.
- 경로 선택은 `step4_step_cost`의 **가중 최단**이다. `quality_ratio` 등은 **타일 수 ÷ 타일 수**로만 두고, 가중 거리와 혼합하지 않는다(후속 단계 계약).

## 계약 요약

- 입력 `mining_map`: Pass1·Pass2 직후 등 **관측 레이아웃**(belt/pipe는 strip 후 재배치).
- `final_mining_map`: 내부 transport 정의(asteroid ∩ mineable)에 사용. 기존 Pass3 baseline과 동일.
- `is_external`: STEP4와 동일한 외부 판정.
- job 목록: 호출자가 넘기지 않으면 `collect_routing_jobs`로 **strip 이전** 원본 맵에서 수집한 뒤, `(stub, extractor, placement_id)` 기준 **안정 정렬**.
- **한 job이라도 경로 실패**하면 전체 `internal_transport_count`는 `None`, `failure_reason` 및 per-job trace에 사유를 남긴다.

## 파이프라인·replay 필드(요약)

- `solver_summary` / `solver_replay.optimization_metrics` / `final_validation`에 **additive** 키로 노출: 순차 counterfactual 내부 transport, aggregation 라벨, (가능 시) `optimization_internal_transport_quality_ratio` = `after_internal_transport_count / counterfactual` (`counterfactual`이 양의 정수일 때만).

## 관련 코드

- STEP4 탐색: `step4_dijkstra.dijkstra_route_step4`, `step4_routing_permission`.
- trunk: `validation.final_validation.transport_cells_reaching_external`.
- 내부 타일 수(최종 paint 기준): `solver_timeline.count_internal_transport_tiles_for_kind`.

## 참고

- 상위 로드맵: `documents/Algorithm/mining_solver_recovery_roadmap_2026-05-10.md` (P3 optimization baseline 항목).
