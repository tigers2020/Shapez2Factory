# Plan: graph preview SVG cleanup (2026-05-02)

관련 리서치: [documents/research_graph_preview_svg_cleanup_2026-05-02.md](./research_graph_preview_svg_cleanup_2026-05-02.md)

원본 요청 요약: graph preview fallback 에 남아 있는 SVG 관련 죽은 코드를 모두 제거하고, PNG 기반 경로만 유지한다.

## 구현 접근

1. [django_apps/web/services/graph_preview.py](../../../../../django_apps/web/services/graph_preview.py) 에서 lightweight SVG renderer, SVG helper, `markup` 기반 fallback 을 삭제한다.
2. PNG renderer 는 생성 성공 시 `image_url` 을 반환하고, 실패 시 `image_url=None` 과 `alt_text` 만 반환하는 단순 결과로 축소한다.
3. [django_apps/shapez_solver/view_serialization.py](../../../../../django_apps/shapez_solver/view_serialization.py) 에서 `preview_markup` 필드를 제거한다.
4. [django_apps/web/static/web/js/solver_timeline/graph_markup.js](../../../../../django_apps/web/static/web/js/solver_timeline/graph_markup.js) 는 image-only 렌더링으로 단순화하고, 이미지가 없으면 텍스트 fallback 만 보여 준다.
5. graph preview/unit/integration 테스트에서 SVG 선택과 markup 기대치를 제거하고, PNG/no-image 경로를 검증하도록 갱신한다.

## 호환성 기준

- solver graph node 는 `preview_image_url` 과 `preview_alt` 를 계속 제공해야 한다.
- PNG cache hit 경로와 cache URL 구조는 유지한다.
- 프리뷰 생성 실패 시 API/페이지가 깨지지 않고 "No preview" fallback 으로 남아야 한다.

## 검증

- `python -m pytest tests/unit/web/test_graph_preview.py`
- `python -m pytest tests/integration/web/test_web_smoke.py`
- `python -m pytest tests/integration/api/test_solver_api.py`
- `python -m pytest`
- `python -m ruff check .`
- `python -m mypy .`
- `python -m black .`
