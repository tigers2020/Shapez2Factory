---
type: community
cohesion: 0.15
members: 30
---

# timeline_serialization.py

**Cohesion:** 0.15 - loosely connected
**Members:** 30 nodes

## Members
- [[JSON serialization for Lab replay timeline DTOs (Phase 9A).]] - rationale - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[Raised when wire JSON violates the replay timeline contract.]] - rationale - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[ReplayAnnotation_1]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[ReplayBBox]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[ReplayCellDelta_1]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[ReplayPhase]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[ReplayTimelineDeserializationError]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[ReplayTimelineFrame]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[Serialize to JSON text and back (contract helper for tests).]] - rationale - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[_annotation_from_dict()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[_cell_delta_from_dict()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[_cell_from_dict()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[_mapping()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[_overlay_from_dict()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[_require_int()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[_resolved_layer_for_cell()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[_tuple_from_list()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[_wire_kind()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[_wire_transport()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[build_layer02_exterior_transport_frame()]] - code - django_apps/asteroid_lab/replay/layer02_segment.py
- [[parse_replay_event_type()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[parse_replay_phase()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[replay_bbox_from_json_dict()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[replay_bbox_to_json_dict()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[replay_map_view_from_json_dict()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[replay_map_view_to_json_dict()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[replay_timeline_frame_from_json_dict()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[replay_timeline_frame_json_round_trip()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[replay_timeline_frame_to_json_dict()]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[timeline_serialization.py]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/timeline_serializationpy
SORT file.name ASC
```

## Connections to other communities
- 12 edges to [[_COMMUNITY_Any]]
- 8 edges to [[_COMMUNITY_build_solver_runtime_replay_frames()]]
- 7 edges to [[_COMMUNITY_build_lab_replay_frames_for_project()]]
- 5 edges to [[_COMMUNITY_lab_timeline_adapter.py]]
- 4 edges to [[_COMMUNITY_wire_explicit_height_layer()]]
- 3 edges to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]
- 3 edges to [[_COMMUNITY_build_layer02_timeline_frame_wire_dict()]]
- 2 edges to [[_COMMUNITY_compose_replay_timeline()]]
- 1 edge to [[_COMMUNITY_ValueError]]
- 1 edge to [[_COMMUNITY_ReconstructionCompleteMap]]
- 1 edge to [[_COMMUNITY_ReplayEventType]]
- 1 edge to [[_COMMUNITY_ReplayOverlayCell]]

## Top bridge nodes
- [[ReplayTimelineFrame]] - degree 16, connects to 5 communities
- [[replay_timeline_frame_to_json_dict()]] - degree 8, connects to 4 communities
- [[build_layer02_exterior_transport_frame()]] - degree 7, connects to 4 communities
- [[_cell_from_dict()]] - degree 7, connects to 3 communities
- [[_overlay_from_dict()]] - degree 7, connects to 3 communities