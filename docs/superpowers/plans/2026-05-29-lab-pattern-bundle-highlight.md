# Lab Pattern Bundle Highlight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show genetic-sample equipment silhouettes (miner + extension, no belts) on Lab replay via thin SVG outlines with server-assigned colors.

**Architecture:** Extract shared cell-hull outline tracing from rim highlight; build `pattern_bundle_highlights` wire on L3/L4 segment compose and on timeline enrichment from `equipment_bundles`; Lab JS renders SVG paths using server `color_index` only.

**Tech Stack:** Python 3.12 / Django, pytest, vanilla Lab JS, Tailwind-built `input.css`

**Spec:** [`docs/superpowers/specs/2026-05-29-lab-pattern-bundle-highlight-design.md`](../specs/2026-05-29-lab-pattern-bundle-highlight-design.md)

---

## File map

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/reconstruction/cell_hull_outline.py` | Occupied cells → corner-lattice outline loops (shared geometry) |
| `django_apps/asteroid_lab/reconstruction/rim_highlight.py` | Refactor to call `cell_hull_outline` for void boundary (behavior unchanged) |
| `django_apps/asteroid_lab/replay/pattern_bundle_highlight.py` | Color assignment + wire builder (output-only) |
| `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py` | Attach wire to frames with `equipment_bundles` |
| `django_apps/asteroid_lab/replay/layer03_segment.py` | Probe-window metrics at compose time |
| `django_apps/asteroid_lab/replay/layer04_segment.py` | Selected-placement metrics at compose time |
| `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py` | Call enrichment after rim |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Toggle, SVG render, skip legacy borders when on |
| `assets/css/input.css` | Pattern outline palette + stroke width |
| `django_apps/web/templates/web/asteroid_miner_layout_solver.html` | Toggle checkbox |
| `documents/ai/lab_map_rendering_contract.md` | Document new wire + toggle |

---

### Task 1: Cell hull outline helper

**Files:**
- Create: `django_apps/asteroid_lab/reconstruction/cell_hull_outline.py`
- Modify: `django_apps/asteroid_lab/reconstruction/rim_highlight.py`
- Test: `tests/unit/asteroid_lab/test_cell_hull_outline.py`
- Test: `tests/unit/asteroid_lab/test_rim_highlight.py` (must stay green)

- [ ] **Step 1: Write the failing hull tests**

```python
# tests/unit/asteroid_lab/test_cell_hull_outline.py
from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.cell_hull_outline import (
    build_cell_hull_outline_loops,
)


def test_single_cell_hull_is_closed_rectangle() -> None:
    loops = build_cell_hull_outline_loops(frozenset({(1, 0)}))
    assert len(loops) == 1
    loop = loops[0]
    assert len(loop) >= 4
    assert loop[0] == loop[-1]


def test_two_separated_cells_yield_two_loops() -> None:
    loops = build_cell_hull_outline_loops(frozenset({(1, 0), (5, 0)}))
    assert len(loops) == 2


def test_empty_occupied_returns_empty() -> None:
    assert build_cell_hull_outline_loops(frozenset()) == ()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/asteroid_lab/test_cell_hull_outline.py -v`  
Expected: FAIL — `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Implement `cell_hull_outline.py`**

Move segment collection + `_trace_outline_loops` logic from `rim_highlight.py` into:

```python
# django_apps/asteroid_lab/reconstruction/cell_hull_outline.py
"""Corner-lattice hull outlines for occupied unit cells (geometry only)."""

from __future__ import annotations

from collections import defaultdict

from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_EDGE_NEIGHBOR: dict[str, tuple[int, int]] = {
    "n": (0, -1),
    "e": (1, 0),
    "s": (0, 1),
    "w": (-1, 0),
}

_SIDE_SEGMENTS: tuple[tuple[str, tuple[Coord, Coord]], ...] = (
    ("n", ((0, 0), (1, 0))),
    ("e", ((1, 0), (1, 1))),
    ("s", ((1, 1), (0, 1))),
    ("w", ((0, 1), (0, 0))),
)


def _exterior_segments_for_occupied(
    occupied: frozenset[Coord],
) -> list[tuple[Coord, Coord]]:
    segments: list[tuple[Coord, Coord]] = []
    for x, y in occupied:
        for ch, (dx, dy) in _EDGE_NEIGHBOR.items():
            if (x + dx, y + dy) in occupied:
                continue
            for side_ch, (a, b) in _SIDE_SEGMENTS:
                if side_ch != ch:
                    continue
                segments.append(((x + a[0], y + a[1]), (x + b[0], y + b[1])))
                break
    return segments


def _normalize_edge(a: Coord, b: Coord) -> tuple[Coord, Coord]:
    return (a, b) if a <= b else (b, a)


def _trace_outline_loops(
    segments: list[tuple[Coord, Coord]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    # Copy existing implementation from rim_highlight._trace_outline_loops unchanged
    ...


def build_cell_hull_outline_loops(
    occupied: frozenset[Coord],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    if not occupied:
        return ()
    return _trace_outline_loops(_exterior_segments_for_occupied(occupied))
```

