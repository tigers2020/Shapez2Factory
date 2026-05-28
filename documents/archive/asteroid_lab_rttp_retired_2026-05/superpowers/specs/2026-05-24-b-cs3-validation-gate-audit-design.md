# B-CS3 — Validation Gate Boundary Audit (Design)

**Status:** CLOSED 2026-05-24 (Solver Release Architect) — evidence via `test_b_cs3_validation_gate_boundary.py`  
**Owner:** asteroid-lab / RTTP Axis B core closure  
**Track:** Boundary audit + test hardening (**no solver logic changes**)  
**Scope:** RTTP v0.1 normal path + macro validation path + PR-C replay/ORM contamination boundary  
**Prerequisite:** B-CS1 `test_rttp_commit_survivability.py`; B-CS2 CLOSED (`solver_run_id` 55); D+ PR-2/PR-3 CLOSED  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Related:**

- [ADR-003 — Final Validation As Assertion Gate](../../../documents/adr/ADR-003-final-validation-assertion-gate.md)
- [`asteroid_lab_08_validation.md`](../../../documents/Algorithm/asteroid_lab_08_validation.md)
- [`2026-05-24-b-cs2-trunk-ops-smoke-design.md`](2026-05-24-b-cs2-trunk-ops-smoke-design.md) — ops evidence (contrast: B-CS3 = architecture evidence)
- [`2026-05-24-repo-decontamination-authority-design.md`](2026-05-24-repo-decontamination-authority-design.md) — PR-C outline (validation/replay portion only; see B-CS3-9)
- [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md) — B-CS3 row

---

## Problem

Final validation is defined as a **read-only assertion gate**: it must not repair layout, invent routes, mutate topology, or consume replay/debug artifacts as algorithm input ([ADR-003](../../../documents/adr/ADR-003-final-validation-assertion-gate.md), [Phase 8](../../../documents/Algorithm/asteroid_lab_08_validation.md)).

Current enforcement is **uneven**:

| Area | Gap |
|------|-----|
| `final_validation.py` | Only weak guards (`test_rttp_lns.py` source/import string checks); no dedicated immutability or import-boundary suite |
| Catalog validation | Stronger (`test_validation_readonly_guards.py`) — D+ PR-2 scope only |
| Macro path | `validate_macro_layout` + `_run_macro_rttp_pipeline` are **live** though macro track is PAUSE |
| PR-C replay boundary | Outlined in decontamination spec §9; **not consolidated** for validation modules |
| `reachable` in validation | Reads candidate snapshot field; must be classified as **assert-only**, not commit reprobe substitute |
| Pipeline ordering | Normal path runs LNS before validation; must be **test-locked** so validation cannot move before repair |

B-CS2 proved trunk-connected commit on a real slug. B-CS3 closes the **validation gate boundary** with pytest/static evidence, not ops smoke.

---

## Goal

Prove (by static import guards, immutability sentinels, and pipeline-order tests) that all validation entrypoints remain read-only and cannot reach repair, LNS, route probing, route-domain rebuilding, replay ORM/NDJSON, or `solver_summary` as algorithm input.

---

## Non-goals

| Item | Rationale |
|------|-----------|
| Validation behavior / rule changes | Audit hardens boundaries; does not change pass/fail semantics |
| New repair, LNS, or route-domain logic | Forbidden — separate bug track if leak found |
| Macro track reactivation | Boundary audit only |
| Catalog fail-closed relaxation | D+ PR-2 authority unchanged |
| Replay persistence redesign | Output-only contract unchanged |
| Primary `run_solver` ops smoke | Optional secondary; B-CS2 already covers real-slug shell |
| Criteria drift to green tests | Forbidden shortcuts |

---

## Scope (confirmed: **C-full single audit**)

```text
B-CS3 = validation gate boundary audit (one milestone)

Include:
  1. RTTP v0.1 normal path (commit → optional LNS → validate_pipeline_layout)
  2. Macro-only validation branch (validate_macro_layout; no LNS on macro path today)
  3. PR-C replay / NDJSON / SolverRun ORM / route_domain builder contamination boundary
  4. final_validation read-only / no-repair / no-probe guards
  5. Pipeline ordering: repair stages before validation tail

Exclude:
  validation logic improvement, new repair, macro feature work, run_solver quality targets
```

**Staged split (B-CS3a/b) rejected** — leaves PR-C gap open and delays Axis B closure.

---

## North-star invariant

```text
Validation is an assertion gate.
Validation reads final committed state (and catalog slice for mapped checks).
Validation does not repair, route, or mutate topology.
Validation does not consume replay / NDJSON / solver_summary as algorithm input.
Candidate-time reachable is not commit proof; validation must not re-probe.
```

---

## Audited modules and entrypoints

