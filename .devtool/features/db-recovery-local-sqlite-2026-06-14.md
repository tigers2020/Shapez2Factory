---
title: DB recovery (local SQLite)
status: done
modified: 2026-06-14
---

## Scope

Restore local `db.sqlite3` after file loss (`DJANGO_USE_SQLITE=1`).

## Acceptance

- [x] Migrations applied
- [x] game_data imported and verify OK
- [x] API smoke (health + shape-preview)

## Progress

- 2026-06-14: Restored Tier A bundle + Tier B dump paths from git `01ef3060`. Fresh migrate + `import_game_data`. User project rows (asteroid_lab) empty — not in game_data bundle.
