# PR-CLI-2e — L3..L6 + stack_runner Move (GATED on boundary-m-repack stability)

**Type:** refactoring (relocation)
**Depends on:** PR-CLI-2d **AND** L3 boundary-m-repack PR-B/C merged & green
**Enables:** PR-CLI-3b (full pure CLI)
**Branch (suggested):** `feat/asteroid-cli-first-l3-stack-move`

---

## GATE (BA-3) — do not start until ALL true

```text
[x] 2026-05-30-layer-03-boundary-m-repack-greedy PR-B merged to master
[x] PR-C (if separate) merged or explicitly out of scope
[x] Lab gate green on master with new L3
[x] No open PR currently editing layer_03_rim_mining_bundles/**
```

If the gate cannot be met but the initiative must proceed, the **only** alternative is to move L3 as
**legacy-only** with a retirement banner docstring + tracking issue — never mix algorithm edits here.

### GATE evidence (OPENED 2026-05-30, empirically verified)

- **PR-B merged:** boundary-m-repack greedy (m3e_01) landed as **PR #133**
  ("feat(asteroid-lab): Layer 03 boundary-m-repack greedy (m3e_01)"), merge SHA
  `895a5ecba7f2022adfa97fd584bc84eedaf9b8f6`, merged `2026-05-30T22:21:45Z`. `origin/master` HEAD =
  `895a5ecb …(#133)`.
