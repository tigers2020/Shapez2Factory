# solver graph quantity replica toggle 리서치

날짜: 2026-05-02

## 요청 요약

solver graph 에 버튼을 추가해서, 켰을 때 `quantity` 만큼 base/source 와 target node 를 실제로 복제해서 보이게 만든다.

## 현재 구조 요약

현재 graph 생성과 표시 책임은 아래처럼 나뉜다.

- 백엔드
  - `django_apps/shapez_solver/services/recipe_graph_builder.py`
  - `django_apps/shapez_solver/view_graph_serialization.py`
  - 역할: 대표 graph 구조와 node metadata, preview URL 을 만든다.
- 프런트
  - `django_apps/web/static/web/js/solver_timeline/timeline_request.js`
  - `django_apps/web/static/web/js/solver_timeline/graph_mount.js`
  - `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
  - `django_apps/web/static/web/js/solver_graph_layout.js`
  - 역할: graph 를 받아 마크업과 좌표를 계산하고 선택 상세를 보여 준다.

중요한 현재 계약:

- source / target node 는 각 recipe output 당 1개만 존재한다.
- 필요한 물량은 node 개수가 아니라 `quantity` 로 표현한다.
- layout 은 서버가 아니라 클라이언트가 계산한다.

## 관련 코드 관찰

### 1. graph panel 진입점

`django_apps/web/templates/web/solver.html`

- graph panel 루트는 `[data-solver-timeline]`
- 현재는 target input, error/warning, throughput summary, graph canvas, detail host 만 있다.
- replica toggle UI 는 이 패널 안에 두는 것이 자연스럽다.

### 2. graph fetch / mount 흐름

`django_apps/web/static/web/js/solver_timeline/timeline_request.js`

- API 응답을 받아 `mountGraph(panel, graph)` 로 넘긴다.
- 여기서는 graph 를 저장하거나 별도 UI 상태를 관리하지 않는다.

`django_apps/web/static/web/js/solver_timeline/graph_mount.js`

- `renderSolverGraph(graph)` 로 HTML 렌더
- 클릭 선택 이벤트와 detail 패널 렌더 연결
- 기본 선택은 `role === "target"` 노드 우선

즉 toggle 상태를 반영하려면 `mountGraph()` 가 원본 graph 와 파생 graph 를 구분해서 다룰 수 있어야 한다.

### 3. graph 마크업 / 좌표 계산

`django_apps/web/static/web/js/solver_timeline/graph_markup.js`

- `renderSolverGraph(graph)` 가 직접 `computeGraphLayout(graph)` 를 호출한다.
- node id 는 DOM `data-graph-node-id` 와 선택 상태의 기준이다.
- quantity badge 는 현재 노드 복제가 아니라 라벨 표시용이다.

`django_apps/web/static/web/js/solver_graph_layout.js`

- 주어진 `nodes`, `edges` 를 순수하게 받아 DAG layout 을 계산한다.
- 즉 replica toggle 은 layout 알고리즘 변경 없이, 입력 graph 를 파생 생성해서 해결할 수 있다.

### 4. 선택 상세 패널

`django_apps/web/static/web/js/solver_timeline/graph_detail.js`

- 선택된 node id 로 `graph.nodes` 에서 직접 노드를 찾는다.
- 연결 edge 도 같은 graph 객체에서 계산한다.

그래서 복제 node 를 만들면:

- replica node id 는 원본과 충돌하지 않아야 한다.
- detail 패널은 replica node 도 정상 조회 가능해야 한다.

## 가장 안전한 구현 방향

백엔드 payload 는 유지하고, 프런트에서 “복제 표시용 파생 graph” 를 만드는 방식이 가장 안전하다.

이유:

1. 현재 API / serializer / DTO 계약을 건드리지 않아도 된다.
2. 기존 solver graph 생성 로직과 테스트를 거의 그대로 유지할 수 있다.
3. toggle 은 순수 UI 상태이므로 프런트에 두는 편이 책임이 자연스럽다.

## 파생 graph 생성 규칙 초안

toggle 이 꺼져 있으면 현재 graph 그대로 사용한다.

toggle 이 켜져 있으면:

- `role === "source"` 이고 `quantity > 1` 인 node:
  - quantity 수만큼 replica node 생성
- `role === "target"` 이고 `quantity > 1` 인 node:
  - quantity 수만큼 replica node 생성
- 그 외 intermediate / operation node:
  - 원본 그대로 유지

복제 규칙 후보:

### source node

- 원본 source node 는 제거하고 replica 들로 대체
- 각 replica quantity 는 `1`
- 각 replica 는 원본 source 와 동일한 operation edge 목적지로 연결

예:

- 원본: `source SuSuSuSu quantity=2`
- 변환:
  - `source SuSuSuSu #1 quantity=1`
  - `source SuSuSuSu #2 quantity=1`
