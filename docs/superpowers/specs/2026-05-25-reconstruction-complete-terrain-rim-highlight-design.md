# Reconstruction-Complete Terrain Rim Highlight — Design Spec

**Date:** 2026-05-25  
**Status:** Approved (2026-05-25 — Reconstruction/UI Contract Reviewer; five amendments applied)  
**Work classification:** contract change · UI change  
**Surfaces:** `django_apps/asteroid_lab/reconstruction/` (rim DTO factory), `lab_replay_timeline_payload` (enrichment), Lab replay grid (`asteroid_miner_layout_lab.js`, `input.css`)

**Normative boundary (required):**

```text
Terrain rim highlight is a replay/UI observability artifact.
It is derived from ReconstructionCompleteMap or renderable reconstruction frame data,
and must never become solver, topology, capacity, candidate, route, commit, or validation input.
```

**Related:**

- [`2026-05-26-reconstruction-complete-map-dto-design.md`](2026-05-26-reconstruction-complete-map-dto-design.md) — `ReconstructionCompleteMap` terrain SoT
- [`2026-05-25-reconstruction-field-cell-capacity-contract-design.md`](2026-05-25-reconstruction-field-cell-capacity-contract-design.md) — mineable / field-cell terminology
- [`documents/Algorithm/asteroid_lab_00_overview.md`](../../../documents/Algorithm/asteroid_lab_00_overview.md) — `rim_cells` = candidate anchor filter, not install order
- Sequence 13 Lab replay payload size risks (POST JSON · DevTools observability)

**Non-goals:**

- Implementing or populating `ReconstructionResult.outer_rim_coords` (separate shell-rim track)
- Client-side topology that duplicates `acceptance_topology` / `_rim_cells` for algorithm parity
- Using replay `full_map` or `metrics.terrain_rim_highlight` as solver / RTTP / validation input
- Large golden JSON fixtures for rim wire unless explicitly approved

---

## Problem

After reconstruction completes, Lab users need to see **where mineable field meets non-field** (rim) and **which rim edges face external void** (export / route margin intuition). Today the grid shows per-`cell_kind` tones only; RTTP `rim_cells` and `external_void_cells` are invisible in the product timeline.

Requirements (brainstorming lock):

| Dimension | Choice |
|-----------|--------|
| Rim definition | **A** mineable rim (field cell with 4-neighbor ∉ `field_cells`) + **D** edges whose neighbor ∈ `external_void_cells` |
| Visual | **Single outer contour stroke:** chain `external_void`-facing boundary segments into closed loop(s); Lab draws one SVG path (rose stroke), **not** per-cell fill |
| When visible | Reconstruction phase frames with renderable `full_map`; post-complete frames reuse frozen complete snapshot; UI toggle default **on** |

---

## Architectural decision

### Approach (approved)

**Server-side enrichment at Lab timeline compose** (not persist-time bake-in; not JS-only topology).

1. Canonical rim DTO from `ReconstructionCompleteMap` (or explicit partial sets for in-progress frames).
2. Attach to `ReplayTimelineFrame.metrics["terrain_rim_highlight"]` (output-only).
3. Lab JS paints using static CSS classes (no dynamic Tailwind fragments).
4. Post-complete semantic identity = **one frozen DTO value** reused across frames (see § Frozen snapshot).

Rejected:

- Reading replay `full_map` inside solver / optimization / validation paths
- Per-frame rim recompute after `reconstruction.completed` (semantic drift vs capacity SoT)

---

## Topology SoT

| Set | Definition | Source |
|-----|------------|--------|
| `field_cells` | Coords with `cell_kind ∈ {asteroid_shape_field, asteroid_fluid_field}` | `ReconstructionCompleteMap.field_cells` or partial frame extraction |
| `rim_cells` (**A**) | `{ c ∈ field_cells \| ∃ neighbor4(c) ∉ field_cells }` | Same rule as `optimization.reconstruction_adapter._rim_cells` |
| `external_void_cells` (**D**) | Flood-fill exterior void (acceptance topology) | `ReconstructionCompleteMap.external_void_cells` or partial topology from renderable cells |
| `void_edge_cells` (**D**) | Subset of rim cells + per-cell outward edges into `external_void_cells` | Derived; see § Wire contract |

**Partial reconstruction frames:** Each renderable reconstruction-phase frame’s `full_map` is used **only** as UI/replay enrichment input to derive `(field_cells, external_void_cells)` for that frame’s highlight. Solver/topology/capacity SoT remains `ReconstructionCompleteMap` built from `cleanup + recon` at pipeline boundaries; replay `full_map` must not flow backward into those builders.

---

## DTO contracts (Python)

