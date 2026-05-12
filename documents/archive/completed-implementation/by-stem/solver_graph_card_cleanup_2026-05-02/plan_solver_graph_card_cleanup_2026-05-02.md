# Plan: solver graph card cleanup and straight edge routing (2026-05-02)

관련 리서치: [documents/research_solver_graph_card_cleanup_2026-05-02.md](./research_solver_graph_card_cleanup_2026-05-02.md)

원본 요청 요약: solver graph 에서 preview card 내부 스크롤을 없애고, 다중 input 라인을 더 읽기 쉽게 분리하며, 곡선 edge 를 elbow 직선으로 바꾼다.

## 목표

- shape preview card 는 내부 스크롤바 없이 고정 카드처럼 보인다.
- operation 카드의 `Input A/B` 같은 다중 입력은 서로 다른 도착 lane 을 사용한다.
- edge path 는 cubic bezier 대신 `M/L` 기반 elbow polyline 으로 렌더링된다.
- solver graph payload 와 backend graph 생성 로직은 변경하지 않는다.

## 구현 접근

1. `graph_markup.js` 에서 shape card 루트 overflow 와 내부 spacing 을 줄이고 preview 높이를 고정한다.
2. edge geometry helper 를 분리해서 source/destination anchor 와 lane offset 을 계산한다.
3. operation input/output 에 대해 slot label 기반 lane index 를 적용한다.
4. edge label 위치를 destination-side horizontal segment 근처로 옮긴다.
5. graph markup 전용 unit test 를 추가하고 smoke test marker 를 보강한다.

## 변경 대상

- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- `tests/unit/web/test_solver_graph_markup.py`
- `tests/integration/web/test_web_smoke.py`

## 검증

- `pytest`
- `ruff check .`
- `mypy .`
- `black .`

## 메모

- `solver_graph_layout.js` 의 노드 높이는 우선 유지하고, 카드 압축만으로 해결되는지 본다.
- 필요하다면 이후 별도 작업으로 shape/output fanout lane 분리를 확장할 수 있다.
