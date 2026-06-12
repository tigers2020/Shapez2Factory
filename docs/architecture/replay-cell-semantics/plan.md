# Replay cell semantics — implementation plan

Spec: [spec.md](./spec.md)  
Report: [report.md](./report.md)  
Kanban: `.devtool/features/replay-cell-semantics-2026-06-12.md`

## Sequence

```text
Step 1 ✅ → Step 2 ✅ → Step 3 ✅ → Step 4 ✅
```

## Step 4 — overlay registry + canonical compare ✅

**4a — Registry**

- `replay_overlay_bucket_registry.py` — `SEMANTIC_LOOKUP` / `PAINT_TARGET` roles
- Resolver → `collect_overlay_cells_for_semantic_lookup`
- Paint parity → `collect_overlay_cells_for_paint_target` in `lab_replay_sprite_wire`

**4b — JS compare/fallback**

- Persisted frame: client fast-path → POST → EffectiveCellWire signature compare → server fallback on mismatch
- `detail_source` in frame meta

Validation: registry 4 + replay unit 58 + integration replay_frame_cell 3; ruff replay/

## Hard constraints

- read tolerant / write strict — never merge normalizers
- Step 4 allows targeted JS changes for compare/fallback only
