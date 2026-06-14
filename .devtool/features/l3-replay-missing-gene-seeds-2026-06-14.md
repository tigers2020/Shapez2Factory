---
status: verify
modified: 2026-06-14
---

# L3 replay empty — missing GeneSeed bootstrap

## Scope

User report: L3 replay results not visible. Root cause: `GeneSeed` table empty → L3 `layer_skip_reason=missing_genetic_sample_seeds` → no committed placements / overlays.

## Acceptance

- [x] Solver auto-bootstraps miner GeneSeed catalog when empty (before subprocess)
- [x] L3 wire has committed placements after re-run on original_map project (75 placements, overlay frames)
- [x] L3 route probe reaches exterior-lane L2 connectors (routing surface expansion when goals outside void bbox)
- [x] Targeted tests green (`test_exterior_routing_surface.py`)

## Progress

- 2026-06-14 — diagnose: GeneSeed count 0, L3 skip in runtime wires
- 2026-06-14 — fix: `ensure_miner_gene_seeds_bootstrapped()` in solver enqueue path; verify run_id=22 → 75 committed, 13 L3 replay frames with overlays
- 2026-06-14 — regression after L2 exterior lane: run 26 `route_feasible_rim_anchor_count=0` (connectors at (25,25) outside void bbox -23..23). Fix: `build_layer03_routing_walkable()` expands probe surface; verify original_map → 77 committed
- 2026-06-14 — final/L6 replay empty: tail replay_core frames terrain-only; fix `enrich_lab_timeline_frames_with_carried_layout_overlays()` + cache schema v4
