# Operation: Cutter / Quad Cutter

## This Repo (`cut_vertical_halves`)

Vertical halving splits **west (SW+NW)** and **east (NE+SE)**; return order is **`(west_half, east_half)`**. Prefer these names over `left`/`right` to align with [shape_encoding.md](shape_encoding.md).

## shapez 1 Wiki-Style Summary

- **Cutter**: Cuts input shape **vertically in half**. Left and right halves exit as **separate outputs**.
- **Quad Cutter**: Cuts shape into **4 quadrants**.

## Solver Signature (Conceptual)

```text
cut_half(shape) -> (west_half, east_half)
quad_cut(shape) -> (NE, SE, SW, NW)   # per-quadrant output definition fixed by implementation/game board
```

## Coordinate System Note

- Cutter cuts in **shape coordinate system (code/quadrant array)**, not "how the player views shape rotation".
- To cut in a desired direction, you may need **rotate first → then cut**.

## Shapez 2: Output Order

If east/west labels and **which output is main vs secondary** diverge from game/wiki and code, graph wiring twists. See [shapez2_cutter_outputs.md](shapez2_cutter_outputs.md) for values.

## Sources and Trust

- shapez 1 Fandom and similar community wikis: **Medium–High** (cross-verification recommended).
