# Outer-Rim Direction Arbitration — Implementation Plan (PR-B / P1–P3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** L4 greedy selection prefers higher `effective_mining_gain` so corner W/S overlap keeps the S candidate (gain 9) over W (gain 6); L3 preserves both in pool.

**Architecture:** Add `effective_mining_gain` + L4 sort helpers in `select.py`; filter non-`SUCCEEDED` probes before sort; enrich `RimPlacementRejection` metadata; corner fixture + regression tests. P1/P2 observability optional metrics on L3 wire. **No MWIS.**

**Tech Stack:** Python 3.12+ / Django `asteroid_lab` layers · pytest · ruff · mypy (`django_apps`)

**Spec:** [`2026-05-30-outer-rim-direction-arbitration-design.md`](../specs/2026-05-30-outer-rim-direction-arbitration-design.md) (APPROVED)

**Related (do not implement here):** [`2026-05-30-l4-replay-sprite-cell-kind-fallback.md`](2026-05-30-l4-replay-sprite-cell-kind-fallback.md) (PR-A)

---

## Execution contract

```text
Commit: ONLY when the user explicitly requests git commit.
```

- [ ] **Checkpoint** — Record files + pytest/ruff/mypy; no commit unless user asks.

---

## Acceptance (must all pass)

```text
L3 keeps both W and S feasible candidates (integration or expand on corner fixture).
L4 selects S when S effective_mining_gain=9 and W gain=6 on overlapping footprints.
W rejection reason remains PHYSICAL_OVERLAP.
W rejection metadata points to S winner (conflicting_candidate_id, mining counts).
equivalence_key is not in L4 sort key.
connector_goal_distance uses route_probe_start_coord → goal_coord (not raw anchor+delta).
route_probe_status != SUCCEEDED never enters overlap sort.
```

---

## File map

| File | Responsibility |
|------|----------------|
| `layers/layer_04_rim_bundle_placement/select.py` | Mining-first sort, pre-filter, rejection metadata |
| `layers/layer_04_rim_bundle_placement/sort_keys.py` | **New** — `effective_mining_gain`, `connector_goal_distance`, sort tuple |
| `layers/contracts/rim_placement.py` | Extend `RimPlacementRejection` fields |
| `layers/contracts/candidates.py` | Optional `effective_mining_gain` property on `BundleCandidate` |
| `tests/unit/asteroid_lab/layers/fixtures/layer_03_corner_ws_overlap.py` | **New** — corner map + W/S probe builders |
| `tests/unit/asteroid_lab/layers/test_layer_04_mining_first_selection.py` | **New** — P3 core tests |
| `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py` | Update overlap test for mining-first |
| `tests/unit/asteroid_lab/layers/test_layer_03_corner_ws_pool.py` | **New** — L3 pool retention (optional P1) |
| `docs/superpowers/specs/2026-05-28-layer-04-rim-bundle-placement-design.md` | Add amendment pointer §3.4 superseded |

---

### Task 1: `effective_mining_gain` helper (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/sort_keys.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_04_sort_keys.py`

- [ ] **Step 1: Failing test**

```python
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.sort_keys import (
    effective_mining_gain,
)
from django_apps.asteroid_lab.layers.contracts.candidates import make_bundle_candidate_for_test


def test_effective_mining_gain_equals_mining_cell_count_v1() -> None:
    cells = frozenset({(1, 1), (2, 1), (3, 1)})
    c = make_bundle_candidate_for_test(mining_occupied_cells=cells)
    assert effective_mining_gain(c) == 3
```

- [ ] **Step 2: Run — FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_sort_keys.py::test_effective_mining_gain_equals_mining_cell_count_v1 -v
```

- [ ] **Step 3: Implement**

```python
def effective_mining_gain(candidate: BundleCandidate) -> int:
    return len(candidate.mining_occupied_cells)
```

- [ ] **Step 4: Run — PASS**

---

### Task 2: `connector_goal_distance` helper (TDD)

**Files:**
- Modify: `sort_keys.py`
- Modify: `test_layer_04_sort_keys.py`

- [ ] **Step 5: Failing test**

```python
from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import (
    RouteProbeResult,
    RouteProbedBundleCandidate,
    RouteProbeStatus,
    make_bundle_candidate_for_test,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.sort_keys import (
    connector_goal_distance,
)


def test_connector_goal_distance_uses_probe_start_not_raw_anchor_delta() -> None:
    candidate = make_bundle_candidate_for_test(
        anchor_coord=(5, 5),
        output_dir=Direction.W,
        route_probe_start_coord=(4, 5),
    )
    entry = RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=True,
            goal_coord=(0, 5),
            path_coords=((4, 5), (0, 5)),
            steps_expanded=2,
            transport_kind=candidate.transport_kind,
            route_cost=4,
        ),
        route_goal_id="g0",
        reject_reason=None,
    )
    assert connector_goal_distance(entry) == 4  # |4-0| + |5-5|
