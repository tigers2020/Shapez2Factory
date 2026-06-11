---
type: community
cohesion: 0.10
members: 28
---

# build_layer02_timeline_frame_wire_dict()

**Cohesion:** 0.10 - loosely connected
**Members:** 28 nodes

## Members
- [[Attach exterior connector plan wire to Lab replay frames (output-only).]] - rationale - django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py
- [[Deprecated use ``replay.solver_runtime_assembler.build_solver_runtime_replay_fr]] - rationale - django_apps/asteroid_lab/services/lab_layer02_timeline.py
- [[Drop generic belt overlays on void coords reserved for white L2 markers.]] - rationale - django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py
- [[Index of first frame that should show L2 overlay; None when L2 is not on the tim]] - rationale - django_apps/asteroid_lab/services/lab_layer02_timeline.py
- [[Layer 02 exterior transport runtime replay segment (projection only).]] - rationale - django_apps/asteroid_lab/replay/layer02_segment.py
- [[Layer 02 solver timeline frame builder (append-stack; output-only).]] - rationale - django_apps/asteroid_lab/services/lab_layer02_timeline.py
- [[One append-stack milestone L1 full map + L2 planned connector overlay only.]] - rationale - django_apps/asteroid_lab/services/lab_layer02_timeline.py
- [[Rebuild persistent L2 exterior connector overlay rows from plan wire (SoT).]] - rationale - django_apps/asteroid_lab/replay/persistent_exterior_overlay.py
- [[Return enriched frames and optional frozen plan wire for track metrics.      W]] - rationale - django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py
- [[SoT ``exterior_connector_plan.planned_connectors.void_coord`` — not L2 frame]] - rationale - django_apps/asteroid_lab/replay/persistent_exterior_overlay.py
- [[Wire dict for one L2 append milestone (L1 full map + connector overlay).]] - rationale - django_apps/asteroid_lab/replay/layer02_segment.py
- [[_bbox_from_rows()]] - code - django_apps/asteroid_lab/replay/layer02_segment.py
- [[_connector_coord_keys()]] - code - django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py
- [[_decoded_cell_to_row()]] - code - django_apps/asteroid_lab/replay/layer02_segment.py
- [[_display_rows_from_complete_map()]] - code - django_apps/asteroid_lab/replay/layer02_segment.py
- [[_overlay_without_connector_coord_duplicates()]] - code - django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py
- [[_planned_connectors()]] - code - django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py
- [[build_layer02_runtime_replay_frames()]] - code - django_apps/asteroid_lab/services/lab_layer02_timeline.py
- [[build_layer02_timeline_frame_dict()]] - code - django_apps/asteroid_lab/services/lab_layer02_timeline.py
- [[build_layer02_timeline_frame_wire_dict()]] - code - django_apps/asteroid_lab/replay/layer02_segment.py
- [[enrich_lab_timeline_frames_with_exterior_connector_plan()]] - code - django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py
- [[lab_layer02_timeline.py]] - code - django_apps/asteroid_lab/services/lab_layer02_timeline.py
- [[lab_timeline_exterior_connector_enrichment.py]] - code - django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py
- [[layer02_segment.py]] - code - django_apps/asteroid_lab/replay/layer02_segment.py
- [[map_view_from_complete_map()]] - code - django_apps/asteroid_lab/replay/layer02_segment.py
- [[persistent_connector_overlays_from_wire()]] - code - django_apps/asteroid_lab/replay/persistent_exterior_overlay.py
- [[persistent_exterior_overlay.py]] - code - django_apps/asteroid_lab/replay/persistent_exterior_overlay.py
- [[resolve_l2_complete_frame_index()]] - code - django_apps/asteroid_lab/services/lab_layer02_timeline.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_layer02_timeline_frame_wire_dict
SORT file.name ASC
```

## Connections to other communities
- 11 edges to [[_COMMUNITY_Any]]
- 5 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 5 edges to [[_COMMUNITY_build_solver_runtime_replay_frames()]]
- 3 edges to [[_COMMUNITY_timeline_serialization.py]]
- 2 edges to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]
- 2 edges to [[_COMMUNITY_build_lab_replay_frames_for_project()]]
- 1 edge to [[_COMMUNITY_DecodedCellDTO]]

## Top bridge nodes
- [[map_view_from_complete_map()]] - degree 10, connects to 4 communities
- [[build_layer02_timeline_frame_wire_dict()]] - degree 11, connects to 3 communities
- [[build_layer02_runtime_replay_frames()]] - degree 5, connects to 3 communities
- [[enrich_lab_timeline_frames_with_exterior_connector_plan()]] - degree 7, connects to 2 communities
- [[_display_rows_from_complete_map()]] - degree 6, connects to 2 communities