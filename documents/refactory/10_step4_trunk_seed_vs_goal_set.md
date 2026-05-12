# 목표: `trunk_seed_candidates`와 route goal set 혼동 방지

## 배경

- 정본: `08_step4_routing.md` §9.2 — trunk seed는 merge 힌트·중립 연결점, goal set은 “도달하면 성공인 셀 집합”. 역할이 다르다.

## 현재 상태

- `step4_goal_trunk_seed.py`에서 `build_trunk_seed_candidates_by_kind` / `build_step4_goal_set`로 분리되어 있으나, 신규 기능이 한 집합만 확장하는 실수 가능.

## 목표 상태

- 타입·이름·주석으로 **두 집합의 의미**를 고정한다(예: `TrunkSeedByKind` vs `RouteGoalSet` 별칭, 또는 전용 small dataclass).
- 문서 §9.2의 “첫 route 후 existing trunk 승격” 규칙과 `committed_trunk_by_kind` 갱신 지점을 코드 주석 한 줄로 교차 참조.

## 작업 항목

1. STEP4 merge 라우팅에서 goal set을 만드는 모든 분기 목록화.
2. `cheap_escape`·output stub 좌표가 goal에 섞이지 않는지 정적 체크(선택: assert 개발 전용).
3. replay `solver_summary`에 두 집합을 **동시에** 노출할 때 키 이름 고정.

## 검증

- 단위: 빈 trunk / 비빈 trunk 각각 goal set 동등성.

## 참고 코드

- `step4/step4_goal_trunk_seed.py`, `step4/step4_merge_routing.py`
