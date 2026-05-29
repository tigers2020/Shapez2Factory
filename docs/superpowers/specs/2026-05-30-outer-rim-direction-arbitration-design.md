# Outer-Rim Direction Arbitration — Design Spec

**Document type:** Solver / Lab contract (L3 pool preservation · L4 overlap selection · replay observability)  
**Status:** **APPROVED — Placement Contract Architect amendments applied (2026-05-30)**

**Implementation plans (separate files):**

- PR-A: [`2026-05-30-l4-replay-sprite-cell-kind-fallback.md`](../plans/2026-05-30-l4-replay-sprite-cell-kind-fallback.md)
- PR-B: [`2026-05-30-outer-rim-direction-arbitration.md`](../plans/2026-05-30-outer-rim-direction-arbitration.md)  
**Work classification:** contract change · implementation change · UI change (P0 sprite, separate PR)  
**Scope:** `layer_03_rim_mining_bundles/` · `layer_04_rim_bundle_placement/` · `layers/contracts/` · `replay/layer04_segment.py` · `web/static/web/js/asteroid_miner_layout_lab.js`  
**Parent / amends:** [`2026-05-28-layer-04-rim-bundle-placement-design.md`](2026-05-28-layer-04-rim-bundle-placement-design.md) §3.4 · [`2026-05-28-layer-03-footprint-aware-exterior-direction-enumeration-design.md`](2026-05-28-layer-03-footprint-aware-exterior-direction-enumeration-design.md)

**Korean title (reference):** Outer-rim corner 방향 greedy 선점 — L4 mining-first 선택

---

## §1 — Problem

### 1.1 Symptom

On concave / corner outer-rim anchors, **W and S (or E and N) output directions** can both yield feasible bundle candidates with overlapping `mining_occupied_cells`. The lower-yield direction is selected and the higher-yield direction is rejected with `PHYSICAL_OVERLAP`, not because route probe failed and not because L3 failed to enumerate directions.

### 1.2 Root cause (normative)

This is **not** E/W hard-coding in direction enumeration. `exterior_output_dir_candidates` may return all feasible cardinals. L3 does **not** globally reserve footprint between candidates.

The failure is **L4 greedy selection order**:

```text
select_non_overlapping_candidates sorts by intrinsic_priority_rank, anchor (y,x), equivalence_key, candidate_id
→ first candidate in sort order wins occupied cells
→ later overlapping candidate gets PHYSICAL_OVERLAP
→ equivalence_key hash can decide same-anchor W vs S when ranks tie
```

**Name:** `outer_rim_direction_greedy_preemption` (corner direction arbitration).

### 1.3 Non-goals (v1)

| Item | Status |
|------|--------|
| MWIS / max-weight independent set on overlap graph | **Deferred** (escalation only; §8) |
| Changing M-anchor projection formula | Out of scope |
| Using replay / metrics as solver input | Forbidden (unchanged) |

---

## §2 — Layer responsibilities

### 2.1 L3 — preserve + observe

| MUST | MUST NOT |
|------|----------|
| Enumerate bounded cardinal `output_dir` per rim anchor (R2-lite) | Globally reserve / commit footprint across candidates |
| Keep feasible W and S (etc.) in `normal_candidates` when route probe succeeds | Drop higher-yield direction because a lower-yield direction was enumerated first |
| Expose `effective_mining_gain`, `output_dir`, pool metrics | Use connector distance alone to discard directions before footprint test |

**Normative:**

```text
L3 MUST NOT discard a higher-yield output direction solely because
a lower-yield direction for the same rim/corner area was enumerated first.

Direction enumeration is provisional.
Footprint conflict arbitration belongs to L4 selection unless the conflict
is within a single invalid bundle footprint (local geometry reject).
```

**Forbidden:**

```text
- Reserving W/E before evaluating N/S alternatives (L4 issue; L3 must not add global reserve)
- Rejecting S/N because W/E was enumerated first in L3
- Using field-outside-only rule to reject valid transport-on-field entries (project invariant)
```

