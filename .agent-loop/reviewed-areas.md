# Project Review Memory

Tracks areas reviewed by periodic project review automation to prevent duplicate work.

Read this file before each run to avoid duplicate work.

## 2026-06-09 21:21

Reviewed area:
- path/module/feature: `src/shapez2_factory/interfaces/cli/` (`asteroid_solve.py`, exit-code contract, related tests/docs)

Skipped:
- Django subprocess runner (`django_apps/asteroid_lab/services/solver_subprocess_runner.py`) — deferred to future run
- CI workflow (`.github/workflows/ci.yml`) — out of CLI scope this run
- Issues labeled `reviewing` — none present

Findings:
- SHA-7: [docs] CLI exit-code table in artifact design spec contradicts asteroid_solve implementation
- SHA-8: [test] Missing regression coverage for asteroid_solve ExitCode.STACK_UNAVAILABLE (20)

Notes:
- Spec §6 lists exit codes 0/1/2/3/4/5; implementation uses `ExitCode` 0/10/20 per `asteroid_solve.py` and CLI-first checklist.
- `test_cli_exit_codes.py` covers OK and VALIDATION_FAILED only; no `STACK_UNAVAILABLE` assertion in `tests/`.

## 2026-06-09 21:33 (prior run — memory file missing)

Reviewed area:
- `django_apps/asteroid_lab/services/artifact_ingest.py`
- `tests/unit/asteroid_lab/test_artifact_ingest.py`

Skipped:
- memory file did not exist yet; entries reconstructed from Linear backlog

Findings:
- SHA-9: [bug] artifact ingest indexes COMPLETED SolverRun with empty solver_summary when paths/hash validation decoupled
- SHA-10: [test] Missing regression for artifact ingest when manifest.error_code is set

Notes:
- Ingest fail-closed gaps and missing error_code regression coverage.

## 2026-06-09 22:00

Reviewed area:
- `django_apps/asteroid_lab/services/solver_run_reconcile.py`
- `django_apps/web/views/public_pages.py` (async status poll)
- `tests/unit/asteroid_lab/test_reconcile_solver_run.py`

Skipped:
- `artifact_ingest.py` / CLI exit codes (reviewed 2026-06-09; SHA-7–SHA-10)
- issues labeled `reviewing`: none open

Findings:
- SHA-11: [test] Missing regression for reconcile RECONCILE_FAILURE_LOG_FATAL (subprocess log fatal marker)
- SHA-12: [bug] reconcile_solver_run leaks ArtifactIngestError to async status poll (HTTP 500)

Notes:
- `_attempt_artifact_ingest` only catches `ArtifactManifestReadError`; hashed-but-invalid `solver_summary.json` reproduces uncaught `ArtifactIngestError` via pytest.
- `_log_has_fatal_marker` path works manually but has zero repo test coverage.

## 2026-06-09 23:30

Reviewed area:
- path/module/feature: `src/shapez2_factory/application/asteroid_lab/run_stack.py` + L6 commit-validate stub + solver_summary validation contract (`layer_06_commit_validate`, `solver_run_lab_summary.py`, Lab UI consumption)

Skipped:
- L3 rim greedy placement (SHA-1..SHA-6 in progress)
- L5 transport routing budget (SHA-14)
- CLI/artifact ingest/reconcile/game_data (SHA-7..SHA-13)
- L4 inner pattern fill greedy (spec-aligned; corridor shadow out of L4-1 scope)

Findings:
- SHA-15: [bug] RunStackUseCase sets validation_passed from stack success while L6 commit-validate is no-op

Notes:
- `run_stack.py` sets `validation_passed = run_ok` identical to `run_success`; L6 `run_layer_06_commit_validate` is empty stub; Lab UI/timeline treats `validation_passed` as structural validation outcome.

## 2026-06-10 02:04

