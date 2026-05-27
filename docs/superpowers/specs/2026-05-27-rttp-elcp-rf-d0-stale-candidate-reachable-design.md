# P1-ELCP-RF-D0 — stale_candidate_reachable Commit-Time Drift Investigation — Design Spec

**Date:** 2026-05-27  
**Status:** **CLOSED** (2026-05-27 — D0 report published)  
**Report:** [`../reports/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md`](../reports/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md)  
**Document type:** Read-only regression forensics (E-track, **Layer 2 stale attribution**)  
**Work classification:** documentation · regression forensics (no production behavior change)  
**Parent (REOPENED):** [`2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md`](2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md)  
**Prerequisite (CLOSED):** [`2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-design.md`](2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-design.md) · report [`../reports/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md`](../reports/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md)  
**Implementation plan:** [`../plans/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable.md`](../plans/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable.md)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Korean title (reference):** overlap-pack stale_candidate_reachable commit-time drift forensic 조사

---

## §1 — Executive summary

**C0 (CLOSED)** confirmed overlap-pack raises Gate A `primary_committed_count` **3 → 7** on the same SHA while making `stale_candidate_reachable` the dominant failed bucket (**56.7%** of overlap-pack failures). `lane_capacity_shortfall` B-spec re-gate remains **BLOCKED**.

**D0 sole question (Layer 2 — stale subset only):**

```text
D0 asks why route-feasible candidates become stale/uncommitted under accumulated
commit-time route_domain and reservations, especially after B1 overlap-pack
expands commit_order from 59 to 67.
```

**Normative opening (precise stale definition):**

```text
D0 asks why candidates that were route-feasible before commit remain reachable
under commit-time reprobe but fail to become post-probe committed under the
accumulated route_domain and reservations, especially after B1 overlap-pack
expands commit_order from 59 to 67.
```

Per RF §5.2 and [`asteroid_lab_07_incremental_commit.md`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md): `stale_candidate_reachable` means `candidate.reachable`, commit-time `probe.reachable`, and **not** `post_probe_committed`. D0 does **not** classify these rows as commit-time probe-unreachable.

**Explicitly NOT D0:**

```text
Prove that overlap-pack caused stale_candidate_reachable (causal claim)
lane_capacity_shortfall B-spec implementation or nomination
Commit policy / default GREEDY_REGRET change
Replay · NDJSON · solver_summary as algorithm input
C0 verdict re-litigation (carry-forward §1 only)
Baseline per-candidate deep attribution (aggregate appendix only)
Counterfactual reprobe at selection-time domain (optional future appendix)
```

**Outcome:** One `ElcpD0Verdict` + full 34-row attribution artifact + next-track hint (no B-spec nomination).

---

## §2 — Evidence rules

### §2.1 Primary SoT — overlap-pack stale universe

```text
D0 primary SoT is per-stale attribution over GREEDY_REGRET_OVERLAP_PACK on Gate A
(rttp-core-recovery-test-map), same RF.1 / C0 pipeline config.

Only ledger rows with probe_failure_class == stale_candidate_reachable in the
overlap-pack commit_order universe are eligible for primary attribution.
```

| Field | Value |
|-------|--------|
| `selection_mode` | `GREEDY_REGRET_OVERLAP_PACK` only (deep) |
| Slug | `rttp-core-recovery-test-map` |
| Policies | `INTERIOR_AND_RIM`, `OUTWARD_FROM_RIM`, `PLATFORM_FALLBACK_WHEN_STUB_BLOCKED` |
| ELCP | `exterior_lane_plan` on first `incremental_commit` |
| SHA | Fresh `git rev-parse HEAD` recorded in report |
| Expected stale row count | **34** on current C0 SHA/config (investigation test constant only) |

### §2.2 Baseline role — aggregate contrast only

```text
GREEDY_REGRET baseline is retained as aggregate contrast only:
commit_order_len, primary_committed_count, stale_candidate_reachable_count,
lane_capacity_shortfall_count, stale ratio.

Baseline stale rows are NOT subject to mandatory per-candidate deep attribution in D0.
```

C0 dual-run table is **carry-forward** in report §1 (may cite C0 report; fresh overlap run is D0 primary).

### §2.3 Selection-time domain proxy

Selection-time `route_domain` snapshots are **not** reconstructed. “Originally route-feasible” uses:

- `candidate.reachable == True` (required for stale class)
- `candidate.route_probe_start`, `candidate.route_probe_cost` (DTO reference)

Commit-time truth: M1 mirror at `commit_index` (production helper parity).

