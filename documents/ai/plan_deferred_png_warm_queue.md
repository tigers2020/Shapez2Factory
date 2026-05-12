# 플랜: 스태프 매크로 그래프 PNG 지연 생성 + 클라이언트 워밍 큐

**상태**: 승인 후 구현  
**작성**: 아키텍처 리뷰 반영 (2026-05-06)

---

## 한 줄 결론

**HTML/API 직렬화에서는 Playwright로 PNG를 만들지 않고(캐시 히트만), 누락된 프리뷰는 브라우저가 `warm` API를 동시성 1로 순차 호출해 한 장씩 생성한다.**

---

## 배경

| 기존 | 변경 후 |
|------|---------|
| 페이지 요청 한 번에 모든 shape 노드 PNG 렌더 | 페이지 요청은 캐시 조회만 → 빠른 응답 |
| Playwright 연속 실행 → Gunicorn 타임아웃·OOM 리스크 | 워밍 요청은 노드당 1회 HTTP → 한 요청당 Playwright 1회 |

**제약**: `GET /internal/graph-preview-cache/<hash>.png` 만으로는 `preview_scene`를 복원할 수 없어, **미스 시 PNG 생성은 이미지 GET 핸들러에 두지 않는다.**

---

## 설계

### 1) 직렬화: `sync_png` (이름 확정)

[`serialize_graph_node`](django_apps/shapez_solver/view_graph_serialization.py) 에 플래그 추가.

| `sync_png` | 동작 |
|------------|------|
| `True` (기본, 하위 호환) | 기존과 동일: cache miss 시 Playwright로 생성 |
| `False` | **cache hit**: `preview_image_url`·`preview_alt` 반환 / **cache miss**: PNG 생성 **안 함** |

**cache miss 시 노드 payload에 추가 필드** (스태프 매크로 그래프·워밍 클라이언트 계약):

- `preview_cache_key`: 문자열 (renderer의 cache_key와 동일; 워밍 요청 식별용)
- `needs_warm`: `true`
- `preview_scene`: 기존과 동일 (클라이언트가 warm POST 본문에 실을 수 있음)

선택: `preview_alt`는 `preview_scene` 없이도 채울 수 있으면 미리 넣어 두어 접근성 유지.

### 2) 렌더러: cache-only 조회

[`PlaywrightPngGraphPreviewRenderer`](django_apps/web/services/graph_preview.py) 에 **생성 없이** DB/파일스토어 여부만 보고 `GraphPreview` 를 돌려주는 함수 (예: `render_cached_only`).  
`NoopGraphPreviewRenderer` 는 항상 miss로 취급하거나 `image_url=None` 정책을 문서화.

### 3) 스태프 HTML 뷰

[`macro_pattern_graph`](django_apps/web/views.py): `serialize_recipe` / `serialize_macro_recipe_visual` 경로에 **`sync_png=False`** 전파 (시그니처는 `macro_recipe_graph_visual` / `view_graph_serialization` 쪽에 옵션 추가).

**이미 적용한** `enrich` 시 `visual_graph` 재사용은 유지.

### 4) Warm API

- **Method/Path**: `POST` (제안) `/internal/staff/macro-patterns/api/graph-preview/warm/`  
- **권한**: `staff_site_required` + CSRF(세션 쿠키 기반 POST)
- **1단계 페이로드** (구현 단순):

  ```json
  {
    "cache_key": "24자hex...",
    "preview_scene": { }
  }
  ```

  서버: `cache_key`가 `preview_scene`의 해시와 **일치하는지 검증** (불일치 시 400) → `render()` 1회 → DB/디스크 저장.

- **응답** (기존 URL 스킴 유지, `/media/...` 가 아니라 **Django `reverse` 기준**):

  ```json
  {
    "ok": true,
    "cache_key": "...",
    "preview_image_url": "/internal/graph-preview-cache/....png"
  }
  ```

- **GET 캐시 URL에서 생성 시도 금지** (이미 합의).

### 5) (선택·2단계) 페이로드 축소: 서버 측 scene 임시 저장

노드가 매우 많으면 HTML에 `preview_scene` 반복이 커질 수 있음.

- **최종형**: 직렬화 시 서버가 `preview_cache_key → preview_scene` 를 짧은 TTL 캐시(예: Django cache framework / Redis / DB 보조 테이블)에 저장하고, HTML에는 **`preview_cache_key` + `needs_warm` 만** 내려보냄.
- **Warm API 본문**: `{ "cache_key": "..." }` 만 → 서버가 캐시에서 scene 조회 후 `render()`.

초기 구현은 **본문에 `preview_scene` 포함**으로 시작하고, 필요 시 2단계로 분리.

### 6) 프론트엔드

- 매크로 그래프 에디터 마운트 후: `needs_warm === true` 인 노드를 수집.
- **동시성 1** 로 `fetch` 순차 실행 (`X-CSRFToken` 포함).
- 성공 시 해당 노드 `data.preview_image_url` 설정, `needs_warm` 제거 (React Flow `setNodes` 등).
- 기존 [`mergeSilentPreviewFromServer`](frontend/recipe_graph_editor/src/mergeSilentPreviewFromServer.ts) 패턴 재사용 검토.

나중에 안정화 후 동시성 2~3 가능.

### 7) 그 외 호출부

- `macro_pattern_staff_api_recipe_graph_recompute` 등: 정책에 따라 `sync_png=True` 유지(저장 직후 한 번에 채우기) 또는 동일 지연 + 클라이언트 워밍 — **초기에는 기존 동기 유지 권장**(변경 범위 최소).

---

## 구현 순서 (todo 이름 정리)

1. **renderer-cache-only**: cache-only 조회 API (`render_cached_only` 등)
2. **macro-html-no-sync-render**: `serialize_graph_node(..., sync_png=False)` + 매크로 그래프 HTML만 적용
3. **staff-preview-warm-endpoint**: POST warm 뷰 + `urls.py` + cache_key↔scene 검증
4. **client-preview-warm-queue**: 순차 fetch + CSRF + 노드 data 갱신
5. **cache-key-scene-payload-store** (선택·2단계): TTL 캐시로 HTML 페이로드 축소 + warm 시 cache_key만

---

## 테스트

- 단위: `sync_png=False` 일 때 miss 시 생성 호출 없음, hit 시 URL 있음
- 통합: warm POST 한 번 후 `GraphPreviewImage`(또는 파일) 존재 및 응답 URL

---

## 참고

- 이미지 URL은 프로젝트 기존 이름 공간 유지: [`web:graph_preview_cache`](django_apps/web/urls.py).
- 타일은 이미 WebGL 폴백 차단됨; 워밍 전에는 숏코드/씬 폴백만 표시될 수 있음.
