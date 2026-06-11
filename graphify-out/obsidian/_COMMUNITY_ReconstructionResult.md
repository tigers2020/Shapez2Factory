---
type: community
cohesion: 0.10
members: 40
---

# ReconstructionResult

**Cohesion:** 0.10 - loosely connected
**Members:** 40 nodes

## Members
- [[AcceptanceTopology]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[Attach confidence fields and summary metrics to a reconstruction result.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[Blueprint ``_asteroid_lab_reconstruction.summary_json`` (no per-cell scores).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[Classify mineable cells; hard evidence is never ambiguous.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[CoordFrame]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[Count ambiguous cells that fall outside the mineable set.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[Island-coordinate sets used by reconstruction confidence  acceptance.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[Mineable + external void from a complete decoded cell list.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[Mineable  void topology key for one island-local cell.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[Overlay-only field coords (diagnostic  legacy confidence path).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[Overlay-only topology (diagnostic). Do not use for capacity or OptimizationInput]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[Reconstruction acceptance topology (mineable  external void) without Optimizati]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[Reconstruction confidence  ambiguity (production acceptance; fixtures calibrate]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[ReconstructionResult]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[Terrain topology from reconstruction-complete map SoT.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[Two topology-coordinate masks interior-patch hint and wall-adjacent fill.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[_cells_by_topology_coord()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[_constraint_violations()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[_is_hard_evidence_cell()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[_is_inferred_fill()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[_overlay_field_cells_from_result()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[_topology_coord()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[acceptance_topology.py]] - code - django_apps/asteroid_lab/reconstruction/acceptance_topology.py
- [[acceptance_topology.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[acceptance_topology_from_complete_map()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[acceptance_topology_from_decoded_cells()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[acceptance_topology_from_reconstruction()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[apply_confidence_to_result()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[build_candidate_masks()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[compute_confidence_metrics()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[confidence.py]] - code - django_apps/asteroid_lab/reconstruction/confidence.py
- [[confidence.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[constraint_violation_count()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[external_void_coords_from_reconstruction()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[merge_mask_agreement()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[mineable_coords_from_reconstruction()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[quality_tier_from_metrics()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[reconstruction_acceptance_ok()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[reconstruction_persist_summary()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py
- [[topology_coord_for_cell()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ReconstructionResult
SORT file.name ASC
```

## Connections to other communities
- 12 edges to [[_COMMUNITY_Coord]]
- 8 edges to [[_COMMUNITY_DecodedCellDTO]]
- 7 edges to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 7 edges to [[_COMMUNITY_build_reconstruction_complete_map()]]
- 5 edges to [[_COMMUNITY_build_normalized_reconstruction_topology]]
- 4 edges to [[_COMMUNITY_reconstruct_after_cleanup()]]
- 3 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 3 edges to [[_COMMUNITY_build_reconstructed_map_persist_payload(]]
- 3 edges to [[_COMMUNITY_enrich_lab_timeline_frames_with_terrain_]]
- 3 edges to [[_COMMUNITY_bbox_from_coords()]]
- 2 edges to [[_COMMUNITY_is_asteroid_evidence()]]
- 1 edge to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_run_full_from_cleanup_recon()]]
- 1 edge to [[_COMMUNITY_build_terrain_rim_highlight_from_rendera]]

## Top bridge nodes
- [[ReconstructionResult]] - degree 25, connects to 7 communities
- [[acceptance_topology_from_decoded_cells()]] - degree 13, connects to 5 communities
- [[CoordFrame]] - degree 15, connects to 4 communities
- [[apply_confidence_to_result()]] - degree 15, connects to 4 communities
- [[topology_coord_for_cell()]] - degree 8, connects to 3 communities