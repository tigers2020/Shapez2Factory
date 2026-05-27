# P1-ELCP-RF-E0 — Post-Probe Reservation Conflict / Shared-Transport Policy Forensics — Design Spec

**Date:** 2026-05-27  
**Status:** **CLOSED** (2026-05-27 — E0 report published)  
**Report:** [`../reports/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-report.md`](../reports/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-report.md)  
**Document type:** Read-only regression forensics (E-track, **Layer 3 post-probe reservation mechanism**)  
**Work classification:** documentation · regression forensics (no production behavior change)  
**Parent (REOPENED):** [`2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md`](2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md)  
**Prerequisite (CLOSED):** [`2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-design.md`](2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-design.md) · report [`../reports/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md`](../reports/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md)  
**Related (v0.2):** [`2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`](2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md) §A5 — commit / reservation repair (nomination target class only)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Implementation plan:** [`../plans/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism.md`](../plans/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism.md)

**Korean title (reference):** post-probe reservation conflict / shared-transport policy forensic 조사

---

## §1 — Executive summary

**D0 (CLOSED)** attributed all **34/34** overlap-pack `stale_candidate_reachable` rows to `post_probe_reservation_block` with verdict **`RESERVATION_DRIFT_DOMINANT`**. Commit conflict mix on primary stale rows: **`route_cell_conflict` 22** · **`inlet_on_shared_transport` 12**. `lane_capacity_shortfall` B-spec remains **BLOCKED** (C0 carry-forward).

**E0 outcome contract (B):**

```text
read-only forensic artifact
+ ElcpE0Verdict
+ if one dominant mechanism ≥50% and owner is clear:
    nominate exactly one bounded B-spec (reservation / shared-transport only)
+ no production implementation in E0
```

**E0 evidence model (C):**

```text
E0 primary evidence is a deep mechanism decomposition of the 34 D0 stale rows.
All overlap-pack reservation-class failed rows are retained only as aggregate
appendix context to qualify or veto bounded B-spec nomination.
```

**E0 sole question (Layer 3):**

```text
Why do commit-time reachable routes fail during post-probe reservation/commit,
specifically through route_cell_conflict and inlet_on_shared_transport?
```

Per D0 and [`asteroid_lab_07_incremental_commit.md`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md): primary rows satisfy `candidate.reachable`, commit-time `probe.reachable`, and **not** `post_probe_committed`. E0 explains **how** post-probe reservation checks fail, not whether rows are stale.

**Measurement approach:** **Approach III** — mirror replay of production post-probe commit checks (Approach I) plus bounded `probe.path` / merged `route_cells` diff from M1 ledger metadata.

**Explicitly NOT E0:**

```text
lane_capacity_shortfall B-spec implementation or nomination
Default GREEDY_REGRET / GREEDY_REGRET_OVERLAP_PACK rollout change
Production edits to incremental_commit, selection, or validation
Replay · NDJSON · solver_summary as algorithm input
D0 verdict re-litigation (carry-forward §1 only)
GREEDY_REGRET baseline per-row deep dive
Prove overlap-pack caused reservation failures (causal claim)
Deep attribution on non-stale rows (appendix aggregate only)
occupied_cell_conflict and other D0 reservation-set reasons as primary deep rows
  (present only in appendix when they occur outside the 22+12 stale mix)
```

---

## §2 — Evidence rules

### §2.1 Primary SoT — D0 stale 34 rows (22+12 deep only)

```text
E0 primary SoT is per-row mechanism attribution over GREEDY_REGRET_OVERLAP_PACK on Gate A
(rttp-core-recovery-test-map), same RF.1 / C0 / D0 pipeline config.

Only ledger rows with probe_failure_class == stale_candidate_reachable are eligible
for primary deep mechanism attribution (expected N=34).

Primary deep stratification follows D0 commit_conflict_reason on stale rows:
  route_cell_conflict (expected 22)
  inlet_on_shared_transport (expected 12)

Other D0 reservation-class reasons (e.g. occupied_cell_conflict) MUST NOT be added
to primary deep when absent from the stale 34 mix.
```

