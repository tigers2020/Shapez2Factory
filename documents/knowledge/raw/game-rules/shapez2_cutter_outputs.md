# Shapez 2: Cutter Output Order (east / west)

## This Repo Implementation (`OperationEngine.cut` / `cut_vertical_halves`)

Quadrant indices per [shape_encoding.md](shape_encoding.md): **SW, NW, NE, SE**. Vertical cut splits **west half** and **east half**.

| Output | Quadrants kept | Meaning |
| --- | --- | --- |
| Tuple `[0]` | `quadrants[0]`, `quadrants[1]` | **west** (SW+NW) |
| Tuple `[1]` | `quadrants[2]`, `quadrants[3]` | **east** (NE+SE) |

Return value order is **`(west_half, east_half)`**. Shapez 2 wiki may say "east is main output" with **different order** — wire cutter output ports in graphs using this repo order.

## Wiki Reference (Game-Side Claims)

wiki.gg search snippets/summaries say Cutter cuts vertically in half and:

- **east half → main output**
- **west half → secondary output**

```text
Game UI perspective (reference) — do not confuse with repo tuple order
```

## Project Warning

If output order diverges from recipe graph **port numbers and wiring direction**, the whole DAG connects incorrectly.

## Trust and Verification Needed

- Wiki: **Medium**. Original pages may be inaccessible; content may be snippet-only.
- Prefer **in-game observation** or official patch notes when implementing.

## Related

- [operation_cutter.md](operation_cutter.md)
