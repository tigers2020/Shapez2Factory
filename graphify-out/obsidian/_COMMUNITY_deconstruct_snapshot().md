---
type: community
cohesion: 0.13
members: 22
---

# deconstruct_snapshot()

**Cohesion:** 0.13 - loosely connected
**Members:** 22 nodes

## Members
- [[.run()_1]] - code - src/shapez2_factory/application/asteroid_lab/run_stack.py
- [[Decode + normalize + snapshot DTO.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[Decode, reconstruct, and run L2–L6; return captured layer artifacts.]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_solver_run.py
- [[GoldenSolverArtifacts_1]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_solver_run.py
- [[GoldenSolverConfig]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_solver_run.py
- [[Remove strippable buildings and compute ``wall_coords`` for reconstruction.]] - rationale - src/shapez2_factory/domain/asteroid_lab/cleanup/pipeline.py
- [[Return inclusive (w0, w1, h0, h1) padded around wall_coords, or None if empty.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/grid.py
- [[Run golden-map solver stack and capture L2–L5 artifacts (Django-free).]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_solver_run.py
- [[Strip buildings and compute topology wall coordinates (pre-reconstruction).]] - rationale - src/shapez2_factory/domain/asteroid_lab/cleanup/pipeline.py
- [[Working bbox and coordinate enumeration for reconstruction (2D x,y; layer ignore]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/grid.py
- [[_LayerArtifactCapture]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_solver_run.py
- [[_build_runners()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_solver_run.py
- [[_capture_layer_run()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_solver_run.py
- [[decode_shapez_copy_string()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[deconstruct_snapshot()]] - code - src/shapez2_factory/domain/asteroid_lab/cleanup/pipeline.py
- [[golden_fixture_solver_run.py]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_solver_run.py
- [[grid.py]] - code - django_apps/asteroid_lab/reconstruction/grid.py
- [[grid.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/grid.py
- [[padded_bbox_bounds()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/grid.py
- [[pipeline.py]] - code - django_apps/asteroid_lab/cleanup/pipeline.py
- [[pipeline.py_2]] - code - src/shapez2_factory/domain/asteroid_lab/cleanup/pipeline.py
- [[run_golden_solver()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_solver_run.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/deconstruct_snapshot
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_GameDataRulesPort]]
- 6 edges to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 2 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_run_layers_02_to_06()]]
- 2 edges to [[_COMMUNITY_build_reconstruction_complete_map()]]
- 2 edges to [[_COMMUNITY_reconstruct_after_cleanup()]]
- 2 edges to [[_COMMUNITY_DecodedCellDTO]]
- 1 edge to [[_COMMUNITY_Coord]]
- 1 edge to [[_COMMUNITY_run_full_from_cleanup_recon()]]
- 1 edge to [[_COMMUNITY_complete_map_serializer.py]]
- 1 edge to [[_COMMUNITY_decode_copy_string()]]
- 1 edge to [[_COMMUNITY_build_decoded_blueprint_snapshot()]]
- 1 edge to [[_COMMUNITY_normalize_decoded_blueprint()]]
- 1 edge to [[_COMMUNITY_is_asteroid_evidence()]]
- 1 edge to [[_COMMUNITY_close_diagonal_leaks()]]
- 1 edge to [[_COMMUNITY_stamp_islands_uniform()]]
- 1 edge to [[_COMMUNITY_build_normalized_reconstruction_topology]]

## Top bridge nodes
- [[.run()_1]] - degree 11, connects to 5 communities
- [[decode_shapez_copy_string()]] - degree 8, connects to 5 communities
- [[deconstruct_snapshot()]] - degree 13, connects to 4 communities
- [[run_golden_solver()]] - degree 12, connects to 4 communities
- [[_build_runners()]] - degree 8, connects to 3 communities