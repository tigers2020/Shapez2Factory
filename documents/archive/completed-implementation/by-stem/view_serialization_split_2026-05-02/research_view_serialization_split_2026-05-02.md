# view_serialization split research (2026-05-02)

- Target file: [django_apps/shapez_solver/view_serialization.py](../../../../../django_apps/shapez_solver/view_serialization.py).
- Current responsibilities fall into five groups:
  1. successful solve payload assembly (`serialize_solver_result`)
  2. base demand / step serialization
  3. solver graph serialization (`serialize_solver_graph`, `serialize_graph_node`, `serialize_graph_edge`)
  4. preview scene fallback build (`build_preview_scene`, `serialize_render_scene`)
  5. failure payload assembly (`error_payload`)
- External caller today is only [django_apps/shapez_solver/views.py](../../../../../django_apps/shapez_solver/views.py).
- Graph serialization connects directly to [django_apps/web/services/graph_preview.py](../../../../../django_apps/web/services/graph_preview.py); result payload/step serialization is meaningful independently of graph.
- API contract tests are mainly reviewed by [tests/integration/api/test_solver_api.py](../../../../../tests/integration/api/test_solver_api.py) and [tests/integration/web/test_web_smoke.py](../../../../../tests/integration/web/test_web_smoke.py).
- Safest split: keep public functions `serialize_solver_result()` and `error_payload()`, move graph/preview functions to a separate module and delegate.
- This keeps `views.py` import paths unchanged and makes graph serialization easier to test or swap later.
