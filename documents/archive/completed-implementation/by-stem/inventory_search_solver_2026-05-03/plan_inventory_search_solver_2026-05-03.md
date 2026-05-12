# Plan: inventory search solver pipeline (2026-05-03)

## Summary

Wire `compute_factory_batch` → `InventorySearchSolver` behind a **solver mode** flag; add **FlowGraphBuilder** + **SolverGraph** adapter; **pattern signature** + **macro shortcut actions** (HALF_SPLIT / CHECKER style bundles as folded transitions); legacy regression tests; optional **timeout** and API **solver** metadata with **SearchCost** serialization.

## Human approval

- [ ] Approved by maintainer (name / date): _______________

## Acceptance

- `pytest`
- `ruff check .`
- `mypy .`
- `black --check .`

## Rollout

1. Default remains `legacy_recipe` unless settings set `INVENTORY_SEARCH_SOLVER_DEFAULT=true` or request passes `solver_mode: "inventory_search"`.
2. On inventory path failure, fall back to legacy and set warning in response.

## Related research

- [`research_inventory_search_solver_2026-05-03.md`](./research_inventory_search_solver_2026-05-03.md)
