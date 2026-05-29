# Lab Pattern Bundle Highlight — Design Spec

**Date:** 2026-05-29  
**Status:** Approved (2026-05-29 — Replay/UI Contract Architect; amendments applied)  
**Work classification:** contract change · UI change  
**Surfaces:** `django_apps/asteroid_lab/replay/` (wire + segment compose), `reconstruction/` (shared hull helper only), Lab replay (`asteroid_miner_layout_lab.js`, `input.css`, solver template)

**Normative boundary (required):**

```text
Pattern bundle highlight is a replay/UI observability artifact.
It is derived from genetic-sample equipment footprints (miner + extension only)
and must never become solver, topology, capacity, candidate, route, commit, or validation input.
```

**Related:**

- [`2026-05-25-reconstruction-complete-terrain-rim-highlight-design.md`](2026-05-25-reconstruction-complete-terrain-rim-highlight-design.md) — corner lattice SVG outline pattern
- [`2026-05-28-layer-03-full-pool-windowed-replay-design.md`](2026-05-28-layer-03-full-pool-windowed-replay-design.md) — L3 probe-window frames
- [`documents/ai/lab_map_rendering_contract.md`](../../../documents/ai/lab_map_rendering_contract.md) — Lab grid rendering

**Non-goals:**

- Django Admin genetic sample minimap
- Highlighting `candidate_transport_stub`, `transport_stub`, route paths, or belt cells
- Client-side graph coloring when server `color_index` is present
- Reconstructing candidate geometry from `candidate_ids` during timeline enrichment

---

## Problem

Lab users need to see **genetic-sample pattern silhouettes** (miner + extension layout from DB seeds) at a glance—especially on L3 pool probe windows where many candidates overlap. Per-cell `border-2` equipment bundle strokes are thick and hard to distinguish when bundles are adjacent.

Requirements (approved):

| Dimension | Choice |
|-----------|--------|
| Footprint SoT | `mining_occupied_cells` (L3/L4) or `equipment_bundles[].cells_json` (committed map) — **belts excluded** |
| Visual | Rim-style **SVG outline** on `#lab-optimization-overlay-layer`, **thinner stroke** (~1.25px) |
| Adjacent bundles | **Server** greedy graph coloring → `color_index` on wire |
| Surface | **Lab replay timeline only** |
| Legacy cell borders | **Off** when pattern highlight on; **preserved** when off |

---

## Architectural decision

### Approach (approved)

**Server-side outline + color assignment; Lab JS renders SVG only.**

1. Shared hull builder: occupied cell set → `outline_loops` (corner lattice, same geometry as terrain rim void boundary).
2. Attach `metrics.pattern_bundle_highlights` at **segment compose** (L3/L4) or **timeline enrichment** (full_map + `equipment_bundles`).
3. Lab JS maps `color_index` → fixed stroke palette (no graph coloring on client when `color_index` present).

Rejected:

- JS-only topology or graph coloring as canonical color SoT
- Re-fetching `RouteProbedBundleCandidate` from `candidate_ids` during `enrich_lab_timeline_frames_*`
- Using `transport_stub_cells` / route path cells in highlights

### Module placement

**Primary:** `django_apps/asteroid_lab/replay/pattern_bundle_highlight.py`

```text
pattern_bundle_highlight.py is output-only replay/Lab enrichment support.
It must not be imported by solver placement, routing, validation, or optimization input code.
```

**Shared hull helper:** `django_apps/asteroid_lab/reconstruction/cell_hull_outline.py`  
- Extracted from rim highlight segment tracing; imported by `rim_highlight.py` and `replay/pattern_bundle_highlight.py`.
- `reconstruction/cell_hull_outline.py` is geometry-only; no replay-specific wire types.

---

## Footprint definitions

| Source | Occupied cells | Excluded |
|--------|----------------|----------|
| L3 `RouteProbedBundleCandidate` | `candidate.mining_occupied_cells` | `transport_stub_cells`, route path |
| L4 `RimBundlePlacement` | `extractor_cells ∪ extension_cells` | `output_stub_cells`, `probed_route_path_cells` |
| Committed / cleanup `full_map` | Each `equipment_bundles[]` block via `cells_json` coords | Belts (already omitted by `build_equipment_bundles`) |

