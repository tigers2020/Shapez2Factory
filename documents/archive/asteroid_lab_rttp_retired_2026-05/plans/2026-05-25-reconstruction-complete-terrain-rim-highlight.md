---
status: RETIRED_ARCHIVE
do_not_execute: true
superseded_by: docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md
---

# Reconstruction-Complete Terrain Rim Highlight — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lab replay grid shows mineable rim (A) and external-void-facing edges (D) on reconstruction-complete terrain, with server-computed `metrics.terrain_rim_highlight`, frozen post-complete reuse, and a default-on UI toggle.

**Architecture:** Pure `reconstruction/rim_highlight.py` builds `TerrainRimHighlightDTO` from `ReconstructionCompleteMap` or partial `(field_cells, external_void_cells)`; `lab_timeline_rim_enrichment.py` attaches wire JSON at timeline compose; Lab JS paints static CSS classes after `renderFullMapReplayFrame`. No optimization imports in production rim code.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, black, mypy `django_apps config src`; Lab JS (`asteroid_miner_layout_lab.js`); Tailwind source `assets/css/input.css` → built `app.css`

**Authoritative spec:** [`docs/superpowers/specs/2026-05-25-reconstruction-complete-terrain-rim-highlight-design.md`](../specs/2026-05-25-reconstruction-complete-terrain-rim-highlight-design.md)

**Branch:** `feat/reconstruction-terrain-rim-highlight` (dedicated worktree recommended)

---

## Invariants (do not drift)

```text
Terrain rim highlight is a replay/UI observability artifact.
It is derived from ReconstructionCompleteMap or renderable reconstruction frame data,
and must never become solver, topology, capacity, candidate, route, commit, or validation input.
```

**Module boundary (plan blocker — production code):**

```text
Production rim_highlight.py (and lab_timeline_rim_enrichment.py) must not import optimization.* modules.
Parity with optimization.reconstruction_adapter._rim_cells is test-only,
or the shared neighbor rule must live in a neutral reconstruction/topology helper.
```

**Partial frame rule:** Renderable reconstruction `full_map` / `map_view.full_cells` is **UI/replay enrichment input only**. Solver/topology/capacity SoT remains `ReconstructionCompleteMap` at pipeline boundaries.

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `django_apps/asteroid_lab/reconstruction/rim_topology.py` | Neutral `field_rim_cells(field_cells)` using `neighbors4` (no optimization import) |
| Create | `django_apps/asteroid_lab/reconstruction/rim_highlight.py` | DTOs, void edges, `build_terrain_rim_highlight*`, wire serialize |
| Create | `django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py` | `enrich_lab_timeline_frames_with_terrain_rim`, replay cell → topology |
| Modify | `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py` | Call enrichment; set `track_metrics.frozen_terrain_rim_highlight` |
| Modify | `assets/css/input.css` | `.lab-terrain-rim`, `.lab-terrain-void-edge-*` |
| Modify | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Toggle, `applyTerrainRimHighlight`, HUD roles |
| Modify | `django_apps/web/templates/web/asteroid_miner_layout_solver.html` | Checkbox `#lab-terrain-rim-highlight-toggle` |
| Create | `tests/unit/asteroid_lab/test_rim_highlight.py` | DTO, edges wire rules, parity (test-only `_rim_cells`) |
| Create | `tests/unit/asteroid_lab/test_lab_timeline_rim_enrichment.py` | Frozen reuse, reconstruction vs post-complete |
| Modify | `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` | Toggle id, CSS classes, metrics key |
| Modify | `tests/unit/asteroid_lab/test_rim_highlight_layer_boundary.py` | AST: no `optimization` import from rim_highlight / enrichment |

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Create branch**

```powershell
Set-Location F:\Python_Projects\shapez2Factory
git checkout master
git pull
git checkout -b feat/reconstruction-terrain-rim-highlight
```

- [ ] **Step 2: Baseline narrow gate (pre-edit)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_replay_timeline_dto.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/reconstruction django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
```

Expected: PASS.

---

### Task 1: Neutral rim topology + DTO factory (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/reconstruction/rim_topology.py`
- Create: `django_apps/asteroid_lab/reconstruction/rim_highlight.py`
- Create: `tests/unit/asteroid_lab/test_rim_highlight.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/asteroid_lab/test_rim_highlight.py`:

