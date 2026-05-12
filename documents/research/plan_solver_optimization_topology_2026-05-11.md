# 솔버 최적화(Topology·Trunk·Corridor·Recovery) 구현 플랜

**날짜**: 2026-05-11  
**상태**: 승인 후 구현 반영  
**근거 코드**: `django_apps/shapez_asteroid/services/asteroid_mining_layout/` STEP4·Pass3·P4·`recovery_orchestrator`

## 배경

- STEP4는 stub별 Dijkstra + `trunk_load.mode=accumulate_only`로 **연결성**은 확보하나, 전역 shared trunk 최적화는 제한적이다.
- Pass3는 greedy 압축 + P3E2/P3E3 guarded이며, **추가 topology refinement** 여지가 있다.
- P5 recovery는 `MAX_VALIDATION_RECOVERY_ATTEMPTS=0`일 때 단일 전진 패스로 동작한다.

## 에픽·성공 지표

| 에픽 | 목표 | 성공 지표 |
|------|------|-----------|
| E1 STEP4 | 기존 trunk 근처 job 우선 + trunk 인접 step 비용 소폭 할인 | 동일 입력에서 내부 transport·route 길이가 악화되지 않음(회귀), `trunk_load`에 `job_sort_mode` 등 진단 필드 |
| E2 Pass3 | bounded greedy 재압축 루프 | `PASS3_TOPOLOGY_REFINEMENT_MAX_ITERATIONS` 이내에서 transport 수가 단조 비증가, `validate_final_mining_layout` 통과 유지 |
| E3 P4 | corridor 소스 선택 정합 | solver 풀 키만 있고 **내용이 빈** 경우 Pass3·fallback 풀로 넘어감 |
| E4 Recovery | validation recovery 시도 허용 | `MAX_VALIDATION_RECOVERY_ATTEMPTS=1` 시 2사이클 이내 종료, 무한 루프 없음 |

## 플래그·기본값

- `STEP4_SHARED_TRUNK_JOB_SORT_ENABLED` — constants, 기본 `True` (정렬만, 결과 보수적).
- `STEP4_TRUNK_ADJACENCY_STEP_DISCOUNT` — 양수 할인(비용은 항상 양수).
- `PASS3_TOPOLOGY_REFINEMENT_MAX_ITERATIONS` — 기본 `2`.
- `MAX_VALIDATION_RECOVERY_ATTEMPTS` — 기본 `1` (총 시도 상한과 orchestrator 루프 일치).

## 테스트 범위

- `tests/unit/shapez_asteroid/test_step4_merge_routing.py` — 정렬·trunk_load 메타.
- Pass3 — topology trace 키 또는 반복 횟수 단언.
- `test_reclaim_shadow.py` 또는 corridor 전용 단위 — 빈 solver 풀 fallback.
- Recovery — `recovery_orchestrator` / `validation_recovery_allowed` 캡 동작.

## 범위 외

- Steiner tree / ILP 전역 최적화.
- 실시간 replay streaming.
