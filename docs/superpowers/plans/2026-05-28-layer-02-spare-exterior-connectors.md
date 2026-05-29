# Layer 02 Spare Exterior Connectors — Implementation Plan (v1.2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Plan review (2026-05-28):** v1.1 — `planned_connector_count` semantics, partial spare, wire/overlay/JS `connector_role`, downstream migration.  
> **v1.2:** Mandatory partial-spare test (monkeypatch), `0%` spare-only contract + test, `run_success` as `required_planned >= required_connector_count`, role `strip().lower()` normalization.

**Goal:** Extend Layer 2 to place **required** connectors (target%) plus **spare** connectors up to **reference@100%** using a 2-pass slot algorithm, expose counts/roles on the metrics wire, and render spare candidates with a distinct Lab highlight—without changing L3+ routing or commit semantics.

**Architecture:** Add `ExteriorConnectorRole` and count fields on `ExteriorConnectionPlan`. `build_exterior_connection_plan` runs pass 1 (required) then pass 2 on **remaining** void slots (spare). Wire bumps to `exterior_connector_plan.v2` with `role` per connector. Lab enrichment keeps `overlay_role=planned_exterior_connector` and adds `connector_role`. JS applies white vs cyan highlight from wire SoT.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy `django_apps config src`, `Decimal`, `StrEnum`, Tailwind/input.css, `asteroid_miner_layout_lab.js`

**Spec:** [`2026-05-28-layer-02-spare-exterior-connectors-design.md`](../specs/2026-05-28-layer-02-spare-exterior-connectors-design.md)  
**Parent:** [`2026-05-28-layer-02-exterior-connector-placement-design.md`](../specs/2026-05-28-layer-02-exterior-connector-placement-design.md)

**Work classification:** contract change · implementation change · UI change

**Branch:** Dedicated feature branch / worktree recommended (e.g. `feat/l2-spare-exterior-connectors`)

---

## Out of scope (this plan)

```text
- L3 route probe preferring required over spare
- L5 commit / export filtering unconnected spare
- Changing required_connector_count sizing formula
- Using Lab overlay or replay metrics as solver input
```

```text
L2 spare connectors are visualization/planning candidates only.
They must not be exported, committed, or counted as connected capacity
unless a later layer creates an explicit route reservation.
```

**Follow-up (named):** `PR-L2c-route-spare-promotion` — L3/L5 consume `role` when implemented.

---

## Downstream semantics (normative — do not skip)

Pre-v2 code often equated `planned_connector_count` with “required connectors placed”. **v2 breaks that read.**

| Consumer | Before (v1 mental model) | After (v2) |
|----------|--------------------------|------------|
| `planned_connector_count` | ≈ required placed | **Total** on map = `required_planned_count + spare_planned_count` |
| “How many required belts placed?” | `planned_connector_count` | **`required_planned_count`** |
| “How many spare candidates on map?” | N/A | **`spare_planned_count`** |
| `run_success` / L2 frame title | `planned_connector_count > 0` | **`unmet_reason is None` and `required_planned_count >= required_connector_count`** (allows 0% target) |
| Lab card “Planned connectors” | total placed | Bind to **`planned_connector_count`**; show **“Required connectors”** (sizing) + **“Required planned”** (actual) |

**Files that must be audited in Task 8:**

- `django_apps/asteroid_lab/services/solver_runtime_layer02.py` — `run_success`, summary top-level counts
- `django_apps/asteroid_lab/services/solver_run_lab_summary.py` — L2 highlights (`Planned` vs `Required planned`)
- `django_apps/asteroid_lab/services/lab_layer02_timeline.py` — frame `description` text
- `django_apps/asteroid_lab/layers/layer_02_exterior_transport/wire.py` — `planned_connector_count` identity

**v1 wire reader fallback:** missing `role` / `*_planned_count` → treat all connectors as required (Lab enrichment + JS).

---

## File map

| Action | Path |
|--------|------|
| Create | `django_apps/asteroid_lab/layers/contracts/exterior_connector_role.py` |
| Modify | `django_apps/asteroid_lab/layers/contracts/exterior_connection.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_02_exterior_transport/placement.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_02_exterior_transport/plan.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_02_exterior_transport/wire.py` |
| Modify | `django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py` |
| Modify | `django_apps/asteroid_lab/services/solver_run_lab_summary.py` |
| Modify | `assets/css/input.css` |
| Modify | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_02_contracts.py` |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py` |
| Create | `tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py` |
| Modify | `tests/unit/asteroid_lab/test_lab_timeline_exterior_connector_enrichment.py` |
| Modify | `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` |
| Modify | `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` (if L2 highlight labels asserted) |
| Build | `npm run build:css` (after `input.css` change) |

