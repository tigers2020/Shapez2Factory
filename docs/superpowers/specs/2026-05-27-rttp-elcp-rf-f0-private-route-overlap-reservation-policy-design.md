# P1-ELCP-RF-F0 — Private Route Overlap / Shareable Trunk Reservation Policy — Design Spec

**Date:** 2026-05-27  
**Status:** **Approved for planning** (design-only — no production implementation in F0)  
**Document type:** Bounded B-spec policy contract (F-track, Layer 3 reservation semantics)  
**Work classification:** documentation · contract change (design-only in F0; implementation in F1)  
**Parent (REOPENED):** [`2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md`](2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md)  
**Prerequisite (CLOSED):** [`2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-design.md`](2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-design.md) · report [`../reports/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-report.md`](../reports/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-report.md)  
**Related contracts:** [`2026-05-30-rttp-exterior-lane-trunk-merge-design.md`](2026-05-30-rttp-exterior-lane-trunk-merge-design.md) (ELCP-TM §4.2–§4.3) · [`2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md`](2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md) (FL-06) · [`2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`](2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md) §A5  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Implementation plan:** [`../plans/2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy.md`](../plans/2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy.md)  
**F1.1 forensic (read-only, CLOSED):** [`2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-design.md`](2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-design.md) · report [`../reports/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-report.md`](../reports/2026-05-27-rttp-elcp-rf-f1.1-private-route-overlap-forensic-report.md)

**Korean title (reference):** private route overlap / shareable trunk reservation policy (bounded B-spec)

**Owner module (E0 nomination):** `django_apps/asteroid_lab/optimization/commit/incremental_commit._private_route_cell_overlap`

---

## §1 — Executive summary

**E0 (CLOSED)** nominated exactly one bounded B-spec on `_private_route_cell_overlap`: **23/34** stale rows are `private_route_overlap`; verdict **`ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT`**. Failures are not “no route” — commit-time reprobe is **reachable**, then post-probe reservation rejects via **private overlap** outside shareable trunk allowance.

**F0 sole question:**

```text
When commit-time reprobe finds a reachable route, why does _private_route_cell_overlap
reject cells that may be reusable shareable trunk cells, and what bounded policy change
safely distinguishes illegal private overlap from valid shared trunk reuse?
```

**F0 outcome contract (C + A):**

```text
F0 primary success: safety-first bounded policy correctness (definitions, invariants, evaluation order, test obligations).
F0 output: design spec only — no django_apps/ production edits.
F1 acceptance (B): measurable Gate A unblock while preserving private-approach safety regressions.
```

**F0 approach (normative):** **Layered contract (Approach 3)** — F1 implements **F1a (shareable-set alignment)** then **F1b (reservation-delta + committed growth alignment)**. Spine TM guard ships with F1a or immediately before F1b.

**Explicitly NOT F0 / F1 scope in this spec:**

```text
inlet_on_shared_transport policy (11/34 — separate subtrack)
lane_capacity_shortfall B-spec (BLOCKED per C0/D0/E0)
default selection_mode rollout
broad commit policy rewrite
validation repair
replay · NDJSON · solver_summary as algorithm input
new CommitConflictReason enums
```

---

## §2 — Problem statement (current vs target)

### §2.1 Three-axis mismatch (E0 evidence)

| Axis | ELCP-TM / F0 target | Current production (E0 replay baseline) |
|------|---------------------|----------------------------------------|
| **Shareable scope** | `⋃ active lane trunk_cells` (+ prospective `new_trunk` per §3.1) | `lane_shareable = trunk_row_pre ∪ tm_new_trunk` (current lane only) |
| **Committed growth** | `committed_route_cells \|= branch ∪ new_trunk` (no reused re-insert) | `committed_route_cells \|= full outcome.route_cells` (augment + stub merge) |
| **Overlap input** | `ReservationCandidateCells` after §4 pipeline | `_private_route_cell_overlap(merged_full_route, …)` |

