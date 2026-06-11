---
type: community
cohesion: 1.00
members: 2
---

# Import file registry and canonical order

**Cohesion:** 1.00 - tightly connected
**Members:** 2 nodes

## Members
- [[Import file registry and canonical order (_audit09).]] - rationale - django_apps/game_data/importers/registry.py
- [[registry.py_1]] - code - django_apps/game_data/importers/registry.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Import_file_registry_and_canonical_order
SORT file.name ASC
```
