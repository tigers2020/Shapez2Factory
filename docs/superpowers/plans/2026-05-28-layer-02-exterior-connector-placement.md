# Layer 02 Exterior Connector Placement — Implementation Plan (v2.2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Plan review (2026-05-28):** **v2 replaces v1.** **v2.1:** master EVTC wrapper (`get_active_*` + `space_*_max_per_min_from_row`). **v2.2:** Task 9 reads `SolverRun.config_json` only (no `solver_summary_json` on master). **APPROVED FOR EXECUTION.** **Execution:** Subagent-Driven, task-by-task.

**Goal:** Add Layer 02 exterior connector planning (`VOID_DEEP_SLOTS_V1` + `EDGE_WEIGHTED_EVEN_SPACING_V1` + `FIELDWARD_FACING_V1`) on `ReconstructionCompleteMap`, EVTC-backed capacity, metrics wire, and Lab timeline marker/sprite display — without resurrecting full solver runtime.

**Architecture:** New package slice under `django_apps/asteroid_lab/layers/` (contracts + `layer_02_exterior_transport/` pure modules). BFS uses **NESW-ordered deltas**, not `neighbors4()` (`W,E,N,S`). Capacity: L2 `capacity.py` wraps **master EVTC** (`get_active_exterior_*` + `space_belt_max_per_min_from_row` / `space_pipe_max_per_min_from_row`) — no cap numeric literals in L2. Lab enrichment mirrors `lab_timeline_rim_enrichment.py` (deep-copy, frozen metrics). Payload hook is **no-op-safe** until a later PR persists `exterior_connector_plan` on solver runs.

**Spec note:** Design spec §2.1 illustrative `line×lines_per_space_belt` example may differ from master `space_belt_max` sizing; **L2 follows master EVTC row helpers** until a follow-up spec/game_data amendment aligns naming.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy `django_apps config src`, `Decimal`, `StrEnum`, `dataclasses`

**Spec:** [`2026-05-28-layer-02-exterior-connector-placement-design.md`](../specs/2026-05-28-layer-02-exterior-connector-placement-design.md)

**Branch:** feature branch from current master / decontamination baseline (dedicated worktree recommended)

---

## Repo baseline (P0 facts)

| Fact | Source | Plan impact |
|------|--------|-------------|
| `ReconstructionCompleteMap` has `field_cells`, `external_void_cells`, `coord_frame` | `reconstruction/complete_map.py` | L2 input SoT |
| `field_rim_cells()` exists | `reconstruction/rim_topology.py` | BFS seed only |
| `neighbors4()` order is **W, E, N, S** | `snapshots/grid_contract.py` | **Do not use** for L2 BFS tie-break |
| EVTC tier-1 seed: `15×4×48 → space_belt_max=2880` | `game_data/migrations/0027_*` | No `720/8640/2880` string literals in L2 |
| Capacity sizing (master) | `get_active_exterior_*` + `space_*_max_per_min_from_row` | L2 `capacity.py` wraps these only |
| `exterior_connector_capacity_per_min()` | **Not on merge-base master** | Do **not** import in L2; optional on some branches — ignore for PR-2 |
| Rim highlight = UI only | rim enricher + spec | Share `field_rim_cells`, never read replay wire as L2 input |
| `solver_runtime_entry` = fail-closed stub | `solver_runtime_entry.py` | **No** stack_runner wiring in PR-2 |
| `SolverRun` JSON persistence | `models.py` — `config_json` only | Task 9 hook reads `config_json`; **no** `solver_summary_json` field |
| Local branch may contain layer-stack **stubs** | optional `layers/stack_runner.py` | **Out of scope** — do not block PR-2 on stub wiring |

### P0 corrections from v1 (normative)

1. **Remove** `stack_runner.py`, `layer_post_summary_log.py` modifications from PR-2 scope.
2. **EVTC (master):** `capacity.py` calls `get_active_exterior_shape_transport_capacity` + `space_belt_max_per_min_from_row` (shape) or `get_active_exterior_fluid_transport_capacity` + `space_pipe_max_per_min_from_row` (fluid). Never embed `720`, `8640`, `2880`, `345600` cap literals in L2 production modules.
3. **BFS:** `_NEIGHBOR_DELTAS_NESW` in `slots.py` only.
4. **Rotation:** no `Direction` enum; `rotation.py` int tables only.
5. **`nearest_unused_index`:** prefer **lower** index on tie: scan `(idx - offset, idx + offset)`.
6. **`layout_t`:** base tile only; facing in `rotation`.

---

## Out of scope (PR-2)

```text
- solver_runtime_entry.py full solver resurrection
- stack_runner L2 slot wiring / LayerPostSummaryLogSession metrics
- Layer 3+ route probe, Layer 5 commit mutation
- django_apps/asteroid_lab/optimization/ import
- Using terrain_rim_highlight replay wire as L2 input
```

### Follow-up PR (named, not in this plan)

```text
PR-2b-runtime: wire build_exterior_connection_plan into stack_runner / solver_summary /
  solver_runtime_entry when SOLVER_NOT_AVAILABLE is lifted.
```

