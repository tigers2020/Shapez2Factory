# P1-ELCP-RF-F1.1 — Private Route Overlap Row-Level Forensic — Design Spec

**Date:** 2026-05-27  
**Status:** **CLOSED** (2026-05-27 — harness implemented; report published)  
**Document type:** Read-only regression forensics (F-track, Layer 3 post-F1 diagnosis)  
**Work classification:** documentation · investigation forensics (harness/tests only)  
**Parent (PARTIAL):** [`2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md`](2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md) · F1 report [`../reports/2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy-report.md`](../reports/2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy-report.md)  
**Prerequisite harness (unchanged):** [`2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-design.md`](2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-design.md)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Implementation plan:** [`../plans/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic.md`](../plans/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic.md)

**Korean title (reference):** F1 잔여 private_route_overlap 20건 row-level forensic

---

## §1 — Executive summary

**F1 (PARTIAL)** implemented F0 reservation policy (F1a/F1b/F1c). Tier S and mirror parity pass. **G1 FAIL:** `private_route_overlap` mechanism rows **20** (target ≤11, E0 baseline 23). Stale universe **33** (historical D0/E0 baseline **34** — not redefined).

**F1.1 sole question:**

```text
Among the remaining private_route_overlap rows on current Gate A code,
which are true illegal peer-branch overlaps vs false positives
(trunk evidence missing, full-route-not-reserved growth, spine/stub residual)?
```

**F1.1 outcome contract:**

```text
F1.1 succeeds by explaining the 20 rows, not by reducing the G1 mechanism count.
F1.1 does not attempt to make G1 pass.
F1.1 only determines which subset, if any, is eligible for a later bounded F1.2 policy change.
```

**Approach (normative):** **Read-only forensic (A)** — new harness module; filter E0 rows; secondary root-cause taxonomy; row-level JSON + report + F1.2 nomination. **Counterfactual simulation (B) is out of scope** but evidence fields are counterfactual-ready for a later F1.1b subtrack.

**Explicitly NOT F1.1:**

```text
django_apps/ production policy changes
G1 green attempts or shareable mask widening
F1.1b harness counterfactual simulation (deferred nomination only)
inlet_on_shared_transport deep dive (13 rows)
lane_capacity_shortfall
selection_mode rollout
replay · NDJSON · solver_summary as solver input
new CommitConflictReason enums
E0 mechanism enum re-aggregation (E0 classify_e0_mechanism unchanged)
```

---

## §2 — Problem statement

### §2.1 E0 first-match masks sub-causes

`classify_e0_mechanism` assigns `private_route_overlap` whenever `private_overlap_cells` is non-empty. After F1, **20/33** stale rows still carry that class. Sub-signals (`shareable_trunk_undercoverage`, `spine_augmentation_conflict`, `probe_vs_merged_route_mismatch`) are computed in replay but **never selected** while private overlap is non-empty.

### §2.2 F1.1 target slice

| Universe | Count | Notes |
|----------|------:|-------|
| D0/E0 historical stale baseline | **34** | Report narrative only |
| Current Gate A stale (`EXPECTED_OVERLAP_STALE_ROW_COUNT`) | **33** | Post-F1 regression constant |
| F1.1 deep slice (`elcp_e0_mechanism_class == private_route_overlap`) | **20** | Full row-level forensic |

### §2.3 Safety principle (carry-forward from F0)

```text
true_peer_branch_overlap → retain reject policy; no F1.2 widen nomination when dominant.
Fixable classes (trunk evidence, full-route-not-reserved, spine/stub) → bounded F1.2 tracks only after F1.1 close.
```

---

## §3 — Architecture and modules

### §3.1 Data flow