### `TerrainRimHighlightDTO` (frozen dataclass or typed dict factory output)

```python
@dataclass(frozen=True, slots=True)
class TerrainRimHighlightDTO:
    version: int  # always 1 for this spec
    rim_cells: tuple[tuple[int, int], ...]
    void_edge_cells: tuple[VoidEdgeCellDTO, ...]
    coord_frame: CoordFrame


@dataclass(frozen=True, slots=True)
class VoidEdgeCellDTO:
    x: int
    y: int
    edges: str  # subset of "nesw", canonical order — see wire rules
```

### Factory entry points (no ambiguous `cells` parameter)

**Complete map (canonical for freeze + tests):**

```python
def build_terrain_rim_highlight(
    complete_map: ReconstructionCompleteMap,
) -> TerrainRimHighlightDTO:
    """Rim + void edges from complete-map SoT."""
```

**In-progress reconstruction frames (partial, same topology rules):**

```python
def build_terrain_rim_highlight_from_renderable_cells(
    *,
    field_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
    coord_frame: CoordFrame,
) -> TerrainRimHighlightDTO:
    """Replay/UI enrichment only — not solver input."""
```

Implementation may delegate: `build_terrain_rim_highlight(cm)` calls `build_terrain_rim_highlight_from_renderable_cells(field_cells=cm.field_cells, external_void_cells=cm.external_void_cells, coord_frame=cm.coord_frame)`.

**Module home:** `django_apps/asteroid_lab/reconstruction/rim_highlight.py` (re-export in `__all__` as needed).

**Module boundary (production):**

```text
Production rim_highlight.py must not import optimization.* modules.
Parity with optimization.reconstruction_adapter._rim_cells is test-only,
or the shared neighbor rule must live in a neutral reconstruction/topology helper.
```

**Parity tests (required):** `rim_cells` in DTO equals `_rim_cells(field_cells)` (test-only import); `void_edge_cells` coords ⊆ `rim_cells`.

---

## Wire contract (`metrics`, JSON-serializable)

Embedded at:

```text
ReplayTimelineFrame.metrics["terrain_rim_highlight"]
```

Optional track-level fallback (payload budget):

```text
track_metrics["frozen_terrain_rim_highlight"]
```

### Shape

```json
{
  "terrain_rim_highlight": {
    "version": 1,
    "coord_frame": "island_raw",
    "rim_cells": [[12, 5], [13, 5]],
    "void_edge_cells": [
      {"x": 12, "y": 5, "edges": "nw"},
      {"x": 13, "y": 5, "edges": "e"}
    ]
  }
}
```

### `void_edge_cells.edges` rules (testable)

```text
- Allowed characters: n, e, s, w only.
- Canonical order when serializing: n, then e, then s, then w (e.g. "nw" not "wn").
- Unknown characters are forbidden (deserialization / enrichment must reject or drop frame highlight).
- Empty edges string is forbidden — omit that void_edge_cells entry entirely.
- Every void_edge_cells (x, y) must be in rim_cells.
- Neighbor in external_void_cells is required for each listed edge direction.
```

### Payload budget (Sequence 13 alignment)

- **No large golden JSON** for rim wire in repo unless explicitly approved.
- Prefer compact coords: `rim_cells` as `[[x,y],...]`; omit redundant fields on post-complete frames when `track_metrics.frozen_terrain_rim_highlight` is present (Lab JS resolves: per-frame metrics → else track frozen).
- During reconstruction phase, per-frame highlights may differ — attach per frame only while `inspector.lab_phase == "reconstruction"` and map is renderable.
- Cap: if enrichment would exceed existing replay frame budget policies, drop highlight for that frame (never truncate solver frames).

---

## Enrichment pipeline

**Hook:** `build_lab_replay_frames_for_project()` after `compose_replay_timeline` + `interleave_rttp_snapshot_frames`, before return.

**Function:** `enrich_lab_timeline_frames_with_terrain_rim(frames: list[dict]) -> list[dict]` (pure; deep-copy metrics dict when mutating).

### Per-frame rules

| Condition | `terrain_rim_highlight` |
|-----------|-------------------------|
| `inspector.lab_phase == "reconstruction"` and renderable `map_view` | Compute via `build_terrain_rim_highlight_from_renderable_cells` from that frame’s `full_cells` (+ topology helper shared with acceptance) |
| `event_type == "reconstruction.completed"` (or lab wire `reconstruction.map_complete`) | Build from merged complete cells equivalent; set **frozen** DTO value |
| Post-complete (RTTP milestones, result layout, etc.) | **Reuse frozen complete snapshot value** — same semantic DTO as at completion |
| Decode / non-renderable | Omit key |