---

## File map

| Action | Path |
|--------|------|
| Create | `django_apps/asteroid_lab/layers/__init__.py` (if missing on baseline) |
| Create | `django_apps/asteroid_lab/layers/contracts/cardinal_edge.py` |
| Create | `django_apps/asteroid_lab/layers/contracts/exterior_connection.py` |
| Create | `django_apps/asteroid_lab/layers/shared/ceildiv.py` |
| Create | `django_apps/asteroid_lab/layers/layer_02_exterior_transport/rotation.py` |
| Create | `django_apps/asteroid_lab/layers/layer_02_exterior_transport/slots.py` |
| Create | `django_apps/asteroid_lab/layers/layer_02_exterior_transport/placement.py` |
| Create | `django_apps/asteroid_lab/layers/layer_02_exterior_transport/capacity.py` |
| Create | `django_apps/asteroid_lab/layers/layer_02_exterior_transport/layout_t.py` |
| Create | `django_apps/asteroid_lab/layers/layer_02_exterior_transport/plan.py` |
| Create | `django_apps/asteroid_lab/layers/layer_02_exterior_transport/wire.py` |
| Create | `django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py` |
| Modify | `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py` |
| Modify | `assets/css/input.css` |
| Modify | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` |
| Create | `tests/unit/asteroid_lab/layers/helpers/l02_complete_map_fixtures.py` |
| Create | `tests/unit/asteroid_lab/layers/test_layer_02_*.py` (see tasks) |
| Create | `tests/unit/asteroid_lab/test_lab_timeline_exterior_connector_enrichment.py` |
| Modify | `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` |

**Not modified in PR-2:** `stack_runner.py`, `layer_post_summary_log.py`, `solver_runtime_entry.py`, `run.py` stub (optional thin export only if file already exists).

---

## Task 1 — Contracts

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/__init__.py`
- Create: `django_apps/asteroid_lab/layers/contracts/cardinal_edge.py`
- Create: `django_apps/asteroid_lab/layers/contracts/exterior_connection.py`
- Create: `django_apps/asteroid_lab/layers/shared/__init__.py`
- Create: `django_apps/asteroid_lab/layers/shared/ceildiv.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_02_contracts.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/asteroid_lab/layers/test_layer_02_contracts.py
from decimal import Decimal

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)


def test_cardinal_edge_wire_slugs() -> None:
    assert CardinalEdge.NORTH.value == "north"
    assert CardinalEdge.EAST.value == "east"


def test_exterior_connector_coords_singleton() -> None:
    conn = ExteriorConnector(
        connector_id="ext_conn_00",
        void_coord=(5, -6),
        edge=CardinalEdge.NORTH,
        layout_t="SpaceBelt_Forward",
        rotation=1,
        capacity_per_min=Decimal("1"),
        coords=((5, -6),),
    )
    assert conn.coords == (conn.void_coord,)


def test_exterior_connection_plan_default_rules() -> None:
    plan = ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("100"),
        planning_target_per_min=Decimal("80"),
        per_connector_capacity_per_min=Decimal("1"),
        required_connector_count=0,
        planned_connectors=(),
        unmet_reason=None,
    )
    assert plan.slot_rule == "VOID_DEEP_SLOTS_V1"
    assert plan.placement_rule == "EDGE_WEIGHTED_EVEN_SPACING_V1"
    assert plan.rotation_rule == "FIELDWARD_FACING_V1"
```

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_contracts.py -v
```

- [ ] **Step 3: Implement**

```python
# django_apps/asteroid_lab/layers/contracts/cardinal_edge.py
from enum import StrEnum


class CardinalEdge(StrEnum):
    NORTH = "north"
    EAST = "east"
    SOUTH = "south"
    WEST = "west"
```

```python
# django_apps/asteroid_lab/layers/contracts/exterior_connection.py
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


class ExteriorConnectionShortfallReason(StrEnum):
    MISSING_EVTC_ROW = "missing_evtc_row"
    TARGET_EXCEEDS_TERRAIN_UPPER_BOUND = "target_exceeds_terrain_upper_bound"
    NO_FEASIBLE_CONNECTOR_SITES = "no_feasible_connector_sites"


@dataclass(frozen=True, slots=True)
class ExteriorConnector:
    connector_id: str
    void_coord: Coord
    edge: CardinalEdge
    layout_t: str
    rotation: int
    capacity_per_min: Decimal
    coords: tuple[Coord, ...]


@dataclass(frozen=True, slots=True)
class ExteriorConnectionPlan:
    transport_kind: str
    terrain_upper_bound_per_min: Decimal
    planning_target_per_min: Decimal
    per_connector_capacity_per_min: Decimal
    required_connector_count: int
    planned_connectors: tuple[ExteriorConnector, ...]
    unmet_reason: ExteriorConnectionShortfallReason | None
    slot_rule: str = "VOID_DEEP_SLOTS_V1"
    placement_rule: str = "EDGE_WEIGHTED_EVEN_SPACING_V1"
    rotation_rule: str = "FIELDWARD_FACING_V1"
