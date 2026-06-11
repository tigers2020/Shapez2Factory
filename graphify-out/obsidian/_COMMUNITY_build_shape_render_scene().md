---
type: community
cohesion: 0.19
members: 16
---

# build_shape_render_scene()

**Cohesion:** 0.19 - loosely connected
**Members:** 16 nodes

## Members
- [[NormalizedShapePattern_1]] - code - django_apps/shapez_solver/services/fluid_carrier_render_scene.py
- [[One centered vortex tank for valid pure-fluid patterns; else quadrant scene.]] - rationale - django_apps/shapez_solver/services/fluid_carrier_render_scene.py
- [[Preview scene for ``source_carrier=fluid`` (vortex tank glTF, sprites ``color-`]] - rationale - django_apps/shapez_solver/services/fluid_carrier_render_scene.py
- [[QuadrantPosition_1]] - code - django_apps/shapez_core/services/shape_render_scene.py
- [[ShapeRenderCell]] - code - django_apps/shapez_core/services/shape_render_scene.py
- [[ShapeRenderScene]] - code - django_apps/shapez_core/services/shape_render_scene.py
- [[ShapeRenderScene_1]] - code - django_apps/shapez_solver/services/fluid_carrier_render_scene.py
- [[Single JSON payload contract for graph preview, modal preview, and sprite builde]] - rationale - django_apps/shapez_core/services/shape_render_scene.py
- [[_transform_key()]] - code - django_apps/shapez_core/services/shape_render_scene.py
- [[build_atomic_preview_scene()]] - code - django_apps/web/services/shape_part_sprites.py
- [[build_fluid_carrier_preview_scene()]] - code - django_apps/shapez_solver/services/fluid_carrier_render_scene.py
- [[build_shape_render_scene()]] - code - django_apps/shapez_core/services/shape_render_scene.py
- [[fluid_carrier_render_scene.py]] - code - django_apps/shapez_solver/services/fluid_carrier_render_scene.py
- [[pattern_from_shape()]] - code - django_apps/shapez_core/services/shape_codec.py
- [[serialize_render_scene()]] - code - django_apps/shapez_core/services/shape_render_scene.py
- [[shape_render_scene.py]] - code - django_apps/shapez_core/services/shape_render_scene.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_shape_render_scene
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_shape_part_sprites.py]]
- 3 edges to [[_COMMUNITY_build_demo_parse_row()]]
- 3 edges to [[_COMMUNITY_macro_recipe_graph_visual.py]]
- 2 edges to [[_COMMUNITY_Shape]]
- 2 edges to [[_COMMUNITY_analyze_pattern_lab_shape()]]
- 2 edges to [[_COMMUNITY_ShapeCodeParseError]]
- 2 edges to [[_COMMUNITY_shape_codec.py]]
- 1 edge to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_shape_pattern.py]]
- 1 edge to [[_COMMUNITY_pure_fluid_color()]]

## Top bridge nodes
- [[serialize_render_scene()]] - degree 8, connects to 4 communities
- [[build_shape_render_scene()]] - degree 10, connects to 3 communities
- [[build_fluid_carrier_preview_scene()]] - degree 9, connects to 3 communities
- [[NormalizedShapePattern_1]] - degree 7, connects to 3 communities
- [[build_atomic_preview_scene()]] - degree 6, connects to 2 communities