| Field | Value |
|-------|--------|
| `selection_mode` | `GREEDY_REGRET_OVERLAP_PACK` only (deep) |
| Slug | `rttp-core-recovery-test-map` |
| Policies | `INTERIOR_AND_RIM`, `OUTWARD_FROM_RIM`, `PLATFORM_FALLBACK_WHEN_STUB_BLOCKED` |
| ELCP | `exterior_lane_plan` on first `incremental_commit` |
| SHA | Fresh `git rev-parse HEAD` recorded in report |
| Expected stale row count | **34** (Gate A investigation test constant only) |
| Expected conflict mix | **22** `route_cell_conflict` · **12** `inlet_on_shared_transport` (investigation constants; report documents fresh counts) |

### §2.2 Appendix SoT — all reservation-class failed rows (aggregate only)

```text
E0 appendix SoT is aggregate-only over the overlap-pack commit_order universe:

All failed ledger rows where commit_conflict_reason is in the D0 reservation-class set
(§3.5.1 of D0 spec — reproduced in §3.6 below).

Includes stale and non-stale reservation-class failures.

Appendix MUST report:
  total reservation-class failed count
  stale vs non-stale counts
  commit_conflict_reason histogram
  mechanism-family histogram (route-cell vs inlet) where derivable without per-row deep
```

**No mandatory per-row deep table** for appendix rows.

### §2.3 Baseline role

```text
GREEDY_REGRET baseline is NOT run for E0 deep or appendix.
D0/C0 aggregate carry-forward MAY appear in report §1 for narrative only.
```

### §2.4 Mechanism signal — non-causal

```text
private_overlap_cells, spine_augment_delta, and probe_vs_merged_route_diff are
mechanism attribution evidence, not by themselves proof that the immediately
preceding commit caused the failure.

Same non-causal rule as D0 §2.4 for new_blocking_cells_since_last_commit_count.
```

### §2.5 Evidence precedence

```text
1. Primary 34-row deep mechanism table WINS for ElcpE0Verdict.
2. Appendix reservation-class aggregate qualifies or vetoes B-spec nomination only.
3. D0 per-row table and verdict are carry-forward / §1 narrative only (no re-litigation).
4. RF frozen historical counts are appendix narrative only.
```

### §2.6 Appendix veto (normative)

Appendix **withholds** B-spec nomination (verdict may still be dominant) when:

```text
Appendix veto triggers only when the opposite mechanism family is >50%
among all overlap-pack reservation-class failed rows and exceeds the
primary-dominant family by at least one row.
```

| Term | Definition |
|------|------------|
| **Mechanism family (route-cell)** | `commit_conflict_reason == route_cell_conflict` **or** primary `ElcpE0MechanismClass` ∈ route-cell family (§3.5.1) |
| **Mechanism family (inlet)** | `commit_conflict_reason == inlet_on_shared_transport` **or** primary `ElcpE0MechanismClass` ∈ inlet family (§3.5.2) |
| **Primary-dominant family** | Family with ≥50% of primary 34 rows by mechanism class or conflict reason (whichever E0 uses for verdict) |
| **Opposite family** | The other family |

If appendix distribution is neutral (opposite family ≤50% or lead &lt; 1 row), appendix does **not** veto.

---

## §3 — Measurement contract

### §3.1 Primary capture

Same pattern as D0: patch first `incremental_commit` in `run_rttp_pipeline` with `selection_mode=GREEDY_REGRET_OVERLAP_PACK`. Reuse `build_gate_a_rf1_inputs` from [`rttp_elcp_c0_dual_mode.py`](../../../harness/investigation/rttp_elcp_c0_dual_mode.py).

### §3.2 M1 mirror + stale filter

1. `build_elcp_primary_mirror_ledger` on captured inputs.
2. `assert_mirror_parity(production, mirror)`.
3. `stale_rows = [r for r in ledger if r.probe_failure_class == STALE_CANDIDATE_REACHABLE]`.
4. `enrich_e0_mechanism_rows(...)` → `ElcpE0MechanismRow` (§3.4).

### §3.3 Approach III — mirror replay of post-probe checks

At each stale `commit_index`, using mirror snapshot state at attempt (investigation-only):

