# React Flow / XYFlow 기반 Recipe Graph Editor — 아키텍처·마이그레이션 계획 (2026-05-04)

> **상태**: 기획·승인용 초안. 구현 전 사람 승인 게이트를 통과해야 한다.  
> **전제**: 기존 스태프 그래프 UI(WebGL 캔버스 + `solver_timeline` 마운트)를 **폐기할 방향**으로 전환하되, 저장 형식은 가능한 한 **`MacroRecipe.graph_document` 도메인 계약**을 유지한다.

---

## 0. 목표 (요약)

| 항목 | 내용 |
|------|------|
| **제거** | 메인 그래프 편집기에서 WebGL 기반 노드/와이어 렌더링 |
| **도입** | React Flow(XYFlow) + HTML 커스텀 노드 + SVG 엣지 |
| **유지** | 선택 노드 상세·확대 뷰 등 **단일 WebGL/Three** 프리뷰만 허용 |
| **도메인** | `operation → operation` 직접 연결 금지, 연산 출력은 **intermediate(형태)**를 거침 |
| **팔레트** | 문서 §4 지원 연산만 (LOGIC·UTILITY 제외) |
| **UI 형태** | 동봉 **RECIPE GRAPH EDITOR** 목업과 동일한 구역·레이아웃(§2.1). |

---

## 1. 코드베이스와의 정합

### 1.1 기존 도메인 (`graph_document`)

- 노드: `kind`: `"shape"` \| `"operation"`  
- Shape 역할: `role`: `"source"` \| `"intermediate"` \| `"target"` ([`SolverShapeNode`](django_apps/shapez_solver/dto/solver_graph.py))  
- 엣지: `kind`: `"input"` \| `"output"` (shape ↔ operation 방향은 서버·토폴로지 규칙으로 검증)

React Flow 쪽 **UI 전용 타입**(`intermediate`/`output` 노드 타입)은 다음처럼 매핑한다.

| React Flow `nodeType` (제안) | `graph_document` |
|------------------------------|------------------|
| `shape` (소스 재료) | `kind: "shape"`, `role: "source"` |
| `operation` | `kind: "operation"`, `operation` 필드 |
| `intermediate` | `kind: "shape"`, `role: "intermediate"` |
| `output` | `kind: "shape"`, `role: "target"` |

엣지의 `input`/`output`과 React Flow `source`/`target` 핸들은 **adapter**에서 일관 변환한다.

### 1.2 백엔드 API (현행 — 문서 §7 예시 URL 대체)

신규 `/api/recipe-graphs/` 도입 전에는 **기존 스태프 API**를 계약으로 삼는다.

| 용도 | 메서드·경로 (예) |
|------|------------------|
| 페이지·부트스트랩 | `GET` [`web:macro-pattern-graph`](django_apps/web/urls.py) |
| JSON 재계산·저장 | `POST` `…/api/recipes/<pk>/graph/recompute/` ([`macro-pattern-staff-api-recipe-graph-recompute`](django_apps/web/urls.py)) |
| 레시피 상세 | `GET/PATCH` `…/api/recipes/<pk>/` |

페이로드 필드명은 계속 **`graph_document`** 를 사용한다. React Flow 내부 상태는 **직렬화 시 domain 형태로 변환**해 저장한다.

### 1.3 서버 검증과의 관계

- 권위 있는 검증·재계산: [`validate_graph_document`](django_apps/shapez_solver/services/recipe_graph_recompute.py), [`recipe_graph_topology`](django_apps/shapez_solver/services/recipe_graph_topology.py) 등  
- 프론트 `canConnect` / arity는 **UX 차단**이며, 최종 일치는 서버 응답으로 덮어쓴다.

---

## 2. 최종 아키텍처 (After)

