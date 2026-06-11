---
type: community
cohesion: 0.18
members: 17
---

# build_normalized_reconstruction_topology

**Cohesion:** 0.18 - loosely connected
**Members:** 17 nodes

## Members
- [[Build compare topology from decoded or reconstruction-merged cells.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[Decodedreconstructed cells use island-local topology.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[Identity helper; sets already island-deduped.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[Island-grid topology sets for compare (layer duplicates collapse to ``(x, y)``).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[NormalizedReconstructionTopology]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[RawCoord]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[Symmetric set diffs for fixture assertion messages.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[_cap_coords()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[_is_mineable_occupied()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[_shell_topology_coords()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[build_normalized_reconstruction_topology()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[diff_topology()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[infer_topology_coord_frame()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[normalize_topology_for_compare()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[raw_coords_from_snapshot()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[topology_contract.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[topology_diff_is_empty()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_normalized_reconstruction_topology
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_ReconstructionResult]]
- 3 edges to [[_COMMUNITY_DecodedCellDTO]]
- 2 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_Coord]]
- 1 edge to [[_COMMUNITY_Path]]
- 1 edge to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 1 edge to [[_COMMUNITY_bbox_from_coords()]]
- 1 edge to [[_COMMUNITY_is_asteroid_evidence()]]
- 1 edge to [[_COMMUNITY_reconstruct_after_cleanup()]]
- 1 edge to [[_COMMUNITY_deconstruct_snapshot()]]

## Top bridge nodes
- [[build_normalized_reconstruction_topology()]] - degree 13, connects to 5 communities
- [[topology_contract.py_1]] - degree 11, connects to 2 communities
- [[infer_topology_coord_frame()]] - degree 5, connects to 2 communities
- [[_shell_topology_coords()]] - degree 5, connects to 2 communities
- [[diff_topology()]] - degree 5, connects to 1 community