Refactor `rim_highlight._outer_outline_loops` to use void-boundary segments as today (keep `_void_boundary_segments` in `rim_highlight.py`); only share `_trace_outline_loops` via import from `cell_hull_outline` OR duplicate trace in one place — prefer **single** `_trace_outline_loops` in `cell_hull_outline` exported for rim.

- [ ] **Step 4: Run hull + rim tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_cell_hull_outline.py tests/unit/asteroid_lab/test_rim_highlight.py -v`  
Expected: PASS

- [ ] **Step 5: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/reconstruction/cell_hull_outline.py django_apps/asteroid_lab/reconstruction/rim_highlight.py tests/unit/asteroid_lab/test_cell_hull_outline.py`

---

### Task 2: Pattern bundle highlight wire + color assignment

**Files:**
- Create: `django_apps/asteroid_lab/replay/pattern_bundle_highlight.py`
- Test: `tests/unit/asteroid_lab/test_pattern_bundle_highlight.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/asteroid_lab/test_pattern_bundle_highlight.py
from __future__ import annotations

from django_apps.asteroid_lab.replay.pattern_bundle_highlight import (
    assign_bundle_color_indices,
    build_pattern_bundle_highlights_wire,
)


def test_adjacent_bundles_get_different_color_index() -> None:
    a = frozenset({(1, 0), (2, 0)})
    b = frozenset({(3, 0), (4, 0)})
    indices = assign_bundle_color_indices((a, b))
    assert indices[0] != indices[1]


def test_wire_excludes_empty_and_has_version() -> None:
    wire = build_pattern_bundle_highlights_wire(
        (
            ("k1", frozenset({(1, 0)}), "miner_seed_m0e_01"),
            ("k2", frozenset({(5, 0)}), "miner_seed_m1e_01"),
        )
    )
    assert wire["version"] == 1
    bundles = wire["bundles"]
    assert len(bundles) == 2
    assert bundles[0]["bundle_key"] == "k1"
    assert bundles[0]["gene_key"] == "miner_seed_m0e_01"
    assert "color_index" in bundles[0]
    assert bundles[0]["outline_loops"]


def test_wire_empty_when_no_entries() -> None:
    assert build_pattern_bundle_highlights_wire(()) == {}
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_pattern_bundle_highlight.py -v`

- [ ] **Step 3: Implement module**

```python
# django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
"""Pattern bundle highlight wire for Lab replay (output-only)."""

METRICS_KEY = "pattern_bundle_highlights"
PALETTE_SIZE = 8


def assign_bundle_color_indices(
    bundle_occupied_sets: Sequence[frozenset[Coord]],
) -> tuple[int, ...]:
    # Greedy on 4-neighbor adjacency; see spec
    ...


def build_pattern_bundle_highlights_wire(
    entries: Sequence[tuple[str, frozenset[Coord], str | None]],
) -> dict[str, object]:
    ...
```

Use `build_cell_hull_outline_loops` for each entry's occupied set. Sort entries by `bundle_key` before coloring for stability.

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_pattern_bundle_highlight.py -v`

- [ ] **Step 5: Architecture guard (optional narrow test)**

Add to `tests/unit/architecture/` or existing import-lint pattern if present: assert `layers/stack_runner.py` does not import `pattern_bundle_highlight` (manual grep in PR checklist if no test harness).

---

### Task 3: L3 segment compose wiring

**Files:**
- Modify: `django_apps/asteroid_lab/replay/layer03_segment.py`
- Test: `tests/unit/asteroid_lab/replay/test_layer03_pattern_bundle_highlights.py`

- [ ] **Step 1: Write failing L3 test**

```python
# tests/unit/asteroid_lab/replay/test_layer03_pattern_bundle_highlights.py
from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer03_observability import Layer03Observability
from django_apps.asteroid_lab.layers.contracts.layer03_observability import Layer03SkipReason
from django_apps.asteroid_lab.replay.event_types import EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW
from django_apps.asteroid_lab.replay.layer03_segment import build_layer03_runtime_segment_specs
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    make_route_probed_candidate_for_test,
)


