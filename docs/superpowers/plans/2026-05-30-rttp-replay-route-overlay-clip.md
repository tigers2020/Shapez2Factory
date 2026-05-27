# RTTP Replay Route Overlay Clip — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Lab RTTP commit replay so committed route / FOT / stub overlays survive compose clip while equipment stays anchor-only.

**Architecture:** Equipment → **anchor-only** clip (`lab_anchors`). Transport/route → **dynamic replay render envelope** (`lab_render_bbox` = projected `full_cells` ∪ projected raw overlay, pre-clip) ∩ `known_route_render_domain`. Helpers: `is_transport_or_route_overlay_row`, `project_overlay_coord_to_lab_xy`, `build_lab_render_bbox`, `build_known_route_render_domain` (projected lab coords; no leave-one-out). No solver changes.

**Plan rev2 (2026-05-30):** Removed leave-one-out; unified projected coord frame; deferred stray-route test.

**Plan rev3 (2026-05-30):** `lab_render_bbox` = **dynamic render envelope** (not fixed island bbox); exterior void routes expand envelope; renamed primary survival test.

**Tech Stack:** Python 3.12+, Django `asteroid_lab`, pytest, ruff.

**Spec:** [`../specs/2026-05-30-rttp-replay-route-overlay-clip-design.md`](../specs/2026-05-30-rttp-replay-route-overlay-clip-design.md) (Status: APPROVED, plan rev2 aligned)

**Classification:** contract change · implementation change (replay projection-only)

**Suggested branch:** `fix/rttp-replay-route-overlay-clip`

---

## File map

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py` | Classification helper, bbox/domain builders, dual-channel clip |
| `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py` | Normative clip tests + update existing clip tests |
| `documents/ai/lab_map_rendering_contract.md` | One paragraph cross-link (optional Task 5) |

---

### Task 1: Classification helper + domain/bbox pure functions

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py`
- Test: `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py`

- [ ] **Step 1: Write failing tests for helper and bbox/domain builders**

Add to `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py`:

```python
from django_apps.asteroid_lab.services.lab_rttp_snapshot_compose import (
    build_known_route_render_domain,
    build_lab_render_bbox,
    coord_in_bbox,
    is_transport_or_route_overlay_row,
    project_overlay_coord_to_lab_xy,
)


def test_clip_helper_classifies_fot_and_output_stub_as_transport_route() -> None:
    fot = {
        "x": 1,
        "y": 0,
        "kind": "placement.confirmed_fixed_output_transport",
        "cell_kind": "space_belt",
        "overlay_semantic_kind": "placement.confirmed_fixed_output_transport",
    }
    stub = {
        "x": 2,
        "y": 0,
        "kind": "placement.confirmed_output_stub",
        "cell_kind": "space_belt",
        "overlay_semantic_kind": "placement.confirmed_output_stub",
    }
    assert is_transport_or_route_overlay_row(fot) is True
    assert is_transport_or_route_overlay_row(stub) is True


def test_clip_helper_rejects_shape_miner_equipment() -> None:
    row = {
        "x": 0,
        "y": 0,
        "kind": "placement.confirmed_extractor",
        "cell_kind": "shape_miner",
    }
    assert is_transport_or_route_overlay_row(row) is False


def test_project_overlay_coord_identity_when_in_anchors() -> None:
    anchors = frozenset({(0, 0)})
    assert project_overlay_coord_to_lab_xy(0, 0, anchors) == (0, 0)


def test_lab_render_bbox_uses_projected_overlay_before_clip() -> None:
    base_mv = {
        "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
        "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
    }
    anchors = frozenset({(0, 0)})
    raw = [
        {"x": 0, "y": 0, "kind": "placement.confirmed_extractor", "cell_kind": "shape_miner"},
        {"x": 9, "y": 0, "kind": "route.committed_path", "cell_kind": "space_belt"},
    ]
    bbox = build_lab_render_bbox(base_mv, raw, anchors)
    lab_xy = project_overlay_coord_to_lab_xy(9, 0, anchors)
    assert bbox is not None
    assert coord_in_bbox(lab_xy, bbox) is True


def test_known_route_render_domain_unions_projected_full_cells_and_transport() -> None:
    base_mv = {
        "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
    }
    anchors = frozenset({(0, 0)})
    raw = [
        {"x": 0, "y": 1, "kind": "route.committed_path", "cell_kind": "space_belt"},
        {"x": 0, "y": 2, "kind": "route.committed_path", "cell_kind": "space_belt"},
    ]
    domain = build_known_route_render_domain(base_mv, raw, anchors)
    assert project_overlay_coord_to_lab_xy(0, 0, anchors) in domain
    assert project_overlay_coord_to_lab_xy(0, 1, anchors) in domain
    assert project_overlay_coord_to_lab_xy(0, 2, anchors) in domain
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py::test_clip_helper_classifies_fot_and_output_stub_as_transport_route tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py::test_clip_helper_rejects_shape_miner_equipment tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py::test_project_overlay_coord_identity_when_in_anchors tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py::test_lab_render_bbox_uses_projected_overlay_before_clip tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py::test_known_route_render_domain_unions_projected_full_cells_and_transport -v
```