---

### Task 1: Contract — `ExteriorConnectorRole` + plan fields

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/exterior_connector_role.py`
- Modify: `django_apps/asteroid_lab/layers/contracts/exterior_connection.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_02_contracts.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/asteroid_lab/layers/test_layer_02_contracts.py`:

```python
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)


def test_exterior_connector_role_wire_slugs() -> None:
    assert ExteriorConnectorRole.REQUIRED.value == "required"
    assert ExteriorConnectorRole.SPARE.value == "spare"


def test_exterior_connector_requires_role() -> None:
    conn = ExteriorConnector(
        connector_id="ext_conn_00",
        void_coord=(1, -5),
        edge=CardinalEdge.NORTH,
        layout_t="SpaceBelt_Forward",
        rotation=1,
        capacity_per_min=Decimal("8640"),
        coords=((1, -5),),
        role=ExteriorConnectorRole.REQUIRED,
    )
    assert conn.role is ExteriorConnectorRole.REQUIRED


def test_exterior_connection_plan_reference_and_spare_counts() -> None:
    plan = ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        planning_target_per_min=Decimal("5000"),
        per_connector_capacity_per_min=Decimal("1000"),
        required_connector_count=5,
        reference_connector_count=10,
        spare_connector_count=5,
        planned_connectors=(),
        unmet_reason=None,
    )
    assert plan.reference_connector_count == 10
    assert plan.spare_connector_count == 5
```

Update existing `test_exterior_connector_coords_singleton` to pass `role=ExteriorConnectorRole.REQUIRED`.

Update existing `test_exterior_connection_plan_default_rules` to include `reference_connector_count=0`, `spare_connector_count=0`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_contracts.py -v`  
Expected: FAIL (`ExteriorConnectorRole` missing / `ExteriorConnector` unexpected keyword `role`)

- [ ] **Step 3: Write minimal implementation**

`django_apps/asteroid_lab/layers/contracts/exterior_connector_role.py`:

```python
"""Layer 02 exterior connector role (required vs spare)."""

from __future__ import annotations

from enum import StrEnum


class ExteriorConnectorRole(StrEnum):
    REQUIRED = "required"
    SPARE = "spare"


__all__ = ["ExteriorConnectorRole"]
```

`exterior_connection.py` — import role; extend dataclasses:

```python
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)

@dataclass(frozen=True, slots=True)
class ExteriorConnector:
    ...
    role: ExteriorConnectorRole

@dataclass(frozen=True, slots=True)
class ExteriorConnectionPlan:
    ...
    required_connector_count: int
    reference_connector_count: int
    spare_connector_count: int
    planned_connectors: tuple[ExteriorConnector, ...]
    ...
```

Export `ExteriorConnectorRole` from `exterior_connection.py` `__all__` if that module re-exports contracts.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_contracts.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/layers/contracts/exterior_connector_role.py \
  django_apps/asteroid_lab/layers/contracts/exterior_connection.py \
  tests/unit/asteroid_lab/layers/test_layer_02_contracts.py
git commit -m "feat(l2): add exterior connector role and reference counts"
```

---

### Task 2: Placement helper — remaining slots after pass 1

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/placement.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_02_placement.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/asteroid_lab/layers/test_layer_02_placement.py`:

```python
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.placement import (
    remaining_slots_after_selection,
)


def test_remaining_slots_excludes_used_coords() -> None:
    edge_slots = {
        CardinalEdge.NORTH: [(0, -5), (1, -5), (2, -5)],
        CardinalEdge.EAST: [(5, 0)],
        CardinalEdge.SOUTH: [],
        CardinalEdge.WEST: [],
    }
    used = {(1, -5)}
    remaining = remaining_slots_after_selection(edge_slots, used)
    assert (1, -5) not in remaining[CardinalEdge.NORTH]
    assert len(remaining[CardinalEdge.NORTH]) == 2
    assert remaining[CardinalEdge.EAST] == [(5, 0)]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_placement.py::test_remaining_slots_excludes_used_coords -v`  
