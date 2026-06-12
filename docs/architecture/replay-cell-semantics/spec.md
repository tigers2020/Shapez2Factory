# Replay cell semantics — spec

Kanban: `.devtool/features/replay-cell-semantics-2026-06-12.md`

## Scope

Asteroid Lab replay cell semantics: overlay wire read/write, `EffectiveCellView` merge, serialized-frame lookup, Lab UI client fast-path + server canonical compare.

## Contract decisions

| Question | Decision |
|----------|----------|
| Client POST-only? | **No.** Step 4: client fast-path first; server POST compare; fallback on mismatch |
| Shared overlay keys? | `replay_overlay_bucket_registry.py` — `semantic_lookup` vs `paint_target` roles |
| Remove flat lookup? | Done (Step 3) |
| read vs write transport | **Do not merge.** Read tolerant; write strict |

## Epic acceptance

- [x] Step 1: resolver → `replay_frame_cell_resolver.py`
- [x] Step 2: `replay_cell_semantics.py`
- [x] Step 3: wire tests; flat shim removed
- [x] Step 4: overlay bucket registry + server-canonical compare/fallback

## Step 4 behavior

- **Registry:** `collect_overlay_cells_for_semantic_lookup` vs `collect_overlay_cells_for_paint_target`
- **JS:** persisted frame → render client merge immediately → POST server → mismatch → `server_canonical_fallback`
- **detail_source:** `client_fast_path_confirmed` | `server_canonical_fallback` | `map_view_client_only`
