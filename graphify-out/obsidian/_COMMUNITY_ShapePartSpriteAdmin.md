---
type: community
cohesion: 0.17
members: 15
---

# ShapePartSpriteAdmin

**Cohesion:** 0.17 - loosely connected
**Members:** 15 nodes

## Members
- [[.get_urls()_1]] - code - django_apps/web/admin.py
- [[.has_add_permission()_6]] - code - django_apps/web/admin.py
- [[.has_delete_permission()_5]] - code - django_apps/web/admin.py
- [[.job_status_view()]] - code - django_apps/web/admin.py
- [[.preview_image()]] - code - django_apps/web/admin.py
- [[.render_progress_view()]] - code - django_apps/web/admin.py
- [[.start_missing_job_view()]] - code - django_apps/web/admin.py
- [[.start_sample_quadrants_job_view()]] - code - django_apps/web/admin.py
- [[.start_tank_missing_job_view()]] - code - django_apps/web/admin.py
- [[AsteroidDecodedLayoutDocumentAdmin]] - code - django_apps/web/admin.py
- [[Read-only view of imported decoded JSON (use management command to load).]] - rationale - django_apps/web/admin.py
- [[ShapePartSprite]] - code - django_apps/web/admin.py
- [[ShapePartSpriteAdmin]] - code - django_apps/web/admin.py
- [[admin.py_4]] - code - django_apps/web/admin.py
- [[job_cache_key()]] - code - django_apps/web/services/shape_part_sprite_generation.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ShapePartSpriteAdmin
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY__build_work_queue()]]
- 2 edges to [[_COMMUNITY_shape_part_sprite_generation.py]]

## Top bridge nodes
- [[job_cache_key()]] - degree 6, connects to 1 community
- [[admin.py_4]] - degree 3, connects to 1 community
- [[.start_missing_job_view()]] - degree 3, connects to 1 community
- [[.start_sample_quadrants_job_view()]] - degree 3, connects to 1 community
- [[.start_tank_missing_job_view()]] - degree 3, connects to 1 community