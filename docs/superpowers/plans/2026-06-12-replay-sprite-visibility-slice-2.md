# Replay Sprite Visibility — Slice 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `lab_paint_layers_from_view` resolver + effective-view index builder + Python/JS parity tests — **no canvas/DOM paint swap**.

**Architecture:** `EffectiveCellView` (merged semantic) → `LabPaintLayers` (visual slots: terrain / occupant / transport / chrome[]). Python mirror in `tests/support/lab_replay_paint_plan.py` is the parity authority for golden tests; JS module mirrors for Slice 3 adapter. Index builder collects visible cell universe per frame (wire union + carry hook stub for Slice 3).

**Tech Stack:** Python 3.12 (`TypedDict`, `EffectiveCellView`, pytest), vanilla JS (`lab_replay_paint_plan.js`), existing sprite maps from `lab_sprite_path` / `lab_replay_sprite_wire.py`.

**Spec:** [`docs/superpowers/specs/2026-06-12-replay-sprite-visibility-design.md`](../specs/2026-06-12-replay-sprite-visibility-design.md)  
**Depends on:** Slice 1 commit (`replay_wire_read_sanitize`, `replay_cell_index`, merge input wiring)  
**Kanban:** `.devtool/features/replay-sprite-visibility-2026-06-12.md`

**Slice 2 stop:** Resolver + index + golden/parity/anti-fade/candidate tests green. **`buildCanvasPaintPlan` / `renderFullMapReplayFrame` unchanged.**

**Approved execution notes (2026-06-12):**
1. Confirm/reuse `CELL_KIND_STATIC_RELPATH` (and existing sprite maps) before hard-coding `AsteroidField_Shape.svg` in snapshots.
2. Sanitize **full / delta / overlay** consistently in test helpers and index builder (`sanitize_replay_wire_cell_for_read` on all merge inputs).
3. Add `test_background_fill_allowed_only_when_no_sprite` (or equivalent) — anti-fade + allowed fallback when no occupant/transport sprite.
4. JS contract: `test_js_paint_plan_contains_candidate_priority_guard` — candidate branch guards transport slot (static source scan).

---

## File map (Slice 2)

| File | Responsibility |
|------|----------------|
| `tests/support/lab_replay_paint_plan.py` | Python `LabPaintLayers`, `lab_paint_layers_from_view`, `build_effective_cell_view_index`, sprite resolve helpers |
| `tests/support/lab_replay_paint_fixtures.py` | `frame_38_candidate_miner_fixture()`, shared wire rows |
| `tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py` | Resolver + index + frame-38 + anti-fade + transport-priority tests |
| `tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py` | Golden frame parity (merge → layers vs detail semantics) |
| `django_apps/web/static/web/js/lab_replay_paint_plan.js` | JS mirror: `labPaintLayersFromView`, `buildEffectiveCellViewIndex`, `cellKey` re-export |
| `django_apps/web/templates/web/asteroid_miner_layout_solver.html` | Load `lab_replay_paint_plan.js` after `lab_effective_cell_view.js` (not wired to canvas) |
| `tests/unit/asteroid_lab/test_lab_canvas_renderer.py` | JS contract: module exists, parity snapshot strings |

**Forbidden edits (Slice 2):** `buildCanvasPaintPlan`, `renderFullMapReplayFrame`, `lab_replay_canvas_renderer.js`, DOM tone classes, `NON_SPRITE_OVERLAY_CELL_KINDS` removal (Slice 4).

---

## `LabPaintLayers` contract (locked)

```python
# Terrain modes — void_fill is NOT for asteroid fields
"field_sprite"      # AsteroidField_*.svg
"background_fill"   # island default rgba only when no occupant/transport sprite
"void_fill"         # internal_void / external void only

# Slots (mutually exclusive occupant vs transport sprite by default)
terrain:  null | {mode, rel?, fill?}
occupant: null | {rel: str, rotation: int}
transport: null | {rel: str, rotation: int}
chrome:   list[{kind: "candidate_ring"|..., stroke_only: True}]
```

**Resolver priority (order matters):**

1. If `occupant.kind == "candidate_miner"` → occupant sprite from `output.transport_kind`; chrome `candidate_ring`; **transport slot empty** even if legacy wire had belt tokens.
2. Else committed miner/extension → occupant from kind map.
3. Else if `transport.kind` in `{space_belt, space_pipe}` and `transport.tile_id` → transport slot only.
4. Terrain: field kinds → `field_sprite` if static rel exists; `void_fill` only for void kinds; `background_fill` only when no occupant/transport sprite.

**Anti-fade precondition (testable in Slice 2):** if `occupant` or `transport` sprite present → `terrain.mode != "background_fill"`.

---

### Task 1: Python paint fixtures (frame-38)

