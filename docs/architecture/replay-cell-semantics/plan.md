# Replay cell semantics — implementation plan

Spec: [spec.md](./spec.md)  
Report: [report.md](./report.md)  
Kanban: `.devtool/features/replay-cell-semantics-2026-06-12.md`

## Sequence

```text
Step 1 ✅ → Step 2 ✅ → Step 3 → Step 4 (optional, frozen)
```

## Step 1 — resolver placement ✅

- Move lookup to `django_apps/asteroid_lab/replay/replay_frame_cell_resolver.py`
- Web shim + import compat; tests → `test_replay_frame_cell_resolver.py`
- Validation: pytest resolver tests

## Step 2 — read semantics module ✅

- Add `replay_cell_semantics.py`; refactor `effective_cell_view.py`
- `overlay_wire_contract.py` imports `simulation_for_tile_id` from semantics
- Add `test_replay_cell_semantics.py`
- Validation: pytest effective_cell_view + semantics + shape_belt ban; ruff replay/

## Step 3 — flat shim removal ✅

1. Migrate `test_replay_frame_cell_resolver.py` to assert `EffectiveCellWire` ✅
2. Grep: no runtime imports of `lookup_cell_in_serialized_frame` ✅
3. Delete `lookup_cell_in_serialized_frame` and `replay_frame_cell_lookup.py` ✅
4. Remove dead `_merge_layers` in resolver ✅

Validation: pytest 12 passed (9 unit + 3 integration `-k replay_frame_cell`); ruff clean.

## Step 4 — optional (separate approval)

- Server-canonical compare/fallback vs JS fast-path
- Typed overlay bucket registry (`semantic_lookup` / `paint_target`)

## Hard constraints (all steps)

- No JS changes (Steps 1–3)
- No git clean / reset / branch switch without explicit user request
- read tolerant / write strict — never merge normalizers