### 2.2 L4 — arbitrate overlap

| MUST | MUST NOT |
|------|----------|
| Deterministic **mining-first greedy** non-overlap selection (§3) | Re-run route probe or change L3 expectations |
| Enrich `PHYSICAL_OVERLAP` rejections with winner/loser mining metadata (§4) | Equivalence dedupe (L3 owner) |
| Sort by `effective_mining_gain` before `equivalence_key` when footprints differ | Use `equivalence_key` before mining gain |

---

## §3 — L4 selection contract (replaces parent §3.4 sort)

### 3.1 `effective_mining_gain`

**Definition:**

```text
effective_mining_gain =
  number of mineable asteroid field cells covered by the candidate mining footprint
```

**v1 implementation:**

```python
effective_mining_gain = len(candidate.mining_occupied_cells)
```

Future versions MAY subtract already-covered cells or apply resource weights; the metric name MUST remain `effective_mining_gain`.

Expose on `BundleCandidate` as a derived property or on `RouteProbedBundleCandidate` observability wire only — implementation choice; sort MUST use the definition above.

### 3.2 L4 selection input (normative)

```text
L4 selection input MUST contain only candidates with route_probe_status == SUCCEEDED.

Candidates with route_probe_status != SUCCEEDED MUST NOT enter the non-overlap sort.
They SHOULD be rejected earlier with RimPlacementRejectReason.NON_SUCCEEDED_PROBE
(or equivalent pre-sort rejection) before greedy overlap selection.
```

If a candidate is marked `SUCCEEDED` but `route_cost` is missing on `route_probe_result`, `route_cost` MUST be treated as `+inf` **within** the succeeded pool only (tie-break degradation, not demotion to failed pool).

### 3.3 Sort key (normative)

Succeeded candidates are sorted **ascending** by the tuple below. Lower tuple = earlier = wins overlap conflicts.

| # | Key | Missing value |
|---|-----|----------------|
| 1 | `-effective_mining_gain` | N/A (0 if empty footprint — should not occur for succeeded probes) |
| 2 | `route_cost` | `+inf` if `route_probe_result` is None or `route_cost` absent |
| 3 | `intrinsic_priority_rank` | — |
| 4 | `anchor_coord[1]` (y) | — |
| 5 | `anchor_coord[0]` (x) | — |
| 6 | `connector_goal_distance` | `+inf` if undefined (§3.4) |
| 7 | `output_dir` tie-break | fixed order: N, E, S, W (`Direction` enum: `n`, `e`, `s`, `w`) |
| 8 | `candidate_id` | — |

**Critical:**

```text
equivalence_key MUST NOT appear in the L4 sort key.
When candidates have different mining_occupied_cells, sort MUST NOT use equivalence_key
before effective_mining_gain.
```

`route_cost` is **lower is better** — sort ascending. **Do not** use `-route_cost`.

### 3.4 `connector_goal_distance`

For L4 sort only (not solver routing):

```text
connector_goal_distance =
  Manhattan distance from the candidate's actual transport entry coordinate
  (candidate.route_probe_start_coord, or derive_transport_entry_coord(anchor, output_dir))
  to route_probe_result.goal_coord
```

**Forbidden:** raw `anchor + output_dir delta` without the same normalized cardinal stepping utility used by L3 route probe (`derive_transport_entry_coord` / `rotate_offset` on canonical gene offsets). This project has no `x == 0` column guarantee on reconstruction grids.

If `route_probe_result` is None or `goal_coord` is None → treat as `+inf`.

### 3.5 Acceptance / rejection (unchanged semantics)

```text
Accept when:
  route_probe_status == SUCCEEDED
  occupied_cells ∩ selected_occupied == ∅
  budget_ctx.remaining_budget_ms() > 0 at decision time

Reject overlap:
  reason = PHYSICAL_OVERLAP
  conflicting_candidate_id = winner candidate id (canonical)
  plus metadata §4
```

Greedy scan order = sort order above. **Not** MWIS.

