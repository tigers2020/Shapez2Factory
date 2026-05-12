# Recipe Graph Editor — 구현 진행 요약 (2026-05-04)

본 문서는 [Recipe Graph Editor 플랜](plan_recipe_graph_editor_2026-05-04.md) 대비 **현재까지 구현된 내용**을 한곳에 정리한 스냅샷이다. 플랜의 제품 정의·4계층·로드맵 표는 플랜 문서를 따른다.

---

## 한 줄 요약

`MacroRecipe.graph_document`(JSON)을 **검증·재계산·시각화**하고, 스태프 전용 페이지에서 **JSON·와이어·디바운스된 라이브 미리보기(dry-run)·저장**까지 연결되어 있다. **Pattern Lab**과 카탈로그 후보의 스텝 메타는 `graph_document`가 있으면 **그래프 기준으로 파생**되고, DB `steps`는 편집·타임라인용으로 병행된다.

---

## React Flow 편집기 (플랜 [`plan_react_flow_recipe_graph_2026-05-04.md`](plan_react_flow_recipe_graph_2026-05-04.md))

| 항목 | 요약 |
|------|------|
| 번들·템플릿 | `frontend/recipe_graph_editor/` → `django_apps/web/static/web/js/recipe_graph_editor/`; 스태프 그래프 페이지는 `RECIPE_GRAPH_USE_REACT_FLOW`로 RF vs 레거시 분기([`macro_pattern_graph.html`](../../../../django_apps/web/templates/web/macro_pattern_graph.html)) |
| 기본 편집기 | [`config/settings.py`](../../../../config/settings.py): 환경변수 **미설정 시 React Flow**(레거시는 `RECIPE_GRAPH_USE_REACT_FLOW=0` 등으로만 로드) |
| 도메인 확장 | 엣지 `kind: "delivery"` — intermediate(shape) → target(shape); 검증·재계산·RF 어댑터·프론트 `recipeConnection.ts` 정렬 |
| UX 일부 | 인스펙터 Properties/Notes(localStorage)/검증 배지·재계산 동기화 등(세부는 플랜 §16) |

---

## 단계별 상태 (로드맵 대응)