### §2.4 Attribution signal — non-causal

```text
new_blocking_cells_since_last_commit_count is attribution evidence, not by itself
proof that the immediately preceding commit caused the stale failure.
```

Same for `new_blocking_cells_sample` (bounded coord list).

### §2.5 Precedence

```text
1. Fresh overlap-pack run + 34-row table WINS for D0 verdict.
2. C0 aggregates are appendix / §1 carry-forward only.
3. RF frozen 59/27 stale counts are historical narrative only.
```

---

## §3 — Measurement contract

### §3.1 Primary capture

Same pattern as C0: patch first `incremental_commit` in `run_rttp_pipeline` with `selection_mode=GREEDY_REGRET_OVERLAP_PACK`. Reuse `build_gate_a_rf1_inputs` from [`rttp_elcp_c0_dual_mode.py`](../../../harness/investigation/rttp_elcp_c0_dual_mode.py).

### §3.2 M1 mirror + stale filter

1. `build_elcp_primary_mirror_ledger` on captured inputs.
2. `assert_mirror_parity(production, mirror)`.
3. `stale_rows = [r for r in ledger if r.probe_failure_class == STALE_CANDIDATE_REACHABLE]`.
4. `enrich_stale_attribution_rows(...)` → `ElcpStaleAttributionRow` (§3.4).

### §3.3 Domain diff (Approach 2)

During mirror replay (investigation-only), track after each **successful** commit:

- `committed_route_cells`, `committed_occupied` snapshot.

At each stale `commit_index`, compute cells in `(route ∪ occupied)` at attempt that were absent after the previous successful commit:

- `new_blocking_cells_since_last_commit_count = len(diff)`
- `new_blocking_cells_sample = first 10 coords` sorted lexicographically `(x, y)`

If no prior successful commit: count vs empty set; document in report.

### §3.4 `ElcpStaleAttributionRow` (minimum schema)

| Field | Type / notes |
|-------|----------------|
| `commit_index` | int |
| `candidate_id` | str |
| `probe_failure_class` | always `stale_candidate_reachable` |
| `stale_attribution_class` | `ElcpStaleAttributionClass` |
| `commit_conflict_reason` | `CommitConflictReason` value or null |
| `candidate_route_probe_reachable` | bool (`candidate.reachable`) |
| `commit_probe_reachable` | bool |
| `probe_start` | coord or null |
| `candidate_route_probe_start` | coord or null from DTO |
| `committed_route_cell_count` | int |
| `new_blocking_cells_since_last_commit_count` | int (attribution signal; §2.4) |
| `new_blocking_cells_sample` | ≤10 coords |
| `probe_expanded_nodes` | int or null |
| `probe_max_expansions` | int |

Optional informational: `domain_version`, `deferred_retry_eligible`, `assigned_lane_id`, `git_sha`.

Full **34-row** JSON array is report SoT §4.

### §3.5 `ElcpStaleAttributionClass` (ordered first-match)

Defined in `harness/investigation/rttp_elcp_d0_stale_attribution.py`.

| Class | Rule |
|-------|------|
| `post_probe_reservation_block` | `commit_probe_reachable` and `commit_conflict_reason` ∈ **§3.5.1** |
| `post_probe_policy_block` | `commit_probe_reachable` and conflict present, not in §3.5.1 |
| `probe_start_drift` | `probe_start` and `candidate_route_probe_start` both non-null and unequal |
| `goal_set_shrink` | selection had `goals_nonempty` at pool level but commit step `goals_nonempty` false for this attempt **or** commit goal count < global goal count (harness compares `probe_goal_coords` size vs commit_goals used in mirror) |
| `domain_congestion_at_commit` | RF congestion rule: `committed_route_cell_count / traversable_cell_count >= 0.15` and unreachable not already matched |
| `selection_survivability_gap` | stale row; none of above |
| `unattributed_stale` | classifier internal gap only |

#### §3.5.1 Reservation-class `CommitConflictReason` set

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

`REPROBE_FAILED` on stale rows is **unexpected** (RF.5); if present, classify `post_probe_policy_block` and flag in report §5.

### §3.6 Coverage gates (stale subset)

| Gate | Criterion |
|------|-----------|
| Row count | `len(stale_rows) == 34` (Gate A investigation test only) |
| Attribution coverage | ≥ **95%** of stale rows have class ≠ `unattributed_stale` |
| Unattributed cap | `unattributed_stale` ≤ **10%** of stale rows |

---

## §4 — Verdict contract

### §4.1 `ElcpD0Verdict` (exactly one)

