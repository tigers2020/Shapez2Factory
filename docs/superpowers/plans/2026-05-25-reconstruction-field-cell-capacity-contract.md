# Reconstruction Field Cell Capacity Contract — Historical Tombstone

**Status:** `OBSOLETE / DO NOT EXECUTE`  
**Retired:** 2026-05-26  
**Cleanup:** 2026-05-25 roadmap drift cleanup

This implementation plan is intentionally reduced to a tombstone because its original checklist used the withdrawn overlay path:

```text
ReconstructionResult.cells / recon.cells as terrain SoT
```

That path conflicts with the current roadmap and complete-map contract. Do not restore or execute the removed checklist.

## Authoritative replacement

Use the complete-map DTO plan and spec instead:

- Plan: [`2026-05-26-reconstruction-complete-map-dto.md`](2026-05-26-reconstruction-complete-map-dto.md)
- Spec: [`../specs/2026-05-26-reconstruction-complete-map-dto-design.md`](../specs/2026-05-26-reconstruction-complete-map-dto-design.md)

## Preserved invariant

```text
Solver/Lab capacity, topology mineable sets, and OptimizationInput must consume
ReconstructionCompleteMap, not ReconstructionResult.cells.
```

## Forbidden from this retired plan

- Reintroducing `asteroid_field_cells_from_reconstruction(recon)` as a public SoT.
- Counting terrain capacity from sparse reconstruction overlay cells.
- Treating mask-sized `confirmed_cells` as the terrain upper-bound numerator.
- Using replay/full_map/debug artifacts as solver input.
- Starting capacity C-GATE work without a fresh spec and `documents/ai/current_plan.md` ACTIVE row.

## Reason

`current_plan.md` currently allows only v0.1 next-track selection. Capacity C-GATE is not an implementation track until a new spec and queue row exist. Keeping an executable stale checklist here creates a governance footgun.
