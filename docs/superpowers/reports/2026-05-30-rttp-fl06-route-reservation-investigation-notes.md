# FL-06 Route Reservation Investigation Notes

**Date:** 2026-05-30  
**Design spec:** [`2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md`](../specs/2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md)

---

## Failing candidate (Run 108 / E-track)

```text
candidate_id: -1,-14:cat_canon_manual_Layout_ShapeMiner_N:shape_belt
output_stub: (-1, -16)
policy: PLATFORM_FALLBACK_WHEN_STUB_BLOCKED (OUTWARD_FROM_RIM default)
```

---

## Q1–Q6 answers

| ID | Answer | Evidence |
|----|--------|----------|
| **Q1** | `probe_start` = platform/anchor fallback (not stub) for H1a narrow-corridor repro | `7,5:cat_bv_1_N:shape_belt` → probe_start `(7,5)`, stub `(7,3)` |
| **Q2** | **false** on H1a repro | diagnostic snapshot |
| **Q3** | **false** — stub not on `probe.path` when fallback start used | path-only snapshot |
| **Q4** | **false** before fix — `_route_cells_from_path` omits stub | raw route_cells vs stub |
| **Q5** | **true** — `PLATFORM_FALLBACK_WHEN_STUB_BLOCKED` active under `OUTWARD_FROM_RIM` | pipeline default + narrow repro |
| **Q6** | N-direction stub offset places stub outside traversable phase at commit time (`initial_phase(stub)=None`) while anchor is platform | narrow corridor probe |

---

## Root cause classification

**Primary: H1a** — commit-time probe starts from fallback platform/anchor; `probe.path` and `_route_cells_from_path` omit `output_stub`, but `validate_final_layout` FL-06 requires stub ∈ `reserved_route_cells` when reservation non-empty.

**Secondary: H1b ruled out** for primary repro — stub not on path at all (not path−occupied filtering).

---

## Chosen fix option

**Guarded Option A** implemented in `_route_cells_with_required_output_stub`:

- When `route_cells` non-empty and stub missing: union `{output_stub}` if stub ∉ occupied and stub ∉ blocked_cells.
- Else: `CommitConflictReason.OUTPUT_STUB_NOT_RESERVED` (commit reject).

Rationale: stub is the committed inlet attachment cell (see pre-commit `INLET_ON_SHARED_TRANSPORT` guard). Validation FL-06 checks set membership, not `initial_phase` at stub.

---

## Post-fix canon replay (Run 109)

| Metric | Before (108) | After (109) |
|--------|--------------|-------------|
| Primary FL-xx | FL-06 | **FL-OK** |
| `validation_passed` | false | **true** |
| `committed_count` | 32 | 30 |
| `catalog_passed` | true | true |
| `issue_codes` | rttp_validation_failed, throughput_target_shortfall | throughput_target_shortfall only |

T1b layout gate **PASS**. T2 remains independent (`throughput_target_shortfall`).

Two commits dropped — candidates whose stub could not be legally reserved are now rejected at commit time instead of failing FL-06 at validation.
