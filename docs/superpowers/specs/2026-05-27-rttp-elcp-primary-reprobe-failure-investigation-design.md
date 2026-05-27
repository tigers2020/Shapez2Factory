# RTTP ELCP Primary Reprobe Failure Investigation — Design Spec

**Date:** 2026-05-27  
**Status:** REOPENED (2026-05-27 — universe sanity: forensics scope = `commit_order` only; B-spec withheld)  
**Document type:** Read-only regression forensics (E-track)  
**Work classification:** documentation · regression forensics (no production behavior change)  
**Scope name:** **P1-ELCP-RF** — Primary ELCP commit-time reprobe failure analysis for large RTTP maps  
**Parent (P0 CLOSED):** [`2026-05-27-rttp-lns-elcp-propagation-design.md`](2026-05-27-rttp-lns-elcp-propagation-design.md) (LNS ELCP context propagation)  
**Related contracts:** [`2026-05-30-rttp-exterior-lane-capacity-planner-design.md`](2026-05-30-rttp-exterior-lane-capacity-planner-design.md) (ELCP) · [`2026-05-30-rttp-exterior-lane-trunk-merge-design.md`](2026-05-30-rttp-exterior-lane-trunk-merge-design.md) (ELCP-TM) · [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md) (commit-time reprobe canon)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Implementation plan:** [`../plans/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation.md`](../plans/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation.md)

**Korean title (reference):** RTTP ELCP primary commit reprobe 실패 forensic 조사

---

## §1 — Executive summary

