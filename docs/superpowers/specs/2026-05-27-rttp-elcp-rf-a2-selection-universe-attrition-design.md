# P1-ELCP-RF-A2 — Greedy-Regret Selection Universe Attrition — Design Spec

**Date:** 2026-05-27  
**Status:** Approved for planning (2026-05-27 spec review — blockers amended)  
**Document type:** Read-only regression forensics (E-track, **Layer 1 only**)  
**Work classification:** documentation · regression forensics (no production behavior change)  
**Parent (REOPENED):** [`2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md`](2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md) · report [`../reports/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-report.md`](../reports/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-report.md)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Implementation plan:** [`../plans/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition.md`](../plans/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition.md)

**Korean title (reference):** RTTP greedy-regret selection universe attrition forensic 조사

---

## §1 — Executive summary

**P1-ELCP-RF (Layer 2)** decomposed commit-time failures within **`genome.commit_order` (59 attempts)** only. That work is **out of scope** for A2.

**A2 sole question (Layer 1):**

```text
Why does normal_candidate_count=356 become commit_order_len=59
while placement_goal_count=467?
```

**Explicitly NOT A2:**

```text
Why does commit_order_len=59 become primary_committed_count=3?
Why are there 29 REPROBE_FAILED?
```

Those are P1-ELCP-RF Layer 2 (already documented; may appear only in reconciliation tail column).

**Layer model (forensic flow — mechanism TBD until trace):**

```text
9328 candidate_pool_total
  → 356 normal (route-feasible at generation)
  → 59 commit_order (greedy-regret output — attrition cause: PROVE via round trace)
  → 3 primary committed (Layer 2 — context only, not analyzed in A2)
  → 29 REPROBE_FAILED (Layer 2 — context only, not analyzed in A2)
```

**Placement goal scaling (product rule — verified in A2.1, not hard-coded):**

```text
placement_goal_count = compute_placement_goal_count(
    asteroid_field_cell_count,
    placement_target_percent,
)
```

Recovery map anchor: **583** field cells × **80%** → **467** `placement_goal_count`.  
**59** is observed `commit_order_len`, **not** `placement_goal_count`.

**B-spec:** `lane_capacity_shortfall` remains **BLOCKED** for entire P1-ELCP-RF program until A2 closes and re-gate runs.

---

## §2 — Evidence anchor (frozen from P1-ELCP-RF Task 9)

| Metric | Value | A2 role |
|--------|------:|---------|
| `asteroid_field_cell_count` | 583 | goal scaling input |
| `placement_goal_count` | 467 | `select_genome` `goal_count` (verify propagation) |
| `normal_candidate_count` | 356 | attrition universe **in** |
| `rejected_candidate_count` | 8972 | generation context only |
| `commit_order_len` | 59 | attrition universe **out** |
| `primary_committed_count` | 3 | reconciliation column only |
| `primary_reprobe_failed_count` | 29 | **not** A2 taxonomy input |

**Precedence:** Post-fix recovery-map replay (Gate A parity config).

---

## §3 — Non-goals

| Forbidden in A2 | Owner |
|-----------------|-------|
| Primary commit failure taxonomy (`59 → 3`, `REPROBE_FAILED`) | P1-ELCP-RF Layer 2 |
| `lane_capacity_shortfall` / fill-first fix | B-spec after re-gate |
| Commit-time reprobe / ELCP assignment investigation | Layer 2 |
| Changing `placement_target_percent` or hard-coding goals | Product policy |
| Changing greedy-regret weights / overlap / FOT rules | Selection policy B-spec |
| Production behavior change | — |
| Aggregate-only report without **per-round trace** | Insufficient for A2 CLOSED |
| Stating overlap/FOT pool exhaustion as **proven root cause** before trace | Spec/plan violation |

---

## §4 — Investigation scope (Layer 1 only)

