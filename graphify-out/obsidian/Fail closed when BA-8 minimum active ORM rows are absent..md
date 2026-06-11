---
source_file: "django_apps/game_data/services/game_data_snapshot_export.py"
type: "rationale"
community: "build_game_data_snapshot_payload()"
location: "L52"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/build_game_data_snapshot_payload
---

# Fail closed when BA-8 minimum active ORM rows are absent.

## Connections
- [[_assert_required_snapshot_rows()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/build_game_data_snapshot_payload