---

## §4 — L4 rejection observability

`RimPlacementRejectReason` stays `PHYSICAL_OVERLAP` (no new enum required for v1).

`RimPlacementRejection` MUST add diagnostic fields (wire + replay inspector; not algorithm input):

| Field | Type | Description |
|-------|------|-------------|
| `rejected_candidate_id` | `str` | Loser candidate id (required on rejection rows) |
| `rejected_output_dir` | `str` | Loser `output_dir.value` |
| `rejected_mining_cell_count` | `int` | Loser `effective_mining_gain` |
| `conflicting_candidate_id` | `str \| None` | **Canonical** winner candidate id (existing field) |
| `conflicting_winner_candidate_id` | `str \| None` | MAY mirror `conflicting_candidate_id` for replay readability |
| `conflicting_winner_output_dir` | `str \| None` | Winner direction |
| `conflicting_winner_mining_cell_count` | `int \| None` | Winner gain |
| `winner_selected_due_to_higher_mining_gain` | `bool` | `True` iff winner gain > loser gain |

**Alias policy:**

```text
conflicting_candidate_id remains the canonical winner id field.
conflicting_winner_candidate_id MUST equal conflicting_candidate_id when both are set.
```

**Optional (v1 recommended for inspector):**

| Field | Type | Description |
|-------|------|-------------|
| `overlap_tiebreak_step` | `str \| None` | When `winner_selected_due_to_higher_mining_gain` is false: which sort key broke the tie (`route_cost`, `intrinsic_priority_rank`, `anchor`, `connector_goal_distance`, `output_dir`, `candidate_id`) |

When `winner_selected_due_to_higher_mining_gain` is false (tie on gain), `overlap_tiebreak_step` SHOULD be set during rejection construction.

---

## §5 — L3 observability (P1 / P2)

### 5.1 Per-candidate metrics (pool / replay)

Extend L3 observability wire (output-only) with at minimum:

```text
candidate_id, anchor_coord, output_dir,
effective_mining_gain, route_cost, connector_goal_distance
```

### 5.2 P2 — premature reject audit

Metrics counters (no behavior change required for P3 fix):

```text
direction_pool_retention_by_output_dir  # succeeded normals / attempts per dir
budget_exhausted_before_dir_count     # optional, if budget bias suspected
```

L3 expansion loop order (anchor × sorted dirs × seeds) MAY be documented; changing it is not required if L4 sort fixes the corner fixture.

---

## §6 — PR split

| PR | Priority | Scope |
|----|----------|--------|
| **PR-A** | P0 | Sprite: `miner` / `extension` overlay kinds → correct `shape_miner` / `shape_miner_extension` (or `tile_type`) — no belt fallback. Files: `replay/layer04_segment.py`, `asteroid_miner_layout_lab.js`, `lab_map_rendering_contract.md`. **Do not mix with PR-B.** |
| **PR-B** | P1→P3 | Corner arbitration: P1 observability, P2 L3 audit metrics, **P3 L4 mining-first sort** (core fix). Plan: [`2026-05-30-outer-rim-direction-arbitration.md`](../plans/2026-05-30-outer-rim-direction-arbitration.md) |

**Implementation plans MUST be separate files** (PR-A sprite vs PR-B solver). Do not merge into one plan.

---

## §7 — P0 sprite contract (PR-A summary)

**Bug:** Replay emits `ReplayOverlayCell(kind="miner"|"extension")`. Lab maps `kind` → `cell_kind`; fallback `inferTransportSpriteIdentifier` → belt when `transport_kind == shape_belt`.

**Fix (normative):**

```text
L4 replay overlay MUST emit domain cell_kind (shape_miner / shape_miner_extension / fluid_*)
OR emit tile_type / sprite_identifier for Layout_*Miner*

Lab JS MUST treat legacy kind miner|extension on L4 frames as tint-only OR map to domain kinds
```

Align with [`documents/ai/lab_map_rendering_contract.md`](../../../documents/ai/lab_map_rendering_contract.md).

