# RTTP Ops Authority Tier — Design Spec (CC-3B)

**Date:** 2026-05-30  
**Status:** Approved for implementation planning (governance only; no product fix in this track)  
**Owner:** RTTP Ops Authority / asteroid-lab runtime  
**Track:** CC-3B — canon slug viability via **ops authority tiering** (not throughput-only)  
**Parent:** [`2026-05-30-rttp-ga-evolution-pr-ga-2-governance-close-design.md`](2026-05-30-rttp-ga-evolution-pr-ga-2-governance-close-design.md) §3.3 (CC-3B deferred)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Approval record (2026-05-30):**

1. **C track scope:** tier taxonomy + merge policy only — no code, slug mutation, or throughput policy implementation.  
2. **T1 split:** `T1a commit-executed` / `T1b commit-layout` — do not replace `commit.passed` with a weakened T1.  
3. **T3 dependency:** `T3 ⇒ T0 + T1b + T2` (T1a alone is insufficient for T3 or milestone full-pass).

---

## §1 — Problem

After PR-GA-2 CLOSED ([#97](https://github.com/tigers2020/Shapez2Factory/pull/97) `e43e197b`), **`copy-import-495e552c` “ops failed”** is still interpreted as a generic regression blocker:

- Historical milestones (B-CS2, E3–E5) assumed **T3 full-ops-pass** (`validation_passed=true`, `issue_codes=[]`).
- Capacity C-GATE ([#94](https://github.com/tigers2020/Shapez2Factory/pull/94) `ec1b6a26`) raised complete-map `reconstruction_max` (e.g. run 76: 15360 → runs 102/103: 75360).
- Current runs show **greedy ≡ evolution** failure modes → not selection-layer regression (CC-3A already PASS).
- `rttp.commit.passed=false` on recent runs reflects **post-commit catalog/layout validation**, not “zero commits” — conflating **commit execution** with **layout pass** hides the slug’s useful diagnostic role.

**Goal:**

```text
Stabilize ops smoke authority by tiering T0–T3 (+ T1a/T1b),
reclassify copy-import-495e552c as diagnostic canon,
and stop using T3 failure alone as evidence against unrelated PRs.
```

---

## §2 — Evidence

| Source | Fact |
|--------|------|
| Run 76 (historical, pre–complete-map class) | `reconstruction_max` 15360; 10% target; `validation_passed` true; B-CS2 T3 class |
| Runs 102/103 (2026-05-30, `master`) | Same `issue_codes` for evolution and greedy: `rttp_validation_failed`, `throughput_target_shortfall` |
| Throughput (runs 102/103) | `reconstruction_max` 75360; `actual_committed_output_per_min` 3840; MIN `throughput_target_percent` 10 → target 7536 > actual → **T2 FAIL** at any allowed 10–80% |
| Commit step (run 103) | `rttp.commit` exists; `confirmed_count` 32; `conflict_count` 0; **`passed=false`** → **T1b FAIL** (pipeline `validate_pipeline_layout` on committed set; commit step `passed=validation_passed`) |
| PR-GA-2 governance | CC-3A selection-path PASS; CC-3B deferred to this spec |

**Pipeline fact (normative for T1b):**

```text
_record_pipeline_step(..., step_id=rttp.commit, passed=validation_passed)
where validation_passed comes from validate_pipeline_layout(...) after incremental_commit.
```

---

## §3 — Non-goals (this track)

| Item | Follow-up |
|------|-----------|
| Throughput policy code change (min %, recon_max ceiling, target formula) | Track **D** |
| Slug / map / DB mutation | Tracks **A** or **B** |
| Catalog layout validation rule change | Track **E** (read-only validation; no repair) |
| `SolverRuntimeEntryResult` exit code / `validation_passed` semantics | Out of scope unless future spec |
| Selection / GA / macro / replay contract changes | Closed tracks |
| Deleting B-CS2/E5 history | Deprecation pointer + tier mapping only |

---

## §4 — Ops authority tier taxonomy

### Tier table

| Tier | ID | Name | Proves | Primary readback |
|------|-----|------|--------|------------------|
| **T0** | `selection-path` | Selection authority | Config and step metrics record intended `selection.mode` | [`2026-05-30-rttp-ga-evolution-pr-ga-2-governance-close-design.md`](2026-05-30-rttp-ga-evolution-pr-ga-2-governance-close-design.md) CC-3A |
| **T1a** | `commit-executed` | Commit executed | Incremental commit ran; committed IDs produced | `rttp.commit` step exists; `metrics.committed_ids` non-empty; `metrics.conflict_count` present; `solver_summary.confirmed_count` > 0 |
| **T1b** | `commit-layout` | Commit layout valid | Post-commit catalog/layout validation passed | `rttp.commit.passed == true`; `metrics.validation_passed == true` |
| **T2** | `throughput-budget` | Throughput budget | PR-2c target budget satisfied | `throughput_budget_satisfied == true`; no `throughput_target_shortfall` in `issue_codes` |
| **T3** | `full-ops-pass` | Full healthy ops (legacy) | End-to-end “green slug” class (B-CS2 / E-series) | CLI exit `0`; `validation_passed==true`; `issue_codes==[]`; implies T0+T1b+T2 |

### T1 split (normative)

```text
T1 is split into:
- T1a commit-executed: proves incremental_commit ran and produced committed_ids.
- T1b commit-layout: proves post-commit catalog/layout validation passed.

T3 requires T1b, not merely T1a.
Selection-only PRs may cite T1a as diagnostic evidence on a diagnostic canon slug.
Milestone ops closure requires tiers per merge policy (§8); T3 needs T1b + T2 + T0.
```

**Do not** define a weakened T1 that only checks `committed_ids` and drops layout validation — that would conflate “commit loop ran” with B-CS2 healthy layout evidence.

### Dependency graph

```text
T3  ⇒  T0 + T1b + T2
T1b ⇒  T1a          (layout validation requires a commit step with committed_ids)
T2  ⇏  T1b, T0      (throughput failure does not imply layout or selection failure)
T0  ⇏  T1a, T1b, T2, T3
```

---

## §5 — Current canon slug classification

**Slug:** `copy-import-495e552c`  
**As of:** 2026-05-30 · `master` @ `831e6374` (post PR-GA-2 governance)  
**Evidence runs:** 102 (evolution), 103 (greedy default)

| Tier | Status | Notes |
|------|--------|-------|
| T0 | **PASS** | `selection.mode=evolution` + metrics on 102; greedy parity on 103 |
| T1a | **PASS** | `rttp.commit` exists; `confirmed_count=32`; `conflict_count=0` |
| T1b | **FAIL** | `rttp.commit.passed=false`; catalog layout validation on committed set |
| T2 | **FAIL** | `throughput_budget_satisfied=false`; `throughput_target_shortfall` |
| T3 | **FAIL** | CLI exit 1; `validation_passed=false`; combined issue_codes |

**Reclassified role:**

```text
copy-import-495e552c = diagnostic canon
  Authoritative for: T0 selection-path; T1a commit-executed stress (high confirmed_count)
  NOT authoritative for: T3 full-ops-pass (until pass-capable slug track A or B closes)
```

---

## §6 — Pass-capable slug contract (T3)

A **pass-capable** slug (existing or newly designated) must satisfy on **documented default config** (B-CS2 class unless a follow-up spec narrows flags):

| ID | Criterion |
|----|-----------|
| T3-1 | `python manage.py run_solver --slug <slug> --no-replay` → exit code `0` |
| T3-2 | `solver_summary.validation_passed == true` |
| T3-3 | `solver_summary.issue_codes == []` |
| T3-4 | `rttp.commit.passed == true` (T1b) |
| T3-5 | `throughput_budget_satisfied == true` under default `throughput_target_percent` (T2) |
| T3-6 | T0 selection-path checks pass when evolution mode is in scope for the PR |
| T3-7 | Evidence: `solver_run_id` + readback recorded in `current_plan` / roadmap |

**Standing use:** T3 is required for **milestone ops closure** (B-CS2 successor, E-series smokes), not for every RTTP feature PR.

**Current gap:** `copy-import-495e552c` is **not** pass-capable under T3 (§5).

---

## §7 — Diagnostic slug contract

`copy-import-495e552c` remains valid for:

- **T0** selection-path smokes (including PR-GA-2 CC-3A class)
- **T1a** high-commit-count / commit-executed diagnostics
- Greedy vs mode parity (same `issue_codes` class)
- Teaching which tier failed (T1b vs T2 vs T3) without blocking unrelated PRs

**Forbidden interpretations:**

```text
"T3 failed on copy-import-495e552c" alone does NOT block:
  - selection-only PRs when T0 passes on that slug
  - docs/architecture PRs with no ops claim
  - PRs that document pre-existing T1b/T2 failure on diagnostic canon
```

---

## §8 — Merge blocker policy

| PR class | Required tiers | Slug |
|----------|----------------|------|
| Selection / GA / `selection.mode` | **T0** | Diagnostic canon OK (`copy-import-495e552c`) |
| Commit / catalog / FOT / layout validation | **T0** + targeted **T1b** evidence on PR branch, **or** documented pre-existing T1b FAIL on diagnostic canon plus separate narrow validation gate | Diagnostic canon: pre-existing T1b FAIL is not merge evidence by itself |
| Throughput / PR-2c–2d budget | **T2** (+ **T0** if selection touched) | Diagnostic OK for T2-only failures |
| Milestone ops / B-CS2 successor / “healthy slug” | **T3** | **Pass-capable slug required** (not `copy-import-495e552c` until A/B closes) |
| Pytest-only / standing gates / decontamination | Existing CI scripts | No extra tier |

**Regression rule:** T0 PASS → T0 FAIL on diagnostic canon for a runtime RTTP PR → **merge blocker**.

**Pre-existing failure rule:** If T1b or T2 FAIL on diagnostic canon before the PR branch, PR body must name the tier and run id; failure alone is not evidence against the PR if tier-appropriate gates pass.

---

## §9 — Follow-up tracks (decision matrix)

| Track | Opens when | Delivers | Unblocks |
|-------|------------|----------|----------|
| **C (this spec)** | Now | Tier taxonomy + merge policy + diagnostic reclassification | Stable ops language |
| **E** Commit/layout investigation | T1b FAIL root-cause needed | Read-only report: catalog placement issues on 32-commit layout | T3 if T1b was sole T3 blocker |
| **D** Throughput policy | T2 root-cause isolated | min %, recon_max basis, target ceiling (no validation repair) | T3 if T2 was sole T3 blocker |
| **A** Pass-capable recovery | T3 needed on same slug | Restore T1b+T2 on `copy-import-495e552c` or document impossibility | Milestone ops on legacy slug |
| **B** New pass-capable slug | A too costly | New slug + T3 evidence; keep old slug diagnostic | Milestone ops |

**Recommended order:**

```text
1. C CLOSED (governance doc + current_plan ACTIVE row)
2. E or D — read-only ops report (which tier blocks T3 today)
3. A or B — pass-capable slug authority
```

---

## §10 — Acceptance criteria (C track)

**Design spec (this document) is complete when:**

- Tier taxonomy T0, T1a, T1b, T2, T3 documented with readback fields (§4)
- Dependency `T3 ⇒ T0 + T1b + T2` stated (§4)
- `copy-import-495e552c` classified diagnostic: T0/T1a PASS; T1b/T2/T3 FAIL (§5)
- T3 pass-capable contract defined (§6)
- Diagnostic vs pass-capable roles separated (§5, §7)
- Merge blocker table published (§8)
- Follow-up A/B/D/E matrix without implementing fixes (§9)

**Governance closure (writing-plans / Task 9 class):**

- `current_plan.md` ACTIVE row → CLOSED with date after plan execution
- One-line supersession in [`2026-05-30-rttp-ga-evolution-pr-ga-2-governance-close-design.md`](2026-05-30-rttp-ga-evolution-pr-ga-2-governance-close-design.md) §3.3

**Out of scope for C:** pytest gates, scripts, runtime code — optional follow-up “C-PR” only if standing enforcement is desired.

---

## §11 — Historical milestone mapping

| Legacy doc | Former implicit tier | Current mapping |
|------------|----------------------|-----------------|
| B-CS2 trunk ops smoke | T3 | Requires pass-capable slug; B-CS2-10/11 = **T1b** |
| E3–E5 catalog smokes | T3 | Same |
| PR-GA-2 CC-3A | T0 | Unchanged on diagnostic canon |
| PR-GA-2 CC-3B | T2 (+ T3 confusion) | Split per this spec |

**Deprecation text (for roadmap / B-CS2 plan headers):**

```text
B-CS2 pass criteria describe T3 full-ops-pass on a pass-capable slug.
copy-import-495e552c is diagnostic canon (T0/T1a pass; T1b/T2/T3 fail as of 2026-05-30).
Do not use T3 failure on that slug alone as merge evidence against selection-only PRs.
```

---

## §12 — Verification (governance track)

No pytest required for C track closure.

**Manual verification:**

```powershell
# Reconfirm tier readback on diagnostic canon (informational)
python manage.py run_solver --slug copy-import-495e552c --no-replay
python manage.py run_solver --slug copy-import-495e552c --selection-mode evolution --no-replay
```

Compare `solver_run_id` to §5 table fields.

---

## References

- [`2026-05-30-rttp-ga-evolution-pr-ga-2-governance-close-design.md`](2026-05-30-rttp-ga-evolution-pr-ga-2-governance-close-design.md)  
- [`2026-05-24-b-cs2-trunk-ops-smoke-design.md`](2026-05-24-b-cs2-trunk-ops-smoke-design.md)  
- [`2026-05-24-throughput-target-percent-pr2c-design.md`](2026-05-24-throughput-target-percent-pr2c-design.md)  
- [`2026-05-29-reconstruction-capacity-c-gate-design.md`](2026-05-29-reconstruction-capacity-c-gate-design.md)  
- [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md)  
- [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)