```text
run_gate_a_elcp_e0_reservation_forensics()  # 33 stale rows — unchanged
        │
        ▼ filter private_route_overlap (expect 20)
run_gate_a_elcp_f11_private_overlap_forensics()
        │
        ├─ extended replay evidence per row (read-only production helpers)
        ├─ classify_f11_root_cause (secondary first-match)
        ├─ evaluate_f12_nomination
        └─ ElcpF11ForensicsResult + report
```

- **Do not modify** `classify_e0_mechanism` or E0 investigation test assertions.
- Prefer **new file** `harness/investigation/rttp_elcp_f11_private_overlap_forensic.py`. Touch `rttp_elcp_e0_reservation_mechanism.py` only if an export is strictly required (behavior-identical).

### §3.2 File map

| File | Responsibility |
|------|----------------|
| `harness/investigation/rttp_elcp_f11_private_overlap_forensic.py` | Enums, evidence DTO, partition, classify, nomination, orchestrator |
| `tests/support/rttp_f11_gate_a_frozen_bounds.py` | `F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT = 20`, `F11_UNCLEAR_MAX_ROWS = 2` |
| `tests/unit/harness/test_rttp_elcp_f11_private_overlap_forensic.py` | Pure classify + nomination (no DB) |
| `tests/investigation/test_rttp_elcp_rf_f11_private_overlap_forensic.py` | Slow Gate A integration + `F11_ROWS_JSON` print |
| `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-report.md` | Histogram, nomination, synthesis |
| `documents/ai/current_plan.md` | F1 PARTIAL + F1.1 ACTIVE |

---

## §4 — Symbols and evidence

### §4.1 Replay symbols (non-causal)

| Symbol | Definition |
|--------|------------|
| **O** | `private_overlap_cells` (non-empty on slice rows) |
| **S** | `shareable_at_commit` |
| **R** | `reservation_candidate_cells` (F0 `compute_elcp_reservation_candidate_cells`) |
| **M** | merged/full route at overlap check (production `_attempt_commit_one` chain: branch∪new_trunk + spine augment + FL-06 stub merge) |
| **Δ** | `outcome.committed_route_delta` — **debug-only**; often `∅` on failed attempt |

### §4.2 Partition buckets (all recorded in `overlap_partition`)

```text
O_shareable           = O ∩ S
O_trunk_mask          = O ∩ domain.trunk_mask_cells
O_full_not_reserved   = O ∩ (M \ R)     # SoT for committed_growth_artifact
O_spine_stub          = O ∩ (spine_aug ∪ probe_merged_diff ∪ stub_adjacent)
O_branch_only         = (O ∩ branch_partition) \ (O_trunk_mask ∪ O_spine_stub)
```

**Row fields (normative):**

| Field | Type | Meaning |
|-------|------|---------|
| `overlap_partition` | `dict[str, int]` | Counts for keys: `shareable`, `trunk_mask`, `full_route_not_reserved`, `spine_or_stub`, `branch_only` |
| `overlap_in_shareable_at_commit` | int | \|O_shareable\| |
| `overlap_in_trunk_mask` | int | \|O_trunk_mask\| |
| `overlap_in_full_route_not_reserved` | int | \|O_full_not_reserved\| — **SoT for growth artifact** |
| `overlap_in_committed_delta_only` | int | \|O ∩ Δ\| — debug; may be 0 on failure |
| `overlap_in_spine_or_stub_residual` | int | \|O_spine_stub\| |
| `overlap_in_true_private_branch` | int | \|O_branch_only\| (informational; class rule uses buckets) |
| `shareable_undercoverage_flag` | bool | `(undercoverage ∩ O) ≠ ∅` |
| `spine_stub_residual_flag` | bool | \|O_spine_stub\| > 0 |
| `reservation_candidate_sample` | tuple | ≤10 coords |
| `candidate_route_delta_sample` | tuple | ≤10 coords (symmetric diff path vs R) |
| `branch_cells_sample` / `new_trunk_cells_sample` / `reused_trunk_cells_sample` / `shareable_at_commit_sample` | tuple | ≤10 each |

