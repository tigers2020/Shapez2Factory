# planner_rules.py 리서치

날짜: 2026-05-02

## 대상

- `django_apps/shapez_solver/services/planner_rules.py`
- `django_apps/shapez_solver/services/planner_service.py`
- `tests/unit/shapez_solver/test_planner_service_refactor.py`

## 현재 관찰

- `planner_rules.py`는 규칙 함수 모음 역할을 잘 하고 있지만, operation recipe 조립 코드가 여러 규칙에 반복된다.
- 반복 패턴은 대체로 아래 둘이다.
  - 단일 입력 operation recipe 생성
  - 이항 입력 operation recipe 생성
- `try_rotation()`과 `try_cut_from_source()`는 파생 candidate를 순회하는 구조가 있고, 여기서도 operation 조립이 중복된다.
- `planner_service.py`는 이미 orchestration 중심이므로, 다음 유지보수 비용은 `planner_rules.py` 쪽이 더 크다.

## 유지해야 할 계약

- 외부 공개 함수 이름은 그대로 유지한다.
- `planner_service.py`의 import 경로를 깨지 않는다.
- 규칙별 결과 shape, cost 비교 방식, `UnsupportedTargetError` 흐름은 그대로 유지한다.

## 리팩토링 포인트

- catalog 기본 label/description을 주입하는 내부 helper를 만들면 중복을 크게 줄일 수 있다.
- 단일 입력/이항 입력 operation 조립 helper를 나누면 각 규칙이 의도를 더 직접적으로 드러낼 수 있다.
- cut-from-source BFS는 “다음 파생 후보 만들기” helper로 묶으면 본문이 짧아진다.

## 주의점

- 성능보다 가독성 개선이 목적이므로, 규칙 순서나 선택 기준은 바꾸지 않는다.
- 이미 통과 중인 planner 테스트를 깨지 않도록 operation type, selected output index, description override는 보존해야 한다.
