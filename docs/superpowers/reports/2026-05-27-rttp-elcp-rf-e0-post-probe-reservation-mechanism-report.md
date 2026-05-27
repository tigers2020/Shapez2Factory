# P1-ELCP-RF-E0 — Post-Probe Reservation Mechanism — Report

**Date:** 2026-05-27  
**Status:** **CLOSED** (2026-05-27)  
**Slug:** `rttp-core-recovery-test-map` (Gate A)  
**Git SHA (E0 run):** `428e3bdf1baa2d87d7ef72a09860b716ccee12c8`  
**Spec:** [`2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-design.md`](../specs/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-design.md)  
**Plan:** [`2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism.md`](../plans/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism.md)  
**Prerequisite (CLOSED):** [`2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md`](2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md)

---

## Evidence rule

```text
Primary SoT: 34 D0 stale_candidate_reachable rows — deep ElcpE0MechanismClass per row.
Appendix SoT: aggregate only — all overlap-pack reservation-class failed rows.
Mechanism replay uses commit-order trunk/assignment state (build_stale_replay_signal_cache).
private_overlap_cells and related fields are attribution evidence, not causal proof.
```

**Test:** `tests/investigation/test_rttp_elcp_rf_e0_reservation_mechanism.py::test_gate_a_elcp_e0_overlap_reservation_mechanism`

---

## §1 — D0 carry-forward (aggregate only)

| Field | D0 report (prior SHA) | E0 run (fresh) |
|-------|----------------------|----------------|
| `ElcpD0Verdict` | `RESERVATION_DRIFT_DOMINANT` | carry-forward |
| Stale rows | 34 | **34** |
| `route_cell_conflict` | 22 | **23** |
| `inlet_on_shared_transport` | 12 | **11** |
| `lane_capacity_shortfall` B-spec | **BLOCKED** | **BLOCKED** |

E0 does **not** re-litigate D0; conflict mix drift on fresh SHA is documented only.

---

## §2 — E0 primary universe

| Field | Value |
|-------|------:|
| `selection_mode` | `GREEDY_REGRET_OVERLAP_PACK` |
| Primary deep rows | **34** |
| Mechanism coverage | **100%** |
| Unattributed ratio | **0%** |
| M1 mirror parity | **PASS** |

---

## §3 — Mechanism histogram (primary 34)

| `ElcpE0MechanismClass` | Count | % |
|------------------------|------:|--:|
| `private_route_overlap` | 23 | 67.6 |
| `inlet_stub_on_committed_route` | 11 | 32.4 |

No rows in `shareable_trunk_undercoverage`, `spine_augmentation_conflict`, `probe_vs_merged_route_mismatch`, or `unattributed_*` on this SHA (first-match classification after replay).

**Owner rollup (dominant):** `incremental_commit._private_route_cell_overlap` (route-cell family).

---

## §4 — Per-row artifact

Full per-row JSON is emitted by the investigation test (`E0_ROWS_JSON` print); not duplicated here (34 rows).

**Probe note:** all rows show `probe_expanded_nodes == 500` (`max_expansions`) while `commit_probe_reachable == True`.

**Domain diff note:** `new_blocking_cells_since_last_commit_count == 0` on all 34 rows (same as D0).

---

## §5 — Mechanism synthesis

- **Route-cell stale (23):** commit-time reprobe reaches ELCP connector, but **private route cells** overlap prior `committed_route_cells` outside `lane_shareable` trunk allowance → `route_cell_conflict`. Replay shows non-zero `private_overlap_cell_count` on these rows; many also show `shareable_trunk_undercoverage_count` > 0 but first-match class is `private_route_overlap`.
- **Inlet stale (11):** `output_stub` already lies on `committed_route_cells` at attempt time → `inlet_on_shared_transport` pre-check fires despite reachable reprobe.
- **Non-causal:** overlap counts do not prove the immediately preceding commit caused the failure.

---

## §6 — Verdict, appendix, B-spec nomination

| Field | Value |
|-------|-------|
| **`ElcpE0Verdict`** | **`ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT`** |
| Appendix veto | **No** (appendix family mix aligns with primary: route 23 / inlet 11) |
| **B-spec nomination** | **Yes (1)** |

**Nominated bounded B-spec (prose):**

| Field | Value |
|-------|-------|
| Title | Bounded B-spec: route-cell reservation / shareable trunk / private overlap |
| Owner module | `incremental_commit._private_route_cell_overlap` |
| Rationale | `private_route_overlap` ≥50% of primary 34; single mechanism class dominant |

**Not nominated:** inlet policy (32.4% — below dominance); `lane_capacity_shortfall` remains **BLOCKED**.

### Appendix A — reservation-class failed aggregate

| Metric | Value |
|--------|------:|
| Total reservation-class failed | 34 |
| Stale | 34 |
| Non-stale | 0 |
| `route_cell_conflict` | 23 |
| `inlet_on_shared_transport` | 11 |

---

## §7 — Acceptance (spec §9)

- [x] Overlap-pack Gate A run + M1 parity
- [x] 34 stale rows, full schema
- [x] Mechanism coverage ≥95%; unattributed ≤10%
- [x] Appendix aggregate published
- [x] `ElcpE0Verdict` + B-spec nomination published
- [x] D0 carry-forward §1
- [x] No `django_apps/` production change

```text
E0 CLOSED: ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT — private_route_overlap 23/34;
one bounded B-spec nominated (_private_route_cell_overlap). P1-ELCP-RF parent remains REOPENED.
```
