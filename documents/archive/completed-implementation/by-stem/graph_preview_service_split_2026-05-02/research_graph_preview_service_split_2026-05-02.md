# graph_preview.py 리서치

날짜: 2026-05-02

## 대상

- `django_apps/web/services/graph_preview.py`
- `tests/unit/web/test_graph_preview.py`
- `django_apps/shapez_solver/view_graph_serialization.py`

## 현재 관찰

- 현재 공개 계약은 `GraphPreview`, `GraphPreviewRenderer`, `get_graph_preview_renderer()`, `PlaywrightPngGraphPreviewRenderer`다.
- SVG fallback은 이미 제거되어 이제 PNG 생성만 공식 경로다.
- `PlaywrightPngGraphPreviewRenderer` 한 클래스가 아래 책임을 모두 가진다.
  - 캐시 키 계산
  - 캐시 경로/URL 조립
  - PNG 유효성 검사
  - 임시 scene json 파일 생성
  - `node render_graph_preview.mjs` subprocess 호출
  - 실패 후 generation disable 플래그 관리
- `view_graph_serialization.py`는 이 렌더러를 protocol 기반으로 소비하므로, 공개 계약만 유지하면 내부 분리는 안전하다.

## 테스트 기준

- 기본 renderer 선택은 PNG renderer여야 한다.
- cache key는 stable/versioned여야 한다.
- prerender 실패 시 `image_url is None` fallback 이어야 한다.
- 유효한 캐시 PNG가 있으면 재사용해야 한다.

## 리팩토링 포인트

- 캐시 책임과 subprocess 책임을 별도 helper로 나누면 orchestration이 짧아진다.
- `render()`는 아래 순서만 읽히게 만드는 편이 좋다.
  1. render target 계산
  2. 캐시 hit 검사
  3. generation disabled 검사
  4. PNG 생성 시도
  5. 실패 시 fallback
- 공개 import 경로와 테스트가 기대하는 메서드 `cache_key()`는 유지하는 편이 안전하다.

## 주의점

- 사용자 요청상 SVG 관련 죽은 코드는 다시 살리면 안 된다.
- 테스트가 subclass override로 `_invoke_playwright_prerender()`를 사용하고 있으므로, 이 override 포인트는 유지하는 편이 안전하다.
