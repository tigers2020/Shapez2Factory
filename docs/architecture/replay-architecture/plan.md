# Replay height layer — implementation plan

**Thread:** `replay-architecture`  
**Approved:** 2026-06-12

## Steps

- [x] 1. `spec.md` locked
- [x] 2. Add `lab_replay_height_layer.js` (mirror `map_height_layer.py`)
- [x] 3. Template script tag + load order
- [x] 4. `lab_replay_paint_plan.js` — enrich rows before coord universe
- [x] 5. `tests/support/lab_replay_paint_plan.py` — same enrich hook
- [x] 6. `asteroid_miner_layout_lab.js` — delegate `labCellMapZ`; remove `inferLabCellMapZ`
- [x] 7. `test_lab_replay_height_layer_parity.py` + contract updates — 68+17 pytest pass
- [x] 8. Overlay harvest registry → JS manifest — `lab_replay_overlay_bucket_registry.js` + parity tests

## Stop conditions

- Parity vectors fail → fix mirror before merge
- Paint golden regress → revert enrich hook, diagnose coord collision

## Validation evidence

Run commands in `spec.md`; record in kanban Progress.
