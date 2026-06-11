---
type: community
cohesion: 0.43
members: 8
---

# build_demo_parse_row()

**Cohesion:** 0.43 - moderately connected
**Members:** 8 nodes

## Members
- [[_serialize_pattern()]] - code - django_apps/shapez_core/services/preview_service.py
- [[build_demo_parse_row()]] - code - django_apps/shapez_core/services/preview_service.py
- [[build_demo_parse_rows()]] - code - django_apps/shapez_core/services/preview_service.py
- [[build_shape_preview_response()]] - code - django_apps/shapez_core/services/preview_service.py
- [[demo()]] - code - django_apps/web/views/public_pages.py
- [[get_color_catalog_rows()]] - code - django_apps/shapez_core/services/preview_service.py
- [[get_shape_catalog_rows()]] - code - django_apps/shapez_core/services/preview_service.py
- [[preview_service.py]] - code - django_apps/shapez_core/services/preview_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_demo_parse_row
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_Any]]
- 3 edges to [[_COMMUNITY_ShapeCodeParseError]]
- 3 edges to [[_COMMUNITY_build_shape_render_scene()]]
- 2 edges to [[_COMMUNITY_public_pages.py]]
- 1 edge to [[_COMMUNITY_HttpRequest]]
- 1 edge to [[_COMMUNITY__run_solver_post_traced()]]

## Top bridge nodes
- [[build_demo_parse_row()]] - degree 8, connects to 3 communities
- [[demo()]] - degree 6, connects to 2 communities
- [[build_shape_preview_response()]] - degree 4, connects to 2 communities
- [[_serialize_pattern()]] - degree 4, connects to 2 communities
- [[build_demo_parse_rows()]] - degree 4, connects to 1 community