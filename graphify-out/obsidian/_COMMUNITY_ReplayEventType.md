---
type: community
cohesion: 0.12
members: 25
---

# ReplayEventType

**Cohesion:** 0.12 - loosely connected
**Members:** 25 nodes

## Members
- [[Explicit ReplayEventType adapter coverage (Phase 9B Lab  Phase 9F solver runtim]] - rationale - django_apps/asteroid_lab/replay/replay_event_coverage.py
- [[Layer 05 transport routing replay segment (canonical L5 slug).]] - rationale - django_apps/asteroid_lab/replay/layer05_transport_segment.py
- [[Layer05RoutePlan]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/layer05_post_summary_metrics.py
- [[Legacy event-only projector (metrics frames); prefer runtime builder with overla]] - rationale - django_apps/asteroid_lab/replay/layer03_rim_greedy_segment.py
- [[ReplayEventType]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[Return (9B lab output, post-9B) coverage sets.]] - rationale - django_apps/asteroid_lab/replay/replay_event_coverage.py
- [[RimGreedyObservationPhase]] - code - django_apps/asteroid_lab/replay/layer03_rim_greedy_segment.py
- [[Stable ``event_type`` strings for replay snapshot events (A4 contract).  These]] - rationale - django_apps/asteroid_lab/replay/event_types.py
- [[_event_type_for_phase()]] - code - django_apps/asteroid_lab/replay/layer03_rim_greedy_segment.py
- [[_overlay_from_route_path_fallback()]] - code - django_apps/asteroid_lab/replay/layer05_transport_segment.py
- [[_overlay_from_tile()]] - code - django_apps/asteroid_lab/replay/layer05_transport_segment.py
- [[_overlays_for_plan()]] - code - django_apps/asteroid_lab/replay/layer05_transport_segment.py
- [[_spec()_2]] - code - django_apps/asteroid_lab/replay/layer04_inner_pattern_fill_segment.py
- [[_spec()_4]] - code - django_apps/asteroid_lab/replay/layer05_transport_segment.py
- [[_union_route_path_coords()]] - code - django_apps/asteroid_lab/replay/layer05_transport_segment.py
- [[assert_registered_event_type()]] - code - django_apps/asteroid_lab/replay/event_types.py
- [[build_layer03_rim_greedy_segment_specs()]] - code - django_apps/asteroid_lab/replay/layer03_rim_greedy_segment.py
- [[build_layer05_transport_frames()]] - code - django_apps/asteroid_lab/replay/layer05_transport_segment.py
- [[event_types.py]] - code - django_apps/asteroid_lab/replay/event_types.py
- [[is_registered_event_type()]] - code - django_apps/asteroid_lab/replay/event_types.py
- [[is_rttp_milestone_event_type()]] - code - django_apps/asteroid_lab/replay/event_types.py
- [[layer05_transport_segment.py]] - code - django_apps/asteroid_lab/replay/layer05_transport_segment.py
- [[normalize_rttp_milestone_event_type()]] - code - django_apps/asteroid_lab/replay/event_types.py
- [[replay_event_coverage.py]] - code - django_apps/asteroid_lab/replay/replay_event_coverage.py
- [[replay_event_type_coverage_partitions()]] - code - django_apps/asteroid_lab/replay/replay_event_coverage.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ReplayEventType
SORT file.name ASC
```

## Connections to other communities
- 8 edges to [[_COMMUNITY_build_solver_runtime_replay_frames()]]
- 7 edges to [[_COMMUNITY_ReplayOverlayCell]]
- 4 edges to [[_COMMUNITY_layer03_rim_greedy_segment.py]]
- 2 edges to [[_COMMUNITY_build_layer03_runtime_segment_specs()]]
- 2 edges to [[_COMMUNITY_space_transport_catalog_snapshot.py]]
- 1 edge to [[_COMMUNITY_Coord]]
- 1 edge to [[_COMMUNITY_ReplayRecorder]]
- 1 edge to [[_COMMUNITY_lab_timeline_adapter.py]]
- 1 edge to [[_COMMUNITY_timeline_serialization.py]]
- 1 edge to [[_COMMUNITY_ExteriorConnectionPlan]]
- 1 edge to [[_COMMUNITY_route_layer04_sequential()]]
- 1 edge to [[_COMMUNITY_golden_valid_baseline.py]]
- 1 edge to [[_COMMUNITY_build_failed_source_diagnostic()]]
- 1 edge to [[_COMMUNITY_build_layer05_transport_post_summary_met]]

## Top bridge nodes
- [[ReplayEventType]] - degree 10, connects to 5 communities
- [[assert_registered_event_type()]] - degree 9, connects to 4 communities
- [[Layer05RoutePlan]] - degree 7, connects to 4 communities
- [[build_layer03_rim_greedy_segment_specs()]] - degree 5, connects to 3 communities
- [[build_layer05_transport_frames()]] - degree 8, connects to 2 communities