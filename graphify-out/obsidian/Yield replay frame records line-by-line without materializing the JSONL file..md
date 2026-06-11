---
source_file: "django_apps/asteroid_lab/services/artifact_replay_loader.py"
type: "rationale"
community: "ingest_artifact_for_project()"
location: "L16"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/ingest_artifact_for_project
---

# Yield replay frame records line-by-line without materializing the JSONL file.

## Connections
- [[iter_replay_core_frames()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/ingest_artifact_for_project