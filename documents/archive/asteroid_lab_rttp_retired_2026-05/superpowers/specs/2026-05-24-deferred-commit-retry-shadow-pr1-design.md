# Deferred Commit Retry Shadow — PR-1 (Observe-Only) Design

**Status:** CLOSED 2026-05-24 — merged `1e021f20` (PR #72)  
**Owner:** asteroid-lab / RTTP Axis B  
**Track:** RTTP core — deferred commit retry slice 1 of 4  
**Supersedes (naming only):** [`2026-05-22-deferred-commit-retry-design.md`](2026-05-22-deferred-commit-retry-design.md) (CANCELLED; pre-RTTP v0.1 pipeline)  
**Related:** [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md) · B-CS1 `test_rttp_commit_survivability.py` · D+ catalog observe-only pattern

---

## §1 Scope

### In scope

PR-1 adds **observe-only** diagnostics for deferred commit retry.

Diagnostics are produced **immediately after primary `incremental_commit`** and **before** any LNS / local repair flow.

The diagnostic answers:

- which candidates would enter a one-round deferred retry queue
- why each candidate is eligible
- what retry budget would apply (recorded, not consumed)
- what route-domain snapshot **context** the observation belongs to (metadata only)
- how the observation links to the **primary** commit result

### Out of scope

| Item | Rationale |
|------|-----------|
| Executing deferred retry | PR-3 |
| Changing `CommitResult`, genome, commit order | PR-1 observe-only |
| LNS behavior changes | Separate repair axis |
| Validation repair / fail-closed changes | B-CS3 invariant |
| `route_domain` mutation or rebuild for retry | PR-3+ |
| Reading replay / NDJSON / `solver_summary` as algorithm input | Decontamination + B-CS4 |
| Macro pipeline (`incremental_commit_macro`) | v0.1 normal path only in PR-1 |
| `primary_*` / `final_*` dual diagnostics | PR-2 or PR-4 extension |

### Source point

```text
source_phase = "primary_incremental_commit"
```

PR-1 observes **LNS-before** primary pass only.

### Architecture choice

**Canonical DTO:** `DeferredRetryShadowSummary` built by pure `build_deferred_retry_shadow_summary(...)`.

**Projection only:** `algorithm_steps` / replay / `solver_summary` carry JSON metrics copied from the DTO — never fed back into optimization.

---

## §2 Invariants

| ID | Invariant |
|----|-----------|
| INV-PR1-01 | Observe-only: diagnostic must not change `CommitResult`, validation outcome, selected genome, committed candidates, route reservations, or `route_domain`. |
| INV-PR1-02 | Primary-only: generated after primary `incremental_commit`, before `run_local_lns`. |
| INV-PR1-03 | No replay input: replay frames, `solver_summary`, NDJSON, debug artifacts, and UI payloads must not be read to build the diagnostic. |
| INV-PR1-04 | No route probe: PR-1 must not call `probe_route` or `incremental_commit` again for shadow purposes. |
| INV-PR1-05 | Eligible reason fixed: only `CommitConflictReason.REPROBE_FAILED` from **primary** conflicts are shadow-eligible in PR-1. |
| INV-PR1-06 | Budget recorded, not consumed: `DeferredRetryShadowBudget` is descriptive defaults for PR-3. |
| INV-PR1-07 | Domain context descriptive: counts / version / transport kind only — no domain patch or rebuild. |
| INV-PR1-08 | Deterministic ordering: shadow candidates sorted by `original_commit_order` index, then `candidate_id`. |
| INV-PR1-09 | LNS separation: LNS must not add, remove, or rewrite primary shadow candidates (shadow frozen before LNS). |
| INV-PR1-10 | Validation read-only preserved: final validation remains read-only; no deferred retry from validation. |

---

## §3 Contracts

### Eligibility (PR-1)

```text
eligible iff:
  conflict in primary_commit_result.conflicts
  AND conflict.reason == REPROBE_FAILED
  AND candidate_id appears in genome.commit_order
```

Non-eligible (recorded only in aggregate `ineligible_conflict_count` by reason enum value, not free strings):

`INLET_ON_SHARED_TRANSPORT`, `OVERLAP`, `ROUTE_CELL_CONFLICT`, `OCCUPIED_CELL_CONFLICT`, `TRANSPORT_KIND_CONFLICT`, `HARD_PROTECTED_CONFLICT`, `CANDIDATE_NOT_FOUND`, `MACRO_CHILD_CONFLICT`.

### `domain_snapshot_index`

Number of primary-pass **successful** commits strictly before this candidate in `genome.commit_order` (0 if first in order).

### Budget defaults (PR-1 skeleton)

| Field | Default | Notes |
|-------|---------|-------|
| `max_retry_rounds` | `1` | Matches planned PR-3 v0 |
| `max_candidates` | `len(shadow_candidates)` capped by config | PR-3 may cap lower |
| `route_probe_max_expansions` | `500` | Align with `probe_route` default; wire from config in PR-2 |

### Step id

`RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW = "rttp.deferred_commit_retry_shadow"`

Always `passed=True` in PR-1 (observe-only; does not gate `validation_passed`).

---

## §4 Verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_survivability.py tests/unit/asteroid_lab/test_rttp_lns.py -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
```

Optional ops (no new pass criteria in PR-1): `python manage.py run_solver --slug copy-import-495e552c` — confirm new step appears in `solver_summary.algorithm_steps`.

---

## §5 Follow-on slices (not PR-1)

| PR | Scope |
|----|--------|
| PR-2 | `DeferredRetryShadowConfig` on `RttpPipelineConfig` + no-op wiring / disable flag |
| PR-3 | Bounded deferred retry execution |
| PR-4 | Real-map regression / ops smoke |
