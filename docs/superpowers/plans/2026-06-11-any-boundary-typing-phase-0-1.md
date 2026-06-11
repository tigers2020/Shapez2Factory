# Any Boundary Typing — Phase 0/1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish typing governance aliases and tighten replay overlay wire contracts (dataclass semantic authority + TypedDict wire authority) without behavior change.

**Architecture:** Phase 0 adds `typing_boundary.py` and finalizes docs. Plan 1 introduces `ReplayOverlayCellWire` and converter return typing. Plan 2 types `timeline_serialization.py`. Plan 3 adds `EffectiveCellWire` with external converter while keeping `to_wire()` shim until call sites migrate.

**Tech Stack:** Python 3.12, `typing.TypedDict` / `TypeAlias` / `NotRequired`, pytest, mypy (replay package expansion later).

**Spec:** [`docs/superpowers/specs/2026-06-11-any-boundary-typing-design.md`](../specs/2026-06-11-any-boundary-typing-design.md)  
**Manual:** [`documents/ai/manuals/typing_contracts.md`](../../../documents/ai/manuals/typing_contracts.md)

**Verified paths (Phase 0 inventory):**

```text
django_apps/asteroid_lab/replay/effective_cell_view.py
django_apps/asteroid_lab/replay/overlay_wire_contract.py
django_apps/asteroid_lab/replay/timeline_serialization.py
tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py
```

---

## Plan 1 — Governance aliases + overlay wire TypedDict

**Deliverable:** `typing_boundary.py`, `replay_overlay_wire.py`, typed `overlay_cell_to_wire_dict`, passing overlay wire tests.

---

### Task 1: Add `typing_boundary.py`

**Files:**
- Create: `django_apps/asteroid_lab/typing_boundary.py`

- [ ] **Step 1: Create module with shared aliases**

```python
"""Shared typing aliases for Asteroid Lab wire boundaries."""

from __future__ import annotations

from typing import Any, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]

# typing_contracts: raw JSON before normalization only
RawJsonObject: TypeAlias = dict[str, Any]

__all__ = ["JsonScalar", "JsonValue", "RawJsonObject"]
```

- [ ] **Step 2: Verify import**

Run: `python -c "from django_apps.asteroid_lab.typing_boundary import JsonValue, RawJsonObject; print('ok')"`  
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add django_apps/asteroid_lab/typing_boundary.py
git commit -m "feat(asteroid-lab): add typing_boundary shared JSON aliases"
```

---

### Task 2: Add `ReplayOverlayCellWire` TypedDict

**Files:**
- Create: `django_apps/asteroid_lab/replay/replay_overlay_wire.py`
- Test: `tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py`

- [ ] **Step 1: Write failing test for required wire keys**

Add to `tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py`:

```python
from django_apps.asteroid_lab.replay.replay_overlay_wire import ReplayOverlayCellWire