1. Reconstruct `route_cells` / `merged_route_cells` as production would after probe + spine augment + FL-06 stub merge (same helper chain as [`incremental_commit.py`](../../../django_apps/asteroid_lab/optimization/commit/incremental_commit.py) `_attempt_commit_one`).
2. Resolve `lane_shareable` / `shareable_trunk_cells` from ELCP ledger metadata when present (else `domain.trunk_mask_cells`).
3. Compute:
   - `private_overlap_cells` via `_private_route_cell_overlap`
   - `shareable_trunk_undercoverage_cells` — overlap ∩ `committed_route_cells` where cell ∈ trunk-capable set but ∉ `lane_shareable`
   - `spine_augment_cells` — cells in augmented route not on raw probe path cells (bounded sample ≤10)
   - `probe_path_cells` vs `merged_route_cells` symmetric diff (bounded sample ≤10 each side)
   - `output_stub_in_committed_route` — bool for inlet guard
   - `inlet_stub_adjacent_committed_route_cells` — stub neighbors ∩ `committed_route_cells` (bounded sample ≤10)
4. Classify `ElcpE0MechanismClass` (§3.5) by **ordered first-match** on replay signals, stratified by `commit_conflict_reason` where applicable.

Harness MUST import production helpers for replay (read-only); MUST NOT change production modules.

### §3.4 `ElcpE0MechanismRow` (minimum schema)

| Field | Type / notes |
|-------|----------------|
| `commit_index` | int |
| `candidate_id` | str |
| `probe_failure_class` | always `stale_candidate_reachable` |
| `commit_conflict_reason` | `route_cell_conflict` \| `inlet_on_shared_transport` (expected); other → flag |
| `elcp_e0_mechanism_class` | `ElcpE0MechanismClass` |
| `mechanism_owner_module` | str — bounded owner id (§3.5 tables) |
| `candidate_route_probe_reachable` | bool |
| `commit_probe_reachable` | bool |
| `private_overlap_cell_count` | int |
| `private_overlap_sample` | ≤10 coords |
| `shareable_trunk_undercoverage_count` | int |
| `spine_augment_cell_count` | int |
| `probe_merged_route_diff_count` | int |
| `output_stub_in_committed_route` | bool |
| `probe_expanded_nodes` | int or null |
| `probe_max_expansions` | int |
| `new_blocking_cells_since_last_commit_count` | int (carry-forward from D0; non-causal) |
| `assigned_lane_id` | str or null |
| `git_sha` | str |

Full **34-row** JSON array is report SoT §4.

### §3.5 `ElcpE0MechanismClass` (ordered first-match)

Defined in `harness/investigation/rttp_elcp_e0_reservation_mechanism.py`.

#### §3.5.1 Route-cell family (`commit_conflict_reason == route_cell_conflict`)

| Class | Replay rule | Owner module / boundary |
|-------|-------------|-------------------------|
| `private_route_overlap` | `private_overlap_cells` non-empty | `_private_route_cell_overlap` |
| `shareable_trunk_undercoverage` | undercoverage cells non-empty; private overlap empty or subset explained | ELCP `lane_shareable` / `shareable_trunk_cells_from_states` |
| `spine_augmentation_conflict` | conflict cells ⊆ spine augment delta; prior classes not matched | `_augment_route_cells_with_output_spine` |
| `probe_vs_merged_route_mismatch` | probe reachable; merged-route diff non-empty; reservation check fails | `_route_cells_from_path` + `_route_cells_with_required_output_stub` chain |
| `unattributed_route_cell_mechanism` | `route_cell_conflict` but no rule matched | — |

#### §3.5.2 Inlet family (`commit_conflict_reason == inlet_on_shared_transport`)

| Class | Replay rule | Owner module / boundary |
|-------|-------------|-------------------------|
| `inlet_stub_on_committed_route` | `output_stub_in_committed_route` | `_attempt_commit_one` inlet guard (pre-probe) |
| `inlet_stub_adjacent_shared_transport` | adjacent committed route cells non-empty; stub not in committed route | shared-transport / inlet policy (documented in [`asteroid_lab_07_incremental_commit.md`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md)) |
| `unattributed_inlet_mechanism` | `inlet_on_shared_transport` but no rule matched | — |

#### §3.5.3 Fallback

| Class | When |
|-------|------|
| `unattributed_reservation_mechanism` | unexpected conflict reason on stale row or mirror replay failure |

### §3.6 D0 reservation-class `CommitConflictReason` set (appendix eligibility)

Reproduced from D0 §3.5.1 for appendix aggregate filtering only:

```text
OVERLAP
ROUTE_CELL_CONFLICT
OCCUPIED_CELL_CONFLICT
OUTPUT_STUB_NOT_RESERVED
FIXED_OUTPUT_TRANSPORT_CONFLICT
FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE
HARD_PROTECTED_CONFLICT
INLET_ON_SHARED_TRANSPORT
```