E0 `shareable_trunk_undercoverage` (overlap ∈ `trunk_mask` ∉ `lane_shareable`) signals **shareable scope** drift. E0 `spine_augmentation_conflict` class signals **overlap input** drift (path-exterior cells entering overlap).

### §2.2 Safety principle (non-negotiable)

```text
Allow only legal shared trunk reuse.
Continue rejecting illegal private approach overlap (parallel void highway / peer branch corridor).
```

Widening shareability MUST NOT treat arbitrary `committed_route_cells` or full probe paths as trunk.

---

## §3 — Policy definitions

### §3.1 `ShareableTrunkCells`

At commit attempt *t*:

```text
ShareableTrunkCells =
  ⋃ { s.trunk_cells | s ∈ trunk_states, s.active, s.transport_kind == candidate.transport_kind }
```

**Prospective trunk (normative, not optional):**

```text
ShareableTrunkCells MAY include prospective_new_trunk_cells for the current attempt only when
those cells are explicitly classified as trunk by the ELCP partition (partition new_trunk_cells)
and match candidate.transport_kind.

ShareableTrunkCells MUST NOT include:
  branch_cells
  output_stub-only cells (unless also classified as trunk by partition — normally excluded)
  spine augment cells
  arbitrary committed_route_cells merely because they appear in the candidate route
  skeleton.trunk_mask_cells on ELCP paths (non-ELCP default remains skeleton.trunk_mask_cells per §4.1)
```

**ELCP precedence:** `shareable_at_commit` MUST use active-lane trunk union per above, **NOT** lane-local `trunk_row_pre` alone. Code may retain parameter name `lane_shareable` but semantics MUST match `ShareableTrunkCells`.

### §3.2 `ReservationCandidateCells`

**ELCP base delta:**

```text
base_cells = frozenset(branch_cells) | frozenset(new_trunk_cells)
reused_trunk_cells MUST NOT be included in base_cells
```

**FL-06 stub inclusion (step 3 — bounded):**

```text
Apply FL-06 stub inclusion to base_cells, using path-derived cells only to identify the
legally required output_stub attachment. Path-derived cells MUST NOT widen
ReservationCandidateCells beyond branch ∪ new_trunk ∪ legally required stub cells.

The full probe path MUST NOT re-enter ReservationCandidateCells.
```

**Spine augment (step 4 — bounded):**

```text
Spine augment cells MAY enter ReservationCandidateCells only if they are classified as
trunk-compatible transport by TM evidence or are required by FL-06 output-stub reservation rules.

Spine augment MUST NOT promote a private approach branch into shareable trunk.
```

**Final:**

```text
ReservationCandidateCells =
  stub_aligned_cells ∪ (spine_delta ∩ trunk_compatible_or_fl06_required)
```

where `spine_delta` is augment output minus pre-augment stub-aligned set.

### §3.3 `PrivateRouteOverlap`

```text
PrivateRouteOverlap =
  (ReservationCandidateCells ∩ CommittedRouteCells) \ ShareableTrunkCells

Non-empty PrivateRouteOverlap → CommitConflictReason.ROUTE_CELL_CONFLICT
```

Predicate implementation MAY remain `_private_route_cell_overlap(reservation_candidate_cells, committed_route_cells, shareable_trunk_cells=shareable_at_commit)`.

### §3.4 Illegal private approach

Overlap cell ∈ `CommittedRouteCells` \ `ShareableTrunkCells` where the cell is part of another extractor’s **branch corridor** (not trunk evidence) — includes narrow-corridor forced stub on peer private cell (`test_private_approach_overlap_still_route_cell_conflict` class).

---

## §4 — Overlap evaluation order (normative pipeline)

Order is **fixed**. Reordering steps is an F0 contract violation.

### §4.1 ELCP commit attempt

