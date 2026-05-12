# graph_preview.py 리팩토링 플랜

날짜: 2026-05-02

## 목표

- `graph_preview.py`의 단일 거대 renderer를 내부 helper 조합 구조로 단순화한다.
- 공개 계약과 동작은 유지한다.
- SVG 관련 코드는 추가하지 않는다.

## 변경 범위

- `django_apps/web/services/graph_preview.py`
- 필요 시 `tests/unit/web/test_graph_preview.py`

## 접근

1. cache key, cache path, image url, alt text를 묶는 내부 target helper를 만든다.
2. PNG 캐시 조회와 PNG 유효성 검사를 전담하는 내부 cache helper를 만든다.
3. scene 파일 작성과 `node render_graph_preview.mjs` 호출을 전담하는 내부 prerender helper를 만든다.
4. `PlaywrightPngGraphPreviewRenderer.render()`는 orchestration만 남긴다.
5. 기존 테스트를 돌려 계약 보존을 확인한다.

## 기대 효과

- 파일 읽을 때 책임 경계가 더 선명해진다.
- 이후 cache 정책이나 prerender 전략 변경이 쉬워진다.
- 실패 fallback 동작을 더 추적하기 쉬워진다.
