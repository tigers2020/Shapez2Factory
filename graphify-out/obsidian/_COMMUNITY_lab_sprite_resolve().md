---
type: community
cohesion: 0.15
members: 17
---

# lab_sprite_resolve()

**Cohesion:** 0.15 - loosely connected
**Members:** 17 nodes

## Members
- [[Identifier ``T`` → ``sprite_static_relpath`` when present in basedata import.]] - rationale - django_apps/asteroid_lab/admin_lab_sprites.py
- [[Lab blueprint cell → static sprite relpath + display rotation (Admin mini-map).]] - rationale - django_apps/asteroid_lab/admin_lab_sprites.py
- [[Lab map sprites resolve static paths from ``ShapezGameIdentifier`` rows.]] - rationale - django_apps/shapez_core/services/lab_sprite_identifier_service.py
- [[Latest class`ShapezBasedataRelease` by ``game_version``, or a specific ``relea]] - rationale - django_apps/shapez_core/services/lab_sprite_identifier_service.py
- [[Mirror ``normalizeQuarterTurns`` in ``asteroid_miner_layout_lab.js`` (0..3).]] - rationale - django_apps/asteroid_lab/admin_lab_sprites.py
- [[Return ``(sprite_static_relpath_or_none, display_rotation_quarters)``.      De]] - rationale - django_apps/asteroid_lab/admin_lab_sprites.py
- [[Return ``sprite_static_relpath`` (posix under ``webassetssprites``) or ``]] - rationale - django_apps/shapez_core/services/lab_sprite_identifier_service.py
- [[Static relpath only (no ``R``). Prefer func`lab_sprite_resolve` for ``T``+``R`]] - rationale - django_apps/asteroid_lab/admin_lab_sprites.py
- [[admin_lab_sprites.py]] - code - django_apps/asteroid_lab/admin_lab_sprites.py
- [[get_lab_sprite_relpath_for_value()]] - code - django_apps/shapez_core/services/lab_sprite_identifier_service.py
- [[lab_sprite_identifier_service.py]] - code - django_apps/shapez_core/services/lab_sprite_identifier_service.py
- [[lab_sprite_relpath_for_cell()]] - code - django_apps/asteroid_lab/admin_lab_sprites.py
- [[lab_sprite_relpath_from_cell_kind()]] - code - django_apps/asteroid_lab/admin_lab_sprites.py
- [[lab_sprite_relpath_from_tile_type()]] - code - django_apps/asteroid_lab/admin_lab_sprites.py
- [[lab_sprite_resolve()]] - code - django_apps/asteroid_lab/admin_lab_sprites.py
- [[normalize_lab_rotation_q()]] - code - django_apps/asteroid_lab/admin_lab_sprites.py
- [[resolve_lab_release_for_sprites()]] - code - django_apps/shapez_core/services/lab_sprite_identifier_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/lab_sprite_resolve
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_public_pages.py]]
- 1 edge to [[_COMMUNITY_lab_screen_grid.py]]
- 1 edge to [[_COMMUNITY_resolve_sprite_static_relpath()]]
- 1 edge to [[_COMMUNITY_SafeString]]
- 1 edge to [[_COMMUNITY__IvvdReadOnlyAdminMixin]]

## Top bridge nodes
- [[lab_sprite_resolve()]] - degree 8, connects to 2 communities
- [[normalize_lab_rotation_q()]] - degree 5, connects to 2 communities
- [[resolve_lab_release_for_sprites()]] - degree 4, connects to 2 communities
- [[lab_sprite_relpath_from_tile_type()]] - degree 6, connects to 1 community
- [[lab_sprite_identifier_service.py]] - degree 4, connects to 1 community