```text
Django template (graph 페이지)
└─ React island (root 하나)
   └─ ReactFlowProvider
      ├─ GraphCanvas (XYFlow)
      │   ├─ ShapeNode / OperationNode / IntermediateNode / OutputNode
      │   └─ RecipeEdge (custom)
      ├─ OperationPalette
      ├─ InspectorPanel
      ├─ ValidationPanel
      └─ StatusBar

Selected / Expanded preview (선택 영역만)
└─ 기존 Three.js / shape GLTF 뷰어 — 인스턴스 1~2개로 제한
```

노드 타일: **WebGL 금지** (SVG·CSS·Canvas2D 미니 프리뷰).

### 2.1 시각·레이아웃 — 동봉 **RECIPE GRAPH EDITOR** 목업과 정합

구현 시 **페이지 형태는 동봉 목업 이미지와 동일한 정보 구역·계층**을 목표로 한다. (픽셀 단위 복제가 아니라 **구역·패턴·스타일 언어** 정렬.)

| 구역 | 목업 요구사항 |
|------|----------------|
| **테마** | 다크 모드, 시안·오렌지·퍼플·옐로 포인트, 얇은 테두리·모노스페이스 ID 등 산업/게임 에디터 톤. |
| **헤더** | 좌측: 로고 + 타이틀 **RECIPE GRAPH EDITOR** + 한 줄 부제(예: Create, preview and optimize shape recipes). 우측: **Catalog**, **Edit metadata** (기존 스태프 URL 유지). |
| **좌측 팔레트** | 상단 **Search operations…** 입력. 카테고리 **SHAPE / COLOR / ROTATE / CUT / FLOW** 및 목업과 같은 하위 항목(Base shape, Painter, Color mixer, …). 항목마다 **작은 아이콘 + 라벨**, 카드형 목록. 하단 **Quick access** 영역(예: “드래그해서 빠른 추가” 성격의 드롭 존 — 문구는 목업에 맞춤). |
| **메인 캔버스 (React Flow)** | **상단 오버레이 툴바**: 레시피/와이어 안내 한 줄, **그리드·스냅·줌 %·Fit to screen** 등 뷰 컨트롤. **배경**: 그리드(목업과 동등한 가독성). **노드**: 둥근 사각, 상단 아이콘·타이틀·하단 **노드 ID**(예: `MIX_01`), 좌 **입력**·우 **출력** 포트(작은 사각 핸들). **선택 스테이지 그룹**(목업의 CREATE & COLOR / TRIM & PREPARE / SPLIT & STACK 등 퍼플·오렌지·틸 **트랙 헤더**)은 도메인 필수는 아니며, **1차는 시각적 그룹**(부모 노드·주석 레이어·또는 단순 Y 오프셋)으로 재현하고, **2차**에 레이아웃 엔진과 통합 가능하도록 한다. **엣지**: 부드러운 **베지어 곡선**, 가능하면 **그룹/스테이지와 같은 색상 계열**로 스트로크(커스텀 `RecipeEdge`). **우측 Outputs 구역**: **OUTPUTS** 라벨과 최종 **Output 1 (…)** 형태의 터미널 노드 열 — React Flow에서 오른쪽 고정 패널 또는 동일 뷰포트 내 `output` 노드 군집으로 구현. |
| **하단 인스펙터 (전폭)** | 열 구분: **Selected operation**(선택 없으면 placeholder), **Properties**, **Validation**, **Stats**(예: Nodes / Connections / Outputs 카운트), **Notes**(자유 메모). 목업과 같은 **5블록 가로 스트립**. |
| **풋터 액션** | 좌: **Recompute (dry-run)**, 강조 **Recompute & save graph**. 중앙: **Last recompute** 시간, **Graph is valid** 등 상태. 우: **+ Add output**, **Clear canvas**(위험 동작은 확인 다이얼로그). |

**React Flow 구현 메모**

- `@xyflow/react`의 **Background**, **Controls**, **MiniMap**(목업에 미니맵이 없어도 스코프에 포함 가능 — 목업 우선이면 MiniMap은 옵션).
- 노드·엣지 컴포넌트는 **목업의 카드·포트·곡선선 스타일**에 맞춘 Tailwind 클래스 세트를 공유한다.
- **중간 산출물(intermediate)** 은 목업처럼 연산 블록 사이의 **형태 상태**로 보이도록 하며, §3·§7 규칙과 충돌 없게 표현한다.

