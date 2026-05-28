---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-20
phase: K2
pr: ??
related_docs:
  - documents/Algorithm/solver_runtime/phase_k_route_materialization.md
  - documents/Algorithm/asteroid_lab_07_incremental_commit.md
---

# Phase K2 ? Confirmed Placement Materialization

## Purpose

Materialize **CONFIRMED** extractor?extension occupancy from Incremental Commit into the same `MaterializedLayoutCells` output as Phase K transport materialization.

## Input

```text
IncrementalCommitResult.confirmed
Mapping[candidate_id, GeneCandidate]
Mapping[gene_id, GeneTemplate]  # extension_attachments for R
```

## Output

`MaterializedLayoutCells.equipment_cells` ? `shape_miner` / `fluid_miner` / `*_extension` + `tile_type` (`Layout_*`).

## Pipeline sequence

```text
materialize_route_network
? materialize_confirmed_placements
? merge_materialized_layout  # transport wins on shared trunk coord overlap
```

## Forbidden

- layout commit during candidate generation / route probe stage ([§0.1](00_core_principles.md) ? no install during enumeration)
- Placing miner on `fixed_output_transport` cell (occupied_offsets has no transport)

## Completion criteria

- [x] Each CONFIRMED has extractor + extensions in equipment_cells
- [x] extension R uses `GeneTemplate.extension_attachments` + server 4-neighbor ports
- [x] replay `cell_delta` records equipment + transport together
- [x] `validate_final_layout` ? `placement_not_materialized` unless extension coord is materialized transport (shared trunk)

## Related code

- `placement_network_materializer.py`
- `solver_runtime_pipeline.py`
- `replay_recording_cells.materialized_cells_to_cell_delta`
