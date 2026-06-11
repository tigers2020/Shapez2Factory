---
source_file: "django_apps/asteroid_lab/services/artifact_manifest_reader.py"
type: "rationale"
community: "read_verified_artifact_manifest()"
location: "L114"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/read_verified_artifact_manifest
---

# Validate every declared payload hash and reject missing payload files.

## Connections
- [[verify_manifest_content_hashes()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/read_verified_artifact_manifest