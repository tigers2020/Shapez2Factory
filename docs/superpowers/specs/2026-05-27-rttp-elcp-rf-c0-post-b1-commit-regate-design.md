# P1-ELCP-RF-C0 — Post-B1 Overlap-Pack Commit-Layer Re-Gate — Design Spec

**Date:** 2026-05-27  
**Status:** **CLOSED** (2026-05-27 — C0 report published)  
**Report:** [`../reports/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md`](../reports/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md)  
**Document type:** Read-only regression forensics (E-track, **Layer 2 re-gate only**)  
**Work classification:** documentation · regression forensics (no production behavior change)  
**Parent (REOPENED):** [`2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md`](2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md)  
**Prerequisite (CLOSED):** [`2026-05-27-rttp-elcp-rf-b1-overlap-packing-design.md`](2026-05-27-rttp-elcp-rf-b1-overlap-packing-design.md) · report [`../reports/2026-05-27-rttp-elcp-rf-b1-overlap-packing-report.md`](../reports/2026-05-27-rttp-elcp-rf-b1-overlap-packing-report.md)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Implementation plan:** [`../plans/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate.md`](../plans/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate.md)

**Korean title (reference):** B1 이후 overlap-pack commit-layer re-gate forensic 조사

---

## §1 — Executive summary

**B1 (CLOSED)** increased Gate A `commit_order_len` from **59 → 67** under opt-in `GREEDY_REGRET_OVERLAP_PACK` without changing commit-time ELCP policy. **Primary `primary_committed_count` after overlap-pack has not been measured.**

**C0 sole question (Layer 2 — commit only):**

```text
On the same code SHA and Gate A config, does GREEDY_REGRET_OVERLAP_PACK
(67 commit_order) increase primary incremental_commit success vs GREEDY_REGRET (59)?
```

**Explicitly NOT C0:**

```text
lane_capacity_shortfall B-spec implementation or nomination
Selection trace / overlap graph bounds (A2, B1 Phase 0)
Changing default GREEDY_REGRET or commit-time ELCP policy
```

**Outcome:** Re-gate `lane_capacity_shortfall` program B-spec as **`BLOCKED` | `NARROWED_TO_COMMIT_ORDER` | `UNBLOCKED`** (decision only).

---

## §2 — Evidence rules (normative)

### §2.1 Primary SoT — fresh dual-run (Policy B)

```text
C0 primary evidence MUST be a dual-run comparison on the same code SHA:

1. selection_mode = GREEDY_REGRET
2. selection_mode = GREEDY_REGRET_OVERLAP_PACK

All other pipeline inputs/config MUST be identical.
The only permitted runtime difference between the two C0 runs is selection_mode.
```

Report MUST record `git_sha` (`git rev-parse HEAD` locally; CI `GITHUB_SHA` when present).

### §2.2 Historical appendix only

```text
C0 MUST NOT reuse frozen RF/A2/B1 numeric baselines as primary evidence.
Frozen values are appendix-only historical anchors.
```

| Historical anchor | Value | Source |
|-------------------|------:|--------|
| `commit_order_len` (greedy) | 59 | P1-ELCP-RF / A2 |
| `primary_committed_count` | 3 | P1-ELCP-RF RF.1 |
| `primary_reprobe_failed_count` | 29 | P1-ELCP-RF RF.1 |
| `commit_order_len` (overlap-pack target) | 67 | B1 `target_floor` |

### §2.3 Precedence

```text
1. Fresh dual-run table (same SHA) WINS for all C0 decisions.
2. Frozen numbers MAY appear in report appendix for narrative only.
3. If fresh GREEDY_REGRET baseline drifts from historical 59/3/29, document drift; do not fail C0 solely for historical mismatch.
```

---

## §3 — Scope · slug · config

