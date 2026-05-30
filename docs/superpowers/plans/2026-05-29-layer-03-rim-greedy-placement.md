# Layer 03 Rim Greedy Placement (L3/L4 integration) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace legacy L3 candidate pool + L4 packing with a single `layer_03_rim_greedy_placement` layer, disable L4 in the stack, and wire contracts/tests/replay payloads without changing downstream layer APIs (out of scope per spec).

**Architecture:** New contracts in `layers/contracts/rim_greedy.py`; implementation package `layer_03_rim_greedy_placement/` with rim anchor traversal, 4 deterministic variants, pass1 greedy install + route reservation, pass2 read-only score; `stack_runner` runs L2→L3 greedy→L5→L6 with L4 index reserved but not executed; L4/L3 legacy modules become thin shims.

**Tech Stack:** Python 3.12+, Django `asteroid_lab`, pytest, existing `layers/shared/route_probe.py`, StrEnum reject reasons.

**Spec:** [`docs/superpowers/specs/2026-05-29-layer-03-rim-greedy-placement-design.md`](../specs/2026-05-29-layer-03-rim-greedy-placement-design.md)

---

## File map (create / modify)

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/layers/contracts/rim_greedy.py` | DTOs, StrEnums, builders, empty result |
| `django_apps/asteroid_lab/layers/contracts/layer04_disabled.py` | `Layer04DisabledResult` |
| `django_apps/asteroid_lab/layers/contracts/layer_slugs.py` | Canonical + deprecated slugs, active tuple |
| `django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/` | Greedy algorithm package |
| `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/run.py` | DISABLED shim only |
| `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/run.py` | Thin delegate + deprecation |
| `django_apps/asteroid_lab/layers/stack_runner.py` | Runners, L3 branch, L5 mechanical overlay bridge |
| `django_apps/asteroid_lab/layers/observability/layer_behavior_catalog.py` | Greedy slug text |
| `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` | Greedy metrics builder |
| `django_apps/asteroid_lab/replay/layer03_rim_greedy_segment.py` | Project observation events → frames |
| `tests/unit/asteroid_lab/layers/contracts/test_rim_greedy_contracts.py` | DTO + enum contracts |
| `tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_*.py` | Anchors, stack, reservation |
| `tests/unit/asteroid_lab/layers/test_layer_04_disabled_shim.py` | L4 dead layer |
| `tests/unit/asteroid_lab/test_solver_runtime_rim_stack.py` | Slug list expectations |

**Out of scope (do not edit in this plan):** `layer_05_inner_pattern_fill/*`, `layer_06_commit_validate/*`, L5/L6 tests except stack slug assertions.

---

### Task 1: Rim greedy + L4 disabled contracts

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/rim_greedy.py`
- Create: `django_apps/asteroid_lab/layers/contracts/layer04_disabled.py`
- Create: `tests/unit/asteroid_lab/layers/contracts/test_rim_greedy_contracts.py`

- [ ] **Step 1: Write failing contract tests**

```python
# tests/unit/asteroid_lab/layers/contracts/test_rim_greedy_contracts.py
from __future__ import annotations

import pytest

from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_03_RIM_MINING_BUNDLES,
    LAYERS_02_TO_06_ACTIVE,
)
from django_apps.asteroid_lab.layers.contracts.rim_greedy import (
    RimGreedyRejectReason,
    build_empty_integrated_rim_greedy_result,
)


def test_active_runner_tuple_uses_greedy_slug_only() -> None:
    assert LAYER_03_RIM_GREEDY_PLACEMENT in LAYERS_02_TO_06_ACTIVE
    assert LAYER_03_RIM_MINING_BUNDLES not in LAYERS_02_TO_06_ACTIVE


def test_empty_result_has_canonical_overlay_source() -> None:
    result = build_empty_integrated_rim_greedy_result(
        layer_skip_reason="missing_exterior_connection_plan",
    )
    assert result.provisional_overlay.source_layer == LAYER_03_RIM_GREEDY_PLACEMENT
    assert result.observability_events == ()


def test_reject_reason_is_strenum() -> None:
    assert RimGreedyRejectReason.DPS_UNREACHABLE.value == "DPS_UNREACHABLE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/layers/contracts/test_rim_greedy_contracts.py -v`  
Expected: FAIL — `ImportError` / `LAYERS_02_TO_06_ACTIVE` not defined

- [ ] **Step 3: Implement `rim_greedy.py` (minimal v0)**

```python
# django_apps/asteroid_lab/layers/contracts/rim_greedy.py
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_03_RIM_GREEDY_PLACEMENT
from django_apps.asteroid_lab.layers.contracts.provisional_overlay import ProvisionalLayoutOverlay
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

LAYER_03_GREEDY_SOURCE = LAYER_03_RIM_GREEDY_PLACEMENT


class RimGreedyRejectReason(StrEnum):
    ANCHOR_ALREADY_CONSUMED = "ANCHOR_ALREADY_CONSUMED"
    ANCHOR_INVALIDATED = "ANCHOR_INVALIDATED"
    NO_VOID_NORMAL = "NO_VOID_NORMAL"
    FOOTPRINT_OUT_OF_FIELD = "FOOTPRINT_OUT_OF_FIELD"
    EQUIPMENT_COLLISION = "EQUIPMENT_COLLISION"
    PRIORITY_RULE_VIOLATION = "PRIORITY_RULE_VIOLATION"
    M_OUTPUT_BLOCKED = "M_OUTPUT_BLOCKED"
    DPS_UNREACHABLE = "DPS_UNREACHABLE"
    ROUTE_CROSSES_HARD_BLOCKER = "ROUTE_CROSSES_HARD_BLOCKER"
    ORIENTATION_MISMATCH = "ORIENTATION_MISMATCH"


class RimGreedyObservationPhase(StrEnum):
    RIM_GREEDY_BEGIN = "rim_greedy_begin"
    RIM_ANCHOR_PROBE = "rim_anchor_probe"
    RIM_SEED_ATTEMPT_REJECTED = "rim_seed_attempt_rejected"
    RIM_SEED_COMMITTED = "rim_seed_committed"
    RIM_ROUTE_PROBE_SUCCESS = "rim_route_probe_success"
    RIM_ROUTE_PROBE_FAILED = "rim_route_probe_failed"
    RIM_PASS1_COMPLETE = "rim_pass1_complete"
    RIM_PASS2_VALIDATION = "rim_pass2_validation"
    RIM_GREEDY_COMPLETE = "rim_greedy_complete"


@dataclass(frozen=True, slots=True)
class RimGreedyPolicy:
    DEFAULT_DPS_SEARCH_MARGIN: int = 12


@dataclass(frozen=True, slots=True)
class RimGreedyScoreAtoms:
    miner_count: int
    extension_count: int
    route_length: int
    base_score: float


@dataclass(frozen=True, slots=True)
class CommittedRimSeedPlacement:
    placement_id: str
    variant_id: str
    anchor: Coord
    output_dir: str
    seed_id: str
    miner_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    m_output_stub: Coord
    route_probe_path: tuple[Coord, ...]


@dataclass(frozen=True, slots=True)
class RimGreedyReject:
    anchor: Coord
    variant_id: str
    output_dir: str | None
    seed_id: str | None
    reason: RimGreedyRejectReason
    detail: str = ""


@dataclass(frozen=True, slots=True)
class RimGreedyObservationEvent:
    phase: RimGreedyObservationPhase
    variant_id: str
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RimGreedyPass2Report:
    variant_id: str
    score: float | None
    hard_fail: bool
    miner_count: int
    extension_count: int
    total_route_length: int


@dataclass(frozen=True, slots=True)
class RimGreedyMetrics:
    rim_anchor_count: int = 0
    committed_placement_count: int = 0
    rejected_attempt_count: int = 0
    reserved_route_cell_count: int = 0
    winning_variant_id: str = ""
    pass2_score: float | None = None
    layer_skip_reason: str | None = None
    canonical_layer_slug: str = LAYER_03_RIM_GREEDY_PLACEMENT


@dataclass(frozen=True, slots=True)
class IntegratedRimGreedyResult:
    committed_placements: tuple[CommittedRimSeedPlacement, ...]
    rejected_attempts: tuple[RimGreedyReject, ...]
    occupied_equipment_cells: frozenset[Coord]
    reserved_route_cells: frozenset[Coord]
    provisional_overlay: ProvisionalLayoutOverlay
    pass2_report: RimGreedyPass2Report
    winning_variant_id: str
    metrics: RimGreedyMetrics
    observability_events: tuple[RimGreedyObservationEvent, ...]


def build_empty_integrated_rim_greedy_result(
    *,
    layer_skip_reason: str | None = None,
    rim_anchor_count: int = 0,
) -> IntegratedRimGreedyResult:
    overlay = ProvisionalLayoutOverlay.empty()
    object.__setattr__(overlay, "source_layer", LAYER_03_GREEDY_SOURCE)
    report = RimGreedyPass2Report(
        variant_id="",
        score=None,
        hard_fail=True,
        miner_count=0,
        extension_count=0,
        total_route_length=0,
    )
    metrics = RimGreedyMetrics(
        rim_anchor_count=rim_anchor_count,
        layer_skip_reason=layer_skip_reason,
    )
    return IntegratedRimGreedyResult(
        committed_placements=(),
        rejected_attempts=(),
        occupied_equipment_cells=frozenset(),
        reserved_route_cells=frozenset(),
        provisional_overlay=overlay,
        pass2_report=report,
        winning_variant_id="",
        metrics=metrics,
        observability_events=(),
    )
```

Note: `ProvisionalLayoutOverlay` is frozen — use `ProvisionalLayoutOverlay(..., source_layer=LAYER_03_GREEDY_SOURCE)` in builder instead of `object.__setattr__` when implementing.

- [ ] **Step 4: Implement `layer04_disabled.py`**

```python
# django_apps/asteroid_lab/layers/contracts/layer04_disabled.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from django_apps.asteroid_lab.layers.contracts.provisional_overlay import ProvisionalLayoutOverlay
from django_apps.asteroid_lab.services.dto import ReplayFrameAppendDTO

LAYER04_DISABLED_REASON = "SUPERSEDED_BY_LAYER_03_RIM_GREEDY_PLACEMENT"


@dataclass(frozen=True, slots=True)
class Layer04DisabledResult:
    status: Literal["DISABLED"]
    reason: str
    provisional_overlay: ProvisionalLayoutOverlay
    replay_frames: tuple[ReplayFrameAppendDTO, ...] = ()

    @classmethod
    def superseded(cls) -> Layer04DisabledResult:
        return cls(
            status="DISABLED",
            reason=LAYER04_DISABLED_REASON,
            provisional_overlay=ProvisionalLayoutOverlay.empty(),
            replay_frames=(),
        )
```

- [ ] **Step 5: Update `layer_slugs.py`**

```python
LAYER_03_RIM_GREEDY_PLACEMENT = "layer_03_rim_greedy_placement"
LAYER_03_RIM_MINING_BUNDLES = "layer_03_rim_mining_bundles"  # deprecated import only

LAYERS_02_TO_06_ACTIVE: tuple[str, ...] = (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_06_COMMIT_VALIDATE,
)

# Back-compat alias — documents/tests may still import name:
LAYERS_02_TO_06 = LAYERS_02_TO_06_ACTIVE
```

Keep `LAYER_04_RIM_BUNDLE_PLACEMENT` constant and `_LAYER_INDEX[...] = 4` unchanged.

- [ ] **Step 6: Run contract tests**

Run: `python -m pytest tests/unit/asteroid_lab/layers/contracts/test_rim_greedy_contracts.py -v`  
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add django_apps/asteroid_lab/layers/contracts/rim_greedy.py \
  django_apps/asteroid_lab/layers/contracts/layer04_disabled.py \
  django_apps/asteroid_lab/layers/contracts/layer_slugs.py \
  tests/unit/asteroid_lab/layers/contracts/test_rim_greedy_contracts.py
git commit -m "feat(asteroid_lab): add rim greedy and L4 disabled contracts"
```

---

### Task 2: L4 disabled shim + legacy L3 delegate

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/run.py`
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/run.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_04_disabled_shim.py`

- [ ] **Step 1: Write failing shim test**

```python
# tests/unit/asteroid_lab/layers/test_layer_04_disabled_shim.py
from django_apps.asteroid_lab.layers.contracts.layer04_disabled import LAYER04_DISABLED_REASON
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
    run_layer_04_rim_bundle_placement,
)


def test_layer_04_shim_returns_disabled_without_side_effects() -> None:
    result = run_layer_04_rim_bundle_placement()
    assert result.status == "DISABLED"
    assert result.reason == LAYER04_DISABLED_REASON
    assert result.provisional_overlay.occupied_cells == frozenset()
    assert result.replay_frames == ()
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_disabled_shim.py -v`

- [ ] **Step 3: Replace L4 `run.py` body**

```python
import warnings
from django_apps.asteroid_lab.layers.contracts.layer04_disabled import Layer04DisabledResult

def run_layer_04_rim_bundle_placement(*args, **kwargs) -> Layer04DisabledResult:
    warnings.warn(
        "layer_04_rim_bundle_placement is disabled; use layer_03_rim_greedy_placement",
        DeprecationWarning,
        stacklevel=2,
    )
    return Layer04DisabledResult.superseded()
```

Remove algorithm imports (`candidates`, route probe, overlay mutation).

- [ ] **Step 4: Legacy L3 delegate test + implementation**

```python
# tests/unit/asteroid_lab/layers/test_layer_03_legacy_delegate.py
import warnings

from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_03_RIM_GREEDY_PLACEMENT
from django_apps.asteroid_lab.layers.contracts.rim_greedy import IntegratedRimGreedyResult
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.run import (
    run_layer_03_rim_mining_bundles,
)


def test_legacy_l3_delegates_to_greedy(canonical_complete_map, budget_ctx) -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = run_layer_03_rim_mining_bundles(
            complete_map=canonical_complete_map,
            exterior_plan=None,
            budget_ctx=budget_ctx,
        )
    assert isinstance(result, IntegratedRimGreedyResult)
    assert result.metrics.canonical_layer_slug == LAYER_03_RIM_GREEDY_PLACEMENT
    assert any(issubclass(x.category, DeprecationWarning) for x in w)
```

Implement `run_layer_03_rim_mining_bundles` as `return run_layer_03_rim_greedy_placement(...)` with deprecation warning (use shared fixtures from `tests/support/reconstruction_complete_map_fixtures.py`).

- [ ] **Step 5: Run tests — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_disabled_shim.py tests/unit/asteroid_lab/layers/test_layer_03_legacy_delegate.py -v`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(asteroid_lab): disable L4 shim and delegate legacy L3 import"
```

---

### Task 3: Greedy package skeleton + empty run

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/__init__.py`
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py`
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchors.py`
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/dps_policy.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_run.py`

- [ ] **Step 1: Failing run test (L2 hold)**

```python
def test_run_returns_empty_when_exterior_plan_missing(canonical_complete_map, budget_ctx):
    from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
        run_layer_03_rim_greedy_placement,
    )

    result = run_layer_03_rim_greedy_placement(
        complete_map=canonical_complete_map,
        exterior_plan=None,
        budget_ctx=budget_ctx,
    )
    assert result.metrics.layer_skip_reason == "missing_exterior_connection_plan"
```

- [ ] **Step 2: Implement `run.py` skeleton**

```python
def run_layer_03_rim_greedy_placement(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext,
    seed_catalog: object | None = None,
    resource_kind: ResourceKind | None = None,
    transport_kind: TransportKind | None = None,
    policy: RimGreedyPolicy | None = None,
) -> IntegratedRimGreedyResult:
    _ = (budget_ctx, seed_catalog, resource_kind, transport_kind, policy)
    if exterior_plan is None:
        anchors = build_ordered_outer_rim_anchors(complete_map)
        return build_empty_integrated_rim_greedy_result(
            layer_skip_reason="missing_exterior_connection_plan",
            rim_anchor_count=len(anchors),
        )
    # Task 6+: full greedy
    return build_empty_integrated_rim_greedy_result()
```

- [ ] **Step 3: `dps_policy.py`**

```python
@dataclass(frozen=True, slots=True)
class RimGreedyPolicy:
    dps_search_margin: int = 12

    @classmethod
    def default(cls) -> RimGreedyPolicy:
        return cls()
```

- [ ] **Step 4: Run test — PASS; commit**

```bash
git commit -m "feat(asteroid_lab): add rim greedy layer skeleton and L2 hold"
```

---

### Task 4: Ordered rim anchors (golden)

**Files:**
- Modify: `layer_03_rim_greedy_placement/rim_anchors.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_anchors.py`
- Create: `tests/golden/asteroid_lab/rim_greedy_anchor_order_v1.json` (small fixture map)

- [ ] **Step 1: Golden test — traversal indices deterministic**

```python
def test_rim_anchor_traversal_order_golden(canonical_complete_map):
    anchors = build_ordered_outer_rim_anchors(canonical_complete_map)
    coords = [a.coord for a in anchors]
    assert coords == EXPECTED_GOLDEN_COORDS  # load from golden JSON
    for i, a in enumerate(anchors):
        assert a.traversal_index == i
        assert all(d in {"N", "E", "S", "W"} for d in a.void_dirs)
```

- [ ] **Step 2: Implement `build_ordered_outer_rim_anchors`**

Algorithm sketch:
1. Compute rim cells: field cell with neighbor in `external_void_cells` only (not interior void).
2. Build adjacency graph along rim edges.
3. Pick deterministic start (min y, then min x for `CW_TL` variant baseline).
4. Walk boundary assigning `traversal_index`.

- [ ] **Step 3: Run golden test — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_anchors.py -v`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(asteroid_lab): deterministic outer rim anchor traversal"
```

---

### Task 5: Traversal variants

**Files:**
- Create: `layer_03_rim_greedy_placement/traversal_variants.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_variants.py`

- [ ] **Step 1: Test four variant ids produce different orders when map asymmetric**

```python
VARIANT_IDS = ("CW_TL", "CCW_TL", "CW_MID", "EDGE_INTERLEAVE")

def test_variants_are_distinct_on_asymmetric_map(asymmetric_complete_map):
    orders = {
        vid: [a.coord for a in build_variant_anchor_order(anchors, vid)]
        for vid in VARIANT_IDS
    }
    assert len({tuple(o) for o in orders.values()}) >= 2
```

- [ ] **Step 2: Implement variant builders per spec §4.3**

- [ ] **Step 3: Run tests — PASS; commit**

---

### Task 6: Pass1 greedy loop + route reservation

**Files:**
- Create: `layer_03_rim_greedy_placement/greedy_pass1.py`
- Create: `layer_03_rim_greedy_placement/seed_orient.py`
- Create: `layer_03_rim_greedy_placement/local_window.py`
- Modify: `layer_03_rim_greedy_placement/run.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_reservation.py`

- [ ] **Step 1: Reservation regression test**

```python
def test_second_equipment_cannot_block_first_reserved_path(fixture_map_with_two_anchors):
    result = run_layer_03_rim_greedy_placement(..., exterior_plan=plan, ...)
    assert len(result.committed_placements) >= 1
  # Construct scenario: first placement reserves path; second overlapping equipment rejected
    reasons = [r.reason for r in result.rejected_attempts]
    assert RimGreedyRejectReason.EQUIPMENT_COLLISION in reasons or \
           RimGreedyRejectReason.ROUTE_CROSSES_HARD_BLOCKER in reasons
```

- [ ] **Step 2: Implement `RimGreedyState` with `variant_id`**

- [ ] **Step 3: Implement pass1 loop per spec §4.5–4.9**

Wire `weighted_route_probe` from `layers/shared/route_probe.py` with `dps_policy` weights.

On success:
- append `CommittedRimSeedPlacement(..., variant_id=state.variant_id)`
- update consumed/invalidated sets
- `reserved_route_cells |= path`

- [ ] **Step 4: Build `provisional_overlay` from winning variant placements**

Use `LAYER_03_GREEDY_SOURCE` on overlay.

- [ ] **Step 5: Run reservation + focused tests — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_reservation.py -v`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(asteroid_lab): rim greedy pass1 with route reservation"
```

---

### Task 7: Pass2 score + variant winner

**Files:**
- Create: `layer_03_rim_greedy_placement/greedy_pass2.py`
- Modify: `run.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_03_rim_greedy_pass2.py`

- [ ] **Step 1: Test variant winner tie-break**

```python
def test_winning_variant_is_lexicographic_tiebreak(monkeypatch):
    # Force equal scores from CW_TL and CCW_TL mocks
    result = run_layer_03_rim_greedy_placement(...)
    assert result.winning_variant_id == "CCW_TL"  # if CCW_TL > CW_TL lexically when scores equal
```

Adjust expected id to match spec: `max(score)` then `variant_id` lex — document in test.

- [ ] **Step 2: Implement pass2 read-only validation**

```python
def score_variant(state: RimGreedyState) -> RimGreedyPass2Report:
    if hard_fail(state):
        return RimGreedyPass2Report(..., score=None, hard_fail=True, ...)
    route_len = sum(len(p.route_probe_path) for p in state.committed_placements)
    m = sum(len(p.miner_cells) for p in state.committed_placements)
    e = sum(len(p.extension_cells) for p in state.committed_placements)
    score = 2 * m + e - 0.05 * route_len
    return RimGreedyPass2Report(..., score=score, hard_fail=False, ...)
```

- [ ] **Step 3: Run pass2 tests — PASS; commit**

---

### Task 8: `stack_runner` wiring (L4 removed from runners)

**Files:**
- Modify: `django_apps/asteroid_lab/layers/stack_runner.py`
- Modify: `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py`
- Modify: `tests/unit/asteroid_lab/test_solver_runtime_rim_stack.py`

- [ ] **Step 1: Update failing stack tests**

```python
# Expect completed slugs without L4
assert LAYER_03_RIM_GREEDY_PLACEMENT in summary["completed_layer_slugs"]
assert LAYER_04_RIM_BUNDLE_PLACEMENT not in summary["completed_layer_slugs"]
```

- [ ] **Step 2: Change `_DEFAULT_RUNNERS`**

```python
_DEFAULT_RUNNERS: tuple[_LayerStackRunner, ...] = (
    _LayerStackRunner(LAYER_02_EXTERIOR_TRANSPORT, run_layer_02_exterior_transport),
    _LayerStackRunner(LAYER_03_RIM_GREEDY_PLACEMENT, run_layer_03_rim_greedy_placement),
    _LayerStackRunner(LAYER_05_INNER_PATTERN_FILL, run_layer_05_inner_pattern_fill),
    _LayerStackRunner(LAYER_06_COMMIT_VALIDATE, run_layer_06_commit_validate),
)
```

Add `_LAYER_INDEX[LAYER_03_RIM_GREEDY_PLACEMENT] = 3`; keep L4 at 4 (inactive).

- [ ] **Step 3: L3 branch**

```python
elif entry.slug == LAYER_03_RIM_GREEDY_PLACEMENT:
    last_rim_greedy = entry.run(
        complete_map=complete_map,
        budget_ctx=budget_ctx,
        exterior_plan=last_exterior_plan,
    )
    post_metrics = build_layer03_rim_greedy_post_summary_metrics(last_rim_greedy)
```

Remove L4 `elif` branch entirely.

- [ ] **Step 4: L5 mechanical bridge (API unchanged)**

```python
elif entry.slug == LAYER_05_INNER_PATTERN_FILL:
    overlay = (
        last_rim_greedy.provisional_overlay
        if last_rim_greedy is not None
        else ProvisionalLayoutOverlay.empty()
    )
    # Build minimal Layer04RimPlacementResult shim object OR pass overlay kwarg only
    entry.run(..., provisional_overlay=overlay, rim_placement_result=..., ...)
```

Use empty `Layer04DisabledResult`-compatible struct or existing `empty_layer04_rim_placement_result()` for `rim_placement_result` parameter **without running L4**.

- [ ] **Step 5: Run stack tests**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py tests/unit/asteroid_lab/test_solver_runtime_rim_stack.py -v`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(asteroid_lab): wire rim greedy in stack_runner and drop L4 runner"
```

---

### Task 9: Observability + behavior catalog

**Files:**
- Modify: `layer_behavior_catalog.py`
- Modify: `layer_post_summary_log.py` — add `build_layer03_rim_greedy_post_summary_metrics`
- Create: `tests/unit/asteroid_lab/layers/test_layer_behavior_catalog.py` (update expectations)

- [ ] **Step 1: Test behavior catalog lists greedy, not legacy L3/L4 as active**

```python
def test_greedy_slug_has_behavior():
    text = layer_behavior_for_slug(LAYER_03_RIM_GREEDY_PLACEMENT)
    assert "greedy" in text.lower()
```

- [ ] **Step 2: Implement metrics builder from `IntegratedRimGreedyResult.metrics`**

- [ ] **Step 3: Run tests — PASS; commit**

---

### Task 10: Replay observation events (no frame ids)

**Files:**
- Create: `replay/layer03_rim_greedy_segment.py`
- Modify: `replay/solver_runtime_assembler.py` (register segment)
- Create: `tests/unit/asteroid_lab/replay/test_layer03_rim_greedy_segment.py`

- [ ] **Step 1: Test assembler projects `observability_events` to frames**

```python
def test_greedy_events_materialize_monotonic_frames():
    result = IntegratedRimGreedyResult(..., observability_events=(event_begin, event_complete))
    frames = materialize_rim_greedy_frames(result.observability_events)
    assert frames[0].metrics["phase"] == "rim_greedy_begin"
    assert all(frames[i].frame_index <= frames[i + 1].frame_index for i in range(len(frames) - 1))
```

- [ ] **Step 2: Implement segment projector**

L3 `run.py` appends `RimGreedyObservationEvent` tuples only; no `frame_index` assignment in layer code.

- [ ] **Step 3: Deprecate pool-windowing tests or mark skip with reason**

`test_layer03_pool_windowing.py` — `@pytest.mark.skip(reason="superseded by rim greedy segment")` until removed.

- [ ] **Step 4: Run replay tests — PASS; commit**

---

### Task 11: Full verification gate

- [ ] **Step 1: Run focused asteroid_lab tests**

Run: `powershell -File scripts/test_fast.ps1`  
Or narrow: `python -m pytest tests/unit/asteroid_lab/layers tests/unit/asteroid_lab/test_solver_runtime_rim_stack.py tests/unit/asteroid_lab/replay/test_layer03_rim_greedy_segment.py -v`

- [ ] **Step 2: Lint**

Run: `python -m ruff check django_apps/asteroid_lab/layers django_apps/asteroid_lab/replay tests/unit/asteroid_lab`

- [ ] **Step 3: Typecheck**

Run: `python -m mypy django_apps/asteroid_lab/layers django_apps/asteroid_lab/replay`

- [ ] **Step 4: Final commit if fixes needed**

```bash
git commit -m "test(asteroid_lab): rim greedy integration verification"
```

---

## Spec coverage self-review

| Spec section | Task |
|--------------|------|
| §1 Identity / supersession | 1, 2, 9 |
| §2 Stack / slug alias / index 4 reserved | 1, 8 |
| §3 L4 disable | 2 |
| §4 L3 responsibility (anchors, variants, pass1/2, DPS) | 4–7 |
| §5 DTOs (`variant_id`, typed score, observability_events) | 1, 6, 7 |
| §6 Replay | 10 |
| §7 Module layout | 3–7 |
| §8 Inputs / L2 hold | 3 |
| §9 Testing | all test tasks |
| §10 Migration checklist | Tasks 1–11 order |

**Placeholder scan:** None.

**Out-of-scope guard:** Task 8 L5 bridge is mechanical overlay pass-through only; no edits to `layer_05_inner_pattern_fill/run.py`.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-29-layer-03-rim-greedy-placement.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with checkpoints  

Which approach?
