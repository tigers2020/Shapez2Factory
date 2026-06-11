---
type: community
cohesion: 0.24
members: 16
---

# read_verified_artifact_manifest()

**Cohesion:** 0.24 - loosely connected
**Members:** 16 nodes

## Members
- [[ArtifactManifestReadError]] - code - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[ArtifactManifestRecord_1]] - code - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[Django-side manifest DTO that intentionally avoids core imports.]] - rationale - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[Parse manifest payload with fail-closed schema and lifecycle checks.]] - rationale - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[Plain JSON artifact manifest reader for Django-side ingest.]] - rationale - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[Raised when a finalized artifact manifest is missing or invalid.]] - rationale - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[Read ``manifest.json`` from a finalized artifact directory.]] - rationale - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[Read a manifest and verify all declared payload hashes.]] - rationale - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[Validate every declared payload hash and reject missing payload files.]] - rationale - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[_object_payload()]] - code - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[_string_payload()]] - code - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[artifact_manifest_reader.py]] - code - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[parse_artifact_manifest_payload()]] - code - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[read_artifact_manifest()]] - code - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[read_verified_artifact_manifest()]] - code - django_apps/asteroid_lab/services/artifact_manifest_reader.py
- [[verify_manifest_content_hashes()]] - code - django_apps/asteroid_lab/services/artifact_manifest_reader.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/read_verified_artifact_manifest
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_Any]]
- 3 edges to [[_COMMUNITY_Path]]
- 2 edges to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]
- 2 edges to [[_COMMUNITY_SolverRun]]
- 1 edge to [[_COMMUNITY_Exception]]
- 1 edge to [[_COMMUNITY_ingest_artifact_for_project()]]

## Top bridge nodes
- [[read_verified_artifact_manifest()]] - degree 11, connects to 4 communities
- [[ArtifactManifestReadError]] - degree 8, connects to 1 community
- [[parse_artifact_manifest_payload()]] - degree 8, connects to 1 community
- [[read_artifact_manifest()]] - degree 7, connects to 1 community
- [[verify_manifest_content_hashes()]] - degree 6, connects to 1 community