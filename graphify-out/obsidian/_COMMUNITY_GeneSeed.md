---
type: community
cohesion: 0.33
members: 6
---

# GeneSeed

**Cohesion:** 0.33 - loosely connected
**Members:** 6 nodes

## Members
- [[.__str__()_14]] - code - django_apps/asteroid_lab/models.py
- [[.clean()]] - code - django_apps/asteroid_lab/models.py
- [[.save()]] - code - django_apps/asteroid_lab/models.py
- [[Ensure ``decoded_json`` is populated even when ``save()`` is called outside Mode]] - rationale - django_apps/asteroid_lab/models.py
- [[Gene seed (canonical DB source for L3 genes) copy code decodes into ``decoded_j]] - rationale - django_apps/asteroid_lab/models.py
- [[GeneSeed_1]] - code - django_apps/asteroid_lab/models.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/GeneSeed
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_models.py]]
- 1 edge to [[_COMMUNITY_decode_copy_string()]]
- 1 edge to [[_COMMUNITY_normalize_decoded_blueprint()]]
- 1 edge to [[_COMMUNITY_build_decoded_blueprint_snapshot()]]

## Top bridge nodes
- [[.clean()]] - degree 4, connects to 3 communities
- [[GeneSeed_1]] - degree 5, connects to 1 community