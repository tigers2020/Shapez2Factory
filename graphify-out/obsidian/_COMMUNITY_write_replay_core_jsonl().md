---
type: community
cohesion: 0.39
members: 8
---

# write_replay_core_jsonl()

**Cohesion:** 0.39 - loosely connected
**Members:** 8 nodes

## Members
- [[Core replay JSONL emitter for PR-CLI-3b artifacts.  The emitter is intentional]] - rationale - src/shapez2_factory/application/asteroid_lab/replay_core.py
- [[Raised when replay frames are missing or violate monotonic frame order.]] - rationale - src/shapez2_factory/application/asteroid_lab/replay_core.py
- [[ReplayCoreFrameOrderError]] - code - src/shapez2_factory/application/asteroid_lab/replay_core.py
- [[Write a deterministic replay-core JSONL stream.      The first line is a heade]] - rationale - src/shapez2_factory/application/asteroid_lab/replay_core.py
- [[_frame_index()]] - code - src/shapez2_factory/application/asteroid_lab/replay_core.py
- [[_write_json_line()]] - code - src/shapez2_factory/application/asteroid_lab/replay_core.py
- [[replay_core.py]] - code - src/shapez2_factory/application/asteroid_lab/replay_core.py
- [[write_replay_core_jsonl()]] - code - src/shapez2_factory/application/asteroid_lab/replay_core.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/write_replay_core_jsonl
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_shape_part_sprite_generation.py]]
- 1 edge to [[_COMMUNITY_ValueError]]
- 1 edge to [[_COMMUNITY__run_artifact()]]

## Top bridge nodes
- [[write_replay_core_jsonl()]] - degree 8, connects to 3 communities
- [[_write_json_line()]] - degree 4, connects to 2 communities
- [[ReplayCoreFrameOrderError]] - degree 5, connects to 1 community
- [[_frame_index()]] - degree 4, connects to 1 community