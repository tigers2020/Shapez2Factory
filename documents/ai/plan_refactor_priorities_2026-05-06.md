# Refactoring priority plan (2026-05-06)

## Goal

Order refactoring targets by **risk and impact** based on current code. This document also tracks **progress** (P0 done, etc.). Split actual refactors into small per-item chunks.

## Criteria

1. Architecture rule violations
2. Performance bottlenecks or duplicate computation
3. Coupling at high-change UI · API boundaries
4. Test isolation difficulty
5. File size and mixed responsibilities

## Progress (updated: 2026-05-06 — P7 reflected)

| Priority | Status | Notes |
|----------|--------|-------|
| P0 | **Done** | Reverse dependency removal and solver HTTP boundary cleanup (see P0 table). |
| P1 | **Done** | Removed double `validate_graph_document` (deepcopy): `serialize_macro_recipe_visual`→`_solver_graph_from_validated_document`; staff recompute API still `recompute_validated_graph_document`; shape parse cache on `try_pattern_macro_step_rows_*`. Details in table body. |
| P2 | **Phase 2 done** | Beyond hook split (phase 1): UI · helpers split into `GraphEditorOperationPalette` · `GraphEditorOutputsColumn` · `GraphEditorCanvasPanel` · `GraphEditorRecipeFlowBoard` · `GraphEditorInspectorStrip` · `GraphEditorFooterActions` · `graphEditorNodeData` · `graphEditorPlacement` · `graphEditorFlowViewport` (2026-05-06). |
| P3 | **Phase 1 done** | `recipeConnection.ts` barrel + module split `recipeConnectionCarriers`, etc. (2026-05-06). |
| P4 | **Done** | Graph layout TS module split + static bundle regen · banner · procedure in `documents/ai/manuals/frontend.md` (2026-05-06). |
| P5 | **Done** | `views/` package: `macro_staff.py` (staff macro pages · API) · `public_pages.py` (public pages · demo · preview cache), existing `django_apps.web.views` face via `views/__init__.py` (2026-05-06). |
| P6 | **Done** | Split `macro_recipe_serialization.py` · `macro_recipe_payloads.py`; `macro_recipe_staff_catalog.py` keeps CRUD · derived fields · re-exports (2026-05-06). |
| P7 | **Done** | `nodeEditModalScalars` · `nodeEditModalLabels` · `nodeEditModalFormState` · `nodeEditModalApply` · `NodeEditModalPanels`; `NodeEditModal.tsx` shell · state · assembly only (2026-05-06). |

**Extra work (outside this table):** repo-wide `mypy .` pass via type fixes in some `django_apps/web` modules · unit tests, cleanup unused mypy overrides in `pyproject.toml`.

---

## P0. Remove `shapez_solver` → `web` reverse dependency

**Status: Done (2026-05-06).**

| Item | Content |
|------|---------|
| Affected files | `django_apps/shapez_solver/view_graph_serialization.py`, `django_apps/shapez_solver/services/macro_recipe_graph_visual.py`, `django_apps/web/services/graph_preview.py` |
| Rationale | `.cursor/rules/architecture.mdc` forbids `shapez_solver -> django_apps.web` imports. Before refactor some serialization paths imported `django_apps.web.services.graph_preview` directly. |
| Risk | Solver layer tied to web PNG renderer and static URL assembly weakens tests · reuse · layer boundary. |
| Recommended work | Keep pure graph DTO/preview scene generation in `shapez_solver`; move PNG renderer injection · `static()` URL assembly to `web` layer adapter. |
| Implementation summary | `GraphPreviewRenderer` Protocol · test `NoopGraphPreviewRenderer` in `django_apps/shapez_solver/ports/graph_preview.py`. Serialization APIs take `preview_renderer` arg. `solve_shape` in `django_apps/web/views_solver_api.py`, URLs in `django_apps/web/urls_shapez_solver_api.py` (`app_name="shapez_solver"`), root includes that module in `config/urls.py`. Removed old `django_apps/shapez_solver/urls.py` · `views.py`. |
| Verification | `rg "django_apps\\.web" django_apps/shapez_solver -g "*.py"` (no imports · string comments only if cleaned), `python -m pytest tests/unit/shapez_solver`, integration: `tests/integration/api/test_solver_api.py`, `tests/integration/web/test_macro_pattern_staff.py`, etc. |

