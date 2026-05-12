# Plan: materialized graph render parity (2026-05-02)

관련 리서치: [documents/research_materialized_graph_render_parity_2026-05-02.md](./research_materialized_graph_render_parity_2026-05-02.md)

원본 요청 요약: materialized graph 에서는 최근에 바꾼 카드/edge UI 가 반영되지 않는 것처럼 보인다.

## 목표

- raw graph 와 materialized graph 가 같은 최신 renderer 를 사용하도록 브라우저 캐시 충돌 가능성을 줄인다.
- 실제 materialized graph payload 도 새 마크업 규칙을 통과한다는 테스트를 추가한다.

## 구현 접근

1. solver 페이지의 `solver_timeline.js` script src 에 graph UI version query 를 붙인다.
2. graph 관련 module import 체인에도 동일 version query 를 붙여 nested module 캐시를 분리한다.
3. materialized graph API payload 를 `renderSolverGraph()` 로 렌더하는 테스트를 추가한다.

## 변경 대상

- `django_apps/web/templates/web/solver.html`
- `django_apps/web/static/web/js/solver_timeline.js`
- `django_apps/web/static/web/js/solver_timeline/graph_mount.js`
- `django_apps/web/static/web/js/solver_timeline/graph_viewport.js`
- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- `tests/unit/web/test_solver_graph_markup.py`

## 검증

- `pytest`
- `ruff check .`
- `mypy .`
- `black .`