| Verdict | Threshold (of stale rows, N=34) |
|---------|-----------------------------------|
| `RESERVATION_DRIFT_DOMINANT` | count(`post_probe_reservation_block`) ≥ **50%** **OR** (count with `new_blocking_cells_since_last_commit_count > 0` **and** reservation-class conflict) ≥ **50%** |
| `GOAL_OR_DOMAIN_DRIFT_DOMINANT` | count(`goal_set_shrink` + `probe_start_drift` + `domain_congestion_at_commit`) ≥ **50%** |
| `SELECTION_COMMIT_SURVIVABILITY_GAP` | count(`selection_survivability_gap`) ≥ **50%** |
| `INCONCLUSIVE_NEEDS_TELEMETRY` | no class ≥50% **or** `unattributed_stale` > **10%** |

**Tie-break:** if two verdicts ≥50%, higher count wins; if equal → `INCONCLUSIVE_NEEDS_TELEMETRY`.

D0 **does not** nominate a B-spec. §6 may suggest next track (e.g. production telemetry, selection survivability scoring) as prose only.

### §4.2 Forbidden CI assertions

```text
Full 34-row content hash / snapshot lock
Global invariant stale_count == 34 outside Gate A investigation test
```

### §4.3 Required CI assertions (Gate A investigation test only)

```text
overlap_stale_row_count == 34
attribution_coverage >= 0.95
unattributed_stale_ratio <= 0.10
verdict in ElcpD0Verdict
assert_mirror_parity on overlap primary capture
no django_apps production behavior change
```

---

## §5 — Non-goals (normative)

| Forbidden | Owner |
|-----------|--------|
| Production edits to `incremental_commit`, selection, validation | Future B-spec |
| `lane_capacity_shortfall` B-spec | BLOCKED per C0 |
| Default `GREEDY_REGRET` / overlap-pack rollout change | B1 §7 |
| Replay / NDJSON / metrics as solver input | Forbidden shortcut |
| Dual-run deep attribution on baseline 27 stale | Out of scope |
| Prove overlap-pack caused stale | §2.1 |

---

## §6 — Report deliverable

| § | Content |
|---|---------|
| §1 | C0 carry-forward aggregate (59 vs 67) |
| §2 | D0 universe: 34 overlap stale rows |
| §3 | Full `ElcpStaleAttributionClass` histogram |
| §4 | Full 34-row table + JSON |
| §5 | Drift synthesis (reservation / domain / goal / start); §2.4 non-causal note |
| §6 | `ElcpD0Verdict` + next-track hint (no B-spec) |
| Appendix | Baseline aggregate only |

**Report path:** [`../reports/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md`](../reports/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md)

---

## §7 — Execution architecture

| Component | Path |
|-----------|------|
| Harness | `harness/investigation/rttp_elcp_d0_stale_attribution.py` |
| Frozen Gate A constants | `tests/support/rttp_d0_gate_a_frozen_bounds.py` |
| Unit tests | `tests/unit/harness/test_rttp_elcp_d0_stale_attribution.py` |
| Investigation test | `tests/investigation/test_rttp_elcp_rf_d0_stale_attribution.py` |
| C0 input builder (reuse) | `harness/investigation/rttp_elcp_c0_dual_mode.py` |
| M1 mirror (reuse) | `harness/investigation/rttp_elcp_reprobe_forensics.py` |

**Not modified:** `django_apps/asteroid_lab/optimization/**` production modules.

---

## §8 — Mirror parity · risks

| Gate | Criterion |
|------|-----------|
| M1 parity | Overlap primary `CommitResult` vs mirror aggregates match (same as C0) |
| Stale ⊆ failed ledger | Every stale row is a failed attempt |
| Production diff | Zero `django_apps/` behavior change |

| Risk | Mitigation |
|------|------------|
| Stale count drifts from 34 | Constant only in Gate A test; report documents fresh N |
| Goal shrink false positives | Conservative rules; gaps → `unattributed_stale` |
| Reservation verdict over-interpretation | §2.4 non-causal wording in report §5 |

---

## §9 — Acceptance

- [ ] Overlap-pack Gate A run with primary capture + M1 parity
- [ ] 34 stale rows with full schema §3.4
- [ ] Attribution coverage ≥95%; unattributed ≤10%
- [ ] `ElcpD0Verdict` published in report §6
- [ ] C0 aggregate carry-forward in report §1
- [ ] No production behavior change
- [ ] Investigation test passes (§4.3 assertions)

```text
D0 CLOSED when report + acceptance checklist complete; does not close P1-ELCP-RF parent.
```