```python
"""Terrain rim highlight DTO — replay/UI artifact only."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.optimization.reconstruction_adapter import _rim_cells
from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_decoded_cells,
)
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.rim_highlight import (
    TerrainRimHighlightDTO,
    VoidEdgeCellDTO,
    build_terrain_rim_highlight,
    build_terrain_rim_highlight_from_renderable_cells,
    canonicalize_void_edges,
    terrain_rim_highlight_to_metrics_dict,
)
from django_apps.asteroid_lab.reconstruction.rim_topology import field_rim_cells
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame


def _canon_complete_map():
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    return build_reconstruction_complete_map(cleanup=cleanup, recon=recon)


def test_field_rim_cells_matches_adapter_rim_parity() -> None:
    complete = _canon_complete_map()
    expected = _rim_cells(complete.field_cells)
    assert field_rim_cells(complete.field_cells) == expected


def test_build_terrain_rim_highlight_rim_subset_of_field() -> None:
    complete = _canon_complete_map()
    dto = build_terrain_rim_highlight(complete)
    rim_set = frozenset(dto.rim_cells)
    assert rim_set <= complete.field_cells
    assert dto.version == 1
    assert dto.coord_frame == CoordFrame.ISLAND_RAW


def test_void_edge_cells_subset_of_rim_and_edges_canonical() -> None:
    complete = _canon_complete_map()
    dto = build_terrain_rim_highlight(complete)
    rim_set = frozenset(dto.rim_cells)
    for entry in dto.void_edge_cells:
        assert (entry.x, entry.y) in rim_set
        assert entry.edges == canonicalize_void_edges(entry.edges)
        for ch in entry.edges:
            assert ch in "nesw"


def test_canonicalize_void_edges_rejects_unknown_char() -> None:
    with pytest.raises(ValueError, match="unknown"):
        canonicalize_void_edges("nx")


def test_canonicalize_void_edges_orders_nesw() -> None:
    assert canonicalize_void_edges("wn") == "nw"


def test_metrics_dict_wire_shape() -> None:
    complete = _canon_complete_map()
    dto = build_terrain_rim_highlight(complete)
    wire = terrain_rim_highlight_to_metrics_dict(dto)
    assert wire["version"] == 1
    assert "rim_cells" in wire
    assert "void_edge_cells" in wire
    assert wire["coord_frame"] == CoordFrame.ISLAND_RAW.value


def test_partial_factory_delegates_same_as_complete() -> None:
    complete = _canon_complete_map()
    from_renderable = build_terrain_rim_highlight_from_renderable_cells(
        field_cells=complete.field_cells,
        external_void_cells=complete.external_void_cells,
        coord_frame=complete.coord_frame,
    )
    from_complete = build_terrain_rim_highlight(complete)
    assert from_renderable == from_complete
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rim_highlight.py -v --tb=short
```

Expected: `ModuleNotFoundError` or import errors for `rim_highlight` / `rim_topology`.

- [ ] **Step 3: Implement `rim_topology.py`**

```python
"""Mineable field rim coords (reconstruction layer; not optimization)."""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.grid_contract import Coord, neighbors4


def field_rim_cells(field_cells: frozenset[Coord]) -> frozenset[Coord]:
    rim: set[Coord] = set()
    for coord in field_cells:
        if any(neighbor not in field_cells for neighbor in neighbors4(coord)):
            rim.add(coord)
    return frozenset(rim)


__all__ = ["field_rim_cells"]
```

- [ ] **Step 4: Implement `rim_highlight.py`**

Implement (minimal complete):

- `VoidEdgeCellDTO`, `TerrainRimHighlightDTO` frozen dataclasses
- `canonicalize_void_edges(edges: str) -> str` — allowed `nesw`, canonical order, raise on unknown
- `_void_edge_cells(rim, external_void) -> tuple[VoidEdgeCellDTO, ...]` — neighbor check per direction; omit empty
- `build_terrain_rim_highlight_from_renderable_cells(...)` — `rim = field_rim_cells(field_cells)`, void edges, version=1
- `build_terrain_rim_highlight(complete_map)` — delegate to partial with `complete_map.field_cells` / `external_void_cells` / `coord_frame`
- `terrain_rim_highlight_to_metrics_dict(dto)` — `rim_cells` as `list[list[int]]`, void edges as `list[{"x","y","edges"}]`, `coord_frame` as `.value`

**Do not** `import` anything under `django_apps.asteroid_lab.optimization`.

- [ ] **Step 5: Run tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rim_highlight.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/reconstruction/rim_topology.py django_apps/asteroid_lab/reconstruction/rim_highlight.py
```

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/reconstruction/rim_topology.py django_apps/asteroid_lab/reconstruction/rim_highlight.py tests/unit/asteroid_lab/test_rim_highlight.py
git commit -m "feat(asteroid-lab): add terrain rim highlight DTO factory"
```

