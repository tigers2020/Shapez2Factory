---
type: community
cohesion: 0.14
members: 18
---

# resolve_sprite_static_relpath()

**Cohesion:** 0.14 - loosely connected
**Members:** 18 nodes

## Members
- [[.handle()_8]] - code - django_apps/shapez_core/management/commands/backfill_sprite_static_relpaths.py
- [[0004_shapezgameidentifier_sprite_static_relpath.py]] - code - django_apps/shapez_core/migrations/0004_shapezgameidentifier_sprite_static_relpath.py
- [[Command_8]] - code - django_apps/shapez_core/management/commands/backfill_sprite_static_relpaths.py
- [[Map blueprint ``T`` → posix relpath for every committed SVG under ``sprites``.]] - rationale - django_apps/shapez_core/lab_sprite_path.py
- [[Migration_53]] - code - django_apps/shapez_core/migrations/0004_shapezgameidentifier_sprite_static_relpath.py
- [[Refresh ShapezGameIdentifier.sprite_static_relpath for all rows.]] - rationale - django_apps/shapez_core/management/commands/backfill_sprite_static_relpaths.py
- [[Resolve lab SVG path under ``webassetssprites`` for a basedata identifier ``v]] - rationale - django_apps/shapez_core/lab_sprite_path.py
- [[Return posix relpath under static ``webassetssprites``, or ```` if no file.]] - rationale - django_apps/shapez_core/lab_sprite_path.py
- [[Return posix relpath when ``identifier_value.svg`` exists under ``root`` rules.]] - rationale - django_apps/shapez_core/lab_sprite_path.py
- [[_backfill_sprite_paths()]] - code - django_apps/shapez_core/migrations/0004_shapezgameidentifier_sprite_static_relpath.py
- [[_clear_sprite_paths()]] - code - django_apps/shapez_core/migrations/0004_shapezgameidentifier_sprite_static_relpath.py
- [[_relpath_for_identifier_at_root()]] - code - django_apps/shapez_core/lab_sprite_path.py
- [[``django_appswebstaticwebassetssprites`` (repo layout).]] - rationale - django_apps/shapez_core/lab_sprite_path.py
- [[backfill_sprite_static_relpaths.py]] - code - django_apps/shapez_core/management/commands/backfill_sprite_static_relpaths.py
- [[default_lab_sprites_root()]] - code - django_apps/shapez_core/lab_sprite_path.py
- [[lab_sprite_path.py]] - code - django_apps/shapez_core/lab_sprite_path.py
- [[resolve_sprite_static_relpath()]] - code - django_apps/shapez_core/lab_sprite_path.py
- [[scan_committed_lab_sprite_identifier_map()]] - code - django_apps/shapez_core/lab_sprite_path.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/resolve_sprite_static_relpath
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_Path]]
- 1 edge to [[_COMMUNITY_lab_sprite_resolve()]]
- 1 edge to [[_COMMUNITY_BaseCommand]]
- 1 edge to [[_COMMUNITY__IvvdReadOnlyAdminMixin]]
- 1 edge to [[_COMMUNITY_public_pages.py]]

## Top bridge nodes
- [[resolve_sprite_static_relpath()]] - degree 9, connects to 3 communities
- [[scan_committed_lab_sprite_identifier_map()]] - degree 6, connects to 2 communities
- [[default_lab_sprites_root()]] - degree 5, connects to 1 community
- [[_relpath_for_identifier_at_root()]] - degree 5, connects to 1 community
- [[Command_8]] - degree 3, connects to 1 community