### §4.3 Extended replay

At each stale failure attempt, F1.1 performs the same commit-order walk as E0 `build_stale_replay_signal_cache`, additionally capturing **M**, **R**, partition sets, and optional **Δ** from `CommitResult`. Imports production helpers only; **no** `django_apps/` edits.

---

## §5 — Secondary taxonomy

### §5.1 `ElcpF11PrivateOverlapRootCause`

```text
trunk_evidence_missing
committed_growth_artifact
spine_or_stub_residual_overlap
true_peer_branch_overlap
unclear_needs_trace
```

### §5.2 `classify_f11_root_cause` — ordered first-match

Evaluate on partition sets derived in §4.2. **One** root cause per row; all bucket counts remain in `overlap_partition`.

| Order | Class | Rule |
|------:|-------|------|
| 1 | `trunk_evidence_missing` | `(undercoverage ∩ O) ≠ ∅` |
| 2 | `committed_growth_artifact` | \|O_full_not_reserved\| > 0 |
| 3 | `spine_or_stub_residual_overlap` | \|O_spine_stub\| > 0 |
| 4 | `true_peer_branch_overlap` | \|O_branch_only\| > 0 **or** (`O ∩ trunk_mask = ∅` **and** \|O_full_not_reserved\| = 0 **and** \|O_spine_stub\| = 0) |
| 5 | `unclear_needs_trace` | else |

**Rule 4 rationale:** `O ∩ trunk_mask = ∅` alone must not classify true peer when full-route or spine/stub buckets already explain overlap.

### §5.3 Edge cases

| Case | Handling |
|------|----------|
| Slice row with `O == ∅` | Harness error — exclude at filter |
| Parent `mirror_parity_ok == False` | Abort F1.1 with `INCONCLUSIVE`; no row table |
| `len(stale) ≠ 33` or slice `≠ 20` | Investigation test FAIL — update frozen bounds only when Gate A universe changes |
| `M == R` but `O` non-empty | `unclear_needs_trace` + `replay_invariant_violation: true` in `to_dict()` |
| Multi-bucket row | All partition counts recorded; first-match selects single root cause |

### §5.4 F1.2 owner mapping

| Root cause | F1.2 track (nomination prose) |
|------------|-------------------------------|
| `trunk_evidence_missing` | F1.2a — shareable/trunk evidence alignment (F0 §3.1, INV-S1..S4) |
| `committed_growth_artifact` | F1.2b — overlap input vs M/R reservation boundary (F0 §3.2–§3.3) |
| `spine_or_stub_residual_overlap` | F1.2c — SPINE/FL-06 reservation boundary |
| `true_peer_branch_overlap` | **No widen** — retain safety |
| `unclear_needs_trace` | Telemetry / F1.1b only |

---

## §6 — F1.2 nomination

### §6.1 `F12NominationWithheldReason`

```text
none
unclear_too_high
no_dominant_root_cause
true_peer_dominant
split_fixable_classes
parent_mirror_fail
```

### §6.2 Guards (all required to nominate a fixable F1.2 track)

```text
1. Parent E0 mirror_parity_ok
2. len(f11_rows) == 20
3. unclear_count ≤ 2
4. One root_cause count ≥ 10 (50% of 20) for single-track nomination
5. No production change in F1.1
```

### §6.3 Outcomes

| Condition | Result |
|-----------|--------|
| Dominant `true_peer_branch_overlap` (≥10 rows) | Withheld `true_peer_dominant`; report: retain reject policy |
| Dominant fixable class (≥10) | Nominate matching F1.2a/b/c title + owner |
| Two+ fixable classes each ≥ 7, none ≥ 10 | Withheld `split_fixable_classes` |
| `unclear_count > 2` | Withheld `unclear_too_high` |
| No class ≥ 10 and not split | Withheld `no_dominant_root_cause` |

**Split fixable classes (report prose, normative):**