```

```python
# django_apps/asteroid_lab/layers/shared/ceildiv.py
from __future__ import annotations

from decimal import Decimal, ROUND_CEILING


def ceildiv_decimal(numerator: Decimal, denominator: Decimal) -> int:
    if denominator <= 0 or numerator <= 0:
        return 0
    return int((numerator / denominator).to_integral_value(rounding=ROUND_CEILING))
```

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit (when user requests)**

```text
feat(l2): add exterior connector contracts and ceildiv
```

---

## Task 2 — Rotation constants

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/__init__.py`
- Create: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/rotation.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_02_rotation.py`

- [ ] **Step 1: Failing tests**

```python
from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.rotation import (
    FIELDWARD_ROTATION_BY_EDGE,
    ROTATION_R0_E_CW,
)


def test_rotation_convention_r0_e_clockwise() -> None:
    assert ROTATION_R0_E_CW["east"] == 0
    assert ROTATION_R0_E_CW["south"] == 1
    assert ROTATION_R0_E_CW["west"] == 2
    assert ROTATION_R0_E_CW["north"] == 3


def test_connector_rotation_fieldward_mapping() -> None:
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.NORTH] == 1
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.EAST] == 2
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.SOUTH] == 3
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.WEST] == 0
```

- [ ] **Step 2: Run — FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_rotation.py -v
```

- [ ] **Step 3: Implement**

```python
# rotation.py
from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge

ROTATION_R0_E_CW = {
    "east": 0,
    "south": 1,
    "west": 2,
    "north": 3,
}

FIELDWARD_ROTATION_BY_EDGE = {
    CardinalEdge.NORTH: 1,
    CardinalEdge.EAST: 2,
    CardinalEdge.SOUTH: 3,
    CardinalEdge.WEST: 0,
}
```

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit (when user requests)**

---

## Task 3 — `VOID_DEEP_SLOTS_V1` (`slots.py`)

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/slots.py`
- Create: `tests/unit/asteroid_lab/layers/helpers/l02_complete_map_fixtures.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_02_void_deep_slots.py`

**Normative:** use `field_rim_cells` from `rim_topology`; **never** `neighbors4()` for expansion order.

```python
_NEIGHBOR_DELTAS_NESW: tuple[tuple[CardinalEdge, tuple[int, int]], ...] = (
    (CardinalEdge.NORTH, (0, -1)),
    (CardinalEdge.EAST, (1, 0)),
    (CardinalEdge.SOUTH, (0, 1)),
    (CardinalEdge.WEST, (-1, 0)),
)
```

**Seed loop order (normative):**

```text
for edge in N, E, S, W:
  for source_field in sorted(outer_rim_field):
    seed = source_field + delta(edge)
```

- [ ] **Step 1: Fixture helper**

```python
# tests/unit/asteroid_lab/layers/helpers/l02_complete_map_fixtures.py
from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def make_complete_map(
    *,
    field_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
) -> ReconstructionCompleteMap:
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field_cells,
        shape_field_cell_count=len(field_cells),
        fluid_field_cell_count=0,
        external_void_cells=external_void_cells,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def build_rect_field_with_void_shell(
    *,
    width: int,
    height: int,
    void_pad: int,
) -> ReconstructionCompleteMap:
    field = frozenset((x, y) for x in range(width) for y in range(height))
    void: set[Coord] = set()
    for x in range(-void_pad, width + void_pad):
        for y in range(-void_pad, height + void_pad):
            if (x, y) not in field:
                void.add((x, y))
    return make_complete_map(field_cells=field, external_void_cells=frozenset(void))
```

- [ ] **Step 2: Failing slot tests** (§4.1–4.2 from spec)

```python
from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.slots import (
    VOID_DEPTH_MIN,
    build_candidate_slots_by_edge,
    compute_void_depth_entries,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
    make_complete_map,
)


def test_void_depth_excludes_rim_adjacent() -> None:
    cm = build_rect_field_with_void_shell(width=6, height=6, void_pad=10)
    entries = compute_void_depth_entries(cm)
    shallow = [c for c, e in entries.items() if 1 <= e.depth < VOID_DEPTH_MIN]
    assert shallow
    chosen = {c for slots in build_candidate_slots_by_edge(cm).values() for c in slots}
    assert not chosen.intersection(shallow)


def test_void_depth_includes_at_5() -> None:
    cm = build_rect_field_with_void_shell(width=6, height=6, void_pad=10)
    entries = compute_void_depth_entries(cm)
    at_five = [c for c, e in entries.items() if e.depth == VOID_DEPTH_MIN]
    assert at_five
    chosen = {c for slots in build_candidate_slots_by_edge(cm).values() for c in slots}
    assert at_five[0] in chosen


def test_shallow_void_side_zero_slots() -> None:
    field = frozenset({(0, 0), (1, 0), (0, 1), (1, 1)})
    void = frozenset({(0, -1), (1, -1)})
    cm = make_complete_map(field_cells=field, external_void_cells=void)
    assert build_candidate_slots_by_edge(cm)[CardinalEdge.NORTH] == []
