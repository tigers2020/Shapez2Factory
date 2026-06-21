# Daily Project Inspection Log

Tracks daily inspection automation runs (target rotation, evidence, filed/skipped findings).

**Related docs:**

- Project review memory: [`.agent-loop/reviewed-areas.md`](../../.agent-loop/reviewed-areas.md)
- Project review mutex / holder card: [`project-review-mutex.md`](./project-review-mutex.md) — lock label `auto:project-review-running` on [SHA-67](https://linear.app/zkaufman/issue/SHA-67/automation-project-review-run-mutex-via-dedicated-linear-holder-card) (infrastructure only)

---

## 2026-06-10 Daily Inspection (earlier run)

**Target:** tests / fixtures / regression coverage (pytest config, validation script portability, gate parity)

**Commands run:**
- `git status`, `git branch -v`, `git log --oneline -15`
- `python3 manage.py check`
- `ruff check .`
- `mypy src`
- `mypy django_apps config src` (963 errors — not CI-gated; see SHA-20)
- `black --check .` (pass on `origin/master`; fail on this branch before `1424a207` ancestry)
- `pytest tests/unit/architecture/ -q`
- `pytest tests/integration/web/test_asteroid_miner_layout_solver_async.py -q`
- `pytest --markers`, `pytest --collect-only` (config source warning)
- `gh run list --workflow=ci.yml --limit 5`, `gh run view 27273247252 --log-failed`
- `gh pr list --limit 5`, review of `origin/master:.agent-loop/reviewed-areas.md`

**Files/areas reviewed:**
- `pytest.ini`, `pyproject.toml` (`[tool.pytest.ini_options]`)
- `tests/conftest.py`, `tests/integration/web/test_asteroid_miner_layout_solver_async.py`
- `scripts/test_fast.ps1`, `scripts/test_full.ps1`, `AGENTS.md` § Validation
- `documents/ai/manuals/testing.md`
- `.github/workflows/ci.yml` (cross-check vs prior SHA-18–SHA-20 filings)
- `origin/master:.agent-loop/reviewed-areas.md` (duplicate prevention)

**Findings filed:**

> **Linear MCP blocked:** `https://mcp.linear.app/mcp` returned 401 in this cloud agent session (no `LINEAR_API_KEY`). Draft cards below were **not** created in Linear; paste into Linear manually or re-run with Linear plugin OAuth.

### Draft — SHA-45 (proposed)

**Title:** `[test] Drop or sync stale pyproject.toml pytest config ignored by pytest.ini`

**Labels:** test, infra, refactor | **Priority:** Low

### Draft — SHA-46 (proposed)

**Title:** `[infra] Add cross-platform fast test gate script; AGENTS.md lists PowerShell-only test_fast.ps1`

**Labels:** infra, test, automation, docs | **Priority:** Medium

**Findings skipped (duplicate or weak):**
- CI gaps SHA-18..SHA-20, SHA-30, SHA-40, SHA-41, SHA-44 (see `.agent-loop/reviewed-areas.md`)
- `black --check` failure on branch ancestry without `1424a207` — not filed

**Duplicate checks:**
- Read `origin/master:.agent-loop/reviewed-areas.md` (SHA-7–SHA-44 backlog)
- Linear MCP search unavailable (401)

**Next recommended target:** core runtime / solver / domain logic (`src/shapez2_factory/application/asteroid_lab/layers/`)

---

## 2026-06-10 Daily Inspection (13:01 UTC cron)

**Target:** core runtime / solver / domain — Django subprocess runner + stack orchestration (`django_apps/asteroid_lab/services/solver_subprocess_runner.py`, `solver_runtime_entry.py`, `src/shapez2_factory/interfaces/cli/asteroid_solve.py`, `stack_runner.py`)

**Commands run:**
- `git status`, `git branch -v`, `git log --oneline -15`
- `python3 manage.py check`
- `ruff check django_apps/asteroid_lab/services/solver_subprocess_runner.py src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `pytest tests/unit/asteroid_lab/layers/ tests/unit/asteroid_lab/test_solver_subprocess_runner.py tests/unit/shapez2_factory/ -q` (352 passed, 1 failed under xdist batch)
- `pytest tests/unit/asteroid_lab/test_solver_subprocess_runner.py -q` (5 passed)
- `pytest tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py::test_retention_prunes_oldest_runs_per_project -n 4` (4/5 failed — mtime flake reproduced)
- `curl https://api.linear.app/graphql` (401 — no API key)

**Files/areas reviewed:**
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- `django_apps/asteroid_lab/services/solver_run_reconcile.py` (async ingest path contrast)
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (`ExitCode`, artifact write before return)
- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` (`_prune_old_runs`)
- `tests/unit/asteroid_lab/test_solver_subprocess_runner.py`
- `tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py`
- `.agent-loop/reviewed-areas.md`, automation memory `daily-inspection.md`

**Findings filed:**

> **Linear MCP blocked:** `https://api.linear.app/graphql` returned 401 (no `LINEAR_API_KEY`). Draft cards below were **not** created in Linear.

### Draft — SHA-47 (proposed)

**Title:** `[bug] Sync run_solver_subprocess aborts before ingest when CLI returns exit 20 with written artifacts`

**Description:**

## Problem
`asteroid_solve run` finalizes artifact directories then returns `ExitCode.STACK_UNAVAILABLE` (20) when `RunStackUseCase` reports `ok=False`. The synchronous Django wrapper `run_solver_subprocess` raises `SolverSubprocessError` on any non-zero return code, so `_run_subprocess_runtime_for_project` never calls `ingest_artifact_for_project`. Artifacts on disk are orphaned; `SolverRun` rows are not created/indexed for partial-failure diagnostics. The async reconcile path ingests from `artifact_dir` regardless of exit code — sync and async behavior diverge.

## Evidence
- `asteroid_solve.py` lines 248–287: `writer.finalize(manifest)` then `return int(ExitCode.OK if result.ok else ExitCode.STACK_UNAVAILABLE)`
- `solver_subprocess_runner.py` lines 192–195: `if completed.returncode != 0: raise SolverSubprocessError(...)`
- `solver_runtime_entry.py` lines 92–118: catch `SolverSubprocessError` → `ok=False` without ingest
- `solver_run_reconcile.py` `_attempt_artifact_ingest`: ingests when manifest validates (async path)
- `tests/unit/asteroid_lab/test_solver_subprocess_runner.py`: no test for exit 20 + artifact present
- Related but distinct: SHA-8 (CLI exit 20 unit test), SHA-10 (ingest `error_code` regression)

## Impact
Blocking sync solver runs (`run_solver_runtime_for_project`) lose artifact-first contract on stack-unavailable outcomes. Lab UI/replay cannot surface partial layer summaries; operators see generic subprocess failure instead of ingested FAILED run with manifest `error_code`.

## Suggested Fix
Treat exit 20 like reconcile: if `artifact_dir` contains a verified manifest, return `SolverSubprocessResult` (do not raise) and let runtime entry ingest; map CLI exit to `SolverRun` FAILED/COMPLETED per manifest `error_code`. Preserve raise for exit 10 (validation) when no artifact dir. Add regression test mirroring SHA-8 fixture with `returncode=20` and asserting ingest proceeds.

## Acceptance Criteria
- Sync subprocess path ingests artifacts when CLI exits 20 and manifest verifies
- `SolverRun` row reflects manifest `error_code` / FAILED status
- Exit 10 without artifacts still raises `SolverSubprocessError`
- Regression test in `tests/unit/asteroid_lab/test_solver_subprocess_runner.py` or runtime entry tests

**Labels:** bug, test, automation | **Priority:** High

---

### Draft — SHA-48 (proposed)

**Title:** `[test] layer_post_summary_log retention prune flakes under pytest-xdist (mtime tie-breaking)`

**Description:**

## Problem
`_prune_old_runs` sorts run directories by `st_mtime` only. When four sessions are created in rapid succession (as in `test_retention_prunes_oldest_runs_per_project`), mtimes often tie; Python's sort is unstable for equal keys, so the wrong directories survive. The test fails intermittently under `pytest -n auto` (observed in layer batch run and 4/5 reproduces with `-n 4`).

## Evidence
- `layer_post_summary_log.py` `_prune_old_runs`: `run_dirs.sort(key=lambda p: p.stat().st_mtime)`
- `test_layer_post_summary_log.py::test_retention_prunes_oldest_runs_per_project` expects `{"run-2", "run-3"}`
- Failure under `-n 4`: `assert {'run-0', 'run-3'} == {'run-2', 'run-3'}`
- Solo run passes; batch `pytest tests/unit/asteroid_lab/layers/` had 1 failure in 352 tests

## Impact
CI / `test_fast.ps1` (`-n auto`) non-determinism; false reds on unrelated PRs; erodes trust in layer observability gate.

## Suggested Fix
Use deterministic tie-breaker (`run_dir.name` or creation order) in sort key, e.g. `sort(key=lambda p: (p.stat().st_mtime, p.name))`. Alternatively touch each run dir with monotonic timestamps in the test setup.

## Acceptance Criteria
- `test_retention_prunes_oldest_runs_per_project` passes 20 consecutive runs with `-n 4`
- Prune semantics unchanged: retain newest `max_runs` directories

**Labels:** test, infra | **Priority:** Medium

**Findings skipped (duplicate or weak):**
- CLI exit 20 test coverage only — **SHA-8** (does not cover Django ingest gap)
- Ingest `manifest.error_code` regression — **SHA-10**
- L3/L5 `LayerBudgetContext` discard — **SHA-14**, **SHA-31**
- L6 `validation_passed` semantics — **SHA-15**
- `budget_ctx` discarded in L2/L3 entrypoints — observed (`_ = budget_ctx`); L2 is fast planning, lower signal than SHA-31
- `spawn_solver_subprocess_detached` direct unit coverage — thin but async path covered via `test_solver_run_async_spawn.py` (mocked); not filed

**Duplicate checks:**
- `.agent-loop/reviewed-areas.md` (SHA-7–SHA-44; subprocess runner deferred 2026-06-09)
- Automation memory `daily-inspection.md` (SHA-45/46 drafts from earlier 2026-06-10 run)
- `plans/` grep: no existing SHA-47/48; SHA-8/10 related but different root cause
- Linear API search unavailable (401)

**Next recommended target:** UI / frontend / interaction flow (Asteroid Lab replay viewer, lazy cache UX) — SHA-37/38 filed; consider `django_apps/web/views/` lab pages or `basedata_import_service.py` (deferred 2026-06-10 02:30)

---

## 2026-06-11 Daily Inspection (13:02 UTC cron)

**Target:** UI / frontend / interaction flow — Asteroid Lab run-solver wiring (`asteroid_miner_layout_solver.html`, `asteroid_miner_layout_lab.js`, `public_pages.py`, `solver_runtime_entry.py`, `solver_subprocess_runner.py`)

**Commands run:**
- `git status`, `git branch --show-current`, `git log --oneline -10`
- `python3 manage.py check`
- `python3 -m pytest tests/integration/web/test_asteroid_miner_layout_solver_async.py tests/integration/web/test_web_smoke.py tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py -q` (37 passed)
- `python3 -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py tests/integration/web/test_lab_replay_ssr_manifest.py tests/unit/shapez_core/test_basedata_ivvd.py -q` (28 passed)
- `python3 -m ruff check django_apps/web/views/public_pages.py django_apps/web/services/asteroid_lab_page_context.py django_apps/asteroid_lab/services/solver_runtime_entry.py` (pass)
- `curl https://api.linear.app/graphql` (401 — no `LINEAR_API_KEY`)
- `rg macro_only_mode|rttp_record_replay` (repo-wide wiring audit)

**Files/areas reviewed:**
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html` (macro-only checkbox)
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (run-solver POST body)
- `django_apps/web/views/public_pages.py` (`_run_solver_request_config`, lazy replay cache gate)
- `django_apps/web/services/asteroid_lab_page_context.py` (lazy SSR cache hit branch)
- `django_apps/asteroid_lab/services/solver_runtime_entry.py` (`_build_subprocess_request`)
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py` (`build_solver_cli_args`)
- `django_apps/asteroid_lab/services/solver_run_config_keys.py`, `solver_run_lab_summary.py`
- `documents/superpowers/specs/2026-06-08-l4-inner-pattern-fill-contract.md` (macro-only open question)
- `.agent-loop/reviewed-areas.md`, `plans/` (duplicate prevention)

**Findings filed:**

> **Linear MCP blocked:** `https://api.linear.app/graphql` returned 401 (no `LINEAR_API_KEY`). Draft card below was **not** created in Linear.

### Draft — SHA-69 (proposed)

**Title:** `[ui] Lab Macro-only mode checkbox does not wire macro_only_mode or rttp_record_replay into solver runtime`

**Description:**

## Problem
The Asteroid Mining Lab exposes a "Macro-only mode" checkbox (`#lab-macro-only-mode`). When checked, the client POSTs `macro_only_mode: true` and `rttp_record_replay: true` to the run-solver endpoint. Those keys are defined in `solver_run_config_keys.py` and displayed in lab run summaries, but no runtime code reads them: `_build_subprocess_request` only forwards `throughput_target_percent` and `verbose`; `build_solver_cli_args` has no corresponding CLI flags; domain/stack code has no `macro_only_mode` branch (L4 contract still lists macro-only as an open question). Users believe they toggled a pipeline mode; solver behavior is unchanged.

## Evidence
- `asteroid_miner_layout_lab.js` lines 5109–5131: checkbox → `postBody.macro_only_mode` / `rttp_record_replay`
- `public_pages.py` `_run_solver_request_config`: returns parsed JSON dict as `run_config` unchanged
- `solver_runtime_entry.py` `_build_subprocess_request` lines 143–168: only `throughput_target_percent` extracted from config
- `solver_subprocess_runner.py` `build_solver_cli_args` lines 121–150: no macro/RTTP flags
- `rg macro_only_mode` across `django_apps/` + `src/`: only config key constants and lab summary display — zero consumers
- `documents/superpowers/specs/2026-06-08-l4-inner-pattern-fill-contract.md` §미결정: "macro-only mode에서 L4 skip 여부"
- Contrast: `throughput_target_percent` is wired end-to-end (JS → config → CLI `--throughput-target-percent`)

## Impact
Misleading Lab UX; experiment/debug sessions cannot enable macro-only pipeline from UI; run summary may show absent `macro_only_mode` even when checkbox was checked; agents/operators waste time assuming mode switched.

## Suggested Fix
Either (a) hide/disable checkbox until macro-only contract is implemented, or (b) thread `macro_only_mode` / `rttp_record_replay` through `SolverSubprocessRequest` → CLI args → stack runner with documented layer skip semantics; persist toggles in `SolverRun.config_json` on async enqueue; add integration test that checked checkbox changes artifact `solver_summary.macro_only_mode` or layer observability.

## Acceptance Criteria
- Checkbox state affects solver execution or is removed/disabled with explicit copy
- `macro_only_mode` present in ingested `solver_summary` when toggled on
- Regression test covers run-solver POST with `macro_only_mode: true`
- No silent no-op for `rttp_record_replay` when sent alongside macro-only

**Labels:** bug, ui, test | **Priority:** Medium

**Findings skipped (duplicate or weak):**
- `lab_page_context` lazy cache hit omits `is_cache_summary_valid` — **SHA-37** (page context); loader path — **SHA-38**
- `topology_rules` always `[]` — **SHA-57**
- Replay cache / lazy SSR manifest — **SHA-37**, **SHA-38**, **SHA-21**
- `basedata_import_service.py` IVVD import — deferred (not in today's bounded UI pass)
- Subprocess exit-20 ingest gap — **SHA-45** / daily log SHA-47 draft (distinct root cause)
- All targeted web/lab pytest green — no new regression filed

**Duplicate checks:**
- `.agent-loop/reviewed-areas.md` (SHA-7–SHA-56; solver_timeline SHA-53; recipe editor SHA-56)
- `plans/` grep: no existing SHA-* plan for `macro_only_mode`
- `documents/agent-workflows/daily-project-inspection-log.md` prior entries (SHA-37/38/45–48 drafts)
- Linear API search unavailable (401)

**Next recommended target:** docs / specs / contracts / AGENTS rules (macro-only L4 open question vs UI exposure; replay wiring canon `documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md`) — or CI / scripts / automation (`scripts/test_fast.ps1` cross-platform gap SHA-46)

---

## 2026-06-12 Daily Inspection (13:00 UTC cron)

**Target:** docs / specs / contracts / AGENTS rules — repository map SoT (`structure.md`), agent authority routing (`AGENTS.md`, `.cursor/rules/`), knowledge wiki bootstrap aftermath

**Commands run:**
- `git status`, `git branch --show-current`, `git log --oneline -15`
- `python3 manage.py check` (pass)
- `python3 -m pytest tests/unit/architecture/ -q` (54 passed)
- Custom link-existence scan on `structure.md`, `AGENTS.md`, `documents/agent-workflows/`, `documents/knowledge/wiki/`
- Path inventory: `ls documents/`, `ls documents/`, `find` for `asteroid_lab_*.md`, `documents/game_rules/`, `documents/adr/`
- `curl https://api.linear.app/graphql` (401 — no `LINEAR_API_KEY`)
- `rg` stale authority paths in `.cursor/`, `structure.md`, production code comments

**Files/areas reviewed:**
- `structure.md` § Documents map + Top-level layout links
- `AGENTS.md` § Default workflow authority chain (wiki Index pointer added in bc43d5b6)
- `.cursor/rules/asteroid-lab-invariants.mdc` (glob + six Algorithm file references)
- `documents/knowledge/README.md`, `documents/knowledge/wiki/Index.md`, `documents/knowledge/wiki/Log.md`
- `documents/knowledge/raw/index/document_inventory.md` (stale 2026-05-30 authority table)
- `documents/knowledge/raw/algorithm/README.md` (only `asteroid_lab_11` remains ACTIVE)
- `tests/unit/architecture/test_repo_map_governance.py` (top-level paths only; Documents map not gated)
- Production doc comments: `django_apps/shapez_core/domain/*.py`, `rim_throughput.py`, migration `0026`

**Findings filed:**

> **Linear MCP blocked:** `https://api.linear.app/graphql` returned 401 (no `LINEAR_API_KEY`). Draft card below was **not** created in Linear.

### Draft — SHA-70 (proposed)

**Title:** `[docs] structure.md and asteroid-lab-invariants reference removed documents/ paths after knowledge wiki bootstrap`

**Description:**

## Problem
2026-06-12 wiki bootstrap (`bc43d5b6`) updated `AGENTS.md` to route agents through `documents/knowledge/wiki/Index.md`, but `structure.md` (repository map SoT) and `.cursor/rules/asteroid-lab-invariants.mdc` still declare canonical authority under `documents/README.md`, `documents/index/`, `documents/Algorithm/`, `documents/plans/`, `documents/research/`, and legacy `documents/superpowers/plans/2026-05-30-asteroid-lab-cli-first/` paths that no longer exist on disk. Active `documents/` tree is now `documents/knowledge/` + `documents/ai/manuals/` only; ADRs, game rules, algorithm canon, and CLI-first specs live under `documents/knowledge/raw/` or a reduced `documents/superpowers/` set. Agents following `structure.md` or invariant router globs hit dead paths; `asteroid_lab_12_runtime_replay_wiring.md` and five other Algorithm contracts referenced by invariants are absent repo-wide.

## Evidence
- `structure.md` Documents map: 11 broken relative links (`documents/README.md`, `documents/index/document_inventory.md`, `documents/Algorithm/README.md`, `documents/plans/`, `documents/research/`, `documents/reports/README.md`, `documents/superpowers/plans/2026-05-30-asteroid-lab-cli-first/README.md`, `documents/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`)
- Missing at former canon paths: `documents/ai/START_HERE.md`, `documents/adr/`, `documents/game_rules/`, `documents/domain/asteroid_game_data_snapshot.md` — counterparts exist only under `documents/knowledge/raw/**`
- `.cursor/rules/asteroid-lab-invariants.mdc`: glob `documents/Algorithm/asteroid_lab*.md` matches zero files; references `_01_optimization_input.md` … `_12_runtime_replay_wiring.md` — none on disk (only `documents/knowledge/raw/algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md` marked ACTIVE)
- `documents/knowledge/raw/index/document_inventory.md` still lists deleted paths as `CANON` (dated 2026-05-30)
- `tests/unit/architecture/test_repo_map_governance.py::test_structure_md_top_level_paths_exist` passes because it does not validate § Documents map links
- Code comments still cite `documents/game_rules/*.md` while files are at `documents/knowledge/raw/game-rules/*.md` (e.g. `shape.py`, `crystal_geometry.py`, `rim_throughput.py`)
- `python3 manage.py check` pass; `pytest tests/unit/architecture/ -q` 54 passed

## Impact
Repository map SoT contradicts post-bootstrap layout — agents, automations, and humans lose domain authority chain for Asteroid Lab invariants, ADRs, game rules, and CLI-first specs. Invariant router glob never activates on algorithm edits. Risk of reintroducing deleted archive docs or implementing against stale inventory rows.

## Suggested Fix
Pick one authority policy and apply consistently: (a) restore thin active symlinks or re-export paths for still-canonical docs (`documents/adr/`, active `documents/superpowers/specs/`, surviving algorithm contracts), or (b) update `structure.md` Documents map, `document_inventory.md`, `asteroid-lab-invariants.mdc` globs/references, and code-comment paths to `documents/knowledge/raw/` + wiki Index; add `test_structure_md_document_map_links_exist` (or extend repo-map governance) so future migrations cannot ship with broken SoT links.

## Acceptance Criteria
- Every link in `structure.md` § Documents map resolves on disk or is explicitly marked non-authority
- `asteroid-lab-invariants.mdc` glob matches existing algorithm/canon files or lists wiki/raw successors
- `document_inventory.md` reflects 2026-06-12 layout; no `CANON` rows for missing paths
- Architecture test fails if Documents map links break
- `AGENTS.md` and `structure.md` agree on authority read order

**Labels:** docs, infra, automation | **Priority:** High

**Findings skipped (duplicate or weak):**
- Macro-only Lab checkbox no-op — **SHA-69** (UI; filed 2026-06-11)
- L4 macro-only open question in archived spec `documents/knowledge/raw/docs-superpowers/specs/2026-06-08-l4-inner-pattern-fill-contract.md` — contract gap subsumed by SHA-69 product issue; not a separate docs card
- `scripts/test_fast.ps1` Linux gap — **SHA-46** draft (CI/scripts rotation deferred)
- CI governance script not in CI — **SHA-41** (open plan)
- Wiki internal broken wikilinks — resolved per `documents/knowledge/wiki/Log.md` 2026-06-12 entries; active governance paths are the higher-severity gap
- `documents/knowledge/raw/` internal cross-links to old `documents/Algorithm/` — expected archive noise; fix via inventory/structure update, not separate filing

**Duplicate checks:**
- `.agent-loop/reviewed-areas.md` (SHA-7–SHA-56; no structure.md / wiki-bootstrap entry)
- `documents/agent-workflows/daily-project-inspection-log.md` prior entries (SHA-45–69 drafts; no SHA-70)
- `documents/knowledge/raw/plans/` grep: no plan for structure.md / documents path migration
- Linear API search unavailable (401)

**Next recommended target:** CI / scripts / automation (`scripts/test_fast.ps1` cross-platform gap SHA-46; `check_governance.ps1` CI gap SHA-41) — or performance / large-fixture behavior (`tests/golden/`, golden harness SHA-30)

---

## 2026-06-21 Daily Inspection (13:00 UTC cron)

**Target:** performance / scalability / large-fixture behavior — `tests/golden/`, golden harness post-reset state (`6822b420`), slow exhaustive gene fixtures, lab perf trace contracts

**Commands run:**
- `git status`, `git branch --show-current`, `git log --oneline -10`
- `python3 manage.py check` (pass)
- `python3 -m pytest tests/unit/asteroid_lab/test_lab_perf_trace.py tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py -q` (8 passed)
- `python3 -m pytest tests/unit/asteroid_lab/test_sample_gene_exhaustive.py -m "not slow" -q` (20 deselected; fast slice clean)
- `python3 -m pytest tests/unit/asteroid_lab/test_sample_gene_exhaustive.py::test_exhaustive_generator_extension_count_0_to_3 -q` (1 passed, ~6s — `slow` marker + `conftest` `_SLOW_FIXTURE_NAMES` exclusion verified)
- `python3 -m pytest tests/unit/architecture/test_repo_map_governance.py -q` (1 failed: `test_structure_md_top_level_paths_exist`)
- `ls harness/validators/`, `git log --oneline -3 -- harness/validators/ tests/golden/`
- `rg candidate_selector_trunk_split compare_golden run_golden_loop` (repo-wide)
- `gh pr view 290`, `gh pr list --state open` (duplicate prevention vs 2026-06-20 CI inspection)
- `curl https://api.linear.app/graphql` (400 without body — no `LINEAR_API_KEY`)

**Files/areas reviewed:**
- `tests/golden/README.md`, `tests/golden/candidate_selector_trunk_split_{input,expected}.json`
- `harness/validators/__init__.py` (golden comparators removed)
- `structure.md` § Top-level layout (`compare_golden.py`, `documents/knowledge/raw/ai/templates/`)
- `tests/conftest.py` (`_SLOW_FIXTURE_NAMES`, autouse layout seed)
- `tests/unit/asteroid_lab/conftest.py` (`exhaustive_genes_ext3` module scope)
- `django_apps/asteroid_lab/observability/lab_perf_trace.py`
- `.devtool/features/done/outer-rim-golden-reset-l1-only-2026-06-13.md`
- Commit `6822b420` (golden harness removal)
- Open PR #290 (`SHA-71`/`SHA-72` drafts, 2026-06-20 CI pass)

**Findings filed:**

> **Linear MCP blocked:** no `LINEAR_API_KEY`; GraphQL endpoint returned 400. Draft card below was **not** created in Linear.

### Draft — SHA-73 (proposed)

**Title:** `[test] Reconcile orphaned tests/golden fixtures and docs after golden harness removal`

**Description:**

## Problem
Commit `6822b420` (2026-06-13) removed `harness/validators/compare_golden.py`, `scripts/run_golden_loop.py`, and the `golden-fixture-optimization-loop` skill as part of the L2–L6 algorithm reset. `harness/validators/__init__.py` now states golden comparators were removed. However `tests/golden/candidate_selector_trunk_split_{input,expected}.json` remain with zero pytest references, `tests/golden/README.md` still defers wiring until `compare_golden.py` exists, and `structure.md` still lists `compare_golden.py` under `harness/validators/`. Open **SHA-30** assumed the comparator existed and only needed pytest/CI wiring — that fix direction is obsolete.

## Evidence
- `harness/validators/__init__.py`: `"""golden comparators removed."""`
- `git show 6822b420 --stat`: deletes `compare_golden.py`, `run_golden_loop.py`, golden-loop skill
- `rg candidate_selector_trunk_split tests/` → no matches
- `tests/golden/README.md` §활성화 조건: still references future `compare_golden.py`
- `structure.md` line 36: `Golden comparators (e.g. compare_golden.py)`
- `python3 -m pytest tests/unit/asteroid_lab/test_lab_perf_trace.py …` — 8 passed (perf trace contracts intact)

## Impact
Agents and automations following SHA-30 or `structure.md` hunt a deleted harness; orphaned golden JSON misrepresents regression coverage; future golden work lacks a declared baseline (L1-only post-reset vs revive comparator).

## Suggested Fix
Pick one policy: (a) delete `tests/golden/` fixtures + update `structure.md` / README to document L1-only regression until phase2, superseding SHA-30; or (b) restore a minimal `compare_golden.py` smoke for the trunk-split scenario only. In either case, align `.agent-loop/reviewed-areas.md` SHA-30 notes with post-`6822b420` reality.

## Acceptance Criteria
- No repo doc references nonexistent `compare_golden.py` / `run_golden_loop.py` as active harness
- `tests/golden/` either wired to pytest or removed with rationale in README
- SHA-30 closed or superseded with correct post-reset contract

**Labels:** test, docs, refactor | **Priority:** Medium

**Findings skipped (duplicate or weak):**
- Master CI lint/format red — **SHA-71** draft on open PR [#290](https://github.com/tigers2020/Shapez2Factory/pull/290) (2026-06-20 inspection; not merged to `master` log yet)
- `test_fast.sh` `python` vs `python3` — **SHA-72** draft on PR #290
- game_data bundle / simulation audit TSV CI failures — open PR [#289](https://github.com/tigers2020/Shapez2Factory/pull/289)
- `structure.md` `documents/knowledge/raw/ai/templates/` missing (templates at `documents/ai/templates/`); `documents/README.md` absent — **SHA-70** (docs authority drift; `test_structure_md_top_level_paths_exist` fails)
- L3 budget ignored during probe expansion — **SHA-31**; layer_post_summary mtime flake — **SHA-48** draft
- Lab compose latency — GitHub issue #176 (investigation; no new perf guard in tree)
- `exhaustive_genes_ext3` ~6s/module — correctly `slow` + excluded from `test_fast` via `conftest._SLOW_FIXTURE_NAMES`; not filed

**Duplicate checks:**
- `.agent-loop/reviewed-areas.md` (SHA-30 filed 2026-06-10 for wiring compare_golden — status inverted by `6822b420`)
- `documents/agent-workflows/daily-project-inspection-log.md` (SHA-45–70; SHA-71/72 on PR #290 only)
- `gh pr list` — #290 open (2026-06-20 CI/scripts), #289 open (game_data)
- Linear API unavailable (no key)

**Next recommended target:** dead code / duplication / complexity hotspots (`solver_timeline/` per 2026-06-20 log) — or re-run docs/contracts pass after `documents/` merge stabilizes (SHA-70)
