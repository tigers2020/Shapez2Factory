# P1-ELCP-RF-D0 — stale_candidate_reachable Commit-Time Drift — Report

**Date:** 2026-05-27  
**Status:** **CLOSED** (2026-05-27)  
**Slug:** `rttp-core-recovery-test-map` (Gate A)  
**Git SHA (D0 run):** `9b4fbcf23af3f41b366fa06e51f02b164ffc02aa`  
**Spec:** [`2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-design.md`](../specs/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-design.md)  
**Plan:** [`2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable.md`](../plans/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable.md)  
**Prerequisite (CLOSED):** [`2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md`](2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md)

---

## Evidence rule

```text
Primary SoT: GREEDY_REGRET_OVERLAP_PACK stale_candidate_reachable rows only (34).
C0 dual-run table is carry-forward (§1); baseline has no per-row deep attribution.
new_blocking_cells_since_last_commit_count is attribution evidence, not by itself
proof that the immediately preceding commit caused the stale failure.
```

**Test:** `tests/investigation/test_rttp_elcp_rf_d0_stale_attribution.py::test_gate_a_elcp_d0_overlap_stale_attribution`

---

## §1 — C0 carry-forward (aggregate only)

From C0 report on prior SHA (`bf8c411d…`); narrative anchor unchanged on overlap-pack universe:

| Metric | `GREEDY_REGRET` | `GREEDY_REGRET_OVERLAP_PACK` | Delta |
|--------|----------------:|-----------------------------:|------:|
| `commit_order_len` | 59 | 67 | +8 |
| `primary_committed_count` | 3 | 7 | +4 |
| `stale_candidate_reachable` (failed bucket) | 27 (48.2%) | 34 (56.7%) | +7 |
| `lane_capacity_shortfall` B-spec | — | **BLOCKED** | — |

D0 does **not** re-litigate C0; overlap-pack remains the dominant stale universe.

---

## §2 — D0 primary universe

| Field | Value |
|-------|------:|
| `selection_mode` | `GREEDY_REGRET_OVERLAP_PACK` |
| `stale_row_count` | **34** |
| `attribution_coverage` | **100%** |
| `unattributed_stale_ratio` | **0%** |
| M1 mirror parity | PASS |

All 34 rows satisfy: `candidate.reachable`, commit-time `probe.reachable`, not `post_probe_committed` (RF stale definition).

---

## §3 — Attribution histogram

| `stale_attribution_class` | Count | % |
|---------------------------|------:|--:|
| `post_probe_reservation_block` | 34 | 100% |

No rows in `probe_start_drift`, `goal_set_shrink`, `domain_congestion_at_commit`, or `selection_survivability_gap` on this SHA.

---

## §4 — Commit conflict breakdown (34 rows)

| `commit_conflict_reason` | Count |
|--------------------------|------:|
| `route_cell_conflict` | 22 |
| `inlet_on_shared_transport` | 12 |

**Probe note:** all rows show `probe_expanded_nodes == 500` (`max_expansions`) while `commit_probe_reachable == True` — commit-time probe reports reachable at expansion cap (distinct from `budget_exceeded` unreachable class).

**Domain diff note:** `new_blocking_cells_since_last_commit_count == 0` on all 34 rows — failed attempts share the same committed route/occupied snapshot as the last successful commit before each stall (no new cells between consecutive failures). Reservation conflict reasons still classify rows as `post_probe_reservation_block` via §3.5.1.

Full per-row JSON is emitted by the investigation test (`D0_ROWS_JSON` print); not duplicated here (34 rows).

---

## §5 — Commit-order position analysis

| Band | `commit_index` range | Stale count |
|------|---------------------|------------:|
| Early | 3–13 | 11 |
| Mid | 17–37 | 13 |
| Late | 39–62 | 10 |

Stale failures cluster after the first successful commits (`domain_version` 1→7), consistent with accumulated shared-trunk / route-cell reservation pressure rather than pre-commit probe-unreachability.

---

## §6 — Verdict and next track

| Field | Value |
|-------|-------|
| **`ElcpD0Verdict`** | **`RESERVATION_DRIFT_DOMINANT`** |
| B-spec nomination | **None** (forensic only) |

**Reading:** On Gate A overlap-pack, every stale row is reachable at reprobe but blocked at post-probe commit by reservation-class conflicts (`route_cell_conflict`, `inlet_on_shared_transport`). Next track (program hint, not spec): post-probe reservation / shared-transport commit policy review — **not** `lane_capacity_shortfall` fill-first B-spec (C0 BLOCKED).

**P1-ELCP-RF** parent remains **REOPENED**.

---

## §7 — Acceptance (spec §9)

- [x] Overlap-pack Gate A run + M1 parity
- [x] 34 stale rows, full schema
- [x] Attribution coverage ≥95%; unattributed ≤10%
- [x] `ElcpD0Verdict` published
- [x] C0 aggregate carry-forward §1
- [x] No `django_apps/` production change

```text
D0 CLOSED: RESERVATION_DRIFT_DOMINANT — 34/34 post_probe_reservation_block on overlap-pack Gate A.
```
