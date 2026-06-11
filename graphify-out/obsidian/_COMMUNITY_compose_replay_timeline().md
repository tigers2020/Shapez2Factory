---
type: community
cohesion: 0.40
members: 6
---

# compose_replay_timeline()

**Cohesion:** 0.40 - moderately connected
**Members:** 6 nodes

## Members
- [[Assign global ``frame_index`` 0..n-1; truncate when over max_frames.      Wh]] - rationale - django_apps/asteroid_lab/replay/timeline_composer.py
- [[Merge Lab and runtime frames into one product replay timeline (Phase 9D).]] - rationale - django_apps/asteroid_lab/replay/timeline_composer.py
- [[Retain required keyframes + tail frames within cap slots.      Strategy]] - rationale - django_apps/asteroid_lab/replay/timeline_composer.py
- [[_retain_keyframes_and_tail()]] - code - django_apps/asteroid_lab/replay/timeline_composer.py
- [[compose_replay_timeline()]] - code - django_apps/asteroid_lab/replay/timeline_composer.py
- [[timeline_composer.py]] - code - django_apps/asteroid_lab/replay/timeline_composer.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/compose_replay_timeline
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_timeline_serialization.py]]
- 1 edge to [[_COMMUNITY_build_lab_replay_frames_for_project()]]

## Top bridge nodes
- [[compose_replay_timeline()]] - degree 5, connects to 2 communities
- [[_retain_keyframes_and_tail()]] - degree 4, connects to 1 community