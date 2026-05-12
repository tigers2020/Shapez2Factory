# Plan: shapez_solver views split (2026-05-01)

관련 리서치: [documents/research_shapez_solver_views_split_2026-05-01.md](./research_shapez_solver_views_split_2026-05-01.md)

원본 요청 요약: [django_apps/shapez_solver/views.py](../../../../../django_apps/shapez_solver/views.py) 의 요청 파싱/응답 직렬화 책임을 분리하되, 엔드포인트와 JSON payload 계약은 그대로 유지한다.

## 구현 접근

1. request parsing (`code`, `target_count`, `max_depth`, JSON body 해석) 을 `view_request_parsing.py` 로 추출한다.
2. 성공/실패 payload 와 graph/preview 직렬화를 `view_serialization.py` 로 추출한다.
3. [views.py](../../../../../django_apps/shapez_solver/views.py) 는 서비스 호출과 예외 매핑 중심의 thin controller 로 정리한다.

## 호환성 기준

- `/api/solver/solve/` 라우트와 `solve_shape` 함수는 그대로 유지한다.
- `INVALID_REQUEST`, `EMPTY_SHAPE_CODE`, `SHAPE_CODE_PARSE_ERROR`, `INVALID_TARGET_COUNT`, `UNSUPPORTED_TARGET`, `SOLVER_VALIDATION_ERROR` 응답 구조는 바꾸지 않는다.
- graph node/edge, preview scene, operation icon 직렬화 필드명은 유지한다.

## 검증

- `python -m pytest tests/integration/api/test_solver_api.py`
- `python -m pytest tests/integration/web/test_web_smoke.py`
