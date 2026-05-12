# 리팩터링 우선순위 계획 (2026-05-06)

## 목표

현재 코드 기준으로 리팩터링이 필요한 구간을 **위험도와 효과가 큰 순서**로 정리한다. 본 문서에는 **진행 상황**(P0 완료 등)을 함께 둔다. 실제 리팩터는 항목별로 작게 나누어 진행한다.

## 판단 기준

1. 아키텍처 규칙 위반 여부
2. 성능 병목 또는 중복 계산 여부
3. 변경 빈도가 높은 UI·API 경계의 결합도
4. 테스트 격리 난이도
5. 파일 크기와 책임 혼합 정도

## 진행 상황 (갱신: 2026-05-06 — P7 반영)

| 우선순위 | 상태 | 비고 |
|----------|------|------|
| P0 | **완료** | 역방향 의존 제거 및 solver HTTP 경계 정리(아래 P0 표 참고). |
| P1 | **완료** | 이중 `validate_graph_document`(deepcopy) 제거: `serialize_macro_recipe_visual`→`_solver_graph_from_validated_document`; 스태프 재계산 API는 기존대로 `recompute_validated_graph_document`; `try_pattern_macro_step_rows_*`에 shape 파싱 캐시. 상세는 표 본문. |
| P2 | **2차 완료** | 훅 분리(1차)에 더해 `GraphEditorOperationPalette`·`GraphEditorOutputsColumn`·`GraphEditorCanvasPanel`·`GraphEditorRecipeFlowBoard`·`GraphEditorInspectorStrip`·`GraphEditorFooterActions`·`graphEditorNodeData`·`graphEditorPlacement`·`graphEditorFlowViewport`로 UI·헬퍼 분리(2026-05-06). |
| P3 | **1차 완료** | `recipeConnection.ts` 배럴 + `recipeConnectionCarriers` 등 모듈 분리(2026-05-06). |
| P4 | **완료** | 그래프 레이아웃 TS 모듈 분리 + 정적 번들 재생성·배너·`documents/ai/manuals/frontend.md` 절차 명시(2026-05-06). |
| P5 | **완료** | `views/` 패키지: `macro_staff.py`(스태프 매크로 페이지·API)·`public_pages.py`(공개 페이지·데모·preview cache), `views/__init__.py`에서 기존 `django_apps.web.views` 면 유지(2026-05-06). |
| P6 | **완료** | `macro_recipe_serialization.py`·`macro_recipe_payloads.py` 분리, `macro_recipe_staff_catalog.py`는 CRUD·파생 필드·재노출(2026-05-06). |
| P7 | **완료** | `nodeEditModalScalars`·`nodeEditModalLabels`·`nodeEditModalFormState`·`nodeEditModalApply`·`NodeEditModalPanels`; `NodeEditModal.tsx`는 셸·상태·조립만(2026-05-06). |

**부가 작업 (본 표 범위 밖):** 레포 전역 `mypy .` 통과를 위해 `django_apps/web` 일부 모듈·단위 테스트 타입 보강, `pyproject.toml`의 미사용 mypy override 항목 정리.

---

## P0. `shapez_solver` → `web` 역방향 의존 제거

**상태: 완료 (2026-05-06).**

