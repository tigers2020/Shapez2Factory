# Project Review Memory

Tracks bounded review areas and Linear issues created by periodic automation.
Read this file before each run to avoid duplicate work.

## 2026-06-10 05:07

Reviewed area:
- path/module/feature: `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/` (run.py, candidate_gen.py, shared/route_probe.py) and stack budget wiring in `stack_runner.py` / `layers/contracts/layer_budget.py`

Skipped:
- CI/artifact/recipe-graph/game_data areas — already covered by open Linear issues SHA-7 through SHA-30
- L5 transport budget gap — duplicate of SHA-14

Findings:
- SHA-31: L3 rim greedy placement ignores LayerBudgetContext during Phase B route probe expansion

Notes:
- `run_layer_03_rim_greedy_placement` discards `budget_ctx` via `_ = (budget_ctx, ...)`. Phase B runs anchors×genes×variants×4 weighted A* probes (up to 4096 expanded nodes each) with no `remaining_budget_ms()` polling, unlike L4 inner fill greedy loop. `LayerBudgetContext` doc states budget applies to L2–L5.