### §3.7 Coverage gates (primary 34 rows)

**Unattributed classes** (coverage and §4.6 ratio):

```text
unattributed_route_cell_mechanism
unattributed_inlet_mechanism
unattributed_reservation_mechanism
```

Harness helper (normative):

```python
def is_unattributed_mechanism_class(cls: ElcpE0MechanismClass) -> bool:
    return cls.value.startswith("unattributed_")
```

| Gate | Criterion |
|------|-----------|
| Row count | `len(stale_rows) == 34` (Gate A investigation test only) |
| Mechanism coverage | ≥ **95%** of stale rows have `not is_unattributed_mechanism_class(...)` |
| Unattributed cap | unattributed ≤ **10%** of stale rows |
| Mirror parity | `assert_mirror_parity` PASS on overlap primary capture |

---

## §4 — Verdict and B-spec nomination

### §4.1 `ElcpE0Verdict` (exactly one — primary 34 rows)

Count rows by **mechanism family** (route-cell §3.5.1 vs inlet §3.5.2), not by `commit_conflict_reason` alone.

| Verdict | Threshold (N=34) |
|---------|------------------|
| `ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT` | route-cell family ≥ **50%** |
| `INLET_SHARED_TRANSPORT_POLICY_DOMINANT` | inlet family ≥ **50%** |
| `SPLIT_RESERVATION_POLICY_NEEDS_DECOMPOSITION` | see **Verdict precedence** step 2 or 4 |
| `INCONCLUSIVE_NEEDS_TELEMETRY` | see **Verdict precedence** step 1 or 5 |

**Verdict precedence** (evaluate in order; first match wins):

```text
1. mirror parity fail or unattributed >10% → INCONCLUSIVE_NEEDS_TELEMETRY
2. appendix veto (§2.6) → SPLIT_RESERVATION_POLICY_NEEDS_DECOMPOSITION
3. one mechanism family ≥50% → ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT
   or INLET_SHARED_TRANSPORT_POLICY_DOMINANT (higher count if both ≥50%; equal → INCONCLUSIVE)
4. both families ≥35% and neither reaches 50% → SPLIT_RESERVATION_POLICY_NEEDS_DECOMPOSITION
5. otherwise → INCONCLUSIVE_NEEDS_TELEMETRY
```

**Verdict vs nomination:** `ElcpE0Verdict` MAY be `ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT` while B-spec nomination is **withheld** per §4.3.

### §4.2 Nomination guards (all required for nomination)

```text
1. ElcpE0Verdict is ROUTE_CELL_* or INLET_* (not SPLIT_* or INCONCLUSIVE_*)
2. Appendix does not veto (§2.6)
3. Proposed B-spec is bounded to post-probe reservation / shared-transport policy
4. No lane_capacity_shortfall remediation
5. No default selection_mode or commit policy rollout
6. No production implementation in E0
7. Owner clarity (§4.3) — at most one bounded B-spec nominated
```

### §4.3 Owner clarity — verdict/nomination split

A bounded B-spec MAY be nominated only if **either**:

```text
1. One ElcpE0MechanismClass is ≥50% within the primary 34-row table, or
2. Multiple sub-mechanisms in the dominant family share the same owner module/function
   boundary (§3.5 owner column).
```

If the dominant family is route-cell but owners split across `private_route_overlap`,
`shareable_trunk_undercoverage`, `spine_augmentation_conflict`, and
`probe_vs_merged_route_mismatch` without a single class ≥50% or shared owner:

```text
ElcpE0Verdict MAY be ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT
B-spec nomination MUST be withheld (report §6 states owner split).
```

Same rule for inlet family sub-mechanisms.

### §4.4 Nomination mapping (when §4.2–§4.3 pass)

| Verdict | Nominated B-spec scope (prose title only — implementation is a later track) |
|---------|--------------------------------------------------------------------------------|
| `ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT` + owner clear | One bounded B-spec: route-cell reservation / `shareable_trunk` / private overlap / spine augmentation semantics (v0.2 A5-2 class) |
| `INLET_SHARED_TRANSPORT_POLICY_DOMINANT` + owner clear | One bounded B-spec: `inlet_on_shared_transport` guard or stub-vs-shared-route policy |
| `SPLIT_*` / `INCONCLUSIVE_*` / owner split / appendix veto | **No nomination** — open forensic subtrack or telemetry |

E0 publishes nomination as **title + owner module + primary row evidence** only; no implementation plan in E0 spec.

