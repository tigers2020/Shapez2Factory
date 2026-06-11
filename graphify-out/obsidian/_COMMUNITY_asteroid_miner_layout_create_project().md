---
type: community
cohesion: 0.24
members: 10
---

# asteroid_miner_layout_create_project()

**Cohesion:** 0.24 - loosely connected
**Members:** 10 nodes

## Members
- [[Create ``AsteroidProject`` + ``AsteroidMapInput`` with decoded snapshot.]] - rationale - django_apps/asteroid_lab/services/project_service.py
- [[CreateProjectFromCopyCodeResultDTO]] - code - django_apps/asteroid_lab/services/project_service.py
- [[POST copy text, dedupe by digest, build inspection replay, redirect to slug URL]] - rationale - django_apps/web/views/public_pages.py
- [[Project lifecycle for Asteroid Lab.]] - rationale - django_apps/asteroid_lab/services/project_service.py
- [[Return ``AsteroidProject.slug`` for this copy text, reusing a row with matching]] - rationale - django_apps/asteroid_lab/services/project_service.py
- [[_unique_slug_from_label()]] - code - django_apps/asteroid_lab/services/project_service.py
- [[asteroid_miner_layout_create_project()]] - code - django_apps/web/views/public_pages.py
- [[create_project_from_copy_code()]] - code - django_apps/asteroid_lab/services/project_service.py
- [[project_service.py]] - code - django_apps/asteroid_lab/services/project_service.py
- [[resolve_or_create_project_slug_for_copy_code()]] - code - django_apps/asteroid_lab/services/project_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/asteroid_miner_layout_create_project
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_AsteroidMapInput]]
- 3 edges to [[_COMMUNITY_public_pages.py]]
- 1 edge to [[_COMMUNITY_build_initial_replay_for_map_input()]]
- 1 edge to [[_COMMUNITY_HttpRequest]]

## Top bridge nodes
- [[asteroid_miner_layout_create_project()]] - degree 9, connects to 4 communities
- [[create_project_from_copy_code()]] - degree 6, connects to 1 community
- [[resolve_or_create_project_slug_for_copy_code()]] - degree 5, connects to 1 community