```text
A2.1 — placement_goal propagation: field cells → goal_count → select_genome(resolved_goal)
A2.2 — Per-round greedy-regret trace (MANDATORY — §5.1 schema)
A2.3 — Normal-pool attrition ledger (356 rows) with named attrition classes
A2.4 — PlacementGoalPlan diagnostic caps (informational; do not substitute for trace)
A2.5 — Optional spatial histogram (anchor, output_dir, rim)
A2.6 — Universe reconciliation table: 9328 → 356 → 59 → (3 context)
A2.7 — Owner matrix + Layer-1 follow-up candidate (not B-spec nomination)
A2.8 — lane_capacity_shortfall B-spec re-gate decision (blocked / narrowed / pool-scale)
```

---

## §5 — Hypotheses (prove or reject — not conclusions)

| ID | Hypothesis | Proof required |
|----|------------|----------------|
| **H1** | Greedy loop receives `resolved_goal=467` but stops before goal because **pool becomes empty** | Last round `stop_reason=pool_exhausted`; `commit_order_len=59` |
| **H2** | **Overlap pruning** (`occupied_cells` ∩ committed) removes most candidates per round | `removed_by_overlap_count` dominates round trace |
| **H3** | **FOT conflict pruning** removes additional candidates per round | `removed_by_fot_conflict_count` in trace |
| **H4** | **`dedupe_candidates`** reduces pool before first round | `pool_size_after_dedupe` vs 356 |
| **H5** | **Hard cap at 59** in config or code | Code read + trace shows no cap at 59 |
| **H6** | **`placement_goal_plan` diagnostic caps** explain 59 (not goal clamp) | `anchor_cap` / `route_cap` vs 59 with trace |
| **H7** | **ELCP lane count (25)** caps selection at 59 | Reject if trace shows unrelated stop reason |

**Normative:** H1–H3 may all contribute; A2 report states which are **confirmed**, **rejected**, or **inconclusive** per trace.

---

## §5.1 — Per-round greedy-regret trace row (MANDATORY)

Each iteration of `select_genome` while loop **must** emit one row. A2 is **not CLOSED** without this table for the recovery-map replay.

| Field | Type | Required |
|-------|------|----------|
| `round_index` | int | yes |
| `pool_size_before` | int | yes |
| `resolved_goal` | int | yes (constant 467 expected) |
| `selected_candidate_id` | str | yes |
| `selected_occupied_cells_count` | int | yes |
| `selected_output_stub` | coord | yes |
| `selected_fot_cell` | coord | yes |
| `removed_by_overlap_count` | int | yes |
| `removed_by_fot_conflict_count` | int | yes |
| `removed_by_other_count` | int | yes (should be 0 or documented) |
| `pool_size_after` | int | yes |
| `commit_order_len_so_far` | int | yes |
| `stop_reason` | enum | yes — see below |

**`stop_reason` (final round only on loop exit):**

```text
goal_reached          # len(commit_order) >= resolved_goal
pool_exhausted        # pool empty while len(commit_order) < resolved_goal
```

**Implementation note:** Harness mirrors `greedy_regret.select_genome` logic (read-only); does not modify production selection.

---

## §6 — Normal-pool attrition ledger (356 rows)

Each **normal** candidate (pre-dedupe or post-dedupe per trace design — document choice in plan) gets one row.

| `attrition_class` | Meaning |
|-------------------|---------|
| `selected` | In final `commit_order` |
| `removed_by_overlap` | Eliminated by overlap filter in some round |
| `removed_by_fot` | Eliminated by FOT conflict filter in some round |
| `dedupe_removed` | Dropped by `dedupe_candidates` before loop |
| `unpicked_score` | Remained in pool when loop exits with `stop_reason=goal_reached` (not picked before goal) |
| `unknown_attrition` | No rule matched — cap ≤5% |

```text
A2 is not CLOSED unless 356 → 59 attrition is reconciled by per-round greedy_regret trace,
with at least 95% of removed normal candidates assigned to named attrition classes.
```