Expected: FAIL (`ImportError` or `AttributeError` for missing symbols).

- [ ] **Step 3: Implement helpers in `lab_rttp_snapshot_compose.py`**

`build_lab_render_bbox` builds a **dynamic render envelope**, not a fixed asteroid boundary. Projected raw transport/route overlay coords **may expand** the envelope beyond `full_cells` (exterior void connector belts/pipes are legitimate).

Add imports: `from collections.abc import Mapping, Sequence` and use `tuple[int, int, int, int]` as `(min_x, min_y, max_x, max_y)`.

```python
_TRANSPORT_CELL_KINDS = frozenset({"space_belt", "space_pipe"})
_CONFIRMED_TRANSPORT_KINDS = frozenset(
    {
        "placement.confirmed_fixed_output_transport",
        "placement.confirmed_output_stub",
    }
)


def is_transport_or_route_overlay_row(row: Mapping[str, Any]) -> bool:
    cell_kind = str(row.get("cell_kind") or "")
    if cell_kind in _TRANSPORT_CELL_KINDS:
        return True
    for key in ("kind", "overlay_semantic_kind"):
        val = str(row.get(key) or "")
        if val.startswith("route."):
            return True
        if val in _CONFIRMED_TRANSPORT_KINDS:
            return True
    return False


def project_overlay_coord_to_lab_xy(
    ox: int,
    oy: int,
    lab_anchors: frozenset[tuple[int, int]],
) -> tuple[int, int]:
    raw = (int(ox), int(oy))
    if raw in lab_anchors:
        return raw
    return lab_xy_from_replay_cell(ox, oy)


def _projected_full_cell_coords(
    base_map_view: Mapping[str, Any],
    lab_anchors: frozenset[tuple[int, int]],
) -> set[tuple[int, int]]:
    coords: set[tuple[int, int]] = set()
    full_cells = base_map_view.get("full_cells")
    if not isinstance(full_cells, list):
        return coords
    for raw in full_cells:
        if isinstance(raw, Mapping) and "x" in raw and "y" in raw:
            coords.add(
                project_overlay_coord_to_lab_xy(
                    int(raw["x"]), int(raw["y"]), lab_anchors
                )
            )
    return coords


def _projected_transport_coords_from_overlay(
    overlay_cells: Sequence[Mapping[str, Any]],
    lab_anchors: frozenset[tuple[int, int]],
) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for row in overlay_cells:
        if not isinstance(row, Mapping) or "x" not in row or "y" not in row:
            continue
        if is_transport_or_route_overlay_row(row):
            out.add(
                project_overlay_coord_to_lab_xy(
                    int(row["x"]), int(row["y"]), lab_anchors
                )
            )
    return out


def _projected_coords_for_bbox(
    base_map_view: Mapping[str, Any],
    raw_overlay_cells: Sequence[Mapping[str, Any]],
    lab_anchors: frozenset[tuple[int, int]],
) -> list[tuple[int, int]]:
    coords = list(_projected_full_cell_coords(base_map_view, lab_anchors))
    for row in raw_overlay_cells:
        if isinstance(row, Mapping) and "x" in row and "y" in row:
            coords.append(
                project_overlay_coord_to_lab_xy(
                    int(row["x"]), int(row["y"]), lab_anchors
                )
            )
    return coords


def build_known_route_render_domain(
    base_map_view: Mapping[str, Any],
    raw_overlay_cells: Sequence[Mapping[str, Any]],
    lab_anchors: frozenset[tuple[int, int]],
) -> frozenset[tuple[int, int]]:
    return frozenset(
        _projected_full_cell_coords(base_map_view, lab_anchors)
        | _projected_transport_coords_from_overlay(raw_overlay_cells, lab_anchors)
    )


def build_lab_render_bbox(
    base_map_view: Mapping[str, Any],
    raw_overlay_cells: Sequence[Mapping[str, Any]],
    lab_anchors: frozenset[tuple[int, int]],
) -> tuple[int, int, int, int] | None:
    projected = _projected_coords_for_bbox(
        base_map_view, raw_overlay_cells, lab_anchors
    )
    if not projected:
        return None
    xs = [c[0] for c in projected]
    ys = [c[1] for c in projected]
    return (min(xs), min(ys), max(xs), max(ys))


def coord_in_bbox(coord: tuple[int, int], bbox: tuple[int, int, int, int]) -> bool:
    x, y = coord
    min_x, min_y, max_x, max_y = bbox
    return min_x <= x <= max_x and min_y <= y <= max_y
```

