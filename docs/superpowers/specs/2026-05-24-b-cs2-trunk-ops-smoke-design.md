# B-CS2 — Trunk-Connected Commit Ops Smoke (Design)

**Status:** Approved 2026-05-24 after review (Solver Release Architect)  
**Owner:** asteroid-lab / RTTP Axis B core closure  
**Track:** Operational proof — **no solver logic changes**  
**Prerequisite:** B-CS1 `test_rttp_commit_survivability.py` on `master`; D+ PR-3 merged (`dfbda7b8`); Ops E5 CLOSED  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md) — next focus after Axis A close

**Related:**

- [`2026-05-22-rttp-hybrid-c-layout-design.md`](2026-05-22-rttp-hybrid-c-layout-design.md) — commit re-probe invariant
- [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md) — B-CS2 milestone row
- [`2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md`](2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md) — E5 scope (generator); B-CS2 out of scope there

---

## Problem

B-CS1 proves in pytest that **candidate-time `reachable` is not commit proof** and that **incremental commit re-probes** on the latest route domain (narrow-corridor fixture).

Axis B still lacks **operational evidence** on the canonical real Lab slug that:

1. The full RTTP v0.1 pipeline runs end-to-end on `master`.
2. At least one placement is **committed** after selection (commit-time path exercised).
3. **Route-domain / trunk context** is present in persisted observability (skeleton + transport partition signals), even when the map has **no** pre-existing transport cells.

Without a written pass/fail contract, ad-hoc `run_solver` runs risk post-hoc interpretation and conflation with Ops E5 (catalog-native generator).

## Goal

Close milestone **B-CS2** by running one documented ops smoke on slug `copy-import-495e552c` and recording evidence in `current_plan.md` / roadmap. Success means: **commit-time reprobe invariant is observably satisfied on a real slug via output-only artifacts**, not that we add new pipeline metrics in this milestone.

## Non-goals

| Item | Rationale |
|------|-----------|
| New pipeline metrics (`reprobe_count`, `domain_version` on v0.1 commit step, etc.) | B-CS2 is observe-only; metric gaps are recorded, not fixed here |
| Solver / commit / LNS / validation logic changes | Forbidden — would invalidate ops proof |
| Macro-only path | RTTP macro track PAUSE; smoke uses default v0.1 pipeline |
| Replacing or extending E5 assertions | E5 = catalog generator; B-CS2 = commit / route-domain / trunk observability |
| Second real slug | YAGNI; canonical slug matches Ops A–E |
| pytest for B-CS2 | B-CS1 already covers reprobe contract; B-CS2 is ops closure |

---

## North-star invariant (what B-CS2 closes)

```text
Everything is provisional until connected to exterior trunk.
Candidate-time reachable is NOT commit success proof.
Commit uses the latest route_domain snapshot (incremental_commit).
```

**Operational proxy (v0.1 observability):** On a healthy slug, `run_solver` exits 0, `solver_summary` shows a non-empty `commit_order`, the `rttp.commit` step lists non-empty `committed_ids`, and `validation_passed` / `run_success` are true. That implies the commit loop (including per-candidate reprobe inside `incremental_commit`) ran to a validating layout — we do **not** require a dedicated `reprobe_count` metric in v0.1.

---

## Smoke procedure

**Command (canonical):**

```powershell
python manage.py run_solver --slug copy-import-495e552c
```

**Config constraints:**

- Do **not** pass `macro_only_mode: true`.
- Default `ASTEROID_LAB_RTTP_ENABLED=True`.
- Replay persistence may be on or off; evidence is read from `SolverRun.config_json["solver_summary"]`, not from replay frames as solver input.

**Evidence source:** Latest `SolverRun` for the project after exit 0 — `config_json.solver_summary` (and top-level run fields: `ok`, `solver_run_id`, `run_key` from CLI/result if printed).

---

## Pass criteria (B-CS2-1 … B-CS2-12)

### Run shell

| ID | Assertion |
|----|-----------|
| B-CS2-1 | CLI exit code `0` |
| B-CS2-2 | `solver_summary.algorithm` == `rttp_v0.1` |
| B-CS2-3 | `solver_summary.validation_passed` == `true` |
| B-CS2-4 | `solver_summary.run_success` == `true` |
| B-CS2-5 | `solver_summary.issue_codes` == `[]` (healthy slug; same convention as E5) |

### Commit / reprobe proxy