**Files:**
- Create: `tests/support/lab_replay_paint_fixtures.py`
- Test: `tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py
from tests.support.lab_replay_paint_fixtures import frame_38_candidate_miner_fixture


def test_frame_38_fixture_has_map_view_at_10_7() -> None:
    frame = frame_38_candidate_miner_fixture()
    mv = frame["map_view"]
    full = { (c["x"], c["y"]): c for c in mv["full_cells"] }
    ov = { (c["x"], c["y"]): c for c in mv["overlay_cells"] }
    assert (10, 7) in full
    assert full[(10, 7)]["kind"] == "asteroid_shape_field"
    assert (10, 7) in ov
    assert ov[(10, 7)]["kind"] == "candidate_miner"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py::test_frame_38_fixture_has_map_view_at_10_7 -v`

- [ ] **Step 3: Implement fixture**

```python
# tests/support/lab_replay_paint_fixtures.py
"""Shared replay frame fixtures for paint-plan tests."""

from __future__ import annotations


def frame_38_candidate_miner_fixture() -> dict[str, object]:
    """User-reported frame 38 cell (10,7): field + legacy candidate overlay."""
    return {
        "frame_index": 38,
        "event_type": "fixture.frame_38_candidate_miner",
        "map_view": {
            "full_cells": [
                {
                    "x": 10,
                    "y": 7,
                    "kind": "asteroid_shape_field",
                    "transport": "none",
                    "layer": 0,
                    "rotation": 0,
                },
            ],
            "overlay_cells": [
                {
                    "x": 10,
                    "y": 7,
                    "kind": "candidate_miner",
                    "transport": "shape_belt",
                    "rotation": 0,
                    "layer": 0,
                },
            ],
            "cell_delta": [],
        },
    }
```

- [ ] **Step 4: Run test — expect PASS**

---

### Task 2: Python `lab_paint_layers_from_view` — candidate miner + terrain

**Files:**
- Create: `tests/support/lab_replay_paint_plan.py` (start with resolver only)
- Test: extend `test_lab_replay_paint_plan.py`

- [ ] **Step 1: Write failing tests**

```python
from django_apps.asteroid_lab.replay.effective_cell_view import merge_effective_cell_view
from django_apps.asteroid_lab.replay.effective_cell_wire import effective_cell_to_wire
from django_apps.asteroid_lab.replay.replay_wire_read_sanitize import sanitize_replay_wire_cell_for_read
from tests.support.lab_replay_paint_fixtures import frame_38_candidate_miner_fixture
from tests.support.lab_replay_paint_plan import lab_paint_layers_from_view


def _merged_view_from_frame(frame: dict, x: int, y: int):
    mv = frame["map_view"]
    full = next(c for c in mv["full_cells"] if c["x"] == x and c["y"] == y)
    overlays = [c for c in mv["overlay_cells"] if c["x"] == x and c["y"] == y]
    overlays = [sanitize_replay_wire_cell_for_read(c) for c in overlays]
    view = merge_effective_cell_view(x=x, y=y, frame_index=frame.get("frame_index"), full_cell=full, overlay_cells=overlays)
    assert view is not None
    return effective_cell_to_wire(view)


def test_frame_38_candidate_miner_paint_layers() -> None:
    wire = _merged_view_from_frame(frame_38_candidate_miner_fixture(), 10, 7)
    layers = lab_paint_layers_from_view(wire)
    assert layers["occupant"] is not None
    assert layers["occupant"]["rel"] == "Miner/Layout_ShapeMiner.svg"
    assert layers["transport"] is None
    assert any(c["kind"] == "candidate_ring" for c in layers["chrome"])
    assert layers["terrain"] is not None
    assert layers["terrain"]["mode"] == "field_sprite"
    assert layers["terrain"]["rel"] == "AsteroidField_Shape.svg"


def test_transport_sprite_does_not_override_candidate_miner() -> None:
    wire = {
        "frame_index": 38,
        "coord": {"x": 10, "y": 7, "layer": 0},
        "terrain": {"kind": "asteroid_shape_field", "tile_type": None},
        "occupant": {"kind": "candidate_miner", "rotation": 0},
        "transport": {"kind": "space_belt", "tile_id": "SpaceBelt_Forward", "simulation": None},
        "output": {"transport_kind": "space_belt"},
        "sources": {},
    }
    layers = lab_paint_layers_from_view(wire)
    assert layers["occupant"]["rel"] == "Miner/Layout_ShapeMiner.svg"
    assert layers["transport"] is None


def test_anti_fade_precondition_no_background_fill_when_occupant_sprite() -> None:
    wire = _merged_view_from_frame(frame_38_candidate_miner_fixture(), 10, 7)
    layers = lab_paint_layers_from_view(wire)
    assert layers["occupant"] is not None
    terrain = layers.get("terrain")
    if terrain is not None:
        assert terrain["mode"] != "background_fill"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py -k "frame_38 or transport_sprite or anti_fade" -v`

