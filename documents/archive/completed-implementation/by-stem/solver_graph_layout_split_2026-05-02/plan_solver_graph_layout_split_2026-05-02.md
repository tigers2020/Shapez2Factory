# solver_graph_layout.js 리팩토링 플랜

날짜: 2026-05-02

## 목표

- `solver_graph_layout.js`의 레이아웃 계산 단계를 helper로 분리해 메인 흐름을 단순화한다.
- 출력 좌표와 bounds 계약은 유지한다.

## 변경 범위

- `django_apps/web/static/web/js/solver_graph_layout.js`

## 접근

1. empty graph fallback을 helper로 뺀다.
2. ordered column, adjacency, sorted depth를 묶는 layout state helper를 만든다.
3. vertical top position sweep를 별도 helper로 분리한다.
4. final positions와 bounds 계산을 helper로 분리한다.
5. smoke 테스트로 그래프 페이지 회귀를 확인한다.

## 기대 효과

- 메인 layout 함수가 “준비 → 세로 배치 → 가로 배치 → bounds 산출” 순서로 읽힌다.
- 추후 레이아웃 알고리즘 조정 시 수정 지점이 더 작아진다.
