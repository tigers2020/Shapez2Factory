---
type: community
cohesion: 0.05
members: 61
---

# ReconstructionCompleteMap

**Cohesion:** 0.05 - loosely connected
**Members:** 61 nodes

## Members
- [[All island-local field coords from a complete map (no overlay reads).]] - rationale - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[All reconstruction-complete ``asteroid__field`` cells (shape + fluid).]] - rationale - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[AstarPathResult_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[Asteroid field cell accessors for reconstruction-complete terrain SoT.]] - rationale - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[Count shapefluid field cells on the complete map.]] - rationale - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[Dominant asteroid resource from complete map field counts; tie → shape.]] - rationale - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[Dominant resource from field counts; tie → shape.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/resource_kinds.py
- [[Field cells with at least one 4-neighbor outside ``field_cells``.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/rim_topology.py
- [[Greedy loop place non-overlapping inner routeable groups up to ``max_groups``.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py
- [[Installable platform slots for ``transport_kind`` on reconstruction-complete map]] - rationale - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[Mineable field rim coords (reconstruction layer; not optimization).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/rim_topology.py
- [[Pick void cell on z=1 network for lift egress nearest to ``stub``.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[Place routeable inner miner groups (m3e east) until target or exhaustion.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py
- [[Reconstruction terrain upper-bound capacity (output-only; never solver input).]] - rationale - django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
- [[ReconstructionCompleteMap]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/resource_kinds.py
- [[Resource-kind detection on reconstruction-complete terrain (layer -1  L1 handof]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/resource_kinds.py
- [[Resources with at least one field cell; canonical order shape then fluid.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/resource_kinds.py
- [[Return a lift-feasible anchor where an m3e east group fits.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py
- [[Route inner source lift from field stub to z=1 void, then void-only A.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[RouteableInnerGroupPlacement]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py
- [[Space Lift egress routing for L4 inner sources (z=0 field → z=1 void).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[Terrain upper bound; platform count from complete map field cells only.]] - rationale - django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
- [[VOID_DEEP_SLOTS_V1 exterior void slot catalog from reconstruction-complete map]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/slots.py
- [[Void belt path; prepend field stub only when grid-adjacent to egress.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[VoidDepthEntry]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/slots.py
- [[_coords_adjacent()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[_footprint_at_anchor()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py
- [[_json_safe_source_kind()]] - code - django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
- [[_manhattan()_3]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py
- [[_prepend_lift_segment()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[_stub_has_lift_egress()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py
- [[astar_inner_source_via_space_lift()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[asteroid_field_cell_count_for_placement()]] - code - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[asteroid_field_cells_from_complete_map()]] - code - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[build_candidate_slots_by_edge()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/slots.py
- [[build_reconstruction_capacity_envelope()]] - code - django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
- [[build_reconstruction_capacity_summary()]] - code - django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
- [[build_reconstruction_observability()]] - code - django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
- [[build_void_shell_route_domain()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[compute_void_depth_entries()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/slots.py
- [[connector_reachable_void_cells()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[count_asteroid_field_cells_by_resource()]] - code - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[detect_present_resource_kinds()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/resource_kinds.py
- [[detect_primary_resource_kind()]] - code - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[detect_primary_resource_kind()_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/resource_kinds.py
- [[field_cells.py]] - code - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[field_rim_cells()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/rim_topology.py
- [[inner_routeable_group.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py
- [[is_inner_lift_source()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[lift_void_egress_for_stub()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[place_routeable_inner_groups()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py
- [[reconstruction_capacity_summary.py]] - code - django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
- [[resource_kinds.py]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/resource_kinds.py
- [[rim_topology.py]] - code - django_apps/asteroid_lab/reconstruction/rim_topology.py
- [[rim_topology.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/rim_topology.py
- [[slots.py]] - code - django_apps/asteroid_lab/layers/layer_02_exterior_transport/slots.py
- [[slots.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/slots.py
- [[space_lift_routing.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[total_asteroid_field_cell_count()]] - code - django_apps/asteroid_lab/reconstruction/field_cells.py
- [[try_place_first_routeable_inner_group()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py
- [[try_place_one_routeable_inner_group()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ReconstructionCompleteMap
SORT file.name ASC
```

## Connections to other communities
- 20 edges to [[_COMMUNITY_Coord]]
- 6 edges to [[_COMMUNITY_route_layer04_sequential()]]
- 5 edges to [[_COMMUNITY_Decimal]]
- 5 edges to [[_COMMUNITY_build_layer02_timeline_frame_wire_dict()]]
- 4 edges to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]
- 4 edges to [[_COMMUNITY_ExteriorConnectionPlan]]
- 4 edges to [[_COMMUNITY_run_greedy_inner_fill()]]
- 3 edges to [[_COMMUNITY_Any]]
- 3 edges to [[_COMMUNITY_execute_layer_02_exterior_transport_plan]]
- 3 edges to [[_COMMUNITY_build_solver_runtime_replay_frames()]]
- 3 edges to [[_COMMUNITY_ReconstructionResult]]
- 2 edges to [[_COMMUNITY_run_full_from_cleanup_recon()]]
- 2 edges to [[_COMMUNITY_build_terrain_rim_highlight_from_rendera]]
- 2 edges to [[_COMMUNITY_complete_map_serializer.py]]
- 2 edges to [[_COMMUNITY_GameDataRulesPort]]
- 2 edges to [[_COMMUNITY_run_layers_02_to_06()]]
- 2 edges to [[_COMMUNITY_build_layer03_transport_profiles()]]
- 2 edges to [[_COMMUNITY_bbox_from_coords()]]
- 1 edge to [[_COMMUNITY_exhaustive_generator.py]]
- 1 edge to [[_COMMUNITY_timeline_serialization.py]]
- 1 edge to [[_COMMUNITY_generate_candidates()]]
- 1 edge to [[_COMMUNITY_scan_rim_anchors()]]
- 1 edge to [[_COMMUNITY_run_layer_06_commit_validate()]]
- 1 edge to [[_COMMUNITY_build_reconstruction_complete_map()]]
- 1 edge to [[_COMMUNITY_mining_extraction_rules.py]]
- 1 edge to [[_COMMUNITY_placement.py]]

## Top bridge nodes
- [[ReconstructionCompleteMap]] - degree 58, connects to 20 communities
- [[detect_present_resource_kinds()]] - degree 8, connects to 4 communities
- [[build_reconstruction_capacity_summary()]] - degree 8, connects to 3 communities
- [[build_reconstruction_observability()]] - degree 7, connects to 3 communities
- [[build_candidate_slots_by_edge()]] - degree 6, connects to 3 communities