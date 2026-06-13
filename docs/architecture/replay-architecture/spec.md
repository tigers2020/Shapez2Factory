# Replay height layer — contract

**Thread:** `replay-architecture`  
**Approved:** 2026-06-12 (Option A)

## Scope

Client-side mirror of `map_height_layer.py` for browser read paths (paint index + Z filter). Python remains write-time authority; JS enriches/infers on read when building paint index and filtering.

## Non-goals

- Layer-aware DOM grid (flat index unchanged)
- Merging height policy into `replay_cell_semantics` or `effective_cell_view`
- Backfill/migration of persisted frames server-side

## Decisions

1. **Canon:** `django_apps/asteroid_lab/replay/map_height_layer.py`
2. **Mirror:** `django_apps/web/static/web/js/lab_replay_height_layer.js`
3. **Load order:** `lab_effective_cell_view.js` → `lab_replay_height_layer.js` → `lab_replay_overlay_bucket_registry.js` → `lab_replay_paint_plan.js`
4. **Paint index:** enrich wire rows with `layer` before `collectCoordUniverse`
5. **UI filter:** `labCellMapZ` delegates to mirror module; remove `inferLabCellMapZ`
6. **Parity:** shared fixture table; Python + optional Node gate

## Invariants

- L ∈ {0, 1, 2}; explicit `layer` / `L` / `z` / `Z` wins over inference
- `wire_transport_kind_for_layer_resolution` rules for candidate rows
- Same inputs → same plane on Python write enrich and JS read enrich

## Boundaries

| Module | Role |
|--------|------|
| `map_height_layer.py` | Write + server read enrich |
| `lab_replay_height_layer.js` | Browser read enrich/infer |
| `lab_replay_paint_plan.js` | Enrich + overlay registry harvest before index build |
| `lab_replay_overlay_bucket_registry.js` | Browser overlay bucket harvest (paint + semantic) |
| `asteroid_miner_layout_lab.js` | Z filter via height module; paint targets via overlay registry |

## Validation

```bash
python -m pytest tests/unit/asteroid_lab/replay/test_map_height_layer.py tests/unit/asteroid_lab/replay/test_lab_replay_height_layer_parity.py tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py -q
python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_overlay_bucket_registry_parity.py -q
```
