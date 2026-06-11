---
type: community
cohesion: 0.12
members: 39
---

# Coord

**Cohesion:** 0.12 - loosely connected
**Members:** 39 nodes

## Members
- [[A shortest-path search for Layer 04 (deterministic tie-break).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/astar.py
- [[AstarPathResult]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/astar.py
- [[BBox]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[Bounded weighted route feasibility probe for Layer 03 candidates.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[BundleCandidate_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[Coord]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[Deterministic void-island labels (4-neighbor on external void only).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py
- [[L4RouteSearchDomain]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[Map a failed probe to a detailed reject reason + diagnostic payload.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py
- [[Return distances, visited count, and whether search stopped due to step_limit.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py
- [[RouteGoal_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[RouteProbeDiagnostic]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py
- [[RouteProbeLimits]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[Scale Phase B probe budget so rim stubs can reach exterior goals on large maps.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[Standard 4-neighbors on the active integer topology grid.]] - rationale - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[Structured diagnostics for Layer 03 route probe failures (PR-C audit).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py
- [[WeightedTransportRouteDomain_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[_failed_probe()]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[_field_cells_on_path()]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[_limits_or_default()]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[_manhattan()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py
- [[_manhattan()_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/astar.py
- [[_reconstruct_path()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/astar.py
- [[_reconstruct_path()_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[_resolve_external_void_cells()]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[_stub_coord_for()]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[_stub_void_coord()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py
- [[_unweighted_walkable_bfs()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py
- [[astar.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/astar.py
- [[astar_to_nearest_goal()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/astar.py
- [[classify_exterior_goal_unreachable()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py
- [[immediate_route_probe()]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[label_void_components()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py
- [[neighbors4()]] - code - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[resolve_layer03_route_probe_limits()]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[route_probe.py]] - code - django_apps/asteroid_lab/layers/shared/route_probe.py
- [[route_probe.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py
- [[route_probe_diagnostic.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py
- [[weighted_route_probe()]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Coord
SORT file.name ASC
```

## Connections to other communities
- 21 edges to [[_COMMUNITY_RouteProbedBundleCandidate]]
- 20 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 17 edges to [[_COMMUNITY_reconstruct_after_cleanup()]]
- 12 edges to [[_COMMUNITY_ReconstructionResult]]
- 10 edges to [[_COMMUNITY_generate_candidates()]]
- 10 edges to [[_COMMUNITY_route_layer04_sequential()]]
- 8 edges to [[_COMMUNITY_build_terrain_rim_highlight_from_rendera]]
- 8 edges to [[_COMMUNITY_ExteriorConnectionPlan]]
- 7 edges to [[_COMMUNITY_bbox_from_coords()]]
- 6 edges to [[_COMMUNITY_close_diagonal_leaks()]]
- 5 edges to [[_COMMUNITY_pattern_bundle_highlight.py]]
- 5 edges to [[_COMMUNITY_stamp_islands_uniform()]]
- 4 edges to [[_COMMUNITY_exhaustive_generator.py]]
- 4 edges to [[_COMMUNITY_evaluate_against_golden()]]
- 4 edges to [[_COMMUNITY_StrEnum]]
- 4 edges to [[_COMMUNITY_placement.py]]
- 3 edges to [[_COMMUNITY_layer03_rim_greedy_segment.py]]
- 3 edges to [[_COMMUNITY_footprint_transform.py]]
- 3 edges to [[_COMMUNITY_build_failed_source_diagnostic()]]
- 3 edges to [[_COMMUNITY_run_greedy_inner_fill()]]
- 3 edges to [[_COMMUNITY_build_reconstruction_complete_map()]]
- 2 edges to [[_COMMUNITY_complete_map_serializer.py]]
- 2 edges to [[_COMMUNITY_.validate_route_cell()]]
- 2 edges to [[_COMMUNITY_build_normalized_reconstruction_topology]]
- 1 edge to [[_COMMUNITY_GeneTemplate]]
- 1 edge to [[_COMMUNITY_ReplayEventType]]
- 1 edge to [[_COMMUNITY_ReplayOverlayCell]]
- 1 edge to [[_COMMUNITY_enrich_lab_timeline_frames_with_terrain_]]
- 1 edge to [[_COMMUNITY_gene_template_from_miner_gene_seed()]]
- 1 edge to [[_COMMUNITY_WeightedTransportRouteDomain]]
- 1 edge to [[_COMMUNITY_Decimal]]
- 1 edge to [[_COMMUNITY_scan_rim_anchors()]]
- 1 edge to [[_COMMUNITY_space_transport_catalog_snapshot.py]]
- 1 edge to [[_COMMUNITY_deconstruct_snapshot()]]

## Top bridge nodes
- [[Coord]] - degree 161, connects to 34 communities
- [[RouteGoal_1]] - degree 14, connects to 5 communities
- [[weighted_route_probe()]] - degree 16, connects to 3 communities
- [[immediate_route_probe()]] - degree 13, connects to 3 communities
- [[BundleCandidate_1]] - degree 8, connects to 3 communities