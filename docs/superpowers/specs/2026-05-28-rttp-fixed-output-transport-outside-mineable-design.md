# RTTP Fixed Output Transport Outside-Mineable Contract — Design Spec

**Date:** 2026-05-28  
**Status:** Approved (2026-05-28) — PR-1 plan: [`../plans/2026-05-28-rttp-fot-outside-mineable-pr1.md`](../plans/2026-05-28-rttp-fot-outside-mineable-pr1.md)  
**Work classification:** contract change · implementation change (phased PR-1 → PR-3)  
**Surfaces:** Candidate generator (Layer 2), incremental commit reprobe (Layer 4/7), Lab replay overlay, read-only validation (Layer 8)

**Related:**

- [`2026-05-27-rttp-miner-output-transport-topology-design.md`](2026-05-27-rttp-miner-output-transport-topology-design.md) — `fixed_output_transport_offset` vs `output_stub_offset` topology (INV-R)
- [`documents/Algorithm/asteroid_lab_02_pattern_library.md`](../../../documents/Algorithm/asteroid_lab_02_pattern_library.md) — `output_stub` not occupied; probe start
- [`documents/Algorithm/asteroid_lab_03_candidate_generator.md`](../../../documents/Algorithm/asteroid_lab_03_candidate_generator.md) — generate → validate → probe → normal/rejected
- [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md) — candidate probe ≠ commit proof
- [`documents/Algorithm/asteroid_lab_mining_installation/04_installation_guide.md`](../../../documents/Algorithm/asteroid_lab_mining_installation/04_installation_guide.md) — FOT vs route probe start

---

## Problem

On rim and inner-rim extractor anchors, inward-facing catalog rotations place **fixed output transport (FOT)** on `OptimizationInput.mineable_cells` (asteroid field). Lab replay overlay and committed layouts show the same pattern because both use `BundleCandidate` + `placement_overlay_projection`.

Waste mechanism:

```text
rim mineable anchor + inward output_dir
  → FOT = anchor + unit(output_dir) ∈ mineable_cells
  → field cell consumed by belt/pipe, not extractor/extension capacity
```

With extension throughput tiers (×4 / ×8 / ×12 / ×16), each lost field cell reduces practical capacity ceiling, not only visual clutter.

**Not caused by:** skeleton ring installing belt on rim first. `ring_cells` live on `boundary_offset_frame` outside the mineable bbox (`ring_builder.py`). Field belt/pipe comes from bundle FOT (and overlay route rows), not pre-commit rim ring install order.

---

## Goals

| Phase | Delivers |
|-------|----------|
| **PR-1** | Hard reject: normal pool never admits FOT ∈ `mineable_cells`; enum + tests + replay reject reason |
| **PR-2** | `OUTWARD_FROM_RIM` + void attach surface + platform probe fallback — [`2026-05-28-rttp-fot-pr2-outward-rim-void-probe-design.md`](2026-05-28-rttp-fot-pr2-outward-rim-void-probe-design.md) |
| **PR-3** | Ring/trunk alignment hints for probe cost / preference (no route commit in generator) |

**Non-goals:**

- Candidate generator must not commit placements (Phase 3).
- Replay / solver_summary / metrics must not become algorithm inputs.
- Validation must not repair topology (read-only assert only).
- Extractor anchor must remain ∈ `mineable_cells` (do not move extractor outside field).
- Global optimal routing or regret scoring overhaul in PR-1/PR-2.

---

## Coordinate contract (must not regress)

After RTTP miner topology normalization (INV-R):

```text
extractor_offset              @ anchor + (0, 0)   — occupied
fixed_output_transport_offset @ anchor + unit(output_dir)     — belt/pipe, NOT occupied
output_stub_offset            @ anchor + 2 * unit(output_dir) — route probe start, NOT occupied
```

**Critical naming (differs from informal draft):**

| Cell | Role | `BundleCandidate` / probe |
|------|------|---------------------------|
| FOT | First belt/pipe after extractor | `pattern.fixed_output_transport_offset` → `fixed_output_transport_cell(candidate)` |
| Output stub | Route probe BFS start | `candidate.output_stub` (= projected `output_stub_offset`) |

```text
output_stub == FOT + unit(output_dir)   # same axis, one step further out
output_stub ≠ FOT
```

Route probe (`probe_route`) starts at **`output_stub`**, not FOT (`candidate_generator.py`, `asteroid_lab_02`).

PR-1 reject predicate uses **FOT coord** (`fixed_output_transport_cell`). When FOT ∉ `mineable_cells` and topology INV-R-05 holds, `output_stub` is also outside mineable on the same axis; no separate stub-in-mineable reject is required for PR-1 unless concave exceptions are found in fixtures.