Expected: FAIL (`remaining_slots_after_selection` not defined)

- [ ] **Step 3: Write minimal implementation**

In `placement.py`:

```python
def remaining_slots_after_selection(
    edge_slots: dict[CardinalEdge, list[Coord]],
    used: set[Coord],
) -> dict[CardinalEdge, list[Coord]]:
    return {
        edge: [coord for coord in slots if coord not in used]
        for edge, slots in edge_slots.items()
    }
```

Add to `__all__`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_placement.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/layers/layer_02_exterior_transport/placement.py \
  tests/unit/asteroid_lab/layers/test_layer_02_placement.py
git commit -m "feat(l2): remaining slot map after connector selection"
```

---

### Task 3: Plan builder — 2-pass required + spare

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/plan.py`
- Modify: `tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py`

- [ ] **Step 1: Write the failing tests**

`tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py`:

```python
"""Layer 02 spare (reference@100%) connector placement."""

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)


@pytest.mark.django_db
def test_spare_count_zero_when_target_percent_100() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=100,
        speed_tier=1,
    )
    assert plan.unmet_reason is None
    assert plan.spare_connector_count == 0
    assert plan.reference_connector_count == plan.required_connector_count
    assert all(c.role is ExteriorConnectorRole.REQUIRED for c in plan.planned_connectors)


@pytest.mark.django_db
def test_spare_positive_when_target_below_100() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=50,
        speed_tier=1,
    )
    assert plan.unmet_reason is None
    assert plan.reference_connector_count > plan.required_connector_count
    assert plan.spare_connector_count == (
        plan.reference_connector_count - plan.required_connector_count
    )
    required_rows = [c for c in plan.planned_connectors if c.role is ExteriorConnectorRole.REQUIRED]
    spare_rows = [c for c in plan.planned_connectors if c.role is ExteriorConnectorRole.SPARE]
    assert len(required_rows) == plan.required_connector_count
    assert len(spare_rows) <= plan.spare_connector_count
    assert len(plan.planned_connectors) == len(required_rows) + len(spare_rows)


@pytest.mark.django_db
def test_required_and_spare_void_coords_disjoint() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=50,
        speed_tier=1,
    )
    coords = [c.void_coord for c in plan.planned_connectors]
    assert len(coords) == len(set(coords))


@pytest.mark.django_db
def test_partial_spare_placement_is_success_when_required_slots_fit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Forces total_slots < reference so partial spare is always exercised (no conditional skip)."""
    from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
    from django_apps.asteroid_lab.layers.layer_02_exterior_transport import plan as plan_mod

    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    fake_slots = {
        CardinalEdge.NORTH: [(0, -12), (5, -12), (10, -12)],
        CardinalEdge.EAST: [(22, 5), (22, 10)],
        CardinalEdge.SOUTH: [],
        CardinalEdge.WEST: [],
    }
    monkeypatch.setattr(
        plan_mod,
        "build_candidate_slots_by_edge",
        lambda _cm: fake_slots,
    )
    total_slots = 5

    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("40000"),
        throughput_target_percent=50,
        speed_tier=1,
    )
    required_planned = sum(
        1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.REQUIRED
    )
    spare_planned = sum(
        1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.SPARE
    )

    assert plan.unmet_reason is None
    assert plan.spare_connector_count > 0
    assert total_slots >= plan.required_connector_count
    assert total_slots < plan.reference_connector_count
    assert required_planned == plan.required_connector_count
    assert spare_planned < plan.spare_connector_count


@pytest.mark.django_db
def test_zero_target_places_only_spare_reference_markers() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=0,
        speed_tier=1,
    )
    assert plan.unmet_reason is None
    assert plan.required_connector_count == 0
    assert plan.spare_connector_count == plan.reference_connector_count
    assert plan.planned_connectors
    assert all(c.role is ExteriorConnectorRole.SPARE for c in plan.planned_connectors)
```

**Note:** If `test_partial_spare_*` fails on `reference`/`required` counts after EVTC DB seed changes, adjust `terrain_upper_bound_per_min` using live `resolve_per_connector_capacity` — keep `total_slots=5` via monkeypatch and preserve the three slot inequalities above.

Update `test_required_connectors_uses_evtc_ceildiv_shape` in `test_layer_02_exterior_connection_plan.py`:

