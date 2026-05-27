# P1-ELCP-RF-B1 — Greedy-Regret Overlap Packing — Design Spec

**Date:** 2026-05-27  
**Status:** Approved for planning (2026-05-27 — design review with Selection Policy Architect)  
**Document type:** Selection policy B-spec (Layer 1 implementation)  
**Work classification:** contract change · implementation change  
**Parent (REOPENED):** [`2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md`](2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md)  
**Prerequisite (CLOSED):** [`2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-design.md`](2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-design.md) · report [`../reports/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-report.md`](../reports/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-report.md)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Implementation plan:** [`../plans/2026-05-27-rttp-elcp-rf-b1-overlap-packing.md`](../plans/2026-05-27-rttp-elcp-rf-b1-overlap-packing.md)

**Korean title (reference):** RTTP greedy-regret overlap packing selection policy (B-spec)

---

## §1 — Executive summary

**A2 (CLOSED)** proved Layer 1 attrition on Gate A (`rttp-core-recovery-test-map`, parity config):

```text
356 normal → 59 commit_order (pool_exhausted, goal=467)
297/297 non-selected = removed_by_overlap; FOT attrition = 0
```

**B1 sole question (Layer 1 — selection only):**

```text
Can we increase commit_order_len by meaningful overlap-graph packing
without changing commit-time ELCP policy?
```

**Explicitly NOT B1:**

```text
Why does commit_order_len=59 become primary_committed_count=3?
lane_capacity_shortfall / fill-first commit fixes
Changing placement_target_percent or hard-coding placement_goal_count
59 → 60 noise improvements as acceptance
```

**Acceptance model:** `D → B + C`

1. **Phase 0 (D):** Overlap graph packing bounds on Gate A normal pool (mandatory diagnostic).
2. **Phase 1 (B):** D-derived `target_floor` on Gate A for new selection mode.
3. **Phase C (always):** Frozen slug regression guards; default selection unchanged.

**Blocked (unchanged from A2):** `lane_capacity_shortfall` B-spec for P1-ELCP-RF program.

---

## §2 — Evidence anchor (frozen from A2)

| Metric | Value | B1 role |
|--------|------:|---------|
| `normal_candidate_count` | 356 | Overlap graph vertex set |
| `commit_order_len` (baseline `GREEDY_REGRET`) | 59 | `greedy_regret_baseline` |
| `placement_goal_count` | 467 | `goal_count` input (unchanged) |
| `removed_by_overlap` (attrition) | 297 | Confirms overlap graph is primary lever |
| `removed_by_fot` | 0 | FOT edges optional in Phase 0 appendix only |
| `stop_reason` | `pool_exhausted` | Baseline greedy terminates on empty pool |

**Precedence:** Gate A parity config (P1-ELCP-RF RF.1), same replay path as A2 investigation tests.

---

## §3 — Non-goals

| Forbidden in B1 | Owner |
|-----------------|-------|
| Commit-time ELCP assignment / reprobe / fill-first policy | P1-ELCP-RF Layer 2 |
| `lane_capacity_shortfall` B-spec | Blocked until separate re-gate |
| Changing `RouteProbeResult` semantics or `CommitConflictReason` enum | Commit layer |
| Consuming Phase 0 report JSON / replay artifacts as runtime solver input | Forbidden shortcut |
| Silent global replacement of `GREEDY_REGRET` default | Rollout §7 |
| Acceptance = `commit_order_len > 59` only | Too weak (noise) |
| Candidate generation / pattern library changes | Separate track if Phase 0 NO-GO |

---

## §4 — Rollout contract (`SelectionMode`)

### §4.1 Enum extension

Add to [`selection_mode.py`](../../../django_apps/asteroid_lab/contracts/selection_mode.py):

```text
SelectionMode.GREEDY_REGRET                 # existing default — unchanged behavior
SelectionMode.GREEDY_REGRET_OVERLAP_PACK    # B1 opt-in packing mode
```

### §4.2 Default invariant

```text
RttpPipelineConfig.selection_mode default remains GREEDY_REGRET.
B1 must not silently replace global selection behavior.
```

### §4.3 Opt-in evaluation

