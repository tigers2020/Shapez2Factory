# P1-ELCP-RF-C0 — Post-B1 Commit-Layer Re-Gate — Report

**Date:** 2026-05-27  
**Status:** **CLOSED** (2026-05-27)  
**Slug:** `rttp-core-recovery-test-map` (Gate A RF.1 parity)  
**Git SHA (primary SoT):** `bf8c411dea3f8e5247a0f834d250144e952fbf03`  
**Spec:** [`2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-design.md`](../specs/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-design.md)  
**Plan:** [`2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate.md`](../plans/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate.md)

---

## Evidence rule

```text
Primary SoT: fresh dual-run on same SHA; only selection_mode differs.
Historical 59/3/29/67: appendix only (not used for verdict).
validation_passed is not Layer 2 root-cause SoT;
validation regression is only a safety veto for accepting B1/C0 evidence.
```

**Test:** `tests/investigation/test_rttp_elcp_rf_c0_post_b1_commit_regate.py::test_gate_a_elcp_c0_dual_mode_primary_regate`

---

## §1 — Dual-run comparison table (primary + informational)

| Metric | `GREEDY_REGRET` | `GREEDY_REGRET_OVERLAP_PACK` | Delta | Class |
|--------|----------------:|-----------------------------:|------:|-------|
| `commit_order_len` | 59 | 67 | +8 | primary |
| `primary_committed_count` | 3 | 7 | +4 | primary |
| `primary_conflict_count` | 56 | 60 | +4 | primary |
| `primary_reprobe_failed_count` | 29 | 26 | −3 | primary |
| `lane_capacity_shortfall_count` | 29 | 26 | −3 | primary |
| `route_feasible_shortfall_count` | 56 | 60 | +4 | primary |
| `stale_candidate_reachable_count` | 27 | 34 | +7 | primary (ledger) |
| `validation_passed` | True | True | — | informational_e2e |
| `throughput_shortfall_reason` | None | None | — | informational |

**M1 mirror parity:** PASS both modes. **Bucket coverage:** 100% both modes.

---

## §2 — Layer 2 bucket histograms (failed attempts)

### `GREEDY_REGRET` (56 failed)

| `probe_failure_class` | Count | % |
|----------------------|------:|--:|
| `lane_capacity_shortfall` | 29 | 51.8% |
| `stale_candidate_reachable` | 27 | 48.2% |

**Dominant:** `lane_capacity_shortfall`

### `GREEDY_REGRET_OVERLAP_PACK` (60 failed)

| `probe_failure_class` | Count | % |
|----------------------|------:|--:|
| `stale_candidate_reachable` | 34 | 56.7% |
| `lane_capacity_shortfall` | 26 | 43.3% |

**Dominant:** `stale_candidate_reachable`

---

## §3 — C0 decision heuristic (synthesis)

| Signal | Reading |
|--------|---------|
| `commit_order` | +8 (59→67) — B1 selection lift confirmed on same SHA |
| `primary_committed` | +4 (3→7) — **meaningful** primary commit lift (not ~3 flat) |
| Baseline dominant bucket | `lane_capacity_shortfall` (51.8%) |
| Overlap dominant bucket | `stale_candidate_reachable` (56.7%) — **shift** vs baseline |
| E2E validation | No regression (both pass) |

**Conclusion:** Overlap-pack **does** improve primary commits on Gate A, but the **dominant failure class on the larger commit_order universe** is `stale_candidate_reachable`, not `lane_capacity_shortfall`. Lane-capacity B-spec re-gate remains inappropriate as the immediate next fix target.

---

## §4 — `lane_capacity_shortfall` B-spec re-gate

| Verdict | **BLOCKED** |
|---------|-------------|
| Reason | `stale_candidate_reachable` dominant on overlap-pack (56.7% of failed); lane_capacity_shortfall B-spec not appropriate per C0 heuristic |

**Note:** C0 does **not** nominate a B-spec. Program may open **post-probe commit / reservation** or **selection vs commit contract** track separately.

---

## §5 — Historical appendix (not primary SoT)

| Anchor | Value |
|--------|------:|
| RF/A2 `commit_order_len` | 59 |
| RF `primary_committed` | 3 |
| RF `primary_reprobe_failed` | 29 |
| B1 `target_floor` / overlap `commit_order` | 67 |

Fresh dual-run on `bf8c411d…` matches historical `commit_order` anchors; **primary_committed fresh overlap-pack (7) exceeds historical (3)**.

---

## §6 — Next track (queue hint)

| Priority | Track |
|----------|-------|
| 1 | **Keep B1** — overlap-pack improves primary commits (3→7) with no E2E validation regression |
| 2 | **Investigate `stale_candidate_reachable`** on overlap-pack commit_order (post-probe / reservation B-spec scoping) |
| 3 | Defer **`lane_capacity_shortfall` fill-first B-spec** until stale/reachable bucket no longer dominates overlap-pack forensics |

---

## §7 — Acceptance (spec §10)

- [x] Same SHA dual-run, Gate A config, only `selection_mode` differs
- [x] Primary first `incremental_commit` captured both modes
- [x] M1 mirror parity both modes
- [x] Bucket coverage ≥95% both modes
- [x] Dual-run delta table published (§1)
- [x] Re-gate stated: **BLOCKED** (§4)
- [x] No production behavior change

```text
C0 CLOSED: overlap-pack raises primary_committed 3→7 on Gate A same SHA;
stale_candidate_reachable dominant on overlap-pack → lane_capacity_shortfall B-spec BLOCKED.
```
