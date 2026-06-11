---
type: community
cohesion: 0.24
members: 19
---

# shape_part_sprite_generation.py

**Cohesion:** 0.24 - loosely connected
**Members:** 19 nodes

## Members
- [[Bake PNGs for atomic variants; optionally skip rows that already have a stored i]] - rationale - django_apps/web/services/shape_part_sprite_generation.py
- [[Merge ``updates`` into an existing job dict (admin progress polling).]] - rationale - django_apps/web/services/shape_part_sprite_generation.py
- [[Run Playwright atomic sprite bake (CLI and admin).]] - rationale - django_apps/web/services/shape_part_sprite_generation.py
- [[ShapePartSpriteGenerationStats]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[TextIO]] - code - src/shapez2_factory/application/asteroid_lab/replay_core.py
- [[_check_sprite_renderer_prerequisites()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_import_pillow_image()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_merge_job_done_empty()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_merge_job_done_final()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_merge_job_error()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_merge_job_progress_slice()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_merge_job_running()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_run_node_scene_to_png_bytes()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_run_sprite_job_background()]] - code - django_apps/web/admin.py
- [[_which_node()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_write_stream()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[generate_shape_part_sprites()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[merge_job_state()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[shape_part_sprite_generation.py]] - code - django_apps/web/services/shape_part_sprite_generation.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/shape_part_sprite_generationpy
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY__build_work_queue()]]
- 4 edges to [[_COMMUNITY_Path]]
- 4 edges to [[_COMMUNITY_shape_part_sprites.py]]
- 3 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_ShapePartSpriteAdmin]]
- 2 edges to [[_COMMUNITY_write_replay_core_jsonl()]]
- 1 edge to [[_COMMUNITY_BaseCommand]]

## Top bridge nodes
- [[generate_shape_part_sprites()]] - degree 20, connects to 4 communities
- [[shape_part_sprite_generation.py]] - degree 23, connects to 3 communities
- [[_run_node_scene_to_png_bytes()]] - degree 4, connects to 2 communities
- [[merge_job_state()]] - degree 9, connects to 1 community
- [[_check_sprite_renderer_prerequisites()]] - degree 7, connects to 1 community