```

- [ ] **Step 6: Implement**

```python
def connector_goal_distance(entry: RouteProbedBundleCandidate) -> float:
    result = entry.route_probe_result
    if result is None or result.goal_coord is None:
        return float("inf")
    start = entry.candidate.route_probe_start_coord
    gx, gy = result.goal_coord
    return abs(start[0] - gx) + abs(start[1] - gy)
```

**Forbidden:** `(anchor[0] + dx, anchor[1] + dy)` without `derive_transport_entry_coord` when start coord missing — if `route_probe_start_coord` absent, fall back to `derive_transport_entry_coord(anchor, output_dir)`.

- [ ] **Step 7: Run sort_keys tests — PASS**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_sort_keys.py -v
```

---

### Task 3: Mining-first sort order (TDD)

**Files:**
- Modify: `select.py` — replace `_candidate_sort_key`
- Modify: `test_layer_04_sort_keys.py`

- [ ] **Step 8: Failing test — equivalence_key must not decide**

```python
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select import (
    _candidate_sort_key,
)
from django_apps.asteroid_lab.genetic_sample.enums import Direction
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_sort_prefers_higher_mining_gain_over_equivalence_key_lex_order() -> None:
    low_key = succeeded_probe_at(
        (7, 3),
        equivalence_key="zzz",
        mining=frozenset({(7, 3), (6, 3), (5, 3)}),
        output_dir=Direction.W,
    )
    high_key = succeeded_probe_at(
        (7, 3),
        equivalence_key="aaa",
        mining=frozenset({(7, 3), (6, 3), (5, 3), (7, 4), (7, 5), (6, 4)}),
        output_dir=Direction.S,
    )
    assert _candidate_sort_key(low_key) > _candidate_sort_key(high_key)
```

Extend `succeeded_probe_at` in `layer_04_placement_helpers.py` to accept `output_dir: Direction = Direction.E` and pass through to `make_bundle_candidate_for_test`.

- [ ] **Step 9: Implement `_candidate_sort_key`**

```python
_OUTPUT_DIR_ORDER = {Direction.N: 0, Direction.E: 1, Direction.S: 2, Direction.W: 3}

def _candidate_sort_key(entry: RouteProbedBundleCandidate) -> tuple:
    c = entry.candidate
    rc = entry.route_probe_result.route_cost if entry.route_probe_result else float("inf")
    return (
        -effective_mining_gain(c),
        rc,
        c.intrinsic_priority_rank,
        c.anchor_coord[1],
        c.anchor_coord[0],
        connector_goal_distance(entry),
        _OUTPUT_DIR_ORDER[c.output_dir],
        c.candidate_id,
    )
```

**Do not include `equivalence_key`.**

- [ ] **Step 10: Run tests — PASS**

---

### Task 4: Pre-filter non-SUCCEEDED before sort

**Files:**
- Modify: `select.py`
- Modify: `test_layer_04_rim_placement.py`

- [ ] **Step 11: Failing test**

```python
from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbeStatus
# build failed probe entry; assert not in selected; assert NON_SUCCEEDED_PROBE rejection
```

- [ ] **Step 12: At start of `select_non_overlapping_candidates`:**

```python
succeeded = tuple(e for e in normal_candidates if e.route_probe_status == RouteProbeStatus.SUCCEEDED)
failed = tuple(e for e in normal_candidates if e.route_probe_status != RouteProbeStatus.SUCCEEDED)
# append failed to rejected with NON_SUCCEEDED_PROBE before greedy loop on succeeded
ordered = tuple(sorted(succeeded, key=_candidate_sort_key))
```