---

## Hard invariants

### INV-FOT-01 (PR-1, all policies ≥ `OUTSIDE_MINEABLE`)

For every **normal** `BundleCandidate` and every **confirmed** placement after commit:

```text
fixed_output_transport_cell(candidate) ∉ mineable_cells
fixed_output_transport_cell(candidate) ∉ occupied_cells
```

### INV-FOT-02 (PR-2, `OUTWARD_FROM_RIM`)

When `anchor_coord ∈ rim_cells` and policy is `OUTWARD_FROM_RIM`:

```text
output_dir ∈ outward_dirs(anchor, inp, domain)
```

`outward_dirs` definition (normative):

```text
For each cardinal direction d with unit vector u:
  neighbor = anchor + u
  neighbor ∉ mineable_cells
  AND neighbor ∉ blocked_incompatible_transport_cells for candidate.transport_kind
  AND (neighbor ∈ route_domain.traversable_cells
       OR neighbor is lift platform_coord
       OR neighbor ∈ external_void_cells with path to route_domain — see PR-2 implementation note)
```

**Do not** treat “non-mineable neighbor” alone as outward; must respect `RouteCellDomain` and transport mask (Phase 4).

### INV-FOT-03 (PR-1 optional hardening, same tranche as domain checks)

```text
output_stub ∉ occupied_cells   # already partially enforced
```

For PR-1+, reject before probe when FOT fails; existing `ROUTE_PROBE_START_IN_OCCUPIED` remains for stub ∩ occupied.

### INV-FOT-04 (PR-3, soft / scoring only)

Prefer FOT adjacent to `trunk_mask_cells` / ring frame / `existing_transport` trunk — scoring only, not commit authority.

---

## Policy enum

```python
class FixedOutputTransportPolicy(StrEnum):
    ALLOW = "allow"                          # diagnostic / regression compare only
    PENALIZE_FIELD_USAGE = "penalize_field_usage"  # not normal pool default
    OUTSIDE_MINEABLE = "outside_mineable"    # PR-1 hard reject
    OUTWARD_FROM_RIM = "outward_from_rim"    # PR-2; implies OUTSIDE_MINEABLE at rim
```

**Solver runtime default (after PR-2):** `OUTWARD_FROM_RIM`

**PR-1 production wiring:** `run_rttp_pipeline` passes `OUTSIDE_MINEABLE` into `generate_candidates`. Generator kwarg default remains `ALLOW` so unit tests and direct generator callers are not broken on small greenfield fixtures until PR-2 outward filter.

Diagnostic runs may set `ALLOW` to measure reject volume; production normal pool must not default to `ALLOW`.

---

## Reject reasons (extend `CandidateRejectReason`)

| Enum member | Value string | When |
|-------------|--------------|------|
| `FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE` | `fixed_output_transport_inside_mineable` | PR-1: FOT ∈ `mineable_cells` |
| `OUTPUT_DIR_NOT_OUTWARD_FROM_RIM` | `output_dir_not_outward_from_rim` | PR-2: rim anchor, dir ∉ `outward_dirs` |
| `FIXED_OUTPUT_TRANSPORT_NOT_IN_ROUTE_DOMAIN` | `fixed_output_transport_not_in_route_domain` | PR-1+: FOT not probe-adjacent per domain rules (see below) |
| `FIXED_OUTPUT_TRANSPORT_KIND_BLOCKED` | `fixed_output_transport_kind_blocked` | FOT coord ∈ `blocked_incompatible_transport_cells` |

Existing reasons unchanged: `fixed_output_transport_in_occupied`, `route_probe_start_in_occupied`, etc.

**PR-1 scope note:** `FIXED_OUTPUT_TRANSPORT_NOT_IN_ROUTE_DOMAIN` may be deferred to PR-2 if it duplicates outward filter; minimum PR-1 is mineable + occupied + incompatible transport.

---

## Candidate generator changes (Layer 2)

**Order (after `_project_spec`, before `probe_route`):**

1. `fot_abs = anchor + spec.fixed_output_transport_offset` (same as `fixed_output_transport_cell` on projected candidate).
2. Reject `FIXED_OUTPUT_TRANSPORT_IN_OCCUPIED` if `fot_abs ∈ occupied` (existing).
3. If policy ≥ `OUTSIDE_MINEABLE`: reject `FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE` if `fot_abs ∈ inp.mineable_cells`.
4. If `fot_abs ∈ inp.blocked_incompatible_transport_cells`: reject `FIXED_OUTPUT_TRANSPORT_KIND_BLOCKED`.
5. If policy == `OUTWARD_FROM_RIM` and `anchor ∈ inp.rim_cells`: compute `outward_dirs`; reject `OUTPUT_DIR_NOT_OUTWARD_FROM_RIM` if `spec.output_dir` not allowed.
6. Existing stub/axis checks (`ROUTE_PROBE_START_IN_OCCUPIED`, `EXTENSION_ON_OUTPUT_AXIS`, overlap, `occupied ⊆ mineable`).
7. `probe_route(domain, output_stub, goals)` — unchanged start coord.

