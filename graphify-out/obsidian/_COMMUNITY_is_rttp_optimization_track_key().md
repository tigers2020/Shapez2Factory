---
type: community
cohesion: 0.50
members: 4
---

# is_rttp_optimization_track_key()

**Cohesion:** 0.50 - moderately connected
**Members:** 4 nodes

## Members
- [[Replay track key conventions (Lab UI excludes legacy RTTP artifact tracks).]] - rationale - django_apps/asteroid_lab/replay/replay_track_keys.py
- [[True for RTTP-only tracks (legacy ``rttp-{run}`` and ``{run}rttp``).]] - rationale - django_apps/asteroid_lab/replay/replay_track_keys.py
- [[is_rttp_optimization_track_key()]] - code - django_apps/asteroid_lab/replay/replay_track_keys.py
- [[replay_track_keys.py]] - code - django_apps/asteroid_lab/replay/replay_track_keys.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/is_rttp_optimization_track_key
SORT file.name ASC
```
