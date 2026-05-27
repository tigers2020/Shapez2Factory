# P1-ELCP-RF — Primary ELCP Reprobe Failure Investigation — Report

**Date:** 2026-05-27  
**Status:** **REOPENED** — A-track partial; universe sanity added (Task 9)  
**Design spec:** [`../specs/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md`](../specs/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md)  
**Plan:** [`../plans/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation.md`](../plans/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation.md)

---

## Executive status (2026-05-27 review)

| Verdict | Detail |
|---------|--------|
| **Partial success** | Mirror parity PASS; taxonomy within **selected `commit_order`** is complete |
| **Not closed** | Forensics universe is **not** full candidate-pool / large-map scale |
| **B-spec nomination** | **WITHHELD** (`lane_capacity_shortfall` provisional only) |

```text
REOPEN reason: attempt universe too small — report analyzed selected commit_order only.
Next: reconcile commit_order_len vs normal pool & placement_goal before B-spec.
```

---

## RF.8 — Attempt universe sanity (Task 9)

**Scope of M1 ledger (explicit):** `selected_genome_commit_order_only` — walks `genome.commit_order`, not `generation.normal_candidates`.

**Source:** `extract_elcp_attempt_universe_sanity` on recovery-map replay (`test_recovery_map_primary_reprobe_mass_reproduced`).

| Sanity metric | Value | Notes |
|---------------|------:|-------|
| `candidate_pool_total` | 9328 | normal + rejected at generation |
| `normal_candidate_count` | **356** | route-feasible at candidate phase |
| `rejected_candidate_count` | 8972 | generation rejects |
| `placement_goal_count` | **467** | 80% of 583 field cells |
| `asteroid_field_cell_count` | 583 | platform cells |
| `commit_order_len` | **59** | genes selection placed in commit order |
| `selected_genome_size` | 59 | same as commit_order_len |
| `primary_commit_attempt_count` | 59 | equals commit_order_len by construction |
| `primary_committed_count` | 3 | primary incremental_commit |
| `primary_conflict_count` | 56 | all conflict reasons |
| `primary_reprobe_failed_count` | 29 | subset with `reprobe_failed` |
| `expected_attempt_floor` | min(356, 467) = **356** | upper bound if all normals were attempted |
| `selection_mode` | `greedy_regret` | |
| `max_placement_goal_count_config` | 0 | infer from platform in pipeline |
| `required_external_connectors` | 25 | inp |
| `lane_count` / ELCP `required_lane_count` | 25 | plan active |

**Reconciliation:**

```text
356 normal candidates  →  selection  →  59 commit_order  →  M1 ledger (59 attempts)
467 placement_goal   →  NOT equal to commit_order_len (59)
```

**Conclusion:** Low ledger row count (56 failed + 3 committed = 59) is **expected** given current selection output, not a forensics bug. It does **not** prove taxonomy over the full large-map failure surface. Dominant bucket within 59 attempts **cannot** be promoted to whole-map B-spec without further selection/universe work.

---

## RF.1 — Post-fix reproduction (primary SoT)

| Signal | Value |
|--------|-------|
| Slug | `rttp-core-recovery-test-map` |
| Primary `committed_ids` | **3** |
| Primary `REPROBE_FAILED` | **29** |
| ELCP plan active | yes |
| Harness mirror parity | pass (within same 59-attempt universe) |

**Reproduction:** `tests/investigation/test_rttp_elcp_reprobe_forensics.py::test_recovery_map_primary_reprobe_mass_reproduced`

---

## RF.2 — Taxonomy (commit-order subset only)

Failed ledger rows: **56** (= `commit_order_len` 59 − 3 committed).

| `probe_failure_class` | Count | % of ledger |
|----------------------|------:|------------:|
| `lane_capacity_shortfall` | 29 | 51.8% |
| `stale_candidate_reachable` | 27 | 48.2% |

**Coverage within ledger:** 100% named.  
**Coverage vs candidate pool:** **not claimed** — 56 / 356 normals = 15.7% of pool not attempted.

**Provisional (within 59 attempts only):** `lane_capacity_shortfall` aligns with all 29 `REPROBE_FAILED` rows.

---

## RF.3 — M2 step forensics cross-check

Aggregate commit-step metrics align with primary capture on the same run. Per-candidate histogram remains M1-only.

---

## RF.4 — Run #238 historical appendix

Non-authoritative; narrative overlap only (see prior table).

---

## RF.5 — Deferred retry audit

29 / 29 `REPROBE_FAILED` shadow-eligible. `stale_candidate_reachable` rows mostly non-`REPROBE_FAILED` at commit.

---

## RF.6 — Recovery evidence comparison

Informational only; does not override §2.3 precedence.

---

## RF.7 — Owner matrix (commit-order subset)

Unchanged class → owner mapping; applies only to attempted 59 genes.

---

## Dominant bucket → B-spec nomination

| Item | Status |
|------|--------|
| `lane_capacity_shortfall` as dominant | **BLOCKED** |
| Scope | Dominant only within **59** `commit_order` attempts — **not** proven pool-scale (356 normals) |
| Prior nomination | Revoked |
| Next | **A2 CLOSED** — [`2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-report.md`](2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-report.md); B-spec still **BLOCKED** (Layer 1) |

```text
lane_capacity_shortfall B-spec: BLOCKED
Reason: dominant only within selected commit_order universe, not proven pool-scale dominant.
```

---

## Acceptance checklist (revised)

- [x] RF.1 reproduction (within selected commit_order)
- [x] RF.2 taxonomy ≥95% **within ledger**
- [x] RF.3 M2 alignment
- [x] RF.4 #238 appendix
- [x] RF.5 deferred audit
- [x] RF.6 recovery compare
- [x] RF.7 owner matrix (subset)
- [x] RF.8 universe sanity (Task 9)
- [x] No production behavior change
- [x] Harness mirror parity
- [x] **Layer 1 (A2)** — selection attrition CLOSED (see A2 report)
- [ ] **Track CLOSED** — Layer 2 forensics done; B-spec still blocked
- [ ] **B-spec nomination** — blocked (Layer 1 + narrowed universe)

---

## Tooling delivered

| Artifact | Path |
|----------|------|
| Mirror + classifier | `harness/investigation/rttp_elcp_reprobe_forensics.py` |
| Step forensics | `harness/investigation/rttp_elcp_reprobe_step_forensics.py` |
| Universe sanity | `harness/investigation/rttp_elcp_universe_sanity.py` |
| Tests | `tests/investigation/test_rttp_elcp_reprobe_*.py` |