- [ ] **Step 3: Implement minimal resolver**

Implement `lab_paint_layers_from_view(view: EffectiveCellWire | Mapping) -> dict` in `tests/support/lab_replay_paint_plan.py`:

- Accept wire dict from `effective_cell_to_wire` (nested `terrain`/`occupant`/`transport`/`output` keys).
- `candidate_miner` + `output.transport_kind == space_belt` → `Miner/Layout_ShapeMiner.svg`, `candidate_ring` chrome.
- `candidate_miner` + `space_pipe` → `Miner/Layout_FluidMiner.svg`.
- Reuse sprite rel maps from `tests/support/lab_replay_sprite_wire.py` (`CELL_KIND_STATIC_RELPATH`, `_sprite_relpath_from_tile_type`).
- **Transport slot:** only when `occupant.kind` is NOT `candidate_miner` and transport tile_id present.
- **Terrain:** `field_sprite` for asteroid fields; skip `background_fill` when occupant/transport sprite set.

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py -k "frame_38 or transport_sprite or anti_fade" -v`

- [ ] **Step 5: ruff**

Run: `ruff check tests/support/lab_replay_paint_plan.py tests/support/lab_replay_paint_fixtures.py`

---

### Task 3: Python effective-view index builder

**Files:**
- Extend: `tests/support/lab_replay_paint_plan.py`
- Test: `test_lab_replay_paint_plan.py`

- [ ] **Step 1: Write failing test**

```python
from django_apps.asteroid_lab.replay.replay_cell_index import cell_key
from tests.support.lab_replay_paint_plan import build_effective_cell_view_index


def test_build_effective_cell_view_index_frame_38() -> None:
    frame = frame_38_candidate_miner_fixture()
    index = build_effective_cell_view_index(frame)
    key = cell_key(10, 7, 0)
    assert key in index
    assert index[key]["occupant"]["kind"] == "candidate_miner"
    assert index[key]["output"]["transport_kind"] == "space_belt"
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement `build_effective_cell_view_index(frame)`**

- Collect coordinate universe from `map_view.full_cells`, `overlay_cells`, `cell_delta` (union of `(x,y,layer)`).
- For each coord: sanitize overlay rows, `merge_effective_cell_view`, `effective_cell_to_wire`.
- Return `dict[str, EffectiveCellWire]` keyed by `cell_key(x,y,layer)`.
- **Slice 2 stub:** `carry_layout_snapshot=None` parameter documented for Slice 3; ignore carry when `None`.

- [ ] **Step 4: Run — expect PASS**

---

### Task 4: Golden transport-complete parity

**Files:**
- Create: `tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py`
- Extend: `tests/support/lab_replay_paint_plan.py`

- [ ] **Step 1: Write failing golden test**

```python
from tests.support.lab_replay_sprite_wire import golden_transport_replay_frames
from tests.support.lab_replay_paint_plan import build_effective_cell_view_index, lab_paint_layers_from_view


def test_golden_transport_complete_frame_paint_layers_have_belt_sprites() -> None:
    frames = golden_transport_replay_frames()
    transport = next(f for f in frames if str(f.get("event_type", "")).endswith("transport_routing_complete"))
    index = build_effective_cell_view_index(transport)
    belt_layers = [
        layers
        for _k, view in index.items()
        if (layers := lab_paint_layers_from_view(view))["transport"]
        and layers["transport"]["rel"].startswith("SpaceBelt/")
    ]
    assert belt_layers, "expected at least one transport belt sprite layer in golden frame"
```

Add second assertion: for every indexed view with `occupant.kind == candidate_miner`, transport slot is None.

- [ ] **Step 2: Run — expect FAIL or PASS depending on golden frame content**

- [ ] **Step 3: Extend resolver for committed transport tiles** (space_belt + tile_id → transport slot, occupant empty unless miner kind)

- [ ] **Step 4: Full golden test file green**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py -v`

---

### Task 5: JS mirror module + template load

**Files:**
- Create: `django_apps/web/static/web/js/lab_replay_paint_plan.js`
- Modify: `django_apps/web/templates/web/asteroid_miner_layout_solver.html`
- Modify: `tests/unit/asteroid_lab/test_lab_canvas_renderer.py`

- [ ] **Step 1: Write failing contract tests**

```python
PAINT_JS = JS_DIR / "lab_replay_paint_plan.js"

def test_js_lab_paint_layers_from_view_exists() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "function labPaintLayersFromView" in src
    assert "function buildEffectiveCellViewIndex" in src
    assert "LabReplayPaintPlan" in src