```text
Split fixable classes means F1.1 produced diagnosis, but F1.2 implementation
must not combine multiple policy changes in one PR.
```

### §6.4 Counterfactual (B) — deferred

F1.1 MAY footnote in report: if dominant == `trunk_evidence_missing`, a later **F1.1b** harness counterfactual may simulate `shareable ∪ missing_trunk_evidence` using §4.2 evidence fields. **Not** an F1.1 close gate.

---

## §7 — Row schema `ElcpF11OverlapForensicRow`

Carry forward from `ElcpE0MechanismRow`: `commit_index`, `candidate_id`, `git_sha`, `elcp_e0_mechanism_class`, `private_overlap_cell_count`, `private_overlap_sample`, `assigned_lane_id`.

Add: all §4.2 fields, `f11_root_cause`, `f11_root_cause_owner` (bounded module id string).

`to_dict()` → investigation test print `F11_ROWS_JSON` (exactly **20** elements on current code).

---

## §8 — Success gates and CI

### §8.1 F1.1 close (normative)

```text
- 20/20 rows classified
- unclear_needs_trace ≤ 2
- root_cause_histogram + row JSON emitted
- F1.2 nomination or explicit withheld reason
- no django_apps/ behavior change
- E0 / F1 Tier S / D0 regression tests unchanged
- G1 test remains RED or investigation-only (not merge-blocking)
```

### §8.2 Investigation test assertions

File: `tests/investigation/test_rttp_elcp_rf_f11_private_overlap_forensic.py`

```text
parent_stale_row_count == 33
len(rows) == 20
unclear_count <= 2
mirror_parity_ok is True
# print F11_ROWS_JSON, histogram, nomination
```

**Forbidden in F1.1 test:**

```text
assert private_count <= 11   # G1 — separate test, stays RED
modify test_rttp_elcp_rf_f1_reservation_policy_gate_a.py to pass/xfail by default
```

### §8.3 CI posture

| Test | Merge-blocking |
|------|----------------|
| E0 investigation | existing slow tier |
| F1 G1 | **No** (RED local gate) |
| F1.1 investigation | **No** until F1.2 closes G1 |

Draft PR: G1 xfail only if explicitly WIP — not F1.1 default.

---

## §9 — Report template

Path: `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-report.md`

| § | Content |
|---|---------|
| Evidence rule | Read-only; non-causal; 20-row JSON in test print |
| Parent carry-forward | F1 PARTIAL; G1 FAIL; historical 34 vs current 33 |
| Universe | 33 stale, 20 slice, git SHA |
| Root-cause histogram | counts + % |
| Per-row artifact | pointer to `F11_ROWS_JSON` |
| Synthesis | fixable vs true_peer vs unclear |
| F1.2 nomination | track / withheld + split prose if applicable |
| Non-goals | no G1 green, no production, B deferred |
| CI | G1 RED local |

Header line (normative):

```text
D0/E0 historical stale baseline = 34; current Gate A stale universe = 33;
F1.1 analyzes 20 private_route_overlap rows only.
```

---

## §10 — Non-goals (normative)

| Forbidden | Owner |
|-----------|--------|
| Production edits | F1.2+ |
| G1 green in F1.1 | F1.2 |
| F1.1b counterfactual in F1.1 close | F1.1b nomination |
| Inlet 13-row forensic | separate subtrack |
| Dual F1.2 policy in one PR | split withheld rule |

---

## §11 — Spec self-review (2026-05-27)

| Check | Result |
|-------|--------|
| F1.1 read as G1-green goal? | **No** — §1, §8.1 explicit |
| Counterfactual B in scope? | **No** — §6.4 deferred; evidence-only |
| `committed_delta_only` vs `full_route_not_reserved`? | **Clear** — §4.2 SoT = `O_full_not_reserved`; delta debug-only |
| Placeholders | None |
| Single implementation plan scope? | **Yes** — one harness module + tests + report |
