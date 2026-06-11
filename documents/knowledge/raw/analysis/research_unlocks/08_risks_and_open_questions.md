# Risks and Open Questions — `research_unlocks.json`

## Uncertain meaning

| Item | Risk |
| ---- | ---- |
| `Rewards[].$type` variants | Partial enum coverage |
| Upgrade key → building unlock | No explicit FK in JSON |
| `progression_layout` completeness vs 436 rows | Duplication / drift between layout and snapshots |

## Human review

| Question |
| -------- |
| Collapse level + UpgradeId duplicate `stable_id` rows in audit only? |
| Import full layout or snapshots as source of truth? |
| Map `SG_*` keys to `building_groups` manually? |

## Runtime traps

- Django model `ResearchUnlockManager` or `GameCoreResearchResearchUpgradeId`
- Using `stable_id` as UNIQUE (168 failures)
- Importing `<Title>k__BackingField` instead of `Title`

## Ambiguous IDs

- **`stable_id` unreliable** — use `upgrade_key` / `node_key`
- **`Id` dict vs string** — normalize in one column

## Dynamic schema

- Large nested layout may grow per game version.

## Version drift

- Manifest hash + cross-file shape hash set.

## Missing targets

| Target | Status |
| ------ | ------ |
| `translations.json` | Empty |
| Building FK | Not in dump |
| Full reward expansion | Needs game rules doc |

## Deferred tables

| Table | Reason |
| ----- | ------ |
| `research_shop_item` | Need layout rules |
| `wiki_configuration` | Low planner priority |

## Highest risk

**`progression_layout` stored as JSONField** — defeats normalization and idempotency proofs. **Mitigation:** decompose manager layout into index/FK tables; keep snapshots as row-level source of truth for costs/rewards.
