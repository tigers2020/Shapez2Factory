# solver_graph_layout.js 리서치

날짜: 2026-05-02

## 대상

- `django_apps/web/static/web/js/solver_graph_layout.js`
- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- `tests/integration/web/test_web_smoke.py`

## 현재 관찰

- `solver_graph_layout.js`는 그래프 런타임 레이아웃 핵심이지만, 한 파일 안에 알고리즘 단계가 길게 이어진다.
- 특히 `computeGroupedGraphLayout()`가 아래 단계를 직접 모두 조립한다.
  - depth 계산
  - column grouping
  - barycenter ordering
  - adjacency 준비
  - top position 반복 보정
  - horizontal position 계산
  - 최종 x/y position 생성
  - bounds 계산
- 외부에서 실질적으로 기대하는 공개 계약은 `computeGraphLayout()`과 상수 export들이다.

## 리팩토링 포인트

- empty graph layout, ordered column preparation, vertical pass iteration, final position/bounds 계산을 helper로 나누면 메인 함수가 훨씬 짧아진다.
- adjacency와 sorted depths는 반복 계산 전에 한 번 묶어두는 편이 읽기 좋다.
- vertical placement는 forward/backward sweep이 한 쌍이므로, helper 두 개 또는 pass runner 하나로 추출하기 좋다.

## 주의점

- smoke 테스트는 직접 layout 수치를 검사하진 않지만, 그래프 렌더 출력이 깨지면 페이지 렌더 간접 회귀가 생긴다.
- `transform-origin: 0 0;`, viewport 크기 스타일, `./solver_graph_layout.js` marker는 유지되어야 한다.
- 알고리즘 의미 변경보다 구조 분리가 목적이다.
