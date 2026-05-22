# Commit — Extension on Shared Transport Trunk

**Status:** Approved 2026-05-22 (implements deferred item from shared-transport spec)  
**Related:** [`2026-05-22-shared-transport-inlet-design.md`](2026-05-22-shared-transport-inlet-design.md), [`phase_k2_placement_materialization.md`](../../../documents/Algorithm/solver_runtime/phase_k2_placement_materialization.md)

## Bug

Production run: `19,4:e:shape_belt` skipped with `equipment_transport_overlap` while `validation_passed` and materialization allow extension coords on shared belt cells (transport wins).

Root cause: `_equipment_transport_overlap` rejects when **any** `equipment & committed_route_cells`, including **extensions** on shared trunk.

## v0 rule (align commit with K2/L)

| Check | Rule |
|-------|------|
| Inlet | `fixed_output_transport ∈ committed_route_cells` → `INLET_ON_SHARED_TRANSPORT` (unchanged) |
| Route through equipment | `path ∩ committed_equipment_cells` → `EQUIPMENT_TRANSPORT_OVERLAP` (unchanged) |
| Extractor on transport | `extractor ∈ committed_route_cells` → `EQUIPMENT_TRANSPORT_OVERLAP` |
| Extension on shared trunk | **Allowed** at commit (materializes as transport layer) |

## Tests

- `test_commit_allows_extension_on_committed_transport_trunk`
- Regression: `test_commit_skips_equipment_transport_overlap`, inlet tests