---

## 3. 연결 규칙 (UI + 서버 정렬)

허용 (요약):

- `source shape` → `operation`  
- `intermediate shape` → `operation`  
- `operation` → `intermediate shape`  
- `intermediate shape` → `target shape` (문서상 Output 노드)

금지:

- `operation` → `operation`  
- `source` shape → `intermediate` / `target` 등 **delivery 없이** 동종 shape 직접 연결  
- `operation` → `target/output` 직접  
- 기타 서버 토폴로지와 충돌하는 연결

**구현 시**: React Flow `isValidConnection` + 서버 검증 이중.

---

## 4. 지원 Operation 범위

문서에 명시된 목록으로 제한 (소문자 스네이크는 기존 엔진 키와 맞출 것 — 예: `rotate_cw` vs `ROTATE_CW`는 adapter에서 단일 소스로 정규화).

`OPERATION_SPECS` 입출력 개수는 **반드시** [`operation_engine`](django_apps/shapez_solver/services/operation_engine.py) / 기존 메타와 대조해 확정한다.

---

## 5. 파일·빌드 제안 (저장소 기준)

문서 §5의 `assets/js/graph_editor/`는 이 레포지토리에서는 예를 들어 다음처럼 두는 방안을 권장한다.

```text
assets/js/graph_editor/          # 또는 frontend/graph_editor/
  package.json (Vite)
  vite.config.ts                 # outDir → django_apps/web/static/web/js/
  src/main.tsx
  src/GraphEditorApp.tsx
  ...
django_apps/web/templates/web/
  macro_pattern_graph.html       # 번들 script 한 줄 + root div
django_apps/web/static/web/js/
  graph_editor.bundle.js         # 빌드 산출물
```

Tailwind 사용 시: React 소스 경로를 `@source`에 포함해 purge 누락을 방지한다.

---

## 6. 데이터 모델 (TypeScript + 저장 페이로드)

문서 §6·§7의 TS 타입은 유지하되, **저장 JSON**은 도메인 스키마(`nodes[].kind` / `role` / `edges[].kind`)로 내려가게 한다.

제안 함수:

- `reactFlowToDomainGraph(rfNodes, rfEdges): graph_document`
- `domainGraphToReactFlow(doc): { nodes, edges }`
- `legacyMountGraphToReactFlow` — 현재 `macro_recipe_graph_visual` 출력과의 호환은 Phase 1에서 정의

---

## 7. 인터랙션 (문서 §8 정렬)

### 7.1 Operation 드롭 시 자동 Intermediate

- 연산 노드 추가 시 **출력 슬롯 수만큼** intermediate(shape) 노드 자동 생성 + `operation → intermediate` 엣지 자동 연결.  
- 삭제 정책은 문서 §11 권장안을 기본값으로 하되, 구현 전 **제품 확인** 필요.

### 7.2 Operation arity

- 멀티 입력/출력은 handle·`slot`·서버 엣지 `slot` 필드와 통일.

---

## 8. Color Mixer

- `RGB_COLOR_MIX_TABLE` 등은 [`color_mix_semantics`](django_apps/shapez_solver/services/color_mix_semantics.py) 및 기존 규칙과 **동일 소스**를 목표로 한다 (프론트 중복 시 단위 테스트로 동기화).

---

## 9. 단계별 로드맵 (문서 §11과 통합)