Reviewed area:
- path/module/feature: `django_apps/shapez_solver/services/` — recipe graph validation (`validate_graph_document`, input carrier arity, quantity contract, macro visual serialize path); related unit tests under `tests/unit/shapez_solver/`

Skipped:
- `asteroid_lab/` services (SHA-9–SHA-13, SHA-21–SHA-22 already filed)
- `.github/workflows/` CI gaps (SHA-18–SHA-20 already filed)
- L3–L6 solver layers (SHA-1–SHA-6, SHA-14–SHA-15 already filed)
- Recipe graph editor ↔ Django recompute API wiring (deferred — needs product decision, not a single bug card this run)
- Issues labeled `reviewing` (SHA-16 autotest probe)

Findings:
- SHA-23: Recipe graph validate_graph_document skips input-count check for binary operations
- SHA-24: Recipe graph validate_graph_document accepts non-integer quantity; macro visual truncates via int()

Notes:
- `_validate_operation_inputs` uses `continue` when `len(sorted_edges) < need`; repro: `stacker`/`merge` with one input edge pass validation
- `quantity: 2.9` passes `validate_graph_document`; `_graph_node_doc_to_solver` emits `int(2.9)==2`
- `validate_recipe_graph_context` has quantity type checks but no production callers outside tests

## 2026-06-10 02:30

Reviewed area:
- path/module/feature: `django_apps/shapez_core/` — `/api/health/`, `/api/shape-preview/` (`views.py`, `preview_service.py`, `shape_render_scene.py`); integration tests `tests/integration/web/test_web_smoke.py`, `tests/integration/api/test_health.py`; frontend `quick_solver_preview.js`

Skipped:
- `shapez_solver/` recipe graph (SHA-23–SHA-24 reviewed 02:04)
- `asteroid_lab/` services (SHA-9–SHA-13, SHA-21–SHA-22 already filed)
- `.github/workflows/` CI gaps (SHA-18–SHA-20 already filed)
- L3–L6 solver layers (SHA-1–SHA-6, SHA-14–SHA-15 already filed)
- Graph PNG preview renderer (SHA-17 already filed)
- `basedata_import_service.py` IVVD import (out of bounded scope this run)
- Issues labeled `reviewing` (SHA-16 autotest probe)

Findings:
- SHA-25: test_api_shape_preview_empty_code misnamed; gallery assertions hide missing empty-code API regression
- SHA-26: Shape preview API uses HTTP 400 for empty code but HTTP 200 for parse errors

Notes:
- `test_api_shape_preview_empty_code` GETs `/gallery/` instead of `/api/shape-preview/`; no integration test for empty/whitespace `code` → HTTP 400
- `build_shape_preview_response('')` / `'   '` → 400; parse errors → 200 + `ok: false`; frontend checks `data.ok` only
- Multi-pattern list `[SuSuSuSu, CuCuCuCu]` works in service but has no integration test (not filed — low signal)

## 2026-06-10 04:30

Reviewed area:
- path/module/feature: `harness/validators/compare_golden.py`, `tests/golden/`, `tests/golden/README.md`, CI/test scripts (`ci.yml`, `scripts/test_fast.ps1`)

Skipped:
- CI validation gaps (SHA-18, SHA-19, SHA-20 already open)
- Asteroid Lab subprocess/artifact paths (SHA-7–SHA-13, SHA-21–SHA-29)
- Recipe graph validation (SHA-23, SHA-24)
- Shape preview API (SHA-25, SHA-26)

Findings:
- SHA-30: Golden harness compare_golden.py and tests/golden fixtures are not wired to pytest or CI

Notes:
- `compare_golden.py` is implemented but only imported from `harness/validators/__init__.py`; zero pytest usage.
- `tests/golden/candidate_selector_trunk_split_{input,expected}.json` exists but no code references the scenario name.
- `tests/golden/README.md` still defers test wiring until after compare_golden exists (stale).

## 2026-06-10 05:07

