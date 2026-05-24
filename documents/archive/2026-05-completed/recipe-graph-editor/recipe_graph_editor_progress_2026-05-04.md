# Recipe Graph Editor — implementation progress summary (2026-05-04)

This document consolidates **contents implemented to date** in one place snapshot compared to [Recipe Graph Editor Plan](plan_recipe_graph_editor_2026-05-04.md). The plan's product definition, four layers, and roadmap table follow the plan document.

---

## One line summary

`MacroRecipe.graph_document`(JSON) **validates, recomputes, and visualizes**, on a staff-only page **JSON·wire·debounded live preview (dry-run)·save**is wired through. The step meta of **Pattern Lab** and catalog candidates is **derived based on the graph** if there is a `graph_document`, and DB `steps` runs in parallel for editing and timeline.

---

## React Flow editor (Plan [`plan_react_flow_recipe_graph_2026-05-04.md`](plan_react_flow_recipe_graph_2026-05-04.md))

| Item | Summary |
|------|------|
| Bundle·template | `frontend/recipe_graph_editor/` → `django_apps/web/static/web/js/recipe_graph_editor/`; staff graph page RF vs legacy branch with `RECIPE_GRAPH_USE_REACT_FLOW` ([`macro_pattern_graph.html`](../../../../django_apps/web/templates/web/macro_pattern_graph.html)) |
| Default editor | [`config/settings.py`](../../../../config/settings.py): Environment variable **If not set, React Flow** (Legacy is loaded only with `RECIPE_GRAPH_USE_REACT_FLOW=0`, etc.) |
| Domain extension | edge `kind: "delivery"` — intermediate(shape) → target(shape); Verification·Recalculation·RF adapter·Front `recipeConnection.ts` Sort |
| Partial UX | Inspector Properties/Notes(localStorage)/Verification badge, recalculation synchronization, etc. (details in plan §16) |

---

## Phase status (roadmap mapping)

