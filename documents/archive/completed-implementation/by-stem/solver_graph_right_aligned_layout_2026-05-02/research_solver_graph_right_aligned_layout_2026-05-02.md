# solver graph right-aligned layout 리서치
날짜: 2026-05-02

## 요청 요약

solver graph 의 데이터 흐름은 그대로 `base/source -> target/output` 좌→우로 유지한다. 다만 가로 배치 기준은 왼쪽 기준 확장이 아니라 오른쪽 앵커 기준으로 재정렬해서, target 쪽이 더 일관된 우측 기준선을 갖도록 만든다.

## 현재 구조 요약

- 그래프 방향 메타데이터는 `django_apps/shapez_solver/dto/solver_graph.py` 의 `SolverGraph.direction` 에서 관리되며 현재 `left-to-right` 이다.
- API 직렬화는 `django_apps/shapez_solver/view_graph_serialization.py` 에서 그대로 `graph.layout.direction` 으로 내려보낸다.
- 실제 좌표 계산은 전부 프런트 `django_apps/web/static/web/js/solver_graph_layout.js` 에 있다.
- 그래프 카드와 엣지 SVG 는 `django_apps/web/static/web/js/solver_timeline/graph_markup.js` 가 소비한다.
- solver 페이지 안내 문구는 `django_apps/web/templates/web/solver.html` 에서 직접 렌더링한다.

## 현재 레이아웃 동작 관찰

`computeHorizontalPositions()` 는 depth 순서로 왼쪽에서 오른쪽으로 진행하면서:

1. predecessor 가 이미 차지한 최소 `x` 를 기준으로 다음 노드를 오른쪽으로 밀고
2. 같은 depth 의 다음 노드도 `nextRankLeft` 기준으로 더 오른쪽에 배치한다.

이 방식은 좌→우 edge 단조성은 잘 지키지만, 짧은 side branch 도 branch 길이에 따라 왼쪽에 더 일찍 멈춰서 target 쪽 우측 정렬감이 약해진다.

예시:

- 현재 sample graph 에서는 deepest target node `shape:target` 과 `shape:side-target` 이 같은 depth 임에도 `x` 차이가 한 칸이 아니라 두 칸(`540px`)까지 벌어진다.
- 즉, sink depth 의 노드가 우측 기준선에 맞춰지는 것이 아니라 upstream 에서 누적된 왼쪽 기준 배치의 영향을 계속 받는다.

## 변경 방향

- 그래프 의미와 API 방향 메타데이터는 그대로 `left-to-right` 로 둔다.
- 가로 좌표 계산만 depth 역순으로 처리해서 successor 제약을 먼저 보고 노드를 가능한 한 오른쪽 기준으로 붙인다.
- 같은 depth 에서는 아래 순서를 유지하되, 오른쪽에서 왼쪽으로 채워서 right-aligned baseline 을 만든다.
- 마지막 `buildFinalGraphLayout()` 에서 `x` 도 `y` 처럼 정규화해서 그래프 전체를 padding 안으로 옮긴다.

## 영향 범위

- 변경 필요:
  - `django_apps/web/static/web/js/solver_graph_layout.js`
  - `django_apps/web/templates/web/solver.html`
  - `tests/unit/web/test_solver_graph_layout.py`
  - `tests/integration/web/test_web_smoke.py`
- 변경 불필요:
  - `SolverGraph.direction`
  - graph serializer payload shape
  - graph preview renderer / cache / fallback
  - edge 의미 (`from -> to`)

## 테스트 관점

- 기존 left-to-right edge 검증은 유지해야 한다.
- 새 검증은 "깊이가 같은 terminal node 들이 target 쪽 우측 기준으로 한 칸 간격 정렬되는가" 를 확인하면 된다.
- smoke test 는 더 이상 `right-to-left DAG` 같은 표현을 쓰지 않고, 좌→우 흐름과 right-aligned layout style 을 같이 설명하도록 바뀌어야 한다.

## 결론

이번 변경은 backend 계약 수정이 아니라 프런트 레이아웃 알고리즘 교체에 가깝다. 구현 핵심은 `solver_graph_layout.js` 의 horizontal placement 를 predecessor 기반 전진 배치에서 successor 기반 역방향 우측 앵커 배치로 바꾸는 것이다.