| 항목 | 내용 |
|------|------|
| 영향 파일 | `django_apps/shapez_solver/view_graph_serialization.py`, `django_apps/shapez_solver/services/macro_recipe_graph_visual.py`, `django_apps/web/services/graph_preview.py` |
| 근거 | `.cursor/rules/architecture.mdc`는 `shapez_solver -> django_apps.web` import를 금지한다. 리팩터 전에는 일부 직렬화 경로가 `django_apps.web.services.graph_preview`를 직접 import했다. |
| 위험 | 솔버 레이어가 웹 PNG 렌더러와 정적 URL 생성에 묶여 테스트·재사용·레이어 경계가 약해진다. |
| 권장 작업 | 순수 graph DTO/preview scene 생성은 `shapez_solver`에 남기고, PNG 렌더러 주입·`static()` URL 조립은 `web` 레이어 어댑터로 이동한다. |
| 구현 요약 | `django_apps/shapez_solver/ports/graph_preview.py`에 `GraphPreviewRenderer` Protocol·테스트용 `NoopGraphPreviewRenderer`. 직렬화 API는 `preview_renderer` 인자로 주입. `solve_shape`는 `django_apps/web/views_solver_api.py`, URL은 `django_apps/web/urls_shapez_solver_api.py`(`app_name="shapez_solver"`), 루트는 `config/urls.py`에서 해당 모듈 include. 기존 `django_apps/shapez_solver/urls.py`·`views.py` 제거. |
| 검증 | `rg "django_apps\\.web" django_apps/shapez_solver -g "*.py"` (import 없음·문자열 주석만 허용 시 정리), `python -m pytest tests/unit/shapez_solver`, 통합: `tests/integration/api/test_solver_api.py`, `tests/integration/web/test_macro_pattern_staff.py` 등 |

## P1. `recipe_graph_recompute` 검증·재계산 경로 비용 축소

**상태: 완료 (2026-05-06).** (스태프 API 이중 검증·재계산 경로는 착수 전부터 `recompute_validated_graph_document`로 정리되어 있었음.)

| 항목 | 내용 |
|------|------|
| 영향 파일 | `django_apps/shapez_solver/services/recipe_graph_recompute.py`, `django_apps/web/views.py`, `django_apps/shapez_solver/services/operation_semantics.py` |
| 근거 | `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md`에서 `validate_graph_document`의 `deepcopy`, 스태프 API 이중 검증, 반복 `parse_shape`, `OperationEngine()` 반복 생성이 후속 우선순위로 남아 있다. |
| 위험 | 큰 `graph_document`에서 재계산 API 응답 시간이 증가하고, UI silent dry-run 빈도가 높아질수록 체감 지연이 커진다. |
| 권장 작업 | 이미 검증된 dict를 받는 내부 전용 recompute 경로를 명확히 하고, 요청 단위 shape 파싱 캐시와 `OperationEngine` 재사용 가능성을 검증한다. |
| 구현 요약 | `recompute_validated_graph_document`·`apply_operation(..., shape_parse_cache=...)`·모듈 단일 `_OPERATION_ENGINE`은 기존 유지. 추가로 `macro_recipe_graph_visual.serialize_macro_recipe_visual`에서 `document_to_solver_graph`가 재검증하던 경로를 `_solver_graph_from_validated_document`로 치환해 직렬화당 `deepcopy` 1회 감소. `try_pattern_macro_step_rows_from_graph_document`의 유체 슬롯 라벨에 동일 호출 범위 `shape_parse_cache` 전달. |
| 검증 | `python -m pytest tests/unit/shapez_solver/test_recipe_graph_recompute.py tests/unit/shapez_solver/test_macro_recipe_graph_visual.py tests/integration/web/test_macro_pattern_staff.py`, 대형 체인 문서 `cProfile` 재측정 |

## P2. `GraphEditorApp.tsx` 책임 분리

**상태: 2차 완료 (2026-05-06).** 1차 훅 분리에 더해 팔레트·캔버스(React Flow 보드)·inspector strip·footer·노드 데이터/배치 헬퍼를 별도 모듈로 분리했다.

| 항목 | 내용 |
|------|------|
| 영향 파일 | `frontend/recipe_graph_editor/src/GraphEditorApp.tsx`, `GraphEditorOperationPalette.tsx`, `GraphEditorOutputsColumn.tsx`, `GraphEditorCanvasPanel.tsx`, `GraphEditorRecipeFlowBoard.tsx`, `GraphEditorInspectorStrip.tsx`, `GraphEditorFooterActions.tsx`, `graphEditorNodeData.ts`, `graphEditorPlacement.ts`, `graphEditorFlowViewport.ts` |
| 근거 | 파일이 약 1,356줄이며 팔레트, 캔버스, inspector, footer, 노트 저장, 연결 검증, recompute 호출, silent preview 병합을 모두 가진다. |
| 위험 | 작은 UI 변경도 앱 전체 상태와 충돌하기 쉽고, React Flow 이벤트·서버 동기화·로컬 저장소 로직을 독립 테스트하기 어렵다. |
| 권장 작업 | 우선 `useRecipeGraphRecompute`, `useRecipeGraphSelection`, `useRecipeGraphNotes` 같은 hook 또는 상태 모듈로 추출하고, 이미 분리된 `NodeEditModal`, `InspectorNodeProperties` 패턴을 따른다. |
| 검증 | `cd frontend/recipe_graph_editor && npm run test && npm run build` |

