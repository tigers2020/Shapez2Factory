# planner_rules.py 리팩토링 플랜

날짜: 2026-05-02

## 목표

- `planner_rules.py`에서 반복되는 operation solution 조립 코드를 helper로 정리한다.
- 규칙 함수들이 “무슨 규칙인지”만 드러나도록 본문을 얇게 만든다.

## 변경 범위

- `django_apps/shapez_solver/services/planner_rules.py`
- 필요 시 planner 관련 테스트

## 접근

1. operation catalog 기본값을 읽는 내부 helper를 만든다.
2. 단일 입력/이항 입력 operation solution helper를 만든다.
3. 회전 파생과 cutter 파생도 같은 helper를 사용하도록 정리한다.
4. cut-from-source의 파생 후보 수집을 helper로 분리한다.
5. planner 관련 단위 테스트와 타입/린트를 확인한다.

## 기대 효과

- 규칙 함수가 더 짧아지고 의도가 선명해진다.
- operation recipe 생성 로직 수정 시 한 곳만 손보면 된다.
- 이후 규칙 파일을 rule object 형태로 더 분리하기 쉬워진다.