| Field | Value |
|-------|-------|
| Slug | `rttp-core-recovery-test-map` (Gate A primary, RF.1 parity) |
| Policies | `ExtractorPlacementPolicy.INTERIOR_AND_RIM`, `FixedOutputTransportPolicy.OUTWARD_FROM_RIM`, `RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED` |
| ELCP | `exterior_lane_plan` active on primary `incremental_commit` |
| Pipeline config | Same `RttpPipelineConfig` fields as P1-ELCP-RF RF.1 test (throughput target, placement percent, platform cell count) except `selection_mode` |

**Cert slug:** out of scope for C0 (B1 selection guards only).

---

## §4 — Measurement contract

### §4.1 Primary capture (Layer 2 SoT)

Primary metrics MUST come from the **first** `incremental_commit` call in `run_rttp_pipeline` (before `run_local_lns` / deferred execute merge). Capture via patch on `django_apps.asteroid_lab.optimization.pipeline.incremental_commit` (same pattern as [`test_rttp_elcp_reprobe_forensics.py`](../../../tests/investigation/test_rttp_elcp_reprobe_forensics.py)).

### §4.2 Dual-run comparison table

| Metric | `GREEDY_REGRET` fresh | `GREEDY_REGRET_OVERLAP_PACK` fresh | Delta | SoT class |
|--------|----------------------:|-----------------------------------:|------:|-----------|
| `commit_order_len` | ? | ? | ? | **primary** |
| `primary_committed_count` | ? | ? | ? | **primary** |
| `primary_conflict_count` | ? | ? | ? | **primary** |
| `primary_reprobe_failed_count` | ? | ? | ? | **primary** |
| `lane_capacity_shortfall_count` | ? | ? | ? | **primary** |
| `route_feasible_shortfall_count` | ? | ? | ? | **primary** |
| `stale_candidate_reachable_count` | ? | ? | ? | **primary** (M1 ledger histogram) |
| `validation_passed` | ? | ? | — | **informational_e2e** |
| `throughput_shortfall_reason` | ? | ? | ? | **informational** |

**Labels (normative):**

```text
validation_passed = informational E2E signal, not primary Layer 2 SoT
throughput_shortfall is reported as relative informational signal only.
It must not override primary commit/bucket histogram verdict.
```

### §4.3 M1 mirror + bucket histogram (both modes)

For each mode:

1. `build_elcp_primary_mirror_ledger` on captured primary inputs.
2. `assert_mirror_parity(production=primary, mirror=mirror)`.
3. Failed-attempt `probe_failure_class` histogram (`ElcpProbeFailureClass`).
4. Bucket coverage ≥ **95%** on failed attempts (excluding `unknown_reprobe_failed`).

Reuse classifier canon from [`2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md`](2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md) §5.

### §4.4 M2 cross-check (secondary)

`extract_elcp_reprobe_forensics(algorithm_steps)` — `lane_capacity_shortfall_count` / `route_feasible_shortfall_count` MUST match primary `CommitResult` per mode.

---

## §5 — Non-goals

| Forbidden in C0 | Owner |
|-----------------|-------|
| Production changes to `incremental_commit`, selection, validation | Future B-spec / B1 follow-up |
| `lane_capacity_shortfall` B-spec **implementation** or **nomination** | Separate track after C0 |
| Using Phase 0 / replay JSON as solver input | Forbidden shortcut |
| Cert slug dual-run | Out of scope |
| Default `GREEDY_REGRET` replacement | B1 rollout §7 |

```text
C0 may unblock or narrow a future lane_capacity_shortfall B-spec,
but MUST NOT implement or nominate that B-spec.
```

---

## §6 — C0 decision heuristic (non-normative thresholds)

Final re-gate verdict MUST synthesize **histogram + primary committed delta + validation regression**. The table below is **heuristic guidance only**, not standalone pass/fail rules.

