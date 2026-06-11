---
type: community
cohesion: 0.10
members: 20
---

# BaseCommand

**Cohesion:** 0.10 - loosely connected
**Members:** 20 nodes

## Members
- [[.add_arguments()_6]] - code - django_apps/shapez_core/management/commands/import_shapez_basedata.py
- [[.add_arguments()_8]] - code - django_apps/web/management/commands/generate_shape_part_sprites.py
- [[.handle()_2]] - code - django_apps/asteroid_lab/management/commands/run_solver_reap.py
- [[.handle()_9]] - code - django_apps/shapez_core/management/commands/import_shapez_basedata.py
- [[.handle()_11]] - code - django_apps/web/management/commands/generate_shape_part_sprites.py
- [[.handle()_12]] - code - django_apps/web/management/commands/verify_database.py
- [[ArgumentParser]] - code - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[Bake atomic quadrant PNGs via Playwright and persist ``ShapePartSprite`` rows.]] - rationale - django_apps/web/management/commands/generate_shape_part_sprites.py
- [[BaseCommand]] - code
- [[Command_2]] - code - django_apps/asteroid_lab/management/commands/run_solver_reap.py
- [[Command_9]] - code - django_apps/shapez_core/management/commands/import_shapez_basedata.py
- [[Command_11]] - code - django_apps/web/management/commands/generate_shape_part_sprites.py
- [[Command_12]] - code - django_apps/web/management/commands/verify_database.py
- [[Import a shapez2 basedata bundle (IVVD) into the canonical DB.]] - rationale - django_apps/shapez_core/management/commands/import_shapez_basedata.py
- [[One-shot connectivity check for Render  DATABASE_URL troubleshooting.]] - rationale - django_apps/web/management/commands/verify_database.py
- [[Reap RUNNING solver runs via artifact-first reconcile (PR-CLI-7).]] - rationale - django_apps/asteroid_lab/management/commands/run_solver_reap.py
- [[generate_shape_part_sprites.py]] - code - django_apps/web/management/commands/generate_shape_part_sprites.py
- [[import_shapez_basedata.py]] - code - django_apps/shapez_core/management/commands/import_shapez_basedata.py
- [[run_solver_reap.py]] - code - django_apps/asteroid_lab/management/commands/run_solver_reap.py
- [[verify_database.py]] - code - django_apps/web/management/commands/verify_database.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/BaseCommand
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_Command]]
- 1 edge to [[_COMMUNITY_Command]]
- 1 edge to [[_COMMUNITY_entry_result_to_json_dict()]]
- 1 edge to [[_COMMUNITY_Command]]
- 1 edge to [[_COMMUNITY_.handle()]]
- 1 edge to [[_COMMUNITY_rebuild_game_data_taxonomy()]]
- 1 edge to [[_COMMUNITY_resolve_sprite_static_relpath()]]
- 1 edge to [[_COMMUNITY_shape_part_sprites.py]]
- 1 edge to [[_COMMUNITY_SolverRun]]
- 1 edge to [[_COMMUNITY__IvvdReadOnlyAdminMixin]]
- 1 edge to [[_COMMUNITY__run_artifact()]]
- 1 edge to [[_COMMUNITY_shape_part_sprite_generation.py]]

## Top bridge nodes
- [[BaseCommand]] - degree 13, connects to 8 communities
- [[.handle()_2]] - degree 3, connects to 2 communities
- [[.handle()_11]] - degree 3, connects to 2 communities
- [[.handle()_9]] - degree 2, connects to 1 community
- [[ArgumentParser]] - degree 2, connects to 1 community