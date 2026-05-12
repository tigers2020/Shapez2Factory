# 목표: Protected corridor 생명주기(§14)와 요약 DTO 정렬

## 배경

- 정본: `12_protected_corridor.md` §14.2–§14.2.1 — `candidate_corridor` 생성·`soft_protected` 승격·폐기.
- STEP4 직후 라우팅 상태 요약: `step4_routing_state.py`.

## 현재 상태

- `soft_protected_candidate_corridors`와 `soft_protected_confirmed_corridors`에 **동일 집합**이 들어가, probe 단계와 commit 후 단계의 구분이 요약 블록에서 사라진다.
- **(2026-05-12, PR4-A 1차)** `step4_routing_state._routing_state_from_committed_routes` 한정: commit 스냅샷에서는 후보 풀이 없으므로 **candidate는 `[]`**, confirmed·`soft_protected_corridors`는 동일 soft 풀. 상세·PR4-B 가드 맵: [`documents/plans/active_pr4_protected_corridor_lifecycle.md`](../plans/active_pr4_protected_corridor_lifecycle.md).

## 목표 상태

- 다음 중 하나.
  - **A)** 정본대로 후보/확정을 분리해 채운다(STEP4 commit 시점에는 confirmed만, probe는 별도 trace).
  - **B)** MVP에서는 동치임을 **정본 또는 코드 주석·계약 버전**에 명시하고, 필드 중 하나를 deprecate하여 혼동을 줄인다.

## 작업 항목

1. Pass3·P4·reclaim이 소비하는 키(`hard_protected_corridors`, `soft_protected_corridors`, …)를 표로 정리한다.
2. `reclaim_corridors` / `route_adapter` 등과 **의미 중복**이 없는지 점검한다.
3. replay overlay가 candidate를 그릴 필요가 있는지 UI와 합의한다.

## 검증

- 회귀: 보호 코어 변경 후 Pass3 atomic / P4 soft replace 테스트가 통과하는지.

## 위험

- 집합 분리 시 빈 candidate가 소비자 코드에서 KeyError/빈 리스트 가정을 깨뜨릴 수 있음.

## 참고 코드

- `step4/step4_routing_state.py`
- `reclaim/reclaim_corridors.py`, `routing/route_adapter.py`
