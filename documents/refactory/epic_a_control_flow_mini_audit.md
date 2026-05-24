# Epic A — Control Flow Mini-Audit (§4.3 vs Implementation)

**Nature:** Read-only audit deliverable. **No code, heuristic, or validation algorithm changes.**  
**Canonical (table):** `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` §4.3 (linked with `11_step8_recovery.md` §13.2). If not local, cite **GitHub `master` original** (§5.1).  
**Updated:** 2026-05-12 — §5 reflects full canonical table·Expected citations·PR review **A/B/Info** finalized.

---

## 1. Epic A Entry Conditions (Role of This Document)

| Condition | Status |
|------|------|
| Epic B semantic fields·replay bridge stabilization | Done perspective (merge criteria per reviewer) |
| This mini-audit | **Pre-implementation** deliverable |
| Next step | After §5.4 **PR review classification** fixed, lock goal (A/B) in `02_pipeline_recovery_control_flow.md` and split Epic A **implementation** PR |

---

## 2. Identifier Normalization (Audit Premise)

**trace / summary / canonical trigger are not the same.** Keep this distinction in Epic A implementation.

| Category | Role | Example |
|------|------|------|
| **Canonical trigger** | §4.3 table row ID (contract·review language) | `pass3_connectivity_break` |
| **Trace / debug** | Greedy·Pass3 internal observation (must not alone justify control branches) | `pass3_connectivity_reject_sample` |
| **Summary / contract field** | Flags·phases on `solver_summary`·replay | `recovery_post_reclaim_pass3_connectivity_break`, `recovery_contract_phases[]` |

### 2.1 Three Confusion Sets to Watch

| Canonical (table language) | Actual identifier in code | Notes |
|--------------------|---------------------------|------|
| `pass3_connectivity_break` | `pass3_connectivity_reject_sample` (greedy metrics), `pass3_reverted` + `pass3_rollback_reason` | "Connectivity reject sample" is **during search** rejection; final map revert combines with **bridge validation** failure block |
| (Separate from table) post-reclaim connectivity failure | `post_reclaim_pass3_pass3_reverted`, `post_reclaim_pass3_skip_reason` | `recovery_post_reclaim_pass3_connectivity_break` is **summary tag** |
| `post_reclaim_pass3_connectivity_break` (canonical) | `RECOVERY_PHASE_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK`, `recovery_post_reclaim_pass3_connectivity_break` | `tag_post_reclaim_pass3_connectivity_break` reads `post_reclaim_pass3_pass3_reverted` |

---

## 3. Criteria for "Actual Control Flow"

When auditing, **only the following** count as "recovery path":

- `mining_map` / `map_final` passed by function **return**
- Rollback to prior stage map via **rollback** transaction·`pass3_reverted`, etc.
- Re-execution in `run_solver_timeline_pipeline` **for loop** (next cycle entry condition)
- Early exit via **gates** like `validation_recovery_allowed`

**Excluded:** Do not describe branching as if trace dict values alone imply control flow.

---

## 4. Orchestrator Baseline (One Line)

`recovery_orchestrator.run_solver_timeline_pipeline`:

1. **Once:** Pass12 → STEP4 → fix `routing_snapshot`  
2. **Loop (`max_cycles`):** copy `routing_snapshot` → **Pass3 → P4 → finalize**  
3. Exit if `out["ok"]`. Else if `validation_recovery_allowed(out)`, re-run **same loop (full Pass3→P4→finalize)** with `pass3_recovery_context=True`.  
4. STEP4 is **not** re-invoked inside the loop.

Evidence: `recovery_orchestrator.py` `run_solver_timeline_pipeline` (~lines 339–467), `pass3.py` `run_pass3_stage`, `p4_reclaim.py` `run_p4_reclaim_stage`, `finalize.py` `build_final_solver_output`.

---

## 5. §4.3 Canonical Citation and vs Implementation (For PR Review)

### 5.1 Canonical Source (Authoritative)

