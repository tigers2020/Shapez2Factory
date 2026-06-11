---
type: community
cohesion: 0.23
members: 12
---

# _build_work_queue()

**Cohesion:** 0.23 - loosely connected
**Members:** 12 nodes

## Members
- [[Enumerate finite mesh × non-empty color × quadrant for offline sprite baking.]] - rationale - django_apps/web/services/shape_part_sprites.py
- [[Pedestal bake runs before quadrant variants when not already stored.]] - rationale - django_apps/web/services/shape_part_sprite_generation.py
- [[Return variants to render and how many were skipped as already complete.]] - rationale - django_apps/web/services/shape_part_sprite_generation.py
- [[_build_work_queue()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_prepend_pedestal_if_needed()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_resolve_generation_specs()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_variant_row_exists_with_image()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[``default_fluid_tank_vortex`` (``t``) × colors × quadrants; skip complete rows.]] - rationale - django_apps/web/services/shape_part_sprite_generation.py
- [[``default_rect`` + red, quadrants 0..3 only; optional skip of complete rows.]] - rationale - django_apps/web/services/shape_part_sprite_generation.py
- [[build_sample_quadrant_work_queue()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[build_tank_sprite_work_queue()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[iter_atomic_sprite_specs()]] - code - django_apps/web/services/shape_part_sprites.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/_build_work_queue
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_shape_part_sprite_generation.py]]
- 3 edges to [[_COMMUNITY_ShapePartSpriteAdmin]]
- 2 edges to [[_COMMUNITY_shape_part_sprites.py]]

## Top bridge nodes
- [[_build_work_queue()]] - degree 7, connects to 2 communities
- [[build_tank_sprite_work_queue()]] - degree 6, connects to 2 communities
- [[build_sample_quadrant_work_queue()]] - degree 5, connects to 2 communities
- [[_prepend_pedestal_if_needed()]] - degree 6, connects to 1 community
- [[iter_atomic_sprite_specs()]] - degree 5, connects to 1 community