| Phase | Status | Implementation summary |
|--------|------|-----------|
| P0 | Done | `MacroRecipe.graph_document`(`JSONField`), migrate `0003`, [`recipe_graph_constants.py`](../../../../django_apps/shapez_solver/services/recipe_graph_constants.py); The step-by-step roadmap/solver–graph relationship (A/B/C) is [`plan_recipe_graph_editor_phases_2026-05-04.md`](plan_recipe_graph_editor_phases_2026-05-04.md) |
| P1 | Done | In addition to the existing wire·port·dry-run, **palette** (shape·operation drag source)·**grid background** (display on/off, `localStorage`)·**canvas drop creation**([`graph_mount.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_mount.js) `initRecipeCanvasDrop` + [`macro_pattern_staff.js`](../../../../django_apps/web/static/web/js/macro_pattern_staff.js)); Pattern Lab·Catalog reading path is the same |
| P2 | Done | Add **`graph_cost_hint`**([`recipe_graph_cost_hints.py`](../../../../django_apps/shapez_solver/services/recipe_graph_cost_hints.py)) to recalculate response; [`recipe_graph_recompute.py`](../../../../django_apps/shapez_solver/services/recipe_graph_recompute.py) Maintain existing pipeline |
| P3 | Done | `operation_output_edges` warning when **insufficient number of `output` edges** in multi-output operation([`recipe_graph_recipe_validation.py`](../../../../django_apps/shapez_solver/services/recipe_graph_recipe_validation.py)); Maintain existing DAG/severity display |
| P4 | done(mode A+B stub) | Engine, painting, cutting, etc. are the same as before. **Mode A**: Inventory solver does not use `graph_document` as navigation graph — [`macro_action_generator.py`](../../../../django_apps/shapez_solver/services/macro_action_generator.py)·[`pattern_catalog_repository.py`](../../../../django_apps/shapez_solver/services/pattern_catalog_repository.py) Specified in module documentation. **Mode B (Restricted)**: Extract primitive sequences only from linear/single operation node graphs — [`graph_document_primitive_chain.py`](../../../../django_apps/shapez_solver/services/graph_document_primitive_chain.py), recalculate JSON field **`graph_linear_operation_sequence`** |

---

## Key paths (code)

### Data · domain

- Model: [`MacroRecipe.graph_document`](../../../../django_apps/shapez_solver/models.py)
- [`recipe_graph_recompute.py`](../../../../django_apps/shapez_solver/services/recipe_graph_recompute.py) — `validate_graph_document`, `recompute_graph_document`, **`try_pattern_macro_step_rows_from_graph_document`**
- Macro context validation: [`recipe_graph_recipe_validation.py`](../../../../django_apps/shapez_solver/services/recipe_graph_recipe_validation.py) (multi-output `operation_output_edges`, etc.)
- Recalculation cost hints: [`recipe_graph_cost_hints.py`](../../../../django_apps/shapez_solver/services/recipe_graph_cost_hints.py)
- Linear primitive extraction (restrictions): [`graph_document_primitive_chain.py`](../../../../django_apps/shapez_solver/services/graph_document_primitive_chain.py)
- Pattern Lab matching: [`pattern_lab_service.explain_pattern_family_mismatch`](../../../../django_apps/shapez_solver/services/pattern_lab_service.py)
- Pattern Lab·Catalog macro candidate step: [`pattern_catalog_repository.py`](../../../../django_apps/shapez_solver/services/pattern_catalog_repository.py) (`graph_document` derivation takes precedence)
- Inventory operation dispatch: [`operation_semantics.apply_operation`](../../../../django_apps/shapez_solver/services/operation_semantics.py) — rotation·cutter·**cutter_full**·**half_destroyer**·swapper·stacker·painter·**color_mixer**·splitter·pin_pusher, etc.
- Color mix MVP rule: [`color_mix_semantics.mix_color_pair`](../../../../django_apps/shapez_solver/services/color_mix_semantics.py)
- `graph_document` → Solver UI wire: [`macro_recipe_graph_visual.py`](../../../../django_apps/shapez_solver/services/macro_recipe_graph_visual.py)
- Catalog·Serialization: [`macro_recipe_staff_catalog.py`](../../../../django_apps/shapez_solver/services/macro_recipe_staff_catalog.py) — `pattern_lab_steps` field

### HTTP (staff)

- Page: `GET` [`internal/staff/macro-patterns/`](../../../../django_apps/web/views.py) — `api_recipe_graph_recompute_pattern`(`__RECIPE_ID__`) in bootstrap
- Recompute: `POST` `.../recipes/<id>/graph/recompute/` — body `graph_document`, select `commit`; Response `graph_document`, `warnings`, `validation`, `visual_graph`, **`graph_cost_hint`**, **`graph_linear_operation_sequence`** (only for linear single-operation graphs), **`steps_synced`** (try to synchronize DB steps in graph when `commit`)

### Frontend (web)

- [`macro_pattern_staff.js`](../../../../django_apps/web/static/web/js/macro_pattern_staff.js) — Card UI, graph section (JSON **typing·debounce live dry-run**, preserve JSON string during focus·normalize server on blur, avoid request contention with Abort); **Palette drop·Grid snap**·Empty graph mount; **Engine operations only** Add/Edit dropdown(`recipe_graph_engine_operations`); Apply debounce when entering selection node **shape_code·paint·operation·role**·Preview; **Edge append/wire**·Recalculate·Verify mark; **`steps_synced`** instructions after **Recompute & save graph**
- [`macro_pattern_staff_graph.mjs`](../../../../django_apps/web/static/web/js/macro_pattern_staff_graph.mjs) — `mountGraph` wrapper, passing `recipeWireConnect`
- Solver graph common: [`graph_mount.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_mount.js) (select `recipeWireConnect`); [`graph_markup.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_markup.js), [`graph_detail.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_detail.js), [`graph_viewport.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_viewport.js)

---

## Tests (Representative)

- Units: `test_recipe_graph_recompute.py`, `test_operation_engine.py` (cutter_full·half_destroyer, etc.), `test_pattern_catalog_repository.py`, `test_macro_recipe_staff_catalog.py`, `test_macro_recipe_graph_visual.py`, `test_recipe_graph_cost_hints.py`, `test_graph_document_primitive_chain.py`, …
- Integration: `tests/integration/web/test_macro_pattern_staff.py` (catalog·recalculation·`visual_graph`/`validation`·`graph_cost_hint`/`graph_linear_operation_sequence`)

---

## Not implemented · next candidates

1. ~~**DB `MacroRecipeStep` write synchronization**~~ — **`POST .../graph/recompute/` `commit: true`** when deriving steps with [`sync_macro_recipe_steps_from_graph_document`](../../../../django_apps/shapez_solver/services/macro_recipe_staff_catalog.py) Reflection (skip if derivation is not possible). Catalog PATCH `steps` manual editing remains the same.
2. **Unconnected operation compared to catalog** — Among `OperationType`, only **`crystal_generator`** is not yet in `RECIPE_GRAPH_ENGINE_OPERATIONS` · `apply_operation` path (Pin·crystal series are planned to be expanded after domain rules are confirmed). ~~`splitter`~~, ~~`cutter_full`~~, ~~`half_destroyer`~~ done.
3. Linking **Throughput** and graph editing (late part of P4) — The task of tying quantity and target satisfaction to the graph storage and recalculation flow.
4. (Optional) Graph **Context Menu**, etc. P1 UX Remaining — Edge Form/Wire Click Delete implemented.
5. ~~(Optional) When saving a graph, **DB `steps` automatically synchronizes**~~ — **When `graph/recompute` `commit: true`,** overwrites `MacroRecipeStep` if it can be derived from `graph_document` (if derivation is not possible, existing steps are maintained). Reply `steps_synced`.

---

## Change history (this document)

| date | Content |
|------|------|
| 2026-05-04 | First written: Plan-to-implementation snapshot·path·not implemented list |
| 2026-05-04 | **`color_mixer`** Engine·`apply_operation`·`RECIPE_GRAPH_ENGINE_OPERATIONS`·Graph recalculation + [`color_mix_semantics.py`](../../../../django_apps/shapez_solver/services/color_mix_semantics.py) |
| 2026-05-04 | staff `steps_synced` status phrase after **Recompute & save** + server `graph_document`·wire preview synchronization |
| 2026-05-04 | **`cutter_full`**·**`half_destroyer`**: [`OperationEngine`](../../../../django_apps/shapez_solver/services/operation_engine.py)·[`apply_operation`](../../../../django_apps/shapez_solver /services/operation_semantics.py)·[`RECIPE_GRAPH_ENGINE_OPERATIONS`](../../../../django_apps/shapez_solver/services/recipe_graph_constants.py)·Graph Recalculate 1 input branch; Add unit tests |
| 2026-05-04 | staff Graph UI: JSON·Node fields **debounce live preview**, preserve JSON while editing·`fetch` **Abort**, align operation select with **`recipe_graph_engine_operations`**; **build identifier**·initialization failed on page `console.warn` |
| 2026-05-04 | React Flow plan section reflection: **delivery** Edge·Basic editor RF·Progress table (this section)·plan §16 Synchronization |
