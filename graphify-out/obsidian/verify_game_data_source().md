---
source_file: "django_apps/game_data/services/import_verify.py"
type: "code"
community: "verify_game_data_source()"
location: "L15"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/verify_game_data_source
---

# verify_game_data_source()

## Connections
- [[.handle()_6]] - `calls` [INFERRED]
- [[Ensure ``manifest.json`` hash matches the latest ``ImportBatch`` and artifacts a]] - `rationale_for` [EXTRACTED]
- [[GameDataVerifyError]] - `calls` [EXTRACTED]
- [[ImportBatch]] - `references` [EXTRACTED]
- [[Path]] - `references` [EXTRACTED]
- [[import_verify.py]] - `contains` [EXTRACTED]
- [[sha256_file()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/verify_game_data_source