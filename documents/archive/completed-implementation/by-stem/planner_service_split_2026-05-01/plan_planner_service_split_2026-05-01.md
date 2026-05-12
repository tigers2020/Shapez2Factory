# Plan: planner_service split (2026-05-01)

관련 리서치: [documents/research_planner_service_split_2026-05-01.md](./research_planner_service_split_2026-05-01.md)

원본 요청 요약: [django_apps/shapez_solver/services/planner_service.py](../../../../../django_apps/shapez_solver/services/planner_service.py) 의 내부 책임을 분리하되, 공개 타입과 import 경로는 유지한다.

## 구현 접근

1. 공통 operation recipe 조립과 shape helper 를 `planner_support.py` 로 추출한다.
2. source / rotation / stack / paint / half assembly / quadrant assembly / cut 탐색 규칙을 `planner_rules.py` 로 추출한다.
3. [planner_service.py](../../../../../django_apps/shapez_solver/services/planner_service.py) 는 에러/DTO, `PlannerService.plan()`, `PlannerService.solve_shape()` orchestration 만 남긴다.
4. planner 전용 단위 테스트를 추가해 graph builder 깨짐과 분리된 검증 경로를 확보한다.

## 호환성 기준

- `from django_apps.shapez_solver.services.planner_service import PlannerService, PlannerRequest, PlannerResult, UnsupportedTargetError` 는 그대로 동작해야 한다.
- solver 규칙 우선순위와 비용 비교(`cost.as_sort_key()`)는 유지한다.
- unsupported material, cycle detection, memoization, source/paint/stack/rotation/cut 규칙의 동작은 바꾸지 않는다.

## 검증

- planner 전용 테스트 파일을 추가하고 실행한다.
- 가능하면 기존 planner 관련 테스트도 함께 확인한다.
- 전체 웹 스모크 실패는 현재 `graph_builder` import 문제와 분리해서 보고한다.