```

- [ ] **Step 3: Run — FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_void_deep_slots.py -v
```

- [ ] **Step 4: Implement `slots.py`**

Public API:

```python
VOID_DEPTH_MIN = 5

@dataclass(frozen=True, slots=True)
class VoidDepthEntry:
    void_coord: Coord
    depth: int
    source_edge: CardinalEdge
    source_field: Coord

def compute_void_depth_entries(
    complete_map: ReconstructionCompleteMap,
) -> dict[Coord, VoidDepthEntry]:
    """Multi-source BFS; seeds at depth 1; see spec §1.4."""

def build_candidate_slots_by_edge(
    complete_map: ReconstructionCompleteMap,
) -> dict[CardinalEdge, list[Coord]]:
    """Eligible void coords (depth >= VOID_DEPTH_MIN) sorted per edge."""
```

- [ ] **Step 5: Add `test_void_depth_bfs_only_through_external_void`**, `test_candidate_slot_order_by_edge`, `test_void_deep_slot_edge_from_bfs_source`, `test_no_global_nearest_field_bucket` per spec.

- [ ] **Step 6: Run — PASS**

- [ ] **Step 7: Commit (when user requests)**

---

## Task 4 — `EDGE_WEIGHTED_EVEN_SPACING_V1` (`placement.py`)

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/placement.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_02_placement.py`

- [ ] **Step 1: Failing tests**

```python
from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.placement import (
    choose_even_slots,
    distribute_connector_counts,
    even_slot_index,
    nearest_unused_index,
)


def test_even_slot_index_half_up_not_bankers() -> None:
    assert even_slot_index(i=0, count=3, slot_count=10) == 2


def test_nearest_unused_prefers_lower_index_on_tie() -> None:
    used = {2}
    assert nearest_unused_index(2, 5, used) == 1


def test_edge_weighted_count_distribution_sums_to_n() -> None:
    edge_slots = {
        CardinalEdge.NORTH: [(0, -5)] * 10,
        CardinalEdge.EAST: [(5, 0)] * 10,
        CardinalEdge.SOUTH: [(0, 9)] * 10,
        CardinalEdge.WEST: [(-5, 0)] * 10,
    }
    counts = distribute_connector_counts(9, edge_slots)
    assert sum(counts.values()) == 9


def test_choose_even_slots_raises_when_count_exceeds_slots() -> None:
    import pytest
    from django_apps.asteroid_lab.layers.layer_02_exterior_transport.placement import (
        InsufficientConnectorSlotsError,
    )
    with pytest.raises(InsufficientConnectorSlotsError):
        choose_even_slots([(0, 0), (1, 0)], 3)
```

- [ ] **Step 2: Implement**

```python
def even_slot_index(*, i: int, count: int, slot_count: int) -> int:
    if count <= 0 or slot_count <= 0:
        return 0
    numer = (i + 1) * (slot_count + 1)
    denom = count + 1
    idx = (numer + denom // 2) // denom - 1
    return max(0, min(slot_count - 1, idx))


def nearest_unused_index(idx: int, length: int, used: set[int]) -> int:
    for offset in range(1, length):
        for candidate in (idx - offset, idx + offset):
            if 0 <= candidate < length and candidate not in used:
                return candidate
    return idx
```

Implement `distribute_connector_counts` and `choose_even_slots` per spec §2.2–2.3.

- [ ] **Step 3: Run — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_placement.py -v
```

- [ ] **Step 4: Commit (when user requests)**

---

## Task 5 — EVTC adapter + `layout_t`

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/capacity.py`
- Create: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/layout_t.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_02_capacity.py`

**Normative capacity SoT (current master):**

```text
shape:
  row = get_active_exterior_shape_transport_capacity(speed_tier=...)
  cap = space_belt_max_per_min_from_row(row)

fluid:
  row = get_active_exterior_fluid_transport_capacity(speed_tier=...)
  cap = space_pipe_max_per_min_from_row(row)

LookupError → ExteriorConnectionShortfallReason.MISSING_EVTC_ROW
```

Do **not** import or require `exterior_connector_capacity_per_min()` in L2 (may exist on some branches; merge-base master does not). Do **not** embed numeric cap literals in `layer_02_exterior_transport/`.

- [ ] **Step 1: Failing tests (`@pytest.mark.django_db`)**

```python
# tests/unit/asteroid_lab/layers/test_layer_02_capacity.py
import pytest

from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionShortfallReason,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.capacity import (
    resolve_per_connector_capacity,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.layout_t import (
    default_exterior_connector_layout_t,
)
from django_apps.game_data.services.exterior_transport_capacity import (
    get_active_exterior_shape_transport_capacity,
    space_belt_max_per_min_from_row,
)


@pytest.mark.django_db
def test_shape_capacity_uses_evtc_service() -> None:
    row = get_active_exterior_shape_transport_capacity(speed_tier=1)
    expected = space_belt_max_per_min_from_row(row)

    got = resolve_per_connector_capacity(resource_kind="shape", speed_tier=1)

    assert got.shortfall_reason is None
    assert got.capacity_per_min == expected
    assert got.capacity_per_min is not None
    assert got.capacity_per_min > 0


@pytest.mark.django_db
def test_missing_evtc_row_returns_missing_evtc_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(**_kwargs: object) -> object:
        raise LookupError("no row")

    monkeypatch.setattr(
        "django_apps.asteroid_lab.layers.layer_02_exterior_transport.capacity."
        "get_active_exterior_shape_transport_capacity",
        _boom,
    )

    got = resolve_per_connector_capacity(resource_kind="shape", speed_tier=99)

    assert got.capacity_per_min is None
    assert got.shortfall_reason == ExteriorConnectionShortfallReason.MISSING_EVTC_ROW


def test_layout_t_shape_base() -> None:
    assert default_exterior_connector_layout_t(resource_kind="shape") == "SpaceBelt_Forward"


def test_layout_t_fluid_base() -> None:
    assert default_exterior_connector_layout_t(resource_kind="fluid") == "SpacePipe_Forward"
```

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_capacity.py -v
```

- [ ] **Step 3: Implement `capacity.py`**

```python
# django_apps/asteroid_lab/layers/layer_02_exterior_transport/capacity.py
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionShortfallReason,
)
from django_apps.game_data.services.exterior_transport_capacity import (
    get_active_exterior_fluid_transport_capacity,
    get_active_exterior_shape_transport_capacity,
    space_belt_max_per_min_from_row,
    space_pipe_max_per_min_from_row,
)