| Phase | 초점 | 산출물 |
|------:|------|--------|
| **1** | WebGL 그래프와 상태 분리, 도메인 JSON 어댑터 | `legacyToReactFlow` 초안, WebGL 그래프 엔트리 비활성 플래그 |
| **2** | Vite + React Flow 최소 마운트 | `GraphEditorApp`, 빌드 파이프라인, Django 페이지 연결 |
| **3** | 커스텀 노드 4종 | Shape / Operation / Intermediate / Output |
| **4** | 엣지 검증 | `canConnect`, arity, 중복 입력 방지 |
| **5** | 자동 intermediate 생성 | 드롭·멀티 아웃풋 |
| **6** | 팔레트 | 카탈로그 단일 소스, 검색·DnD |
| **7** | 인스펙터 | 노드별 필드·COLOR_MIXER UI |
| **8** | 백엔드 연동 | 기존 `graph/recompute/` + 검증 결과 반영 |
| **9** | 자동 배치 | 1차 컬럼, 2차 Dagre/ELK |
| **10** | WebGL 단일화 | 타일 프리뷰 비-WebGL, 선택 패널만 Three |

---

## 10. 폐기 범위 (구현 시 삭제·축소 대상)

승인 후 Phase 1~2에서 정리할 후보:

- [`django_apps/web/static/web/js/macro_pattern_graph_editor.js`](django_apps/web/static/web/js/macro_pattern_graph_editor.js) 내 기존 캔버스 마운트 경로  
- [`macro_pattern_staff_graph.mjs`](django_apps/web/static/web/js/macro_pattern_staff_graph.mjs)의 그래프 전체 마운트 (또는 React에서만 호출하도록 축소)  
- 스태프 페이지에 묶인 **그래프용** WebGL/마운트 코드; 단, **동일 모듈을 재사용하는 solver 타임라인**은 건드리지 않는다 ([`architecture.mdc`](.cursor/rules/architecture.mdc) 경계 유지).

---

## 11. 테스트 (문서 §12 반영)

- **단위**: `canConnect`, arity, auto-intermediate, domain ↔ RF 어댑터, 색 테이블  
- **통합**: Django `POST graph/recompute`, 페이지 스모크, 저장 후 재로드  
- **회귀**: 기존 `graph_document` 로드·마이그레이션 스모크

---

## 12. 위험·대응 (문서 §13 요약)

| 위험 | 대응 |
|------|------|
| 도메인 ↔ RF 모델 불일치 | 단일 adapter 모듈 + 서버 검증을 최종 진실로 |
| 빌드·정적 자산 경로 | Vite outDir·Collectstatic·캐시 버스팅(`?v=`) 명시 |
| WebGL 컨텍스트 누수 | 선택 패널 싱글톤 + dispose 테스트 |

---

## 13. 권장 최초 5 작업 (문서 §14과 동일)

1. 도메인 `graph_document` 스키마와 RF 모델 매핑표 확정  
2. 레거시 export + `domainGraphToReactFlow` 스켈레톤  
3. Django 페이지에 빈 React Flow 캔버스 마운트  
4. 커스텀 노드 4종 스타일만  
5. `isValidConnection` + 상태바 메시지  

---

## 14. 승인 게이트

- 본 문서 또는 수정본에 **사람 승인** 후 브랜치 구현 진입.  
- `[documents/` 작성 언어]: 본문 한국어, 식별자·경로·API는 원문 유지.

---

## 15. 이전 계획과의 관계

- [`plan_recipe_graph_workbench_2026-05-04.md`](documents/plan_recipe_graph_workbench_2026-05-04.md)는 **WebGL 워크벤치 레이아웃** 중심이었다. 본 문서가 승인되면 해당 계획의 UI 부분은 **React Flow 전제로 대체**한다. 도메인·토폴로지·팔레트 범위 등 공통 요구는 계승한다.

---

## 16. 최종 Todo list

구현 시 진행 상황을 이 목록으로 추적한다. (순서는 Phase·의존 관계를 우선한다.)

### 공통 · 준비

