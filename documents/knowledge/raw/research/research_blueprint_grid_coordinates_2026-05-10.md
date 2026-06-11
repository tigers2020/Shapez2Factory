# Asteroid / world map grid coordinates (no `x == 0` column)



**Status**: Contract fixed (not a plan experiment draft)



## Copy JSON vs world map (do not mix)



**Shapez2 copy JSON** `BP.Entries` `X`/`Y` are **island blueprint local** coordinates (omitted → `0`; `X==0` is valid). See [`research_shapez2_copy_json_island_local_coords_2026-05-23.md`](research_shapez2_copy_json_island_local_coords_2026-05-23.md).



**This document** applies to the **asteroid / lab world map** after reconstruction (`asteroid_map_coords`, transport BFS): integer column **`x == 0` does not exist**.



## Proposition (world map)



On the asteroid·lab world grid, there is **no tile or column with integer column x where `x == 0`.**



When code uses tile coordinates `(x, y)`, likewise **there is no cell with `x == 0`.** This is a **world grid model** proposition, not decode mistake defense.



## East–west direction and adjacency



- Because **there is no column 0** between positive and negative columns, the nearest positive column west `x == 1` and east negative column `x == -1` are **not two consecutive cells in coordinate space** but in blueprint physics are treated as **east–west adjacent neighbors**.

- So east–west one-step movement allows **`1 ↔ -1` jump** without passing through **`0`.**



Reference implementation code was removed from the repo. Any new coordinate movement or legality checks must satisfy this proposition.



## North–south caution



Assume **no vertical line with `x == 0` exists.** When setting routing·visualization·test coordinates, **do not assume north–south corridors near `x = 0`.**



## Server·API



After decode, **exclude entries with `X == 0`** from computation·summary·API output. Upper-layer contract: [`.cursor/rules/architecture.mdc`](../../.cursor/rules/architecture.mdc).



## Related Documents·Code



- Rule summary: [`AGENTS.md`](../../AGENTS.md) (blueprint coordinates one-liner)

- Architecture: [`.cursor/rules/architecture.mdc`](../../.cursor/rules/architecture.mdc)