- 두 replica 모두 동일 downstream operation 으로 edge 연결

### target node

- 원본 target node 는 제거하고 replica 들로 대체
- 각 replica quantity 는 `1`
- 원본 target 으로 들어오던 upstream output edge 를 모든 replica 에 복제

예:

- 원본: `target CuRuSuSu quantity=4`
- 변환:
  - `target #1`
  - `target #2`
  - `target #3`
  - `target #4`
- upstream operation output edge 가 각 target replica 로 복제됨

## 열린 결정 포인트

### 1. target/source quantity 가 1일 때도 toggle 표시를 유지할지

추천:

- 버튼은 항상 보이되, 실제 node 수 변화는 `quantity > 1` 인 경우에만 발생

이유:

- UI 일관성이 좋다.
- 어떤 shape 는 변화가 없더라도 기능 존재를 사용자가 이해할 수 있다.

### 2. replica label 을 어떻게 보일지

후보:

- `Source #1`, `Source #2`
- `Target #1`, `Target #2`
- shape code 는 그대로 두고 badge 만 `COPY 1/4`

추천:

- 기존 `label` 은 유지하고, 작은 badge 로 `COPY 1/4` 또는 `COPY 2/4` 표시

이유:

- 원래 의미를 해치지 않는다.
- 상세 패널과 카드 텍스트가 덜 요란하다.

### 3. detail 패널 quantity 표기

복제 node 는 실물 1개를 나타내므로 detail 에는 `Quantity x1` 이 자연스럽다.

대신 원본 맥락이 필요하면 replica 메타데이터를 추가해:

- `Replica 2 of 4`
- `Expanded from target quantity`

정도로 보일 수 있다.

## 테스트 영향

### integration web

`tests/integration/web/test_web_smoke.py`

- solver page 에 toggle 버튼 마커가 렌더되는지 확인 필요
- 기존 smoke marker 를 깨지지 않게 유지해야 함

### unit web

새 테스트가 필요해 보인다.

후보:

- `expandGraphQuantities()` 같은 helper 의 순수 단위 테스트
  - source quantity 2 -> source node 2개
  - target quantity 4 -> target node 4개
  - intermediate / operation node 유지
  - edge 복제 수 확인
  - 기존 원본 graph 불변성 확인
- layout 테스트
  - 확장 graph 도 `computeGraphLayout()` 에서 left-to-right edge 조건을 만족하는지

## 리스크

1. target replica 가 많아지면 같은 upstream operation 에서 fan-out edge 가 크게 늘어난다.
2. source replica 가 많으면 같은 downstream operation 에 edge 가 겹쳐 보일 수 있다.
3. 선택 기본값이 “첫 target” 인데 target replica 여러 개가 생기면 어느 replica 를 기본 선택할지 정해야 한다.
4. detail 패널에서 replica 의 의미가 모호하면 사용자가 “왜 다 같은 노드가 여러 개지?”라고 느낄 수 있다.

## 결론

이 기능은 백엔드 graph 계약을 바꾸기보다, 프런트에서 toggle 기반 파생 graph 를 만드는 방식이 가장 안전하다.

핵심 작업 범위는:

- solver page 에 toggle 버튼 추가
- graph mount 경로에 UI 상태 추가
- source/target quantity 를 replica node 들로 확장하는 프런트 helper 추가
- replica 카드와 detail UI 보강
- unit/integration 테스트 추가
