# Plan: solver graph right-aligned layout (2026-05-02)

관련 리서치: [documents/research_solver_graph_right_aligned_layout_2026-05-02.md](./research_solver_graph_right_aligned_layout_2026-05-02.md)

원본 요청 요약: solver graph 는 base/source 가 왼쪽, target/output 이 오른쪽에 있어야 한다. `right-to-left` 라는 표현 대신, 좌→우 흐름은 유지하고 그래프 가로 배치만 오른쪽 정렬 기준으로 바꾼다.

## 목표

- API 의 `graph.layout.direction` 은 계속 `left-to-right` 를 유지한다.
- 그래프 카드/엣지 의미는 그대로 두고, 노드 가로 배치만 successor 기준 right-aligned baseline 으로 바꾼다.
- stable preview 동작과 payload 는 유지한다.
- solver 페이지 문구와 테스트를 새 의미에 맞게 정리한다.

## 구현 접근

1. `solver_graph_layout.js` 의 horizontal placement 를 depth 역순 계산으로 바꾼다.
2. sink depth 는 오른쪽 앵커에서 시작하고, 같은 depth 의 나머지 노드는 왼쪽으로 채운다.
3. predecessor/successor 간 `COLUMN_GAP` 제약은 유지해서 모든 edge 는 계속 좌→우로 흐르게 한다.
4. 최종 레이아웃 조립 시 `x` 와 `y` 를 모두 padding 기준으로 정규화한다.
5. solver 페이지 설명 문구를 "stable previews + base left / target right + right-aligned layout style" 로 교체한다.
6. unit / integration test 를 새 기준으로 갱신한다.

## 변경 대상

- `django_apps/web/static/web/js/solver_graph_layout.js`
- `django_apps/web/templates/web/solver.html`
- `tests/unit/web/test_solver_graph_layout.py`
- `tests/integration/web/test_web_smoke.py`

## 테스트

- unit:
  - deterministic layout 유지
  - 모든 edge 좌→우 유지
  - late merge branch 가 여전히 depth 내부에서 서로 다른 `x` 를 가질 수 있음
  - deepest terminal node 들이 right-aligned baseline 으로 한 칸 간격 정렬됨
- integration:
  - solver page 문구 변경 반영
  - API `graph.layout.direction == "left-to-right"` 유지
- harness:
  - `pytest`
  - `ruff check .`
  - `mypy .`
  - `black .`

## 메모

- backend DTO / serializer 계약은 이번 범위에서 변경하지 않는다.
- preview renderer 와 cache key 는 이번 작업과 무관하므로 손대지 않는다.
