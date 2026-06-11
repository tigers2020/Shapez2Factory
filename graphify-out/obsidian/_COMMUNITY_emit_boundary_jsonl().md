---
type: community
cohesion: 0.27
members: 11
---

# emit_boundary_jsonl()

**Cohesion:** 0.27 - loosely connected
**Members:** 11 nodes

## Members
- [[.emit()]] - code - django_apps/asteroid_lab/observability/boundary_jsonl.py
- [[Append-only JSONL logs at data transformation boundaries (no stdlib logging  no]] - rationale - django_apps/asteroid_lab/observability/boundary_jsonl.py
- [[BoundaryJsonlSink]] - code - django_apps/asteroid_lab/observability/boundary_jsonl.py
- [[Django boundary sink adapter — forwards core payloads to func`emit_boundary_js]] - rationale - django_apps/asteroid_lab/observability/boundary_jsonl.py
- [[Write one JSON object as a single line to ``{dir}{run_id}.jsonl``.]] - rationale - django_apps/asteroid_lab/observability/boundary_jsonl.py
- [[_repo_base_dir()]] - code - django_apps/asteroid_lab/observability/boundary_jsonl.py
- [[_sanitize_run_id()]] - code - django_apps/asteroid_lab/observability/boundary_jsonl.py
- [[boundary_jsonl.py]] - code - django_apps/asteroid_lab/observability/boundary_jsonl.py
- [[boundary_jsonl_dir()]] - code - django_apps/asteroid_lab/observability/boundary_jsonl.py
- [[boundary_jsonl_enabled()]] - code - django_apps/asteroid_lab/observability/boundary_jsonl.py
- [[emit_boundary_jsonl()]] - code - django_apps/asteroid_lab/observability/boundary_jsonl.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/emit_boundary_jsonl
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_Path]]
- 2 edges to [[_COMMUNITY_AsteroidMapInput]]

## Top bridge nodes
- [[emit_boundary_jsonl()]] - degree 9, connects to 2 communities
- [[boundary_jsonl_dir()]] - degree 4, connects to 1 community
- [[_repo_base_dir()]] - degree 3, connects to 1 community
- [[.emit()]] - degree 3, connects to 1 community