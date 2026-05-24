# Asteroid Lab — Optimization Sequence 1A·1B scope

**Status:** `ACTIVE` (fixed implementation scope)  
**Reference docs:** [`documents/Algorithm/asteroid_lab_10_development_sequence.md`](../../Algorithm/asteroid_lab_10_development_sequence.md) Sequence 1A·1B, [`asteroid_lab_01_optimization_input.md`](../../Algorithm/asteroid_lab_01_optimization_input.md)

## Approved scope

1. **Sequence 1A — Domain DTO contracts**  
   - `Coord` = Server X/Y, `neighbors4_server`, `cardinal_unit_toward`  
   - `OptimizationInput` and enums · auxiliary DTOs listed in Phase 1·4·6·7·8·9 docs (evolution · recovery · validation · replay type slots)  
   - `TopologyGraph` undirected contract (storage: bidirectional edges)  
   - `RouteDomainSnapshotBuilder.build_snapshot` / `build_seed_snapshot` signatures (sync with Phase 7·1)

2. **Sequence 1B — Reconstruction → OptimizationInput + seed route_domain**  
   - `ReconstructionResult` + required `DecodedCellDTO.server_x`/`server_y`  
   - rim · interior · mineable · blocked · transport · empty trunk/greenfield same path  
   - seed snapshot: `hard_blocked` · `transport_mask` · `RouteClass` consistent with `blocked_cells`

## Package paths (fixed)

- **Code:** `django_apps/asteroid_lab/optimization/` (no Django ORM; reference existing DTOs like `DecodedCellDTO` only)  
- **Coords:** when `ReconstructionResult.server_xy_params` exists, restore Server coords via `server_xy_for_raw_xy` even if `DecodedCellDTO` lacks `server_x`/`server_y`.  
- **Tests:** `tests/unit/asteroid_lab/test_optimization_input.py`

Do not use legacy paths `django_apps.shapez_asteroid` · `tests/unit/shapez_asteroid/` from older docs.

## Human approval

Implement within scope and paths in this document. Revise this plan and re-approve before scope changes.