## P3. `recipeConnection.ts` 규칙 모듈 분해

**상태: 1차 완료 (2026-05-06).** 공개 API는 `recipeConnection.ts`에서 재export 유지. 구현은 `recipeConnectionUtils.ts`, `recipeConnectionCarriers.ts`, `recipeConnectionInputSort.ts`, `recipeConnectionPredicates.ts`, `recipeConnectionPainter.ts`, `recipeConnectionEvaluate.ts`, `recipeConnectionRemovals.ts`.

| 항목 | 내용 |
|------|------|
| 영향 파일 | `frontend/recipe_graph_editor/src/recipeConnection.ts`, `django_apps/shapez_solver/services/recipe_graph_input_carrier.py`, `tests/fixtures/recipe_connection_rule_scenarios.json` |
| 근거 | 약 645줄 안에 carrier 판정, painter 보정, 중복 링크 검사, edge 제거 정책, connection 변환이 섞여 있다. Python 쪽 carrier 규칙과 정렬 fixture로 맞추는 구조라 변경 시 양쪽 동기화 비용이 크다. |
| 위험 | 연결 규칙 변경 시 UI 허용 규칙과 서버 재계산 규칙이 어긋날 수 있다. |
| 권장 작업 | carrier 기대값, painter handle 정규화, 제거 정책, edge 변환을 별도 모듈로 나눈다. 공통 fixture 기반 테스트는 유지하고 케이스를 추가한다. |
| 검증 | `cd frontend/recipe_graph_editor && npm run test`, `python -m pytest tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py` |

## P4. 그래프 레이아웃 엔진과 빌드 산출물 경계 정리

**상태: 완료 (2026-05-06).**

| 항목 | 내용 |
|------|------|
| 영향 파일 | `frontend/graph_layout/src/graphLayoutEngine.ts`(진입·공개 API만), `graphLayoutMath.ts`, `graphLayoutDebug.ts`, `graphLayoutInput.ts`, `graphLayoutPorts.ts`, `graphLayoutMergeOrdering.ts`, `graphLayoutAdjacency.ts`, `graphLayoutBarycenter.ts`, `graphLayoutColumnPlan.ts`, `graphLayoutVertical.ts`, `graphLayoutHorizontal.ts`, `graphLayoutBounds.ts`, `graphLayoutGrouped.ts`, `graphLayoutPinned.ts`, `django_apps/web/static/web/js/solver_graph_layout.js`, `django_apps/web/static/web/js/editor_graph_layout.js`, 루트 `package.json`(`build:graph-layout` 배너), `documents/ai/manuals/frontend.md` |
| 근거 | `graphLayoutEngine.ts`가 약 924줄이며 solver layout, editor layout, pinned layout, overlap 해소를 한 파일에서 처리한다. `django_apps/web/static/web/js/*_graph_layout.js`는 같은 엔진에서 빌드된 추적 산출물이다. |
| 위험 | 소스와 정적 산출물이 어긋나면 브라우저 동작과 테스트 기준이 달라진다. layout 정책 변경 시 solver/editor 회귀 범위도 커진다. |
| 권장 작업 | solver/editor/pinned 레이아웃 단계를 내부 모듈로 나누고, 빌드 산출물 갱신 명령을 문서화한다. 산출물은 수동 수정 금지 원칙을 주석 또는 문서에 명시한다. |
| 구현 요약 | 단계별 `graphLayout*.ts`로 분리: 입력·깊이(`graphLayoutInput`), 포트·머지 정렬(`graphLayoutPorts`, `graphLayoutMergeOrdering`), 인접·바센터(`graphLayoutAdjacency`, `graphLayoutBarycenter`), 열 계획(`graphLayoutColumnPlan`), 수직·수평·바운드(`graphLayoutVertical`, `graphLayoutHorizontal`, `graphLayoutBounds`), 그룹·핀(`graphLayoutGrouped`, `graphLayoutPinned`). `graphLayoutEngine.ts`는 공개 export + `computeGraphLayout` 오케스트레이션만 유지. esbuild `--banner:js`로 정적 JS 상단에 생성 파일·재빌드 명령 안내. 매뉴얼에 `npm run build:graph-layout` 및 수동 편집 금지 명시. |
| 검증 | `npm run build:graph-layout`, `npm --prefix frontend/recipe_graph_editor run build`, `npm --prefix frontend/recipe_graph_editor test`, `python -m pytest tests/unit/web/test_editor_graph_layout.py` |

