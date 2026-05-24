# 0-extension miner placement suppression (implementation canonical, 2026-05-09)

## Goal

Before Pass3 shortens long pipes, filter **standalone (0-extension) bundles** far from trunk at placement stage.

## Per-context `min_extensions`

| Context | Value | Notes |
|----------|---:|------|
| pass2_spine | 1 | `_place_pass2_spine_phase` |
| pass2_scan | 2 | `_place_scan_pass("pass2")` |
| pass3_scan | 2 | `_place_scan_pass("pass3")` |
| recovery (rail_reloc etc.) | 0 | narrow-space survival |
| `_build_opportunity_score` | 0 (default) | avoid slot estimate distortion — do not change call sites |

Constants: `solver_service.MIN_EXTENSIONS_PASS2_SPINE`, `MIN_EXTENSIONS_PASS2_SCAN`, `MIN_EXTENSIONS_PASS3_SCAN`, `MIN_EXTENSIONS_RECOVERY`.

## 0-extension exception

`placement.stub_outlet_on_or_adjacent_to_transport(out_pos, transport_cell_keys)` — outlet on existing transport cell or 4-adjacent.

Call sites assemble callback via `solver_service._transport_touch_predicate(transport_cells)`.

## Ranking

- `_place_scan_pass`: `rank_key = (-n_ext, ma, -ext_on_boundary, dir_rank[d], ti)`
- `select_best_extension_tree_for_pass2`: `inner = (-n_extensions, ma, -ext_on_boundary, ti)`
- trace: `select_best_extension_tree_for_pass2` exit includes `ranking: extension_count_first`

## Trace keys (relaxed selector)

- `below_min_extensions`
- `zero_extension_rejected_not_trunk_adjacent`
- on success optional: `zero_extension_gate` = `zero_extension_trunk_adjacent_allowed`

## P1 — marginal route · ROI (placement gate)

Use Manhattan lower bound (`shapez_manhattan`) from outlet to **anchor or existing transport** as marginal; filter further with extension-count caps and coarse ROI.

| Constant | Meaning |
|------|------|
| `MAX_MARGINAL_ROUTE_MANHATTAN_BY_EXT` | 0→1, 1→3, 2→6, 3→12 |
| `PRODUCTION_SCORE_PER_SLOT_BLOCK` | 100 per slot block (`1+n_extensions` blocks) |
| `ROUTE_COST_PER_MANHATTAN_UNIT` | 8 per marginal unit |
| `MIN_PLACEMENT_ROI_SCORE_BY_PASS` | pass2→80, pass3→160 |

Functions: `_marginal_route_manhattan_to_trunk`, `_bundle_placement_roi_score`, `_placement_p1_roi_gate_ok`.

Application points:

- `_place_scan_pass` tree bundle loop: before `rank_key` per direction after `chosen_tree` (`roi_pass_key=pass_name`).
- `_place_pass2_spine_phase` before candidate placement (`roi_pass_key="pass2"`, trace `placement_p1_rejected`, `context: pass2_spine`).

When tuning, re-run unit tests and real-map regression with constants above.

## P2 (optional, not implemented)

Pre-routing low-ROI bundle prune — separate plan.