- [ ] 본 문서 **사람 승인** 기록(승인일·요약)
- [x] `graph_document` ↔ React Flow **매핑표** 문서화(PR 또는 본 문서 부록)
- [x] Vite(또는 선택 빌더) + React + `@xyflow/react` **프로젝트 스캐폴딩**
- [x] 빌드 산출물 → `django_apps/web/static/web/js/` 및 템플릿 **번들 로드·캐시 버스트**
- [x] Tailwind: React 소스 경로 `@source` 등록·purge 검증

### Phase 1 — 도메인 상태 분리 · 어댑터

- [x] 스태프 그래프 관련 **WebGL/마운트 진입점** 파일 목록 확정
- [x] **직렬화 가능한 그래프 스냅샷** 추출(도메인 JSON 기준)
- [x] `domain_graph_to_react_flow` / `react_flow_to_domain_graph` **스켈레톤 + 단위 테스트 초안**
- [x] 레거시 시각화 출력과의 **호환 범위** 정의(`macro_recipe_graph_visual` 등)
- [x] 기존 WebGL 그래프 **비활성 플래그**(또는 feature flag) 추가

### Phase 2 — React Flow 최소 장착 · §2.1 레이아웃 뼈대

- [x] `macro_pattern_graph.html`(또는 전용 템플릿)에 **React root + 번들** 마운트
- [x] `GraphEditorApp` / `ReactFlowProvider` **기본 구성**
- [x] §2.1에 맞춘 **페이지 격자**: 헤더 · 좌 팔레트 영역 · 중앙 캔버스 · 하단 5열 인스펙터 · 풋터(플레이스홀더 허용)
- [x] Background · pan/zoom · selection 동작
- [x] (선택) Controls · MiniMap

### Phase 3 — 커스텀 노드 4종

- [x] `ShapeNode` — 소스 재료·미니 프리뷰(WebGL 없음)
- [x] `OperationNode` — 아이콘·라벨·ID·입출력 핸들
- [x] `IntermediateNode` — produced-by·미니 프리뷰
- [x] `OutputNode` — target·우측 OUTPUTS 구역 배치 정책 반영
- [x] 선택·경고·오류 **배지 스타일**(목업 톤)

### Phase 4 — 엣지 · 연결 검증

- [x] 커스텀 `RecipeEdge`(베지어·`data.domainKind`별 스트로크) — `frontend/recipe_graph_editor/src/recipeFlowEdges.tsx`
- [x] `isValidConnection` — §3 규칙 + `recipeConnection.ts`·`wouldConnectAfterRemovals`
- [x] Operation **입력 arity**·**중복 입력** 차단 — `operationArity.ts` 등
- [x] 잘못된 연결 시 메시지 — `#macro-graph-status`(스로틀) + 하단 **Inspector Validation** 열(`GraphEditorApp.tsx`)
- [x] §3 **intermediate → output(target)** 수동 배선 — 엣지 종류 ``delivery`` (`recipe_graph_topology.py`·`recipe_graph_recompute.py`·RF 어댑터·`recipeConnection.ts`)

### Phase 5 — 자동 Intermediate

- [x] 팔레트에서 연산 **드롭 시** 연산 노드 + 출력 수만큼 intermediate + 엣지 자동 생성 — 캔버스 `onDrop` + `ensureOperationOutputArtifacts`(클릭 추가는 기존대로 격자 배치·연결 후 스테이징)
- [x] 멀티 아웃풋 연산 **슬롯별 intermediate** 및 위치 오프셋 — `operationOutputStaging.ts` 등
- [x] 노드/연산 삭제 시 **intermediate·엣지 정리 정책** 구현 및 확인 — `recipeGraphNodeCleanup.ts` + `GraphEditorApp` `onNodesChange`(연산 삭제 시 출력 스테이징 intermediate 연쇄 제거)

### Phase 6 — Operation 팔레트

