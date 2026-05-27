# P1-ELCP-RF-F1.1 — Private Route Overlap Row-Level Forensic — Report

**Date:** 2026-05-27  
**Status:** **CLOSED** (2026-05-27)  
**Git SHA (F1.1 run):** `f8d5773c8e9748eb99e70249edad39a3a005e359`  
**Spec:** [`2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-design.md`](../specs/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-design.md)  
**Plan:** [`2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic.md`](../plans/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic.md)  
**Parent (PARTIAL):** [`2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy-report.md`](2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy-report.md)

---

## Evidence rule

```text
Read-only forensic; overlap partition fields are attribution evidence, not causal proof.
Primary SoT: 20-row F11_ROWS_JSON from investigation test print.
D0/E0 historical stale baseline = 34; current Gate A stale universe = 33;
F1.1 analyzes 20 private_route_overlap rows only.
F1.1 does not attempt to make G1 pass.
```

**Test:** `tests/investigation/test_rttp_elcp_rf_f11_private_overlap_forensic.py::test_gate_a_f11_private_overlap_forensic`

---

## §1 — Parent carry-forward

| Field | Value |
|-------|------:|
| F1 status | **PARTIAL** — G1 not met (20 > 11) |
| Parent stale rows | **33** |
| F1.1 slice rows | **20** |
| M1 mirror parity | **PASS** |
| `unclear_needs_trace` | **0** |

---

## §2 — Root-cause histogram

| `f11_root_cause` | Count | % |
|------------------|------:|--:|
| `trunk_evidence_missing` | 20 | 100% |
| `committed_growth_artifact` | 0 | 0% |
| `spine_or_stub_residual_overlap` | 0 | 0% |
| `true_peer_branch_overlap` | 0 | 0% |
| `unclear_needs_trace` | 0 | 0% |

**Partition note (aggregate):** all 20 rows show `overlap_in_full_route_not_reserved == 0` and `shareable_undercoverage_flag == True`. Overlap cells lie in `trunk_mask` but not in `shareable_at_commit` at attempt time (undercoverage ∩ O non-empty).

---

## §3 — Per-row artifact

Full per-row JSON is emitted by the investigation test (`F11_ROWS_JSON` print); not duplicated here (20 rows).

---

## §4 — Synthesis

- **No row** classified as `true_peer_branch_overlap` on current Gate A code after F1 policy.
- **All 20** rows are **policy-evidence** failures: overlap cells are trunk-capable but excluded from `shareable_at_commit` (F1a shareable union did not cover committed trunk cells on the overlap corridor).
- **`committed_growth_artifact` (O ∩ (M \\ R))** did not fire on any row — full-route-not-reserved growth is not the dominant residual mechanism on this slice.
- F1 G1 remains **not met** (20 `private_route_overlap` mechanism rows); F1.1 explains **why** without greening G1.

---

## §5 — F1.2 nomination

| Field | Value |
|-------|-------|
| Nominated | **yes** |
| Track | **F1.2a** |
| Title | Bounded F1.2a: trunk_evidence_missing |
| Withheld reason | `none` |

**Counterfactual (deferred):** F1.1b may simulate widened shareable evidence only after F1.2a safety review (INV-S1..S4). Not in F1.1 close gate.

**Split fixable classes:** not applicable (single dominant class).

---

## §6 — Non-goals confirmed

```text
No django_apps/ production changes in F1.1.
No G1 green attempt.
Counterfactual B not executed.
```

---

## §7 — CI posture

| Test | Status |
|------|--------|
| F1.1 investigation | **PASS** (slow, local) |
| F1 G1 | **XFAIL** / known not met — not merge-blocking |
| E0 investigation | unchanged |