---

### Task 2: Lab timeline enrichment + frozen track_metrics (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py`
- Modify: `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`
- Create: `tests/unit/asteroid_lab/test_lab_timeline_rim_enrichment.py`
- Create: `tests/unit/asteroid_lab/test_rim_highlight_layer_boundary.py`

- [ ] **Step 1: Write failing enrichment tests**

Create `tests/unit/asteroid_lab/test_lab_timeline_rim_enrichment.py`:

```python
"""Lab timeline terrain_rim_highlight enrichment (output-only)."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.evidence import ASTEROID_FIELD_KINDS
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.services.lab_timeline_rim_enrichment import (
    enrich_lab_timeline_frames_with_terrain_rim,
)


def _frame(
    *,
    lab_phase: str,
    event_type: str,
    full_cells: list[dict],
    frame_index: int = 0,
) -> dict:
    return {
        "frame_index": frame_index,
        "phase": "reconstruction",
        "event_type": event_type,
        "title": "t",
        "description": "",
        "inspector": {"lab_phase": lab_phase, "lab_event_type": "reconstruction.begin"},
        "metrics": {},
        "map_view": {
            "full_cells": full_cells,
            "cell_delta": [],
            "overlay_cells": [],
            "annotations": [],
            "bbox": {"min_x": 0, "min_y": 0, "max_x": 1, "max_y": 1},
        },
    }


def test_reconstruction_phase_attaches_highlight() -> None:
    cells = [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}]
    frames = [_frame(lab_phase="reconstruction", event_type="reconstruction.started", full_cells=cells)]
    out, frozen = enrich_lab_timeline_frames_with_terrain_rim(frames)
    assert "terrain_rim_highlight" in out[0]["metrics"]


def test_post_complete_reuses_frozen_semantic_value() -> None:
    field_kind = next(iter(ASTEROID_FIELD_KINDS))
    growing = [
        {"x": 0, "y": 0, "kind": field_kind},
        {"x": 1, "y": 0, "kind": field_kind},
    ]
    frames = [
        _frame(
            lab_phase="reconstruction",
            event_type="reconstruction.started",
            full_cells=[growing[0]],
            frame_index=0,
        ),
        _frame(
            lab_phase="reconstruction",
            event_type=ReplayEventType.RECONSTRUCTION_COMPLETED.value,
            full_cells=growing,
            frame_index=1,
        ),
        _frame(
            lab_phase="reconstruction",
            event_type="optimization.input_loaded",
            full_cells=growing,
            frame_index=2,
        ),
    ]
    out, frozen = enrich_lab_timeline_frames_with_terrain_rim(frames)
    complete_wire = out[1]["metrics"]["terrain_rim_highlight"]
    assert frozen == complete_wire
    assert out[2]["metrics"].get("terrain_rim_highlight") in (None, complete_wire)
    if "terrain_rim_highlight" in out[2]["metrics"]:
        assert out[2]["metrics"]["terrain_rim_highlight"] == complete_wire


def test_decode_frame_omits_highlight() -> None:
    frames = [_frame(lab_phase="decode", event_type="decode.started", full_cells=[])]
    out, frozen = enrich_lab_timeline_frames_with_terrain_rim(frames)
    assert "terrain_rim_highlight" not in out[0]["metrics"]
    assert frozen is None
```

Create `tests/unit/asteroid_lab/test_rim_highlight_layer_boundary.py`:

```python
"""Production rim highlight must not import optimization."""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PATHS = [
    REPO / "django_apps" / "asteroid_lab" / "reconstruction" / "rim_highlight.py",
    REPO / "django_apps" / "asteroid_lab" / "services" / "lab_timeline_rim_enrichment.py",
]


@pytest.mark.parametrize("path", PATHS)
def test_no_optimization_import(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "optimization" not in node.module, node.module
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "optimization" not in alias.name, alias.name
```

(Add `import pytest` at top of boundary test file.)

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_timeline_rim_enrichment.py tests/unit/asteroid_lab/test_rim_highlight_layer_boundary.py -v --tb=short
```

- [ ] **Step 3: Implement `lab_timeline_rim_enrichment.py`**

Key functions:

```python
LAB_PHASE_RECONSTRUCTION = "reconstruction"
COMPLETE_EVENT_TYPES = frozenset({
    "reconstruction.completed",
    "reconstruction.map_complete",
})

