# RTTP Local LNS — ELCP Context Propagation — Design Spec

**Document type:** Contract fix (wiring / repair-path parity)  
**Status:** Approved (2026-05-27 — minor amendments applied)  
**Work classification:** contract change · regression fix  
**Parent:** [`2026-05-30-rttp-exterior-lane-capacity-planner-design.md`](2026-05-30-rttp-exterior-lane-capacity-planner-design.md) (ELCP) · [`2026-05-30-rttp-exterior-lane-trunk-merge-design.md`](2026-05-30-rttp-exterior-lane-trunk-merge-design.md) (ELCP-TM)  
**Implementation plan:** [`../plans/2026-05-27-rttp-lns-elcp-propagation.md`](../plans/2026-05-27-rttp-lns-elcp-propagation.md)

**Korean title (reference):** RTTP Local LNS ELCP context 전파 수정

---

## §1 — Executive summary

Run #238 (`project_id=23`, `run_key=rttp-b0751b201d8f`) exposed a **repair-path wiring bug**: primary `incremental_commit` runs with `exterior_lane_plan`, but `run_local_lns` retry calls `incremental_commit` **without** ELCP context. LNS then replaces a sparse ELCP-aware result (3 commits) with a higher-count **ELCP-free** result (17 commits), producing `exterior_lane_assignments=[]` while validation still receives a non-null `exterior_lane_plan` → `route_without_lane_assignment` and `rttp_validation_failed`.

This spec closes the gap by:

1. **Propagating ELCP context** from the primary RTTP commit path into every LNS retry `incremental_commit` call.
2. **Adding a replacement guard** so a non-ELCP retry result cannot replace an ELCP-aware primary result when `exterior_lane_plan` is present.
3. **Locking the contract with regression tests** before any primary ELCP reprobe-failure tuning.