```text
GREEDY_REGRET_OVERLAP_PACK is initially opt-in (pipeline config / run_solver flag).
Gate A + frozen slug guards must pass before any default promotion discussion.
```

### §4.4 Dispatch

[`primary_genome.py`](../../../django_apps/asteroid_lab/optimization/selection/primary_genome.py) dispatches:

| Mode | Implementation |
|------|----------------|
| `GREEDY_REGRET` | Existing `select_genome` (unchanged) |
| `EVOLUTION` | Existing `select_genome_evolution` (unchanged) |
| `GREEDY_REGRET_OVERLAP_PACK` | New `select_genome_overlap_pack` (or equivalent) in `selection/overlap_pack.py` |

**Contract updates required:** `SelectionMode` enum tests, `solver_runtime_entry` allowlist for run config `mode` string, `run_solver` choices/help text if exposed.

---

## §5 — Phase 0: Overlap graph diagnostic (mandatory gate)

### §5.1 Purpose

Establish packing **upper/lower bounds** before Phase 1 targets or algorithm choice.

### §5.2 Graph definition

**Vertices:** normal candidates after `dedupe_candidates` (same universe as `select_genome`).

**Edge (undirected):** candidates A, B are adjacent iff:

```text
occupied_cells(A) ∩ occupied_cells(B) ≠ ∅
```

**FOT:** Not part of primary graph on Gate A (FOT attrition = 0 in A2). Phase 0 report MAY include optional `fot_conflict_edge_count` as appendix only.

### §5.3 Required report fields

| Field | Type | Required |
|-------|------|----------|
| `vertex_count` | int | yes (expect 356 on Gate A) |
| `edge_count` | int | yes |
| `connected_component_count` | int | yes |
| `greedy_regret_baseline` | int | yes (production `GREEDY_REGRET` `len(commit_order)`) |
| `best_known_independent_set_size` | int | yes |
| `exact_mis_size` | int \| null | per-component exact when tractable; null if skipped |
| `upper_bound` | int \| null | sum per-component MIS upper bounds; `component_exact` only if all exact |
| `chromatic_upper_bound_sum` | int | diagnostic (greedy coloring; bounds χ, not \|MIS\|) |
| `component_sizes` | list[int] | yes (sorted descending) |
| `exact_mis_component_count` | int | components solved exactly |
| `heuristic_mis_component_count` | int | components solved heuristically only |

### §5.4 Algorithms (deterministic)

**Module:** `harness/investigation/rttp_overlap_graph_packing_bounds.py` (read-only; mirrors candidate pool from Gate A replay).

| Step | Rule |
|------|------|
| Build graph | O(n²) pair check on `occupied_cells`; n ≤ 356 on Gate A |
| Per component | If `|V| ≤ 40`: exact MIS (branch-and-bound or Bron–Kerbosch on conflict graph) |
| Large component | Deterministic heuristic MIS: e.g. min-degree removal order, tie-break by `candidate_id` lexicographic |
| `best_known_independent_set_size` | Sum of per-component independent set sizes |
| `upper_bound` | When any component uses heuristic only: `vertex_count` (trivial) or documented bound; report MUST state method |

**Determinism:** Same candidate pool + same config → identical report fields (no randomness).

### §5.5 Artifact boundary (normative)

```text
Overlap graph diagnostic output is report/test evidence only.
Runtime selection MUST rebuild the graph from the live candidate pool.
Runtime selection MUST NOT consume report JSON, JSONL replay, or investigation artifacts.
```

### §5.6 Phase 0 early-exit matrix

| Condition | B1 program decision |
|-----------|---------------------|
| `best_known_independent_set_size ≤ greedy_regret_baseline + 5` | **NO-GO** — selection packing not viable on Gate A; escalate to candidate generation / pattern diversity (document in report) |
| `best_known_independent_set_size` in (64, 99) | Proceed; Phase 1 `target_floor = best_known_independent_set_size` |
| `best_known_independent_set_size ≥ 100` | Proceed; Phase 1 uses formula §6.2 |

### §5.7 Phase 0 acceptance checklist

- [ ] **B1.0.1** Gate A replay produces overlap graph report with all §5.3 fields
- [ ] **B1.0.2** `greedy_regret_baseline == 59` on frozen Gate A config
- [ ] **B1.0.3** `vertex_count == 356`
- [ ] **B1.0.4** Phase 0 report published (investigation report section or dedicated report file)
- [ ] **B1.0.5** No production pipeline default change