### Frozen snapshot (amendment 4)

```text
Post-complete frames reuse the frozen complete reconstruction rim snapshot value.
Implementations may copy the serialized dict for mutation safety,
but semantic identity must remain the completed reconstruction rim snapshot.
Recompute on post-complete frames is forbidden.
```

**Track fallback:** When post-complete frame omits per-frame key, Lab reads `track_metrics.frozen_terrain_rim_highlight` (same semantic value).

**Building frozen value:** Prefer `build_terrain_rim_highlight(complete_map)` at solver boundary where `cleanup + recon` are available; when enriching persisted replay only, derive complete-equivalent cells from final reconstruction `full_map` for **display enrichment only** (still not solver input).

---

## Lab UI

### Toggle (requirement 4)

- Control: checkbox **「Rim highlight」** near timeline controls.
- Default: **checked**.
- Persistence: `localStorage` key `lab-terrain-rim-highlight` (`"1"` / `"0"`).
- When off: skip rim paint after `renderFullMapReplayFrame`; do not alter base `full_map` tones.

### Rendering

After `renderFullMapCells` / diff / bundle strokes:

1. Resolve highlight: `frame.metrics.terrain_rim_highlight` ?? `trackMetrics.frozen_terrain_rim_highlight`.
2. Read `outer_outline_loops[0]` (primary closed polygon in corner lattice coords).
3. Map corners to stage pixels (`visualCol` + replay layout) and draw **one** `<path>` on `#lab-optimization-overlay-layer` (class `lab-terrain-rim-outline-path`).
4. Do **not** tint individual rim cells; `rim_cells` / `void_edge_cells` remain for HUD/debug wire only.

### CSS (amendment 5 — no dynamic Tailwind)

Add to `django_apps/web/static/web/css` (or `assets/css/input.css` per project convention):

```css
.lab-terrain-rim {
  box-shadow: inset 0 0 0 1px rgba(251, 113, 133, 0.45);
  background-color: rgba(76, 5, 25, 0.12);
}

.lab-terrain-void-edge-n { border-top: 2px solid rgba(253, 164, 175, 0.95); }
.lab-terrain-void-edge-e { border-right: 2px solid rgba(253, 164, 175, 0.95); }
.lab-terrain-void-edge-s { border-bottom: 2px solid rgba(253, 164, 175, 0.95); }
.lab-terrain-void-edge-w { border-left: 2px solid rgba(253, 164, 175, 0.95); }
```

Do **not** build class names from runtime color tokens (`border-${color}-300`).

### HUD

| Hover target | `data-overlay-role` / HUD role text |
|--------------|-------------------------------------|
| Rim cell (no void edge on that side) | `terrain_rim` |
| Cell with void edge | `terrain_void_edge` |

---

## Testing

| Layer | Test |
|-------|------|
| unit | `test_rim_highlight.py`: rim parity with `_rim_cells`; void edges ⊆ rim; `edges` canonical order; invalid char raises |
| unit | `test_lab_timeline_rim_enrichment.py`: reconstruction frames differ when field grows; post-complete frames share identical serialized highlight value; frozen in track_metrics |
| unit | forbidden shortcut guard: no import of `terrain_rim_highlight` from `optimization/` commit/validation modules |
| UI strings | `test_asteroid_lab_ui_strings.py`: toggle id, CSS class names, metrics key string |
| integration smoke | existing Lab page smoke still loads; optional assert `terrain_rim_highlight` key present after solver run fixture |

---

## Risks

| Risk | Mitigation |
|------|------------|
| POST JSON growth | Track-level frozen DTO; omit duplicate on post-complete frames |
| Topology drift JS vs Python | No client topology; server-only enrichment |
| Tailwind purge | Static CSS classes only |
| Confusion with `outer_rim_coords` | Document non-goal; use `terrain_rim_highlight` wire name |

---

## Implementation plan

Invoke **writing-plans** → `docs/superpowers/plans/2026-05-25-reconstruction-complete-terrain-rim-highlight.md` after spec review.

**Suggested PR slices:**

1. `rim_highlight.py` + unit tests (DTO + wire rules)
2. Timeline enrichment + track_metrics frozen
3. Lab JS + CSS + toggle + UI strings tests

---

## Spec self-review (2026-05-25)

| Check | Result |
|-------|--------|
| Placeholders / TBD | None |
| Internal consistency | Partial vs complete factories aligned; frozen reuse vs per-frame reconstruction clear |
| Scope | Single plan; no solver behavior change |
| Ambiguity | `edges` order and forbidden chars specified; `cells` ambiguous arg removed |
| Boundary line | Required normative sentence present |
| Reviewer amendments 1–5 | Applied |