| Module / symbol | Role |
|-----------------|------|
| `optimization/validation/final_validation.py` | `validate_final_layout`, `validate_macro_layout` |
| `optimization/validation/catalog_layout_validation.py` | `validate_pipeline_layout` (AND composition) |
| `adapters/catalog_placement_validation.py` | Mapped fail-closed catalog checks |
| `adapters/catalog_placement_audit.py` | Observe-only audit metrics (pipeline step) |
| `optimization/pipeline.py` | `_run_rttp_pipeline` (LNS → validate); `_run_macro_rttp_pipeline` (commit → validate) |

**Not in scope for mutation:** `incremental_commit`, `local_lns`, `route_probe`, `RouteDomainSnapshotBuilder` — except to assert validation **does not import/call** them.

---

## PASS authority

```text
Primary (B-CS3 closure):
  - New/updated pytest boundary tests (B-CS3-1 … B-CS3-10)
  - AST import/call boundary tests (PASS authority — not plain source-word guards)
  - Read-only immutability sentinel tests (five input classes; deepcopy + call sentinels)
  - Pipeline ordering tests (normal + macro branches)

Secondary (regression, no new ops contract):
  - test_rttp_commit_survivability.py (B-CS1)
  - python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map"
  - Optional: run_solver on copy-import-495e552c only if current_plan requires — not B-CS3 primary gate
```

```text
B-CS2 = ops evidence
B-CS3 = architecture boundary evidence
```

---

## Pass criteria

### B-CS3-1 — `final_validation` import boundary

`final_validation.py` must not import (direct or re-export):

- LNS / repair: `local_lns`, `incremental_commit`, `greedy_regret`, `candidate_generator`
- Route execution: `route_probe`, `run_route_probe`, `build_route_domain_from_skeleton`, `RouteDomainSnapshotBuilder`
- Replay / persistence: `replay_pipeline_service`, `replay_recorder`, `DbRttpReplaySink`, `lab_rttp_snapshot_compose`, replay ORM models
- Debug input: NDJSON readers, `solver_summary` as decision input

**Existing partial guard:** `test_rttp_lns.py::test_lns_only_runs_after_commit_failure` — supersede/extend, do not delete until replacement is stronger ([`docs/ai/test_cleanup_audit.md`](../../ai/test_cleanup_audit.md)).

**Import/call boundary test authority:** Prefer **AST-based** `import` / `ImportFrom` inspection (as in `test_validation_readonly_guards._forbidden_imports`) or **monkeypatch call sentinels** that raise if repair/probe/builders are invoked from validation entrypoints. Plain source-word / `inspect.getsource` substring guards are **supplementary smoke only** — they must **not** be the sole B-CS3 PASS authority.

### B-CS3-2 — Read-only behavior (immutability)

Validation must not mutate any of these **five sentinel input classes**:

1. **Candidates / selected candidates** — `BundleCandidate`, `MacroBundleCandidate`, `candidates_by_id`, `macros_by_id`
2. **Commit result** — `committed_ids`, `reserved_route_cells`, `CommitResult` / macro commit DTO fields passed in
3. **Topology graph** — `OptimizationInput` topology / mineable cell sets (and graph objects if present on `inp`)
4. **Route domain snapshot** — any `route_domain` or domain snapshot object if passed into validation (future-proof; assert no mutation when wired)
5. **Catalog placement validation input** — `BuildingCatalogSlice`, `catalog_placement_ref`, classification rows

**Proof method (required combination):**

- **Before/after equality:** `copy.deepcopy` or serialized snapshot (e.g. `pickle`/`dataclasses.asdict` where stable) on the five classes; call validation; assert unchanged.
- **Call sentinels:** monkeypatch `run_route_probe`, `run_local_lns`, `incremental_commit`, `build_route_domain_from_skeleton`, replay readers to raise a dedicated `AssertionError` subclass if invoked during validation.

### B-CS3-3 — No route invention

Validation must not call route probe or allocate new `RouteReservation` / path cells.

### B-CS3-4 — No topology repair

Validation must not add/remove graph nodes, edges, or edge costs.

### B-CS3-5 — No placement repair

Validation must not add/remove/move buildings, extensions, belts, pipes, or catalog footprint cells.

### B-CS3-6 — `reachable` semantics

- Reading `candidate.reachable` is allowed **only** as a stored snapshot assert on committed candidates.
- Validation must not call `run_route_probe` or `incremental_commit` to refresh reachability.
- Document alignment with B-CS1: candidate-time reachable ≠ commit proof; validation does not close that gap.

### B-CS3-7 — Pipeline ordering (normal path)

In `_run_rttp_pipeline`:

```text
incremental_commit → (run_local_lns if conflicts) → validate_pipeline_layout → audit step
```

Tests must fail if validation is invoked before LNS/commit repair block (e.g. via controlled mock ordering or source-order AST check on pipeline body).

### B-CS3-8 — Macro validation branch

`_run_macro_rttp_pipeline`: `incremental_commit_macro` → `validate_macro_layout` → optional `validate_catalog_placements` AND.