def test_overlay_cell_wire_typed_dict_exports() -> None:
    """Wire type module is importable for converter return typing."""
    assert ReplayOverlayCellWire.__name__ == "ReplayOverlayCellWire"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py::test_overlay_cell_wire_typed_dict_exports -v`  
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create wire TypedDict (matches overlay_cell_to_wire_dict today)**

```python
"""Replay overlay cell wire shapes (JSON projection authority only)."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class ReplayOverlayCellWire(TypedDict):
    """One overlay cell row in replay timeline / transient overlay wire."""

    x: int
    y: int
    kind: str
    transport: str
    transport_kind: str
    output_transport_kind: str
    tile_type: str
    rotation: int
    layer: NotRequired[int]
    simulation: NotRequired[str]


__all__ = ["ReplayOverlayCellWire"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py::test_overlay_cell_wire_typed_dict_exports -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/replay/replay_overlay_wire.py tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py
git commit -m "feat(asteroid-lab): add ReplayOverlayCellWire TypedDict"
```

---

### Task 3: Tighten `overlay_cell_to_wire_dict` return type

**Files:**
- Modify: `django_apps/asteroid_lab/replay/overlay_wire_contract.py`
- Test: `tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py`

- [ ] **Step 1: Write failing test asserting dual transport keys**

Add to `test_overlay_wire_contract.py`:

```python
def test_overlay_cell_to_wire_dict_returns_dual_transport_keys() -> None:
    cell = build_routed_transport_overlay_cell(
        x=1,
        y=2,
        transport_kind="space_pipe",
        tile_id="SpacePipe_Straight",
        rotation=0,
    )
    row = overlay_cell_to_wire_dict(cell)
    assert row["transport"] == "space_pipe"
    assert row["transport_kind"] == "space_pipe"
    assert row["transport"] == row["transport_kind"]
    assert "z" not in row
```

- [ ] **Step 2: Run test — should pass on current code (documents contract)**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py::test_overlay_cell_to_wire_dict_returns_dual_transport_keys -v`  
Expected: PASS (baseline before type change)

- [ ] **Step 3: Update converter signature and annotation**

In `overlay_wire_contract.py`:

```python
from django_apps.asteroid_lab.replay.replay_overlay_wire import ReplayOverlayCellWire

def overlay_cell_to_wire_dict(cell: ReplayOverlayCell) -> ReplayOverlayCellWire:
    occupancy = str(cell.transport or OCCUPANCY_TRANSPORT_NONE)
    output = str(cell.output_transport_kind or OUTPUT_TRANSPORT_NONE)
    row: ReplayOverlayCellWire = {
        "x": int(cell.x),
        "y": int(cell.y),
        "kind": str(cell.kind),
        "transport": occupancy,
        "transport_kind": occupancy,
        "output_transport_kind": output,
        "tile_type": str(cell.tile_type),
        "rotation": int(cell.rotation),
    }
    if cell.layer is not None:
        row["layer"] = int(cell.layer)
    if cell.tile_type:
        simulation = simulation_for_tile_id(cell.tile_type)
        if simulation:
            row["simulation"] = simulation
    return enrich_replay_wire_row_with_layer(row)
```

Ensure `enrich_replay_wire_row_with_layer` return is compatible (cast or update its annotation if mypy complains).

- [ ] **Step 4: Run full overlay wire test module**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py -q`  
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/replay/overlay_wire_contract.py
git commit -m "feat(asteroid-lab): type overlay_cell_to_wire_dict as ReplayOverlayCellWire"
```

---

### Plan 1 validation gate

```bash
python -m pytest tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py -q
ruff check django_apps/asteroid_lab/typing_boundary.py django_apps/asteroid_lab/replay/replay_overlay_wire.py django_apps/asteroid_lab/replay/overlay_wire_contract.py
```

---

## Plan 2 — `timeline_serialization` TypedDict + adapter converter-only

**Deliverable:** Named wire TypedDicts for bbox/cell/overlay/frame; `lab_timeline_adapter.py` stops hand-building overlay dicts.

**Prerequisite:** Plan 1 merged.

---

### Task 4: `ReplayBBoxWire` and bbox converters

**Files:**
- Modify: `django_apps/asteroid_lab/replay/replay_overlay_wire.py` (or new `replay_timeline_wire.py`)
- Modify: `django_apps/asteroid_lab/replay/timeline_serialization.py`
- Test: `tests/unit/asteroid_lab/replay/test_replay_timeline_dto.py` (or existing timeline serialization tests)

- [ ] **Step 1: Add `ReplayBBoxWire` TypedDict**

```python
class ReplayBBoxWire(TypedDict):
    min_x: int
    min_y: int
    max_x: int
    max_y: int
```

- [ ] **Step 2: Change `replay_bbox_to_json_dict` → `replay_bbox_to_wire` returning `ReplayBBoxWire`**

Keep `replay_bbox_to_json_dict` as deprecated alias if external callers exist; grep first.

- [ ] **Step 3: Add round-trip test**

```python
def test_replay_bbox_wire_round_trip() -> None:
    from django_apps.asteroid_lab.replay.timeline_dtos import ReplayBBox
    from django_apps.asteroid_lab.replay.timeline_serialization import (
        replay_bbox_from_json_dict,
        replay_bbox_to_wire,
    )

    bbox = ReplayBBox(min_x=0, min_y=0, max_x=10, max_y=10)
    wire = replay_bbox_to_wire(bbox)
    assert wire == {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 10}
    assert replay_bbox_from_json_dict(wire) == bbox
```

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest tests/unit/asteroid_lab/replay/ -q -k bbox`  
Commit: `feat(asteroid-lab): add ReplayBBoxWire and typed bbox converter`

---

### Task 5: Overlay/cell wire types in serialization

**Files:**
- Modify: `django_apps/asteroid_lab/replay/timeline_serialization.py`
- Modify: `django_apps/asteroid_lab/replay/replay_overlay_wire.py`

- [ ] **Step 1: Replace `_cell_from_dict(data: dict[str, Any])` input with `Mapping[str, object]` at public boundary**

Validate inside; keep internal helpers typed.

- [ ] **Step 2: Add `replay_overlay_cell_from_wire(raw: Mapping[str, object]) -> ReplayOverlayCell`**

Reuse `_wire_kind`, `_wire_transport` helpers; reject invalid ints with `ReplayTimelineDeserializationError`.

- [ ] **Step 3: Add deserialize reject test**

```python
def test_replay_overlay_cell_from_wire_rejects_non_int_x() -> None:
    from django_apps.asteroid_lab.replay.timeline_serialization import (
        ReplayTimelineDeserializationError,
        replay_overlay_cell_from_wire,
    )

    with pytest.raises(ReplayTimelineDeserializationError, match="cell.x"):
        replay_overlay_cell_from_wire({"x": "bad", "y": 0})
```

- [ ] **Step 4: Run replay tests and commit**

Run: `python -m pytest tests/unit/asteroid_lab/replay/ -q`  
Commit: `feat(asteroid-lab): typed overlay cell deserialization for replay timeline`

---

### Task 6: `lab_timeline_adapter.py` converter-only migration

**Files:**
- Modify: `django_apps/asteroid_lab/replay/lab_timeline_adapter.py`
- Test: existing lab timeline / replay integration tests

- [ ] **Step 1: Grep for hand-built overlay dict literals**

Run: `rg '"overlay_cells"' django_apps/asteroid_lab/replay/lab_timeline_adapter.py`  
Run: `rg '\{"x":' django_apps/asteroid_lab/replay/lab_timeline_adapter.py`

- [ ] **Step 2: Replace each hand-built overlay row with `overlay_cell_to_wire_dict(cell)` or batch helper**

Do not change frame semantics — only construction path.

- [ ] **Step 3: Run regression bundle**

```bash
python -m pytest tests/unit/asteroid_lab/replay/ -q
python -m pytest tests/unit/asteroid_lab/test_lab_replay_sprite_paint_golden.py -q
```

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor(asteroid-lab): lab_timeline_adapter overlay wire via converter only"
```

---

### Plan 2 validation gate

```bash
python -m pytest tests/unit/asteroid_lab/replay/ -q
mypy django_apps/asteroid_lab/replay/timeline_serialization.py django_apps/asteroid_lab/replay/lab_timeline_adapter.py
```

---

## Plan 3 — `EffectiveCellWire` + external converter

**Deliverable:** `EffectiveCellWire` TypedDict, `effective_cell_to_wire()`, call sites migrated; `to_wire()` kept as shim delegating to converter (removal in follow-up PR).

**Prerequisite:** Plan 2 merged.

**Verified path:** `django_apps/asteroid_lab/replay/effective_cell_view.py`

---

### Task 7: `EffectiveCellWire` TypedDict

**Files:**
- Create: `django_apps/asteroid_lab/replay/effective_cell_wire.py`
- Test: `tests/unit/asteroid_lab/replay/test_effective_cell_view.py`

- [ ] **Step 1: Add wire TypedDict matching `to_wire()` output today**

```python
from typing import NotRequired, TypedDict


class EffectiveCellCoordWire(TypedDict):
    x: int
    y: int
    layer: int


class EffectiveCellTerrainWire(TypedDict):
    kind: str
    tile_type: str | None


class EffectiveCellOccupantWire(TypedDict):
    kind: str
    rotation: int | None


class EffectiveCellTransportWire(TypedDict):
    kind: str
    tile_id: str | None
    simulation: str | None


class EffectiveCellOutputWire(TypedDict):
    transport_kind: str


class EffectiveCellWire(TypedDict):
    frame_index: int | None
    coord: EffectiveCellCoordWire
    terrain: EffectiveCellTerrainWire
    occupant: EffectiveCellOccupantWire
    transport: EffectiveCellTransportWire
    output: EffectiveCellOutputWire
    sources: dict[str, object]
```

- [ ] **Step 2: Add converter function**

In same module or `effective_cell_view.py`:

```python
def effective_cell_to_wire(view: EffectiveCellView) -> EffectiveCellWire:
    return {
        "frame_index": view.frame_index,
        "coord": {"x": view.x, "y": view.y, "layer": view.layer},
        "terrain": {
            "kind": view.terrain_kind,
            "tile_type": view.terrain_tile_type,
        },
        "occupant": {
            "kind": view.occupant_kind,
            "rotation": view.occupant_rotation,
        },
        "transport": {
            "kind": view.transport_kind,
            "tile_id": view.transport_tile_id,
            "simulation": view.simulation,
        },
        "output": {"transport_kind": view.output_transport_kind},
        "sources": dict(view.sources),
    }
```

- [ ] **Step 3: Test converter matches `to_wire()`**

```python
def test_effective_cell_to_wire_matches_to_wire_shim() -> None:
    from django_apps.asteroid_lab.replay.effective_cell_view import (
        EffectiveCellView,
        effective_cell_to_wire,
    )

    view = EffectiveCellView(
        frame_index=0,
        x=1,
        y=2,
        layer=0,
        terrain_kind="void",
        terrain_tile_type=None,
        occupant_kind="",
        occupant_rotation=None,
        transport_kind="none",
        transport_tile_id=None,
        simulation=None,
        output_transport_kind="none",
    )
    assert effective_cell_to_wire(view) == view.to_wire()
```

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/replay/effective_cell_wire.py django_apps/asteroid_lab/replay/effective_cell_view.py tests/unit/asteroid_lab/replay/test_effective_cell_view.py
git commit -m "feat(asteroid-lab): add EffectiveCellWire and effective_cell_to_wire converter"
```

---

### Task 8: Migrate call sites (keep `to_wire()` shim)

**Files:**
- Modify: `tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py` (lines using `view.to_wire()`)
- Modify: `tests/unit/asteroid_lab/test_shape_belt_ui_wire_ban.py`
- Grep: `\.to_wire\(\)` under `django_apps/` and `tests/`

- [ ] **Step 1: Grep call sites**

Run: `rg '\.to_wire\(\)' django_apps tests`

- [ ] **Step 2: Replace production call sites with `effective_cell_to_wire(view)`**

- [ ] **Step 3: Change `EffectiveCellView.to_wire` to delegate**

```python
def to_wire(self) -> EffectiveCellWire:
    from django_apps.asteroid_lab.replay.effective_cell_wire import effective_cell_to_wire

    return effective_cell_to_wire(self)
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/unit/asteroid_lab/replay/test_effective_cell_view.py -q
python -m pytest tests/unit/asteroid_lab/test_shape_belt_ui_wire_ban.py -q
python -m pytest tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py -q
```

- [ ] **Step 5: Commit**

```bash
git commit -m "refactor(asteroid-lab): migrate effective cell wire emission to converter"
```

**Follow-up PR (not this plan):** remove `to_wire()` method after all call sites use `effective_cell_to_wire`.

---

### Plan 3 validation gate

```bash
python -m pytest tests/unit/asteroid_lab/replay/ tests/unit/asteroid_lab/test_shape_belt_ui_wire_ban.py -q
```

---

## Plan self-review (spec coverage)

| Spec requirement | Plan task |
|------------------|-----------|
| `typing_boundary.py` in `django_apps/asteroid_lab/` | Task 1 |
| `ReplayOverlayCellWire` + converter return type | Tasks 2–3 |
| `timeline_serialization` TypedDict + validate | Tasks 4–5 |
| `lab_timeline_adapter` converter-only | Task 6 |
| `EffectiveCellWire` two-step `to_wire` migration | Tasks 7–8 |
| Ban-test / mypy CI expansion | Deferred post Plan 3 |
| `solver_run_lab_summary` | Out of scope (Phase 2 per spec) |

No TBD placeholders in task steps.

---

## Execution handoff

**Plan saved to:** `docs/superpowers/plans/2026-06-11-any-boundary-typing-phase-0-1.md`

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per plan (1 → 2 → 3), review between plans  
2. **Inline Execution** — run Plan 1 tasks in this session with checkpoints before Plan 2

Which approach?
