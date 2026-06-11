---
type: community
cohesion: 0.17
members: 16
---

# build_reconstruction_complete_map()

**Cohesion:** 0.17 - loosely connected
**Members:** 16 nodes

## Members
- [[Island-local coord → ``asteroid_shape_field``  ``asteroid_fluid_field``.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[Layer 1 facade — delegates to reconstruction (no layers import in reconstructio]] - rationale - django_apps/asteroid_lab/layers/layer_01_reconstruction/run.py
- [[Merged cleanup structural map + reconstruction overlay.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[Overlay-only count for contract tests (not terrain SoT).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[Reconstruction-complete map DTO and sole terrain SoT factory.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[ReconstructionCompleteMap_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[Sole entry point for reconstruction-complete terrain SoT.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[_count_by_resource()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[_field_cells_from_decoded_cells()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[build_reconstruction_complete_map()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[complete_map.py]] - code - django_apps/asteroid_lab/reconstruction/complete_map.py
- [[complete_map.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[mineable_field_kind_by_coord()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[overlay_field_cell_count()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map.py
- [[run.py]] - code - django_apps/asteroid_lab/layers/layer_01_reconstruction/run.py
- [[run_layer_01()]] - code - django_apps/asteroid_lab/layers/layer_01_reconstruction/run.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_reconstruction_complete_map
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_ReconstructionResult]]
- 3 edges to [[_COMMUNITY_DecodedCellDTO]]
- 3 edges to [[_COMMUNITY_Coord]]
- 2 edges to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 2 edges to [[_COMMUNITY_deconstruct_snapshot()]]
- 1 edge to [[_COMMUNITY_run_full_from_cleanup_recon()]]
- 1 edge to [[_COMMUNITY_write_lab_solver_layer_stack_logs()]]
- 1 edge to [[_COMMUNITY_ReconstructionCompleteMap]]
- 1 edge to [[_COMMUNITY_generate_candidates()]]
- 1 edge to [[_COMMUNITY_scan_rim_anchors()]]

## Top bridge nodes
- [[run_layer_01()]] - degree 7, connects to 5 communities
- [[build_reconstruction_complete_map()]] - degree 14, connects to 4 communities
- [[_field_cells_from_decoded_cells()]] - degree 6, connects to 3 communities
- [[mineable_field_kind_by_coord()]] - degree 6, connects to 3 communities
- [[_count_by_resource()]] - degree 4, connects to 2 communities