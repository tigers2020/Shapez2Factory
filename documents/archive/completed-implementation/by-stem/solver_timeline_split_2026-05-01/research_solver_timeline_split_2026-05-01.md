# solver_timeline split research (2026-05-01)

- 대상 파일은 [django_apps/web/static/web/js/solver_timeline.js](../../../../../django_apps/web/static/web/js/solver_timeline.js) 이고 현재 576줄 규모다.
- 외부 계약은 [django_apps/web/templates/web/solver.html](../../../../../django_apps/web/templates/web/solver.html) 의 `data-solver-*`, `data-graph-*`, `data-shape-gltf-viewer` 셀렉터와 [django_apps/web/static/web/js/solver_timeline.js](../../../../../django_apps/web/static/web/js/solver_timeline.js) 파일명을 유지하는 것이다.
- 현재 책임 군집은 5개다: 공통 DOM 유틸(`escapeHtml`, `setBanner`, viewer dispose), 그래프 마크업(`renderShapeGraphNode`, `renderGraphEdges`, `renderSolverGraph`), viewport 상호작용(`resetGraphViewport`, `zoomGraphViewport`, `initGraphViewport`), 선택 상세패널(`connectedEdges`, `renderSelectedNodeDetail`, `mountGraph`), 요청/상태 처리(`renderThroughputSummary`, `requestTimeline`, `scheduleTimeline`, `initSolverTimeline`).
- 현재 워크트리는 더티 상태이며 특히 [django_apps/web/static/web/js/solver_timeline.js](../../../../../django_apps/web/static/web/js/solver_timeline.js) 에 quantity badge, throughput summary, `target_count` 반영 로직이 이미 추가되어 있다. 이번 작업은 해당 기능을 보존한 채 모듈로 이동해야 한다.
- 현재 웹 스모크는 이번 프론트 작업과 무관하게 [django_apps/shapez_solver/services/factory_throughput_service.py](../../../../../django_apps/shapez_solver/services/factory_throughput_service.py) 의 `graph_builder` import 실패로 막힐 가능성이 높다.
