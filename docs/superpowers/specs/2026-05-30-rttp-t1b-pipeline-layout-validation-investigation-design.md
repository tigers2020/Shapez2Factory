# T1b Pipeline Layout Validation Investigation — Design Spec

**Date:** 2026-05-30  
**Status:** CLOSED (E-track read-only investigation; report 2026-05-30, primary **FL-06**)  
**Owner:** RTTP Validation Track / asteroid-lab Layer 4 validation  
**Scope name:** **T1b Pipeline Layout Validation Investigation**  
**Alias (ops tier):** T1b catalog layout  
**Primary hypothesis:** `validate_final_layout` assert failure  
**Parent tier spec:** [`2026-05-30-rttp-ops-authority-tier-design.md`](2026-05-30-rttp-ops-authority-tier-design.md) (T1b = `commit-layout`)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Executable plan:** [`../plans/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation.md`](../plans/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation.md)

This read-only investigation treats “T1b catalog layout” as the ops-tier alias, but scopes the actual failure surface to `validate_pipeline_layout`, with Run 103 evidence indicating catalog audit pass and final layout assertion failure as the primary hypothesis.

**Approval record (2026-05-30):**

```text
Approved for spec drafting.

Use A: T1b Pipeline Layout Validation Investigation.
Keep “T1b catalog layout” only as the ops-tier alias.
Primary hypothesis is validate_final_layout assertion failure, because Run 103 catalog audit passed while pipeline/commit validation failed.
This E phase is read-only: no production fix, no validation relaxation, no throughput policy change, no slug replacement.
```

---

## §1 — Problem

Diagnostic canon **`copy-import-495e552c`** satisfies **T0** (selection-path) and **T1a** (commit-executed: 32 commits, `conflict_count=0`) but fails **T1b** (`rttp.commit.passed=false`, `metrics.validation_passed=false`).

The ops tier alias **T1b catalog layout** historically suggested catalog footprint mismatch. **Run 103** evidence contradicts that as the primary failure mode:

- `rttp.catalog_placement_validation.passed=true`
- `matched_count=32`, `mismatch_candidate_count=0`, `catalog_error_issue_codes=[]`

**Goal:**

```text
Identify which validate_final_layout assert (FL-xx) fails on the diagnostic canon,
confirm catalog audit pass (E.2),
classify T1b vs T2 causality (E.4),
and produce an owner matrix for the next product/policy track — without changing runtime behavior in E phase.
```

---

## §2 — Evidence (frozen)

| Run | Config class | T1a | T1b (`rttp.commit`) | Catalog audit | T2 signal |
|-----|--------------|-----|---------------------|---------------|-----------|
| **55** (B-CS2 historical) | default greedy, low commit count | 1 commit | **PASS** | (historical T3 pass class) | — |
| **76** (PR-2d ops) | 10% target, pre–complete-map recon | 13 commits | **PASS** | — | PASS @ 1536 target |
| **102** | evolution primary | 32 commits | **FAIL** | (not primary for E) | `throughput_target_shortfall` |
| **103** | greedy default (CC-3A parity) | 32 commits, conflict 0 | **FAIL** `validation_passed=false` | **PASS** 32/32, 0 mismatch | `throughput_target_shortfall`, `throughput_shortfall_reason: selection_goal_cap` |

**Pipeline composition (normative):**

```python
# catalog_layout_validation.py
layout_ok = validate_final_layout(...)
if catalog_mode == "observe_only":
    return layout_ok, None
catalog_result = validate_catalog_placements(...)
return layout_ok and catalog_result.passed, catalog_result
```

When `catalog_mode != "observe_only"`, catalog audit **runs**, but the returned `validation_passed` is **`layout_ok AND catalog_result.passed`**. Run 103 proves `layout_ok` was **false** while catalog passed.

**Stress hypothesis (secondary):** Run 55 (1 commit) vs Run 103 (32 commits) suggests commit accumulation / congestion may trigger layout asserts absent at low commit counts.

---

## §3 — Non-goals (E phase)

| Forbidden in E | Follow-up track |
|----------------|-----------------|
| Production validation rule change / assert weakening | Separate fix spec after owner matrix |
| Catalog data / footprint edits | A/B slug or catalog data track |
| Commit logic / LNS / route reservation fixes | Commit/routing spec |
| Throughput policy (`min %`, recon ceiling, goal cap) | **D** |
| Slug replacement or map mutation | **A/B** |
| Replay / solver_summary / NDJSON as algorithm **input** | Forbidden shortcut (standing) |
| Repair logic inside validation modules | Forbidden shortcut (standing) |

---

## §4 — Investigation scope (subsections)

```text
E.1 final_layout assert taxonomy (primary)
E.2 catalog audit confirmation (secondary — Run 103 closure)
E.3 pipeline composition boundary (layout_ok vs catalog_result vs step passed)
E.4 T1b vs T2 causality (informational only)
```

---

## §5 — Failure taxonomy (`validate_final_layout`)

Source: [`django_apps/asteroid_lab/optimization/validation/final_validation.py`](../../../django_apps/asteroid_lab/optimization/validation/final_validation.py).

| Assert ID | Condition (matches code order) | Likely owner |
|-----------|--------------------------------|--------------|
| **FL-01** | `not committed_ids` | ruled out for Run 103 (32 ids) |
| **FL-02** | `candidate_id` missing from `candidates_by_id` | commit / genome integrity |
| **FL-03** | committed equipment `occupied_cells` overlap across commits | candidate selection / commit disjointness |
| **FL-04** | FOT cell ∈ `inp.mineable_cells` (INV-VALIDATION-FOT-01) | FOT placement policy |
| **FL-05** | current FOT overlaps prior occupied **OR** current occupied overlaps prior FOT | cross-commit FOT tracking (see FOT PR-1/PR-2) |
| **FL-06** | `reserved_route_cells` is non-empty **AND** `output_stub ∉ reserved_route_cells` | route reservation / stub alignment |
| **FL-07** | `reserved_route_cells ∩ occupied_seen` non-empty (route vs equipment collision) | route reservation / commit routing domain |
| **FL-08** | `not candidate.occupied_cells.issubset(inp.mineable_cells)` | mineable / FOT policy drift |
| **FL-09** | `not candidate.reachable` | candidate-phase reachable flag vs commit-time reality |

