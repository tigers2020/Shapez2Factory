---
type: community
cohesion: 0.10
members: 29
---

# shape_part_sprites.py

**Cohesion:** 0.10 - loosely connected
**Members:** 29 nodes

## Members
- [[._log()]] - code - django_apps/web/management/commands/align_shape_part_sprite_asset_names.py
- [[.add_arguments()_7]] - code - django_apps/web/management/commands/align_shape_part_sprite_asset_names.py
- [[.handle()_10]] - code - django_apps/web/management/commands/align_shape_part_sprite_asset_names.py
- [[Align ``assetsshape_part_sprites`` PNG names with ``ShapePartSprite.sprite_key]] - rationale - django_apps/web/management/commands/align_shape_part_sprite_asset_names.py
- [[All ``sprite_key`` values produced by func`iter_atomic_sprite_specs` (+ pedest]] - rationale - django_apps/web/management/commands/align_shape_part_sprite_asset_names.py
- [[Atomic part sprite catalog and preview_scene helpers for recipe tile composition]] - rationale - django_apps/web/services/shape_part_sprites.py
- [[Command_10]] - code - django_apps/web/management/commands/align_shape_part_sprite_asset_names.py
- [[Empty layer, pedestal on; for transparent tile underlay.]] - rationale - django_apps/web/services/shape_part_sprites.py
- [[Inverse of func`sprite_key_to_storage_basename`; ``None`` when not a baked par]] - rationale - django_apps/web/services/shape_part_sprites.py
- [[Manifest  file key aligned with glTF ``extras.script`` naming ``color-{letter}]] - rationale - django_apps/web/services/shape_part_sprites.py
- [[One shape layer as 8 characters (four quadrant tokens), matching game shape-code]] - rationale - django_apps/web/services/shape_part_sprites.py
- [[PNG basename for ``sprite_key`` (```` → ``_``; safe on Windows).]] - rationale - django_apps/web/services/shape_part_sprites.py
- [[Stable manifest  DB key ``{8-char layer}{renderer_version}`` (e.g. ``Cr------]] - rationale - django_apps/web/services/shape_part_sprites.py
- [[Strip Django collision suffixes (``_v1_Ab12cdE.png`` → ``_v1.png``).]] - rationale - django_apps/web/services/shape_part_sprites.py
- [[Value for class`~django_apps.web.models.ShapePartSprite` ``image`` field.]] - rationale - django_apps/web/services/shape_part_sprites.py
- [[_catalog_sprite_keys()]] - code - django_apps/web/management/commands/align_shape_part_sprite_asset_names.py
- [[_persist_sprite_variant_row()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[_sprite_key_and_scene_for_spec()]] - code - django_apps/web/services/shape_part_sprite_generation.py
- [[align_shape_part_sprite_asset_names.py]] - code - django_apps/web/management/commands/align_shape_part_sprite_asset_names.py
- [[atomic_layer_game_code()]] - code - django_apps/web/services/shape_part_sprites.py
- [[build_pedestal_only_preview_scene()]] - code - django_apps/web/services/shape_part_sprites.py
- [[canonical_shape_part_sprite_basename()]] - code - django_apps/web/services/shape_part_sprites.py
- [[make_pedestal_sprite_key()]] - code - django_apps/web/services/shape_part_sprites.py
- [[make_sprite_key()]] - code - django_apps/web/services/shape_part_sprites.py
- [[make_tank_vortex_sprite_key()]] - code - django_apps/web/services/shape_part_sprites.py
- [[shape_part_sprite_image_relpath()]] - code - django_apps/web/services/shape_part_sprites.py
- [[shape_part_sprites.py]] - code - django_apps/web/services/shape_part_sprites.py
- [[sprite_key_from_storage_basename()]] - code - django_apps/web/services/shape_part_sprites.py
- [[sprite_key_to_storage_basename()]] - code - django_apps/web/services/shape_part_sprites.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/shape_part_spritespy
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_build_shape_render_scene()]]
- 4 edges to [[_COMMUNITY_shape_part_sprite_generation.py]]
- 2 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY__build_work_queue()]]
- 1 edge to [[_COMMUNITY_BaseCommand]]
- 1 edge to [[_COMMUNITY_shape_part_sprite_storage()]]

## Top bridge nodes
- [[_sprite_key_and_scene_for_spec()]] - degree 8, connects to 3 communities
- [[shape_part_sprites.py]] - degree 12, connects to 2 communities
- [[_persist_sprite_variant_row()]] - degree 4, connects to 2 communities
- [[.handle()_10]] - degree 7, connects to 1 community
- [[_catalog_sprite_keys()]] - degree 7, connects to 1 community