### §4.5 Forbidden CI assertions

```text
Full 34-row content hash / snapshot lock
Global invariant stale_count == 34 outside Gate A investigation test
Mandatory B-spec nomination when verdict is dominant
```

### §4.6 Required CI assertions (Gate A investigation test only)

```text
overlap_stale_row_count == 34
mechanism_coverage >= 0.95  # using is_unattributed_mechanism_class (§3.7)
unattributed_mechanism_ratio <= 0.10
verdict in ElcpE0Verdict
assert_mirror_parity on overlap primary capture
no django_apps production behavior change
```

---

## §5 — Non-goals (normative)

| Forbidden | Owner |
|-----------|--------|
| Production edits to `incremental_commit`, selection, validation | Nominated B-spec track |
| `lane_capacity_shortfall` B-spec | BLOCKED per C0/D0 |
| Default `GREEDY_REGRET` / overlap-pack rollout | B1 §7 |
| Replay / NDJSON / metrics as solver input | Forbidden shortcut |
| Per-row deep on appendix non-stale rows | Out of scope |
| Dual B-spec nomination | E0 contract |
| D0 verdict re-litigation | §2.5 |

---

## §6 — Report deliverable

| § | Content |
|---|---------|
| §1 | D0 carry-forward (`RESERVATION_DRIFT_DOMINANT`, 22/12 mix) |
| §2 | E0 primary universe (34 stale rows) |
| §3 | `ElcpE0MechanismClass` histogram + owner rollup |
| §4 | Full 34-row table + JSON |
| §5 | Mechanism synthesis (non-causal §2.4); probe vs merged route notes |
| §6 | `ElcpE0Verdict` + B-spec nomination block (or explicit withheld reason) |
| Appendix A | Reservation-class failed aggregate (§2.2) + veto qualification |
| Appendix B | Optional: stale vs non-stale ratio narrative |

**Report path:** [`../reports/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-report.md`](../reports/2026-05-27-rttp-elcp-rf-e0-post-probe-reservation-mechanism-report.md) *(created at E0 close)*

---

## §7 — Execution architecture

| Component | Path |
|-----------|------|
| Harness | `harness/investigation/rttp_elcp_e0_reservation_mechanism.py` |
| Frozen Gate A constants | `tests/support/rttp_e0_gate_a_frozen_bounds.py` |
| Unit tests | `tests/unit/harness/test_rttp_elcp_e0_reservation_mechanism.py` |
| Investigation test | `tests/investigation/test_rttp_elcp_rf_e0_reservation_mechanism.py` |
| D0 harness (reuse) | `harness/investigation/rttp_elcp_d0_stale_attribution.py` |
| C0 input builder (reuse) | `harness/investigation/rttp_elcp_c0_dual_mode.py` |
| M1 mirror (reuse) | `harness/investigation/rttp_elcp_reprobe_forensics.py` |

**Not modified:** `django_apps/asteroid_lab/optimization/**` production modules.

---

## §8 — Mirror parity · risks

| Gate | Criterion |
|------|-----------|
| M1 parity | Overlap primary `CommitResult` vs mirror aggregates match (same as D0) |
| Stale ⊆ failed ledger | Every primary row is a failed stale attempt |
| Production diff | Zero `django_apps/` behavior change |

| Risk | Mitigation |
|------|------------|
| Stale count drifts from 34 | Constants only in Gate A test; report documents fresh N |
| Harness / production helper drift | Unit tests on synthetic mirror fixtures; parity gate |
| Verdict without nomination confusion | Report §6 explicit withheld-reason enum |
| Appendix veto over-use | §2.6 numeric threshold (>50% and ≥1 row lead) |

---

## §9 — Acceptance

- [x] Overlap-pack Gate A run with primary capture + M1 parity
- [x] 34 stale rows with full schema §3.4
- [x] Mechanism coverage ≥95%; unattributed ≤10%
- [x] Appendix aggregate §2.2 published
- [x] `ElcpE0Verdict` published in report §6
- [x] B-spec nomination or explicit withheld reason (§4.3–§4.4)
- [x] D0 carry-forward in report §1
- [x] No production behavior change
- [x] Investigation test passes (§4.6 assertions)

```text
E0 CLOSED when report + acceptance checklist complete; does not close P1-ELCP-RF parent.
Nominated B-spec (if any) opens a separate bounded implementation track (not E0).
```