## P1. Reduce cost of `recipe_graph_recompute` validation · recompute path

**Status: Done (2026-05-06).** (Staff API double validation · recompute path was already `recompute_validated_graph_document` before start.)

| Item | Content |
|------|---------|
| Affected files | `django_apps/shapez_solver/services/recipe_graph_recompute.py`, `django_apps/web/views.py`, `django_apps/shapez_solver/services/operation_semantics.py` |
| Rationale | `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` lists `validate_graph_document` `deepcopy`, staff API double validation, repeated `parse_shape`, repeated `OperationEngine()` creation as follow-up priorities. |
| Risk | Large `graph_document` increases recompute API latency; worse as UI silent dry-run frequency rises. |
| Recommended work | Clarify internal recompute path for already-validated dict; verify per-request shape parse cache and `OperationEngine` reuse. |
| Implementation summary | Keep existing `recompute_validated_graph_document` · `apply_operation(..., shape_parse_cache=...)` · module singleton `_OPERATION_ENGINE`. Additionally replace `document_to_solver_graph` re-validation in `macro_recipe_graph_visual.serialize_macro_recipe_visual` with `_solver_graph_from_validated_document` — one fewer `deepcopy` per serialization. Pass same-scope `shape_parse_cache` to fluid slot labels in `try_pattern_macro_step_rows_from_graph_document`. |
| Verification | `python -m pytest tests/unit/shapez_solver/test_recipe_graph_recompute.py tests/unit/shapez_solver/test_macro_recipe_graph_visual.py tests/integration/web/test_macro_pattern_staff.py`, `cProfile` remeasure on large chain doc |

## P2. Split responsibilities of `GraphEditorApp.tsx`

**Status: Phase 2 done (2026-05-06).** Beyond phase 1 hook split: palette · canvas (React Flow board) · inspector strip · footer · node data/placement helpers in separate modules.

| Item | Content |
|------|---------|
| Affected files | `frontend/recipe_graph_editor/src/GraphEditorApp.tsx`, `GraphEditorOperationPalette.tsx`, `GraphEditorOutputsColumn.tsx`, `GraphEditorCanvasPanel.tsx`, `GraphEditorRecipeFlowBoard.tsx`, `GraphEditorInspectorStrip.tsx`, `GraphEditorFooterActions.tsx`, `graphEditorNodeData.ts`, `graphEditorPlacement.ts`, `graphEditorFlowViewport.ts` |
| Rationale | ~1,356 lines holding palette, canvas, inspector, footer, note save, connection validation, recompute calls, silent preview merge. |
| Risk | Small UI changes collide with whole app state; hard to test React Flow events · server sync · local storage independently. |
| Recommended work | Extract hooks/state modules like `useRecipeGraphRecompute`, `useRecipeGraphSelection`, `useRecipeGraphNotes` first; follow split pattern of `NodeEditModal`, `InspectorNodeProperties`. |
| Verification | `cd frontend/recipe_graph_editor && npm run test && npm run build` |

## P3. Decompose `recipeConnection.ts` rule modules

**Status: Phase 1 done (2026-05-06).** Public API re-exported from `recipeConnection.ts`. Impl in `recipeConnectionUtils.ts`, `recipeConnectionCarriers.ts`, `recipeConnectionInputSort.ts`, `recipeConnectionPredicates.ts`, `recipeConnectionPainter.ts`, `recipeConnectionEvaluate.ts`, `recipeConnectionRemovals.ts`.

| Item | Content |
|------|---------|
| Affected files | `frontend/recipe_graph_editor/src/recipeConnection.ts`, `django_apps/shapez_solver/services/recipe_graph_input_carrier.py`, `tests/fixtures/recipe_connection_rule_scenarios.json` |
| Rationale | ~645 lines mixing carrier judgment, painter correction, duplicate link check, edge removal policy, connection conversion. Python carrier rules and alignment fixtures mean high sync cost on change. |
| Risk | UI allow rules and server recompute rules can diverge on connection rule changes. |
| Recommended work | Split carrier expectations, painter handle normalization, removal policy, edge conversion. Keep fixture-based tests and add cases. |
| Verification | `cd frontend/recipe_graph_editor && npm run test`, `python -m pytest tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py` |