**L3 compose rule:**

```text
For L3 probe-window frames, pattern_bundle_highlights must be built from the candidate
objects available during segment composition. Enrichment must not reconstruct candidate
geometry from candidate_ids.
```

**L4 rule:** Include when frame carries frame-native placement artifact (selected provisional placement). Use placement equipment cells only—not rejected-only frames without geometry.

| Frame | `pattern_bundle_highlights` |
|-------|----------------------------|
| `layer03_rim_bundle_pool_probe_window` | Yes — per candidate in window |
| `layer04_rim_candidate_selected` (and equivalent selected overlay frames) | Yes — per selected placement |
| `full_map` + `equipment_bundles` | Yes — per bundle block |
| decode-only / no geometry | Omit key |
| `candidate_ids` only, no cells | Omit key |

---

## Server contracts (Python)

### `PatternBundleHighlightDTO` / wire entry

```python
@dataclass(frozen=True, slots=True)
class PatternBundleWireEntry:
    bundle_key: str
    color_index: int
    outline_loops: tuple[tuple[tuple[int, int], ...], ...]
    gene_key: str | None = None
```

### Functions (`replay/pattern_bundle_highlight.py`)

```python
def build_outline_loops_for_occupied_cells(
    occupied: frozenset[Coord],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Corner-lattice hull; empty occupied → ()."""


def assign_bundle_color_indices(
    bundle_occupied_sets: Sequence[frozenset[Coord]],
) -> tuple[int, ...]:
    """Greedy graph coloring on 4-neighbor bundle adjacency; stable input order."""


def build_pattern_bundle_highlights_wire(
    entries: Sequence[tuple[str, frozenset[Coord], str | None]],
) -> dict[str, object]:
    """Returns {"version": 1, "bundles": [...]} or {} when no bundles."""
```

- `bundle_key`: L3/L4 `candidate_id`; committed map `equipment:{bundle_id}`.
- `gene_key`: set when known (L3/L4 placement metadata).
- `color_index`: `0 .. palette_size-1` from `assign_bundle_color_indices` in **stable bundle order**.

### Color assignment (canonical — server only)

```text
Two bundles are adjacent iff some cell in A is 4-neighbor to some cell in B.
Process bundles in deterministic sort order (bundle_key).
Greedy: assign smallest color_index not used by an adjacent already-colored bundle.
```

Lab JS **must not** re-run graph coloring when every bundle has `color_index`.

Defensive fallback: if `color_index` missing on an entry, map `bundle_key` hash mod palette size (test-only path; production wire always includes `color_index`).

---

## Wire contract (`metrics`, JSON-serializable)

```json
{
  "pattern_bundle_highlights": {
    "version": 1,
    "bundles": [
      {
        "bundle_key": "layer_03:miner_seed_m3e_01:12:5:e:0:shape_belt",
        "gene_key": "miner_seed_m3e_01",
        "color_index": 2,
        "outline_loops": [[[12, 5], [13, 5], [13, 6], [12, 6], [12, 5]]]
      }
    ]
  }
}
```

Embedded at:

```text
ReplayTimelineFrame.metrics["pattern_bundle_highlights"]
```

No track-level frozen snapshot required (bundles vary per frame). Omit key when `bundles` is empty.

---

## Enrichment pipeline

### A) Segment compose (L3 / L4)

- **`replay/layer03_segment.py`:** When building each `layer03_rim_bundle_pool_probe_window` spec, set `metrics["pattern_bundle_highlights"]` from `plan.candidates` → `entry.candidate.mining_occupied_cells` + `gene_key`.
- **`replay/layer04_segment.py`:** When building selected-placement frame specs, set highlights from `extractor_cells | extension_cells` per placement.

### B) Timeline enrichment (committed map)

- **`services/lab_timeline_pattern_bundle_enrichment.py`:** `enrich_lab_timeline_frames_with_pattern_bundle_highlights(frames) -> list[dict]`
- Hook in `build_lab_replay_frames_for_project()` after rim enrichment.
- For each frame with renderable `map_view` and `cell_overlay_json.equipment_bundles`, build wire from bundle `cells_json` coords (equipment only).

