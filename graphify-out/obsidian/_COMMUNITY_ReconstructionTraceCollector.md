---
type: community
cohesion: 0.24
members: 10
---

# ReconstructionTraceCollector

**Cohesion:** 0.24 - loosely connected
**Members:** 10 nodes

## Members
- [[.__init__()_20]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/trace.py
- [[.append()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/trace.py
- [[.events()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/trace.py
- [[Append-only collector; optional on ``reconstruct_after_cleanup``.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/trace.py
- [[One logical trace step for replay assembly.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/trace.py
- [[Output-only reconstruction trace (never algorithm input).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/trace.py
- [[ReconstructionTraceCollector_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/trace.py
- [[ReconstructionTraceEvent_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/trace.py
- [[trace.py]] - code - django_apps/asteroid_lab/reconstruction/trace.py
- [[trace.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/trace.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ReconstructionTraceCollector
SORT file.name ASC
```
