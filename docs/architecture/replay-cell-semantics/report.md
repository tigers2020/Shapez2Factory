# Architecture Improvement Report — replay cell semantics

**Thread slug:** `replay-cell-semantics`  
**Updated:** 2026-06-12 (post Step 2)  
**Kanban:** `.devtool/features/replay-cell-semantics-2026-06-12.md`

## Scope

Replay cell semantics boundary after Step 1: overlay wire read path, `EffectiveCellView` merge, serialized-frame lookup, Lab UI client fast-path.

## Repository state (at last review)

Dirty tree with Step 1–2 WIP + governance edits. Graph GRAPH_STALE (`224d6bac` vs HEAD). graphify query blocked on Windows cp949 — grep/read evidence used.

## Current architecture map

| Item | Finding |
|------|---------|
| Domain | Lab cell detail: terrain / occupant / transport / output for one `(x,y)` |
| Server entry | `asteroid_miner_layout_replay_frame_cell` → `lookup_effective_cell_in_serialized_frame` |
| Client entry | `labCellDetailLookupInMapView` → `LabEffectiveCellView.mergeEffectiveCellView` |
| Core types | `EffectiveCellView`, `EffectiveCellWire`, overlay wire rows |
| Read policy | `replay_cell_semantics.py` (Step 2 ✅) |
| Write policy | `overlay_wire_contract.py` (strict emission) |
| Frame harvest | `replay_frame_cell_resolver.py` (Step 1 ✅) |
| Deprecated | ~~`replay_frame_cell_lookup`~~ removed Step 3 ✅ |

## Complexity symptoms (remaining)

| Symptom | Evidence | Refactor pressure |
|---------|----------|-------------------|
| Python/JS drift | `effective_cell_view.py` ↔ `lab_effective_cell_view.js` | Step 4 compare or ongoing parity tests |
| Overlay bucket harvest | `_collect_overlay_cells` hardcoded keys | Step 4 registry |
| Flat shim | Tests still use deprecated flat lookup | **Step 3** |
| Dual lookup paths | Server serialized frame vs client `map_view` | Frozen until Step 4 |

## Recommendation

**Step 2 complete.** Proceed **Step 3 only** on separate execution prompt — wire tests, grep-clean, remove flat shim.

Do not bundle Step 4. Do not merge read/write transport normalizers.

## Deep module (Step 2 — delivered)

**Module:** `replay_cell_semantics.py`  
**Owns:** kind sets, read transport normalization, occupant mapping, route tile resolution, simulation id  
**Does not own:** frame harvest, merge orchestration, write strict profile mapping

## Design alternatives (historical)

- **Option A (chosen):** Python semantics module + JS mirror until Step 4
- **Option B:** Single policy class with read/write modes — rejected (write path already in overlay_wire_contract)

## Open questions

1. Step 3: re-export compat vs update all importers — prefer minimal diff
2. Step 4: overlay registry shape — defer until compare mode spec

```text
STOPPED_AT_ARCHITECTURE_REVIEW (report persisted; Step 2 implemented separately)
```