**Forbidden:**

- Using `output_stub` coord as FOT reject target.
- Committing belt/pipe in generator.
- Importing replay artifacts into reject logic.

**Extractor placement policy (orthogonal):**

`ExtractorPlacementPolicy` remains separate. PR-2 may change runtime default from `INTERIOR_AND_RIM` to `RIM_ONLY` only if product approves; this spec does not mandate it. Outward filter applies when anchor ∈ `rim_cells`; inner anchors still benefit from PR-1 `OUTSIDE_MINEABLE`.

---

## Commit changes (Layer 7)

Before commit-time reprobe accepts a candidate:

- Assert INV-FOT-01 against latest `OptimizationInput` and projected FOT (defense in depth; do not trust generation-time pool alone).
- Reprobe still authoritative for reachability; FOT geometry is not repaired at commit.

---

## Validation changes (Layer 8, read-only)

Add assert-only issue path (or extend `validate_final_layout`) for confirmed layout where any committed candidate has FOT ∈ `mineable_cells`. **Fail, do not repair.**

---

## Replay / UI

Expose new reject reason strings in RTTP replay diagnostics / rejected candidate payloads (same enum values as `CandidateRejectReason`).

Overlay acceptance (PR-1):

```text
confirmed + candidate overlay: zero cells with
  overlay_semantic_kind ∈ {placement.*_fixed_output_transport}
  AND coord ∈ mineable_cells
```

---

## Phased delivery (approved sequencing)

| PR | Scope | Out of scope |
|----|-------|--------------|
| **PR-1** | `OUTSIDE_MINEABLE` hard reject + enum + unit tests + replay reason + commit/validation asserts | Outward filter, regret scoring |
| **PR-2** | `OUTWARD_FROM_RIM` + `outward_dirs` + rim tests + runtime default policy | Ring scoring |
| **PR-3** | FOT ↔ trunk/ring adjacency preference (probe cost / tie-break only) | Generator route commit |

Do not ship PR-3 in the same merge as PR-1.

---

## Test plan (normative names)

**Candidate generator**

- `test_candidate_rejects_fixed_output_transport_inside_mineable`
- `test_candidate_accepts_outward_fot_on_rim`
- `test_candidate_rejects_inward_output_dir_from_rim` (PR-2)
- `test_candidate_rejects_fot_in_blocked_incompatible_transport`
- `test_candidate_generation_records_fot_reject_reason_enum`

**Commit**

- `test_incremental_commit_never_confirms_candidate_with_mineable_fot`
- `test_commit_reprobe_preserves_fot_outside_mineable_invariant`

**Validation**

- `test_validation_fails_confirmed_candidate_with_mineable_fot` (assert only, no repair)

**Replay / overlay**

- `test_replay_marks_rejected_candidate_fot_inside_mineable`
- `test_lab_overlay_has_zero_confirmed_mineable_fot_cells`

Use fixture rim anchors with inward vs outward rotations; assert reject before probe for PR-1 cases.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Normal candidate pool shrink | Record reject counts by reason in replay diagnostics; compare `ALLOW` vs `OUTSIDE_MINEABLE` on representative slugs |
| Concave rim multiple outward dirs | `outward_dirs` is a set; any valid dir accepts catalog spec with matching `output_dir` |
| Confusion FOT vs stub | Docs + tests pin `fixed_output_transport_cell` vs `output_stub` |
| Overlap with topology PR1 | Topology PR fixes occupied/R-cell pollution; this spec fixes FOT mineable placement |

---

## Self-review (2026-05-28)

| Check | Result |
|-------|--------|
| Generator does not commit | Pass |
| Probe start remains `output_stub` | Pass |
| Validation read-only | Pass |
| FOT ≠ output_stub documented | Pass (corrected from draft) |
| Placeholder/TBD | None |
| Single-plan scope | PR-1 fits one implementation plan; PR-2/3 separate plans |

---

## Approval

- [x] User review of this spec file (architect B+C + phased PR-1/2/3)
- [x] Implementation plan: [`2026-05-28-rttp-fot-outside-mineable-pr1.md`](../plans/2026-05-28-rttp-fot-outside-mineable-pr1.md)
