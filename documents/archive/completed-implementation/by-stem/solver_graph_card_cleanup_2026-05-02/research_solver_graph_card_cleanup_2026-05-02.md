# solver graph card cleanup research

Date: 2026-05-02

## Request summary

- Remove preview card internal scroll
- When multiple inputs enter operation card, separate lines so port mapping is easier to read
- Change current curved edges to straight elbow-style bent segments

## Current structure observations

### 1. Shape card scroll cause

`django_apps/web/static/web/js/solver_timeline/graph_markup.js`

- Shape card root uses `overflow-x-hidden overflow-y-auto` directly.
- Card body grows on `flex-1` and preview area also takes `flex-1`.
- Overlapping badges like `OUTPUT`, `BATCH`, `CONSUMED/UNUSED`, `REUSED` on target/source cards exceed card height and trigger internal scrollbar.

### 2. Edge label overlap cause

- `computeEdgeGeometry()` computes all edge anchors at single vertical center point per node.
- `renderEdgeLabel()` places one `foreignObject` at midpoint.
- Lines like `Input A`, `Input B` into same operation card share nearly same visual position.

### 3. Curved edge implementation location

- `renderEdgePath()` builds only SVG cubic bezier (`C`).
- No port separation per operation input/output; all edges depart/arrive at card center.

## Facts needed for implementation

- Backend payload already provides `edge.slot`, `edge.label`, `edge.kind`, operation `input_count`, `output_count`.
- `recipe_graph_builder.py` builds input edges as `Input A`, `Input B`, ... and outputs as `Output A`, `Output B`, ...
- Lane index can be derived on frontend only; API change not required.

## Change direction

- Shape card: switch to `overflow-hidden` and fixed preview height to eliminate internal scroll.
- Edge anchors: apply slot-based lane offset on operation cards only.
- Edge path: elbow polyline with `M/L`.
- Labels: place near destination last horizontal segment, following lane offset so they read with input ports.

## Test direction

- On graph markup render string:
  - confirm `overflow-y-auto` removed
  - confirm no cubic bezier `C` in path; uses `L`-based bent path
  - confirm `Input A`, `Input B` edge geometry destination `y` differ
- Keep existing layout tests for left→right monotonicity and bounds stability.
