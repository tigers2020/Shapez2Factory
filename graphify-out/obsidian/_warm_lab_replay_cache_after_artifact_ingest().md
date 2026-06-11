---
source_file: "django_apps/asteroid_lab/services/artifact_ingest.py"
type: "code"
community: "ingest_artifact_for_project()"
location: "L117"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/ingest_artifact_for_project
---

# _warm_lab_replay_cache_after_artifact_ingest()

## Connections
- [[Compose artifact replay for lazy SSR preview (non-fatal on failure).]] - `rationale_for` [EXTRACTED]
- [[artifact_ingest.py]] - `contains` [EXTRACTED]
- [[build_lab_replay_frames_for_project()]] - `calls` [INFERRED]
- [[ingest_artifact_for_project()]] - `calls` [EXTRACTED]
- [[lab_replay_frames_are_renderable()]] - `calls` [INFERRED]
- [[persist_composed_replay_for_run_id()]] - `calls` [INFERRED]
- [[replay_compose_cache_enabled()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/ingest_artifact_for_project