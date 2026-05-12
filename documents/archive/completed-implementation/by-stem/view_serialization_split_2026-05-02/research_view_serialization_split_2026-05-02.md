# view_serialization split research (2026-05-02)

- 대상 파일은 [django_apps/shapez_solver/view_serialization.py](../../../../../django_apps/shapez_solver/view_serialization.py) 이다.
- 현재 책임은 5묶음이다.
  1. solve 성공 payload 조립 (`serialize_solver_result`)
  2. base demand / step serialization
  3. solver graph serialization (`serialize_solver_graph`, `serialize_graph_node`, `serialize_graph_edge`)
  4. preview scene fallback build (`build_preview_scene`, `serialize_render_scene`)
  5. 실패 payload 조립 (`error_payload`)
- 외부 호출자는 현재 [django_apps/shapez_solver/views.py](../../../../../django_apps/shapez_solver/views.py) 한 곳이다.
- graph serialization은 [django_apps/web/services/graph_preview.py](../../../../../django_apps/web/services/graph_preview.py) 와 직접 연결되고, result payload/step serialization은 graph 없이도 독립 의미를 가진다.
- API 계약 테스트는 [tests/integration/api/test_solver_api.py](../../../../../tests/integration/api/test_solver_api.py) 와 [tests/integration/web/test_web_smoke.py](../../../../../tests/integration/web/test_web_smoke.py) 가 주로 본다.
- 따라서 가장 안전한 분리 방식은 공개 함수 `serialize_solver_result()` 와 `error_payload()` 는 유지하고, graph/preview 관련 함수를 별도 모듈로 옮겨서 위임하는 것이다.
- 이렇게 하면 `views.py` import 경로는 그대로 두고, 추후 graph serialization만 별도로 테스트하거나 교체하기 쉬워진다.
