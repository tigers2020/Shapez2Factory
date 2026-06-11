---
type: community
cohesion: 0.07
members: 40
---

# route_layer04_sequential()

**Cohesion:** 0.07 - loosely connected
**Members:** 40 nodes

## Members
- [[Convert committed L3 placements and L4 routeable inner groups to L5 inputs.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/source_adapter.py
- [[Deprecated L4 transport replay path; delegates to ``layer05_transport_segment``.]] - rationale - django_apps/asteroid_lab/replay/layer04_transport_segment.py
- [[Layer 04 shared router helpers + MVP delegate to sequential router.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/mvp_router.py
- [[Layer 04 transport routing orchestrator (PR-L4-0 stub).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py
- [[Layer04RoutePlan]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/layer04_post_summary_metrics.py
- [[Layer04SourceView]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py
- [[MVP routing when map + rim + exterior plan are present (canonical L5 slug).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py
- [[Map L3 ``throughput_factor`` to L4 connector lane M-units.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/source_adapter.py
- [[Map L3 rim greedy result into Layer 04 routing source views.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/source_adapter.py
- [[ResourceKind_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/equivalence_key.py
- [[RouteGroupRegistry_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py
- [[Semantic equivalence keys for rim bundle dedupe (gene_key excluded).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/shared/equivalence_key.py
- [[Sequential merge-aware Layer 04 transport router.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py
- [[_build_goal_set()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py
- [[_collect_equipment()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/mvp_router.py
- [[_connector_goals_with_capacity()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py
- [[_manhattan()_2]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/mvp_router.py
- [[_nearest_goal_estimate()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/mvp_router.py
- [[_route_not_found_detail()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py
- [[_sort_sources()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/mvp_router.py
- [[_transport_kind_enum()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/mvp_router.py
- [[_transport_kind_for_resource()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/mvp_router.py
- [[_unit_capacity_m()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/mvp_router.py
- [[build_equivalence_key()]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/equivalence_key.py
- [[build_equivalence_key_from_candidate()]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/equivalence_key.py
- [[build_layer04_sources()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/source_adapter.py
- [[build_layer04_transport_frames()]] - code - django_apps/asteroid_lab/replay/layer04_transport_segment.py
- [[collect_inner_routeable_equipment()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/source_adapter.py
- [[equivalence_key.py]] - code - django_apps/asteroid_lab/layers/shared/equivalence_key.py
- [[equivalence_key.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/equivalence_key.py
- [[layer04_transport_segment.py]] - code - django_apps/asteroid_lab/replay/layer04_transport_segment.py
- [[mvp_router.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/mvp_router.py
- [[route_layer04_mvp()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/mvp_router.py
- [[route_layer04_sequential()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py
- [[run.py_4]] - code - django_apps/asteroid_lab/layers/layer_04_transport_routing/run.py
- [[run.py_10]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py
- [[run_layer_05_transport_routing()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py
- [[sequential_router.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py
- [[source_adapter.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/source_adapter.py
- [[throughput_factor_to_source_load_m()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/source_adapter.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/route_layer04_sequential
SORT file.name ASC
```

## Connections to other communities
- 10 edges to [[_COMMUNITY_Coord]]
- 6 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 5 edges to [[_COMMUNITY_layer03_rim_greedy_segment.py]]
- 4 edges to [[_COMMUNITY_ExteriorConnectionPlan]]
- 4 edges to [[_COMMUNITY_build_solver_runtime_replay_frames()]]
- 3 edges to [[_COMMUNITY_exhaustive_generator.py]]
- 2 edges to [[_COMMUNITY_run_layers_02_to_06()]]
- 1 edge to [[_COMMUNITY_run_full_from_cleanup_recon()]]
- 1 edge to [[_COMMUNITY_ReplayEventType]]
- 1 edge to [[_COMMUNITY_build_layer05_transport_post_summary_met]]
- 1 edge to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_generate_candidates()]]
- 1 edge to [[_COMMUNITY_.validate_route_cell()]]
- 1 edge to [[_COMMUNITY_bbox_from_coords()]]
- 1 edge to [[_COMMUNITY_space_transport_catalog_snapshot.py]]

## Top bridge nodes
- [[route_layer04_sequential()]] - degree 26, connects to 10 communities
- [[run_layer_05_transport_routing()]] - degree 12, connects to 7 communities
- [[route_layer04_mvp()]] - degree 6, connects to 3 communities
- [[ResourceKind_1]] - degree 5, connects to 3 communities
- [[build_layer04_sources()]] - degree 7, connects to 2 communities