## P5. `django_apps/web/views.py`의 스태프 매크로 API 분리

**상태: 완료 (2026-05-06).**

| 항목 | 내용 |
|------|------|
| 영향 파일 | `django_apps/web/views/__init__.py`, `django_apps/web/views/macro_staff.py`, `django_apps/web/views/public_pages.py`(기존 단일 `views.py` 제거), `django_apps/web/urls.py`는 `from django_apps.web import views` 유지 |
| 근거 | 약 600줄 안에 staff macro 관리, graph recompute API, sprite manifest, gallery/home/support/demo 페이지가 함께 있다. |
| 위험 | 웹 페이지 변경과 스태프 API 변경의 충돌 가능성이 높고, 뷰 테스트의 실패 원인 추적이 어려워진다. |
| 권장 작업 | URL 이름과 view signature는 유지하면서 `web/views/macro_staff.py`, `web/views/public_pages.py` 또는 동등한 모듈로 내부 이동한다. |
| 구현 요약 | 스태프 전용: `staff_site_required`, 매크로 목록·신규·편집·그래프 페이지, graph-preview warm, sprite manifest, catalog/recipes/recompute/recipe detail JSON API. 공개: 홈·갤러리·solver·pattern lab·support·graph preview cache·demo. |
| 검증 | `python -m pytest tests/integration/web/test_macro_pattern_staff.py tests/integration/web/test_web_smoke.py` |

## P6. `macro_recipe_staff_catalog.py` 저장·직렬화 책임 분리

**상태: 완료 (2026-05-06).**

| 항목 | 내용 |
|------|------|
| 영향 파일 | `django_apps/shapez_solver/services/macro_recipe_staff_catalog.py`, `macro_recipe_serialization.py`(신규), `macro_recipe_payloads.py`(신규) |
| 근거 | 카탈로그 snapshot, recipe 직렬화, payload 파싱, create/update/delete, graph-derived step sync가 한 서비스에 들어 있다. |
| 위험 | DB 저장 로직과 API payload 검증이 함께 움직여 회귀 범위가 커진다. |
| 권장 작업 | `macro_recipe_serialization.py`, `macro_recipe_payloads.py`, `macro_recipe_staff_catalog.py`처럼 경계를 나누되 공개 함수명은 유지하는 compatibility wrapper를 둔다. |
| 구현 요약 | 직렬화·카탈로그 스냅샷(`MACRO_RECIPE_DETAIL_PREFETCHES`, `serialize_recipe`, `build_catalog_snapshot`, `allowed_strategy_codes`, `operation_choices` 등)은 `macro_recipe_serialization.py`. 페이로드 검증·스텝 파싱·`update_recipe` 필드 적용은 `macro_recipe_payloads.py`. 초안/생성/갱신/삭제·그래프 파생 필드·그래프→스텝 동기화는 `macro_recipe_staff_catalog.py`에 유지하고, 기존 `from …macro_recipe_staff_catalog import …` 공개 면은 동일. |
| 검증 | `python -m pytest tests/unit/shapez_solver/test_macro_recipe_staff_catalog.py tests/integration/web/test_macro_pattern_staff.py`(25 passed), `ruff check`(해당 3모듈), `mypy`(해당 3모듈) |

