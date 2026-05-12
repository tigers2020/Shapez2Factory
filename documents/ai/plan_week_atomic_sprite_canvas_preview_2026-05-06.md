# 주간 개발 계획: 원자 스프라이트 아틀라스 + Canvas2D 합성 프리뷰

**역할·관점**: Rendering Pipeline Architect  
**상태**: 이번 주(2026-05-06 주차) 개발 방향 확정용 초안 — 구현 전 리뷰·승인 권장  
**관련 선행 플랜**: [plan_deferred_png_warm_queue.md](plan_deferred_png_warm_queue.md) (지연 warm·`sync_png=False`)

---

## 한 줄 결론

**완성 shape PNG를 노드마다 서버에서 굽는 패턴을 버리고, 유한한 원자 파츠(메시×색×사분면 등)만 오프라인·일괄 생성한 뒤, 런타임에는 `preview_scene.cells[]`를 그대로 Canvas2D `drawImage` 명령 버퍼로 쓰는 구조가 장기적으로 맞다.**

---

## 현재 파이프라인과 비용

```text
target shape
  → preview_scene 생성
  → Playwright
  → Chromium / Three.js
  → 오프스크린 렌더
  → PNG 저장
```

이 경로를 **노드마다** 수행하므로 비용은 대략:

```text
O(노드 수 × full_scene_render_cost)
```

Render·Gunicorn·프록시의 **요청 시간 한도**에 걸리기 쉽다.

---

## 목표 아키텍처

### 패러다임 전환

```text
full scene server rendering
  → client-side deterministic composition
```

shapez2Factory의 `preview_scene.cells[]`는 이미 `mesh_key`, `color_code`, `quadrant_index`, `position` 등 **원시 서술자**를 갖고 있어, 사실상 **렌더 커맨드 버퍼**에 가깝다. 여기에 맞춰:

```text
preview_scene → Canvas2D renderer (클라이언트)
```

만 추가하면 된다.

### 도메인 가정 (유한 스프라이트)

기본 메시 예시:

- `default_rect`, `default_circle`, `default_star`, `default_diamond`, `default_pin`, crystal 등 ([`shape_gltf/constants.js`](../../django_apps/web/static/web/js/shape_gltf/constants.js) 의 `MODEL_FILES` 와 정합)

색상 팔레트는 게임 규칙상 **유한** → 조합 전체를 **finite sprite atlas** 로 축소 가능.

---

## 서버·자산 측면

### 1차 목표

- **원자 PNG 약 160장 분량**(예: 형태×색×`quadrant` q0–q3)을 **빌드·관리 스크립트로 선생성**
- 저장 위치 후보:
  - **단일 `atlas.png` + `manifest.json`** (UV: `[x,y,w,h]` 권장 — HTTP 요청 수·디코드 비용 감소)
  - 또는 DB Blob + GET (운영·버전 일관성 우선 시; 아틀라스도 DB 한 행으로 가능)

### 파츠 생성 스크립트 (이번 주 산출물)

- 기존 [`scripts/render_graph_preview.mjs`](../../scripts/render_graph_preview.mjs) 또는 동일 Three·카메라 기준의 **오프라인 전용** 스크립트로:
  - 각 원자 조합·사분면만 렌더 → 타일 크기 고정 PNG 또는 아틀라스 팩킹
- 산출물: `atlas.png`, `manifest.json`(키 규칙 예: `rect_red_q0`), 선택 시 메타(`version`, 렌더 프리셋)

---

## 프론트엔드

- **타일 프리뷰**: WebGL N컨텍스트 없이 **Canvas2D** 만 사용

```text
for each cell in preview_scene.cells:
    키 = f(mesh_key, color 변형, quadrant, …)
    drawImage(atlas, sx,sy,sw,sh, dx,dy,dw,dh)
```

- 노드 수가 늘어도 비용은 대략 **그리기 호출 수**에 비례 → UI 수준에 가깝다.

---

## 단계별 전략 (강력 추천 순서)

| 단계 | 내용 |
|------|------|
| **1** | **warm 큐·기존 API 유지** — 미등록 키·유체·크리스탈 예외·품질 폴백용 안전장치 |
| **2** | **타일 프리뷰만** Canvas2D 스프라이트 합성으로 교체 ([`recipeShapePreview.tsx`](../../frontend/recipe_graph_editor/src/recipeShapePreview.tsx) 타일 분기) |
| **3** | **Playwright PNG** 는 모달·내보내기·고품질 전용으로 축소 |

---

## 성능 비교 (개념)

**현재 (노드당 합성 PNG)**:

```text
Node.js → Playwright → Chromium → Three/WebGL → PNG 인코드 → 저장
```

**변경 후 (타일)**:

```text
drawImage() × 셀 수
```

---

## 리스크·주의

- `transform_key`, 유체 캐리어, 크리스탈 쉐이딩 등으로 **원자 집합이 160을 넘을 수 있음** → 열거·테스트로 확정; 미커버는 warm/모달 유지
- 스태프 타일을 Playwright와 **픽셀 일치**시킬지, **근사 프리뷰**로 정책 고정할지 결정 필요
- 아틀라스 버전 갱신 시 **캐시 무효화**(파일명 hash 또는 `manifest.version`)

---

## 이번 주 작업 후보 (체크리스트)

1. **원자 키 스펙 문서화**: `mesh_key` × 색 × 사분면 × (필요 시 `transform`) → 문자열 키 규칙
2. **`scripts/` 오프라인 빌드 스크립트**: 아틀라스+매니페스트 출력 (로컬/CI에서 실행)
3. **정적 서빙 또는 DB 적재** 방식 결정 및 Django `collectstatic`/마이그레이션 중 택일
4. **프로토타입**: 단일 `preview_scene`로 Canvas2D 합성 컴포넌트 + 타일 경로 연결
5. **회귀**: 대표 셀 조합 golden 스냅샷 또는 시각 스모크

---

## 참고 코드 경로

- 씬 직렬화: [`django_apps/shapez_solver/view_graph_serialization.py`](../../django_apps/shapez_solver/view_graph_serialization.py)
- 타일/모달 프리뷰 UI: [`frontend/recipe_graph_editor/src/recipeShapePreview.tsx`](../../frontend/recipe_graph_editor/src/recipeShapePreview.tsx)
- 기존 서버 PNG 렌더: [`django_apps/web/services/graph_preview.py`](../../django_apps/web/services/graph_preview.py)

---

## 최종 판단 (아키텍트 요약)

이 접근은 단순 타임아웃 회피용 workaround가 아니라, **렌더링 책임을 서버 전체 씬 렌더에서 클라이언트 결정론적 합성으로 옮기는** 구조 변경이다. 프로젝트에 이미 있는 `preview_scene.cells[]` 모델과 잘 맞는다.