---

## §7 — Investigation methods

| ID | Method | Role | Required |
|----|--------|------|----------|
| **S1** | Selection mirror trace (`harness/investigation/rttp_greedy_regret_selection_trace.py`) | Per-round table §5.1 | **yes** |
| **S2** | Step forensics | Cross-check `placement_goal_count`, plan caps | yes |
| **S3** | Code contract read | Confirm no hidden cap at 59 | yes |
| **S4** | Universe reconciliation table | 9328 → 356 → 59 → 3 (3 = context) | yes |

**Rejected:** mutating selection to force 467 picks; aggregate counts without round trace.

---

## §8 — Deliverables

| # | Artifact |
|---|----------|
| 1 | This design spec |
| 2 | Plan `2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition.md` |
| 3 | Report `2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-report.md` |
| 4 | `harness/investigation/rttp_greedy_regret_selection_trace.py` |
| 5 | `tests/investigation/test_rttp_greedy_regret_selection_attrition.py` |

---

## §9 — Acceptance (A2 CLOSED)

**Normative gates:**

```text
A2 is not CLOSED unless 356 → 59 attrition is reconciled by per-round greedy_regret trace,
with at least 95% of removed normal candidates assigned to named attrition classes.

B-spec nomination remains blocked unless A2 proves whether commit_order_len=59 is
intended_cap, expected algorithmic side-effect, or bug.
```

**Checklist:**

- [ ] **A2.1** `placement_goal_count` derived from `asteroid_field_cell_count` × `placement_target_percent` (propagated to `select_genome`)
- [ ] **A2.2** Full per-round trace table (§5.1) for recovery-map replay
- [ ] **A2.3** ≥ **95%** of normal candidates assigned named `attrition_class`; `unknown_attrition` ≤ **5%** or gap documented
- [ ] **A2.4** Verdict on **59:** `intended_cap` \| `algorithmic_side_effect` \| `bug` — **evidence from trace only** (no pre-baked expectation in report)
- [ ] **A2.5** H1–H7 each marked confirmed / rejected / inconclusive
- [ ] **A2.6** Reconciliation table published
- [ ] **A2.7** `lane_capacity_shortfall` B-spec re-gate only (no nomination in A2)
- [ ] **No production behavior change**

**P1-ELCP-RF program:** remains **REOPENED** until A2 CLOSED + re-gate.

---

## §10 — B-spec re-gate (decision only — not nomination in A2)

| A2 trace outcome | `lane_capacity_shortfall` B-spec |
|------------------|----------------------------------|
| Layer 1 dominates (pool exhausted before goal) | **BLOCKED** — selection / reachability first |
| Layer 2 dominates (59 ≈ non-overlapping packable set) | **NARROWED_TO_COMMIT_ORDER** — ELCP commit scoped |
| Both | Split tracks |

A2 report **does not** nominate a B-spec; it only unblocks re-gate.

---

## §11 — Spec review record (2026-05-27)

| Check | Result |
|-------|--------|
| Layer 1 only (356 → 59) | **PASS** (amended) |
| No production behavior change | **PASS** |
| Hypothesis separation (H1 overlap/FOT not conclusion) | **PASS** (amended) |
| Per-round trace mandatory | **PASS** (amended §5.1) |
| Attrition taxonomy | **PASS** (amended §6) |
| Universe reconciliation | **PASS** |
| B-spec blocked until A2 | **PASS** (amended §9) |

**Reviewer gate:** Proceed to `writing-plans`.

---

## §12 — References

- [`greedy_regret.py`](../../../django_apps/asteroid_lab/optimization/selection/greedy_regret.py)
- [`placement_goal.py`](../../../django_apps/asteroid_lab/services/placement_goal.py)
- [`rttp_elcp_universe_sanity.py`](../../../harness/investigation/rttp_elcp_universe_sanity.py)
