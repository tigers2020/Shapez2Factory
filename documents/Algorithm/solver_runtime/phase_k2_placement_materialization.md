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

# Phase K2 ??Confirmed Placement Materialization

## ëª©ì 

Incremental Commit??**CONFIRMED** ??extractorÂ·extension ?ìœ ë¥?Phase K transport materializationê³?**?™ì¼??* `MaterializedLayoutCells` ?°ì¶œë¬¼ì— ?¹ê²©?œë‹¤.

## ?…ë ¥

```text
IncrementalCommitResult.confirmed
Mapping[candidate_id, GeneCandidate]
Mapping[gene_id, GeneTemplate]  # extension_attachments for R
```

## ?°ì¶œë¬?

`MaterializedLayoutCells.equipment_cells` ??`shape_miner` / `fluid_miner` / `*_extension` + `tile_type` (`Layout_*`).

## ?Œì´?„ë¼???œì„œ

```text
materialize_route_network
??materialize_confirmed_placements
??merge_materialized_layout  # transport wins on shared trunk coord overlap
```

## ê¸ˆì?

- candidate generation / route probe ?¨ê³„ layout commit ([Â§0.1](00_core_principles.md) ??enumeration ì¤??¤ì¹˜)
- `fixed_output_transport` ?€??miner ë°°ì¹˜ (occupied_offsets??transport ?†ìŒ)

## ?„ë£Œ ì¡°ê±´

- [x] CONFIRMEDë§ˆë‹¤ extractor + extensionsê°€ equipment_cells???¬í•¨
- [x] extension R?€ `GeneTemplate.extension_attachments` + server 4-neighbor ports
- [x] replay `cell_delta`??equipment + transport ?™ì‹œ ê¸°ë¡
- [x] `validate_final_layout` ??`placement_not_materialized` unless extension coord is materialized transport (shared trunk)

## ê´€??ì½”ë“œ

- `placement_network_materializer.py`
- `solver_runtime_pipeline.py`
- `replay_recording_cells.materialized_cells_to_cell_delta`
