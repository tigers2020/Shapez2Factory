# T1b Pipeline Layout Validation — Investigation Report

**Date:** 2026-05-30  
**Status:** CLOSED (E-track read-only investigation)  
**Canon slug:** `copy-import-495e552c`  
**Design spec:** [`2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md`](../specs/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md)  
**Plan:** [`2026-05-30-rttp-t1b-pipeline-layout-validation-investigation.md`](../plans/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation.md)

---

## Evidence table

| Run / replay | committed_count | catalog_passed | validation_passed | Primary FL-xx | detail |
|--------------|-----------------|----------------|-------------------|---------------|--------|
| Canon probe (`run_canon_slug_probe`, default DB) | 32 | true | false | **FL-06** | `candidate_id=-1,-14:cat_canon_manual_Layout_ShapeMiner_N:shape_belt`; `output_stub=(-1,-16)`; `reserved_route_cells_nonempty=true` |
| Ops replay (same config class) | 32 | true | false | **FL-06** (same) | `solver_run_id=108`; `issue_codes=[rttp_validation_failed, throughput_target_shortfall]` |

**Historical reference (Run 103):** catalog audit PASS, commit `validation_passed=false` — consistent with this probe.

---

## E.2 Catalog audit

- `catalog_passed=true`
- `catalog_mismatch_count=0`
- `catalog_error_issue_codes=[]`
- **Confirmed:** catalog path is not the primary T1b failure for this slug.

---

## E.3 Pipeline composition

- `commit_passed=false`, `validation_passed=false` → `pipeline_composition_anomaly=false`
- **No wiring anomaly:** step `passed` matches `metrics.validation_passed` as expected from `pipeline.py`.

---

## E.4 T2 causality

- **Classification:** `T2_independent`
- **Notes:** Layout gate failed on **FL-06** (stub vs reserved route cells) before throughput semantics apply. `throughput_target_shortfall` and `selection_goal_cap` are parallel T2 signals on the same run; they do not explain the layout assert failure.

---

## Owner matrix (next track)

| FL-xx | Condition | Likely owner | Recommended next track |
|-------|-----------|--------------|------------------------|
| **FL-06** | `reserved_route_cells` non-empty AND `output_stub ∉ reserved_route_cells` | Route reservation / output-stub alignment after multi-commit | **Fix spec:** commit routing domain — ensure committed `output_stub` is included in `reserved_route_cells` (or reservation policy documents intentional exclusion) |

**Not recommended next:** catalog data edit, validation assert weakening, slug swap (A/B) until routing/stub policy is resolved.

---

## Conclusion

Primary T1b failure on diagnostic canon is **FL-06** (output stub not in reserved route cells when reservation set is non-empty), **not** catalog audit mismatch.

At 32-commit stress, the first failing candidate in commit order exposes stub/reservation misalignment:

```text
candidate_id: -1,-14:cat_canon_manual_Layout_ShapeMiner_N:shape_belt
output_stub: (-1, -16)
```

---

## Spec §11 acceptance checklist

- [x] Primary failing **FL-xx** identified (FL-06)
- [x] E.2 catalog audit pass confirmed
- [x] E.3 pipeline composition verified (no anomaly)
- [x] E.4 T2 causality classified (`T2_independent`)
- [x] Owner matrix row selected (routing / stub alignment fix spec)
- [x] No production validation behavior change in E phase
- [x] `current_plan.md` E row → CLOSED (see governance commit)

---

## Tooling delivered (investigation-only)

| Artifact | Path |
|----------|------|
| FL-xx probe | `harness/investigation/rttp_final_layout_assert_probe.py` |
| Step forensics | `harness/investigation/rttp_t1b_step_forensics.py` |
| Canon CLI probe | `harness/investigation/run_canon_slug_probe.py` |
| Unit tests | `tests/investigation/test_rttp_final_layout_assert_probe.py` |
| Integration test (test DB; skips if slug absent) | `tests/investigation/test_rttp_t1b_canon_slug_layout_probe.py` |
