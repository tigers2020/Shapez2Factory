---
status: verify
modified: 2026-06-14
---

# L1–L6 replay loop (5m)

## Scope

`/loop 5m` until Lab replay timeline shows L1–L6 properly for `documents/testmap/original_map.txt` (runtime wires + composed frames, no `missing_runtime_wires` when solver run exists).

## Acceptance

- [x] Solver artifact includes `output/solver_runtime_wires.v1.json` on successful run (even without L2 exterior plan)
- [x] `build_lab_replay_frames_for_project(project_id, solver_run_id=…)` → no `missing_runtime_wires`; L1–L6 frames present
- [x] Inline Lab page uses latest solver run when composing replay (not L1-only)
- [x] Loop gate script returns `OVERALL_OK=true`

## Progress

- 2026-06-14 — loop start — root cause: CLI skips runtime wires when `exterior_plan is None` (L2 skeleton); inline SSR omits `solver_run_id`.
- 2026-06-14 — implement — CLI always writes wires on `result.ok`; inline SSR passes `solver_run_id`; wire compose appends replay_core layers missing from wire projection (L6).
- 2026-06-14 — verify — `uv run python scripts/check_l1_l6_replay_gate.py` → `OVERALL_OK=true` (17 frames, wires present, diagnostic None).
- 2026-06-14 — fix order — wire+L2 replay_core merge was append-only → L3 wire frames before replay_core L2; merged by canonical L2→L6 order.
