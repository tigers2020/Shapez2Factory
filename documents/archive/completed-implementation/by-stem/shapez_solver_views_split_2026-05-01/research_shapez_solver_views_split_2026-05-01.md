# shapez_solver views split research (2026-05-01)

- 대상 파일은 [django_apps/shapez_solver/views.py](../../../../../django_apps/shapez_solver/views.py) 이고, 현재 단일 파일에 요청 파싱, 서비스 호출, 에러 매핑, graph/preview 응답 직렬화가 함께 들어 있다.
- 외부 계약은 `/api/solver/solve/` 엔드포인트 응답 shape 와 [tests/integration/web/test_web_smoke.py](../../../../../tests/integration/web/test_web_smoke.py), [tests/integration/api/test_solver_api.py](../../../../../tests/integration/api/test_solver_api.py) 가 검증하는 `ok`, `error`, `target`, `target_count`, `base_demands`, `steps`, `graph.nodes`, `graph.edges`, `preview_markup`, `preview_image_url` 필드다.
- 내부 책임은 3묶음이다: 요청 추출(`_extract_*`), 성공/실패 payload 조립(`_serialize_solver_result`, `_error_payload`), graph/preview 세부 직렬화(`_serialize_solver_graph`, `_serialize_graph_node`, `_serialize_render_scene`).
- 리팩토링은 뷰 함수 본문은 유지하되, request parsing 과 response serialization 을 별도 모듈로 옮기는 방식이 가장 안전하다.
