---
source_file: "django_apps/game_data/services/import_guards.py"
type: "rationale"
community: "import_guards.py"
location: "L31"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/import_guardspy
---

# Run before GameDataImporter mutates the database.

## Connections
- [[assert_import_preconditions()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/import_guardspy