---
type: community
cohesion: 0.33
members: 7
---

# .__call__()

**Cohesion:** 0.33 - loosely connected
**Members:** 7 nodes

## Members
- [[.__call__()]] - code - django_apps/web/middleware/request_id.py
- [[.__init__()_7]] - code - django_apps/web/middleware/request_id.py
- [[Assign a local request_id per HTTP request; echo on response header.]] - rationale - django_apps/web/middleware/request_id.py
- [[HTTP request correlation ID for ambient structured logging.]] - rationale - django_apps/web/middleware/request_id.py
- [[RequestIdMiddleware]] - code - django_apps/web/middleware/request_id.py
- [[_generate_request_id()]] - code - django_apps/web/middleware/request_id.py
- [[request_id.py]] - code - django_apps/web/middleware/request_id.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/__call__
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_HttpRequest]]
- 2 edges to [[_COMMUNITY_public_pages.py]]

## Top bridge nodes
- [[.__call__()]] - degree 4, connects to 2 communities
- [[.__init__()_7]] - degree 3, connects to 2 communities