Export new symbols in `__all__` (include `project_overlay_coord_to_lab_xy`, `build_lab_render_bbox`, `build_known_route_render_domain`, `coord_in_bbox`, `is_transport_or_route_overlay_row`).

- [ ] **Step 4: Run Step 1 tests — expect PASS**

Same pytest command as Step 2.

- [ ] **Step 5: Commit** (when user requests git commit)

```bash
git add django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py
git commit -m "feat(replay): add RTTP transport overlay classification and bbox helpers"
```

---

### Task 2: Dual-channel clip + route survival tests

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py` (`clip_overlay_cells_to_base_map_domain`)
- Test: `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py`

- [ ] **Step 1: Write failing integration tests for dual-channel clip**

```python
def test_exterior_route_expands_dynamic_bbox_and_survives_anchor_clip() -> None:
    """Exterior void route expands render envelope; only mineable anchor is (0,0)."""
    base_mv = {
        "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
        "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
    }
    overlay = [
        {"x": 0, "y": 0, "kind": "placement.confirmed_extractor", "cell_kind": "shape_miner"},
        {
            "x": 9,
            "y": 0,
            "kind": "route.committed_path",
            "cell_kind": "space_belt",
            "tile_type": "SpaceBelt_Forward",
        },
    ]
    clipped = clip_overlay_cells_to_base_map_domain(overlay, base_mv)
    kinds = {(c["x"], c["y"]): c.get("kind") for c in clipped}
    assert kinds[(0, 0)] == "placement.confirmed_extractor"
    assert kinds[(9, 0)] == "route.committed_path"


def test_equipment_outside_anchor_still_dropped() -> None:
    base_mv = {
        "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
    }
    overlay = [
        {
            "x": 5,
            "y": 0,
            "kind": "placement.confirmed_extractor",
            "cell_kind": "shape_miner",
        },
    ]
    clipped = clip_overlay_cells_to_base_map_domain(overlay, base_mv)
    assert clipped == []


def test_route_outside_explicit_render_bbox_is_dropped() -> None:
    base_mv = {
        "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
        "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
    }
    overlay = [
        {"x": 9, "y": 0, "kind": "route.committed_path", "cell_kind": "space_belt"},
    ]
    clipped = clip_overlay_cells_to_base_map_domain(
        overlay,
        base_mv,
        lab_render_bbox_override=(0, 0, 0, 0),
    )
    assert clipped == []