- [x] `operationCatalog`(SHAPE / ROTATE / CUT / FLOW / COLOR) — **엔진 목록과 단일 정합**(부트스트랩 + 비활성 처리)
- [x] 검색·카테고리·아이콘+라벨 카드
- [x] 드래그 앤 드롭·키보드 접근 가능한 추가 버튼 — 연산·빈 소스 **DnD**(`RecipeFlowBoard`); 팔레트 항목은 `<button>`으로 **Enter/Space** 클릭 동작 유지
- [x] LOGIC·UTILITY **미노출** 확인(카탈로그 필터 정책 명시) — `operationPaletteGroups.ts` 주석: 비표시 계열은 카탈로그 미포함 또는 `engineOperationIds` 비포함 시 비활성

### Phase 7 — 인스펙터 패널

- [x] 선택 노드별 **Properties** 전용 필드 편집 — 단일 선택 시 하단 Properties 열에 인라인 폼(`InspectorNodeProperties`); 다중/미선택 시 기존 요약 문구
- [x] **Validation** 패널 — 서버 `validationOk`/풋터 힌트 + **연결 거부 메시지** 요약
- [x] **Stats** — 노드·엣지·출력 수
- [x] **Notes** — 브라우저 `localStorage`(`shapez-recipe-graph-notes:<recipeId>`), 400ms 디바운스 저장; 서버 미동기화

### Phase 8 — 백엔드 연동

- [x] `POST …/graph/recompute/` **dry-run** 연결 및 UI 반영(버튼 + 연결 후 silent dry-run)
- [x] **저장(commit)** 플로우 및 에러 처리
- [x] 재계산 결과로 **intermediate shape_code·검증 상태** 갱신(응답 `react_flow` 동기화)
- [x] 백엔드 검증 실패 시 노드/엣지 **validationState** 반영(RF 노드 데이터에 미전파 시 부분 완료) — 노드 `data.validationSeverity`(issues의 `node_ids` 매핑); 엣지 표시는 미구현

### Phase 9 — 자동 배치

- [x] **Auto arrange** 버튼 — 1차 좌→우 컬럼 레이아웃 — `recipeGraphAutoLayout.ts` + 캔버스 툴바 **Auto arrange**
- [x] 수동 드래그 후 **position 저장** 검증 — 어댑터 소수 좌표 round-trip 단위 테스트(`test_react_flow_round_trip_preserves_fractional_positions`)
- [ ] (2차) Dagre / ELK 도입 여부 결정 및 통합

### Phase 10 — WebGL 프리뷰 단일화

- [x] 그래프 타일 **WebGL 제거** — React Flow 편집기 번들(`frontend/recipe_graph_editor`)은 노드 미니 프리뷰가 이미지/CSS 기반(Three/WebGL 미사용); 레거시 스태프 WebGL 경로는 Phase「폐기·정리」항목
- [ ] **선택 노드** 패널에만 Three.js / GLTF **단일 렌더러** 재사용
- [ ] 확대 모달은 **mount 시 생성·close 시 dispose** 패턴 점검

### 폐기 · 정리

- [x] 스태프 전용 **구 그래프 WebGL 마운트** — 기본은 RF(`config/settings.py`: 미설정 시 `RECIPE_GRAPH_USE_REACT_FLOW=True`); 레거시는 `RECIPE_GRAPH_USE_REACT_FLOW=0` 시에만 [`macro_pattern_graph.html`](django_apps/web/templates/web/macro_pattern_graph.html) 분기로 로드
- [ ] Solver 타임라인 등 **공유 모듈 회귀** 테스트 통과 확인

### 테스트 · QA

- [ ] 단위: 어댑터·`canConnect`·arity·auto-intermediate·색 테이블
- [ ] 통합: 페이지 로드·recompute·저장·재로드·§2.1 스모크(팔레트·캔버스·인스펙터 가시성)
- [ ] 회귀: 기존 `graph_document` 로드·마이그레이션

### 문서 · 마무리

- [x] [`recipe_graph_editor_progress`](documents/recipe_graph_editor_progress_2026-05-04.md) — React Flow 전환·delivery 엣지 등 후속 구간 반영(2026-05-04 변경 이력)
- [x] `structure.md` — **`frontend/recipe_graph_editor/`** 소스 및 **`static/web/js/recipe_graph_editor/`** 산출 경로 한 줄

