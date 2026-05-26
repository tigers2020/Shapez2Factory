# Asteroid Lab — RTTP & Catalog Roadmap

**As of:** 2026-05-30  
**Branch:** `master` @ [`f2750c3e`](https://github.com/tigers2020/Shapez2Factory/commit/f2750c3e) + E-track close (local, push pending)  
**Governance:** [`documents/ai/current_plan.md`](../../documents/ai/current_plan.md) § Authority precedence · [`documents/index/document_inventory.md`](../../documents/index/document_inventory.md) § Asteroid Lab authority by topic  
**Queue authority:** [`documents/ai/current_plan.md`](../../documents/ai/current_plan.md)

Living **dual-axis** progress board. Commit links mark `master` merges. **Not algorithm input.**

---

## North Star (canonical algorithm)

```text
Everything is provisional until connected to exterior trunk.
```

RTTP is a **route-feasible placement optimizer**, not a “place many miners” heuristic.

```text
소행성 지형 복원
→ 배치 후보 생성
→ 즉시 route feasibility 확인
→ bundle 조합 선택 (v0.1: greedy-regret; full GA deferred)
→ commit 시점 최신 route_domain으로 재-probe
→ 외부 trunk에 연결된 route만 확정
→ 최종 validation = read-only assert
→ replay/UI = output-only
```

| # | Stage | Algorithm doc | v0.1 gate (tests / code) |
|---|--------|---------------|---------------------------|
| 1 | Decode | import / copy pipeline | ✅ Lab decode path |
| 2 | Reconstruction | `reconstruction/` | ✅ narrow gate [`7a7d426e`](https://github.com/tigers2020/Shapez2Factory/commit/7a7d426e) |
| 3 | Pattern Compiler | `asteroid_lab_02` · `pattern_library` | ✅ `test_rttp_*` patterns |
| 4 | Candidate Generator | `asteroid_lab_03` | ✅ `test_rttp_candidate_generator.py` |
| 5 | Immediate Route Probe | `asteroid_lab_04` | ✅ probe at generation |
| 6 | Candidate Pool | `asteroid_lab_03` | ✅ unreachable excluded from normal pool |
| 7 | Evolutionary Search | `asteroid_lab_05` | 🟡 **greedy-regret** default + optional **evolution** primary ([`2026-05-29-rttp-ga-evolution-design`](specs/2026-05-29-rttp-ga-evolution-design.md) PR-GA-2 **CLOSED** #97 `e43e197b`); macro GA deferred |
| 8 | Incremental Commit | `asteroid_lab_07` | ✅ `test_rttp_commit.py` (`test_commit_reprobes_latest_domain`) |
| 9 | Reservation / Trunk | commit + trunk merge | ✅ `test_rttp_existing_trunk.py` |
| 10 | Validation | `asteroid_lab_08` · ADR-003 | ✅ read-only core; catalog footprint D+ PR-1..PR-3 closed |
| 11 | Replay / UI | `asteroid_lab_09` · 3B-S | ✅ output-only; no replay-as-input |

**Catalog arc** (Axis A below) feeds steps **3–4** and future step **10** footprint checks; it does **not** replace steps **5–9**.

---

## Progress at a glance (two axes)

```text
Axis A — Catalog input canon (game_data → RTTP consumption)
[████████████████████████]  ✅     (D+ PR-1 ✅; PR-2 ✅; PR-3 ✅)

Axis B — RTTP core closure (route-feasible commit end-to-end)
[████████████████████████]  ✅     (B-CS1–B-CS4 formal milestones CLOSED; standing narrow gate)

Parallel — MacroBundle T3
[██████████████████████]  ✅ CLOSED · ⏸ PAUSE (not core 11-step)
```

| Axis | Open next | Blocks |
|------|-----------|--------|
| **A** | PR-GA-2 **CLOSED** [#97](https://github.com/tigers2020/Shapez2Factory/pull/97) `e43e197b`. **CC-3B ops tier CLOSED** [`2026-05-30-rttp-ops-authority-tier-design`](specs/2026-05-30-rttp-ops-authority-tier-design.md) `32c55473`. **E T1b investigation CLOSED** (primary **FL-06**) [`2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design`](specs/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md). **Next:** FL-06 output-stub / route-reservation alignment fix spec → **D** throughput (after T1b) → A/B pass-capable slug; macro child-pool optional. | — |
| **A (D+)** | — (D+ PR-1..PR-3 closed) | — |
| **B** | Standing gates: reconstruction narrow + PR-B optimization contamination; FOT PR-1/2 + cross-commit hotfix on `master` | — |
| **Decontamination** | — (PR-A..E **CLOSED** on `master`) | — |
| **Parallel** | None (paused) | macro child-pool fixture spec before unpause |

### Decontamination — PR-B (optimization import canon) — master CLOSED

| Step | Status | Evidence |
|------|--------|----------|
| PR-B AST import + token gates | ✅ | [`e56ff048`](https://github.com/tigers2020/Shapez2Factory/commit/e56ff048) PR #69 |
| Milestone substring test absorbed | ✅ | removed `test_optimization_milestone_import_boundary.py` |
| Standing gate | ✅ | `scripts/test_optimization_contamination.ps1` |
| Spec | ✅ | [`2026-05-24-decontamination-pr-b-optimization-gates-design.md`](specs/2026-05-24-decontamination-pr-b-optimization-gates-design.md) |

### Decontamination — PR-D (quarantine / stale path isolation) — master CLOSED

| Step | Status | Evidence |
|------|--------|----------|
| Two-tier registry + bounded active-root gate | ✅ | [`08320666`](https://github.com/tigers2020/Shapez2Factory/commit/08320666) PR #70 |
| Plans snapshot `do_not_use_as_authority` | ✅ | `documents/plans/asteroid_lab_optimization/` |
| PR-E candidates declared (not deleted) | ✅ | `PR_E_DELETE_CANDIDATES` in `quarantine_registry.py` |
| Standing gate | ✅ | `scripts/test_quarantine_registry.ps1` |
| Spec | ✅ | [`2026-05-24-decontamination-pr-d-quarantine-design.md`](specs/2026-05-24-decontamination-pr-d-quarantine-design.md) |

### Decontamination — PR-E (dead code deletion) — master CLOSED

| Step | Status | Evidence |
|------|--------|----------|
| Applied-only registry (`PrEDeleteCandidate`, `replacements` tuple) | ✅ | [`64a8fee9`](https://github.com/tigers2020/Shapez2Factory/commit/64a8fee9) PR #71 |
| E-1/E-2 file deletion + E-3 pytest node removal | ✅ | 3 `PR_E_APPLIED_DELETIONS` records |
| Quarantine gate applied-only (9 tests) | ✅ | `scripts/test_quarantine_registry.ps1` |
| Collection delta documented | ✅ | 1493→1495 (deletions −2, gate +4; report) |
| Spec | ✅ | [`2026-05-24-decontamination-pr-e-dead-code-design.md`](specs/2026-05-24-decontamination-pr-e-dead-code-design.md) |

**Open next:** **FL-06** output-stub / route-reservation alignment fix spec (recommended) → **D** T2 throughput policy (after T1b resolved) → **A/B** pass-capable ops slug ([`2026-05-30-rttp-ops-authority-tier-design`](specs/2026-05-30-rttp-ops-authority-tier-design.md) §9). **E** T1b investigation **CLOSED** — primary FL-06; report [`2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report`](reports/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report.md). Diagnostic canon: `copy-import-495e552c` (T0/T1a pass; T1b FL-06; not T3). PR-GA-2 **CLOSED** [#97](https://github.com/tigers2020/Shapez2Factory/pull/97) `e43e197b`. CC-3B ops tier **CLOSED** `32c55473`. Macro **PAUSED**. See [`current_plan.md`](../../documents/ai/current_plan.md).

### Roadmap drift cleanup — tombstone plans (PR #90) — master CLOSED

| Item | Status | Evidence |
|------|--------|----------|
| STALE capacity plan → `OBSOLETE / DO NOT EXECUTE` | ✅ | [`64d90603`](https://github.com/tigers2020/Shapez2Factory/commit/64d90603) PR [#90](https://github.com/tigers2020/Shapez2Factory/pull/90) |
| Macro v1 plan → `PAUSED / DO NOT EXECUTE` | ✅ | same |
| Replacement for capacity C-GATE | — | [`2026-05-26-reconstruction-complete-map-dto.md`](plans/2026-05-26-reconstruction-complete-map-dto.md) + fresh spec before ACTIVE row |

### Post-2026-05-24 — Axis B addenda (merged on `master`)

| Slice | Status | PR / commit |
|-------|--------|-------------|
| FOT outside mineable PR-1 | ✅ | [#88](https://github.com/tigers2020/Shapez2Factory/pull/88) [`ebde4c2c`](https://github.com/tigers2020/Shapez2Factory/commit/ebde4c2c) |
| FOT outward rim / void probe PR-2 | ✅ | [#89](https://github.com/tigers2020/Shapez2Factory/pull/89) [`75c5ad08`](https://github.com/tigers2020/Shapez2Factory/commit/75c5ad08) |
| FOT cross-commit hotfix (PR1.5) | ✅ | [`04bf7b4f`](https://github.com/tigers2020/Shapez2Factory/commit/04bf7b4f) |
| Reconstruction complete-map + replay footprint | ✅ | [#83](https://github.com/tigers2020/Shapez2Factory/pull/83) [`7d07394b`](https://github.com/tigers2020/Shapez2Factory/commit/7d07394b) |

### Deferred commit retry — PR-1 shadow (observe-only) — master CLOSED

| Step | Status | Evidence |
|------|--------|----------|
| Spec | ✅ | [`2026-05-24-deferred-commit-retry-shadow-pr1-design.md`](specs/2026-05-24-deferred-commit-retry-shadow-pr1-design.md) |
| Plan | ✅ | [`2026-05-24-deferred-commit-retry-shadow-pr1.md`](plans/2026-05-24-deferred-commit-retry-shadow-pr1.md) |
| Pure builder + pipeline step `rttp.deferred_commit_retry_shadow` | ✅ | [`1e021f20`](https://github.com/tigers2020/Shapez2Factory/commit/1e021f20) PR #72 |
| PR-2 policy DTO wiring / no-op | ✅ | [`a5cfca87`](https://github.com/tigers2020/Shapez2Factory/commit/a5cfca87) PR #73 |
| PR-3 bounded execution | ✅ | [`d3de9645`](https://github.com/tigers2020/Shapez2Factory/commit/d3de9645) PR #75 |
| PR-4 ops smoke | ✅ | [`64473a87`](https://github.com/tigers2020/Shapez2Factory/commit/64473a87) PR #76; ops `solver_run_id` 57 |

**Deferred commit retry slice 1–4:** **CLOSED** on `master` (2026-05-24).

**Commit survivability arc (v0.1 scope):** **CLOSED** — primary commit + observe-only shadow + runtime policy + bounded execute + real-map ops smoke are all on `master`. Full GA, macro unpause, capacity C-GATE, and multi-round retry remain **future governance tracks** (not implicit).

---

## Axis B — RTTP core (11-step closure)

**Design authority:** [`2026-05-22-rttp-hybrid-c-layout-design.md`](specs/2026-05-22-rttp-hybrid-c-layout-design.md) · [`documents/Algorithm/asteroid_lab_00_overview.md`](../../documents/Algorithm/asteroid_lab_00_overview.md)

### B0 — Runtime shell (config-gated entry)

| Step | Status | Commit / evidence |
|------|--------|-------------------|
| RTTP Hybrid C package on `master` | ✅ | [`docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md`](specs/2026-05-22-rttp-hybrid-c-layout-design.md) |
| `solver_runtime_entry` + `ASTEROID_LAB_RTTP_ENABLED` | ✅ | [`current_plan.md`](../../documents/ai/current_plan.md) |
| Strip-solver → recon-only baseline | ✅ | [`2026-05-22-strip-solver-keep-recon-complete-design.md`](specs/2026-05-22-strip-solver-keep-recon-complete-design.md) |

### B1–B6 — Steps 1–6 (decode → pool)

| Step | Status | Regression |
|------|--------|------------|
| 1–2 Decode + reconstruction | ✅ | `scripts/test_reconstruction_narrow.ps1` |
| 3–6 Pattern → probe → pool | ✅ | `python -m pytest tests/unit/asteroid_lab/ -k rttp -v` (excl. macro_real_map if paused) |

### B7 — Step 7 (selection)

| Step | Status | Note |
|------|--------|------|
| Greedy-regret `PlacementGenome` (default) | ✅ | `test_rttp_greedy_regret.py` |
| Bounded evolution primary (`selection.mode=evolution`) | ✅ | PR-GA-2 [#97](https://github.com/tigers2020/Shapez2Factory/pull/97) `e43e197b`; `test_rttp_ga_evolution_pr_ga_2.py` |
| Macro pipeline GA / full Seq 4–5 | ⏸ deferred | New spec + board section required |

### B8–B9 — Steps 8–9 (commit + trunk)

| Step | Status | Commit / test |
|------|--------|---------------|
| Incremental commit + **re-probe** | ✅ | `test_rttp_commit.py` |
| LNS repair on failure | ✅ | `test_rttp_lns.py` |
| Existing trunk / route domain | ✅ | `test_rttp_existing_trunk.py` · B2-T3 [`38042eed`](https://github.com/tigers2020/Shapez2Factory/commit/38042eed) |

**Invariant:** candidate-time `reachable` is **not** commit success proof — commit always uses latest `route_domain` snapshot.

### B10 — Step 10 (validation)

| Step | Status | Note |
|------|--------|------|
| Read-only final layout assert | ✅ | pipeline `validate_final_layout` |
| Catalog placement audit (observe) | ✅ | D+ PR-1 [`3208f67e`](https://github.com/tigers2020/Shapez2Factory/commit/3208f67e); Ops E3 CLOSED (solver_run_id 49) |
| Catalog fail-closed (mapped only) | ✅ | D+ PR-2 worktree 2026-05-24; Ops E4 `solver_run_id` 51 |

### B11 — Step 11 (replay / UI)

| Step | Status | Note |
|------|--------|------|
| Replay sink output-only | ✅ | `test_rttp_replay_*.py` |
| 3B-S product timeline | ✅ | `lab_rttp_snapshot_compose` |

### B-CS — Core closure milestones

| ID | Milestone | Status | Evidence |
|----|-----------|--------|----------|
| B-CS1 | Commit survivability regression pack | ✅ | `tests/unit/asteroid_lab/test_rttp_commit_survivability.py` |
| B-CS2 | Ops smoke — trunk-connected commit on real slug | ✅ | `solver_run_id` 55; `run_key` `rttp-3afe34cb62c4`; spec [`2026-05-24-b-cs2-trunk-ops-smoke-design.md`](specs/2026-05-24-b-cs2-trunk-ops-smoke-design.md) |
| B-CS3 | Validation gate audit (no repair in validation) | ✅ | `test_b_cs3_validation_gate_boundary.py`; spec [`2026-05-24-b-cs3-validation-gate-audit-design.md`](specs/2026-05-24-b-cs3-validation-gate-audit-design.md) |
| B-CS4 | Reconstruction / Lab replay boundary audit | ✅ | `test_b_cs4_reconstruction_replay_boundary.py`; spec [`2026-05-24-b-cs4-reconstruction-replay-boundary-design.md`](specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md); standing owner: `scripts/test_reconstruction_narrow.ps1` |

---

## Parallel — MacroBundle T3 (not Axis B)

**Goal:** Macro-only pipeline branch for v1 experiments. **PAUSED** — no new macro/E2E.

| Step | Status | Commit |
|------|--------|--------|
| PR-A..J macro pipeline | ✅ | e.g. [`61af24b0`](https://github.com/tigers2020/Shapez2Factory/commit/61af24b0) … [`2fa55aac`](https://github.com/tigers2020/Shapez2Factory/commit/2fa55aac) |
| PR-K/L web + Lab UI | ✅ | [`129d067e`](https://github.com/tigers2020/Shapez2Factory/commit/129d067e) · [`5b06d705`](https://github.com/tigers2020/Shapez2Factory/commit/5b06d705) |
| CI macro smoke + CLI | ✅ | [`c8b5dc76`](https://github.com/tigers2020/Shapez2Factory/commit/c8b5dc76) · [`82c86ca3`](https://github.com/tigers2020/Shapez2Factory/commit/82c86ca3) |
| Real-map macro E2E | ✅ | [`3c9fae42`](https://github.com/tigers2020/Shapez2Factory/commit/3c9fae42) |
| Pause declared | ⏸ | [`0178435e`](https://github.com/tigers2020/Shapez2Factory/commit/0178435e) |
| v1 implementation plan tombstoned | ⏸ | PR [#90](https://github.com/tigers2020/Shapez2Factory/pull/90) — [`2026-05-23-rttp-v1-macrobundle-t3.md`](plans/2026-05-23-rttp-v1-macrobundle-t3.md) **PAUSED / DO NOT EXECUTE** |

---

## Axis A — Catalog input canon

**Purpose:** Replace synthetic `lin_*` candidate geometry with **game_data-native** catalog footprints.  
**Does not close** RTTP core (Axis B) by itself.

**Centerline:**

```text
Catalog-native geometry → route feasibility inputs → (later) commit survivability hardening
```

### A0 — Reconstruction gate (feeds step 2)

| Step | Status | Commit |
|------|--------|--------|
| Replay / topology narrow gate | ✅ | [`7a7d426e`](https://github.com/tigers2020/Shapez2Factory/commit/7a7d426e) |
| Island bbox only | ✅ | [`8c98de84`](https://github.com/tigers2020/Shapez2Factory/commit/8c98de84) |

### A1 — Track A: Provenance gate

| Step | Status | Commit |
|------|--------|--------|
| Runtime provenance enforcement | ✅ | [`0a73eec3`](https://github.com/tigers2020/Shapez2Factory/commit/0a73eec3) |
| Master integration | ✅ | [`1c4baecd`](https://github.com/tigers2020/Shapez2Factory/commit/1c4baecd) · PR #57 |

### A2 — Track B2: Slice → transport → route domain

**Plan:** [`2026-05-24-building-catalog-slice-first-consumption.md`](plans/2026-05-24-building-catalog-slice-first-consumption.md)

| Step | Status | Commit / PR |
|------|--------|-------------|
| `BuildingCatalogSlice` + hash | ✅ | [`62ae2a17`](https://github.com/tigers2020/Shapez2Factory/commit/62ae2a17) · [`72029f52`](https://github.com/tigers2020/Shapez2Factory/commit/72029f52) |
| Provenance v2 | ✅ | [`83f14561`](https://github.com/tigers2020/Shapez2Factory/commit/83f14561) |
| T1 RTTP consumes slice | ✅ | [`b575c175`](https://github.com/tigers2020/Shapez2Factory/commit/b575c175) |
| Per-cell transport (#60) | ✅ | [`493e72c3`](https://github.com/tigers2020/Shapez2Factory/commit/493e72c3) |
| B2-T2 (#62) | ✅ | [`94027496`](https://github.com/tigers2020/Shapez2Factory/commit/94027496) |
| B2-T3 route domain (#61) | ✅ | [`38042eed`](https://github.com/tigers2020/Shapez2Factory/commit/38042eed) |

### A3 — Track D: Footprint & connector v2

| Step | Status | Commit / PR |
|------|--------|-------------|
| Slice v2 geometries + metrics | ✅ | [`f781d7df`](https://github.com/tigers2020/Shapez2Factory/commit/f781d7df) · **PR #63** |
| Plan close | ✅ | [`182b1e20`](https://github.com/tigers2020/Shapez2Factory/commit/182b1e20) |

### A4 — PR-A: Doc authority repair

| Step | Status | Commit / PR |
|------|--------|-------------|
| Contamination policy + inventory | ✅ | [`cd364b84`](https://github.com/tigers2020/Shapez2Factory/commit/cd364b84) · **PR #64** |
| Plan close | ✅ | [`c20fc1e5`](https://github.com/tigers2020/Shapez2Factory/commit/c20fc1e5) |

### A5 — Track D+ PR-1: Observe-only placement audit

**Spec:** [`2026-05-24-track-d-plus-catalog-placement-validation-design.md`](specs/2026-05-24-track-d-plus-catalog-placement-validation-design.md)  
**Plan:** [`2026-05-24-track-d-plus-pr1-catalog-placement-audit.md`](plans/2026-05-24-track-d-plus-pr1-catalog-placement-audit.md)

| Task | Status | Commit |
|------|--------|--------|
| Contracts + transform + audit | ✅ | [`3208f67e`](https://github.com/tigers2020/Shapez2Factory/commit/3208f67e) |
| Pipeline step `rttp.catalog_placement_validation` | ✅ | same |
| Pytest taxonomy (E3 fixtures) | ✅ | same |
| Ops smoke E3 (real slug) | ✅ | `solver_run_id` 49; `config_json.solver_summary`: `rttp.catalog_placement_validation`, `observe_only`, `validation_passed`/`run_success` true |
| Close in `current_plan` | ✅ | PR-1 CLOSED |

**PR-1 contract:** must **not** change `validation_passed`, selection, fitness, macro, or replay semantics.

### A6 — Track D+ PR-2: Fail-closed (mapped candidates)

**Plan:** [`2026-05-24-track-d-plus-pr2-catalog-placement-validation.md`](plans/2026-05-24-track-d-plus-pr2-catalog-placement-validation.md) — **CLOSED** (merged `d676286f`, PR #65)

| Step | Status | Evidence |
|------|--------|----------|
| `CatalogValidationResult` + `CatalogPlacementIssueRow` | ✅ | `contracts/catalog_validation.py`, shared classification |
| Mapped ref + ERROR → `validation_passed=false` | ✅ | `test_catalog_placement_validation.py` |
| Unmapped synthetic → WARNING only | ✅ | pipeline + unit tests |
| Pipeline AND + runtime `issue_codes` | ✅ | Task 3 + 3.5; Ops E4 |
| Read-only AST guards | ✅ | `test_validation_readonly_guards.py` |
| B-CS1 prerequisite regression | ✅ | `test_rttp_commit_survivability.py` (restored for gate) |

### A7 — Track D+ PR-3: Catalog-native generator

**Plan:** [`2026-05-24-track-d-plus-pr3-catalog-native-generator.md`](plans/2026-05-24-track-d-plus-pr3-catalog-native-generator.md) — **CLOSED** (merged `dfbda7b8`, PR #66)

| Step | Status | Evidence |
|------|--------|----------|
| Production `catalog_placement_ref` on all normal candidates | ✅ | `candidate_generator.py` + unit/arch tests |
| `build_catalog_placement_specs` from slice | ✅ | adapters + placements tests |
| `lin_*` / `build_pattern_library` test-only | ✅ | `pattern_library` docstring + `synthetic_lin_patterns` marker |
| Ops smoke E5 (real slug) | ✅ | `solver_run_id` 54; `normal_count` 127; `unmapped_candidate_count` 0 |

**Axis A:** **CLOSED** (A5 Ops E3 + A6 + A7 done, 2026-05-24).

---

## Ops smoke index (`copy-import-495e552c`)

| Smoke | Axis | Status |
|-------|------|--------|
| A | A2 provenance v2 | ✅ |
| B | A2 B2-T2 transport | ✅ |
| C | A2 B2-T3 route domain | ✅ |
| D | A3 Track D `rttp.catalog_slice` | ✅ |
| **E3** | **A5 D+ placement audit (observe_only)** | **✅ CLOSED** | `solver_run_id` 49 |
| **E4** | **A6 D+ mapped fail-closed** | **✅ CLOSED** | `solver_run_id` 51; `mapped_fail_closed`; warning-only `issue_codes` `[]` |
| **E5** | **A7 D+ catalog-native generator** | **✅ CLOSED** | `solver_run_id` 54; `normal_count` 127; `unmapped_candidate_count` 0 |
| **B-CS2** | **Axis B trunk-connected commit (real slug)** | **✅ CLOSED** | `solver_run_id` 55; `confirmed_count` 1; `skeleton_id` present; `mismatched_existing_transport_count` 0 |

---

## Verification commands

**RTTP core (Axis B):**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v
```

**Catalog / D+ (Axis A):**

```powershell
python -m pytest tests/unit/architecture/test_catalog_consumption_boundaries.py -v
python -m ruff check django_apps/asteroid_lab/contracts django_apps/asteroid_lab/adapters django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/optimization/rttp_solver_summary.py
```

**Reconstruction (step 2):**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

**PR-B optimization contamination (decontamination):**

```powershell
powershell -File scripts/test_optimization_contamination.ps1
```

---

## Document map

| Order | Document |
|-------|----------|
| 1 | **This roadmap** — dual-axis commits + 11-step index |
| 2 | [`documents/ai/current_plan.md`](../../documents/ai/current_plan.md) § Authority precedence — queue + closure rules |
| 3 | [`documents/ai/current_plan.md`](../../documents/ai/current_plan.md) — active queue |
| 4 | Topic specs / plans under `docs/superpowers/` |
| 5 | [`documents/Algorithm/asteroid_lab_*.md`](../../documents/Algorithm/) — phase contracts |

---

## Maintenance

1. **Never** merge Axis A % into Axis B %.
2. When merging to `master`, add SHA to the relevant Axis table.
3. New work must declare axis: **A** (catalog), **B** (core), or **Parallel** (macro).
4. Promoting full GA (step 7) requires new spec + new board section — not implicit.