@dataclass(frozen=True, slots=True)
class CapacityResolution:
    capacity_per_min: Decimal | None
    shortfall_reason: ExteriorConnectionShortfallReason | None


def resolve_per_connector_capacity(
    *,
    resource_kind: str,
    speed_tier: int,
) -> CapacityResolution:
    try:
        if resource_kind == "fluid":
            row = get_active_exterior_fluid_transport_capacity(speed_tier=speed_tier)
            cap = space_pipe_max_per_min_from_row(row)
        else:
            row = get_active_exterior_shape_transport_capacity(speed_tier=speed_tier)
            cap = space_belt_max_per_min_from_row(row)
    except LookupError:
        return CapacityResolution(
            capacity_per_min=None,
            shortfall_reason=ExteriorConnectionShortfallReason.MISSING_EVTC_ROW,
        )

    return CapacityResolution(capacity_per_min=cap, shortfall_reason=None)
```

```python
# django_apps/asteroid_lab/layers/layer_02_exterior_transport/layout_t.py
def default_exterior_connector_layout_t(*, resource_kind: str) -> str:
    if resource_kind == "fluid":
        return "SpacePipe_Forward"
    return "SpaceBelt_Forward"
```

- [ ] **Step 4: Run — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_capacity.py -v
```

- [ ] **Step 5: Commit (when user requests)**

```text
feat(l2): add EVTC capacity adapter and layout_t defaults
```

---

## Task 6 — Plan builder + wire

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/plan.py`
- Create: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/wire.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py`

- [ ] **Step 1: Failing integration tests (`@pytest.mark.django_db`)**

```python
# tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py
from decimal import Decimal

import pytest

from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionShortfallReason,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.layout_t import (
    default_exterior_connector_layout_t,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)


@pytest.mark.django_db
def test_required_connectors_uses_evtc_ceildiv_shape() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=100,
        speed_tier=1,
    )
    assert plan.unmet_reason is None
    assert len(plan.planned_connectors) == plan.required_connector_count
    assert plan.required_connector_count >= 1


@pytest.mark.django_db
def test_insufficient_slots_fail_closed() -> None:
    cm = build_rect_field_with_void_shell(width=2, height=2, void_pad=3)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("999999"),
        throughput_target_percent=100,
        speed_tier=1,
    )
    assert plan.unmet_reason == ExteriorConnectionShortfallReason.NO_FEASIBLE_CONNECTOR_SITES
    assert plan.planned_connectors == ()


@pytest.mark.django_db
def test_planned_connector_snapshot_fields() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("5000"),
        throughput_target_percent=50,
        speed_tier=1,
    )
    assert plan.planned_connectors
    row = plan.planned_connectors[0]
    assert row.connector_id.startswith("ext_conn_")
    assert row.coords == (row.void_coord,)
    assert row.layout_t == "SpaceBelt_Forward"
    assert 0 <= row.rotation <= 3


@pytest.mark.django_db
def test_wire_uses_lowercase_edge_slug() -> None:
    cm = build_rect_field_with_void_shell(width=8, height=8, void_pad=10)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("3000"),
        throughput_target_percent=100,
        speed_tier=1,
    )
    wire = exterior_connector_plan_to_metrics_dict(plan)["exterior_connector_plan"]
    assert isinstance(wire, dict)
    connectors = wire.get("planned_connectors")
    assert isinstance(connectors, list) and connectors
    assert connectors[0]["edge"] in {"north", "east", "south", "west"}


def test_layout_t_and_rotation_are_separate() -> None:
    from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
    from django_apps.asteroid_lab.layers.layer_02_exterior_transport.rotation import (
        FIELDWARD_ROTATION_BY_EDGE,
    )

    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.EAST] == 2
    assert default_exterior_connector_layout_t(resource_kind="shape") == "SpaceBelt_Forward"
```

