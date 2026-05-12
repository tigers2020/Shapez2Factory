# solver graph card cleanup 리서치
날짜: 2026-05-02

## 요청 요약

- preview card 내부 스크롤 제거
- 다중 input 이 operation 카드에 들어올 때 어떤 라인이 어떤 포트로 들어가는지 더 읽기 쉽게 분리
- 현재 곡선형 edge 를 직선형, 구체적으로 elbow 스타일의 꺾이는 선으로 변경

## 현재 구조 관찰

### 1. shape card 스크롤 원인

`django_apps/web/static/web/js/solver_timeline/graph_markup.js`

- shape card 루트가 `overflow-x-hidden overflow-y-auto` 를 직접 사용한다.
- 카드 본문이 `flex-1` 기반으로 늘어나고 preview 영역도 `flex-1` 을 차지한다.
- target/source 카드에 `OUTPUT`, `BATCH`, `CONSUMED/UNUSED`, `REUSED` 같은 badge 가 겹치면 카드 높이보다 내용이 커지면서 내부 스크롤바가 발생한다.

### 2. edge 라벨 겹침 원인

- `computeEdgeGeometry()` 가 모든 edge 의 anchor 를 노드 세로 중앙 한 점으로만 계산한다.
- `renderEdgeLabel()` 은 midpoint 기준 한 위치에 `foreignObject` 를 올린다.
- 따라서 `Input A`, `Input B` 처럼 같은 operation 카드로 들어가는 line 들이 시각적으로 거의 같은 위치를 공유한다.

### 3. 곡선형 edge 구현 위치

- `renderEdgePath()` 가 SVG cubic bezier (`C`) 한 종류만 만든다.
- operation input/output 별 port 분리는 없고, 모든 edge 가 카드 중앙에서 출발/도착한다.

## 구현에 필요한 사실

- backend payload 는 이미 `edge.slot`, `edge.label`, `edge.kind`, operation `input_count`, `output_count` 를 제공한다.
- `recipe_graph_builder.py` 는 input edge 를 `Input A`, `Input B`, ... 식으로 만들고 output edge 도 `Output A`, `Output B`, ... 식으로 만든다.
- 따라서 frontend 만으로 lane index 를 파생할 수 있고 API 변경은 불필요하다.

## 변경 방향

- shape card 는 `overflow-hidden` 으로 바꾸고 preview 영역을 고정 높이로 바꿔 내부 스크롤 자체를 없앤다.
- edge anchor 는 operation 카드에서만 slot 기반 lane offset 을 적용한다.
- edge path 는 `M/L` 기반 elbow polyline 으로 바꾼다.
- 라벨은 midpoint 가 아니라 destination 쪽 마지막 horizontal segment 근처에 두고, lane offset 을 그대로 따라가게 해 입력 포트와 같이 읽히게 만든다.

## 테스트 방향

- graph markup 렌더 결과 문자열 기준으로:
  - `overflow-y-auto` 제거 확인
  - path 에 cubic bezier `C` 가 없고 `L` 기반 꺾임 경로 사용 확인
  - `Input A`, `Input B` edge geometry 의 destination `y` 값이 다름을 확인
- 기존 layout test 는 유지해서 좌→우 단조성과 bounds 안정성을 계속 보장한다.