Reviewed area:
- path/module/feature: `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/` (run.py, candidate_gen.py, shared/route_probe.py) and stack budget wiring in `stack_runner.py` / `layers/contracts/layer_budget.py`

Skipped:
- CI/artifact/recipe-graph/game_data areas — already covered by open Linear issues SHA-7 through SHA-30
- L5 transport budget gap — duplicate of SHA-14

Findings:
- SHA-31: L3 rim greedy placement ignores LayerBudgetContext during Phase B route probe expansion

Notes:
- `run_layer_03_rim_greedy_placement` discards `budget_ctx` via `_ = (budget_ctx, ...)`. Phase B runs anchors×genes×variants×4 weighted A* probes (up to 4096 expanded nodes each) with no `remaining_budget_ms()` polling, unlike L4 inner fill greedy loop. `LayerBudgetContext` doc states budget applies to L2–L5.

## 2026-06-10 09:30

Reviewed area:
- path/module/feature: `django_apps/game_data/browse/` (views, registry, browse_index template) + `tests/unit/game_data/test_admin_browse.py`

Skipped:
- reason: No prior review memory file existed (first persisted run on this branch); duplicate prevention used Linear open-issue search instead

Findings:
- SHA-39: game_data browse dashboard omits validate_aggregate_root_inlines errors from staff UI

Notes:
- `game_data_browse` calls `validate_section_admin_targets()` only; `validate_aggregate_root_inlines()` exists in registry but is pytest-only
- Template `browse_index.html` renders `section_errors` but has no aggregate-root error block
- Prior automation issues SHA-7..SHA-38 already cover CLI/artifact ingest, replay cache, CI gaps, layer budget, recipe graph validation

## 2026-06-10 10:00

Reviewed area:
- path/module/feature: `frontend/recipe_graph_editor/` CI/build pipeline; `.github/workflows/ci.yml`; root `package.json`; `scripts/test_fast.ps1`; `documents/ai/manuals/testing.md`

Skipped:
- `frontend/graph_layout/` — covered by SHA-35 (open Backlog)
- `django_apps/game_data/browse/` — covered by SHA-39 (reviewed ~09:34 UTC)
- `django_apps/asteroid_lab/` replay cache loaders — covered by SHA-37, SHA-38
- Issues labeled `reviewing` — only archived SHA-16 autotest probe

Findings:
- SHA-40: CI never runs recipe graph editor Vitest or build:recipe-graph-editor; committed bundles can drift

Notes:
- `ci.yml` has no Node/npm steps; Vitest and Vite build are manual-only per manuals. Vite outDir writes committed `django_apps/web/static/web/js/recipe_graph_editor/recipe-graph-editor.{js,css}`. Related but distinct from SHA-35 (graph-layout esbuild bundles).

## 2026-06-10 11:30

Reviewed area:
- path/module/feature: `assets/css/input.css` + `django_apps/web/static/web/css/app.css` + Tailwind `build:css` CI gap (`.github/workflows/ci.yml`, `package.json`, `DESIGN.md`)

Skipped:
- CI validation gaps already filed: SHA-35 (graph-layout), SHA-40 (recipe-graph-editor), SHA-42 (locale), SHA-41 (governance), SHA-19/20 (manage.py check, mypy scope)
- Asteroid Lab replay/ingest areas (SHA-21, SHA-37, SHA-38, SHA-33, etc.)
- Solver layer budget issues (SHA-14, SHA-31, SHA-32)
- Locale strict-mode gap (SHA-43)

Findings:
- SHA-44: CI never runs build:css; committed app.css can drift from Tailwind source

