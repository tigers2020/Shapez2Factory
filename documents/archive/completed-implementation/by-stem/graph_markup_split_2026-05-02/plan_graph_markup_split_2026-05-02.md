# graph_markup.js 리팩토링 플랜

날짜: 2026-05-02

## 목표

- `graph_markup.js`의 마크업 조립 책임을 helper로 나눠서 읽기 흐름을 단순화한다.
- 그래프 렌더 출력 계약과 smoke marker는 유지한다.

## 변경 범위

- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- 필요 시 `django_apps/web/static/web/js/solver_timeline.js`

## 접근

1. preview markup helper와 shape meta badge helper를 분리한다.
2. edge path/label helper를 분리한다.
3. viewport controls, hint, stage markup helper를 분리한다.
4. 깨진 안내 문구는 ASCII 기반 정상 문자열로 교체한다.
5. smoke 테스트 범위를 다시 실행해 회귀를 확인한다.

## 기대 효과

- 그래프 카드와 viewport 레이아웃을 별개로 읽을 수 있다.
- preview fallback이나 edge 스타일 변경 시 수정 범위가 더 작아진다.
- 프런트 다음 분리 대상인 `solver_graph_layout.js`와 경계가 더 선명해진다.