def test_template_loads_lab_replay_paint_plan_js() -> None:
    tpl = TPL.read_text(encoding="utf-8")
    assert "lab_replay_paint_plan.js" in tpl
    # must load after lab_effective_cell_view.js
    assert tpl.index("lab_effective_cell_view.js") < tpl.index("lab_replay_paint_plan.js")
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement JS module**

Mirror Python resolver logic:
- `labPaintLayersFromView(view)` — same slot rules as Python
- `buildEffectiveCellViewIndex(frame)` — uses `LabReplayWireSanitize.sanitizeReplayWireCellForRead`, `LabEffectiveCellView.mergeEffectiveCellView`, `LabReplayWireSanitize.cellKey`
- Export `global.LabReplayPaintPlan = { labPaintLayersFromView, buildEffectiveCellViewIndex }`
- Sprite rel constants duplicated minimally (match Python paths) — document parity requirement in file header

Template insert after `lab_effective_cell_view.js`:

```html
<script src="{% static 'web/js/lab_replay_paint_plan.js' %}?v=replay_paint_plan_v1" defer></script>
```

- [ ] **Step 4: Run contract tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_canvas_renderer.py -k "paint_plan or lab_replay_paint" -v`

**Do NOT call `labPaintLayersFromView` from `asteroid_miner_layout_lab.js` yet.**

---

### Task 6: JS/Python parity snapshot test

**Files:**
- Extend: `tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py`

- [ ] **Step 1: Add parity helper test (Python authority)**

```python
def test_python_paint_layers_frame_38_contract_snapshot() -> None:
    """Stable contract snapshot for JS parity reviewers."""
    wire = _merged_view_from_frame(frame_38_candidate_miner_fixture(), 10, 7)
    layers = lab_paint_layers_from_view(wire)
    assert layers == {
        "terrain": {"mode": "field_sprite", "rel": "AsteroidField_Shape.svg"},
        "occupant": {"rel": "Miner/Layout_ShapeMiner.svg", "rotation": 0},
        "transport": None,
        "chrome": [{"kind": "candidate_ring", "stroke_only": True}],
    }
```

Adjust exact dict keys (`stroke_only` vs `strokeOnly`) to match Python TypedDict choice — **use snake_case in Python**; JS uses camelCase in object but parity test compares via documented mapping table in test file.

- [ ] **Step 2: Document parity table in test module docstring for Task 5 implementer**

- [ ] **Step 3: Run full Slice 2 pytest gate**

```bash
python -m pytest \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py \
  tests/unit/asteroid_lab/test_lab_canvas_renderer.py \
  -k "paint_plan or lab_replay_paint or frame_38 or anti_fade or transport_sprite or golden_transport" \
  -q
```

Expected: all passed

- [ ] **Step 4: Regression — Slice 1 tests still green**

```bash
python -m pytest tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py \
  tests/unit/asteroid_lab/replay/test_replay_wire_audit.py \
  tests/unit/asteroid_lab/replay/test_replay_frame_cell_resolver.py -q
```

- [ ] **Step 5: Update kanban** — Progress note Slice 2 complete; `status: verify`

- [ ] **Step 6: Commit (when user requests)**

```bash
git add tests/support/lab_replay_paint_plan.py tests/support/lab_replay_paint_fixtures.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py \
  django_apps/web/static/web/js/lab_replay_paint_plan.js \
  django_apps/web/templates/web/asteroid_miner_layout_solver.html \
  tests/unit/asteroid_lab/test_lab_canvas_renderer.py \
  .devtool/features/replay-sprite-visibility-2026-06-12.md

git commit -m "feat(replay): Slice 2 LabPaintLayers resolver and parity tests"
```

---

## Spec coverage self-check (Slice 2)

| Spec requirement | Task |
|------------------|------|
| `lab_paint_layers_from_view` | Task 2 |
| terrain / occupant / transport / chrome split | Task 2 |
| candidate_miner → miner sprite + ring | Task 2 |
| transport does not override candidate | Task 2 |
| anti-fade precondition | Task 2 |
| index universe (wire union) | Task 3 |
| frame-38 fixture | Task 1 |
| golden parity | Task 4 |
| JS mirror module | Task 5 |
| **No canvas/DOM swap** | Forbidden list |

## Out of scope (Slice 2)

- `buildLabPaintPlanFromEffectiveViews` / canvas renderer changes (Slice 3)
- DOM chrome-only / `NON_SPRITE` removal (Slice 4)
- Harvest quarantine (Slice 5)
- `data-lab-paint-v2` flag wiring (Slice 3)
- Layout carry from `lastFrameWithSpriteCapableCells` implementation (stub only in index builder API)

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-2.md`.

**After your review:** Subagent-Driven execution starting Task 1. Do not start until approved.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task + spec/code review between tasks  
2. **Inline Execution** — `executing-plans` in one session with checkpoints

Which approach?
