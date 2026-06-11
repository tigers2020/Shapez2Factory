---
source_file: "django_apps/game_data/services/import_guards.py"
type: "code"
community: "import_guards.py"
location: "L30"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/import_guardspy
---

# assert_import_preconditions()

## Connections
- [[.run()]] - `calls` [INFERRED]
- [[Run before GameDataImporter mutates the database.]] - `rationale_for` [EXTRACTED]
- [[assert_game_data_migrations_applied()]] - `calls` [EXTRACTED]
- [[import_guards.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/import_guardspy