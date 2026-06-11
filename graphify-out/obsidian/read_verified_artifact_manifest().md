---
source_file: "django_apps/asteroid_lab/services/artifact_manifest_reader.py"
type: "code"
community: "read_verified_artifact_manifest()"
location: "L130"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/read_verified_artifact_manifest
---

# read_verified_artifact_manifest()

## Connections
- [[ArtifactManifestRecord_1]] - `references` [EXTRACTED]
- [[Path]] - `references` [EXTRACTED]
- [[Read a manifest and verify all declared payload hashes.]] - `rationale_for` [EXTRACTED]
- [[_attempt_artifact_ingest()]] - `calls` [INFERRED]
- [[artifact_manifest_reader.py]] - `contains` [EXTRACTED]
- [[build_solver_runtime_replay_frames_from_artifact_run()]] - `calls` [INFERRED]
- [[compose_lab_replay_frames_from_artifact_run()]] - `calls` [INFERRED]
- [[ingest_artifact_for_project()]] - `calls` [INFERRED]
- [[read_artifact_manifest()]] - `calls` [EXTRACTED]
- [[reconcile_solver_run()]] - `calls` [INFERRED]
- [[verify_manifest_content_hashes()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/read_verified_artifact_manifest