---
type: community
cohesion: 0.50
members: 4
---

# _related_for()

**Cohesion:** 0.50 - moderately connected
**Members:** 4 nodes

## Members
- [[AggregateRootSpec]] - code - django_apps/game_data/admin.py
- [[RelatedChangelistSpec]] - code - django_apps/game_data/admin.py
- [[_aggregate_spec()]] - code - django_apps/game_data/admin.py
- [[_related_for()]] - code - django_apps/game_data/admin.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/_related_for
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_admin.py]]

## Top bridge nodes
- [[_aggregate_spec()]] - degree 3, connects to 1 community
- [[_related_for()]] - degree 3, connects to 1 community