def _replay_cell_to_decoded(row: Mapping[str, Any]) -> DecodedCellDTO: ...
def _field_cells_from_full_cells(rows: Sequence[Mapping]) -> frozenset[Coord]: ...
def _topology_from_renderable_rows(rows) -> tuple[frozenset[Coord], frozenset[Coord]]: ...
    # acceptance_topology_from_decoded_cells(cells, field_cells=field_cells)

def enrich_lab_timeline_frames_with_terrain_rim(
    frames: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    frozen_wire: dict[str, Any] | None = None
    out: list[dict[str, Any]] = []
    for fr in frames:
        fr_copy = copy.deepcopy(fr)
        metrics = dict(fr_copy.get("metrics") or {})
        inspector = fr_copy.get("inspector") or {}
        lab_phase = str(inspector.get("lab_phase") or "")
        event_type = str(fr_copy.get("event_type") or "")
        if not frame_has_renderable_map(fr_copy):
            fr_copy["metrics"] = metrics
            out.append(fr_copy)
            continue
        if lab_phase == LAB_PHASE_RECONSTRUCTION:
            rows = fr_copy["map_view"]["full_cells"]
            field_cells, external_void = _topology_from_renderable_rows(rows)
            dto = build_terrain_rim_highlight_from_renderable_cells(...)
            wire = terrain_rim_highlight_to_metrics_dict(dto)
            if event_type in COMPLETE_EVENT_TYPES or inspector.get("lab_event_type") in COMPLETE_EVENT_TYPES:
                frozen_wire = wire
            metrics["terrain_rim_highlight"] = wire
        elif frozen_wire is not None:
            pass  # omit per-frame on post-complete (track fallback) OR metrics["terrain_rim_highlight"] = copy.deepcopy(frozen_wire)
        fr_copy["metrics"] = metrics
        out.append(fr_copy)
    return out, frozen_wire
```

Import `frame_has_renderable_map` from `lab_rttp_snapshot_compose` (services layer — OK).

**Post-complete policy (spec):** omit per-frame key; Lab uses `track_metrics.frozen_terrain_rim_highlight`. Test may accept either omitted or equal wire on frame 2 — adjust test to: frame 2 must NOT recompute (if present, must equal `frozen`).

- [ ] **Step 4: Wire `lab_replay_timeline_payload.py`**

After `interleave_rttp_snapshot_frames`:

```python
from django_apps.asteroid_lab.services.lab_timeline_rim_enrichment import (
    enrich_lab_timeline_frames_with_terrain_rim,
)

serialized, frozen_wire = enrich_lab_timeline_frames_with_terrain_rim(serialized)
metrics = _track_metrics_from_serialized_frames(serialized, diagnostic_reason=diagnostic)
if frozen_wire is not None:
    metrics["frozen_terrain_rim_highlight"] = frozen_wire
```

- [ ] **Step 5: Run tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_timeline_rim_enrichment.py tests/unit/asteroid_lab/test_rim_highlight_layer_boundary.py tests/unit/asteroid_lab/test_rim_highlight.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
```

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py django_apps/asteroid_lab/services/lab_replay_timeline_payload.py tests/unit/asteroid_lab/test_lab_timeline_rim_enrichment.py tests/unit/asteroid_lab/test_rim_highlight_layer_boundary.py
git commit -m "feat(asteroid-lab): enrich lab replay timeline with terrain rim highlight"
```

---

### Task 3: Lab CSS + JS toggle + paint (TDD)

**Files:**
- Modify: `assets/css/input.css`
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- Modify: `django_apps/web/templates/web/asteroid_miner_layout_solver.html`
- Modify: `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py`

- [ ] **Step 1: Write failing UI string tests**

Append to `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py`:

```python
def test_lab_terrain_rim_highlight_toggle_and_css_contract() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    css = (REPO / "assets" / "css" / "input.css").read_text(encoding="utf-8")
    assert 'id="lab-terrain-rim-highlight-toggle"' in template
    assert "lab-terrain-rim-highlight" in template or "Rim highlight" in template
    assert "terrain_rim_highlight" in js
    assert "frozen_terrain_rim_highlight" in js
    assert "applyTerrainRimHighlight" in js
    assert "lab-terrain-rim" in css
    assert "lab-terrain-void-edge-n" in css
    assert "localStorage" in js and "lab-terrain-rim-highlight" in js
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py::test_lab_terrain_rim_highlight_toggle_and_css_contract -v --tb=short
```

- [ ] **Step 3: Add CSS to `assets/css/input.css`**

After `.lab-bundle-bridge-n` block, add:

```css
  .lab-terrain-rim {
    box-shadow: inset 0 0 0 1px rgba(251, 113, 133, 0.45);
    background-color: rgba(76, 5, 25, 0.12);
  }

  .lab-terrain-void-edge-n {
    border-top: 2px solid rgba(253, 164, 175, 0.95);
  }
  .lab-terrain-void-edge-e {
    border-right: 2px solid rgba(253, 164, 175, 0.95);
  }
  .lab-terrain-void-edge-s {
    border-bottom: 2px solid rgba(253, 164, 175, 0.95);
  }
  .lab-terrain-void-edge-w {
    border-left: 2px solid rgba(253, 164, 175, 0.95);
  }
```

Rebuild CSS if project uses a build step (check README); otherwise ensure `app.css` is regenerated per frontend manual.

- [ ] **Step 4: Template toggle**

In `asteroid_miner_layout_solver.html` inside `#lab-timeline-controls`, add:

```html
<label class="flex items-center gap-2 text-xs text-slate-400">
  <input type="checkbox" id="lab-terrain-rim-highlight-toggle" checked />
  Rim highlight
</label>
```

- [ ] **Step 5: Lab JS**

In `asteroid_miner_layout_lab.js`:

1. `const LAB_TERRAIN_RIM_STORAGE_KEY = "lab-terrain-rim-highlight";`
2. `function isTerrainRimHighlightEnabled()` — read checkbox + localStorage default `"1"`
3. `function resolveTerrainRimHighlightWire(frame, trackMetrics)` — `frame.metrics.terrain_rim_highlight ?? trackMetrics.frozen_terrain_rim_highlight`
4. `function applyTerrainRimHighlight(wire, domCells, resolveCellIndex)` — loop rim_cells add `lab-terrain-rim`; void_edge_cells add edge classes via `edges.includes("n")` etc.; set HUD role `terrain_rim` / `terrain_void_edge`
5. Call from `renderFullMapReplayFrame` after bundle strokes if `isTerrainRimHighlightEnabled()`
6. Toggle change listener persists localStorage and re-renders current frame
7. `clearTerrainRimClasses(el)` in `resetGridBase` or before repaint — strip `lab-terrain-rim` and `lab-terrain-void-edge-*` classes

**No dynamic Tailwind** class assembly.

- [ ] **Step 6: Run UI tests + smoke**

```powershell
python -m pytest tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py -v --tb=short
python -m pytest tests/integration/web/test_asteroid_lab_replay_timeline_smoke.py -v --tb=short
```

- [ ] **Step 7: Commit**

```bash
git add assets/css/input.css django_apps/web/static/web/js/asteroid_miner_layout_lab.js django_apps/web/templates/web/asteroid_miner_layout_solver.html tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py
git commit -m "feat(web): lab terrain rim highlight toggle and grid paint"
```

---

### Task 4: Full gate and docs

**Files:**
- Modify: `documents/ai/current_plan.md` (optional queue note — only if team tracks active items there)

- [ ] **Step 1: Narrow asteroid_lab gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rim_highlight.py tests/unit/asteroid_lab/test_lab_timeline_rim_enrichment.py tests/unit/asteroid_lab/test_rim_highlight_layer_boundary.py tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/reconstruction/rim_topology.py django_apps/asteroid_lab/reconstruction/rim_highlight.py django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
```

- [ ] **Step 2: PR full gate (before merge)**

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m mypy django_apps config src
python -m black --check .
```

- [ ] **Step 3: Mark spec plan link in spec (optional)**

Spec § Implementation plan already points here; set `documents/ai/current_plan.md` item when CLOSED after PR.

---

## Plan self-review (2026-05-25)

| Check | Result |
|-------|--------|
| Spec coverage | DTO, wire rules, enrichment, frozen track, UI toggle, CSS, tests, boundary sentence — all tasked |
| Placeholders | None |
| Type consistency | `build_terrain_rim_highlight(complete_map)` / partial factory used throughout |
| Module boundary | Plan blocker paragraph + AST test Task 2 |
| Reviewer hardening | Included in plan + spec § DTO |

---

## Spec coverage map

| Spec section | Task |
|--------------|------|
| Normative boundary | Invariants + boundary test |
| Topology SoT / partial full_map | Task 2 enrichment |
| DTO factories | Task 1 |
| Wire `edges` rules | Task 1 `canonicalize_void_edges` + tests |
| Payload `frozen_terrain_rim_highlight` | Task 2 |
| Frozen reuse | Task 2 tests + enrichment logic |
| Lab toggle + CSS | Task 3 |
| Forbidden optimization import | Task 2 boundary test |