```text
(0) Preconditions
    Rebuild domain; fill-first assign lane L; commit-time reprobe reachable

(1) Partition route (ELCP-TM)
    branch_cells, reused_trunk_cells, new_trunk_cells
    prospective_new_trunk_cells := new_trunk_cells only

(2) Base reservation delta
    base_cells := branch_cells ∪ new_trunk_cells (no reused)

(3) FL-06 stub rule
    stub_aligned_cells via FL-06 on base_cells (§3.2 bounds)
    None → OUTPUT_STUB_NOT_RESERVED (stop)

(4) Bounded spine augment (TM guard)
    shareable_preview := ShareableTrunkCells (§3.1, includes prospective new_trunk)
    augment toward first attachment to shareable_preview; SPINE-G1..G4 (§4.2)

(5) ReservationCandidateCells
    per §3.2 final formula

(6) ShareableTrunkCells (commit-time)
    shareable_at_commit per §3.1 (same set as step 4 preview — no widening)

(7) Private overlap check
    _private_route_cell_overlap(ReservationCandidateCells, CommittedRouteCells, shareable_at_commit)
    non-empty → ROUTE_CELL_CONFLICT (stop)

(8) Post-overlap guards
    occupied_cell_conflict, protected_corridor, transport_kind, FOT, etc. (unchanged relative order)

(9) On success — committed update target semantics (F1b only)
    committed_route_cells |= ReservationCandidateCells
    MUST NOT |= full augmented probe path when ELCP-TM delta semantics apply

    F1a MAY leave committed growth unchanged if explicitly documented as transitional in the F1 plan,
    but F1b MUST close committed-growth drift.
```

### §4.2 Spine augment guard (SPINE-G*)

| ID | Rule |
|----|------|
| SPINE-G1 | Extension stops at first cell ∈ `shareable_at_commit` (preview). |
| SPINE-G2 | Traversal MUST NOT step through `CommittedRouteCells \ ShareableTrunkCells` (private corridor). |
| SPINE-G3 | Spine-only cells MUST NOT be treated as trunk for shareability (INV-S4). |
| SPINE-G4 | Augment MUST NOT expand `ReservationCandidateCells` beyond stub→trunk attachment + first trunk touch. |

### §4.3 Non-ELCP branch

Steps (1)(2) use probe path cells (minus occupied). Step (6) uses `skeleton.trunk_mask_cells`. Steps (3)(4)(5)(7) apply with non-ELCP shareable default. Step (9) F1b alignment applies where ELCP-TM is disabled (existing A3.1 behavior preserved).

### §4.4 Conflict reasons

F0 adds **no** new `CommitConflictReason` values. Policy change affects **which cells** constitute private overlap, not the reason enum.

---

## §5 — Safety invariants

| ID | Invariant |
|----|-----------|
| INV-S1 | `ShareableTrunkCells` ⊆ trunk evidence (lane `trunk_states`); never “all `committed_route_cells`”. |
| INV-S2 | No shareability across `transport_kind` mismatch. |
| INV-S3 | Private approach overlap MUST remain rejected (narrow corridor / forced stub class). |
| INV-S4 | Widening shareability MUST NOT add cells solely because they appear in non-trunk branches. |
| INV-S5 | No validation repair; no replay/NDJSON/metrics as algorithm input. |
| INV-S6 | Full probe path MUST NOT be overlap input (only `ReservationCandidateCells`). |

---

## §6 — F1 implementation phases (reference)

| Phase | Scope | Closes |
|-------|--------|--------|
| **F1a** | §3.1 `shareable_at_commit`; §4 steps (5)(6)(7) on `ReservationCandidateCells`; SPINE-G* | Shareable scope + overlap input |
| **F1b** | §4 steps (1)(2)(9); `committed_route_cells` delta growth | Committed growth drift |
| **F1c** | E0 harness replay contract update; Tier G investigation metrics | Forensic parity + Gate A measurement |

**F1 measurable acceptance (B — not F0 gate):**

```text
G1: E0 replay under F1 contract reduces E0 `private_route_overlap` mechanism rows by ≥50%
    from the 23-row baseline (Gate A overlap-pack stale universe).

Guards:
  Tier S safety tests: 0 regressions
  D0 investigation regression: test_gate_a_elcp_d0_overlap_stale_attribution remains green
```

If F1a alone does not meet G1, F1b is **required** before closing F1.

---

## §7 — Test obligations (F0 designs; F1 implements)

