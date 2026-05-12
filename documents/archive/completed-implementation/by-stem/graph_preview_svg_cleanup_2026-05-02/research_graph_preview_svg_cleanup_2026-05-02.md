# graph preview SVG cleanup research (2026-05-02)

- 사용자 요청은 SVG 관련 코드를 죽은 코드로 보고 모두 삭제하는 것이다.
- 현재 SVG 경로의 핵심은 [django_apps/web/services/graph_preview.py](../../../../../django_apps/web/services/graph_preview.py) 안의 `LightweightGraphPreviewRenderer` 와 `_render_scene_markup()` 계열 helper 다.
- [config/settings.py](../../../../../config/settings.py) 기본값은 이미 `SOLVER_GRAPH_PREVIEW_RENDERER = "playwright_png"` 이다. 즉 런타임 기본 경로는 PNG 프리뷰이며, SVG는 fallback/선택 모드로만 남아 있다.
- [django_apps/shapez_solver/view_serialization.py](../../../../../django_apps/shapez_solver/view_serialization.py) 는 graph shape node payload에 `preview_markup`, `preview_image_url`, `preview_alt` 를 함께 실어 보낸다.
- 프런트에서는 [django_apps/web/static/web/js/solver_timeline/graph_markup.js](../../../../../django_apps/web/static/web/js/solver_timeline/graph_markup.js) 가 `node.preview_markup || "No preview"` fallback 을 사용한다. 즉 SVG markup payload가 아직 직접 소비된다.
- 테스트는 [tests/unit/web/test_graph_preview.py](../../../../../tests/unit/web/test_graph_preview.py) 에서 lightweight renderer 선택과 SVG markup 출력을 검증하고, [tests/integration/web/test_web_smoke.py](../../../../../tests/integration/web/test_web_smoke.py) 에서 `preview_markup` 문자열 존재를 확인한다.
- 따라서 SVG 삭제 범위는 세 묶음이다.
  1. backend renderer: lightweight SVG renderer와 관련 helper 삭제
  2. API serialization: `preview_markup` 필드 제거
  3. frontend/tests: markup fallback 제거, image/no-preview 경로 기준으로 갱신
- `PlaywrightPngGraphPreviewRenderer` 는 현재 PNG 생성 실패 시 lightweight renderer fallback 으로 돌아간다. SVG를 제거하려면 실패 시 `image_url=None` 인 빈 preview 결과를 내려주는 쪽이 자연스럽다.
- `graph_preview_cache` URL과 PNG cache key 경로는 SVG와 무관하므로 유지해도 된다.
