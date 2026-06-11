---
type: community
cohesion: 0.15
members: 21
---

# ingest_artifact_for_project()

**Cohesion:** 0.15 - loosely connected
**Members:** 21 nodes

## Members
- [[ArtifactIngestError]] - code - django_apps/asteroid_lab/services/artifact_ingest.py
- [[ArtifactIngestOptions]] - code - django_apps/asteroid_lab/services/artifact_ingest.py
- [[ArtifactIngestResult]] - code - django_apps/asteroid_lab/services/artifact_ingest.py
- [[ArtifactReplayLoadError]] - code - django_apps/asteroid_lab/services/artifact_replay_loader.py
- [[Compose artifact replay for lazy SSR preview (non-fatal on failure).]] - rationale - django_apps/asteroid_lab/services/artifact_ingest.py
- [[Ingest finalized CLI artifacts into Django indexcache rows.]] - rationale - django_apps/asteroid_lab/services/artifact_ingest.py
- [[Per-caller ingest behavior. Status reconcile uses the fast path.]] - rationale - django_apps/asteroid_lab/services/artifact_ingest.py
- [[Raised when an artifact replay JSONL stream is malformed.]] - rationale - django_apps/asteroid_lab/services/artifact_replay_loader.py
- [[Raised when artifact ingest must fail closed.]] - rationale - django_apps/asteroid_lab/services/artifact_ingest.py
- [[SolverRun row and manifest indexed from a finalized artifact.]] - rationale - django_apps/asteroid_lab/services/artifact_ingest.py
- [[Streaming loader for artifact ``replay_core.jsonl`` files.]] - rationale - django_apps/asteroid_lab/services/artifact_replay_loader.py
- [[Verify a finalized artifact and write indexcache fields only.]] - rationale - django_apps/asteroid_lab/services/artifact_ingest.py
- [[Yield replay frame records line-by-line without materializing the JSONL file.]] - rationale - django_apps/asteroid_lab/services/artifact_replay_loader.py
- [[_dict_json_file()]] - code - django_apps/asteroid_lab/services/artifact_ingest.py
- [[_lab_replay_manifest_summary()]] - code - django_apps/asteroid_lab/services/artifact_ingest.py
- [[_manifest_path()]] - code - django_apps/asteroid_lab/services/artifact_ingest.py
- [[_warm_lab_replay_cache_after_artifact_ingest()]] - code - django_apps/asteroid_lab/services/artifact_ingest.py
- [[artifact_ingest.py]] - code - django_apps/asteroid_lab/services/artifact_ingest.py
- [[artifact_replay_loader.py]] - code - django_apps/asteroid_lab/services/artifact_replay_loader.py
- [[ingest_artifact_for_project()]] - code - django_apps/asteroid_lab/services/artifact_ingest.py
- [[iter_replay_core_frames()]] - code - django_apps/asteroid_lab/services/artifact_replay_loader.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ingest_artifact_for_project
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_Path]]
- 4 edges to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]
- 3 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_Exception]]
- 2 edges to [[_COMMUNITY_lab_page_context()]]
- 1 edge to [[_COMMUNITY_build_lab_replay_frames_for_project()]]
- 1 edge to [[_COMMUNITY_read_verified_artifact_manifest()]]
- 1 edge to [[_COMMUNITY_entry_result_to_json_dict()]]
- 1 edge to [[_COMMUNITY_SolverRun]]

## Top bridge nodes
- [[ingest_artifact_for_project()]] - degree 13, connects to 4 communities
- [[_lab_replay_manifest_summary()]] - degree 7, connects to 3 communities
- [[_warm_lab_replay_cache_after_artifact_ingest()]] - degree 7, connects to 3 communities
- [[iter_replay_core_frames()]] - degree 7, connects to 3 communities
- [[_manifest_path()]] - degree 6, connects to 2 communities