After **LNS ELCP propagation (P0)** closed the wiring bug (Run #238 Case A — non-ELCP LNS retry masking primary ELCP results), **post-fix runs (#239–241)** still show **sparse primary commits** (~3) with a **high `reprobe_failed` conflict rate** on large recovery maps. Throughput shortfall remains a separate P1; this track does **not** fix throughput.

**Problem in one line:** commit failures are recorded overwhelmingly as `CommitConflictReason.REPROBE_FAILED`, but that label **collapses** distinct failure modes (probe start blocked, fill-first lane exhaustion, probe unreachable, budget cutoff, post-probe commit checks, candidate-time vs commit-time reachability drift).

**Goal:**

```text
Decompose primary ELCP commit-time REPROBE_FAILED mass into a forensic taxonomy,
map buckets to owner modules,
audit deferred-retry eligibility vs outcomes,
and nominate exactly ONE dominant bucket for a follow-up bounded B-spec —
without changing production commit policy, probe semantics, or validation behavior.
```

**Approach:** Read-only **A-track** — **Approach I** (harness mirror loop) primary + **Approach III** (`algorithm_steps` aggregate forensics) secondary. **Approach II** (optional `forensics_collector` on `incremental_commit`) is **rejected** for this spec.

---

## §2 — Evidence

### §2.1 Primary SoT — Post-fix ELCP primary replay

| Field | Value |
|-------|--------|
| Map slug | `rttp-core-recovery-test-map` (import via [`import_rttp_core_recovery_test_map`](../../../django_apps/asteroid_lab/management/commands/import_rttp_core_recovery_test_map.py)) |
| Code baseline | **Current master** after LNS ELCP propagation P0 merge (PR [#110](https://github.com/tigers2020/Shapez2Factory/pull/110)) |
| Reference runs | **#239–241** (post-fix: ~3 committed / 3 assignments, `validation_passed`, no `route_without_lane_assignment`; high primary `reprobe_failed`) |
| Authority | **Primary taxonomy SoT** — all bucket percentages, owner matrix decisions, and B-spec nomination |

**Observed signals (aggregate, from parent spec + post-fix readback):**

- Primary `incremental_commit` with ELCP active
- Low `committed_ids` cardinality
- High `conflict_count` with `reason == reprobe_failed`
- Non-zero `lane_capacity_shortfall_count` / `route_feasible_shortfall_count` on ELCP path (see [`incremental_commit.py`](../../../django_apps/asteroid_lab/optimization/commit/incremental_commit.py))

**Purpose:**

- Current P1 high `REPROBE_FAILED` sub-bucket decomposition
- Attempt-ledger + harness-signal classification
- Deferred-retry eligibility audit on primary conflicts
- Recovery evidence comparison (route/domain delta summary)

### §2.2 Historical appendix — Frozen Run #238

| Field | Value |
|-------|--------|
| Run | **#238** |
| `project_id` | `23` |
| `run_key` | `rttp-b0751b201d8f` |
| Authority | **Historical appendix only** — not primary taxonomy SoT |

**Historical chain (frozen narrative):**

| Stage | ELCP | committed | conflicts (approx.) | Notes |
|-------|------|-----------|---------------------|-------|
| Primary `incremental_commit` | ON | 3 | ~56 | High `reprobe_failed`; ELCP path used |
| `run_local_lns` retry (pre-P0) | **OFF** | 17 | ~8 | `exterior_lane_assignments=[]` — masked primary failure |
| Validation | plan present | — | — | `route_without_lane_assignment` (P0 symptom) |

**Purpose:**

- Pre/post P0 narrative (how LNS bypass obscured primary failure)
- Overlap comparison between historical symptoms and post-fix taxonomy
- **Not** a primary fix target or bucket-percentage authority

### §2.3 Evidence precedence (normative)

```text
1. Primary taxonomy decisions MUST use post-fix replay (§2.1).
2. Run #238 MAY support historical narrative and overlap tables only (§2.2).
3. If #238 and post-fix replay disagree on bucket mix or dominant cause, post-fix replay WINS.
4. conflicts[] alone MUST NOT be used as taxonomy SoT (see §5).
```

---

## §3 — Non-goals (A phase)

| Forbidden in A | Follow-up track |
|----------------|-----------------|
| Probe `max_expansions` / budget changes | B-spec after dominant bucket |
| Tie-break / trunk ordering / fill-first policy changes | ELCP-TM / assignment B-spec |
| Lane merge / capacity planner edits | ELCP policy spec |
| `deferred_retry_execute` policy changes | Separate P1 note (parent propagation spec) |
| `incremental_commit_macro` ELCP propagation | Separate ticket |
| Production `route_domain` builder changes | Domain / reservation B-spec |
| Validation rule change / assert weakening / repair in validation | Forbidden shortcut (standing) |
| LNS retry behavior changes | CLOSED under P0 spec |
| Throughput / placement goal tuning | Gate B / Track D |
| Replay / artifact / metrics as **solver input** | Forbidden shortcut (standing) |
| **Approach II** — `forensics_collector` on production `incremental_commit` | Rejected — touches production commit path |
| Slug replacement or map mutation | A/B slug track |

### §3.1 Investigation-only vs production contract (normative)

```text
This investigation may introduce test-only / harness-only classifiers and ledgers,
but MUST NOT add diagnostic fields to production RouteProbeResult
or change CommitConflictReason semantics.
```

`probe_failure_class` and attempt-ledger DTOs live under `harness/investigation/` (and investigation tests) only.

---

## §4 — Investigation scope (subsections)

```text
RF.1 — Post-fix primary replay reproduction (§2.1)
RF.2 — Sub-bucket taxonomy via harness mirror + attempt ledger (§5)
RF.3 — Step forensics aggregate cross-check (Approach III)
RF.4 — Historical appendix readback (Run #238, §2.2)
RF.5 — Deferred retry shadow audit (primary REPROBE_FAILED eligibility)
RF.6 — Recovery canon comparison (primary fail vs recovery evidence JSON)
RF.7 — Owner matrix + single dominant-bucket B-spec nomination (§12)
```

**Explicit non-goal:** fixing commit count or throughput in A phase.

---

## §5 — Failure taxonomy (primary)

### §5.1 Why `conflicts[]` is insufficient

On the ELCP primary path, multiple distinct conditions append `CommitConflictReason.REPROBE_FAILED`:

| Actual condition (code path) | `CommitConflictReason` | Counter signals |
|------------------------------|------------------------|-----------------|
| `resolve_route_probe_start(...) is None` | `REPROBE_FAILED` | `route_feasible_shortfall_count` += 1 |
| `assign_fill_first_exterior_lane(...) is None` | `REPROBE_FAILED` | `lane_capacity_shortfall_count` += 1, `route_feasible_shortfall_count` += 1 |
| `probe_route` not reachable / post-probe commit fail | `REPROBE_FAILED` | probe result, later attempt outcome |

Source: [`incremental_commit.py`](../../../django_apps/asteroid_lab/optimization/commit/incremental_commit.py) ELCP branch (~L531–576) and `_attempt_commit`.

**Normative:**

```text
conflicts[].reason == reprobe_failed is NOT a diagnostic bucket.
Investigation MUST derive sub-buckets from attempt-ledger + harness signals.
```

`RouteProbeResult` has **no** `failure_reason` field (`reachable`, `cost`, `reached_goal`, `path`, `expanded_nodes` only). Do **not** add production fields; derive **`probe_failure_class`** (investigation-only enum) in harness.

### §5.2 `probe_failure_class` (investigation-only enum)

Defined in `harness/investigation/` (e.g. `ElcpProbeFailureClass` StrEnum). Assigned by **ordered rules** (first match wins unless noted):

| Class | Classification rule (harness) | Likely owner |
|-------|------------------------------|--------------|
| `start_blocked` | `probe_start is None` before fill-first | `resolve_route_probe_start` / FOT stub policy |
| `lane_capacity_shortfall` | ELCP branch: `fill_first is None` on this attempt | `exterior_lane_fill_first` / ELCP plan |
| `budget_exceeded` | `not probe.reachable` and `probe.expanded_nodes >= max_expansions` | `route_probe` |
| `probe_unreachable` | `not probe.reachable`, goals non-empty, `expanded_nodes < max_expansions` | `route_probe` / domain |
| `no_goal_cells` | commit goals empty after filter / connector off-domain | EVTC goals / goal filter |
| `post_probe_commit_fail` | fill-first OK; `_attempt_commit` returns non-commit (overlap, stub, FOT, etc.) | `incremental_commit` post-probe |
| `stale_candidate_reachable` | `candidate.reachable` and commit-time failure not explained by above | selection vs commit contract ([`asteroid_lab_07`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md)) |
| `domain_congestion` | unreachable + high committed route density (threshold documented in report) | `RouteDomainSnapshotBuilder` / reservation |
| `trunk_ordering_pressure` | fill-first OK; large `tm_new_trunk`; correlated failures on later indices (report-defined) | ELCP-TM trunk partition |
| `unknown_reprobe_failed` | no rule matched | gap — must document |

### §5.3 Attempt ledger row (minimum schema)

Each row = one `genome.commit_order` step where primary commit did not commit the candidate (or mirror stopped at same decision point as production).

| Field | Type / notes |
|-------|----------------|
| `candidate_id` | str |
| `commit_index` | int (0-based order index) |
| `candidate_reachable` | bool (candidate-phase flag) |
| `probe_start` | coord or null |
| `fill_first_ok` | bool |
| `assigned_lane_id` | str or null |
| `probe_reachable` | bool or null |
| `probe_expanded_nodes` | int or null |
| `max_expansions` | int |
| `probe_failure_class` | `ElcpProbeFailureClass` |
| `lane_capacity_shortfall_delta` | 0/1 for this attempt |
| `route_feasible_shortfall_delta` | 0/1 for this attempt |
| `commit_conflict_reason` | str or null (production enum value if mirror records conflict) |
| `domain_version` | int (after prior commits in mirror) |
| `deferred_retry_eligible` | bool (shadow rule: `REPROBE_FAILED` on primary — see §8) |

Ledger is **output-only** (JSON / report tables); not persisted as solver input.

### §5.4 Bucket coverage gates (report)

| Gate | Criterion |
|------|-----------|
| Bucket coverage | ≥ **95%** of failed attempts map to a named class (excluding `unknown`) |
| Unknown cap | `unknown_reprobe_failed` ≤ **5%** of failed attempts **or** each remainder documented with explicit gap |

---

## §6 — Investigation methods

| ID | Method | Role | A phase |
|----|--------|------|---------|
| **M1** | **Harness mirror loop (Approach I)** | Replay commit order; call same pure helpers as production ELCP path; record attempt ledger; classify `probe_failure_class` | **Primary** |
| **M2** | **Step forensics (Approach III)** | `extract_elcp_reprobe_forensics(algorithm_steps)` — `conflict_count`, `lane_capacity_shortfall_count`, `route_feasible_shortfall_count`, reprobe histogram | **Secondary** cross-check |
| **M3** | **Frozen #238 readback** | DB / `algorithm_steps` parse for appendix table | Appendix only |
| **M4** | **Deferred retry audit** | Recompute `build_deferred_retry_shadow_summary` eligibility vs primary conflicts | RF.5 |
| **M5** | **Recovery comparison** | Compare post-fix primary fail ledger aggregates vs [`docs/superpowers/reports/`](../../reports/) `2026-05-30-rttp-core-recovery-evidence-*.json` | RF.6 |

**Rejected for this spec:**

| Approach | Reason |
|----------|--------|
| **II — Optional `forensics_collector` on `incremental_commit`** | Production module touch; conflicts with “no production behavior change” bar |

**Recommended execution:** **M1 + M2** in parallel on post-fix canon; **M3** for appendix; **M4–M5** before report sign-off.

### §6.1 Harness mirror loop (M1) — normative behavior

```text
1. Load OptimizationInput + skeleton + genome + candidates + exterior_lane_plan
   (same pipeline entry as post-fix RTTP v0.1 path).
2. Walk genome.commit_order in order.
3. At each step, mirror production ELCP branch:
   - rebuild route domain (committed route / occupied state)
   - resolve_route_probe_start
   - assign_fill_first_exterior_lane (when plan active)
   - probe_route / precomputed path as production
   - _attempt_commit when production would
4. Record ledger fields; do NOT mutate production CommitResult used by solver.
5. Classify probe_failure_class via §5.2 rules.
```

**Mirror parity (required):** see §11 — aggregate counts MUST match production `incremental_commit` on the same inputs.

Implementation lives under `harness/investigation/rttp_elcp_reprobe_forensics.py` (name may adjust in plan; behavior normative here).

---

## §7 — Deliverables

| # | Artifact | Location |
|---|----------|----------|
| 1 | This design spec | `docs/superpowers/specs/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md` |
| 2 | Executable investigation plan | `docs/superpowers/plans/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation.md` |
| 3 | Investigation report (taxonomy table, owner matrix, dominant bucket, #238 appendix) | `docs/superpowers/reports/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-report.md` |
| 4 | Harness mirror + classifier | `harness/investigation/rttp_elcp_reprobe_forensics.py` |
| 5 | Step forensics helper | `harness/investigation/rttp_elcp_reprobe_step_forensics.py` (or merged module if plan prefers) |
| 6 | Investigation tests (no production expected-output change) | `tests/investigation/test_rttp_elcp_reprobe_forensics.py` |

---

## §8 — Deferred retry audit (RF.5)

**Canon:** only primary-phase `CommitConflictReason.REPROBE_FAILED` conflicts are shadow-eligible ([`deferred_retry_shadow.py`](../../../django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py), PR-1/PR-3 specs).

**Report MUST include:**

```text
eligible_reprobe_failed_count
primary_reprobe_failed_count
overlap_table: candidate_id × (ledger class, shadow eligible)
```

**Question to answer (read-only):** among ledger-classified failures, what fraction are shadow-eligible but remain in final `CommitResult.conflicts` because deferred execute is off or bounded?

No change to `deferred_retry_execute` in A phase.

---

## §9 — Recovery comparison (RF.6)

Compare **post-fix primary** mirror outcomes on `rttp-core-recovery-test-map` against latest recovery evidence JSON (e.g. `after-evtc.json`, `after-s2b1.json`) on:

- `committed_extractor_count` / route cells / exterior route presence
- validation pass class vs primary sparse commit

**Output:** informational table only — does not override §2.3 precedence.

---

## §10 — Risks and assumptions

| Risk | Mitigation |
|------|------------|
| Harness mirror **drifts** from production commit loop | §11 parity check on aggregate counters; investigation test on canon slug |
| #238 appendix misread as fix target | §2.3 precedence; appendix labeled non-authoritative |
| `unknown` bucket too large | Explicit gap section in report; refine rules in A only (harness), not production |
| `assumption:` post-fix #239–241 still reproduce high `reprobe_failed` | RF.1 fails loudly in report if not reproduced |
| Dominant bucket ambiguous (two ~equal) | Report MUST document tie-break rationale; nominate **one** B-spec or declare `inconclusive` with split follow-up |

---

## §11 — Acceptance (A track)

- [x] **RF.1** Post-fix replay reproduces primary mass `reprobe_failed` with sparse commits (within selected `commit_order`)
- [x] **RF.2** Ledger produced; ≥ **95%** named **within commit_order attempts**; not claimed over full `normal_candidates`
- [x] **RF.3** M2 aggregates align with M1 on same run
- [x] **RF.4** Run #238 appendix (non-authoritative)
- [x] **RF.5** Deferred retry audit
- [x] **RF.6** Recovery comparison (informational)
- [x] **RF.7** Owner matrix (commit-order subset)
- [x] **RF.8** Attempt universe sanity (Task 9) — `normal_candidate_count`, `commit_order_len`, `placement_goal_count`, caps documented
- [x] **No production behavior change**
- [x] **Harness mirror parity** (same universe as production primary commit)
- [ ] **Track CLOSED** — blocked until universe reconciliation or explicit narrowed B-spec scope
- [ ] **B-spec nomination** — **blocked** until `commit_order_len` reconciled vs pool / placement_goal

```text
B-spec nomination is blocked until commit_order_len / attempted_count
is reconciled against candidate pool size and expected large-map scale.
```

---

## §12 — Next track matrix (decision only — not executed in A)

Report MUST select **one** dominant `probe_failure_class` (or declare inconclusive). At most **one** row below becomes the recommended B-spec; others remain queued.

| Dominant class | Likely B-spec direction |
|----------------|----------------------|
| `start_blocked` | FOT / `resolve_route_probe_start` / stub policy |
| `lane_capacity_shortfall` | ELCP fill-first / capacity assignment (bounded) |
| `budget_exceeded` | Isolated probe budget study (not bundled with policy) |
| `probe_unreachable` | `route_probe` / goal set / domain traversability |
| `no_goal_cells` | EVTC exterior goals / connector alignment |
| `post_probe_commit_fail` | Post-probe reservation / stub / overlap (e.g. FL-06 class) |
| `stale_candidate_reachable` | Selection vs commit contract + narrow reprobe doc/fix |
| `domain_congestion` | Route domain rebuild / reservation density |
| `trunk_ordering_pressure` | ELCP-TM trunk ordering (bounded) |
| `unknown` (over cap) | Instrumentation-only follow-up — no policy B-spec until gap closed |

**Throughput / Gate B:** remains outside this track unless dominant bucket analysis proves commit feasibility is blocked solely by taxonomy gap (unlikely).

---

## §13 — Approval record

```text
Approved 2026-05-27 (RTTP Regression Forensics Lead).

Evidence: Option 3 (Both) — primary SoT #239–241 post-fix replay;
historical appendix Run #238.
Methods: Approach I primary + Approach III secondary; Approach II rejected.
Scope: read-only; no RouteProbeResult / CommitConflictReason production changes.
Harness mirror parity required (§11).
```

---

## References

- [`2026-05-27-rttp-lns-elcp-propagation-design.md`](2026-05-27-rttp-lns-elcp-propagation-design.md) — P0 CLOSED; §8 follow-up queue
- [`2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md`](2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md) — E-track pattern (harness probe + report)
- [`django_apps/asteroid_lab/optimization/commit/incremental_commit.py`](../../../django_apps/asteroid_lab/optimization/commit/incremental_commit.py)
- [`django_apps/asteroid_lab/optimization/routing/route_probe.py`](../../../django_apps/asteroid_lab/optimization/routing/route_probe.py)
- [`django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py`](../../../django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py)
- [`harness/investigation/rttp_t1b_step_forensics.py`](../../../harness/investigation/rttp_t1b_step_forensics.py) — step forensics pattern
- [`harness/investigation/rttp_final_layout_assert_probe.py`](../../../harness/investigation/rttp_final_layout_assert_probe.py) — mirror-without-mutation pattern