**Out of scope for this spec:** primary ELCP reprobe failure rate (56/59 on Run #238), lane assignment policy changes, throughput tuning, timing instrumentation, 13D-SSR, boundary JSONL RTTP stage emit.

---

## §2 — Problem statement (diagnosis summary)

### Observed failure chain (Run #238)

| Stage | ELCP | committed | conflicts | `exterior_lane_assignments` |
|-------|------|-----------|-----------|----------------------------|
| Primary `incremental_commit` | ON | 3 | 56 | (not exported separately; ELCP path used) |
| `run_local_lns` retry | **OFF** | **17** | 8 | **[]** |
| `validate_exterior_lane_contract` | plan present | — | — | emits `route_without_lane_assignment` |

Evidence that final commit bypassed ELCP:

- `lane_capacity_shortfall_count == 0`
- `route_feasible_shortfall_count == 0`
- `exterior_lane_assignments == []`
- `external_lane_assigned_loads == {}`

Root cause location:

```text
pipeline._run_v01_rttp_pipeline
  incremental_commit(..., exterior_lane_plan=plan, ...)   # primary — OK
  run_local_lns(...)                                       # missing ELCP args
    incremental_commit(...)                                # use_elcp=False
```

Classification: **Case A — wiring bug** (not serialization loss, not assignment-policy-only).

---

## §3 — Normative contract

### §3.1 Repair-path parity (required)

> **When `exterior_lane_plan` is present in the primary RTTP commit path, all repair/retry commit paths that may replace the primary `CommitResult` must preserve ELCP context or must be disqualified from replacing an ELCP-aware result.**

### §3.2 Preferred strategy (A)

**A. LNS retry performs ELCP-aware commit** — pass the same ELCP arguments primary commit receives:

- `exterior_lane_plan`
- `route_probe_start_policy`
- `resource_kind`

### §3.3 Fallback guard (B — mandatory in addition to A)

**B. Non-ELCP retry results must not replace ELCP-aware primary results** when ELCP is active for the pipeline run.

**ELCP active** (canonical predicate):

```text
exterior_lane_plan is not None
AND required/planned lane count > 0
```

Implementation MUST use the canonical lane-count field on `ExteriorLaneCapacityPlan` (`required_lane_count` today). Do **not** hard-code `.lanes` length if the DTO exposes a different public accessor; add a shared helper (e.g. `elcp_plan_is_active(plan)`) rather than scattering field access.

A retry `CommitResult` is **ELCP-incomplete** when:

```text
elcp_plan_is_active(exterior_lane_plan)
AND len(committed_ids) > 0
AND len(exterior_lane_assignments) != len(committed_ids)
```

An ELCP-incomplete retry MUST NOT become the pipeline's final `commit_result` via LNS replacement logic, even if `len(retry.committed_ids) > len(primary.committed_ids)`.

### §3.4 Assignment cardinality invariant (validation bridge)

When ELCP is active for the **final** commit path and `committed_ids` is non-empty:

```text
len(exterior_lane_assignments) == len(committed_ids)
```

Each assignment row MUST include `candidate_id` and `exterior_lane_id` (existing ELCP-TM shape).

Validation (`validate_exterior_lane_contract_issues`) MUST NOT emit `route_without_lane_assignment` for a final commit that satisfies §3.4.

### §3.5 Explicit non-goals

| Item | Disposition |
|------|-------------|
| Fix primary ELCP reprobe failure rate on large maps | **P1 follow-up** after this wiring fix |
| Change `assign_fill_first_exterior_lane` policy | Out of scope |
| Throughput / placement goal tuning | Out of scope |
| `deferred_retry_execute` ELCP awareness | **P1 note** — not required for this patch unless trivial; document as follow-up |
| `incremental_commit_macro` ELCP propagation | **P1 note** — macro path currently calls `incremental_commit` without plan; separate ticket |

---

## §4 — Design

### §4.1 `run_local_lns` signature extension

Add optional ELCP parameters mirroring primary commit:

```python
def run_local_lns(
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    genome: PlacementGenome,
    candidates_by_id: dict[str, BundleCandidate],
    commit_result: CommitResult,
    *,
    policy: ExtractorPlacementPolicy = ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    config: LocalLnsConfig | None = None,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None = None,
    route_probe_start_policy: RouteProbeStartPolicy = RouteProbeStartPolicy.OUTPUT_STUB_ONLY,
    resource_kind: str | None = None,
) -> tuple[PlacementGenome, CommitResult]:
```

Forward these into every `incremental_commit(...)` call inside the LNS loop.

When `exterior_lane_plan is None`, behavior MUST remain identical to today (no ELCP, no guard side effects beyond the guard predicate being vacuously false).

**Propagation rule:** When `exterior_lane_plan` is present, `route_probe_start_policy` and `resource_kind` MUST be propagated **exactly** from the primary commit call site. If the primary path uses a derived `resource_kind` (e.g. `_resource_kind_for_transport(inp.transport_kind)`), LNS MUST receive that same derived value — not an independent recompute unless both call sites share one deterministic helper (they do today via pipeline).

### §4.2 Replacement guard helper

Introduce **module-level, unit-testable** helpers in:

```text
django_apps/asteroid_lab/optimization/commit/elcp_commit_guard.py
```

Required exports:

```python
def elcp_plan_is_active(exterior_lane_plan: ExteriorLaneCapacityPlan | None) -> bool:
    """True when plan is non-null and required_lane_count > 0."""

def is_elcp_incomplete_commit_result(
    *,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None,
    commit_result: CommitResult,
) -> bool:
    """Predicate per §3.3; uses elcp_plan_is_active."""

def retry_may_replace_best(
    *,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None,
    best_result: CommitResult,
    retry_result: CommitResult,
) -> bool:
    """Replacement gate for LNS; False when retry is ELCP-incomplete."""
```

`local_lns.py` imports from `elcp_commit_guard.py`. Guard helpers MUST be directly unit-tested (not only via monkeypatched LNS integration tests).

### §4.3 LNS replacement logic (normative)

Current behavior (simplified):

```python
if len(retry_result.committed_ids) > len(best_result.committed_ids):
    best_result = retry_result
```

New behavior when `exterior_lane_plan` is active:

```python
def _retry_may_replace_best(
    *,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None,
    best_result: CommitResult,
    retry_result: CommitResult,
) -> bool:
    if len(retry_result.committed_ids) <= len(best_result.committed_ids):
        return False
    if is_elcp_incomplete_commit_result(
        exterior_lane_plan=exterior_lane_plan,
        commit_result=retry_result,
    ):
        return False
    return True
```

**All LNS return paths, including conflict-free early return, MUST pass through `retry_may_replace_best` or an equivalent ELCP completeness guard when ELCP is active.**

Apply the guard to:

1. Normal replacement (`len(retry.committed_ids) > len(best.committed_ids)`)
2. **Early exit** when `retry_result.conflicts` is empty — do **not** return an ELCP-incomplete retry as the final result even if conflict-free.

**Early-exit tie-break:** If retry is conflict-free but ELCP-incomplete, keep iterating or return `best_result` (primary or prior best ELCP-complete result). Prefer returning the best ELCP-complete result over a conflict-free ELCP-incomplete retry.

### §4.4 Pipeline call site

In `_run_v01_rttp_pipeline` (or equivalent v0.1 RTTP path), change:

```python
genome, commit_result = run_local_lns(
    inp,
    skeleton,
    genome,
    candidates_by_id,
    commit_result,
    policy=policy,
)
```

to:

```python
genome, commit_result = run_local_lns(
    inp,
    skeleton,
    genome,
    candidates_by_id,
    commit_result,
    policy=policy,
    exterior_lane_plan=exterior_lane_plan,
    route_probe_start_policy=route_probe_start_policy,
    resource_kind=_resource_kind_for_transport(inp.transport_kind),
)
```

`exterior_lane_plan` is the same object already built for primary commit via `_exterior_lane_plan_for_pipeline(inp, config)`.

### §4.5 Observability (optional, low cost)

When replacement guard rejects a retry, pipeline MAY increment a diagnostic counter on the commit step metrics (output-only):

```json
"lns_elcp_incomplete_retry_rejected_count": 1
```

Not required for v0 if tests cover behavior; useful for Run #238-style regression visibility.

---

## §5 — Data flow (after fix)

```text
_exterior_lane_plan_for_pipeline(inp, config)
        │
        ├─► incremental_commit(..., exterior_lane_plan=plan, ...)  → primary CommitResult
        │
        └─► run_local_lns(..., exterior_lane_plan=plan, ...)
                 │
                 └─► incremental_commit(..., exterior_lane_plan=plan, ...)  → retry CommitResult
                          │
                          ├─ ELCP-complete + more commits → may replace primary
                          └─ ELCP-incomplete → rejected by guard (B)

validate_pipeline_layout(..., exterior_lane_plan=plan, lane_commit_snapshot=...)
        │
        └─► validate_exterior_lane_contract_issues  → no route_without_lane_assignment when §3.4 holds
```

---

## §6 — Testing (required before merge)

**Work classification:** contract change → tests first (TDD).

### Test 1 — LNS retry receives ELCP context

**File:** `tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py` (new)

**Given:**

- Non-null `exterior_lane_plan` with `required_lane_count >= 1`
- Primary `CommitResult` with conflicts (triggers LNS)
- Monkeypatched `incremental_commit` capturing kwargs

**Expect:**

- Every LNS `incremental_commit` call receives `exterior_lane_plan=plan`
- Same `route_probe_start_policy` and `resource_kind` as passed to `run_local_lns`
- When retry commits at least one candidate under a fixture where ELCP commits succeed, `retry_result.exterior_lane_assignments` is non-empty and matches committed cardinality

Use existing fixtures from `test_incremental_commit_elcp.py` / `greenfield_optimization_input` where possible.

### Test 2 — Replacement guard

**Given:**

- `exterior_lane_plan` present
- Primary result: ELCP-aware (`assignments` cardinality matches `committed_ids`, may be sparse)
- Monkeypatched retry `incremental_commit` returns **more** `committed_ids` but **empty** `exterior_lane_assignments` (simulates pre-fix bug)

**Expect:**

- Final LNS output remains primary (or best ELCP-complete) result
- Retry with higher commit count does **not** replace when ELCP-incomplete

### Test 3 — Validation bridge integration

**File:** extend `tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py` or add pipeline-level unit test with mocked LNS disabled

**Given:**

- `exterior_lane_plan` present
- Final `commit_result.committed_ids` non-empty
- Final `commit_result.exterior_lane_assignments` with one row per committed id (synthetic fixture)

**Expect:**

- `validate_exterior_lane_contract_issues(...)` does **not** include `route_without_lane_assignment`
- `validate_pipeline_layout(...)` structural path consistent with §3.4

### Regression anchor — Run #238 shape (optional integration)

After implementation, manual or integration re-run on `rttp-core-recovery-test-map` SHOULD show:

- `exterior_lane_assignments` non-empty when `committed_ids` non-empty
- No `route_without_lane_assignment` solely due to LNS ELCP bypass

Throughput may still fail (`throughput_target_shortfall`) — that is acceptable for this patch.

---

## §7 — Success criteria

| ID | Criterion |
|----|-----------|
| SC-1 | LNS `incremental_commit` receives full ELCP context when plan is present |
| SC-2 | ELCP-incomplete retry cannot replace ELCP-aware primary when plan is present |
| SC-3 | Final commit satisfies §3.4 assignment cardinality whenever ELCP active and commits exist |
| SC-4 | No `route_without_lane_assignment` from empty assignments after LNS on ELCP-enabled runs |
| SC-5 | Existing non-ELCP runs (`exterior_lane_plan is None`) behave unchanged |

---

## §8 — Follow-up queue (post-merge)

| Re-run outcome | Next queue |
|----------------|------------|
| Assignments populated + validation pass | Throughput / capacity tuning |
| Assignments populated + validation fail (route conflicts) | ELCP validation / route conflict detail |
| ELCP-aware LNS still ~3 commits, high `reprobe_failed` | Primary ELCP reprobe failure analysis (P1) |
| Runtime still ~48s | `solver_summary_stack` timing |
| POST payload still small | 13C transport closed |

**P1 tickets (not this spec):**

- `deferred_retry_execute` ELCP propagation when `observe_only=False`
- `incremental_commit_macro` ELCP propagation
- Primary fill-first probe failure tuning on large blueprints

---

## §9 — File map (implementation preview)

| File | Change |
|------|--------|
| `django_apps/asteroid_lab/optimization/commit/elcp_commit_guard.py` | **NEW** — `elcp_plan_is_active`, `is_elcp_incomplete_commit_result`, `retry_may_replace_best` |
| `django_apps/asteroid_lab/optimization/commit/local_lns.py` | ELCP params, import guard, forward to `incremental_commit` |
| `django_apps/asteroid_lab/optimization/pipeline.py` | Pass ELCP context into `run_local_lns` |
| `tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py` | **NEW** — Tests 1–2 |
| `tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py` | Test 3 extension |

---

## §10 — Risks and assumptions

| Risk | Mitigation |
|------|------------|
| ELCP-aware LNS still low commit count on Run #238 map | Expected; guard prevents false "win" via non-ELCP retry; P1 reprobe queue |
| Guard too strict blocks legitimate LNS improvement | Guard only applies when plan present; incomplete = missing assignment rows |
| `assumption:` Run #238 diagnosis (LNS bypass) remains accurate | Regression Test 2 encodes the failure mode |

---

## §11 — Approval checklist

- [x] User reviewed this spec (2026-05-27 — approved with minor amendments)
- [x] §3.1 contract wording accepted
- [x] Strategy A + guard B accepted
- [x] Test plan accepted
- [x] Minor amendments applied (canonical lane-count predicate, guard helper module, early-exit MUST, exact propagation)
- [x] Implementation plan: [`../plans/2026-05-27-rttp-lns-elcp-propagation.md`](../plans/2026-05-27-rttp-lns-elcp-propagation.md)
