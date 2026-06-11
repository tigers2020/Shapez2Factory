---
type: community
cohesion: 0.12
members: 16
---

# timeline_dtos.py

**Cohesion:** 0.12 - loosely connected
**Members:** 16 nodes

## Members
- [[2D-renderable map payload; every timeline frame must include one.]] - rationale - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[Full snapshot cell in ``map_view.full_cells``.]] - rationale - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[Highlight  probe path  bundle overlay cell.]] - rationale - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[Inclusive Labworld bounding box for replay map_view (wire min_xmax_xmin_yma]] - rationale - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[Lab replay timeline DTOs (Phase 9A product contract; output-only artifact).]] - rationale - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[Map annotation (label, reject reason, goal marker).]] - rationale - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[Materialized cell change in ``map_view.cell_delta``.]] - rationale - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[ReplayAnnotation]] - code - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[ReplayBBox_1]] - code - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[ReplayCell_1]] - code - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[ReplayCellDelta]] - code - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[ReplayMapView_1]] - code - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[ReplayOverlayCell_1]] - code - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[ReplayTimelineFrame_1]] - code - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[Single frame on the product Lab replay timeline (never algorithm input).]] - rationale - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[timeline_dtos.py]] - code - django_apps/asteroid_lab/replay/timeline_dtos.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/timeline_dtospy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_build_solver_runtime_replay_frames()]]

## Top bridge nodes
- [[timeline_dtos.py]] - degree 9, connects to 1 community
- [[ReplayMapView_1]] - degree 3, connects to 1 community