## P7. `NodeEditModal.tsx` 폼 상태와 표시 컴포넌트 분리

**상태: 완료 (2026-05-06).**

| 항목 | 내용 |
|------|------|
| 영향 파일 | `NodeEditModal.tsx`(얇게 유지), `NodeEditModalPanels.tsx`(신규), `nodeEditModalScalars.ts`, `nodeEditModalLabels.ts`, `nodeEditModalFormState.ts`, `nodeEditModalApply.ts` |
| 근거 | 약 614줄이며 shape/source/operation별 폼 상태, validation, 표시 컴포넌트가 한 파일에 있다. |
| 위험 | graph editor의 노드 데이터 스키마 변경 시 모달 렌더링과 저장 로직이 같이 흔들린다. |
| 권장 작업 | node type별 form section과 `nodeData -> formState -> patch` 변환 함수를 분리한다. |
| 구현 요약 | 스칼라·미리보기 필드는 `nodeEditModalScalars.ts`. 제목·role·shape 힌트 문자열은 `nodeEditModalLabels.ts`. `formFieldsFromNodeData`는 `nodeEditModalFormState.ts`. Apply 패치는 `buildNodeEditApplyPayload`(`nodeEditModalApply.ts`). 타입별 폼 UI는 `OperationFields`·`IntermediatePanel`·`ShapeOutputPanel`(`NodeEditModalPanels.tsx`). 공개 타입 `NodeEditAnchor`·`NodeEditModal` export 경로 유지. |
| 검증 | `npm run test`·`npm run build`(frontend/recipe_graph_editor), vitest 14 passed |

## 실행 순서 제안

1. ~~P0를 먼저 처리해 레이어 규칙을 회복한다.~~ **P0 완료.**
2. ~~P1: 검증·직렬화 이중 비용~~ **P1 완료** (`serialize_macro_recipe_visual` 단일 검증·패턴 매크로 파싱 캐시; 재계산 경로는 기존 구현).
3. ~~P2: `GraphEditorApp` 훅 분리 + 컴포넌트·헬퍼 파일 분리~~ **P2 2차 완료** (훅 + 팔레트·캔버스·inspector·footer·`graphEditorNodeData` 등).
4. P3~P4는 프론트 그래프 편집기 변경이 잦은 구간이므로 한 항목씩 PR 또는 커밋 단위로 나눈다.
5. P5~P7은 공개 URL·함수 signature를 유지하는 이동형 리팩터로 처리한다.

**P2 후속 vs P3 우선순위 (2026-05-06 확정):** P3(`recipeConnection.ts` 모듈 분해)를 먼저 한다. 규칙·carrier·Python fixture 정렬 경계가 더 무겁고, 실행 순서 제안도 P2 1차 다음이 P3이다. P2의 팔레트·캔버스·inspector 파일 분리는 동일 P2의 가독성 후속으로 P3 이후에 진행한다.

## 보류·주의

- P0에서 `macro_recipe_graph_visual` 경로는 preview 렌더러 주입으로 정리됨. 로컬에 미커밋 수정이 있으면 병합·리베이스 시 여전히 `git diff`로 충돌 여부를 확인할 것.
- 정책: `django_apps/web/static/web/js/solver_graph_layout.js`, `editor_graph_layout.js`는 **esbuild 추적 산출물**이며 소스는 `frontend/graph_layout/src/` 이다. 갱신은 `npm run build:graph-layout`(루트).
- TODO: DB 스키마 변경, 마이그레이션, 공개 URL 이름 변경은 이 문서 범위에서 제외한다.

## 검증 메모

- **P0·P1·P2(2차)·P3(1차)·P4·P5·P6·P7 구현 완료.** 이후 리팩터 착수 시 각 표의 검증 명령을 항목별로 실행한다.
- 품질 게이트 예시: `python -m pytest` → `ruff check .` → `mypy .` → `black .`(프로젝트 규칙은 `AGENTS.md` 참고).
