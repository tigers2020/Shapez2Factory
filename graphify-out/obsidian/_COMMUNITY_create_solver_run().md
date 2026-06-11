---
type: community
cohesion: 0.15
members: 22
---

# create_solver_run()

**Cohesion:** 0.15 - loosely connected
**Members:** 22 nodes

## Members
- [[Create a new inspection run, or reuse and clear frames when ``overwrite`` is tru]] - rationale - django_apps/asteroid_lab/services/experiment_service.py
- [[Ensure a ``ReplayTrack`` exists for (project, ``track_key``), linked to ``solver]] - rationale - django_apps/asteroid_lab/services/experiment_service.py
- [[Insert a ``SolverRun``, replacing any prior row for the same ``(project, run_key]] - rationale - django_apps/asteroid_lab/services/experiment_service.py
- [[Insert one ``SolverRun`` plus default ``ReplayTrack`` scaffolding.      Does]] - rationale - django_apps/asteroid_lab/services/experiment_service.py
- [[Keyword args for ``SolverRun.objects.create``  ``create_solver_run``.]] - rationale - django_apps/asteroid_lab/services/solver_run_fast_cache.py
- [[Mirror selected ``config_json`` keys onto denormalized JSON columns.]] - rationale - django_apps/asteroid_lab/services/solver_run_fast_cache.py
- [[ORM fast-cache mirrors on ``SolverRun`` (UIindex only; never solver algorithm i]] - rationale - django_apps/asteroid_lab/services/solver_run_fast_cache.py
- [[Orchestrate lab solver run rows and default replay scaffolding.  Creating ``Re]] - rationale - django_apps/asteroid_lab/services/experiment_service.py
- [[ReplayTrackRefDTO]] - code - django_apps/asteroid_lab/services/experiment_service.py
- [[SolverRunDTO]] - code - django_apps/asteroid_lab/services/experiment_service.py
- [[_dict_or_empty()_1]] - code - django_apps/asteroid_lab/services/solver_run_fast_cache.py
- [[_list_or_empty()_1]] - code - django_apps/asteroid_lab/services/solver_run_fast_cache.py
- [[_solver_run_dto()]] - code - django_apps/asteroid_lab/services/experiment_service.py
- [[create_or_replace_solver_run()]] - code - django_apps/asteroid_lab/services/experiment_service.py
- [[create_solver_run()]] - code - django_apps/asteroid_lab/services/experiment_service.py
- [[empty_lab_replay_manifest_summary()]] - code - django_apps/asteroid_lab/services/solver_run_fast_cache.py
- [[empty_solver_run_fast_cache_kwargs()]] - code - django_apps/asteroid_lab/services/solver_run_fast_cache.py
- [[ensure_default_replay_track()]] - code - django_apps/asteroid_lab/services/experiment_service.py
- [[experiment_service.py]] - code - django_apps/asteroid_lab/services/experiment_service.py
- [[resolve_inspection_solver_run()]] - code - django_apps/asteroid_lab/services/experiment_service.py
- [[solver_run_fast_cache.py]] - code - django_apps/asteroid_lab/services/solver_run_fast_cache.py
- [[sync_solver_run_fast_cache_from_config_json()]] - code - django_apps/asteroid_lab/services/solver_run_fast_cache.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/create_solver_run
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_SolverRun]]
- 1 edge to [[_COMMUNITY_build_initial_replay_for_map_input()]]
- 1 edge to [[_COMMUNITY_lab_page_context()]]

## Top bridge nodes
- [[resolve_inspection_solver_run()]] - degree 8, connects to 2 communities
- [[sync_solver_run_fast_cache_from_config_json()]] - degree 8, connects to 2 communities
- [[create_solver_run()]] - degree 10, connects to 1 community
- [[create_or_replace_solver_run()]] - degree 5, connects to 1 community
- [[_solver_run_dto()]] - degree 5, connects to 1 community