- [ ] **Step 2: Implement `build_exterior_connection_plan` pipeline** (spec §2.4; no `run.py` stack dependency)

```python
def build_exterior_connection_plan(
    *,
    complete_map: ReconstructionCompleteMap,
    resource_kind: str,
    terrain_upper_bound_per_min: Decimal,
    throughput_target_percent: int,
    speed_tier: int = 1,
) -> ExteriorConnectionPlan:
    cap_res = resolve_per_connector_capacity(resource_kind=resource_kind, speed_tier=speed_tier)
    if cap_res.shortfall_reason is not None or cap_res.capacity_per_min is None:
        return _empty_plan(
            complete_map=complete_map,
            resource_kind=resource_kind,
            terrain_upper_bound_per_min=terrain_upper_bound_per_min,
            throughput_target_percent=throughput_target_percent,
            unmet_reason=cap_res.shortfall_reason,
        )
    planning_target = terrain_upper_bound_per_min * Decimal(throughput_target_percent) / Decimal(100)
    required = ceildiv_decimal(planning_target, cap_res.capacity_per_min)
    edge_slots = build_candidate_slots_by_edge(complete_map)
    if sum(len(s) for s in edge_slots.values()) < required:
        return _empty_plan(
            complete_map=complete_map,
            resource_kind=resource_kind,
            terrain_upper_bound_per_min=terrain_upper_bound_per_min,
            throughput_target_percent=throughput_target_percent,
            unmet_reason=ExteriorConnectionShortfallReason.NO_FEASIBLE_CONNECTOR_SITES,
            required_connector_count=required,
            per_connector_capacity_per_min=cap_res.capacity_per_min,
        )
    counts = distribute_connector_counts(required, edge_slots)
    connectors: list[ExteriorConnector] = []
    seq = 0
    for edge in (CardinalEdge.NORTH, CardinalEdge.EAST, CardinalEdge.SOUTH, CardinalEdge.WEST):
        chosen = choose_even_slots(edge_slots[edge], counts[edge])
        for void_coord in chosen:
            connectors.append(
                ExteriorConnector(
                    connector_id=f"ext_conn_{seq:02d}",
                    void_coord=void_coord,
                    edge=edge,
                    layout_t=default_exterior_connector_layout_t(resource_kind=resource_kind),
                    rotation=FIELDWARD_ROTATION_BY_EDGE[edge],
                    capacity_per_min=cap_res.capacity_per_min,
                    coords=(void_coord,),
                )
            )
            seq += 1
    return ExteriorConnectionPlan(
        transport_kind=resource_kind,
        terrain_upper_bound_per_min=terrain_upper_bound_per_min,
        planning_target_per_min=planning_target,
        per_connector_capacity_per_min=cap_res.capacity_per_min,
        required_connector_count=required,
        planned_connectors=tuple(connectors),
        unmet_reason=None,
    )
```

Implement private `_empty_plan(...)` helper returning zero `planned_connectors` with populated metadata fields.

- [ ] **Step 3: Implement `wire.py`**

```python
def exterior_connector_plan_to_metrics_dict(plan: ExteriorConnectionPlan) -> dict[str, object]:
    counts_by_edge = {e.value: 0 for e in CardinalEdge}
    for conn in plan.planned_connectors:
        counts_by_edge[conn.edge.value] += 1
    return {
        "exterior_connector_plan": {
            "version": "exterior_connector_plan.v1",
            "slot_rule": plan.slot_rule,
            "placement_rule": plan.placement_rule,
            "rotation_rule": plan.rotation_rule,
            "rotation_convention": "R0_E_CW",
            "required_connector_count": plan.required_connector_count,
            "planned_connector_count": len(plan.planned_connectors),
            "counts_by_edge": counts_by_edge,
            "planned_connectors": [
                {
                    "connector_id": c.connector_id,
                    "void_coord": {"x": c.void_coord[0], "y": c.void_coord[1]},
                    "edge": c.edge.value,
                    "layout_t": c.layout_t,
                    "rotation": c.rotation,
                    "capacity_per_min": str(c.capacity_per_min),
                    "coords": [{"x": xy[0], "y": xy[1]} for xy in c.coords],
                }
                for c in plan.planned_connectors
            ],
            "unmet_reason": plan.unmet_reason.value if plan.unmet_reason else None,
        }
    }
```