- [ ] **Step 13: Run layer_04 tests**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py -v
```

Update `test_select_rejects_lower_priority_on_physical_overlap`: give **high** more mining cells than **low** (not only lower `intrinsic_priority_rank`), or invert ranks so mining-first semantics are what the test documents.

---

### Task 5: `RimPlacementRejection` metadata (TDD)

**Files:**
- Modify: `layers/contracts/rim_placement.py`
- Modify: `select.py` — populate on `PHYSICAL_OVERLAP`
- Modify: `test_layer_04_mining_first_selection.py`

- [ ] **Step 14: Extend dataclass**

Add fields per spec §4: `rejected_candidate_id`, `rejected_output_dir`, `rejected_mining_cell_count`, `conflicting_winner_candidate_id`, `conflicting_winner_output_dir`, `conflicting_winner_mining_cell_count`, `winner_selected_due_to_higher_mining_gain`, optional `overlap_tiebreak_step`.

`conflicting_winner_candidate_id` MUST mirror `conflicting_candidate_id`.

- [ ] **Step 15: On overlap reject, fill from winner entry**

```python
winner_gain = effective_mining_gain(winner.candidate)
loser_gain = effective_mining_gain(entry.candidate)
winner_selected_due_to_higher_mining_gain = winner_gain > loser_gain
```

- [ ] **Step 16: Run tests**

---

### Task 6: Corner W/S fixture + P3 acceptance test

**Files:**
- Create: `tests/unit/asteroid_lab/layers/fixtures/layer_03_corner_ws_overlap.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_04_mining_first_selection.py`

- [ ] **Step 17: Fixture builders**

Provide:

```python
def corner_ws_w_probe() -> RouteProbedBundleCandidate: ...  # gain 6, Direction.W
def corner_ws_s_probe() -> RouteProbedBundleCandidate: ...  # gain 9, Direction.S
# shared anchor (7, 3); mining sets overlap; both SUCCEEDED; route_cost optional tie
```

Use explicit `mining_occupied_cells` frozensets (6 vs 9 cells) — no full map required for L4 unit test.

- [ ] **Step 18: Core acceptance test**

```python
def test_l4_selects_higher_gain_s_over_w_on_overlap() -> None:
    w = corner_ws_w_probe()
    s = corner_ws_s_probe()
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    selected, rejected = select_non_overlapping_candidates(
        normal_candidates=(w, s),  # deliberate W-first input order
        budget_ctx=ctx,
    )
    assert len(selected) == 1
    assert selected[0].candidate.candidate_id == s.candidate.candidate_id
    assert selected[0].candidate.output_dir == Direction.S
    rej = rejected[0]
    assert rej.reason == RimPlacementRejectReason.PHYSICAL_OVERLAP
    assert rej.rejected_candidate_id == w.candidate.candidate_id
    assert rej.conflicting_candidate_id == s.candidate.candidate_id
    assert rej.winner_selected_due_to_higher_mining_gain is True
```

- [ ] **Step 19: Run**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_mining_first_selection.py -v
```

---

### Task 7: L3 pool retention (P1 / integration)

**Files:**
- Create: `tests/unit/asteroid_lab/layers/test_layer_03_corner_ws_pool.py`
- Use: `layer_03_corner_ws_overlap.py` with `ReconstructionCompleteMap` + `expand_rim_bundle_candidates` when map ready

- [ ] **Step 20: Integration test (skip if fixture map not yet built)**

```python
result = expand_rim_bundle_candidates(...)
dirs = {e.candidate.output_dir for e in result.normal_candidates}
assert Direction.W in dirs and Direction.S in dirs
```

If full map is too heavy for v1, document skip and rely on Task 6 for P3; still add L3 metrics wire in Task 8.

---

### Task 8: L3 observability metrics (P1 — output only)

**Files:**
- Modify: `layers/contracts/layer03_observability.py` (or wire builder)
- Modify: pool summary JSON in replay assembler if already listing candidates

- [ ] **Step 21:** Add per-candidate preview fields: `effective_mining_gain`, `output_dir`, `route_cost`, `connector_goal_distance` on observability wire (not solver input).

---

### Task 9: Parent spec amendment note

**Files:**
- Modify: `docs/superpowers/specs/2026-05-28-layer-04-rim-bundle-placement-design.md`

- [ ] **Step 22:** At §3.4 add:

```markdown
> **Superseded (2026-05-30):** Sort key replaced by
> [`2026-05-30-outer-rim-direction-arbitration-design.md`](2026-05-30-outer-rim-direction-arbitration-design.md) §3.
```

---

### Task 10: Full verification gate

- [ ] **Step 23:**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_sort_keys.py tests/unit/asteroid_lab/layers/test_layer_04_mining_first_selection.py tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py -v
python -m ruff check django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement django_apps/asteroid_lab/layers/contracts/rim_placement.py
python -m mypy django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement django_apps/asteroid_lab/layers/contracts/rim_placement.py
```

---

## MWIS escalation (do not implement)

Per spec §8 — only if Task 6 passes but production maps still fail.

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| §3.1 effective_mining_gain | Task 1 |
| §3.2 SUCCEEDED-only input | Task 4 |
| §3.3 sort key (no equivalence_key) | Task 3 |
| §3.4 connector_goal_distance via entry coord | Task 2 |
| §4 rejection metadata | Task 5 |
| §9 corner W/S fixture | Task 6–7 |
| PR-B separate from PR-A | Separate plan ✓ |
