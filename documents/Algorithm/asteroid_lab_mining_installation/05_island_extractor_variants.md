---
status: CANON
owner: asteroid-lab
last_reviewed: 2026-05-23
language: en
related_docs:
  - asteroid_lab_mining_installation/04_installation_guide.md
  - asteroid_lab_mining_installation/03_db_cross_reference.md
---

# Island Extractor Default Blueprints (Balance / Omni / Fluid)

Extractors pasted as Shapez 2 **Island blueprints** differ in internal `B.Entries` composition by variant. Use the **code catalog** and **DB seed** below as canon when Lab, tests, and Admin must share the same strings.

## In-game variants (summary)

| Variant | `variant_key` | Top-level `T` | Role |
|------|---------------|------------|------|
| Balance extractor | `shape_balance` | `Layout_ShapeMiner` | Evenly distributes shapes across 12 lines |
| Omni extractor | `shape_omni` | `Layout_ShapeMiner` | Restores and outputs fragment shapes to full form |
| Fluid extractor | `fluid_default` | `Layout_FluidMiner` | Pump-based fluid extraction (single version) |

Shape extractors may share the same outer `Layout_*` type but have different nested buildings. Lab `cell_classifier` only sees top-level `Layout_ShapeMiner`; distinguish balance/omni via **inner fingerprint** or game metadata.

## Code canon

| Path | Content |
|------|------|
| `django_apps/asteroid_lab/catalog/island_extractor_defaults.py` | `ISLAND_EXTRACTOR_DEFAULTS`, `SHAPEZ2-4-` copy strings, `inner_entry_fingerprint()` |
| `django_apps/asteroid_lab/catalog/__init__.py` | Public re-export |

Application code can read copy strings via `ISLAND_EXTRACTOR_DEFAULTS` / `default_record()` without DB.

## DB canon

| Model | Purpose |
|------|------|
| `asteroid_lab.IslandExtractorBlueprint` | Admin·browse·seeded copy_code + `inner_fingerprint` |

Seed (idempotent):

```powershell
python manage.py seed_island_extractor_blueprints
```

Use `--dry-run` to preview upsert targets only.

## Regression fingerprint

`inner_entry_fingerprint(copy_code)` = SHA-256 of sorted JSON of nested `B.Entries` `T` frequencies.

Tests: `tests/unit/asteroid_lab/test_island_extractor_blueprint_defaults.py`

- balance vs omni fingerprint mismatch
- balance `BeltPortSenderInternalVariant` count > omni
- fluid `PumpDefaultInternalVariant` == 16

## Blueprint vs Asteroid Lab miner

| Layer | Identification |
|------|------|
| Island paste (this doc) | `Layout_ShapeMiner` / `Layout_FluidMiner` + nested factory |
| Asteroid map optimization | `GeneTemplate`, `Layout_*MinerExtension` field tiles — [`04_installation_guide.md`](04_installation_guide.md) |

See [`03_db_cross_reference.md`](03_db_cross_reference.md) § Blueprint `Layout_*` vs DB.
