# P1-ELCP-RF-F1 — Private Route Overlap Reservation Policy — Report

**Date:** 2026-05-27  
**Status:** **PARTIAL** — F1a/F1b/F1c implemented; **G1 not met** (follow-up required)  
**Spec:** [`2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md`](../specs/2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md)  
**Plan:** [`2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy.md`](../plans/2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy.md)

---

## §1 — Implementation summary

| Phase | Status |
|-------|--------|
| F1a | **DONE** — `shareable_trunk_cells_for_transport`, `ReservationCandidateCells` overlap input, spine guard |
| F1b | **DONE** — `committed_route_delta` on ELCP success |
| F1c | **DONE** — E0 + mirror replay aligned with F0 pipeline |

**Production modules:** `exterior_lane_trunk.py`, `reservation_overlap_policy.py`, `incremental_commit.py`  
**Harness:** `rttp_elcp_e0_reservation_mechanism.py`, `rttp_elcp_reprobe_forensics.py`

---

## §2 — Gate A measurable (G1)

| Metric | E0 baseline | F1 run |
|--------|-------------|--------|
| Stale universe rows | 34 | **33** (−1 commit unblocked) |
| `private_route_overlap` mechanism rows | 23 | **20** (−3, **13%** reduction) |
| G1 target (≤11 rows, ≥50%) | — | **NOT MET** |
| Tier S safety | — | **PASS** |
| Mirror parity | — | **PASS** |

```text
G1 BLOCKED: need further policy iteration (likely branch–branch overlap on committed deltas)
or spec-amended shareability rule with safety proof.
```

---

## §3 — Conflict mix (stale 33)

| `commit_conflict_reason` | Count |
|--------------------------|------:|
| `route_cell_conflict` | 20 |
| `inlet_on_shared_transport` | 13 |

Mechanism histogram: `private_route_overlap` 20 · `inlet_stub_on_committed_route` 13.

---

## §4 — Next

1. Forensic sample of remaining 20 `private_route_overlap` rows (branch vs trunk).  
2. Optional F1.1: widen shareable only with INV-S1..S4 proof + Tier S re-run.  
3. Inlet subtrack (13 rows) remains out of scope.
