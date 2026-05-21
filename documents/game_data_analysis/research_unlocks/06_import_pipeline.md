# Import Pipeline — `research_unlocks.json`

**Prerequisites:** `manifest.json`; **`items.json`** imported first (shape hash validation).

## Stages (summary)

1. **Load** — UTF-8-SIG; verify manifest hash `f9f7f226…`.
2. **Validate** — 436 rows; route by `source_type_name`; reject unknown kinds.
3. **Normalize** — `Id` dict → `node_key` string; strip `k__BackingField` keys; skip duplicate backing values.
4. **Register source_object_record** per index.
5. **Sample** — seed `20260521`, indices 32, 207, 231 in audit.
6. **DTOs** — per entity kind; separate `ProgressionLayoutDTO` from manager row.
7. **Validate** — all `ShapeHash` exist in `shape_recipe`; upgrade keys unique; warn duplicate `stable_id`.
8. **Upsert** — `research_upgrade` on `upgrade_key`; milestones/quests/upgrades on `node_key`.
9. **Children** — costs, rewards, prerequisites, milestone lines (ordered indices).
10. **Layout** — import manager `progression_layout` into index tables after nodes exist.
11. **Invariants** — 168 upgrades, 13 milestones, 188 quests, 51 side upgrades, 4 mechanics; no orphan prereqs.
12. **Audit** — duplicate stable_id report, unresolved shape hashes, sample keys.

## Idempotency

Natural keys: `upgrade_key`, `node_key` per entity table. Child rows: `(parent_id, sort_order)`.

## Unknown → `unknown_property` only.