**Priority for Run 103 hypothesis:** FL-06, FL-07, FL-08, FL-09 > FL-03 > FL-04/FL-05 > catalog (ruled out).

**FL-03 vs FL-07 separation (owner matrix):**

| Assert | Collision surface | Owner |
|--------|-------------------|-------|
| FL-03 | equipment `occupied_cells` vs equipment `occupied_cells` | selection / commit disjointness |
| FL-07 | `reserved_route_cells` vs committed `occupied_cells` | route reservation / routing domain |

---

## §6 — Catalog audit confirmation (E.2)

**Run 103 closure criteria:**

- `rttp.catalog_placement_validation.passed == true`
- `metrics.mismatch_candidate_count == 0`
- `metrics.catalog_error_issue_codes == []`
- Mode: `mapped_fail_closed` (not `observe_only`)

**E.2 pass:** catalog path is **not** the primary T1b failure for this slug unless replay harness disagrees with persisted step metrics.

---

## §7 — Pipeline composition (E.3)

**Invariants to verify:**

```text
rttp.commit.metrics.validation_passed == validate_pipeline_layout(...)[0]
rttp.commit.passed == validation_passed (same boolean wired in pipeline.py)
```

**Anomaly class (high severity):** all `validate_final_layout` asserts pass on replay, but `rttp.commit.passed=false` → investigate step wiring / stale metrics, not layout rules.

---

## §8 — T1b vs T2 causality (E.4)

- CLI / entry `validation_passed` derives from **`pipeline_result.validation_passed`** (layout pipeline gate), not throughput alone.
- Run 103 also emits **`throughput_target_shortfall`** and **`selection_goal_cap`** — parallel signals on **T2**.
- **Investigation output (required enum):**

```text
T2_independent | T2_derived_from_layout | inconclusive
```

Do **not** open Track **D** (throughput policy) until E deliverables are CLOSED unless user explicitly reprioritizes.

---

## §9 — Investigation methods

| Method | Role | E phase use |
|--------|------|-------------|
| **1 — Validation replay harness (primary)** | Re-run canon slug; capture `validate_pipeline_layout` inputs; return first failing **FL-xx** | Assert ID confirmation |
| **2 — Step forensics (secondary)** | Parse `algorithm_steps` from `run_solver --json` / DB readback | Hypothesis + E.2/E.3 |
| **3 — Goal-count bisect (ops-only, optional)** | `--max-placement-goal-count` sweep | Stress threshold; does not identify assert line |

**Recommended:** Methods **1 + 2** in parallel.

---

## §10 — Deliverables

| # | Artifact | Location |
|---|----------|----------|
| 1 | This design spec | `docs/superpowers/specs/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md` |
| 2 | Executable investigation plan | `docs/superpowers/plans/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation.md` |
| 3 | Investigation report (evidence table + FL-xx + owner matrix + T2 class) | `docs/superpowers/reports/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report.md` |
| 4 | Read-only assert probe (investigation tooling; no change to `validate_final_layout`) | `harness/investigation/rttp_final_layout_assert_probe.py` |

---

## §11 — Acceptance (E track CLOSED)

- [ ] Primary failing **FL-xx** identified for Run 103 canon replay **or** documented inconclusive with explicit gap
- [ ] E.2 catalog audit pass confirmed on replay
- [ ] E.3 pipeline composition verified (no wiring anomaly, or anomaly documented)
- [ ] E.4 T2 causality classified (`T2_independent` | `T2_derived_from_layout` | `inconclusive`)
- [ ] Owner matrix row selected for next track (fix / policy / slug / data / no-op / instrumentation-only)
- [ ] No production validation behavior change in E phase
- [ ] `current_plan.md` E row → **CLOSED** with report link

---

## §12 — Next PR matrix (decision only — not executed in E)

| Investigation outcome | Next track |
|-----------------------|------------|
| FL-04 / FL-08 FOT or mineable subset | FOT / validation policy spec |
| FL-09 reachable | Algorithm doc vs commit reprobe gap spec |
| FL-06 / FL-07 route reservation | Commit / routing domain spec |
| FL-03 occupied overlap | Commit / LNS disjointness spec |
| FL-05 cross-commit FOT | FOT cross-commit tracking spec |
| All asserts pass on replay but step false | E.3 pipeline wiring bug spec (high severity) |
| Slug inherently non-T3 under current rules | **A/B** pass-capable slug |
| T2 only after T1b resolved | **D** throughput policy |

---

## References


- [`2026-05-30-rttp-ops-authority-tier-design.md`](2026-05-30-rttp-ops-authority-tier-design.md) — T1b tier definition
- [`django_apps/asteroid_lab/optimization/validation/final_validation.py`](../../../django_apps/asteroid_lab/optimization/validation/final_validation.py)
- [`django_apps/asteroid_lab/optimization/validation/catalog_layout_validation.py`](../../../django_apps/asteroid_lab/optimization/validation/catalog_layout_validation.py)
- [`documents/Algorithm/asteroid_lab_10_development_sequence.md`](../../../documents/Algorithm/asteroid_lab_10_development_sequence.md) Sequence 7 — validation
- Run 103 readback (2026-05-30 ops session) — catalog pass / commit fail