```python
assert len(plan.planned_connectors) == plan.reference_connector_count
assert plan.reference_connector_count >= plan.required_connector_count
```

(At 100% target, `reference == required` so length still matches both.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py -v`  
Expected: FAIL (`spare_connector_count` missing or wrong)

- [ ] **Step 3: Write minimal implementation**

In `plan.py`:

1. Import `ExteriorConnectorRole`, `remaining_slots_after_selection`.
2. After resolving `cap_res.capacity_per_min`:

```python
reference = ceildiv_decimal(terrain_upper_bound_per_min, cap_res.capacity_per_min)
required = ceildiv_decimal(planning_target, cap_res.capacity_per_min)
spare = max(0, reference - required)
```

3. Fail-closed when `total_slots < required` (unchanged); populate `reference_connector_count`, `spare_connector_count` on all return paths in `_empty_plan`.
4. Pass 1: existing loop with `role=ExteriorConnectorRole.REQUIRED` — when `required == 0`, loop body runs zero times (valid).
5. Build `used = {c.void_coord for c in connectors}`.
6. Pass 2 when `spare > 0`:

```python
remaining = remaining_slots_after_selection(edge_slots, used)
remaining_total = sum(len(s) for s in remaining.values())
spare_to_place = min(spare, remaining_total)
if spare_to_place > 0:
    spare_counts = distribute_connector_counts(spare_to_place, remaining)
    for edge in _EDGES_ORDER:
        chosen = choose_even_slots(remaining[edge], spare_counts[edge])
        for void_coord in chosen:
            connectors.append(
                ExteriorConnector(
                    ...,
                    role=ExteriorConnectorRole.SPARE,
                )
            )
            seq += 1
```

7. Return plan with `reference_connector_count=reference`, `spare_connector_count=spare`.

Update `_empty_plan` signature and all call sites to pass `reference_connector_count` and `spare_connector_count` (use `reference`/`spare` locals or `0`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/layers/layer_02_exterior_transport/plan.py \
  tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py \
  tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py
git commit -m "feat(l2): 2-pass required and spare exterior connector placement"
```

---

### Task 4: Metrics wire v2

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/wire.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py` (wire section)

- [ ] **Step 1: Write the failing test**

Append to `test_layer_02_spare_connectors.py`:

```python
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)


@pytest.mark.django_db
def test_wire_v2_includes_role_and_reference_counts() -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        throughput_target_percent=50,
        speed_tier=1,
    )
    wire = exterior_connector_plan_to_metrics_dict(plan)["exterior_connector_plan"]
    assert wire["version"] == "exterior_connector_plan.v2"
    assert wire["reference_connector_count"] == plan.reference_connector_count
    assert wire["spare_connector_count"] == plan.spare_connector_count
    required_planned = sum(
        1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.REQUIRED
    )
    spare_planned = sum(
        1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.SPARE
    )
    assert wire["required_planned_count"] == required_planned
    assert wire["spare_planned_count"] == spare_planned
    assert wire["planned_connector_count"] == required_planned + spare_planned
    assert wire["planned_connector_count"] == len(plan.planned_connectors)
    roles = {row["role"] for row in wire["planned_connectors"]}
    assert roles <= {"required", "spare"}
```

Update `test_wire_uses_lowercase_edge_slug` to expect `version == exterior_connector_plan.v2` and each connector has `"role"`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py::test_wire_v2_includes_role_and_reference_counts -v`  
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

In `wire.py`:

```python
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)

required_planned = sum(
    1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.REQUIRED
)
spare_planned = sum(
    1 for c in plan.planned_connectors if c.role is ExteriorConnectorRole.SPARE
)

return {
    "exterior_connector_plan": {
        "version": "exterior_connector_plan.v2",
        ...
        "required_connector_count": plan.required_connector_count,
        "reference_connector_count": plan.reference_connector_count,
        "spare_connector_count": plan.spare_connector_count,
        "required_planned_count": required_planned,
        "spare_planned_count": spare_planned,
        "planned_connector_count": required_planned + spare_planned,
        "planned_connectors": [
            {
                ...
                "role": c.role.value,
            }
            for c in plan.planned_connectors
        ],
    }
}
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/layers/layer_02_exterior_transport/wire.py \
  tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py \
  tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py
git commit -m "feat(l2): exterior connector plan wire v2 with roles"
```

---