---

## 17. 부록 A — `graph_document` ↔ React Flow 스냅샷 매핑 (v1)

> 구현 권위: `django_apps/shapez_solver/services/recipe_graph_react_flow_adapter.py` 의 `domain_graph_to_react_flow` / `react_flow_to_domain_graph`. 스냅샷 최상위 `version` 필드는 `REACT_FLOW_GRAPH_PAYLOAD_VERSION`(현재 1)이다. 그래프 저장 계약(`schema_version`, `nodes`, `edges`)은 `graph_document`가 유지된다.

### 17.1 노드

| `graph_document` | React Flow `type` | `data` (요약) |
|------------------|-------------------|---------------|
| `kind: "shape"`, `role: "source"` | `shape` | `shape_code`, `quantity`, `role` |
| `kind: "shape"`, `role: "intermediate"` | `intermediate` | 동일 |
| `kind: "shape"`, `role: "target"` | `output` | 동일 |
| `kind: "operation"` | `operation` | `operation`, (선택) `paint_color` |

공통: `id`, `position: { x, y }` ← 도메인의 `x`, `y`(float).

### 17.2 엣지

| `graph_document` | React Flow |
|------------------|------------|
| `from`, `to`, `kind` (`input` \| `output` \| `delivery`) | `source`=`from`, `target`=`to`, `data.domainKind`=`kind` (`delivery`: intermediate→target 납품) |
| (선택) `slot` | `data.slot` |

React Flow `id`는 스냅샷에서 `e-{from}-{to}-{kind}` 규칙으로 부여한다.

### 17.3 부트스트랩 · 재계산 API

- 스태프 그래프 페이지(`macro_pattern_graph`)의 `macro-graph-bootstrap` JSON에 `react_flow_initial` 키가 포함된다. 값은 검증된 `graph_document`의 변환 결과이거나, 문서가 없거나 검증 실패 시 `null`이다.
- `POST …/api/recipes/<pk>/graph/recompute/` 요청 본문은 **`graph_document`와 `react_flow` 중 하나만** 보낸다. `react_flow`를 보낼 때는 클라이언트가 역변환(TypeScript)하지 않고, 서버가 `react_flow_to_domain_graph` → `validate_graph_document` → `recompute_graph_document` 순으로 처리한다(권위: 파이썬 어댑터만).
- 응답 JSON에는 항상 갱신된 **`react_flow`** 스냅샷(`domain_graph_to_react_flow(doc)`)이 포함되며, 편집기는 이 값으로 캔버스 상태를 동기화한다.

### 17.4 레거시 WebGL·그래프 마운트 진입점 (정리 대상)

| 경로 | 역할 |
|------|------|
| `django_apps/web/static/web/js/macro_pattern_graph_editor.js` | 스태프 매크로 그래프 레거시 편집기(카드·캔버스·Three importmap 연동) |
| `django_apps/web/static/web/js/macro_pattern_staff_graph.mjs` | 스태프 전용 그래프 시각화 모듈 |
| `django_apps/web/static/web/js/solver_timeline.js` + `solver_timeline/graph_mount.js` | 솔버 타임라인에서 `mountGraph` 로 그래프 마운트 |

React Flow 전환 후에는 위 중 **그래프 편집** 경로를 플래그로 차단·제거하고, 타임라인 등 **읽기 전용** 공유 모듈은 회귀 테스트로 보호한다.

### 17.5 `macro_recipe_graph_visual` 호환

`serialize_macro_recipe_visual` 이 만드는 `visual_graph`는 카탈로그·API 응답용 **읽기 전용** 요약으로 유지한다. 편집기 상태의 권위는 `graph_document` 및 본 부록의 React Flow 스냅샷이며, 동일 레시피에 대해 시각 노드 수·ID가 1:1일 필요는 없다(편집기는 `recipe_graph_react_flow_adapter` 스키마를 따른다).