---

## §6 — Phase 1: Implementation acceptance (D-derived)

### §6.1 Goal

```text
new_commit_order_len >= target_floor
```

on Gate A when `selection_mode == GREEDY_REGRET_OVERLAP_PACK`, with `goal_count` unchanged (467).

**Rejected acceptance:**

```text
new_commit_order_len > 59   # insufficient — noise
new_commit_order_len == 60  # explicitly not product-grade
```

### §6.2 `target_floor` formula

After Phase 0, compute:

```text
if best_known_independent_set_size < 100:
    target_floor = best_known_independent_set_size
else:
    target_floor = max(100, floor(0.50 * best_known_independent_set_size))
```

**Stretch (non-blocking, report only):** `floor(0.70 * best_known_independent_set_size)`.

### §6.3 Implementation approach (phased)

**Primary: B1-B-lite** (`selection/overlap_pack.py`)

| Function | Responsibility |
|----------|----------------|
| `build_overlap_graph(candidates)` | Adjacency from `occupied_cells` intersection |
| `compute_best_known_independent_set(...)` | Component split + exact/heuristic MIS (§5.4) |
| `order_independent_set_by_weight(...)` | Order picked IDs by `_base_score` (reuse greedy_regret scoring helpers) |
| `build_overlap_pack_commit_order(...)` | Emit `PlacementGenome.commit_order` up to `goal_count` |

**Secondary (if B1-B-lite below `target_floor` on Gate A):**

- **B1-A:** Spatial diversity tie-break inside greedy rounds (anchor/region spread).
- **B1-C:** One-pass local swap/repair after initial pack (deterministic; no commit calls).

**Selection order for implementation plan:**

```text
Phase 0 (D) → B1-B-lite → (optional) B1-A tie-break → (optional) B1-C 1-pass repair
```

### §6.4 Overlap-pack selection semantics

`GREEDY_REGRET_OVERLAP_PACK` MUST:

1. Call `dedupe_candidates` (same as greedy_regret).
2. Build overlap graph from deduped pool.
3. Compute independent set (best-known / exact per component rules).
4. Order selected candidates by weighted score (throughput, rim alignment, route cost — reuse `_base_score` / `_priority` where applicable).
5. Truncate or extend to `goal_count`:
   - If `|IS| >= goal_count`: take first `goal_count` by score order.
   - If `|IS| < goal_count`: append additional non-overlapping candidates via deterministic greedy fill on remaining pool (document in plan).

**FOT pruning:** Apply same `_fot_conflict` filters as `select_genome` when extending beyond initial IS (Gate A FOT=0 but contract must match greedy_regret for other slugs).

### §6.5 Phase 1 acceptance checklist

- [ ] **B1.1.1** `GREEDY_REGRET_OVERLAP_PACK` on Gate A: `len(commit_order) >= target_floor`
- [ ] **B1.1.2** `GREEDY_REGRET` default unchanged: Gate A baseline still `commit_order_len == 59`
- [ ] **B1.1.3** A2 trace parity still holds for `GREEDY_REGRET` mode
- [ ] **B1.1.4** Phase 0 report cited in B1 investigation/implementation report with `target_floor` computation shown
- [ ] **B1.1.5** No commit-layer ELCP code changes for B1 closure

---

## §7 — Phase C: Regression guard (mandatory)

### §7.1 Frozen slugs

From [`rttp_recovery_evidence.py`](../../../django_apps/asteroid_lab/contracts/rttp_recovery_evidence.py):

```text
GATE_A_PRIMARY_SLUGS:
  - rttp-core-recovery-test-map
  - rttp-cert-candidate-recon-l0
```

### §7.2 Guard rules

| Guard | Rule |
|-------|------|
| Default mode | `GREEDY_REGRET`: `commit_order_len` **≥** recorded baseline per slug (pre-B1 baseline captured in test constants) |
| New mode | `GREEDY_REGRET_OVERLAP_PACK`: Gate A `>= target_floor`; cert slug `>= GREEDY_REGRET` baseline on same slug |
| Validation | `validation_passed` / transport invariants unchanged for default mode runs |
| Commit | No change to `incremental_commit` ELCP branch behavior |
| Forensics | Phase 0 harness output not wired into `run_rttp_pipeline` |