---

## §8 — MWIS escalation (C — not v1)

Implement MWIS only if **after** PR-B P3:

1. Corner W/S fixture still selects W over S.  
2. Repeated fixtures where two medium-yield placements beat one high-yield greedy choice.  
3. Benchmark shows mining coverage regression from greedy.  
4. Overlap graph construction already exists and MWIS marginal cost is low.

Until then: **YAGNI**.

---

## §9 — Tests

### 9.1 Fixture — corner W/S overlap (`tests/unit/asteroid_lab/layers/fixtures/`)

Synthetic `ReconstructionCompleteMap` + minimal L2 plan + one seed:

```text
Anchor on corner outer rim.

W candidate: output_dir=W, effective_mining_gain=6
S candidate: output_dir=S, effective_mining_gain=9
mining_occupied_cells overlap between W and S
Both route_probe SUCCEEDED
```

### 9.2 L3 test

```python
pool_dirs = {c.candidate.output_dir for c in normal_candidates}
assert Direction.W in pool_dirs and Direction.S in pool_dirs
```

### 9.3 L4 test

```python
selected = result.selected_placements[0]
assert selected.candidate_id == s_candidate.candidate_id
assert selected.output_dir == Direction.S  # via placement metadata or probed entry
assert effective_mining_gain(selected) == 9

rejected_w = find_overlap_rejection(rejected_candidate_id=w_candidate.candidate_id)
assert rejected_w.reason == RimPlacementRejectReason.PHYSICAL_OVERLAP
assert rejected_w.conflicting_candidate_id == s_candidate.candidate_id
assert rejected_w.conflicting_winner_output_dir == Direction.S.value
assert rejected_w.conflicting_winner_mining_cell_count == 9
assert rejected_w.winner_selected_due_to_higher_mining_gain is True
```

Use `candidate_id` / `output_dir` as identifiers — anchor alone is insufficient when W and S share the same rim anchor.

### 9.4 Regression — sort key

Unit test: two synthetic `RouteProbedBundleCandidate` entries, same anchor and rank, different `mining_occupied_cells` — assert sort order prefers higher `effective_mining_gain` regardless of `equivalence_key` lexicographic order.

### 9.5 PR-A tests

JS or Python contract test: overlay row with `kind=miner` does not resolve to `SpaceBelt_Forward`.

---

## §10 — References

- [`2026-05-28-layer-04-rim-bundle-placement-design.md`](2026-05-28-layer-04-rim-bundle-placement-design.md) — §3.4 superseded by this spec §3  
- [`django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/select.py`](../../../django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/select.py) — current greedy implementation  
- [`django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/rim_anchors.py`](../../../django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/rim_anchors.py) — direction enumeration (unchanged)

---

## Approval log

| Decision | Status |
|----------|--------|
| L4 approach B (mining-first greedy) | **APPROVED** |
| MWIS (C) | **Promoted** → [`2026-05-31-layer-04-v2-component-packing-optimizer-design.md`](2026-05-31-layer-04-v2-component-packing-optimizer-design.md) (component-local, \|C\|≤20) |
| PR-A / PR-B split | **APPROVED** |
| `route_cost` ASC (not `-route_cost`) | **APPROVED** (blocking amendment 1) |
| `effective_mining_gain` naming | **APPROVED** (blocking amendment 2) |
| Overlap rejection metadata | **APPROVED** (blocking amendment 3) |
| Separate PR-A / PR-B plan files | **APPROVED** (blocking amendment 1) |
| `connector_goal_distance` via transport entry coord | **APPROVED** (blocking amendment 2) |
| L4 input = SUCCEEDED only; no failed in sort | **APPROVED** (blocking amendment 3) |
| `conflicting_winner_candidate_id` + alias policy | **APPROVED** (blocking amendment 4) |
| `overlap_tiebreak_step` optional | **Recommended** (non-blocking A) |
| L4 asserts by `candidate_id` not anchor alone | **APPROVED** (non-blocking B) |