**Forbidden during enrichment:**

```text
Reconstructing candidate geometry from metrics.candidate_ids, map_view, or solver DB.
```

---

## Lab UI

### Toggle

- Template: checkbox `lab-pattern-bundle-highlight-toggle`, label `Pattern highlight`, default **checked**.
- `localStorage` key `lab-pattern-bundle-highlight` (`"1"` / `"0"`).

### Rendering

- Reuse `cornerToStagePx` + `#lab-optimization-overlay-layer` (same layer as terrain rim).
- One SVG container class: `lab-pattern-bundle-outline-svg`.
- Per bundle: `<path class="lab-pattern-bundle-outline-path" data-color-index="N">`.
- CSS palette: 8 fixed stroke colors in `input.css` (e.g. `.lab-pattern-bundle-outline-path[data-color-index="0"] { stroke: ... }`).
- `stroke-width: 1.25`; `fill: none`; `stroke-linejoin: round`.

### Interaction with legacy bundle visuals

```text
When pattern highlight enabled:
  - Skip applyEquipmentBundleGroupVisualsFromOverlay (no border-2 / inset / bridges).
When disabled:
  - Preserve existing applyEquipmentBundleGroupVisualsFromOverlay behavior.
```

Rim highlight and pattern highlight may both be on; draw pattern paths after rim clear or in same SVG pass (pattern paths appended after rim path in overlay layer).

### JS functions

- `isPatternBundleHighlightEnabled()`
- `resolvePatternBundleHighlightWire(frame)`
- `applyPatternBundleHighlightSvg(wire, layout, cellPx, gapPx)`
- `clearPatternBundleOutlineSvg()` — clears only pattern SVG nodes (or full layer clear coordinated with rim — prefer dedicated class selector on pattern SVG root to avoid clearing rim).

**Clear strategy:** Pattern SVG root has class `lab-pattern-bundle-outline-svg`; rim uses `lab-terrain-rim-outline-svg`. `clearTerrainRimOutlineSvg` must not remove pattern SVG; `clearPatternBundleOutlineSvg` removes only pattern root.

---

## Acceptance criteria

```text
- pattern_bundle_highlights never contains transport_stub cells.
- pattern_bundle_highlights never contains candidate_route_path cells.
- pattern_bundle_highlights.bundles[*].outline_loops are closed (first point repeats at end).
- Server-provided color_index is stable for deterministic input order.
- UI does not run graph coloring when color_index exists on all bundles.
- Pattern highlight on disables legacy equipment bundle cell border rendering.
- Pattern highlight off preserves legacy applyEquipmentBundleGroupVisualsFromOverlay behavior.
- pattern_bundle_highlight modules are not imported from solver/layer optimization code paths.
- L3 probe-window wire is built at segment compose time, not from candidate_ids re-query.
```

---

## Testing

| Area | Tests |
|------|-------|
| Hull | `tests/unit/asteroid_lab/test_cell_hull_outline.py` — single cell, L-shape, two separated components |
| Wire + color | `tests/unit/asteroid_lab/test_pattern_bundle_highlight.py` — adjacent bundles differ `color_index`; belt coords absent |
| L3 segment | `tests/unit/asteroid_lab/replay/test_layer03_pattern_bundle_highlights.py` — probe window metrics include bundles count == candidates |
| L4 segment | `tests/unit/asteroid_lab/replay/test_layer04_pattern_bundle_highlights.py` — selected frame has highlights from equipment cells only |
| Enrichment | `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py` |
| UI contract | extend `test_asteroid_lab_ui_strings.py` — toggle, CSS classes, JS wire key |

---

## Risks

- **Overlay layer ordering:** Rim + pattern SVG coexistence — use separate SVG roots and scoped clear functions.
- **Payload size:** L3 windows with many candidates multiply loops; bounded by existing pool window caps.
- **assumption:** `mining_occupied_cells` always equals genetic equipment tree (no belt); validated by existing L3 projection tests.