### Task 5: Lab overlay enrichment — `connector_role`

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py`
- Modify: `tests/unit/asteroid_lab/test_lab_timeline_exterior_connector_enrichment.py`

- [ ] **Step 1: Write the failing test**

```python
def test_overlay_includes_connector_role_spare() -> None:
    plan_wire = {
        "version": "exterior_connector_plan.v2",
        "planned_connectors": [
            {
                "connector_id": "ext_conn_09",
                "void_coord": {"x": 3, "y": -6},
                "edge": "north",
                "layout_t": "SpaceBelt_Forward",
                "rotation": 1,
                "role": "spare",
                "coords": [{"x": 3, "y": -6}],
            }
        ],
    }
    ...
    assert at[0].get("connector_role") == "spare"
    assert at[0].get("overlay_role") == "planned_exterior_connector"
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_timeline_exterior_connector_enrichment.py::test_overlay_includes_connector_role_spare -v`

- [ ] **Step 3: Implementation**

In `_planned_connectors`, normalize role (v1 wire / legacy safe):

```python
role = str(item.get("role") or "required").strip().lower()
if role not in {"required", "spare"}:
    role = "required"
...
{
    ...
    "overlay_role": OVERLAY_ROLE,
    "connector_role": role,
}
```

Add test `test_overlay_unknown_role_normalizes_to_required`:

```python
def test_overlay_unknown_role_normalizes_to_required() -> None:
    plan_wire = {
        "version": "exterior_connector_plan.v2",
        "planned_connectors": [
            {
                "connector_id": "ext_conn_00",
                "void_coord": {"x": 5, "y": -6},
                "role": "future",
                "layout_t": "SpaceBelt_Forward",
                "rotation": 1,
                "coords": [{"x": 5, "y": -6}],
            }
        ],
    }
    out, _ = enrich_lab_timeline_frames_with_exterior_connector_plan(
        [_frame()], plan_wire=plan_wire, l2_complete_frame_index=0,
    )
    overlay = out[0]["map_view"]["overlay_cells"]
    assert overlay[0].get("connector_role") == "required"
```

- [ ] **Step 4: Run enrichment tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_timeline_exterior_connector_enrichment.py tests/unit/asteroid_lab/test_lab_layer02_timeline.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py \
  tests/unit/asteroid_lab/test_lab_timeline_exterior_connector_enrichment.py
git commit -m "feat(lab): pass connector_role on L2 exterior overlay"
```

---

### Task 6: Lab JS + CSS — spare highlight

**Files:**
- Modify: `assets/css/input.css`
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- Modify: `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py`
- Shell: `npm run build:css`

- [ ] **Step 1: Write the failing UI contract test**

In `test_asteroid_lab_ui_strings.py` → `test_lab_exterior_connector_overlay_contract`:

```python
assert "lab-planned-exterior-connector-spare" in css
assert "applyPlannedExteriorConnectorSpareHighlight" in js
assert "connector_role" in js
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py::test_lab_exterior_connector_overlay_contract -v`

- [ ] **Step 3: CSS** (`input.css` after required block)

```css
  .lab-planned-exterior-connector-spare {
    z-index: 2;
    box-shadow: inset 0 0 0 2px rgba(34, 211, 238, 0.92);
    background-color: rgba(34, 211, 238, 0.14);
  }
```

- [ ] **Step 4: JS changes** (`asteroid_miner_layout_lab.js`)

1. **`plannedConnectorCellsFromWire`** — include role from wire:

```javascript
connector_role: item.role != null ? String(item.role) : "required",
```

2. **`overlayCellsFromMapView`** — preserve `connector_role` on mapped rows (fallback path when wire absent):

```javascript
if (c.connector_role != null && String(c.connector_role) !== "") {
  row.connector_role = String(c.connector_role);
}
```

3. Add **`applyPlannedExteriorConnectorSpareHighlight(el)`** (cyan inset; mirror white helper). **Keep both CSS class and inline helper** (same pattern as required).

4. **`renderPlannedExteriorConnectorHighlights`** — normalize unknown role to required; branch highlight:

```javascript
function normalizeConnectorRole(raw) {
  const role = String(raw || "required").trim().toLowerCase();
  return role === "spare" ? "spare" : "required";
}

// inside loop:
const role = normalizeConnectorRole(cell.connector_role);
if (role === "spare") {
  el.className = LAB_CELL_BASE + " lab-planned-exterior-connector-spare";
  applyPlannedExteriorConnectorSpareHighlight(el);
} else {
  el.className = LAB_CELL_BASE + " lab-planned-exterior-connector";
  applyPlannedExteriorConnectorWhiteHighlight(el);
}
```

