---
type: community
cohesion: 0.33
members: 6
---

# google_social_login_enabled()

**Cohesion:** 0.33 - loosely connected
**Members:** 6 nodes

## Members
- [[Expose ``settings.DEBUG`` for templates (e.g. safe dev-only UI).]] - rationale - django_apps/web/context_processors.py
- [[Template context processors for the web app.]] - rationale - django_apps/web/context_processors.py
- [[True when Google OAuth works env id+secret (see settings) or SocialApp for SITE]] - rationale - django_apps/web/context_processors.py
- [[context_processors.py]] - code - django_apps/web/context_processors.py
- [[django_debug()]] - code - django_apps/web/context_processors.py
- [[google_social_login_enabled()]] - code - django_apps/web/context_processors.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/google_social_login_enabled
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_HttpRequest]]

## Top bridge nodes
- [[django_debug()]] - degree 3, connects to 1 community
- [[google_social_login_enabled()]] - degree 3, connects to 1 community