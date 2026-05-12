# Plan: view_serialization split (2026-05-02)

관련 리서치: [documents/research_view_serialization_split_2026-05-02.md](./research_view_serialization_split_2026-05-02.md)

원본 요청 요약: `view_serialization.py` 안에 섞여 있는 graph/preview serialization 책임을 분리하되, 현재 API payload 계약은 유지한다.

## 구현 접근

1. graph node/edge/preview serialization을 새 모듈로 추출한다.
2. [view_serialization.py](../../../../../django_apps/shapez_solver/view_serialization.py) 는 solve result payload, base demand, step, error payload 중심으로 줄인다.
3. `serialize_solver_result()` 는 새 graph serialization helper 를 호출만 하도록 정리한다.

## 호환성 기준

- `from django_apps.shapez_solver.view_serialization import serialize_solver_result, error_payload` 는 그대로 동작해야 한다.
- `target`, `target_count`, `base_demands`, `steps`, `graph` 필드 구조는 유지한다.
- graph node의 `preview_image_url`, `preview_alt`, `quantity`, `reused_count` 필드는 유지한다.

## 검증

- `python -m pytest tests/integration/api/test_solver_api.py`
- `python -m pytest tests/integration/web/test_web_smoke.py`
- `python -m mypy django_apps/shapez_solver/view_serialization.py`
- `python -m ruff check django_apps/shapez_solver/view_serialization.py`
