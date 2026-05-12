# graph_markup.js 리서치

날짜: 2026-05-02

## 대상

- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- `django_apps/web/static/web/js/solver_timeline.js`
- `tests/integration/web/test_web_smoke.py`

## 현재 관찰

- `graph_markup.js` 한 파일이 아래 책임을 함께 가진다.
  - quantity badge 포맷
  - shape node preview fallback markup
  - shape card markup
  - operation node markup
  - edge svg path/label markup
  - viewport/stage/zoom control markup
- 공개 entrypoint는 `renderSolverGraph(graph)` 하나다.
- smoke 테스트는 `solver_timeline.js`의 compatibility marker comment와 실제 페이지 렌더 경로를 간접 검증한다.
- 현재 안내 문구 문자열에 깨진 문자 `夷?wheel to zoom`이 섞여 있다.

## 리팩토링 포인트

- preview body, shape header, shape footer badge, controls, hint, stage wrapper를 helper로 분리하면 node renderer가 짧아진다.
- edge path 계산과 edge label markup도 분리 가능하다.
- `renderSolverGraph()`는 layout 계산 후 viewport 조립만 남기는 편이 더 읽기 좋다.

## 주의점

- `renderSolverGraph()` export와 `GRAPH_PADDING`, `NODE_HEIGHT`, `NODE_WIDTH` 재export는 유지해야 한다.
- smoke marker인 `data-graph-viewport`, `preview_image_url`, `No preview`, `./solver_graph_layout.js`는 유지하는 편이 안전하다.
- 문자열 수정 시 테스트가 기대하는 `"wheel to zoom"` 텍스트는 그대로 포함해야 한다.
