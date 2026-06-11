---
type: community
cohesion: 0.11
members: 23
---

# replay_service.py

**Cohesion:** 0.11 - loosely connected
**Members:** 23 nodes

## Members
- [[.next_frame_index()]] - code - django_apps/asteroid_lab/services/replay_recorder.py
- [[Append one ``ReplayFrame`` with strictly monotonic ``frame_index``.      Store]] - rationale - django_apps/asteroid_lab/services/replay_service.py
- [[JSON-serializable legacy Lab ORM frame (cell lookup API only; not timeline sourc]] - rationale - django_apps/web/services/asteroid_lab_page_context.py
- [[Next ``frame_index`` that func`append_replay_frame` would assign (read-only or]] - rationale - django_apps/asteroid_lab/services/replay_service.py
- [[PlaybackPatchDTO]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[PlaybackSessionDTO]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[Replay timeline persistence.  Architectural rule ``ReplayFrame``  ``Repl]] - rationale - django_apps/asteroid_lab/services/replay_service.py
- [[ReplayFrame_1]] - code - django_apps/web/services/asteroid_lab_page_context.py
- [[ReplayFrameDTO]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[ReplayFrameRowDTO]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[ReplayTrackPayloadDTO]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[Return ordered frames including ``metric_snapshot_json`` overlays (UI only).]] - rationale - django_apps/asteroid_lab/services/replay_service.py
- [[UIPlaybackSession_1]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[Upsert ``UIPlaybackSession`` for the track (transport UI state only).      ``U]] - rationale - django_apps/asteroid_lab/services/replay_service.py
- [[_frame_row()]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[_next_frame_index()]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[_session_dto()]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[append_replay_frame()]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[get_replay_track_payload()]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[next_replay_frame_index()]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[replay_service.py]] - code - django_apps/asteroid_lab/services/replay_service.py
- [[serialize_replay_frame()]] - code - django_apps/web/services/asteroid_lab_page_context.py
- [[update_playback_session()]] - code - django_apps/asteroid_lab/services/replay_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/replay_servicepy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_build_lab_replay_frames_for_project()]]
- 2 edges to [[_COMMUNITY_ReplayRecorder]]
- 1 edge to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_lab_timeline_adapter.py]]
- 1 edge to [[_COMMUNITY_lab_page_context()]]
- 1 edge to [[_COMMUNITY__run_solver_post_traced()]]

## Top bridge nodes
- [[serialize_replay_frame()]] - degree 5, connects to 3 communities
- [[ReplayFrameRowDTO]] - degree 4, connects to 2 communities
- [[append_replay_frame()]] - degree 7, connects to 1 community
- [[ReplayFrame_1]] - degree 3, connects to 1 community
- [[.next_frame_index()]] - degree 2, connects to 1 community