- [ ] **Step 4: Run — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py -v
```

- [ ] **Step 5: Commit (when user requests)**

---

## Task 7 — Literal gate (AST-based)

**Files:**
- Create: `tests/unit/asteroid_lab/layers/test_layer_02_evtc_no_literals.py`

**Scope:** production modules only under `layer_02_exterior_transport/` (not tests).

**Hard-forbid** `ast.Constant` numeric values (int or float) in these files:

```text
capacity.py
plan.py
wire.py
layout_t.py
```

Forbidden values: `720`, `8640`, `2880`, `345600`, `12`, `48`

**Allowlist** (other L2 modules may use small integers freely):

```text
rotation.py   — 0, 1, 2, 3 only (plus no forbidden cap values)
slots.py      — VOID_DEPTH_MIN = 5; grid math integers allowed
placement.py  — no cap scan (distribution math only)
```

- [ ] **Step 1: Implement gate test**

```python
# tests/unit/asteroid_lab/layers/test_layer_02_evtc_no_literals.py
from __future__ import annotations

import ast
from pathlib import Path

import pytest

_L2_PKG = Path("django_apps/asteroid_lab/layers/layer_02_exterior_transport")
_FORBIDDEN_CAPS = frozenset({720, 8640, 2880, 345600, 12, 48})
_SCAN_FILES = ("capacity.py", "plan.py", "wire.py", "layout_t.py")


