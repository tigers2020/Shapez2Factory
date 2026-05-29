# Layer 04 Rim Bundle Placement (PR-3c) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `layer_04_rim_bundle_placement` to convert L3 `normal_candidates` into deterministic `PROVISIONAL_PLACED` selections, a `ProvisionalLayoutOverlay`, and replay frames—without mutating `ReconstructionCompleteMap`—and rewire the stack to L3→L4→L5→L6.

**Architecture:** Shared contracts (`PlacementCommitState`, `ProvisionalLayoutOverlay`, `Layer04RimPlacementResult`) live under `layers/contracts/`. L4 logic splits `select.py` (ordering + greedy non-overlap), `place.py` (L3→`RimBundlePlacement` + overlay build), `replay.py` (`ReplayFrameAppendDTO` emission), `run.py` (orchestration). Rename existing inner-fill and commit packages to L5/L6; extend `stack_runner` to `run_layers_02_to_06` with explicit kwargs between layers.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy `django_apps config src`, frozen dataclasses, `StrEnum`

**Spec:** [`2026-05-28-layer-04-rim-bundle-placement-design.md`](../specs/2026-05-28-layer-04-rim-bundle-placement-design.md)  
**Depends on:** PR-3a + PR-3b merged (`RimBundleCandidateSet`, L3 expand, stack L2→L3 wire)

**Work classification:** contract change · implementation change

**Branch:** `feat/layer-04-rim-placement-replay-pr3c`

**Commit:** only when the user explicitly requests git commit.

**Architect review patches (2026-05-28):** Applied before execution — uppercase `RimPlacementRejectReason` values; `Layer04RimPlacementResult` factory-only in production; `MappingProxyType` for `by_cell`; `SNAPSHOT_EVENT_TYPES` = full replay allowlist; no `exterior_plan=object()` in tests; guard tests for `PROVISIONAL_PLACED`-only and stack complete_map identity.

---

## Out of scope (PR-3c)

```text
- L5 inner pattern fill generator (stub signature only)
- L6 commit / route commit / validation logic
- Modifying Layer 03 tests or probe/dedupe behavior
- xfail/skip to green
- UI color/CSS for provisional overlay
- DB persistence of replay frames from stack_runner
```

---

## File map

| Action | Path |
|--------|------|
| Create | `django_apps/asteroid_lab/layers/contracts/placement_state.py` |
| Create | `django_apps/asteroid_lab/layers/contracts/provisional_overlay.py` |
| Create | `django_apps/asteroid_lab/layers/contracts/rim_placement.py` |
| Create | `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/__init__.py` |
| Create | `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/select.py` |
| Create | `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/place.py` |
| Create | `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/replay.py` |
| Create | `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/run.py` |
| Rename | `layer_04_inner_pattern_fill/` → `layer_05_inner_pattern_fill/` |
| Rename | `layer_05_commit_validate/` → `layer_06_commit_validate/` |
| Modify | `django_apps/asteroid_lab/layers/contracts/layer_slugs.py` |
| Modify | `django_apps/asteroid_lab/layers/contracts/__init__.py` |
| Modify | `django_apps/asteroid_lab/layers/stack_runner.py` |
| Modify | `django_apps/asteroid_lab/layers/__init__.py` |
| Modify | `django_apps/asteroid_lab/replay/event_types.py` |
| Modify | `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` |
| Modify | `django_apps/asteroid_lab/services/solver_run_lab_summary.py` |
| Create | `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py` |
| Create | `tests/unit/asteroid_lab/layers/fixtures/layer_04_placement_helpers.py` |
| Modify | `tests/unit/asteroid_lab/layers/test_stack_runner_budget_interruption.py` |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py` |
| Modify | `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` |
| Patch | `docs/superpowers/specs/2026-05-27-asteroid-lab-algorithm-layer-stack-design.md` (layer table §1) |

---

## Execution order

```text
1. Task 1–3: shared contracts + tests
2. Task 4–7: L4 select/place/replay/run + unit tests
3. Task 8: layer renumber (L5/L6 packages + slugs)
4. Task 9: stack_runner + post-summary + downstream imports
5. Task 10: PR-3c gate (pytest narrow → ruff → mypy)
```

---

### Task 1: `PlacementCommitState` shared enum

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/placement_state.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py`

- [ ] **Step 1: Write the failing test**