| ID | Assertion |
|----|-----------|
| B-CS2-6 | `solver_summary.confirmed_count` > 0 (alias: committed count at summary level) |
| B-CS2-7 | `len(solver_summary.commit_order)` > 0 |
| B-CS2-8 | Step `rttp.commit` exists in `algorithm_steps` |
| B-CS2-9 | `rttp.commit.metrics.committed_ids` non-empty list |
| B-CS2-10 | `rttp.commit.passed` == `true` |
| B-CS2-11 | `rttp.commit.metrics.validation_passed` == `true` |
| B-CS2-12 | `rttp.commit.metrics.commit_order` non-empty and **consistent** with top-level `solver_summary.commit_order` |

### Route-domain / trunk observability

| ID | Assertion |
|----|-----------|
| B-CS2-13 | Step `rttp.route_domain` exists |
| B-CS2-14 | `rttp.route_domain.metrics.skeleton_id` present (non-empty string) |
| B-CS2-15 | `mismatched_existing_transport_count` key present on `rttp.route_domain.metrics` (value may be `0` on this slug) |
| B-CS2-16 | Step `rttp.genome_selection` exists; `metrics.commit_order` non-empty |

### Pipeline ordering (regression guard)

| ID | Assertion |
|----|-----------|
| B-CS2-17 | `algorithm_steps` contains, in order relative to RTTP core: `reconstruction` → `rttp.catalog_slice` (if present) → `rttp.route_domain` → `rttp.candidate_pool` → `rttp.genome_selection` → `rttp.commit` → `rttp.catalog_placement_validation` (tail audit step allowed) |

### Explicitly **not** B-CS2 pass/fail

| Item | Note |
|------|------|
| E5 `unmapped_candidate_count == 0` | Record for context only; **not** a B-CS2 gate (E5 already closed) |
| E5 `normal_count` on candidate pool | Informational; commit may succeed with subset committed |
| `reprobe_count`, `rollback_count`, `reached_goal_kind`, `goal_priority` | **Not emitted** on v0.1 commit step today — absence is expected; record in evidence table |
| `domain_version` on v0.1 commit metrics | Macro path only; absent on v0.1 is OK |
| Non-zero `conflict_count` alone | **Not** a failure if B-CS2-3..12 pass (LNS may have run) |

---

## Known slug context (`copy-import-495e552c`)

Per [`current_plan.md`](../../../documents/ai/current_plan.md) Ops smoke B/C notes:

- Pre-reconstruction map may have **`transport_component_count` 0**; topology strips top-level transport before adapter.
- **Trunk signal on this slug** is primarily **skeleton ring / route-domain** (`skeleton_id`, route-domain step), not `existing_trunk_cells` from reconstruction transport.
- `mismatched_existing_transport_count == 0` is typical for a shape-belt run with no wrong-kind cells — still required as **key presence**, not `> 0`.

---

## Forbidden (hard)

- Validation repair or relaxing fail-closed catalog rules to pass smoke
- Any change to `incremental_commit`, `pipeline`, `candidate_generator`, or `final_validation` **for smoke green**
- Using replay frames, NDJSON, or `solver_summary` as **algorithm input**
- Unmapped synthetic fail-closed waiver
- RTTP macro track work (`macro_only_mode` smoke as substitute)
- Treating E5 catalog metrics as B-CS2 success criteria

---

## Deliverables

| Artifact | Action |
|----------|--------|
| This spec | Authority for B-CS2 pass/fail |
| Implementation plan | [`2026-05-24-b-cs2-trunk-ops-smoke.md`](../plans/2026-05-24-b-cs2-trunk-ops-smoke.md) |
| `documents/ai/current_plan.md` | Add **CLOSED** B-CS2 entry with `solver_run_id`, `run_key`, evidence bullets |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | Mark B-CS2 ✅; bump Axis B progress note |

No application code PR unless smoke **fails** B-CS2-1..17 — then stop with `BLOCKED:` and open a **separate** bug track (not smoke criteria drift).

---

## Self-review

| Check | Status |
|-------|--------|
| No TBD / placeholder gates | Pass |
| Keys match `rttp_solver_summary.py` + `pipeline.py` metrics_json | Pass |
| Distinguishes E5 vs B-CS2 | Pass |
| Allows zero existing transport on canonical slug | Pass |
| No requirement for non-existent reprobe_count metric | Pass |
| Single-slug, docs-only closure scope | Pass |