Notes:
- `package.json` `build:css` outputs committed `app.css`; `ci.yml` has no Node/npm step.
- `DESIGN.md` requires `npm run build:css` after template/`@source` changes; production loads committed `app.css` via `base.html`.
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` checks a few lab overlay class substrings in `app.css` but is not a full rebuild drift gate.
- Fresh `npm run build:css` on current tree matches committed `app.css` (md5 `450986bed220fc6a44cda342682a81af`); gap is missing CI enforcement, not current drift.

## 2026-06-10 14:00

Reviewed area:
- path/module/feature: `django_apps/shapez_solver/services/pattern_lab_service.py` + Pattern Lab UI (`public_pages.pattern_lab`, `pattern_lab.html`) + `pattern_catalog_repository.py` stub; related tests `tests/unit/shapez_solver/test_pattern_lab_service.py`, `tests/integration/web/test_pattern_lab.py`

Skipped:
- `shapez_solver/` recipe graph validate_graph_document gaps (SHA-23, SHA-24 reviewed 2026-06-10 02:04)
- Asteroid Lab / replay / subprocess areas (SHA-45–SHA-48 and prior)
- CI / frontend bundle drift (SHA-35, SHA-40, SHA-44, SHA-42)
- Issues labeled `reviewing` (SHA-16 autotest probe, archived)

Findings:
- SHA-49: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts

Notes:
- `analyze_pattern_lab_shape('CuCuCuCu:CuCuCuCu')` errors with single-layer-only message; `explain_pattern_family_mismatch` accepts same code (multi-layer tests exist).
- `PatternCatalogRepository.find_macro_candidates` is intentional no-op after migration `0009_drop_pattern_catalog_tables`; template already states catalog removed — not filed.
- `documents/research/pattern_family_macro_taxonomy.md` still describes DB MacroRecipe lookup (stale doc); deferred — not a runtime bug card this run.

## 2026-06-10 16:00

Reviewed area:
- path/module/feature: `django_apps/web/static/web/js/solver_timeline/` (graph_mount, graph_markup, graph_viewport, graph_detail, throughput_summary, dom_utils) + template script wiring (`solver.html`, `home.html`) + pytest coverage (`test_solver_graph_markup.py`, `test_web_smoke.py`)

Skipped:
- `quick_solver_preview.js` GLTF teardown on ok:false — duplicate of SHA-52 (reviewed ~15:33 UTC)
- `recipe_graph_editor/` React Flow bundle — SHA-40 (CI drift)
- `frontend/graph_layout/` esbuild bundles — SHA-35 (CI drift)
- Asteroid Lab replay/timeline JS — SHA-48, SHA-21, SHA-37, SHA-38
- CI/css/locale/governance gaps — SHA-44, SHA-42, SHA-41, SHA-19, SHA-20
- Issues labeled `reviewing` — SHA-16 autotest probe (archived)

Findings:
- SHA-53: solver_timeline graph modules are not mounted on any page; pytest still asserts production layout

Notes:
- `mountGraph()` / `updateThroughputSummary()` have zero production importers; only `TIMELINE_DEBOUNCE_MS` from `constants.js` is used (via `quick_solver_preview.js`)
- No template defines `[data-solver-throughput-summary]`; `/solver/` loads preview-only module while page copy says graph UI is under construction
- Staff graphs use committed `recipe-graph-editor.js`, not `solver_timeline/` Canvas stack

## 2026-06-10 21:05

Reviewed area:
- path/module/feature: `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` + retention test `tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py`

Skipped:
- `solver_subprocess_runner.py` — SHA-45 already filed
- `pytest.ini` vs `pyproject.toml` marker drift — draft noted in daily inspection log; defer to dedicated infra run
- L2–L6 solver layers, replay cache, CI bundle drift — SHA-7..SHA-65 already filed
- Issues labeled `reviewing` — SHA-16 autotest probe (archived)

Findings:
- SHA-66: Layer post-summary log retention sorts runs by mtime; prune test fails and can delete wrong runs

Notes:
- `_prune_old_runs` orders by `st_mtime` only; `test_retention_prunes_oldest_runs_per_project` fails 5/5 with `{'run-0','run-3'}` vs expected `{'run-2','run-3'}`
- Mutex lock held on SHA-66 during run (`auto:project-review-running`), removed on completion