| Observation | Suggested next track |
|-------------|----------------------|
| `commit_order` ↑, `primary_committed` still ~3 (Δ≤1 vs fresh baseline) | Layer 2 B-spec review (`lane_capacity_shortfall` candidate) |
| Overlap-pack: `lane_capacity_shortfall` dominant bucket (≥40% of failed **or** #1 class) | Re-gate **`UNBLOCKED`** or **`NARROWED_TO_COMMIT_ORDER`** |
| Overlap-pack: `stale_candidate_reachable` dominant | Post-probe / reservation B-spec; lane B-spec stays **BLOCKED** |
| Overlap-pack: `validation_passed` E2E regression (baseline pass → overlap fail) | **C0 BLOCKED** — B1 follow-up / rollback |
| Overlap-pack: `primary_committed` meaningfully ↑ (Δ≥2 **or** >2× fresh baseline) | Keep B1; re-measure next bottleneck |

**`~3` committed:** treat fresh baseline `primary_committed_count` as anchor; “still ~3” means overlap-pack Δ≤1 unless histogram shows clear dominant shift.

---

## §7 — Re-gate output (`lane_capacity_shortfall`)

Report § MUST state exactly one:

| Verdict | Meaning |
|---------|---------|
| **BLOCKED** | Layer 1 / selection still dominates, or wrong bucket for lane B-spec, or C0 blocked by validation regression |
| **NARROWED_TO_COMMIT_ORDER** | Lane issue appears within commit-order universe but scope/placement goal still caps impact |
| **UNBLOCKED** | Layer 2 `lane_capacity_shortfall` may proceed to **separate** B-spec drafting (C0 does not open that spec) |

---

## §8 — Execution architecture

**Approach 1 (mandatory):** dedicated harness + investigation test.

| Component | Path |
|-----------|------|
| Harness | `harness/investigation/rttp_elcp_c0_dual_mode.py` |
| Test | `tests/investigation/test_rttp_elcp_rf_c0_post_b1_commit_regate.py` |
| Report | `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md` |
| Historical constants (appendix only) | `tests/support/rttp_c0_historical_anchors.py` |

**Not modified:** `incremental_commit.py`, `pipeline.py` (except test patch), `greedy_regret.py`, `overlap_pack.py`, `selection_mode.py`.

---

## §9 — Deliverables

| # | Artifact |
|---|----------|
| 1 | This design spec |
| 2 | Plan [`2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate.md`](../plans/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate.md) |
| 3 | Report `2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md` |
| 4 | `harness/investigation/rttp_elcp_c0_dual_mode.py` |
| 5 | `tests/investigation/test_rttp_elcp_rf_c0_post_b1_commit_regate.py` |
| 6 | `tests/support/rttp_c0_historical_anchors.py` (appendix constants; not test SoT) |

---

## §10 — Acceptance (C0 CLOSED)

```text
C0 CLOSED iff:
1. both selection modes run on the same SHA and same Gate A config;
2. primary incremental_commit first-call result is captured for both modes;
3. M1 mirror parity passes for both modes;
4. bucket coverage is ≥95% for both modes;
5. dual-run delta table is published;
6. lane_capacity_shortfall re-gate is stated as BLOCKED, NARROWED_TO_COMMIT_ORDER, or UNBLOCKED;
7. no production behavior change.
```

---

## §11 — Program status interactions

| Program | After C0 |
|---------|----------|
| **P1-ELCP-RF** | Stays **REOPENED** until product closes Layer 2 or opens B-spec |
| **B1** | Unaffected; C0 does not revoke B1 CLOSED |
| **`lane_capacity_shortfall` B-spec** | Updated only by C0 re-gate verdict (no implementation in C0) |

---

## §12 — Risks

| Risk | Mitigation |
|------|------------|
| Master drift changes fresh `GREEDY_REGRET` away from 59 | Record `git_sha`; dual-run internal comparison remains valid |
| E2E validation conflated with primary commit | `informational_e2e` label; primary table excludes validation from SoT |
| Throughput misread as root cause | `informational` only; cannot override histogram verdict |
| LNS masks primary in `PipelineResult.commit_result` | Always use patched first `incremental_commit` return |