- **Blob (readable):** [github.com/tigers2020/Shapez2Factory/blob/master/documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md](https://github.com/tigers2020/Shapez2Factory/blob/master/documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md)  
- **Raw (copy baseline):** [raw.githubusercontent.com/.../02_pipeline_control_flow.md](https://raw.githubusercontent.com/tigers2020/Shapez2Factory/master/documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md)  
- Citation point: sync with **`master` HEAD**. If canonical moves/changes, **re-copy** table in this section.

### 5.2 §4.3 Recovery Trigger Recovery Paths (Full Canonical Table)

Below is the canonical **§4.3 table** copied verbatim (rendering same as canonical).

```text
| Trigger | Occurrence Point | Recovery Return Path | On Failure |
| ----------------------------- | ----------------------------------------- | ------------------------------------------------------- | ---------------------------------------------- |
| `step4_routing_failure` | STEP 4 route generation failure | Retry STEP 4; rollback that placement or use alternate trunk | Roll back unrouted placement then retry STEP 4 |
| `step4_capacity_failure` | STEP 4 capacity split/additional trunk failure | Retry STEP 4; change trunk split candidate | Roll back offending placement |
| `pass3_connectivity_break` | STEP 5 Pass3 breaks connectivity | Apply **§4.3.1** → return to **STEP 6 Reclaim placement loop** | Roll back Pass3 changes; keep last known-good |
| `post_reclaim_pass3_connectivity_break` | STEP 7 post-reclaim Pass3 rerun breaks connectivity | Roll back rerun changes → STEP 9 (**no additional rerun**, §4.3.2) | Keep existing connected layout; partial success possible |
| `reclaim_incremental_failure` | STEP 6 new placement routing failure | Roll back that reclaim candidate; continue STEP 6 | Final validation when candidates exhausted |
| `final_validation_failure` | STEP 9 invariant failure | After recovery, re-validate STEP 9 (**no STEP 4 re-entry**) | Partial success or solver failure after attempts exceeded |
```

Sentence after canonical table (same source):

```text
`final_validation_failure` recovery does not automatically re-run STEP 4 main pipeline. If capacity redesign is needed, upper orchestrator runs separately.
```

§4.3.2 gist (STEP 7 failure; same source summary):

```text
- Connectivity break: trigger=post_reclaim_pass3_connectivity_break
- Return: not STEP 6 re-entry; roll back only Pass3 changes from rerun and proceed to STEP 9 Final validation.
- Failure in same rerun block → not another rollback/re-search loop; immediately restore known-good and proceed to STEP 9 (no additional rerun).
```

### 5.3 Implementation Mapping Table (Expected = §5.2 Citation Summary)

**Criterion:** return path·rollback·`run_solver_timeline_pipeline` loop only (do not infer control meaning from trace field names alone).

| Canonical Trigger | Expected §4.3 (Citation Summary) | Current Return Path (Implementation) | Drift? | PR Review (A/B/Info) | Notes |
|--------------------|---------------------------|------------------------------|--------|-------------------|-------|
| `step4_routing_failure` | After recovery **retry STEP 4**, etc. (table "Recovery Return" and "On Failure" columns). | STEP4 in `run_solver_timeline_pipeline` **once outside loop**. Partial failure summarized in `finalize.py` as `partial_success`·`step4_partial_failure`, etc.; **no dedicated STEP4 retry loop**. | **yes** | **B** | Orchestrator not 1:1 with table "STEP 4 retry" → recommend **MVP exception documentation (B)**. |
| `step4_capacity_failure` | On STEP 4 capacity failure **retry STEP 4**·rollback (table). | No separate `return_reason=…capacity…` trigger; `validation_recovery_allowed` does not gate loop on capacity (`recovery_policy.py`). | **yes** | **B** | Row exists in canonical → **exception·mapping documentation (B)**. |
| `pass3_connectivity_break` | §4.3.1·return to **STEP 6 Reclaim**; on failure Pass3 rollback·known-good. | On Pass3 revert `map_final` keeps STEP4 snapshot then **P4 (reclaim path)** in same cycle (`pass3.py`). **Remedial STEP4 once** from §4.3.1 not explicit separate branch in code. | **partial** | **B** | If "STEP6 = reclaim loop" interpretation, path is close; §4.3.1 details → **canonical exception (B)** review. |
| `post_reclaim_pass3_connectivity_break` | rerun rollback → **STEP 9**, no additional rerun (§4.3.2). | `_run_post_reclaim_pass3_once` on validation failure **returns previous map** then P4 stage ends·finalize (`solver_timeline.py`). **No re-search loop within same rerun block**. | **no** (STEP7 meaning) | **Info** | Aligns with canonical for STEP7 block. Later `validation_recovery` re-running Pass3→P4→finalize is **separate trigger** (`final_validation_failure` row). |
| `reclaim_incremental_failure` | candidate rollback then **continue STEP 6**; exhausted → Final validation. | Rollback and loop continue·tagging inside P4 loop (`p4_reclaim.py`, `recovery_policy.py`). | **no** | **Info** | Direction matches canonical; limits vs §4.2·§12 separate comparison. |
| `final_validation_failure` | After recovery **re-validate STEP 9**; **no automatic STEP 4 re-run** (table·following sentence). | STEP4 does not re-enter (**aligned**). But `validation_recovery_allowed` repeats **full Pass3→P4→finalize** as additional cycle (`recovery_orchestrator.py` lines 350–464). If table read narrowly as **STEP9-only re-run**, **mismatch**. | **partial** | **B** | **Most important row:** "no STEP4" satisfied; narrow "STEP9 only" vs full cycle → **MVP exception·terminology alignment (B)** documentation safer. |

### 5.4 PR #6 Follow-Up Gate (Final Classification)

| Gate | Status |
|--------|------|
| Canonical §4.3 citation secured | **Done** (§5.1–5.2) |
| §5 Expected authoritative citation | **Done** (§5.3 "Expected" = §5.2 citation summary) |
| Per-row A/B/Info | **Done** (§5.3 last column) |
| `final_validation_failure` classification | **B** (STEP4 non-re-entry is Info-like, but **STEP9-only narrow reading** gap → recommend **B** exception documentation) |

**Epic A implementation branch:** After §5.4 merged in this repo and team agrees to reflect **B wording** in canonical or this `refactory` plan, open branch (same as review comment).

---

## 6. A/B Classification Guide (For Audit Conclusions)

| Class | Meaning | Next Action |
|------|------|-----------|
| **A** | Canonical table is correct; plan to align implementation is realistic | Epic A implementation PR adjusts **control flow only** (with regression·NDJSON·contract) |
| **B** | Keep current behavior; add **MVP exception** section·table column ("implementation mapping") to canonical | Record **official deviation** in `02_pipeline_control_flow.md` (external canonical) or this repo summary |

**Forbidden in Epic A (reminder):** reroute heuristics·congestion tuning·reclaim strategy·corridor replacement policy·validation algorithm redesign. **Control-flow normalization / doc·contract alignment only.**

**PR review gate:** When §5.3·§5.4 classification merges with team agreement, doc phase before Epic A **implementation** is complete (re-copy §5.2 if canonical `master` changes).

---

## 7. Recommended Follow-Up (Not Implementation)

1. **Canonical sync:** If `master` §4.3 table changes, **re-copy full text** in §5.2 and align §5.3 Expected summary.  
2. **B classification documentation:** Add **MVP implementation mapping** section to `02_pipeline_recovery_control_flow.md` or canonical repo fixing **B** rationale for `step4_*`·`final_validation_failure`·`pass3_connectivity_break` on one page.  
3. Decide in separate ticket whether to add **canonical trigger id** to `recovery_contract_phases` (optional).  
4. Unit test: "stage order snapshot for one trigger" aligns with verification section in `02_pipeline_recovery_control_flow.md`.

---

## 8. Reference Paths (Evidence)

| File | Purpose |
|------|------|
| `solver_pipeline/recovery_orchestrator.py` | Timeline loop·validation recovery |
| `solver_pipeline/pass3.py` | Pass3 accept/revert·`pass3_reverted` |
| `solver_pipeline/p4_reclaim.py` | P4 + post-reclaim Pass3 + tagging calls |
| `solver/solver_timeline.py` | `_run_post_reclaim_pass3_once` revert |
| `solver/recovery_policy.py` | `tag_*`, `validation_recovery_allowed`, phases |
| `solver_pipeline/finalize.py` | `return_reason`, `step4_partial_failure`, termination |

---

## 9. Relationship to `02_pipeline_recovery_control_flow.md`

- **02:** Goals·risks·reference code (epic plan).  
- **This document:** §4.3 **canonical citation** (§5.2)·implementation comparison table·**A/B/Info** finalized (§5.3–5.4).  
- Before Epic A implementation, reflect MVP exception (B) paragraph in **02** and record same **B** rationale in canonical when needed.