5. **`overlayToneClasses` / `toneForFullMapCell`** — if `normalizeConnectorRole(cell.connector_role) === "spare"`, return spare class.

- [ ] **Step 5: Build CSS**

Run: `npm run build:css`  
Expected: `django_apps/web/static/web/css/app.css` contains `lab-planned-exterior-connector-spare`

- [ ] **Step 6: Run UI contract test**

Run: `python -m pytest tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py::test_lab_exterior_connector_overlay_contract -v`  
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add assets/css/input.css django_apps/web/static/web/js/asteroid_miner_layout_lab.js \
  django_apps/web/static/web/css/app.css tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py
git commit -m "feat(lab): cyan highlight for spare exterior connectors"
```

---

### Task 7: Lab summary highlights

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- Modify: `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` (if present)

- [ ] **Step 1: Add highlights in L2 layer card**

When `l2_plan` is dict, **do not** relabel `Planned connectors` to mean required-only. Bind explicitly:

```python
_highlight("Required connectors", l2_plan.get("required_connector_count", _PLACEHOLDER)),
_highlight("Required planned", l2_plan.get("required_planned_count", _PLACEHOLDER)),
_highlight("Planned connectors", l2_plan.get("planned_connector_count", _PLACEHOLDER)),
_highlight("Reference connectors", l2_plan.get("reference_connector_count", _PLACEHOLDER)),
_highlight("Spare connectors", l2_plan.get("spare_connector_count", _PLACEHOLDER)),
_highlight("Spare planned", l2_plan.get("spare_planned_count", _PLACEHOLDER)),
```

Keep **Reference belts @100% terrain** on `capacity.external_connector_count` (EVTC observability). When v2 plan wire exists, add test assertion: `reference_connector_count == external_connector_count` for shape primary fixtures.

**v1 plan wire fallback:** if `required_planned_count` absent, use `planned_connector_count` for `Required planned` display only.

- [ ] **Step 2: Extend test**

If `test_solver_run_lab_summary` lists L2 labels, assert `"Reference connectors"` and `"Spare connectors"` appear when plan wire includes v2 fields.

- [ ] **Step 3: Run**

Run: `python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/services/solver_run_lab_summary.py \
  tests/unit/asteroid_lab/test_solver_run_lab_summary.py
