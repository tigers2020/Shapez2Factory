---
type: community
cohesion: 0.29
members: 7
---

# solver_runtime_types.py

**Cohesion:** 0.29 - loosely connected
**Members:** 7 nodes

## Members
- [[Result of enqueueing a detached subprocess run (HTTP 202).]] - rationale - django_apps/asteroid_lab/services/solver_runtime_types.py
- [[Shared solver runtime entry DTOs (no service imports).]] - rationale - django_apps/asteroid_lab/services/solver_runtime_types.py
- [[SolverEnqueueResult_1]] - code - django_apps/asteroid_lab/services/solver_runtime_types.py
- [[SolverRuntimeEntryErrorCode]] - code - django_apps/asteroid_lab/services/solver_runtime_types.py
- [[SolverRuntimeEntryResult_1]] - code - django_apps/asteroid_lab/services/solver_runtime_types.py
- [[Structured failure codes for solver runtime entry (no free-form strings).]] - rationale - django_apps/asteroid_lab/services/solver_runtime_types.py
- [[solver_runtime_types.py]] - code - django_apps/asteroid_lab/services/solver_runtime_types.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/solver_runtime_typespy
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_Enum]]
- 1 edge to [[_COMMUNITY_entry_result_to_json_dict()]]

## Top bridge nodes
- [[solver_runtime_types.py]] - degree 6, connects to 2 communities
- [[SolverRuntimeEntryErrorCode]] - degree 3, connects to 1 community