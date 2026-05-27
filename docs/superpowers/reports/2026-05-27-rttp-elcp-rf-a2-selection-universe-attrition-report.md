# P1-ELCP-RF-A2 — Selection Universe Attrition — Investigation Report

**Date:** 2026-05-27  
**Status:** CLOSED (Layer 1 read-only forensics)  
**Slug / config:** `rttp-core-recovery-test-map` — **Gate A parity config** (P1-ELCP-RF RF.1)  
**Spec:** [`2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-design.md`](../specs/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-design.md)

---

## 1. Executive (Layer 1 only)

**Question:** Why does `normal_candidate_count=356` become `commit_order_len=59` while `placement_goal_count=467`?

**Answer (trace-backed):** Production `select_genome` received `goal_count=467`, ran **59** greedy-regret rounds, then exited with **`stop_reason=pool_exhausted`** (empty pool, `len(commit_order)=59`). All **297** non-selected normal candidates in the attrition ledger are class **`removed_by_overlap`**; **`removed_by_fot`** count is **0** on this baseline. This is an **algorithmic side-effect** of overlap pruning under greedy packing—not a hard-coded cap at 59 and not `placement_goal_count`.

**Out of scope:** Why 59 attempts yield 3 primary commits / 29 `REPROBE_FAILED` (P1-ELCP-RF Layer 2).

---

## 2. Universe reconciliation

| Stage | Count | Notes |
|-------|------:|-------|
| `candidate_pool_total` | 9328 | 356 normal + 8972 rejected |
| `normal_candidate_count` | 356 | route-feasible at generation |
| `commit_order_len` | 59 | greedy-regret output |
| `placement_goal_count` | 467 | 583 field cells × 80% |
| `primary_committed_count` | 3 | Layer 2 context only |

Harness: `trace_greedy_regret_selection` **parity** with production `select_primary_genome` genome on Gate A replay.

---

## 3. Per-round trace summary

| Metric | Value |
|--------|------:|
| `round_trace` rows | 59 |
| `resolved_goal` | 467 |
| `stop_reason` | `pool_exhausted` |
| Final round `pool_size_after` | 0 (asserted when `pool_exhausted`) |

**Round-level pruning (aggregated):** Sum of `removed_by_overlap_count` across rounds = **297** (matches attrition ledger). Sum of `removed_by_fot_conflict_count` = **0**.

Detailed row dump: reproduce via `pytest … -s` prints `A2_ROUND_TRACE_LEN`, `A2_STOP_REASON`.

---

## 4. Attrition ledger (356 normals)

| `attrition_class` | Count |
|-------------------|------:|
| `selected` | 59 |
| `removed_by_overlap` | 297 |
| `removed_by_fot` | 0 |
| `dedupe_removed` | 0 |
| `unpicked_score` | 0 |
| `unknown_attrition` | 0 |

**Coverage:** 100% named classes (≥95% gate met).

---

## 5. Hypothesis matrix (H1–H7)

| ID | Hypothesis | Verdict | Evidence |
|----|------------|---------|----------|
| H1 | Loop stops with `pool_exhausted` before `resolved_goal` | **Confirmed** | `stop_reason=pool_exhausted`, `len(commit_order)=59`, `resolved_goal=467` |
| H2 | Overlap pruning removes most attrition | **Confirmed** | 297/297 non-selected = `removed_by_overlap` |
| H3 | FOT conflict drives attrition on this slug | **Rejected** | 0 `removed_by_fot`; round trace FOT removal sum 0 |
| H4 | Dedupe shrinks pool before loop | **Rejected** | `dedupe_removed_count=0` |
| H5 | Hidden cap at 59 in code | **Rejected** | No cap; trace stops at pool empty |
| H6 | `placement_goal_plan` diagnostic caps explain 59 | **Inconclusive / weak** | Goal 467 propagated; caps informational only |
| H7 | ELCP lane count (25) caps selection at 59 | **Rejected** | Stop reason pool exhaustion at round 59, not lane count |

**Note:** H2 confirms overlap **assignments in the ledger**; it does not by itself prove future map slugs behave identically.

---

## 6. Verdict on `commit_order_len=59`

| Option | Selected? |
|--------|-----------|
| `intended_cap` | No |
| `algorithmic_side_effect` | **Yes** |
| `bug` | No evidence on Gate A baseline |

**Rationale:** Goal 467 was supplied; loop terminated early because the candidate pool became empty after overlap filtering (`pool_exhausted`). No `unpicked_score` rows (pool empty, not `goal_reached`).

---

## 7. B-spec re-gate (`lane_capacity_shortfall`)

| Decision | Value |
|----------|-------|
| Re-gate | **BLOCKED** (Layer 1 dominates on this slug) |
| Nomination | **None** (A2 does not nominate B-spec) |

**Reason:** Selection delivers only **59** placements vs **467** goal before commit; pool-scale `lane_capacity_shortfall` B-spec remains inappropriate until selection reachability / attrition is addressed or a separate slug proves Layer 2 dominance.

**P1-ELCP-RF Layer 2:** Commit-order scoped forensics remain valid but **NARROWED** B-spec for fill-first is still **blocked** at program level until product prioritization after selection track.

---

## 8. Acceptance (spec §9)

- [x] A2.1 placement goal propagation (467 from field cells × percent)
- [x] A2.2 Full per-round trace (59 rows)
- [x] A2.3 ≥95% attrition named (100%)
- [x] A2.4 Verdict: `algorithmic_side_effect` (trace only)
- [x] A2.5 H1–H7 matrix
- [x] A2.6 Reconciliation table
- [x] A2.7 B-spec re-gate only — **BLOCKED**
- [x] No production behavior change

```text
A2 is CLOSED: 356 → 59 reconciled by per-round greedy_regret trace with 100% named attrition classes.
B-spec nomination remains blocked; lane_capacity_shortfall re-gate: BLOCKED (Layer 1).
```

---

## 9. Tooling

| Artifact | Path |
|----------|------|
| Selection trace | `harness/investigation/rttp_greedy_regret_selection_trace.py` |
| Tests | `tests/investigation/test_rttp_greedy_regret_selection_attrition.py` |

**Gate A frozen asserts** live only in `test_recovery_map_selection_attrition_trace_gate_a_parity_config`; drift = baseline/config change, not automatic algorithm regression.
