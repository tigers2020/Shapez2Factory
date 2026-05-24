---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: en
dump_source: game_data_backup/game_data_dump.json
related_docs:
  - asteroid_lab_mining_installation/00_source_of_truth.md
  - asteroid_lab_mining_installation/01_rule_reconciliation.md
  - docs/domain/asteroid_game_data_snapshot.md
---

# DB Cross-Reference — Miner, Extension, Transport

Fixed import dump: **layer A** (normalized ORM) and **layer B** (reflected/semi-structured rows). When content here changes, update verdicts in [`01_rule_reconciliation.md`](01_rule_reconciliation.md).

**Command to regenerate listing:**

```powershell
rg "ShapeMiner|FluidMiner|MinerExtension|ExtractorDefault|PumpDefault" game_data_backup/game_data_dump.json
```

## Layer A — `game_data` normalized tables

| Table | Miner-related keys (this dump) | Notes |
|--------|-------------------------|------|
| `game_data.buildingvariant` | `ExtractorDefaultInternalVariant`, `PumpDefaultInternalVariant` | Only 2 internal variants in dump matching Miner/Extractor/Pump name filter |
| `game_data.buildingfootprinttile` | `variant:ExtractorDefaultInternalVariant:tile:0` (x=0,y=0); `variant:PumpDefaultInternalVariant:tile:0` (x=0,y=0) | 1 tile per variant |
| `game_data.buildingconnector` | 2 rows connected to above variants | See `canonical_id` prefix |
| `game_data.buildinggroup` | `ExtractorDefaultVariant`, `PumpDefaultVariant` | Groups containing internal variant members |
| `game_data.buildinggroupmember` | Members of above groups | 131 variant rows total in dump |
| `game_data.toolbarbuildingplacement` | Miner toolbar node reference placements | 78 total in dump |
| `game_data.toolbartreenode` | `ExtractorDefaultVariant`, `PumpDefaultVariant`, `ShapeMinerExtractorsGroup`, `ShapeMinerChainsGroup`, `FluidMinerExtractorsGroup`, `FluidMinerChainsGroup` | Island/toolbar classification |
| `game_data.toolbarelement` | Actions linked to miner nodes (hash id) | Paired with `toolbartreenode` |
| `game_data.transportbuildingregistry` | belt/pipe transport kinds (PR-1 extension) | Compare with `AsteroidGameDataSnapshot.transport_registry` |

### Blueprint `Layout_*` names vs DB

Decoded copy code uses `Layout_ShapeMiner`, `Layout_FluidMiner`, `Layout_*MinerExtension`, etc. (`django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py`). **These strings are not `buildingvariant.internal_name` rows in this dump.** Lab optimization geometry uses `GeneTemplate` + footprint import; it does not use raw `Layout_*` type strings directly.

| Surface | Identifier style | Present in this dump? |
|------|---------------|----------------|
| Blueprint decode | `Layout_ShapeMiner`, `Layout_FluidMinerExtension`, etc. | Paste/sample paths, not variant table |
| Normalized DB | `ExtractorDefaultInternalVariant`, `PumpDefaultInternalVariant`, etc. | Yes (layer A) |
| Lab code | `GeneTemplate`, `VALID_THROUGHPUT_FACTORS` | Code only (layer C) |

## Layer B — Reflected / semi-structured

| Source | Miner-related `type_name` / keys (sample) | Purpose |
|------|-----------------------------------|------|
| `game_data.unknownproperty` | `ShapeMinerMetadata`, `ShapeMinerExtensionMetadata`, `FluidMinerExtensionMetadata`, `*PlacementHelper`, `*SidePanelModuleDataProvider`, `*DynamicDrawer`, etc. | Placement/metadata reflection — not yet promoted to scalar ORM |
| `game_data.clrtyperegistryentry` | Linked to simulation CLR rows | Medium confidence; pair with `simulationsystem` audit |
| `game_data.simulationsystem` | Filter by `Miner` / `Extractor` / `Pump` entry ids | Throughput/rate paths — extend `docs/domain/game_data_json_deep/simulation_systems*` |
| Island·toolbar JSON paths | `ShapeMinerExtractorsGroup`, `FluidMinerChainsGroup`, placer stable_keys | UI placement groups |

**Throughput:** This dump's `buildingvariant` has no single `throughput_rate` column. Absolute throughput canon is [`shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md) (CANON) + `gene_template.VALID_THROUGHPUT_FACTORS` (layer C) until layer B paths are sampled into import.

## Layer C / D pointers (no duplicate narrative here)

| topic | Code | Tests |
|-------|------|--------|
| Throughput 4/8/12/16 | `django_apps/asteroid_lab/optimization/gene_template.py` | `tests/unit/asteroid_lab/test_gene_template_loader.py::test_gene_template_throughput_factor_matches_extension_count` |
| Extension 0..3 | `throughput_factor_for_extension_count()` | `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py::test_exhaustive_generator_extension_count_0_to_3` |
| rim-only anchor | `candidate_dtos.ExtractorPlacementPolicy.RIM_ONLY` | `test_candidate_generator.py::test_candidate_generator_does_not_commit_placements` |

## `01` update notes (PR-1)

| topic | normalized_db_evidence (filled) | reflected_db_evidence (filled) | Verdict notes |
|-------|------------------------------|-----------------------------|-----------|
| Extension max 0..3 | toolbar groups + 2 internal variants; blueprint `Layout_*` is separate | `*PlacementHelper`, `*ExtensionMetadata` type_name | keep; explain Layout vs DB in `04` |
| Throughput 4/8/12/16 | No dedicated rate table | `unknownproperty` sample + future `simulation_systems` audit | `needs-review` until rate linked to B path |
