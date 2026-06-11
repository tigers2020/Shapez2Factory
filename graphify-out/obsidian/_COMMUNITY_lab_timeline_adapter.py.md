---
type: community
cohesion: 0.15
members: 27
---

# lab_timeline_adapter.py

**Cohesion:** 0.15 - loosely connected
**Members:** 27 nodes

## Members
- [[Deep copy of snapshot fields for immutability tests (not part of public API).]] - rationale - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[Lab ReplayFrame  SnapshotEventDTO → ReplayTimelineFrame (Phase 9B; output-only)]] - rationale - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[LabTimelineAdapterError]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[Raised when a Lab replay frame cannot be conservatively wrapped for 9B.]] - rationale - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[ReplayCell]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[Trace highlights win on duplicate ``(x, y)``.]] - rationale - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[Wire overlay for bundle highlight persisted bundles, else rebuild from map cell]] - rationale - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[Wrap one in-memory Lab snapshot event (does not mutate ``event``).]] - rationale - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[Wrap one persisted Lab ``ReplayFrame`` row (does not mutate ``row``).]] - rationale - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_bbox_from_cells()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_build_map_view()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_cell_from_row()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_cell_overlay_json_for_timeline_lab_frame()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_inspector_from_lab()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_lab_event_type_to_timeline()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_lab_phase_to_timeline()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_merge_overlay_cells()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_normalize_lab_diff()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_overlay_from_row()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_overlay_rows_from_json()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_rows_to_full_cells()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_snapshot_fields_from_payload()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[_trace_overlay_cells_from_diff()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[lab_replay_row_to_timeline_frame()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[lab_snapshot_event_payload_copy()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[lab_snapshot_event_to_timeline_frame()]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py
- [[lab_timeline_adapter.py]] - code - django_apps/asteroid_lab/replay/lab_timeline_adapter.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/lab_timeline_adapterpy
SORT file.name ASC
```

## Connections to other communities
- 11 edges to [[_COMMUNITY_Any]]
- 5 edges to [[_COMMUNITY_timeline_serialization.py]]
- 5 edges to [[_COMMUNITY_ReplayOverlayCell]]
- 3 edges to [[_COMMUNITY_build_solver_runtime_replay_frames()]]
- 2 edges to [[_COMMUNITY_wire_explicit_height_layer()]]
- 2 edges to [[_COMMUNITY_ReplayRecorder]]
- 1 edge to [[_COMMUNITY_ValueError]]
- 1 edge to [[_COMMUNITY_ReplayEventType]]
- 1 edge to [[_COMMUNITY_replay_service.py]]
- 1 edge to [[_COMMUNITY_build_lab_replay_frames_for_project()]]

## Top bridge nodes
- [[lab_replay_row_to_timeline_frame()]] - degree 13, connects to 3 communities
- [[_overlay_from_row()]] - degree 6, connects to 3 communities
- [[_build_map_view()]] - degree 12, connects to 2 communities
- [[lab_snapshot_event_to_timeline_frame()]] - degree 10, connects to 2 communities
- [[_cell_overlay_json_for_timeline_lab_frame()]] - degree 6, connects to 2 communities