```python
def test_placement_commit_state_provisional_value() -> None:
    from django_apps.asteroid_lab.layers.contracts.placement_state import (
        PlacementCommitState,
    )

    assert PlacementCommitState.PROVISIONAL_PLACED.value == "PROVISIONAL_PLACED"
    assert PlacementCommitState.ROUTED_CONFIRMED.value == "ROUTED_CONFIRMED"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py::test_placement_commit_state_provisional_value -v`  
Expected: FAIL — `ModuleNotFoundError` or import error

- [ ] **Step 3: Write minimal implementation**

```python
"""Placement commit lifecycle states (L4–L6)."""

from __future__ import annotations

from enum import StrEnum


class PlacementCommitState(StrEnum):
    PROVISIONAL_PLACED = "PROVISIONAL_PLACED"
    ROUTED_CONFIRMED = "ROUTED_CONFIRMED"
    QUARANTINED_UNROUTED = "QUARANTINED_UNROUTED"
    ROLLED_BACK = "ROLLED_BACK"


__all__ = ["PlacementCommitState"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py::test_placement_commit_state_provisional_value -v`  
Expected: PASS

- [ ] **Step 5: Commit** (user request only)

```bash
git add django_apps/asteroid_lab/layers/contracts/placement_state.py tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py
git commit -m "feat(asteroid_lab): add PlacementCommitState contract"
```

---

### Task 2: `ProvisionalLayoutOverlay` + `empty()`

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/provisional_overlay.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py`

- [ ] **Step 1: Write the failing test**

```python
def test_provisional_overlay_empty() -> None:
    from django_apps.asteroid_lab.layers.contracts.placement_state import (
        PlacementCommitState,
    )
    from django_apps.asteroid_lab.layers.contracts.provisional_overlay import (
        ProvisionalLayoutOverlay,
    )

    overlay = ProvisionalLayoutOverlay.empty()
    assert overlay.occupied_cells == frozenset()
    assert dict(overlay.by_cell) == {}
    assert overlay.source_layer == "layer_04_rim_bundle_placement"