def test_mixed_confirmed_overlay_keeps_equipment_and_route_by_channel() -> None:
    base_mv = {
        "full_cells": [
            {"x": 0, "y": 0, "kind": "asteroid_shape_field"},
            {"x": 1, "y": 0, "kind": "internal_void"},
        ],
        "bbox": {"min_x": 0, "min_y": 0, "max_x": 1, "max_y": 0},
    }
    overlay = [
        {"x": 0, "y": 0, "kind": "placement.confirmed_extractor", "cell_kind": "shape_miner"},
        {"x": 1, "y": 0, "kind": "route.committed_path", "cell_kind": "space_belt"},
    ]
    clipped = clip_overlay_cells_to_base_map_domain(overlay, base_mv)
    assert len(clipped) == 2
```

- [ ] **Step 2: Run new tests — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py -k "exterior_route_expands or equipment_outside_anchor or route_outside_explicit or mixed_confirmed" -v
```

- [ ] **Step 3: Rewrite `clip_overlay_cells_to_base_map_domain`**

```python
def clip_overlay_cells_to_base_map_domain(
    overlay_cells: list[dict[str, Any]],
    base_map_view: dict[str, Any],
    *,
    lab_render_bbox_override: tuple[int, int, int, int] | None = None,
) -> list[dict[str, Any]]:
    lab_anchors = _base_map_overlay_anchors(base_map_view)
    if not lab_anchors and not overlay_cells:
        return []
    render_bbox = lab_render_bbox_override or build_lab_render_bbox(
        base_map_view, overlay_cells, lab_anchors
    )
    route_domain = build_known_route_render_domain(
        base_map_view, overlay_cells, lab_anchors
    )
    clipped: list[dict[str, Any]] = []
    for cell in overlay_cells:
        if "x" not in cell or "y" not in cell:
            continue
        ox, oy = int(cell["x"]), int(cell["y"])
        lab_xy = project_overlay_coord_to_lab_xy(ox, oy, lab_anchors)
        if is_transport_or_route_overlay_row(cell):
            if render_bbox is None or not coord_in_bbox(lab_xy, render_bbox):
                continue
            if lab_xy not in route_domain:
                continue
            projected = dict(cell)
            projected["x"] = lab_xy[0]
            projected["y"] = lab_xy[1]
            clipped.append(projected)
            continue
        if lab_xy in lab_anchors:
            projected = dict(cell)
            projected["x"] = lab_xy[0]
            projected["y"] = lab_xy[1]
            clipped.append(projected)
    return clipped
```

**Note:** `lab_render_bbox_override` is a test-only kwarg for `test_route_outside_explicit_render_bbox_is_dropped` (forces bbox `(0,0,0,0)` while domain still includes projected route — route dropped by bbox only).

- [ ] **Step 4: Update `test_project_rttp_overlay_cells_clipped_to_base_map_domain`**

Current test expects route at `(9, 0)` **dropped**. Change overlay to equipment-only for anchor clip, or add route with coords inside domain and assert **kept**:

```python
def test_project_rttp_overlay_cells_clipped_to_base_map_domain() -> None:
    base_mv = {
        "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
        "cell_delta": [],
        "overlay_cells": [],
        "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
    }
    overlay = [
        {"x": 0, "y": 0, "kind": "route_domain.preferred"},
        {"x": 9, "y": 0, "kind": "probe.start"},
    ]
    clipped = clip_overlay_cells_to_base_map_domain(overlay, base_mv)
    assert clipped == [{"x": 0, "y": 0, "kind": "route_domain.preferred"}]
```

(`route_domain.*` / `probe.start` remain **equipment channel** — anchor-only; only `(0,0)` kept.)

- [ ] **Step 5: Run full compose test file**

```bash
python -m pytest tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py
git commit -m "fix(replay): dual-channel RTTP overlay clip for committed routes"
```

---

### Task 3: `project_rttp_row` end-to-end projection test