- **PR-C:** no separate PR-C exists — the full m3e_01 enhancement shipped in PR #133. PR-C is therefore
  **out of scope (absorbed into PR-B/#133)**.
- **Lab gate green on master with new L3** (verified on `feat/asteroid-cli-first-l3-stack-move` @ `895a5ecb`):
  - `pytest tests/unit/asteroid_lab/layers/ tests/unit/asteroid_lab/replay/` — **173 passed**, 2 warnings.
  - `pytest tests/unit/shapez2_factory/ tests/unit/architecture/test_shapez2_factory_core_purity.py` — **85 passed**.
  - `pytest .../test_contract_shim_identity.py` (worktree baseline) — combined **100 passed**.
- **No open PR editing layer_03:** `gh pr list --state open` → `[]` (#132 fast-cache + #133 m3e_01 both MERGED).
- **GATE = OPEN.** Step 0 SHA to record in PR description: `895a5ecba7f2022adfa97fd584bc84eedaf9b8f6` (#133).

## Goal

Relocate `layer_03..layer_06` **and** `stack_runner` into core **in one PR**, so that the moment
stack_runner enters core it already calls in-core L3–L6. This guarantees **no `django_apps` bridge ever
exists in core** — BA-1 is preserved at every committed state.

> **Structural amendment (2026-05-30):** `stack_runner` move was pulled out of PR-CLI-2d into this PR.
> Reason: stack_runner transitively needs L3–L6; moving it earlier forced a `django_apps` bridge that
> violated BA-1. By moving L3–L6 + stack_runner together, core never imports `django_apps`.

## Behavior contract

- L3 greedy / boundary-m-repack behavior identical to post-PR-B master (pure relocation).
- `stack_runner` in core; `run_full_from_cleanup_recon` produces identical `StackRunResult`.
- Zero `django_apps` imports reachable from core; purity gate has no exceptions.

## Non-goals

- No algorithm tuning.
- No CLI (3a already shipped; full run is 3b).

---

## Move set

> **Move-set correction (2026-05-30, post-merge audit):** master's active L3 directory is
> **`layer_03_rim_greedy_placement/`** (12 files, holds m3e_01 + the greedy algorithm). The original plan
> table listed only the legacy `layer_03_rim_mining_bundles/`, which is now a 2-file deprecation **delegate
> stub**. Both move; the active greedy package is the real payload.

| From | To | Kind |
|------|-----|------|
| [`layers/layer_03_rim_greedy_placement/`](../../../../django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/) (12 files) | `application/asteroid_lab/layers/layer_03_rim_greedy_placement/` | **active L3 (m3e_01) — real algorithm** |
| [`layers/layer_03_rim_mining_bundles/`](../../../../django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/) | `application/asteroid_lab/layers/layer_03_rim_mining_bundles/` | legacy delegate stub |
| `layers/layer_04_rim_bundle_placement/` | `application/asteroid_lab/layers/layer_04_rim_bundle_placement/` | disabled shim |
| `layers/layer_05_inner_pattern_fill/` | `application/asteroid_lab/layers/layer_05_inner_pattern_fill/` | no-op signature stub |
| `layers/layer_06_commit_validate/` | `application/asteroid_lab/layers/layer_06_commit_validate/` | no-op skeleton stub |
| [`layers/stack_runner.py`](../../../../django_apps/asteroid_lab/layers/stack_runner.py) | `application/asteroid_lab/stack_runner.py` (Step 2) | orchestrator — split pure vs Django |

**Deferred-from-2d prerequisites (must move in Step 1 so L4/L5 can be pure):** PR-CLI-2d Step 1 explicitly
deferred `rim_placement` + `layer04_disabled` to 2e because they import `services.dto`. Audit confirms all
three are pure (no Django/ORM):

| From | To | Note |
|------|-----|------|
| `services/dto.py` (self-declared "no Django imports"; imports only `shapez2_factory.domain...DecodedCellDTO`) | `domain/asteroid_lab/service_dtos.py` | whole-file move + shim (PR-CLI-2a pure-DTO precedent); needed for `ReplayFrameAppendDTO` |
| `layers/contracts/layer04_disabled.py` | `application/asteroid_lab/layers/contracts/layer04_disabled.py` | needs `ReplayFrameAppendDTO` (now core) |
| `layers/contracts/rim_placement.py` | `application/asteroid_lab/layers/contracts/rim_placement.py` | needs `ReplayFrameAppendDTO` (now core) |

**`seed_orient.py` split (the one non-shim Django coupling in L3):** `seed_orient` imports
`snapshots.equipment_bundles.ports_compatible` (game-data catalog dependency, not in core) **only** inside
`placement_extension_rotation`, which is consumed **only** by Django replay
(`replay/layer03_rim_greedy_segment.py`) + tests — never by the greedy hot path. Therefore:

- **Core `seed_orient`** keeps the pure greedy parts: `layout_seed_at_anchor`, `SeedLayout`,
  `SeedLayoutReject`, `str_output_dir_to_direction`, `placement_output_rotation`, `_DIR_DELTA`,
  `_OUTPUT_TO_ROTATION`.
- **Django shim `seed_orient`** re-exports the core symbols **and** retains `placement_extension_rotation`
  locally (it stays Django-coupled via `ports_compatible`). No `equipment_bundles`/game-data import enters core.

**`stack_runner` Step 2 — APPROVED WITH BOUNDARY AMENDMENTS (reviewer, 2026-05-30):** use **Approach A** —
make core *more ignorant*: core computes results only, Django owns logs/settings/files/observability.

- **Core** `application/asteroid_lab/stack_runner.py` (pure, BA-1): `run_layers_02_to_06(*, complete_map,
  budget_ctx, runners) -> CoreStackRunResult` where `CoreStackRunResult = (stack_result: StackRunResult,
  layer_summaries: tuple[LayerPostSummaryRecord, ...])`. Runner-injected orchestration (loop + 60s budget via
  injected `budget_ctx.now_fn` + per-layer metric build via core `post_summary_metrics`). **No
  `post_summary_session`, no settings, no file I/O, no `django`/`django_apps` import.** L4 stays disabled via
  the **core** `empty_layer04_rim_placement_result()` / `Layer04DisabledResult.superseded()` — never the
  Django L4 path. Collects the exact `LayerPostSummaryRecord`s (incl. `SKIPPED_BUDGET` on timeout) the old
  code emitted, in order, and returns them instead of writing.
- **Django wrapper** `django_apps/asteroid_lab/layers/stack_runner.py`: keeps the FULL existing public surface
  (`run_layers_02_to_06(..., post_summary_session=None) -> StackRunResult`, `run_layers_02_to_05`,
  `run_full_from_cleanup_recon`, `_DEFAULT_RUNNERS` = Django layer shims, `__all__`) for zero test churn.
  Delegates orchestration to the core runner, then — when a session exists — writes each returned record and
  closes. `run_full_from_cleanup_recon` owns L1 `run_layer_01` + L1 timing + L1 record +
  `create_layer_post_summary_log_session` (settings flag `ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_ENABLED`).

**Forbidden in core:** `from django.conf import settings`, any Django `LayerPostSummaryLogSession` type in a
core signature, any `django_apps...layer_04` import. Allowed fallback (not used here): pure `Protocol` sink.

### Step 2 acceptance gate

```text
[x] core stack_runner imports no django/django_apps/config/settings (purity gate + Django-free subprocess test)
[x] Django wrapper owns L1 run_layer_01 + post-summary file logging + session creation + settings flag
[x] core receives now_fn / budget context by injection (budget_ctx.now_fn)
[x] L4 remains disabled without importing Django L4 (core empty_layer04_rim_placement_result)
[x] old django stack_runner path is explicit wrapper preserving full public surface (__all__ identical)
[x] existing layer/replay tests remain green (175 incl. +2 boundary tests) + post-summary log tests green
[x] purity gate has zero django_apps exceptions
```

New tests: `test_core_stack_runner_does_not_import_django`(+importable without settings, subprocess),
`test_django_run_full_wrapper_delegates_to_core_runner`, `test_layer4_disabled_result_is_core_pure`.

## Tasks

- [x] **Step 0:** GATE verified OPEN (PR #133 `895a5ecb`; lab gate 173+85 green; no open L3 PR). SHA recorded above.
- [x] **Step 1:** L3 greedy(12) + legacy/L4/L5/L6 + deferred `service_dtos`/`layer04_disabled`/`rim_placement`
  moved to core; `seed_orient` split; shims at all original paths. spec✅ + quality✅ (175 layers/replay green).
- [x] **Step 2:** `stack_runner` split (Approach A): pure core `run_layers_02_to_06 -> CoreStackRunResult`
  (records only), Django wrapper owns L1/session/settings/file-write. spec✅ + quality✅.
- [x] **Step 3:** No `_l3_l6_bridge` anywhere; core has zero `django_apps`/`from django` imports (docstring-only
  matches); purity gate `test_shapez2_factory_has_no_forbidden_imports` green.
- [x] **Step 4:** Full suite green — `tests/unit/asteroid_lab/ + shapez2_factory/ + architecture/` = **858 passed, 1 xfailed**.
- [x] **Step 5:** `ruff` clean · `black --check` clean · `mypy src` clean (112 files) · reconstruction narrow **25 passed**.

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/layers/ -v
python -m pytest tests/unit/shapez2_factory/ tests/unit/architecture/test_shapez2_factory_core_purity.py -v
powershell -File scripts/test_reconstruction_narrow.ps1
python -m mypy django_apps config src
```

## Risks

- `invariant:` 60s budget owned solely by stack_runner; injected clock keeps `LayerBudgetContext` semantics.
- `invariant:` L3 emits `PROVISIONAL_PLACED` + overlay; no `replay/*` import, no L6 commit.
- `invariant:` commit-time latest `route_domain` re-probe; `RouteDomainSnapshotBuilder` sole owner.
- Merge conflict risk if L3 track reopens — keep PR small/fast after gate opens.

## Done criteria

- L3–L6 + stack_runner all in core; no bridge; purity gate clean; behavior identical to master; gates green.

## Status — DONE (2026-05-30, uncommitted on `feat/asteroid-cli-first-l3-stack-move`)

All Steps 0–5 complete; acceptance gate fully checked. L3–L6 + `stack_runner` (+ deferred `service_dtos`,
`layer04_disabled`, `rim_placement`) relocated to pure core with explicit-name shims; `stack_runner` split
Approach A (core returns records, Django writes). Verified: full suite **858 passed / 1 xfailed**, core purity
green (zero `django_apps` exceptions), Django-free subprocess import green, ruff/black/`mypy src` clean,
reconstruction narrow **25 passed**. Per-step spec + code-quality reviews passed. **No commit/push** (awaiting
explicit user request). Env note: worktree runs require `PYTHONPATH=<worktree>/src` (editable install resolves
to the main checkout) — must confirm CI/editable wiring at merge time.