def test_provisional_overlay_post_init_rejects_by_cell_mismatch() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import BundleCellRole
    from django_apps.asteroid_lab.layers.contracts.placement_state import (
        PlacementCommitState,
    )
    from django_apps.asteroid_lab.layers.contracts.provisional_overlay import (
        ProvisionalLayoutOverlay,
        ProvisionalPlacedCell,
    )
    from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind

    coord = (3, 4)
    cell = ProvisionalPlacedCell(
        coord=coord,
        candidate_id="c1",
        placement_id="c1:prov",
        role=BundleCellRole.MINER,
        transport_kind=TransportKind.SHAPE_BELT,
        placement_state=PlacementCommitState.PROVISIONAL_PLACED,
    )
    with pytest.raises(ValueError, match="by_cell keys must equal occupied_cells"):
        ProvisionalLayoutOverlay(
            occupied_cells=frozenset(),
            extractor_cells=frozenset({coord}),
            extension_cells=frozenset(),
            transport_stub_cells=frozenset(),
            by_cell={coord: cell},
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py -k provisional_overlay -v`  
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
"""Ephemeral provisional occupancy overlay (L4 output; L5/L6 input)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from django_apps.asteroid_lab.layers.contracts.candidates import BundleCellRole
from django_apps.asteroid_lab.layers.contracts.placement_state import PlacementCommitState
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

LAYER_04_SOURCE = "layer_04_rim_bundle_placement"


@dataclass(frozen=True, slots=True)
class ProvisionalPlacedCell:
    coord: Coord
    candidate_id: str
    placement_id: str
    role: BundleCellRole
    transport_kind: TransportKind
    placement_state: PlacementCommitState


@dataclass(frozen=True, slots=True)
class ProvisionalLayoutOverlay:
    occupied_cells: frozenset[Coord]
    extractor_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    transport_stub_cells: frozenset[Coord]
    by_cell: Mapping[Coord, ProvisionalPlacedCell]
    source_layer: str = LAYER_04_SOURCE

    def __post_init__(self) -> None:
        if frozenset(self.by_cell.keys()) != self.occupied_cells:
            msg = "by_cell keys must equal occupied_cells"
            raise ValueError(msg)
        object.__setattr__(self, "by_cell", MappingProxyType(dict(self.by_cell)))

    @classmethod
    def empty(cls) -> ProvisionalLayoutOverlay:
        return cls(
            occupied_cells=frozenset(),
            extractor_cells=frozenset(),
            extension_cells=frozenset(),
            transport_stub_cells=frozenset(),
            by_cell=MappingProxyType({}),
        )


__all__ = [
    "LAYER_04_SOURCE",
    "ProvisionalLayoutOverlay",
    "ProvisionalPlacedCell",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py -k provisional_overlay -v`  
Expected: PASS

- [ ] **Step 5: Commit** (user request only)

---

### Task 3: `rim_placement` contracts + test helpers fixture

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/rim_placement.py`
- Create: `tests/unit/asteroid_lab/layers/fixtures/layer_04_placement_helpers.py`
- Modify: `django_apps/asteroid_lab/layers/contracts/__init__.py` (exports)
- Test: `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py`

- [ ] **Step 1: Write fixture helper** (`layer_04_placement_helpers.py`)

```python
"""Test helpers for Layer 04 placement (not algorithm input)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
    make_bundle_candidate_for_test,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind


def succeeded_probe_at(
    anchor: tuple[int, int],
    *,
    rank: int = 1,
    gene_key: str = "miner_seed_m3e_01",
    equivalence_key: str = "equiv_a",
    mining: frozenset[tuple[int, int]] | None = None,
    transport: frozenset[tuple[int, int]] | None = None,
    goal: tuple[int, int] = (8, 4),
) -> RouteProbedBundleCandidate:
    stub_start = (anchor[0] + 1, anchor[1]) if transport is None else min(transport)
    candidate = make_bundle_candidate_for_test(
        gene_key=gene_key,
        intrinsic_priority_rank=rank,
        anchor_coord=anchor,
        equivalence_key=equivalence_key,
        mining_occupied_cells=mining or frozenset({anchor}),
        transport_stub_cells=transport or frozenset({stub_start}),
        route_probe_start_coord=stub_start,
    )
    path = (stub_start, goal)
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=True,
            goal_coord=goal,
            path_coords=path,
            steps_expanded=len(path),
            transport_kind=TransportKind.SHAPE_BELT,
        ),
        route_goal_id="ext_conn_00",
        reject_reason=None,
    )
```

- [ ] **Step 2: Write failing test for `Layer04RimPlacementResult` invariants**

```python
def test_layer04_result_selected_count_matches_placements() -> None:
    from django_apps.asteroid_lab.layers.contracts.provisional_overlay import (
        ProvisionalLayoutOverlay,
    )
    from django_apps.asteroid_lab.layers.contracts.rim_placement import (
        Layer04RimPlacementResult,
    )

    overlay = ProvisionalLayoutOverlay.empty()
    with pytest.raises(ValueError, match="selected_count"):
        Layer04RimPlacementResult(
            selected_placements=(),
            rejected_candidates=(),
            selected_count=1,
            rejected_overlap_count=0,
            rejected_budget_count=0,
            provisional_overlay=overlay,
            replay_frames=(),
        )


def test_build_layer04_rim_placement_result_sets_counts() -> None:
    from django_apps.asteroid_lab.layers.contracts.provisional_overlay import (
        ProvisionalLayoutOverlay,
    )
    from django_apps.asteroid_lab.layers.contracts.rim_placement import (
        build_layer04_rim_placement_result,
    )

    overlay = ProvisionalLayoutOverlay.empty()
    result = build_layer04_rim_placement_result(
        selected_placements=(),
        rejected_candidates=(),
        provisional_overlay=overlay,
        replay_frames=(),
    )
    assert result.selected_count == 0
    assert result.rejected_overlap_count == 0
    assert result.rejected_budget_count == 0
```

- [ ] **Step 3: Implement `rim_placement.py`**

Include: `RimPlacementRejectReason`, `RimBundlePlacement`, `RimPlacementRejection`, `Layer04RimPlacementResult`, `build_layer04_rim_placement_result`.

Enum values (uppercase, aligned with `PlacementCommitState`):

```python
class RimPlacementRejectReason(StrEnum):
    PHYSICAL_OVERLAP = "PHYSICAL_OVERLAP"
    BUDGET_INTERRUPTED = "BUDGET_INTERRUPTED"
    NON_SUCCEEDED_PROBE = "NON_SUCCEEDED_PROBE"
```

`Layer04RimPlacementResult.__post_init__`: validate counts; **`run.py` and stack_runner MUST call `build_layer04_rim_placement_result` only** (not bare constructor).

`RimBundlePlacement.__post_init__`: require `placement_state == PlacementCommitState.PROVISIONAL_PLACED`.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py -k layer04_result -v`  
Expected: PASS

---

### Task 4: Deterministic selection (`select.py`)

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/select.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py`

- [ ] **Step 1: Write failing overlap test**

```python
def test_select_rejects_lower_priority_on_physical_overlap() -> None:
    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select import (
        select_non_overlapping_candidates,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
        succeeded_probe_at,
    )

    high = succeeded_probe_at((3, 4), rank=1, equivalence_key="eq_high")
    low = succeeded_probe_at(
        (3, 4), rank=9, equivalence_key="eq_low", gene_key="miner_seed_m1e_01"
    )
    # same occupied cells → overlap
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    selected, rejected = select_non_overlapping_candidates(
        normal_candidates=(low, high),  # unsorted input
        budget_ctx=ctx,
    )
    assert [e.candidate.candidate_id for e in selected] == [high.candidate.candidate_id]
    assert len(rejected) == 1
    from django_apps.asteroid_lab.layers.contracts.rim_placement import (
        RimPlacementRejectReason,
    )

    assert rejected[0].reason is RimPlacementRejectReason.PHYSICAL_OVERLAP
    assert rejected[0].reason.value == "PHYSICAL_OVERLAP"
    assert rejected[0].conflicting_candidate_id == high.candidate.candidate_id


def test_select_does_not_dedupe_equivalence_when_cells_disjoint() -> None:
    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select import (
        select_non_overlapping_candidates,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
        succeeded_probe_at,
    )

    a = succeeded_probe_at((3, 4), rank=1, equivalence_key="same_eq")
    b = succeeded_probe_at(
        (10, 4),
        rank=2,
        equivalence_key="same_eq",
        mining=frozenset({(10, 4)}),
        transport=frozenset({(11, 4)}),
    )
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    selected, rejected = select_non_overlapping_candidates(
        normal_candidates=(a, b),
        budget_ctx=ctx,
    )
    assert len(selected) == 2
    assert rejected == ()
```

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Implement `select.py`**

```python
def _candidate_sort_key(entry: RouteProbedBundleCandidate) -> tuple:
    c = entry.candidate
    y, x = c.anchor_coord[1], c.anchor_coord[0]
    return (c.intrinsic_priority_rank, y, x, c.equivalence_key, c.candidate_id)


def select_non_overlapping_candidates(
    *,
    normal_candidates: tuple[RouteProbedBundleCandidate, ...],
    budget_ctx: LayerBudgetContext,
) -> tuple[tuple[RouteProbedBundleCandidate, ...], tuple[RimPlacementRejection, ...]]:
    ordered = tuple(sorted(normal_candidates, key=_candidate_sort_key))
    selected: list[RouteProbedBundleCandidate] = []
    rejected: list[RimPlacementRejection] = []
    occupied: set[Coord] = set()
    for entry in ordered:
        if budget_ctx.remaining_budget_ms() <= 0:
            rejected.append(
                RimPlacementRejection(
                    candidate_id=entry.candidate.candidate_id,
                    equivalence_key=entry.candidate.equivalence_key,
                    reason=RimPlacementRejectReason.BUDGET_INTERRUPTED,
                )
            )
            continue
        cells = entry.candidate.mining_occupied_cells | entry.candidate.transport_stub_cells
        conflict = cells & frozenset(occupied)
        if conflict:
            winner_id = selected[-1].candidate.candidate_id if selected else None
            # find actual conflicting selected candidate
            ...
            rejected.append(
                RimPlacementRejection(
                    candidate_id=entry.candidate.candidate_id,
                    equivalence_key=entry.candidate.equivalence_key,
                    reason=RimPlacementRejectReason.PHYSICAL_OVERLAP,
                    conflicting_candidate_id=conflicting_id,
                    conflicting_cells=conflict,
                )
            )
            continue
        selected.append(entry)
        occupied |= set(cells)
    return tuple(selected), tuple(rejected)
```

Resolve `conflicting_candidate_id` by scanning `selected` for first entry whose occupied intersects (not only last).

- [ ] **Step 4: Run overlap + dedupe tests — PASS**

---

### Task 5: Placement + overlay build (`place.py`)

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/place.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py`

- [ ] **Step 1: Write failing test**

```python
def test_build_placement_provisional_state_only() -> None:
    from django_apps.asteroid_lab.layers.contracts.placement_state import (
        PlacementCommitState,
    )
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.place import (
        build_rim_bundle_placement,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
        succeeded_probe_at,
    )

    entry = succeeded_probe_at((3, 4))
    placement = build_rim_bundle_placement(entry)
    assert placement.placement_state is PlacementCommitState.PROVISIONAL_PLACED
    assert placement.occupied_cells == (
        entry.candidate.mining_occupied_cells | entry.candidate.transport_stub_cells
    )
```

- [ ] **Step 2: Implement `place.py`**

Functions:
- `build_rim_bundle_placement(entry) -> RimBundlePlacement`
- `build_provisional_overlay(placements: tuple[RimBundlePlacement, ...]) -> ProvisionalLayoutOverlay`

Map `BundlePlacement.cell_role` → extractor/extension/output_stub aggregates.

- [ ] **Step 3: Run test — PASS**

---

### Task 6: Replay event types + `replay.py`

**Files:**
- Modify: `django_apps/asteroid_lab/replay/event_types.py`
- Create: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/replay.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py`

- [ ] **Step 1: Add constants**

```python
EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN = "layer04_rim_placement_begin"
EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED = "layer04_rim_candidate_selected"
EVENT_TYPE_LAYER04_RIM_CANDIDATE_REJECTED_OVERLAP = "layer04_rim_candidate_rejected_overlap"
EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE = "layer04_rim_placement_complete"
```

Add all four to `SNAPSHOT_EVENT_TYPES`.

**Registry note:** `SNAPSHOT_EVENT_TYPES` in this repo is the **replay frame `event_type` allowlist** (not “full-map snapshot only”). Register all four Layer04 kinds including `layer04_rim_candidate_rejected_overlap` so `is_registered_event_type` / `assert_registered_event_type` accept overlap-rejection frames.

- [ ] **Step 2: Write failing replay test**

```python
def test_build_layer04_replay_frames_emits_begin_selected_complete() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN,
        EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE,
        is_registered_event_type,
    )
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.replay import (
        build_layer04_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
        succeeded_probe_at,
    )

    entry = succeeded_probe_at((3, 4))
    frames = build_layer04_replay_frames(
        selected=(build_rim_bundle_placement(entry),),
        rejected=(),
    )
    types = [f.frame_payload["event_type"] for f in frames]
    assert types[0] == EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN
    assert EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED in types
    assert types[-1] == EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE
    assert all(is_registered_event_type(t) for t in types)
    assert frames[1].frame_payload["placement_state"] == "PROVISIONAL_PLACED"
```

- [ ] **Step 3: Implement `replay.py`**

Return `tuple[ReplayFrameAppendDTO, ...]` with `frame_payload` containing spec metadata; `phase="layer_04_rim_bundle_placement"`.

- [ ] **Step 4: Run test — PASS**

---

### Task 7: `run_layer_04` orchestration + integration tests

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/run.py`
- Create: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/__init__.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py`

- [ ] **Step 1: Write failing tests**

```python
def test_run_layer04_does_not_mutate_complete_map() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        Layer03ExpansionMetrics,
        build_rim_bundle_candidate_set,
    )
    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.contracts.provisional_overlay import (
        LAYER_04_SOURCE,
    )
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
        run_layer_04_rim_bundle_placement,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        golden_5x5_complete_map,
        minimal_l2_plan_for_golden,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
        succeeded_probe_at,
    )

    complete = golden_5x5_complete_map()
    cells_before = dict(complete.cells)
    candidate_set = build_rim_bundle_candidate_set(
        normal_candidates=(succeeded_probe_at((6, 4)),),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics.empty(),
    )
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    result = run_layer_04_rim_bundle_placement(
        complete_map=complete,
        exterior_plan=minimal_l2_plan_for_golden(),
        candidate_set=candidate_set,
        budget_ctx=ctx,
    )
    assert complete.cells == cells_before
    assert result.selected_count == 1
    assert result.provisional_overlay.occupied_cells
    assert result.provisional_overlay.source_layer == LAYER_04_SOURCE


def test_layer04_never_outputs_routed_confirmed() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        Layer03ExpansionMetrics,
        build_rim_bundle_candidate_set,
    )
    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.contracts.placement_state import (
        PlacementCommitState,
    )
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
        run_layer_04_rim_bundle_placement,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        golden_5x5_complete_map,
        minimal_l2_plan_for_golden,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
        succeeded_probe_at,
    )

    candidate_set = build_rim_bundle_candidate_set(
        normal_candidates=(succeeded_probe_at((6, 4)),),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics.empty(),
    )
    result = run_layer_04_rim_bundle_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        candidate_set=candidate_set,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert all(
        p.placement_state is PlacementCommitState.PROVISIONAL_PLACED
        for p in result.selected_placements
    )
    assert PlacementCommitState.ROUTED_CONFIRMED not in {
        p.placement_state for p in result.selected_placements
    }


def test_run_layer04_hold_when_exterior_plan_none() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        Layer03ExpansionMetrics,
        build_rim_bundle_candidate_set,
    )
    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
        run_layer_04_rim_bundle_placement,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        golden_5x5_complete_map,
    )

    candidate_set = build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics.empty(),
    )
    result = run_layer_04_rim_bundle_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=None,
        candidate_set=candidate_set,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result.selected_count == 0
    assert result.provisional_overlay.occupied_cells == frozenset()


def test_run_layer04_empty_normal_candidates_yields_empty_selection() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        Layer03ExpansionMetrics,
        build_rim_bundle_candidate_set,
    )
    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
        run_layer_04_rim_bundle_placement,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        golden_5x5_complete_map,
        minimal_l2_plan_for_golden,
    )

    candidate_set = build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics.empty(),
    )
    result = run_layer_04_rim_bundle_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        candidate_set=candidate_set,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    assert result.selected_count == 0
```

`run_layer_04_rim_bundle_placement` early return when `exterior_plan is None` OR `not candidate_set.normal_candidates`.

- [ ] **Step 2: Implement `run.py`**

Wire: select → place → overlay → replay → `build_layer04_rim_placement_result`.

- [ ] **Step 3: Run full `test_layer_04_rim_placement.py`**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py -v`  
Expected: all PASS

---

### Task 8: Rename L4→L5 inner fill, L5→L6 commit

**Files:**
- Rename dirs (git mv):
  - `layer_04_inner_pattern_fill` → `layer_05_inner_pattern_fill`
  - `layer_05_commit_validate` → `layer_06_commit_validate`
- Update function names inside `run.py`:
  - `run_layer_04_inner_pattern_fill` → `run_layer_05_inner_pattern_fill`
  - `run_layer_05_commit_validate` → `run_layer_06_commit_validate`

- [ ] **Step 1: git mv packages**

```bash
git mv django_apps/asteroid_lab/layers/layer_04_inner_pattern_fill django_apps/asteroid_lab/layers/layer_05_inner_pattern_fill
git mv django_apps/asteroid_lab/layers/layer_05_commit_validate django_apps/asteroid_lab/layers/layer_06_commit_validate
```

- [ ] **Step 2: Update `layer_slugs.py`**

```python
LAYER_04_RIM_BUNDLE_PLACEMENT = "layer_04_rim_bundle_placement"
LAYER_05_INNER_PATTERN_FILL = "layer_05_inner_pattern_fill"
LAYER_06_COMMIT_VALIDATE = "layer_06_commit_validate"

LAYERS_02_TO_06: tuple[str, ...] = (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_MINING_BUNDLES,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_06_COMMIT_VALIDATE,
)
```

Remove old `LAYER_04_INNER_PATTERN_FILL` / `LAYER_05_COMMIT_VALIDATE` aliases unless a deprecated alias is required for external API (prefer clean break + update all imports).

- [ ] **Step 3: Update L5 stub signature** (`layer_05_inner_pattern_fill/run.py`)

```python
def run_layer_05_inner_pattern_fill(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    rim_placement_result: Layer04RimPlacementResult,
    provisional_overlay: ProvisionalLayoutOverlay,
    budget_ctx: LayerBudgetContext,
) -> None:
    _ = (complete_map, exterior_plan, rim_placement_result, provisional_overlay, budget_ctx)
```

- [ ] **Step 4: Verify imports**

Run: `python -m ruff check django_apps/asteroid_lab/layers/`  
Fix any stale import paths.

---

### Task 9: `stack_runner` L3→L4→L5→L6 + post-summary

**Files:**
- Modify: `django_apps/asteroid_lab/layers/stack_runner.py`
- Modify: `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py`
- Modify: `tests/unit/asteroid_lab/layers/test_stack_runner_budget_interruption.py`

- [ ] **Step 1: Write failing stack wiring test**

Add to `test_stack_runner_budget_interruption.py`:

```python
def test_stack_runner_passes_l3_result_to_l4_and_overlay_to_l5() -> None:
    from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
        LAYER_02_EXTERIOR_TRANSPORT,
        LAYER_03_RIM_MINING_BUNDLES,
        LAYER_04_RIM_BUNDLE_PLACEMENT,
        LAYER_05_INNER_PATTERN_FILL,
    )
    from django_apps.asteroid_lab.layers.stack_runner import _LayerStackRunner, run_layers_02_to_06

    l3_out = object()
    l4_out = object()
    captured_l4: dict[str, object] = {}
    captured_l5: dict[str, object] = {}

    def fake_l2(**_kwargs: object) -> object:
        return object()

    def fake_l3(**_kwargs: object) -> object:
        return l3_out

    def fake_l4(**kwargs: object) -> object:
        captured_l4.update(kwargs)
        return l4_out

    def fake_l5(**kwargs: object) -> None:
        captured_l5.update(kwargs)

    runners = (
        _LayerStackRunner(LAYER_02_EXTERIOR_TRANSPORT, fake_l2),
        _LayerStackRunner(LAYER_03_RIM_MINING_BUNDLES, fake_l3),
        _LayerStackRunner(LAYER_04_RIM_BUNDLE_PLACEMENT, fake_l4),
        _LayerStackRunner(LAYER_05_INNER_PATTERN_FILL, fake_l5),
    )
    ...
    assert captured_l4.get("candidate_set") is l3_out
    assert captured_l5.get("rim_placement_result") is l4_out
    assert captured_l5.get("provisional_overlay") is getattr(l4_out, "provisional_overlay", l4_out)
```

Use a real `Layer04RimPlacementResult` from `build_layer04_rim_placement_result` (empty) as `l4_out` so `provisional_overlay` is a real DTO.

- [ ] **Step 1b: Stack complete_map identity guard** (same file)

```python
def test_stack_runner_layer04_does_not_mutate_complete_map() -> None:
    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
        LAYER_02_EXTERIOR_TRANSPORT,
        LAYER_03_RIM_MINING_BUNDLES,
        LAYER_04_RIM_BUNDLE_PLACEMENT,
    )
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
        run_layer_04_rim_bundle_placement,
    )
    from django_apps.asteroid_lab.layers.stack_runner import _LayerStackRunner, run_layers_02_to_06
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        golden_5x5_complete_map,
        minimal_l2_plan_for_golden,
    )

    complete = golden_5x5_complete_map()
    cells_before = dict(complete.cells)

    def fake_l2(**_kwargs: object) -> object:
        return minimal_l2_plan_for_golden()

    def fake_l3(**kwargs: object) -> object:
        from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.run import (
            run_layer_03_rim_mining_bundles,
        )

        return run_layer_03_rim_mining_bundles(
            complete_map=kwargs["complete_map"],
            exterior_plan=kwargs["exterior_plan"],
            budget_ctx=kwargs["budget_ctx"],
        )

    runners = (
        _LayerStackRunner(LAYER_02_EXTERIOR_TRANSPORT, fake_l2),
        _LayerStackRunner(LAYER_03_RIM_MINING_BUNDLES, fake_l3),
        _LayerStackRunner(LAYER_04_RIM_BUNDLE_PLACEMENT, run_layer_04_rim_bundle_placement),
    )
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    run_layers_02_to_06(complete_map=complete, budget_ctx=ctx, runners=runners)
    assert complete.cells == cells_before
```

- [ ] **Step 2: Implement `stack_runner.py` changes**

- Rename `_Layer02To05Runner` → `_LayerStackRunner`
- Rename `run_layers_02_to_05` → `run_layers_02_to_06`
- Update `_LAYER_INDEX` for 6 layers (2–6)
- Loop body:

```python
last_exterior_plan: ExteriorConnectionPlan | None = None
last_candidate_set: RimBundleCandidateSet | None = None
last_placement_result: Layer04RimPlacementResult | None = None

elif entry.slug == LAYER_03_RIM_MINING_BUNDLES:
    last_candidate_set = entry.run(...)
elif entry.slug == LAYER_04_RIM_BUNDLE_PLACEMENT:
    last_placement_result = entry.run(
        complete_map=complete_map,
        exterior_plan=last_exterior_plan,
        candidate_set=last_candidate_set or empty_set,
        budget_ctx=budget_ctx,
    )
    post_metrics = build_layer04_post_summary_metrics(last_placement_result)
elif entry.slug == LAYER_05_INNER_PATTERN_FILL:
    entry.run(
        complete_map=complete_map,
        exterior_plan=last_exterior_plan,
        rim_placement_result=last_placement_result or empty_layer04,
        provisional_overlay=(last_placement_result.provisional_overlay if last_placement_result else ProvisionalLayoutOverlay.empty()),
        budget_ctx=budget_ctx,
    )
```

- Budget fail-closed: if budget zero before L5, L4 may have completed but L5/L6 must not run (existing loop semantics).

- [ ] **Step 3: Add `build_layer04_post_summary_metrics`**

```python
def build_layer04_post_summary_metrics(result: Layer04RimPlacementResult) -> dict[str, object]:
    return {
        "selected_count": result.selected_count,
        "rejected_overlap_count": result.rejected_overlap_count,
        "rejected_budget_count": result.rejected_budget_count,
        "overlay_occupied_cell_count": len(result.provisional_overlay.occupied_cells),
    }
```

- [ ] **Step 4: Update `layers/__init__.py` exports**

Export `run_layers_02_to_06`; optionally keep `run_layers_02_to_05` as deprecated wrapper calling `_06` for one release — **prefer direct rename** per file map.

- [ ] **Step 5: Run stack tests**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_stack_runner_budget_interruption.py -v`  
Expected: PASS

- [ ] **Step 6: Budget interruption does not call L5**

Extend existing budget test: when budget exhausted after L4 slug registered, assert `LAYER_05_INNER_PATTERN_FILL` not in `completed_layer_slugs`.

---

### Task 10: Downstream slug references + doc patch

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- Modify: `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`
- Modify: `tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py`
- Patch: `docs/superpowers/specs/2026-05-27-asteroid-lab-algorithm-layer-stack-design.md` §1 table

- [ ] **Step 1: Update lab summary layer list**

Insert L4 rim placement row; renumber inner fill → 5, commit → 6.

- [ ] **Step 2: Fix tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py -v`

- [ ] **Step 3: Patch parent stack design doc** (layer table + package tree only)

---

### Task 11: PR-3c validation gate

- [ ] **Step 1: Narrow pytest**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py tests/unit/asteroid_lab/layers/test_stack_runner_budget_interruption.py tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v
```

Expected: PASS

- [ ] **Step 2: ruff**

```bash
python -m ruff check django_apps/asteroid_lab/layers/ django_apps/asteroid_lab/replay/event_types.py tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py
```

Expected: PASS

- [ ] **Step 3: mypy**

```bash
python -m mypy django_apps/asteroid_lab/layers/contracts/placement_state.py django_apps/asteroid_lab/layers/contracts/provisional_overlay.py django_apps/asteroid_lab/layers/contracts/rim_placement.py django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement django_apps/asteroid_lab/layers/stack_runner.py
```

Expected: PASS

- [ ] **Step 4: Confirm Layer 03 tests untouched**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py tests/unit/asteroid_lab/layers/test_layer_03_route_goal_builder.py tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py -v
```

Expected: PASS (no edits to these files in PR-3c)

---

## Forbidden (agent checklist)

```text
Do not modify Layer 03 tests to make Layer 04 pass.
Do not relax Layer 03 route probe, dedupe, or hold assertions.
Do not mark failing tests xfail/skip.
Do not set placement_state to ROUTED_CONFIRMED in L4.
Do not mutate ReconstructionCompleteMap in L4.
Do not use free-form strings for RimPlacementRejection.reason (enum only).
If L3 expectations conflict with L4, stop and report contract conflict.
```

---

## Spec self-review (plan author)

| Check | Result |
|-------|--------|
| Option B overlay | Tasks 2, 5, 7 |
| No complete_map mutation | Task 7 test |
| Selection sort + overlap | Task 4 |
| No equivalence dedupe | Task 4 test |
| PROVISIONAL_PLACED only | Tasks 3, 5, 7 guard test |
| Replay event registration | Task 6 (all 4 in allowlist) |
| stack_runner L3→L4→L5 | Task 9 |
| complete_map identity in stack | Task 9 step 1b |
| Uppercase reject enum | Task 3, 4 |
| MappingProxyType by_cell | Task 2 |
| Factory-only L04 result in run | Task 3, 7 |
| L5/L6 rename | Task 8 |
| L3 tests untouched | Task 11 step 4 |
| Placeholder scan | No TBD steps |

---

## Acceptance checklist (PR-3c)

```text
[ ] layer_04_rim_bundle_placement package
[ ] PlacementCommitState shared enum
[ ] RimPlacementRejectReason enum
[ ] ProvisionalLayoutOverlay DTO
[ ] L3 normal_candidates → selected_placements
[ ] physical overlap reject deterministic
[ ] complete_map not mutated
[ ] replay event_types registered
[ ] stack_runner L3→L4→L5 wiring
[ ] layer_04_inner_pattern_fill → layer_05_inner_pattern_fill rename
[ ] layer_05_commit_validate → layer_06_commit_validate rename
[ ] build_layer04_post_summary_metrics
[ ] narrow pytest + ruff + mypy pass
[ ] Layer 03 tests unchanged
[ ] test_layer04_never_outputs_routed_confirmed
[ ] RimPlacementRejectReason uppercase values
[ ] ProvisionalLayoutOverlay.by_cell MappingProxyType
```

---

## Suggested commit message (when user requests)

```text
feat(asteroid_lab): add layer 04 rim placement replay materialization
```