**Files:**
- Test: `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py`

- [ ] **Step 1: Add failing test**

```python
def test_project_rttp_commit_row_keeps_route_overlay_on_map() -> None:
    base = {
        "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
        "cell_delta": [],
        "overlay_cells": [],
        "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
    }
    row = {
        "event_type": "routing.committed",
        "phase": "incremental_commit",
        "title": "Commit",
        "description": "RTTP commit domain snapshot.",
        "metrics": {},
        "cell_overlay_json": {
            "cells": [
                {"x": 0, "y": 0, "kind": "placement.confirmed_extractor", "cell_kind": "shape_miner"},
                {
                    "x": 9,
                    "y": 0,
                    "kind": "route.committed_path",
                    "cell_kind": "space_belt",
                    "tile_type": "SpaceBelt_Forward",
                },
            ]
        },
    }
    out = project_rttp_row_to_product_frame(row, base_map_view=base)
    ov = out["map_view"]["overlay_cells"]
    assert any(c.get("kind") == "route.committed_path" for c in ov)
```

- [ ] **Step 2: Run test — expect PASS** (Task 2 should satisfy; if FAIL, wire `project_rttp_row_to_product_frame` only passes through clip — no extra change expected)

```bash
python -m pytest tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py::test_project_rttp_commit_row_keeps_route_overlay_on_map -v
```

- [ ] **Step 3: Commit** (optional squash with Task 2)

---

### Task 4: Lint and regression sweep

**Files:** (verification only)

- [ ] **Step 1: Ruff on touched paths**

```bash
python -m ruff check django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py
```

- [ ] **Step 2: Related replay diagnostics tests (no code change expected)**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py -v
```

- [ ] **Step 3: Commit** if lint-only fixes

---

### Task 5 (optional): Document cross-link

**Files:**
- Modify: `documents/ai/lab_map_rendering_contract.md`

- [ ] **Step 1: Add subsection under Replay grid bbox**

```markdown
### RTTP compose dual-channel clip

`lab_rttp_snapshot_compose.clip_overlay_cells_to_base_map_domain` keeps equipment on mineable anchors and transport/route rows via `lab_render_bbox` + `known_route_render_domain` (see spec `docs/superpowers/specs/2026-05-30-rttp-replay-route-overlay-clip-design.md`).
```

- [ ] **Step 2: Commit**

```bash
git add documents/ai/lab_map_rendering_contract.md
git commit -m "docs: note RTTP dual-channel overlay clip in lab map contract"
```

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| `is_transport_or_route_overlay_row` single helper | Task 1 |
| Projected lab coord frame (`project_overlay_coord_to_lab_xy`) | Task 1 + Task 2 |
| Dynamic render envelope (`lab_render_bbox`; exterior routes expand) | Task 1 `build_lab_render_bbox` + Task 2 |
| `test_exterior_route_expands_dynamic_bbox_and_survives_anchor_clip` | Task 2 Step 1 |
| Equipment anchor-only | Task 2 clip branch |
| Transport bbox + `known_route_render_domain` union (no leave-one-out) | Task 2 |
| No `base_domain_bbox` membership guard | Task 2 |
| Explicit bbox drop test | Task 2 `lab_render_bbox_override` |
| Stray route suppression | **Deferred** — spec follow-up connected-component guard |
| Algorithm non-goals | No other modules in plan |
| Update existing clip test | Task 2 Step 4 |
| Optional lab_map_rendering_contract | Task 5 |

No placeholders remain in task steps. Rev3: `lab_render_bbox` is dynamic render envelope; exterior void routes expand it (not fixed island clip).

---

## Manual verification (post-implementation)

1. Run solver on ShapeMiner layout slug used in report.
2. Lab replay: scrub **selection** (many overlays) vs **commit** (equipment + belt path visible).
3. Confirm `description` `committed_ids` count aligns with visible miner anchors (not required to match `commit_order` length).

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-30-rttp-replay-route-overlay-clip.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute in this session with executing-plans checkpoints  

Which approach do you want?