git commit -m "feat(lab): show L2 reference and spare connector counts"
```

---

### Task 8: Fix downstream constructors and runtime tests

**Files:** Grep-driven — any `ExteriorConnector(` / `ExteriorConnectionPlan(` without new fields.

- [ ] **Step 1: Grep and fix**

Run: `rg "ExteriorConnector\(" django_apps tests`  
Run: `rg "ExteriorConnectionPlan\(" django_apps tests`

Add `role=...` and `reference_connector_count` / `spare_connector_count` to each callsite.

Likely files:
- `tests/unit/asteroid_lab/layers/test_layer_02_contracts.py` (done in Task 1)
- `tests/unit/asteroid_lab/test_lab_layer02_timeline.py` — sample wire may need `"role": "required"`
- `django_apps/asteroid_lab/services/solver_runtime_layer02.py`:

```python
required_connector_count = int(plan_wire.get("required_connector_count") or 0)
required_planned = int(plan_wire.get("required_planned_count") or 0)
planned_total = int(plan_wire.get("planned_connector_count") or len(plan.planned_connectors))
run_success = (
    unmet_reason is None
    and required_planned >= required_connector_count
)
# summary: planned_connector_count=planned_total; 0% target => required_planned==0 is success
```

- `django_apps/asteroid_lab/services/lab_layer02_timeline.py` — description: `Planned {planned_connector_count} exterior connector(s) ({required_planned_count} required, {spare_planned_count} spare)`

- [ ] **Step 2: Run broad L2 slice**

Run: `python -m pytest tests/unit/asteroid_lab/layers/ tests/unit/asteroid_lab/test_lab_layer02_timeline.py tests/unit/asteroid_lab/test_solver_runtime_entry_layer02.py tests/unit/asteroid_lab/test_lab_replay_exterior_connector_wire.py -v`  
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore(l2): fix callsites for spare connector contract"
```

---

### Task 9: Lint, typecheck, docs sync

- [ ] **Step 1: Ruff on touched paths**

Run: `python -m ruff check django_apps/asteroid_lab/layers/ django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py django_apps/asteroid_lab/services/solver_run_lab_summary.py tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py`

- [ ] **Step 2: Mypy**

Run: `python -m mypy django_apps/asteroid_lab/layers/contracts/exterior_connection.py django_apps/asteroid_lab/layers/layer_02_exterior_transport/plan.py django_apps/asteroid_lab/layers/layer_02_exterior_transport/wire.py`

- [ ] **Step 3: Amend parent placement spec cross-link**

In `docs/superpowers/specs/2026-05-28-layer-02-exterior-connector-placement-design.md` §3.4 metrics example, add one line:

```text
See spare/reference extension: 2026-05-28-layer-02-spare-exterior-connectors-design.md
```

- [ ] **Step 4: Update `documents/ai/current_plan.md`**

Add active line for this track (do not mark CLOSED until PR merged).

---

## Plan self-review

| Spec requirement | Task |
|------------------|------|
| Count formulas A | Task 3 |
| 2-pass placement | Task 2, 3 |
| Partial spare success (mandatory) | Task 3 (`test_partial_spare_placement_*` + monkeypatch) |
| Zero % spare-only | Task 3 (`test_zero_target_places_only_spare_reference_markers`) |
| `run_success` >= required sizing | Task 8 |
| `planned_connector_count` = required_planned + spare_planned | Task 4 wire + Downstream § |
| `required_planned_count` from roles (not sizing alone) | Task 4 test |
| `ExteriorConnectorRole` | Task 1 |
| Wire v2 + role; v1 reader fallback | Task 4, 5, 6, Downstream § |
| Lab overlay `connector_role` + unknown → required | Task 5 |
| JS wire + overlay fallback `connector_role` | Task 6 |
| Spare cyan CSS + inline helper | Task 6 |
| Summary + runtime downstream | Task 7, 8 |
| Spare not export/commit | Out of scope + spec §6 |
| L3/L5 exclusion deferred | Out of scope |
| No solver input from overlay | Normative in spec; no Task violates |

**Architect feedback (2026-05-28) — addressed:**

1. `planned_connector_count` semantics → Downstream § + Task 4/7/8  
2. Partial spare test (mandatory, monkeypatch) → Task 3  
3. Wire `required_planned_count` from roles; `spare_planned` by SPARE role → Task 4  
4. Role `strip().lower()` normalization → Task 5, 6  
5. JS `overlayCellsFromMapView` + wire SoT → Task 6  
6. CSS + inline dual path → Task 6  
7. Stronger spare-not-committed wording → spec §6 + plan Out of scope  
8. Zero % spare-only → spec §2.2 + Task 3  
9. `run_success` = `required_planned >= required_connector_count` → Downstream § + Task 8  

**Placeholder scan:** None (all steps name concrete paths and code).

**Type consistency:** `role` / `connector_role` on DTO, wire, overlay, JS all use `required` | `spare` (unknown → `required`).

---

## Verification (iteration gate)

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py::test_partial_spare_placement_is_success_when_required_slots_fit \
  tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py::test_zero_target_places_only_spare_reference_markers \
  tests/unit/asteroid_lab/layers/test_layer_02_spare_connectors.py \
  tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py \
  tests/unit/asteroid_lab/layers/test_layer_02_placement.py \
  tests/unit/asteroid_lab/layers/test_layer_02_contracts.py \
  tests/unit/asteroid_lab/test_lab_timeline_exterior_connector_enrichment.py \
  tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py::test_lab_exterior_connector_overlay_contract \
  -v
python -m ruff check django_apps/asteroid_lab/layers/ django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py
```

**PR full gate (before merge):** `powershell -File scripts/test_full.ps1` → `ruff check .` → `mypy django_apps config src` → `black --check .` → `python -m pytest`

---

## Execution handoff

**Status:** v1.2 — **approved for implementation** (Solver Contract Architect, 2026-05-28).

Plan: `docs/superpowers/plans/2026-05-28-layer-02-spare-exterior-connectors.md`  
Spec: `docs/superpowers/specs/2026-05-28-layer-02-spare-exterior-connectors-design.md`

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with executing-plans checkpoints  

Which approach do you want?
