---
status: done
modified: 2026-06-14
---

# Reconstruction simplify — miner/extension → asteroid_field only

## Scope

Strip topology fill (inner fill, outer detection, flood fill, wall projection, diagonal_closed, transport pocket logic). On SHAPEZ2 decode: convert miner/extension to `asteroid_*_field`, stamp islands, return.

## Acceptance

- [x] `reconstruct_after_cleanup` / `run_topology_reconstruction` no flood-fill or barrier logic
- [x] Original map (578 extensions) → 578 `asteroid_shape_field` cells
- [x] Focused reconstruction unit tests green or updated to new contract
- [x] `scripts/test_reconstruction_narrow.ps1` or equivalent pytest slice passes

## Progress

- 2026-06-14: Session start — user requested extreme simplification; implementing pipeline rewrite.
- 2026-06-14: `pipeline.py` rewritten (~730→~220 lines). Tests updated. 40 reconstruction tests green.
- 2026-06-14: Narrow gate 25/25 green. `original_map.txt` → 578 `asteroid_shape_field`.