## P4. Graph layout engine vs build artifact boundary

**Status: Done (2026-05-06).**

| Item | Content |
|------|---------|
| Affected files | `frontend/graph_layout/src/graphLayoutEngine.ts` (entry · public API only), `graphLayoutMath.ts`, `graphLayoutDebug.ts`, `graphLayoutInput.ts`, `graphLayoutPorts.ts`, `graphLayoutMergeOrdering.ts`, `graphLayoutAdjacency.ts`, `graphLayoutBarycenter.ts`, `graphLayoutColumnPlan.ts`, `graphLayoutVertical.ts`, `graphLayoutHorizontal.ts`, `graphLayoutBounds.ts`, `graphLayoutGrouped.ts`, `graphLayoutPinned.ts`, `django_apps/web/static/web/js/solver_graph_layout.js`, `django_apps/web/static/web/js/editor_graph_layout.js`, root `package.json` (`build:graph-layout` banner), `documents/ai/manuals/frontend.md` |
| Rationale | `graphLayoutEngine.ts` ~924 lines handling solver layout, editor layout, pinned layout, overlap resolution in one file. `django_apps/web/static/web/js/*_graph_layout.js` are traced build outputs of same engine. |
| Risk | Source vs static artifact drift changes browser behavior vs test baseline. Layout policy changes widen solver/editor regression scope. |
| Recommended work | Split solver/editor/pinned layout stages into internal modules; document build artifact refresh command. No manual edit of artifacts — document in comments or docs. |
| Implementation summary | Split by stage into `graphLayout*.ts`: input · depth (`graphLayoutInput`), ports · merge ordering (`graphLayoutPorts`, `graphLayoutMergeOrdering`), adjacency · barycenter (`graphLayoutAdjacency`, `graphLayoutBarycenter`), column plan (`graphLayoutColumnPlan`), vertical · horizontal · bounds (`graphLayoutVertical`, `graphLayoutHorizontal`, `graphLayoutBounds`), grouped · pinned (`graphLayoutGrouped`, `graphLayoutPinned`). `graphLayoutEngine.ts` keeps public export + `computeGraphLayout` orchestration only. esbuild `--banner:js` on static JS top with generated file · rebuild command. Manual documents `npm run build:graph-layout` and no manual edit. |
| Verification | `npm run build:graph-layout`, `npm --prefix frontend/recipe_graph_editor run build`, `npm --prefix frontend/recipe_graph_editor test`, `python -m pytest tests/unit/web/test_editor_graph_layout.py` |

## P5. Split staff macro API from `django_apps/web/views.py`

**Status: Done (2026-05-06).**

| Item | Content |
|------|---------|
| Affected files | `django_apps/web/views/__init__.py`, `django_apps/web/views/macro_staff.py`, `django_apps/web/views/public_pages.py` (removed monolithic `views.py`), `django_apps/web/urls.py` still `from django_apps.web import views` |
| Rationale | ~600 lines mixing staff macro management, graph recompute API, sprite manifest, gallery/home/support/demo pages. |
| Risk | Web page changes collide with staff API changes; hard to trace view test failures. |
| Recommended work | Internal move to `web/views/macro_staff.py`, `web/views/public_pages.py` or equivalent while keeping URL names and view signatures. |
| Implementation summary | Staff-only: `staff_site_required`, macro list · create · edit · graph pages, graph-preview warm, sprite manifest, catalog/recipes/recompute/recipe detail JSON API. Public: home · gallery · solver · pattern lab · support · graph preview cache · demo. |
| Verification | `python -m pytest tests/integration/web/test_macro_pattern_staff.py tests/integration/web/test_web_smoke.py` |

## P6. Split storage · serialization responsibilities of `macro_recipe_staff_catalog.py`

**Status: Done (2026-05-06).**