def test_probe_window_metrics_include_pattern_bundle_highlights() -> None:
    entry = make_route_probed_candidate_for_test()
    obs = Layer03Observability(
        skip_reason=Layer03SkipReason.NONE,
        rim_anchor_count=1,
        route_probe_attempt_count=1,
        route_probe_succeeded_count=1,
        normal_candidate_count=1,
        diagnostic_rejected_count=0,
        reject_reason_counts=(),
        replay_pool_candidates=(entry,),
    )
    specs = build_layer03_runtime_segment_specs(observability=obs)
    probe = [s for s in specs if s.event_type.value == EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW]
    assert len(probe) == 1
    highlights = probe[0].metrics.get("pattern_bundle_highlights")
    assert highlights is not None
    bundles = highlights["bundles"]
    assert len(bundles) >= 1
    assert bundles[0]["bundle_key"] == entry.candidate.candidate_id
```

Adjust fixture import to match repo's actual `make_route_probed_candidate_for_test` location (grep before implementing).

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_layer03_pattern_bundle_highlights.py -v`

- [ ] **Step 3: Wire L3 segment**

In `layer03_segment.py`, add helper:

```python
def _pattern_bundle_highlights_for_plan(plan: PoolProbeWindowPlan) -> dict[str, object]:
    entries = [
        (
            entry.candidate.candidate_id,
            entry.candidate.mining_occupied_cells,
            entry.candidate.gene_key,
        )
        for entry in plan.candidates
    ]
    return build_pattern_bundle_highlights_wire(entries)
```

Merge into `_probe_window_metrics` return dict under key `pattern_bundle_highlights` (full wire object, not nested twice).

- [ ] **Step 4: Run test — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_layer03_pattern_bundle_highlights.py -v`

---

### Task 4: L4 selected-placement wiring

**Files:**
- Modify: `django_apps/asteroid_lab/replay/layer04_segment.py`
- Test: `tests/unit/asteroid_lab/replay/test_layer04_pattern_bundle_highlights.py`

- [ ] **Step 1: Write failing L4 test**

Use `build_layer04_runtime_segment_specs` with one `RimBundlePlacement` from `tests/unit/asteroid_lab/layers/fixtures/layer_04_placement_helpers.py`. Assert selected frame metrics contain `pattern_bundle_highlights` with equipment coords only (stub coords not in any loop point set).

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement**

For each `LAYER04_RIM_CANDIDATE_SELECTED` spec metrics, add:

```python
occupied = placement.extractor_cells | placement.extension_cells
wire = build_pattern_bundle_highlights_wire(
    ((placement.candidate_id, occupied, placement.gene_key),)
)
```

Do **not** add highlights to overlap-rejected-only frames without placement geometry.

- [ ] **Step 4: Run test — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_layer04_pattern_bundle_highlights.py -v`

---

### Task 5: Timeline enrichment for `equipment_bundles`

