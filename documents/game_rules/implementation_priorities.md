# Implementation Priorities (Project Perspective)

Recommended order from the user-provided review document, preserved as-is.

1. **Lock Shape canonical model** — fix string, quadrant order, and normalization in one place ([shape_encoding.md](shape_encoding.md), [solver_domain_model.md](solver_domain_model.md))
2. **Split operations into pure functions** — cut / rotate / stack / paint / swap / pin / crystal, etc. ([solver_operation_interface.md](solver_operation_interface.md))
3. **Test Stacker / Cutter / Swapper / Crystal / Pin rules** — do not rely on wiki/snippets alone; cross-verify in-game when possible
4. **Reflect quantities on edges and operation plans, not just nodes** ([solver_quantity_flow.md](solver_quantity_flow.md)) — alignment with recipe graph DTO and `recipe_graph_*` services (separate work)
5. **Search layer (BFS/Dijkstra/A*, etc.) over naive recursive decomposition** ([solver_search_strategy.md](solver_search_strategy.md)) — extend existing solver modules for inventory/macro search (separate work)

## One-Line Summary

At this stage, stabilizing **shape algebra** before "shape rendering/graph UI" pays off.
