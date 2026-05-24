# shapez_solver views split research (2026-05-01)

- Target file: [django_apps/shapez_solver/views.py](../../../../../django_apps/shapez_solver/views.py); request parsing, service calls, error mapping, and graph/preview response serialization live in one file.
- External contract is `/api/solver/solve/` response shape and fields verified by [tests/integration/web/test_web_smoke.py](../../../../../tests/integration/web/test_web_smoke.py) and [tests/integration/api/test_solver_api.py](../../../../../tests/integration/api/test_solver_api.py): `ok`, `error`, `target`, `target_count`, `base_demands`, `steps`, `graph.nodes`, `graph.edges`, `preview_markup`, `preview_image_url`.
- Internal responsibilities group into three: request extraction (`_extract_*`), success/failure payload assembly (`_serialize_solver_result`, `_error_payload`), graph/preview detail serialization (`_serialize_solver_graph`, `_serialize_graph_node`, `_serialize_render_scene`).
- Safest refactor: keep view function bodies, move request parsing and response serialization to separate modules.