Same import/replay boundaries as B-CS3-1–6 for `validate_macro_layout` and macro validation code path. **Note:** macro path has no LNS today — document as observed behavior, not a pass criterion to add LNS.

### B-CS3-9 — Replay contamination boundary (PR-C partial absorption)

Validation package and adapters listed above must not:

- Import Django replay ORM models or `replay_pipeline_service` frame readers
- Read `SolverRun.config_json` / persisted replay frames inside validation
- Import `lab_rttp_snapshot_compose` or NDJSON stack parsers

**Reuse patterns from:** `test_persistence_does_not_read_replay_frames.py`, `test_replay_pipeline_service_has_no_forbidden_imports` — consolidate under validation-focused test module(s).

**PR-C closure statement (scoped):**

```text
B-CS3 absorbs the PR-C validation/replay contamination boundary portion only.
If PR-C contains broader decontamination work outside validation entrypoints
(e.g. PR-B optimization contamination tokens, PR-D quarantine moves, PR-E dead code),
that broader scope remains separate and is NOT closed by B-CS3.
```

When B-CS3-9 passes, no **additional** PR-C milestone is required **for validation-module replay/ORM import boundaries** only.

### B-CS3-10 — Catalog AND composition

`validate_pipeline_layout` must call `validate_final_layout` first; catalog fail-closed must not bypass layout assert. `observe_only` mode skips catalog **enforcement** but must not skip `validate_final_layout`.

---

## PASS / FAIL summary (closure gate)

**PASS when all hold:**

- Validation modules do not import/call repair, LNS, route probe, route-domain builder, replay ORM, NDJSON, or `solver_summary` input paths (AST or call-sentinel proof).
- Validation does not mutate candidate / commit / topology / route_domain / catalog inputs (five-class sentinel suite).
- `reachable` is snapshot/assert-only; validation does not re-probe.
- Normal path: validation runs after commit and optional LNS.
- Macro path: same assertion-gate import/replay boundaries on `validate_macro_layout`.
- PR-C **validation/replay contamination** portion is covered by B-CS3-9 tests.

**FAIL / BLOCKED when any hold:**

- Validation calls `run_route_probe` or equivalent route invention.
- Validation rebuilds or mutates `route_domain`.
- Validation imports replay ORM, NDJSON readers, or uses `solver_summary` as algorithm input.
- Validation mutates placement, topology, or candidate state.
- Pipeline allows validation before the allowed repair/commit stage.

---

## Allowed changes

| Artifact | Allowed |
|----------|---------|
| `tests/unit/asteroid_lab/test_*validation*boundary*.py` (new or extend) | Yes |
| `tests/unit/architecture/` (if import graph fits existing pattern) | Yes |
| `docs/superpowers/specs/` (this file) | Yes |
| `docs/superpowers/plans/` (audit plan) | Yes |
| `documents/ai/current_plan.md`, roadmap | On CLOSED |
| `django_apps/asteroid_lab/optimization/**` production code | **No** (unless BLOCKED leak requires separate bug PR — out of B-CS3 scope) |

---

## Forbidden (hard)

- Solver logic changes to make tests pass
- Validation repair or relaxing D+ fail-closed rules
- Moving validation before LNS/commit in pipeline
- Using replay / NDJSON / `solver_summary` as algorithm input
- Deleting `test_rttp_lns` / `test_validation_readonly_guards` guards before equivalent or stronger replacements exist
- Treating optional `run_solver` smoke as primary B-CS3 gate

---

## Deliverables

| Artifact | Action |
|----------|--------|
| This spec | B-CS3 pass/fail authority |
| Implementation/audit plan | `docs/superpowers/plans/2026-05-24-b-cs3-validation-gate-audit.md` (via writing-plans) |
| Pytest guard suite | B-CS3-1 … B-CS3-10 |
| `documents/ai/current_plan.md` | B-CS3 **CLOSED** with test command evidence |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | B-CS3 ✅; Axis B progress note |

No application-code PR for B-CS3 unless audit discovers a **confirmed leak** — then stop with `BLOCKED:` and open a **separate** fix track (not criteria drift).

---

## If audit finds a leak

```text
BLOCKED:
- missing context: <module, call path>
- risky change: validation reaches repair/replay input
- recommended next step: separate bug PR; do not weaken B-CS3 criteria
```

B-CS3 milestone closes only when boundaries are **proven** or leak is filed and explicitly deferred with user approval.

---

## Self-review

| Check | Status |
|-------|--------|
| No TBD / placeholder gates | Pass |
| Scope C (normal + macro + PR-C) explicit | Pass |
| Distinguishes B-CS2 ops vs B-CS3 pytest authority | Pass |
| PR-C partial absorption scoped | Pass |
| AST PASS authority (not source-word only) | Pass |
| Five-class immutability sentinels | Pass |
| Macro path LNS absence documented | Pass |
| Forbidden solver logic changes | Pass |
| Single-milestone (not B-CS3a/b) | Pass |