### §7.1 Tier S — Safety (F1 MUST pass)

| ID | Existing test / class |
|----|------------------------|
| S1 | `test_private_route_overlap_excludes_skeleton_trunk_cells` |
| S2 | `test_private_approach_overlap_still_route_cell_conflict` |
| S3 | `test_wrong_transport_kind_still_blocked` |
| S4 | `test_two_extractors_may_share_skeleton_trunk_spine` |

### §7.2 Tier C — Contract (F1 new or extended unit)

| ID | Proves |
|----|--------|
| C1 | `shareable_at_commit` == active trunk union + partition `new_trunk` only |
| C2 | `branch_cells` ∉ shareable; peer branch overlap → private non-empty |
| C3 | `reused_trunk_cells` ∉ `ReservationCandidateCells`; trunk reuse → empty private |
| C4 | Spine stops at shareable preview; excess augment ∉ `ReservationCandidateCells` |
| C5 | FL-06 legally required stub ∈ `ReservationCandidateCells` when reservable |

### §7.3 Tier G — Gate A measurable (F1 acceptance)

| ID | Proves |
|----|--------|
| G1 | E0 34-row replay: `private_route_overlap` mechanism rows ≥50% reduction from 23 baseline |
| G2 | `tests/investigation/test_rttp_elcp_rf_d0_stale_attribution.py` Gate A green |
| G3 | Tier S suite green after G1 run |

F0 does **not** implement tests or production code.

---

## §8 — Evidence and module boundaries

### §8.1 Evidence SoT (read-only for F0)

| Source | Use |
|--------|-----|
| [`2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-report.md`](../reports/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-report.md) | 23/34 `private_route_overlap`; owner nomination |
| [`2026-05-30-rttp-exterior-lane-trunk-merge-design.md`](2026-05-30-rttp-exterior-lane-trunk-merge-design.md) §4.2–§4.3 | Trunk shareability + spine guard intent |
| `harness/investigation/rttp_elcp_e0_reservation_mechanism.py` | E0 replay baseline (F1c updates contract) |
| `incremental_commit.py` | `_private_route_cell_overlap`, `_augment_route_cells_with_output_spine`, ELCP loop |
| `exterior_lane_trunk.shareable_trunk_cells_from_states` | Union helper (must drive ELCP shareable) |

### §8.2 Module boundaries (F1)

```text
exterior_lane_trunk.py     — partition, shareable_trunk_cells_from_states (no policy invention)
incremental_commit.py      — pipeline §4; overlap predicate; committed growth (F1b)
harness/investigation/     — F1c replay only; not algorithm input
validation                 — read-only; no repair
selection                  — out of scope
```

---

## §9 — F0 scope boundary and status

| Rule | Value |
|------|--------|
| F0 edits | `docs/superpowers/specs/` (this document) only |
| Production | **No** `django_apps/` changes in F0 |
| Plans | F1 plan created after user approves this spec (writing-plans skill) |
| Parent queue | **P1-ELCP-RF** remains REOPENED until F1 closes nominated B-spec |
| Status | **Approved for planning** — ready for implementation plan, **not** implementation |

### §9.1 Lineage

```text
D0 CLOSED → E0 CLOSED (nominate 1 B-spec) → F0 APPROVED (policy contract) → F1 (F1a→F1b→F1c)
```

### §9.2 E0 harness replay note (F1c)

E0 `ElcpE0MechanismClass.private_route_overlap` classification MUST be recomputed under §4 pipeline when measuring G1. Mechanism class name is retained; replay rules change to match F0 contract.

---

## §10 — Acceptance (F0 document only)

- [x] Definitions §3.1–§3.4 with prospective trunk and spine bounds
- [x] Normative evaluation order §4.1–§4.3
- [x] Safety invariants §5
- [x] F1 phase map + G1 wording §6
- [x] Test obligations §7
- [x] Scope: design-only, no production §9
- [x] No TBD / TODO placeholders

**F0 spec CLOSED for design when:** user reviews this file and approves → invoke **writing-plans** for F1 implementation plan.
