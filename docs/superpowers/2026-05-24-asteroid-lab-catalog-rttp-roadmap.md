# Asteroid Lab — RTTP & Catalog Roadmap

**Roadmap version:** **v0.2** (active) · **v0.1** closed 2026-05-30  
**As of:** 2026-05-30  
**Branch:** `master` @ [`e8138dab`](https://github.com/tigers2020/Shapez2Factory/commit/e8138dab) (PR-F2 close)  
**Governance:** [`documents/ai/current_plan.md`](../../documents/ai/current_plan.md) § Authority precedence · [`documents/index/document_inventory.md`](../../documents/index/document_inventory.md) § Asteroid Lab authority by topic  
**Queue authority:** [`documents/ai/current_plan.md`](../../documents/ai/current_plan.md) — day-to-day NEXT/CLOSED rows

Living **dual-axis** progress board (v0.1) plus **v0.2 governance tracks**. Commit links mark `master` merges. **Not algorithm input.**

---

## Version glossary (do not conflate)

| Label | Meaning | Authority doc |
|-------|---------|-----------------|
| **Roadmap v0.1** | Axis A (catalog canon) + Axis B (RTTP 11-step core) + B-CS formal closure | This file § [v0.1 archive](#v01-archive-closed-2026-05-30) |
| **Roadmap v0.2** | Ops canon, throughput policy observability, test decontamination F-series, standing gates | This file § [v0.2 active](#v02--active-scope) |
| **RTTP replay v0.2** | Replay on/off parity + `:rttp` DB track (2026-05-23) | [`2026-05-23-rttp-v0.2-replay-parity-design.md`](specs/2026-05-23-rttp-v0.2-replay-parity-design.md) — **merged under v0.1 runtime** |

Promoting **macro unpause**, **full GA**, or **product throughput Track A** requires a **new spec + ACTIVE row** in `current_plan.md` — not implicit in v0.2.

---

## v0.2 — Active scope

### Intent

v0.1 proved **route-feasible RTTP + catalog-native candidates** on `master`. v0.2 makes that stack **operable and trustworthy**: explicit ops slugs, diagnostic vs pass-capable contracts, T2 policy in code/summary, and gated test cleanup — **without** reopening core commit/LNS/validation semantics.

### In scope (v0.2 tracks)

| Track | ID | Goal | Close when |
|-------|-----|------|------------|
| **C — Ops & throughput governance** | C1–C4 | T0–T3 ops tier + diagnostic canon + pass-capable reference slug + T2 observability in solver summary | D-PR [#99](https://github.com/tigers2020/Shapez2Factory/pull/99) merged; standing ops doc/spec pointers stable |
| **F — Test decontamination** | F0–F5 | Inventory-driven, registry-gated deletes only | PR-F3..F5 each CLOSED or SKIP with evidence; `scripts/test_quarantine_registry.ps1` green |
| **G — Standing gates** | G1–G4 | Maintenance ownership documented | Reconstruction narrow, optimization contamination, quarantine registry, capacity SoT scripts owned and referenced here |

### Out of scope (explicit electives → v0.3+)

- **Macro unpause** — blocked until **macro child-pool fixture** spec (≤2 `normal_candidates` on 4×4 under `OUTSIDE_MINEABLE` today).
- **Product Track A** — throughput hardening on `recon-l0` / non-diagnostic maps — **not opened** unless product requests.
- **Full GA / macro GA** — beyond config-gated evolution primary (PR-GA-2).
- **PR-1b** route tile synthesis · **PR-2** island materializer (reconstruction deferrals).
- Algorithm changes that weaken validation read-only rules, FOT guards, or replay-as-input forbidden shortcuts.

### v0.2 definition of done

1. **C-track:** D-PR merged; `copy-import-495e552c` remains **diagnostic canon** (T2 shortfall expected); `rttp-cert-candidate-tiny-passable-v2` remains **pass-capable reference** (Lab badge on `master`).
2. **F-track:** PR-F3 (`game_data`) complete; F4/F5 complete or SKIP per inventory; no ungated test deletes.
3. **G-track:** All four standing gate scripts documented below and green on `master` after each merge.
4. **Queue:** `current_plan.md` NEXT points at **v0.3 track selection** (macro / Track A / GA) or states **v0.2 CLOSED** with date.

---

## v0.2 — Progress at a glance

```text
C — Ops & throughput governance
[██████████████████░░░░░░]  ~75%   (tier + slugs + D-GOV ✅; D-PR #99 OPEN)

F — Test decontamination (PR-F series)
[████████████░░░░░░░░░░░░]  ~50%   (F0 ✅ F2 ✅; F3 ACTIVE; F4–F5 READY; F1 SKIP)

G — Standing maintenance gates
[████████████████████████]  ✅     (scripts exist; ownership below)

Parallel — MacroBundle T3
[██████████████████████]  ✅ code · ⏸ PAUSE (not v0.2)
```

### v0.2 work queue (execution order)

Use [`current_plan.md`](../../documents/ai/current_plan.md) for branch names and PR URLs. Order:

| # | Item | Status | Axis / track | Blocker |
|---|------|--------|--------------|---------|
| 1 | **D-PR** — T2 diagnostic canon observability | **OPEN** PR [#99](https://github.com/tigers2020/Shapez2Factory/pull/99) | C | GitHub `ci` green before merge |
| 2 | **PR-F3** — `game_data` human/package review | **NEXT** | F | Plan: [`2026-05-30-test-cleanup-aggressive-decontamination-pr-f.md`](plans/2026-05-30-test-cleanup-aggressive-decontamination-pr-f.md) |
| 3 | **PR-F4** — next package (registry-gated) | READY | F | After F3 |
| 4 | **PR-F5** — final F-series slice | READY | F | After F4 |
| 5 | **v0.3 track selection** | **LATER** (product) | Elective | New spec each: macro unpause · Track A throughput · full GA |

**Do not execute** tombstoned plans: [`2026-05-23-rttp-v1-macrobundle-t3.md`](plans/2026-05-23-rttp-v1-macrobundle-t3.md) (`PAUSED / DO NOT EXECUTE`), stale capacity checklist (PR #90).

---

## v0.2 — Track C (ops & throughput governance)

**Slugs (canon):**

| Role | Slug | T2 expectation |
|------|------|----------------|
| Diagnostic canon | `copy-import-495e552c` | **Expected shortfall** (`throughput_target_shortfall`); not a merge blocker |
| Pass-capable reference | `rttp-cert-candidate-tiny-passable-v2` | Borderline pass (`actual=target=480`); `slug_class=pass_capable` |

| Step | Status | Evidence |
|------|--------|----------|
| C1 — Ops authority tier T0–T3 | ✅ | [`2026-05-30-rttp-ops-authority-tier-design.md`](specs/2026-05-30-rttp-ops-authority-tier-design.md); `master` `32c55473` |
| C2 — Throughput policy design (approach C) | ✅ | D-GOV CLOSED — [`2026-05-30-rttp-throughput-policy-t2-diagnostic-canon-design.md`](specs/2026-05-30-rttp-throughput-policy-t2-diagnostic-canon-design.md) |
| C3 — Pass-capable slug + Lab badge | ✅ | PR [#101](https://github.com/tigers2020/Shapez2Factory/pull/101), [#102](https://github.com/tigers2020/Shapez2Factory/pull/102); reports under `reports/2026-05-30-rttp-pass-capable-*` |
| C4 — T2 diagnostic observability (summary fields) | 🔄 | PR [#99](https://github.com/tigers2020/Shapez2Factory/pull/99); plan [`2026-05-30-rttp-throughput-policy-t2-diagnostic-canon.md`](plans/2026-05-30-rttp-throughput-policy-t2-diagnostic-canon.md) |
| FL-06 output-stub / route-reservation | ✅ | Merged 2026-05-30 — canon T1b PASS (Run 109) |
| GA evolution PR-GA-1 shadow | ✅ | PR [#95](https://github.com/tigers2020/Shapez2Factory/pull/95) |
| GA evolution PR-GA-2 selection primary | ✅ | PR [#97](https://github.com/tigers2020/Shapez2Factory/pull/97) |

**Post–v0.2 elective (Track A):** real-map throughput campaigns on non-diagnostic slugs — **requires new spec**; do not reinterpret diagnostic canon as product FAIL.

---

## v0.2 — Track F (test decontamination)

**Spec:** [`2026-05-30-test-cleanup-aggressive-decontamination-design.md`](specs/2026-05-30-test-cleanup-aggressive-decontamination-design.md)  
**Inventory:** [`reports/2026-05-30-test-decontamination-inventory.md`](reports/2026-05-30-test-decontamination-inventory.md)  
**Gate:** `scripts/test_quarantine_registry.ps1` — deletes only via `PR_F_*` registry.

| Step | Status | Evidence |
|------|--------|----------|
| F0 — Inventory (no deletes) | ✅ | PR #100 `b5aa58fc` |
| F1 — Mechanical auto-delete | **SKIP** | 0 mechanical rows |
| F2 — `asteroid_lab` human review | ✅ | PR-F2; 0 deletions; 2× `PROTECTED_CONTRACT` |
| F3 — `game_data` human review | **ACTIVE** | Branch `feat/decontamination-pr-f3-game-data` |
| F4 — Next package | READY | After F3 |
| F5 — Final F slice | READY | After F4 |

**v0.1 decontamination (already on `master`):** PR-A..E closed — see [v0.1 archive](#decontamination-pr-ae--master-closed).

---

## v0.2 — Track G (standing gates)

| Gate | Owner script | Scope |
|------|--------------|--------|
| G1 — Reconstruction / replay boundary | `scripts/test_reconstruction_narrow.ps1` | B-CS4; **excludes** `test_rttp_replay_*` |
| G2 — Optimization contamination | `scripts/test_optimization_contamination.ps1` | PR-B AST/token gates |
| G3 — Quarantine registry | `scripts/test_quarantine_registry.ps1` | PR-D + PR-F applied deletes |
| G4 — Capacity complete-map SoT | `scripts/test_capacity_sot.ps1` | C-GATE architecture (PR #94); no solver semantics change |

Full PR gate: [`AGENTS.md`](../../AGENTS.md) · `scripts/test_full.ps1`.

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
→ bundle 조합 선택 (default greedy-regret; evolution primary optional)
→ commit 시점 최신 route_domain으로 재-probe
→ 외부 trunk에 연결된 route만 확정
→ 최종 validation = read-only assert
→ replay/UI = output-only
```

| # | Stage | Algorithm doc | v0.1 gate | v0.2 note |
|---|--------|---------------|-----------|-----------|
| 1 | Decode | import / copy pipeline | ✅ | — |
| 2 | Reconstruction | `reconstruction/` | ✅ narrow gate | Capacity C-GATE architecture ✅ |
| 3 | Pattern Compiler | `asteroid_lab_02` · `pattern_library` | ✅ | — |
| 4 | Candidate Generator | `asteroid_lab_03` | ✅ catalog-native | — |
| 5 | Immediate Route Probe | `asteroid_lab_04` | ✅ | — |
| 6 | Candidate Pool | `asteroid_lab_03` | ✅ | — |
| 7 | Evolutionary Search | `asteroid_lab_05` | ✅ greedy + optional evolution | Full GA / macro GA → **v0.3+** |
| 8 | Incremental Commit | `asteroid_lab_07` | ✅ | FL-06 alignment ✅ |
| 9 | Reservation / Trunk | commit + trunk merge | ✅ | — |
| 10 | Validation | `asteroid_lab_08` · ADR-003 | ✅ D+ | — |
| 11 | Replay / UI | `asteroid_lab_09` · 3B-S | ✅ | pass_capable Lab badge ✅ |

**Catalog arc** (v0.1 Axis A) feeds steps **3–4** and step **10**; it does **not** replace steps **5–9**.

---

## v0.3+ electives (not started — pick one with spec)

| Elective | Prerequisite | Why deferred |
|----------|--------------|--------------|
| **Macro unpause** | Macro child-pool fixture spec | 4×4 / narrow-corridor → ≤2 `normal_candidates`; MacroBundleT3 needs ≥3 |
| **Track A product throughput** | Product request + new spec | Diagnostic canon deliberately shortfall-expected |
| **Full GA / macro GA** | New board section + budget/ops gates | PR-GA-2 covers config-gated evolution primary only |
| **PR-1b / PR-2 reconstruction** | Separate reconstruction spec | Deferred from complete-map PR #83 |

---

## v0.1 archive (closed 2026-05-30)

v0.1 **definition:** Catalog input canon (Axis A) + RTTP core 11-step closure (Axis B) + B-CS1–B-CS4 milestones. **Status: CLOSED on `master`.**

```text
Axis A — Catalog input canon
[████████████████████████]  ✅     (D+ PR-1..PR-3; B2; Track D)

Axis B — RTTP core closure
[████████████████████████]  ✅     (B-CS1–B-CS4; standing narrow gate)

Parallel — MacroBundle T3
[██████████████████████]  ✅ CLOSED · ⏸ PAUSE
```

### Post–v0.1 addenda merged before v0.2 board (reference only)

| Slice | Status | PR / commit |
|-------|--------|-------------|
| FOT PR-1 / PR-2 + cross-commit hotfix | ✅ | #88, #89, `04bf7b4f` |
| Reconstruction complete-map + replay footprint | ✅ | #83 `7d07394b` |
| Deferred commit retry PR-1..PR-4 | ✅ | #72–#76 |
| Roadmap drift tombstones | ✅ | #90 `64d90603` |
| Throughput PR-2a–2d | ✅ | #79–#81 |
| Capacity C-GATE (architecture) | ✅ | #94 `ec1b6a26` |

### Decontamination PR-A..E — master CLOSED

| PR | Status | Commit |
|----|--------|--------|
| PR-B optimization gates | ✅ | `e56ff048` #69 |
| PR-D quarantine | ✅ | `08320666` #70 |
| PR-E dead code | ✅ | `64a8fee9` #71 |

Specs: [`2026-05-24-decontamination-pr-b-optimization-gates-design.md`](specs/2026-05-24-decontamination-pr-b-optimization-gates-design.md), [`2026-05-24-decontamination-pr-d-quarantine-design.md`](specs/2026-05-24-decontamination-pr-d-quarantine-design.md), [`2026-05-24-decontamination-pr-e-dead-code-design.md`](specs/2026-05-24-decontamination-pr-e-dead-code-design.md).

### Axis B — RTTP core (11-step) — v0.1 evidence

**Design authority:** [`2026-05-22-rttp-hybrid-c-layout-design.md`](specs/2026-05-22-rttp-hybrid-c-layout-design.md)

| Block | Status | Regression |
|-------|--------|------------|
| B0 runtime shell | ✅ | `ASTEROID_LAB_RTTP_ENABLED` |
| B1–B6 decode → pool | ✅ | `test_reconstruction_narrow.ps1` · `-k rttp` |
| B7 selection | ✅ greedy + evolution | `test_rttp_greedy_regret.py` · `test_rttp_ga_evolution_pr_ga_2.py` |
| B8–B9 commit + trunk | ✅ | `test_rttp_commit.py` · `test_rttp_lns.py` |
| B10 validation | ✅ | D+ PR-1..PR-3 |
| B11 replay / UI | ✅ | `test_rttp_replay_*` · 3B-S compose |
| B-CS1..B-CS4 | ✅ | survivability · ops smoke · B-CS3/4 boundary tests |

### Axis A — Catalog input canon — v0.1 evidence

**Axis A: CLOSED** (2026-05-24). Plans: B2 consumption, Track D, D+ PR-1..PR-3 under `docs/superpowers/plans/2026-05-24-*`.

### Parallel — MacroBundle T3

**PAUSED** — [`2026-05-23-rttp-v1-macrobundle-t3.md`](plans/2026-05-23-rttp-v1-macrobundle-t3.md) tombstoned PR #90. Runtime macro code remains; no new macro/E2E until unpause spec.

---

## Ops smoke index

### v0.1 diagnostic slug (`copy-import-495e552c`)

| Smoke | Axis | Status |
|-------|------|--------|
| A–E5, B-CS2 | A / B | ✅ (see v0.1 archive commits) |

### v0.2 canon slugs

| Slug | Role | Evidence |
|------|------|----------|
| `copy-import-495e552c` | Diagnostic canon | T0/T1a/T1b pass; T2 **expected shortfall** post D-GOV |
| `rttp-cert-candidate-tiny-passable-v2` | Pass-capable reference | PR #101; [`task4-confirm-v2.json`](reports/2026-05-30-rttp-pass-capable-slug-certification-task4-confirm-v2.json) |

---

## Verification commands

**v0.2 C-track (RTTP + policy):**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k rttp
python -m ruff check django_apps/asteroid_lab/optimization django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py django_apps/asteroid_lab/services/solver_runtime_entry.py
```

**v0.2 F-track + G3:**

```powershell
powershell -File scripts/test_quarantine_registry.ps1
```

**v0.1 standing (still required on every RTTP/recon touch):**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
powershell -File scripts/test_optimization_contamination.ps1
powershell -File scripts/test_capacity_sot.ps1
```

**Catalog boundaries (Axis A maintenance):**

```powershell
python -m pytest tests/unit/architecture/test_catalog_consumption_boundaries.py -v
```

---

## Document map

| Order | Document |
|-------|----------|
| 1 | **This roadmap** — v0.2 queue + v0.1 archive |
| 2 | [`documents/ai/current_plan.md`](../../documents/ai/current_plan.md) — ACTIVE/NEXT/CLOSED rows |
| 3 | Topic specs / plans under `docs/superpowers/` |
| 4 | [`documents/Algorithm/asteroid_lab_*.md`](../../documents/Algorithm/) — phase contracts |

---

## Maintenance

1. **Roadmap version:** Update the **v0.2 progress bars** and **work queue** when merging C/F tracks; move closed v0.2 slices to a dated CLOSED table — do not delete v0.1 archive without tombstone.
2. **Never** merge Axis A % into Axis B % (v0.1 rule, still applies).
3. New work must declare: **C** (ops/governance), **F** (decontamination), **G** (gate-only), **v0.1 axis** (A/B), or **Parallel** (macro).
4. Opening **v0.3** requires a short **v0.3 scope** section here + ACTIVE row in `current_plan.md`.
5. Promoting full GA, macro unpause, or Track A throughput requires **new spec** — not implicit from v0.2 %.
