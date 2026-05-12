# Plan: solver graph quantity replica toggle (2026-05-02)

관련 리서치: [documents/research_solver_graph_quantity_replica_toggle_2026-05-02.md](./research_solver_graph_quantity_replica_toggle_2026-05-02.md)

원본 요청 요약: solver graph 에 버튼을 추가해서, 활성화 시 `quantity` 만큼 base/source 와 target node 를 실제 복제 표시한다.

## 목표

- 기본 graph 표시와 API payload 는 유지한다.
- 사용자가 버튼으로 “대표 노드 보기”와 “quantity 복제 보기”를 전환할 수 있어야 한다.
- 복제 보기는 source/target node 만 확장하고 intermediate / operation node 는 기존대로 유지한다.

## 구현 접근

1. solver page graph panel 에 replica toggle 버튼을 추가한다.
2. 프런트에 graph view state 를 두고, 원본 graph 와 확장 graph 를 전환해서 mount 한다.
3. 별도 helper 에서 source/target `quantity` 를 replica node/edge 로 확장한다.
4. replica node 가 기존 선택/상세 패널과 충돌하지 않도록 id 와 표시 메타데이터를 부여한다.
5. smoke / unit 테스트를 추가한다.

## 변경 대상

- `django_apps/web/templates/web/solver.html`
- `django_apps/web/static/web/js/solver_timeline.js`
- `django_apps/web/static/web/js/solver_timeline/timeline_request.js`
- `django_apps/web/static/web/js/solver_timeline/graph_mount.js`
- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- `django_apps/web/static/web/js/solver_timeline/graph_detail.js`
- 새 helper 파일 1개
  - 예: `django_apps/web/static/web/js/solver_timeline/graph_quantity_toggle.js`
- 테스트
  - `tests/integration/web/test_web_smoke.py`
  - 새 unit 테스트 1개

## 세부 단계

### 1. UI 토글 추가

- graph panel 상단에 버튼을 추가한다.
- 기본 상태는 off 로 둔다.
- panel dataset 또는 JS state 로 현재 on/off 를 저장한다.
- 토글 라벨은 quantity 복제 목적이 바로 드러나게 둔다.

예:

- `Show quantity replicas`
- off/on 스타일 변경

### 2. 파생 graph helper 추가

새 helper 는 아래 계약을 가진다.

- 입력: serialized graph payload
- 출력: 원본과 같은 shape 의 graph payload

동작:

- `quantity <= 1` 이면 원본 노드 유지
- `role === "source"` 또는 `role === "target"` 이고 `quantity > 1` 이면:
  - node 를 quantity 수만큼 복제
  - 복제 node `quantity = 1`
  - replica metadata 추가
    - `replica_index`
    - `replica_total`
    - `replica_of`
  - 관련 edge 를 각 replica 에 맞춰 복제

id 규칙 예:

- `${node.id}::replica::1`
- `${node.id}::replica::2`

### 3. mount 흐름 연결

- 최신 API graph 는 panel 에 원본으로 저장한다.
- 토글 on/off 시 재요청 없이 현재 graph 를 다시 render 한다.
- on 이면 helper 로 확장한 graph 를 `renderSolverGraph()` 와 detail selection 에 넘긴다.

### 4. 마크업 / 상세 표시 보강

- replica node 카드에 `COPY 1/4` 같은 작은 badge 를 추가한다.
- detail 패널에서도 replica 정보 문구를 보여 준다.
- 기존 quantity badge 는 replica node 에서는 `x1` 이 되므로, 원본 대비 왜 늘어났는지 보조 문구가 필요하다.

### 5. 테스트

- integration smoke:
  - solver page 에 toggle 마커가 있는지
- unit:
  - helper 가 source/target 만 확장하는지
  - edge 복제가 맞는지
  - quantity 가 1이면 불변인지
  - 원본 graph 를 mutate 하지 않는지

## 트레이드오프

- 장점:
  - 백엔드 계약을 바꾸지 않는다.
  - 토글 UX 를 빠르게 구현할 수 있다.
  - layout 엔진 재사용이 가능하다.
- 단점:
  - target/source fan-out 이 커지면 그래프가 넓고 복잡해질 수 있다.
  - edge 중복이 많아져 시각적으로 조밀해질 수 있다.

## 검증 계획

- `python -m pytest tests/integration/web/test_web_smoke.py`
- `python -m pytest` 또는 최소한 새 web unit 테스트 + 관련 smoke
- 필요 시 `python -m ruff check django_apps/web/static/web/js tests`

## 승인 후 구현 메모

- 백엔드 `recipe_graph_builder.py` 는 이번 범위에서 건드리지 않는다.
- API 응답 필드 추가도 우선은 피하고, 프런트 파생 데이터로 해결한다.
- replica 확장은 source/target 만 대상으로 제한한다.
