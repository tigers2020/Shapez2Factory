# Game data import boundary — implementation plan

**Thread:** `game-data-import-boundary`  
**Approved:** 2026-06-14  
**Spec:** [spec.md](./spec.md)

## Steps

- [x] 1. Add `django_apps/game_data/services/bundle_gate.py`
- [x] 2. Delegate `tests/unit/game_data/dump_paths.py` to production resolver
- [x] 3. Wire `import_game_data` command (auto-resolve, gate before import)
- [x] 4. Refactor `verify_game_data_source` to call gate first
- [x] 5. Refactor `GameDataImporter` to accept `GameDataBundle`
- [x] 6. Add `tests/unit/game_data/test_bundle_gate.py`

## Stop conditions

- Gate blocks loaddata Tier B fixtures → gate is import-only; loaddata unchanged
- Importer phase moves beyond `_load_manifest` → stop

## Validation evidence

Recorded in kanban Progress (`.devtool/features/codebase-architecture-review-2026-06-14.md`). As-built map: [report.md](./report.md) § Implementation status.