### §7.3 Frozen test migration

`test_recovery_map_selection_attrition_trace_gate_a_parity_config`:

- `GREEDY_REGRET` assertions remain `== 59` until baseline intentionally versioned.
- Add separate test module for `GREEDY_REGRET_OVERLAP_PACK` with `>= target_floor` (computed in test from Phase 0 harness or frozen constants documented in report).

---

## §8 — Hypotheses (B1)

| ID | Hypothesis | Phase | Proof |
|----|------------|-------|-------|
| **B1-H0** | Overlap graph independent set size ≫ 59 | 0 | `best_known_independent_set_size` report |
| **B1-H1** | Greedy-regret pick order causes early `pool_exhausted` | 0 + A2 trace | `greedy_regret_baseline` vs MIS |
| **B1-H2** | B1-B-lite reaches `target_floor` on Gate A | 1 | Gate A test |
| **B1-H3** | B1-A alone sufficient | 1 | Only if trace shows MIS headroom with order-only fix |
| **B1-H4** | Cert slug does not regress under default mode | C | Slug guard tests |

---

## §9 — Deliverables

| # | Artifact |
|---|----------|
| 1 | This design spec |
| 2 | Plan `2026-05-27-rttp-elcp-rf-b1-overlap-packing.md` *(writing-plans)* |
| 3 | Report `2026-05-27-rttp-elcp-rf-b1-overlap-packing-report.md` *(post Phase 0/1)* |
| 4 | `harness/investigation/rttp_overlap_graph_packing_bounds.py` |
| 5 | `django_apps/asteroid_lab/optimization/selection/overlap_pack.py` |
| 6 | `django_apps/asteroid_lab/contracts/selection_mode.py` (enum) |
| 7 | `django_apps/asteroid_lab/optimization/selection/primary_genome.py` (dispatch) |
| 8 | `tests/investigation/test_rttp_overlap_graph_packing_bounds.py` |
| 9 | `tests/unit/asteroid_lab/test_rttp_b1_overlap_pack_selection.py` (name TBD in plan) |
| 10 | Slug regression tests under `tests/unit/asteroid_lab/` |

---

## §10 — Program status interactions

| Program item | Status after B1 spec approval |
|--------------|-------------------------------|
| P1-ELCP-RF-A2 | **CLOSED** (unchanged) |
| P1-ELCP-RF Layer 2 | **REOPENED** — not in B1 scope |
| `lane_capacity_shortfall` B-spec | **BLOCKED** (unchanged) |
| P1-ELCP-RF-B1 | **ACTIVE** — Phase 0 then Phase 1 |

**B1 does not close P1-ELCP-RF.** Layer 2 (`59 → 3`) remains a separate track after selection reachability improves.

---

## §11 — Spec review record (2026-05-27)

| Check | Result |
|-------|--------|
| Layer 1 only (selection packing) | **PASS** |
| A2 evidence anchor consistent | **PASS** |
| Acceptance D → B + C | **PASS** |
| No `59+1` acceptance | **PASS** |
| `SelectionMode` rollout A | **PASS** |
| Default `GREEDY_REGRET` unchanged | **PASS** |
| Phase 0 artifacts not solver input | **PASS** |
| `lane_capacity_shortfall` blocked | **PASS** |
| Deterministic MIS/heuristic | **PASS** |
| Placeholder / TBD scan | **PASS** |

**Reviewer gate:** User review of written spec → `writing-plans`.

---

## §12 — References

- [`greedy_regret.py`](../../../django_apps/asteroid_lab/optimization/selection/greedy_regret.py)
- [`rttp_greedy_regret_selection_trace.py`](../../../harness/investigation/rttp_greedy_regret_selection_trace.py)
- [`input_contracts.py`](../../../django_apps/asteroid_lab/optimization/input_contracts.py) — `RttpPipelineConfig.selection_mode`
- [`solver_runtime_entry.py`](../../../django_apps/asteroid_lab/services/solver_runtime_entry.py) — run config mode allowlist
- A2 report: [`2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-report.md`](../reports/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-report.md)
