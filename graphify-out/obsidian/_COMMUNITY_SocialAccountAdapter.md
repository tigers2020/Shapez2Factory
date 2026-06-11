---
type: community
cohesion: 0.29
members: 7
---

# SocialAccountAdapter

**Cohesion:** 0.29 - loosely connected
**Members:** 7 nodes

## Members
- [[.pre_social_login()]] - code - django_apps/web/social_adapter.py
- [[DefaultSocialAccountAdapter]] - code
- [[SocialAccountAdapter]] - code - django_apps/web/social_adapter.py
- [[SocialLogin]] - code - django_apps/web/social_adapter.py
- [[Trusted OAuth (Google) match verified provider email to an existing user.]] - rationale - django_apps/web/social_adapter.py
- [[django-allauth socialaccount adapter (see SOCIALACCOUNT_ADAPTER in settings).]] - rationale - django_apps/web/social_adapter.py
- [[social_adapter.py]] - code - django_apps/web/social_adapter.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/SocialAccountAdapter
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_HttpRequest]]

## Top bridge nodes
- [[.pre_social_login()]] - degree 3, connects to 1 community