| Phase | 상태 | 구현 요약 |
|--------|------|-----------|
| P0 | 완료 | `MacroRecipe.graph_document`(`JSONField`), 마이그레이션 `0003`, [`recipe_graph_constants.py`](../../../../django_apps/shapez_solver/services/recipe_graph_constants.py); 단계별 로드맵·솔버–그래프 관계(A/B/C)는 [`plan_recipe_graph_editor_phases_2026-05-04.md`](plan_recipe_graph_editor_phases_2026-05-04.md) |
| P1 | 완료 | 기존 와이어·포트·dry-run에 더해 **팔레트**(shape·연산 드래그 소스)·**그리드 배경**(표시 on/off, `localStorage`)·**캔버스 드롭 생성**([`graph_mount.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_mount.js) `initRecipeCanvasDrop` + [`macro_pattern_staff.js`](../../../../django_apps/web/static/web/js/macro_pattern_staff.js)); Pattern Lab·카탈로그 읽기 경로 동일 |
| P2 | 완료 | 재계산 응답에 **`graph_cost_hint`**([`recipe_graph_cost_hints.py`](../../../../django_apps/shapez_solver/services/recipe_graph_cost_hints.py)) 추가; [`recipe_graph_recompute.py`](../../../../django_apps/shapez_solver/services/recipe_graph_recompute.py) 기존 파이프라인 유지 |
| P3 | 완료 | 멀티 출력 연산에서 **`output` 엣지 수 부족** 시 `operation_output_edges` 경고([`recipe_graph_recipe_validation.py`](../../../../django_apps/shapez_solver/services/recipe_graph_recipe_validation.py)); 기존 DAG·심각도 표시 유지 |
| P4 | 완료(모드 A+B 스텁) | 엔진·색칠·절단 등 기존과 동일. **모드 A**: 인벤토리 솔버는 `graph_document`를 탐색 그래프로 쓰지 않음 — [`macro_action_generator.py`](../../../../django_apps/shapez_solver/services/macro_action_generator.py)·[`pattern_catalog_repository.py`](../../../../django_apps/shapez_solver/services/pattern_catalog_repository.py) 모듈 문서로 명시. **모드 B(제한)**: 선형·단일 연산 노드 그래프에서만 primitive 시퀀스 추출 — [`graph_document_primitive_chain.py`](../../../../django_apps/shapez_solver/services/graph_document_primitive_chain.py), 재계산 JSON 필드 **`graph_linear_operation_sequence`** |

---

## 주요 경로 (코드)

### 데이터·도메인

- 모델: [`MacroRecipe.graph_document`](../../../../django_apps/shapez_solver/models.py)
- [`recipe_graph_recompute.py`](../../../../django_apps/shapez_solver/services/recipe_graph_recompute.py) — `validate_graph_document`, `recompute_graph_document`, **`try_pattern_macro_step_rows_from_graph_document`**
- 매크로 컨텍스트 검증: [`recipe_graph_recipe_validation.py`](../../../../django_apps/shapez_solver/services/recipe_graph_recipe_validation.py)(멀티 출력 `operation_output_edges` 등)
- 재계산 비용 힌트: [`recipe_graph_cost_hints.py`](../../../../django_apps/shapez_solver/services/recipe_graph_cost_hints.py)
- 선형 primitive 추출(제한): [`graph_document_primitive_chain.py`](../../../../django_apps/shapez_solver/services/graph_document_primitive_chain.py)
- Pattern Lab 정합: [`pattern_lab_service.explain_pattern_family_mismatch`](../../../../django_apps/shapez_solver/services/pattern_lab_service.py)
- Pattern Lab·카탈로그 매크로 후보 스텝: [`pattern_catalog_repository.py`](../../../../django_apps/shapez_solver/services/pattern_catalog_repository.py)(`graph_document` 파생 우선)
- 인벤토리 연산 디스패치: [`operation_semantics.apply_operation`](../../../../django_apps/shapez_solver/services/operation_semantics.py) — 회전·cutter·**cutter_full**·**half_destroyer**·swapper·stacker·painter·**color_mixer**·splitter·pin_pusher 등
- 색 혼합 MVP 규칙: [`color_mix_semantics.mix_color_pair`](../../../../django_apps/shapez_solver/services/color_mix_semantics.py)
- `graph_document` → 솔버 UI wire: [`macro_recipe_graph_visual.py`](../../../../django_apps/shapez_solver/services/macro_recipe_graph_visual.py)
- 카탈로그·직렬화: [`macro_recipe_staff_catalog.py`](../../../../django_apps/shapez_solver/services/macro_recipe_staff_catalog.py) — `pattern_lab_steps` 필드

### HTTP (스태프)

- 페이지: `GET` [`internal/staff/macro-patterns/`](../../../../django_apps/web/views.py) — 부트스트랩에 `api_recipe_graph_recompute_pattern`(`__RECIPE_ID__`)
- 재계산: `POST` `.../recipes/<id>/graph/recompute/` — 본문 `graph_document`, 선택 `commit`; 응답 `graph_document`, `warnings`, `validation`, `visual_graph`, **`graph_cost_hint`**, **`graph_linear_operation_sequence`**(선형 단일 연산 그래프일 때만), **`steps_synced`** (`commit` 시 그래프에서 DB 스텝 동기 시도)

### 프론트 (웹)

- [`macro_pattern_staff.js`](../../../../django_apps/web/static/web/js/macro_pattern_staff.js) — 카드 UI, 그래프 섹션(JSON **타이핑·디바운스 라이브 dry-run**, 포커스 중에는 JSON 문자열 보존·blur 시 서버 정규화, Abort로 요청 경합 방지); **팔레트 드롭·그리드 스냅**·빈 그래프 마운트; **엔진 연산만** Add/Edit 드롭다운(`recipe_graph_engine_operations`); 선택 노드 **shape_code·paint·연산·role** 입력 시 디바운스 적용·미리보기; **엣지 append/와이어**·재계산·검증 표시; **Recompute & save graph** 후 **`steps_synced`** 안내
- [`macro_pattern_staff_graph.mjs`](../../../../django_apps/web/static/web/js/macro_pattern_staff_graph.mjs) — `mountGraph` 래퍼, `recipeWireConnect` 전달
- 솔버 그래프 공용: [`graph_mount.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_mount.js)(선택 `recipeWireConnect`), [`graph_markup.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_markup.js), [`graph_detail.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_detail.js), [`graph_viewport.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_viewport.js)

---

## 테스트 (대표)

- 단위: `test_recipe_graph_recompute.py`, `test_operation_engine.py`(cutter_full·half_destroyer 등), `test_pattern_catalog_repository.py`, `test_macro_recipe_staff_catalog.py`, `test_macro_recipe_graph_visual.py`, `test_recipe_graph_cost_hints.py`, `test_graph_document_primitive_chain.py`, …
- 통합: `tests/integration/web/test_macro_pattern_staff.py`(카탈로그·재계산·`visual_graph`/`validation`·`graph_cost_hint`/`graph_linear_operation_sequence`)

---

## 미구현·다음 후보

1. ~~**DB `MacroRecipeStep` 쓰기 동기**~~ — **`POST .../graph/recompute/` `commit: true`** 시 [`sync_macro_recipe_steps_from_graph_document`](../../../../django_apps/shapez_solver/services/macro_recipe_staff_catalog.py)로 파생 스텝 반영(파생 불가 시 스킵). 카탈로그 PATCH `steps` 수동 편집은 그대로.
2. **카탈로그 대비 미연결 연산** — `OperationType` 중 **`crystal_generator`**만 아직 `RECIPE_GRAPH_ENGINE_OPERATIONS`·`apply_operation` 경로에 없음(기획상 핀·크리스탈 계열은 확장 시 도메인 규칙 확정 후). ~~`splitter`~~, ~~`cutter_full`~~, ~~`half_destroyer`~~ 완료.
3. **Throughput**과 그래프 편집 연동(P4 후반) — 수량·목표 만족을 그래프 저장·재계산 흐름에 묶는 작업.
4. (선택) 그래프 **컨텍스트 메뉴** 등 P1 UX 잔여 — 엣지 폼/와이어 클릭 삭제는 구현됨.
5. ~~(선택) 그래프 저장 시 **DB `steps` 자동 동기**~~ — **`graph/recompute` `commit: true` 시** `graph_document`에서 파생 가능하면 `MacroRecipeStep` 덮어쓰기(파생 불가면 기존 스텝 유지). 응답 `steps_synced`.

---

## 변경 이력 (본 문서)

| 날짜 | 내용 |
|------|------|
| 2026-05-04 | 최초 작성: 플랜 대비 구현 스냅샷·경로·미구현 목록 |
| 2026-05-04 | **`color_mixer`** 엔진·`apply_operation`·`RECIPE_GRAPH_ENGINE_OPERATIONS`·그래프 재계산 + [`color_mix_semantics.py`](../../../../django_apps/shapez_solver/services/color_mix_semantics.py) |
| 2026-05-04 | 스태프 **Recompute & save** 후 `steps_synced` 상태 문구 + 서버 `graph_document`·와이어 미리보기 동기 |
| 2026-05-04 | **`cutter_full`**·**`half_destroyer`**: [`OperationEngine`](../../../../django_apps/shapez_solver/services/operation_engine.py)·[`apply_operation`](../../../../django_apps/shapez_solver/services/operation_semantics.py)·[`RECIPE_GRAPH_ENGINE_OPERATIONS`](../../../../django_apps/shapez_solver/services/recipe_graph_constants.py)·그래프 재계산 1입력 분기; 단위 테스트 추가 |
| 2026-05-04 | 스태프 그래프 UI: JSON·노드 필드 **디바운스 라이브 미리보기**, 편집 중 JSON 보존·`fetch` **Abort**, 연산 셀렉트를 **`recipe_graph_engine_operations`와 정렬**; 페이지에 **빌드 식별자**·초기화 실패 `console.warn` |
| 2026-05-04 | React Flow 플랜 구간 반영: **delivery** 엣지·기본 편집기 RF·진행 표(본 섹션)·플랜 §16 동기화 |