**Files:**
- Create: `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- Modify: `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`
- Test: `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`

- [ ] **Step 1: Write failing enrichment test**

Build minimal serialized frame dict with `cell_overlay_json.equipment_bundles` from `build_equipment_bundles` on two separated miners; call enricher; assert `metrics.pattern_bundle_highlights.bundles` length == 2.

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Implement enrichment**

```python
def enrich_lab_timeline_frames_with_pattern_bundle_highlights(
    frames: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for frame in frames:
        frame_copy = copy.deepcopy(frame)
        wire = _wire_from_frame_overlay(frame)
        if wire:
            metrics = dict(frame_copy.get("metrics") or {})
            metrics[METRICS_KEY] = wire
            frame_copy["metrics"] = metrics
        out.append(frame_copy)
    return out
```

Skip frames that already have `pattern_bundle_highlights` from L3/L4 compose (do not overwrite).

Hook in `lab_replay_timeline_payload.py`:

```python
serialized = enrich_lab_timeline_frames_with_pattern_bundle_highlights(serialized)
```

after rim enrichment line.

- [ ] **Step 4: Run test — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`

---

### Task 6: Lab JS + CSS + template

**Files:**
- Modify: `django_apps/web/templates/web/asteroid_miner_layout_solver.html`
- Modify: `assets/css/input.css`
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- Test: `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py`

- [ ] **Step 1: Extend UI contract test (failing)**

```python
def test_lab_pattern_bundle_highlight_toggle_and_css_contract() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    js = (REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js").read_text(encoding="utf-8")
    css = (REPO / "assets" / "css" / "input.css").read_text(encoding="utf-8")
    assert 'id="lab-pattern-bundle-highlight-toggle"' in template
    assert "pattern_bundle_highlights" in js
    assert "applyPatternBundleHighlightSvg" in js
    assert "lab-pattern-bundle-outline-path" in css
    assert "lab-pattern-bundle-highlight" in js
```

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Template toggle**

Next to rim toggle:

```html
<label class="flex items-center gap-2 text-slate-400">
  <input type="checkbox" id="lab-pattern-bundle-highlight-toggle" checked />
  Pattern highlight
</label>
```

- [ ] **Step 4: CSS**

```css
.lab-pattern-bundle-outline-svg {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
}

.lab-pattern-bundle-outline-path {
  fill: none;
  stroke-width: 1.25;
  stroke-linejoin: round;
  stroke-linecap: round;
}

.lab-pattern-bundle-outline-path[data-color-index="0"] { stroke: rgba(250, 204, 21, 0.95); }
/* ... indices 1-7 ... */
```

- [ ] **Step 5: JS**

- Constants: `LAB_PATTERN_BUNDLE_STORAGE_KEY = "lab-pattern-bundle-highlight"`
- `clearPatternBundleOutlineSvg()` — remove `.lab-pattern-bundle-outline-svg` only
- Update `clearTerrainRimOutlineSvg()` — remove `.lab-terrain-rim-outline-svg` only (stop using `layer.textContent = ""`)
- `applyPatternBundleHighlightSvg(wire, layout, cellPx, gapPx)` — loop bundles, set `d` + `data-color-index`
- In `renderFullMapReplayFrame`: if pattern enabled, call `applyPatternBundleHighlightSvg`; else `clearPatternBundleOutlineSvg`
- Gate `applyEquipmentBundleGroupVisualsFromOverlay` behind `!isPatternBundleHighlightEnabled()`
- Wire toggle listener beside rim toggle (`persist` + re-render current frame)

- [ ] **Step 6: Build CSS**

Run: `npm run build:css` (or project script documented in `test_asteroid_lab_ui_strings`)

- [ ] **Step 7: Run UI test — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py::test_lab_pattern_bundle_highlight_toggle_and_css_contract -v`

---

### Task 7: Documentation

**Files:**
- Modify: `documents/ai/lab_map_rendering_contract.md`

- [ ] **Step 1: Add section "Pattern bundle highlight"**

Document: `metrics.pattern_bundle_highlights`, toggle id, server `color_index`, legacy bundle border skip when on, separate SVG root from rim.

---

### Task 8: Integration verification

- [ ] **Step 1: Run narrow asteroid_lab tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_cell_hull_outline.py tests/unit/asteroid_lab/test_pattern_bundle_highlight.py tests/unit/asteroid_lab/replay/test_layer03_pattern_bundle_highlights.py tests/unit/asteroid_lab/replay/test_layer04_pattern_bundle_highlights.py tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py tests/unit/asteroid_lab/test_rim_highlight.py tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py -v`

Expected: PASS

- [ ] **Step 2: Ruff on touched paths**

Run: `python -m ruff check django_apps/asteroid_lab/reconstruction/cell_hull_outline.py django_apps/asteroid_lab/replay/pattern_bundle_highlight.py django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py django_apps/asteroid_lab/replay/layer03_segment.py django_apps/asteroid_lab/replay/layer04_segment.py`

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| Server-only graph coloring | Task 2 |
| `replay/pattern_bundle_highlight.py` + import ban | Task 2, PR checklist |
| L3 compose-time, no candidate_ids re-query | Task 3 |
| L4 frame-native equipment cells | Task 4 |
| `equipment_bundles` enrichment | Task 5 |
| SVG + thin stroke + palette | Task 6 |
| Legacy border skip when on | Task 6 |
| Acceptance criteria tests | Tasks 1–6 |
| `lab_map_rendering_contract.md` | Task 7 |

No TBD placeholders in task steps.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-29-lab-pattern-bundle-highlight.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with executing-plans checkpoints  

Which approach do you want?