def _numeric_constants(path: Path) -> list[int | float]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: list[int | float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            out.append(node.value)
    return out


@pytest.mark.parametrize("filename", _SCAN_FILES)
def test_layer_02_cap_modules_have_no_forbidden_numeric_literals(filename: str) -> None:
    path = _L2_PKG / filename
    assert path.is_file(), f"missing {path}"
    nums = _numeric_constants(path)
    bad = [n for n in nums if n in _FORBIDDEN_CAPS]
    assert bad == [], f"{filename} contains forbidden cap literals: {bad}"


def test_rotation_py_only_rotation_integers() -> None:
    path = _L2_PKG / "rotation.py"
    nums = _numeric_constants(path)
    assert all(n in {0, 1, 2, 3} for n in nums)
```

- [ ] **Step 2: Run — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_evtc_no_literals.py -v
```

---

## Task 8 — Lab timeline enrichment

**Files:**
- Create: `django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py`
- Test: `tests/unit/asteroid_lab/test_lab_timeline_exterior_connector_enrichment.py`

Mirror `lab_timeline_rim_enrichment.py`:

- `copy.deepcopy` metrics / map_view when mutating
- `METRICS_KEY = "exterior_connector_plan"`
- Return `(frames, frozen_wire)`

- [ ] **Step 1: Failing tests**

```python
# tests/unit/asteroid_lab/test_lab_timeline_exterior_connector_enrichment.py
from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
    METRICS_KEY,
    enrich_lab_timeline_frames_with_exterior_connector_plan,
)


def _frame() -> dict:
    return {
        "frame_index": 0,
        "metrics": {},
        "map_view": {
            "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
            "overlay_cells": [],
            "cell_delta": [],
            "annotations": [],
            "bbox": {"min_x": 0, "min_y": -6, "max_x": 5, "max_y": 0},
        },
    }


def test_l2_frame_attaches_metrics_and_overlay() -> None:
    plan_wire = {
        "version": "exterior_connector_plan.v1",
        "planned_connectors": [
            {
                "connector_id": "ext_conn_00",
                "void_coord": {"x": 5, "y": -6},
                "edge": "north",
                "layout_t": "SpaceBelt_Forward",
                "rotation": 1,
                "coords": [{"x": 5, "y": -6}],
            }
        ],
    }
    frames = [_frame()]
    out, frozen = enrich_lab_timeline_frames_with_exterior_connector_plan(
        frames,
        plan_wire=plan_wire,
        l2_complete_frame_index=0,
    )
    assert METRICS_KEY in out[0]["metrics"]
    overlay = out[0]["map_view"]["overlay_cells"]
    assert any(c.get("overlay_role") == "planned_exterior_connector" for c in overlay)
    assert any(c.get("tile_type") == "SpaceBelt_Forward" for c in overlay)
    assert frozen is not None


def test_no_plan_wire_noop() -> None:
    frames = [_frame()]
    out, frozen = enrich_lab_timeline_frames_with_exterior_connector_plan(frames, plan_wire=None)
    assert out == frames
    assert frozen is None
```

- [ ] **Step 2: Implement enricher** — one overlay row per connector:

```python
{
    "x": void_x,
    "y": void_y,
    "overlay_role": "planned_exterior_connector",
    "tile_type": layout_t,
    "rotation": rotation,
    "connector_id": connector_id,
}
```

- [ ] **Step 3: Run — PASS**

---

## Task 9 — Lab payload hook (no-op safe)

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`
- Test: extend `tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py` or add narrow test module

**Master constraint (normative):**

```text
Current master has no SolverRun.solver_summary_json.
PR-2 hook reads only SolverRun.config_json and is no-op-safe.
Runtime persistence of exterior_connector_plan into config_json remains PR-2b.
```

- [ ] **Step 1: Add helper**

```python
# django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
from typing import Any

from django_apps.asteroid_lab.models import SolverRun


def _exterior_connector_plan_wire_for_run(run: SolverRun | None) -> dict[str, Any] | None:
    if run is None:
        return None

    config = dict(run.config_json or {})
    wire = config.get("exterior_connector_plan")
    if isinstance(wire, dict):
        return wire

    summary = config.get("solver_summary")
    if isinstance(summary, dict):
        nested = summary.get("exterior_connector_plan")
        if isinstance(nested, dict):
            return nested

    return None
```

Do **not** reference `run.solver_summary_json` or `hasattr(run, "solver_summary_json")`.

- [ ] **Step 2: After rim enrichment**

```python
serialized, frozen_rim_wire = enrich_lab_timeline_frames_with_terrain_rim(serialized)

plan_wire = _exterior_connector_plan_wire_for_run(run)
serialized, frozen_connector_wire = enrich_lab_timeline_frames_with_exterior_connector_plan(
    serialized,
    plan_wire=plan_wire,
)
# ... existing track metrics ...
if frozen_connector_wire is not None:
    metrics["frozen_exterior_connector_plan"] = frozen_connector_wire
```

- [ ] **Step 3: Unit tests**

```python
def test_exterior_connector_plan_wire_reads_config_json_top_level() -> None:
    run = SolverRun(config_json={"exterior_connector_plan": {"version": "exterior_connector_plan.v1"}})
    wire = _exterior_connector_plan_wire_for_run(run)
    assert wire is not None
    assert wire.get("version") == "exterior_connector_plan.v1"


def test_exterior_connector_plan_wire_reads_nested_solver_summary() -> None:
    run = SolverRun(
        config_json={
            "solver_summary": {"exterior_connector_plan": {"planned_connectors": []}},
        }
    )
    wire = _exterior_connector_plan_wire_for_run(run)
    assert isinstance(wire, dict)


def test_exterior_connector_plan_wire_none_when_run_missing() -> None:
    assert _exterior_connector_plan_wire_for_run(None) is None
```

- [ ] **Step 4: Commit (when user requests)**

```text
feat(lab): hook exterior connector plan from SolverRun.config_json
```

---

## Task 10 — Lab CSS + JS

**Files:**
- Modify: `assets/css/input.css`
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- Modify: `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py`

- [ ] **Step 1: CSS** `.lab-planned-exterior-connector` (white ring)

- [ ] **Step 2: JS**

```javascript
const LAB_EXTERIOR_CONNECTOR_ROLE = "planned_exterior_connector";
const LAB_EXTERIOR_CONNECTOR_METRICS_KEY = "exterior_connector_plan";
const LAB_FROZEN_EXTERIOR_CONNECTOR_PLAN_KEY = "frozen_exterior_connector_plan";
```

Resolve wire: per-frame metrics → `trackMetrics.frozen_exterior_connector_plan`. Apply overlay cells in replay render path (same hook region as terrain rim).

- [ ] **Step 3: UI string test**

- [ ] **Step 4: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py -v
```

---

## Task 11 — Integration gate

- [ ] **Step 1: Narrow pytest**

```powershell
python -m pytest `
  tests/unit/asteroid_lab/layers/test_layer_02_contracts.py `
  tests/unit/asteroid_lab/layers/test_layer_02_rotation.py `
  tests/unit/asteroid_lab/layers/test_layer_02_void_deep_slots.py `
  tests/unit/asteroid_lab/layers/test_layer_02_placement.py `
  tests/unit/asteroid_lab/layers/test_layer_02_capacity.py `
  tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py `
  tests/unit/asteroid_lab/layers/test_layer_02_evtc_no_literals.py `
  tests/unit/asteroid_lab/test_lab_timeline_exterior_connector_enrichment.py `
  tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py -v
```

- [ ] **Step 2: Ruff + mypy**

```powershell
python -m ruff check django_apps/asteroid_lab/layers/ django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py
python -m mypy django_apps/asteroid_lab/layers django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py
```

---

## Spec coverage self-review (v2.2)

| Spec requirement | Task |
|------------------|------|
| VOID_DEEP_SLOTS_V1 depth ≥5, BFS NESW | 3 |
| No nearest_field bucketing | 3 |
| EDGE_WEIGHTED_EVEN_SPACING_V1 | 4 |
| Half-up `even_slot_index` | 4 |
| FIELDWARD N→1,E→2,S→3,W→0 | 2 |
| layout_t base + rotation separate | 5, 6 |
| EVTC DB-derived caps, no L2 literals | 5, 7 |
| Metrics wire + frozen | 6, 8, 9 |
| Lab marker + sprite void_coord | 8, 10 |
| §4 tests | 3–10 |

**v2.1 EVTC alignment:** L2 `resolve_per_connector_capacity` uses master `space_belt_max_per_min_from_row` / `space_pipe_max_per_min_from_row`. If design spec later mandates per-building `space_belt_connector_capacity_per_min_from_row`, add a **game_data** helper in a separate PR and switch L2 adapter — do not assume it exists on master today.

---

## Execution handoff

**Plan v2.2 saved to** `docs/superpowers/plans/2026-05-28-layer-02-exterior-connector-placement.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session with executing-plans checkpoints  

**Which approach?**
