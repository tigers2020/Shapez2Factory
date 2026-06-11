---
type: community
cohesion: 0.22
members: 15
---

# ReplayRecorder

**Cohesion:** 0.22 - loosely connected
**Members:** 15 nodes

## Members
- [[.__init__()]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[._enforce_max_frames()]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[._payload_dict()]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[._should_skip_for_policy()]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[.record_event()]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[.record_many()]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[A4 replay-first capture ``SnapshotEventDTO`` → ``ReplayFrame`` (append-only UI]] - rationale - django_apps/asteroid_lab/services/replay_recorder.py
- [[Persists class`SnapshotEventDTO` as ``ReplayFrame`` rows (output-only artifact]] - rationale - django_apps/asteroid_lab/services/replay_recorder.py
- [[Raised when ``ReplayRecordingPolicyDTO.max_frames`` would be exceeded.]] - rationale - django_apps/asteroid_lab/services/replay_recorder.py
- [[ReplayRecorder]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[ReplayRecorderCapExceeded]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[ReplayRecordingPolicyDTO]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[SnapshotEventDTO]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[SnapshotFrameDTO]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[replay_recorder.py]] - code - django_apps/asteroid_lab/services/replay_recorder.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ReplayRecorder
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 2 edges to [[_COMMUNITY_lab_timeline_adapter.py]]
- 2 edges to [[_COMMUNITY_replay_service.py]]
- 1 edge to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_ReplayEventType]]
- 1 edge to [[_COMMUNITY_Exception]]

## Top bridge nodes
- [[ReplayRecorder]] - degree 11, connects to 2 communities
- [[.record_event()]] - degree 9, connects to 2 communities
- [[SnapshotEventDTO]] - degree 7, connects to 2 communities
- [[SnapshotFrameDTO]] - degree 4, connects to 1 community
- [[ReplayRecorderCapExceeded]] - degree 4, connects to 1 community