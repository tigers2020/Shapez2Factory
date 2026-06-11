---
type: community
cohesion: 0.14
members: 21
---

# enrich_lab_timeline_frames_with_terrain_

**Cohesion:** 0.14 - loosely connected
**Members:** 21 nodes

## Members
- [[Attach pattern bundle highlight wire to Lab replay timeline frames (output-only)]] - rationale - django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py
- [[Attach terrain rim highlight wire to Lab replay timeline frames (output-only).]] - rationale - django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py
- [[Lab timeline helpers for reconstruction-complete source frames (replay package).]] - rationale - django_apps/asteroid_lab/replay/reconstruction_source.py
- [[Last renderable ``reconstruction.completed`` frame (L1 map base for runtime appe]] - rationale - django_apps/asteroid_lab/replay/reconstruction_source.py
- [[Return enriched frames and optional frozen complete-map rim wire.]] - rationale - django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py
- [[Return frames with ``metrics.pattern_bundle_highlights`` when equipment bundles]] - rationale - django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py
- [[_cell_overlay_from_frame()]] - code - django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py
- [[_decoded_from_replay_row()]] - code - django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py
- [[_full_cell_rows_from_frame()]] - code - django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py
- [[_highlight_wire_from_frame_rows()]] - code - django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py
- [[_is_complete_frame()]] - code - django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py
- [[_pattern_bundle_wire_is_usable()]] - code - django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py
- [[_topology_from_renderable_rows()]] - code - django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py
- [[_wire_from_equipment_bundles()]] - code - django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py
- [[enrich_lab_timeline_frames_with_pattern_bundle_highlights()]] - code - django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py
- [[enrich_lab_timeline_frames_with_terrain_rim()]] - code - django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py
- [[find_reconstruction_complete_source_frame()]] - code - django_apps/asteroid_lab/replay/reconstruction_source.py
- [[frame_has_renderable_map()]] - code - django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py
- [[lab_timeline_pattern_bundle_enrichment.py]] - code - django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py
- [[lab_timeline_rim_enrichment.py]] - code - django_apps/asteroid_lab/services/lab_timeline_rim_enrichment.py
- [[reconstruction_source.py]] - code - django_apps/asteroid_lab/replay/reconstruction_source.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/enrich_lab_timeline_frames_with_terrain_
SORT file.name ASC
```

## Connections to other communities
- 12 edges to [[_COMMUNITY_Any]]
- 3 edges to [[_COMMUNITY_ReconstructionResult]]
- 2 edges to [[_COMMUNITY_build_terrain_rim_highlight_from_rendera]]
- 2 edges to [[_COMMUNITY_build_lab_replay_frames_for_project()]]
- 1 edge to [[_COMMUNITY_DecodedCellDTO]]
- 1 edge to [[_COMMUNITY_Coord]]
- 1 edge to [[_COMMUNITY_ReplayOverlayCell]]
- 1 edge to [[_COMMUNITY_build_solver_runtime_replay_frames()]]

## Top bridge nodes
- [[_topology_from_renderable_rows()]] - degree 7, connects to 3 communities
- [[_highlight_wire_from_frame_rows()]] - degree 7, connects to 3 communities
- [[enrich_lab_timeline_frames_with_pattern_bundle_highlights()]] - degree 8, connects to 2 communities
- [[enrich_lab_timeline_frames_with_terrain_rim()]] - degree 8, connects to 2 communities
- [[find_reconstruction_complete_source_frame()]] - degree 5, connects to 2 communities