| Item | Content |
|------|---------|
| Affected files | `django_apps/shapez_solver/services/macro_recipe_staff_catalog.py`, `macro_recipe_serialization.py` (new), `macro_recipe_payloads.py` (new) |
| Rationale | Catalog snapshot, recipe serialization, payload parsing, create/update/delete, graph-derived step sync in one service. |
| Risk | DB persistence and API payload validation move together → large regression scope. |
| Recommended work | Split boundaries like `macro_recipe_serialization.py`, `macro_recipe_payloads.py`, `macro_recipe_staff_catalog.py` but keep public function names via compatibility wrappers. |
| Implementation summary | Serialization · catalog snapshot (`MACRO_RECIPE_DETAIL_PREFETCHES`, `serialize_recipe`, `build_catalog_snapshot`, `allowed_strategy_codes`, `operation_choices`, etc.) in `macro_recipe_serialization.py`. Payload validation · step parsing · `update_recipe` field apply in `macro_recipe_payloads.py`. Draft/create/update/delete · graph-derived fields · graph→step sync stay in `macro_recipe_staff_catalog.py`; existing `from …macro_recipe_staff_catalog import …` public face unchanged. |
| Verification | `python -m pytest tests/unit/shapez_solver/test_macro_recipe_staff_catalog.py tests/integration/web/test_macro_pattern_staff.py` (25 passed), `ruff check` (those 3 modules), `mypy` (those 3 modules) |

## P7. Split form state and display components of `NodeEditModal.tsx`

**Status: Done (2026-05-06).**

| Item | Content |
|------|---------|
| Affected files | `NodeEditModal.tsx` (kept thin), `NodeEditModalPanels.tsx` (new), `nodeEditModalScalars.ts`, `nodeEditModalLabels.ts`, `nodeEditModalFormState.ts`, `nodeEditModalApply.ts` |
| Rationale | ~614 lines mixing shape/source/operation form state, validation, display components. |
| Risk | Graph editor node data schema changes shake modal rendering and save logic together. |
| Recommended work | Split node-type form sections and `nodeData -> formState -> patch` transforms. |
| Implementation summary | Scalars · preview fields in `nodeEditModalScalars.ts`. Title · role · shape hint strings in `nodeEditModalLabels.ts`. `formFieldsFromNodeData` in `nodeEditModalFormState.ts`. Apply patch in `buildNodeEditApplyPayload` (`nodeEditModalApply.ts`). Type-specific form UI in `OperationFields` · `IntermediatePanel` · `ShapeOutputPanel` (`NodeEditModalPanels.tsx`). Keep public types `NodeEditAnchor` · `NodeEditModal` export paths. |
| Verification | `npm run test` · `npm run build` (frontend/recipe_graph_editor), vitest 14 passed |

## Suggested execution order

1. ~~Handle P0 first to restore layer rules.~~ **P0 done.**
2. ~~P1: double validation · serialization cost~~ **P1 done** (`serialize_macro_recipe_visual` single validation · pattern macro parse cache; recompute path pre-existing).
3. ~~P2: `GraphEditorApp` hook split + component · helper file split~~ **P2 phase 2 done** (hooks + palette · canvas · inspector · footer · `graphEditorNodeData`, etc.).
4. P3~P4: high-change frontend graph editor areas — one PR or commit per item.
5. P5~P7: move-style refactors keeping public URL · function signatures.

**P2 follow-up vs P3 priority (confirmed 2026-05-06):** Do P3 (`recipeConnection.ts` module split) first. Rule · carrier · Python fixture alignment boundary is heavier; execution order also had P3 after P2 phase 1. P2 palette · canvas · inspector file split is readability follow-up within P2 after P3.

## Deferred · cautions

- P0: `macro_recipe_graph_visual` path cleaned via preview renderer injection. If local uncommitted changes exist, still check conflicts via `git diff` on merge/rebase.
- Policy: `django_apps/web/static/web/js/solver_graph_layout.js`, `editor_graph_layout.js` are **esbuild traced outputs**; source is `frontend/graph_layout/src/`. Refresh via `npm run build:graph-layout` (repo root).
- TODO: DB schema changes, migrations, public URL renames excluded from this document scope.

## Verification notes

- **P0 · P1 · P2 (phase 2) · P3 (phase 1) · P4 · P5 · P6 · P7 implementation done.** Run each table's verification commands per item on future refactors.
- Example quality gate: `python -m pytest` → `ruff check .` → `mypy .` → `black .` (see project rules in `AGENTS.md`).
