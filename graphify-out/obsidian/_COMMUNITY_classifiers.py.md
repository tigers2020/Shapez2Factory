---
type: community
cohesion: 0.33
members: 6
---

# classifiers.py

**Cohesion:** 0.33 - loosely connected
**Members:** 6 nodes

## Members
- [[Extract short kind from CLR generic string without using it as canonical_id.]] - rationale - django_apps/game_data/services/classifiers.py
- [[Map dump source_type_name strings to domain element kinds.]] - rationale - django_apps/game_data/services/classifiers.py
- [[classifiers.py]] - code - django_apps/game_data/services/classifiers.py
- [[simulation_kind_key()]] - code - django_apps/game_data/services/classifiers.py
- [[toolbar_element_kind()]] - code - django_apps/game_data/services/classifiers.py
- [[transport_category()]] - code - django_apps/game_data/services/classifiers.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/classifierspy
SORT file.name ASC
```
