# Extraction Rate Authority Audit

**Date:** 2026-05-24  
**Owner:** game_data + asteroid_lab  
**Related spec:** [`docs/superpowers/specs/2026-05-24-mining-extraction-rule-design.md`](../../docs/superpowers/specs/2026-05-24-mining-extraction-rule-design.md)

---

## Executive summary

`game_data` import reflects **runtime reflection** (`source_method: runtime_reflection`; export warnings include registry reflection snapshots). It is **not** a complete, queryable game-rules database for miner/pump **extraction rates**.

Queryable CANON scalars for Lab/RTTP are introduced as **`MiningExtractionRule`** (`source_kind=CANON_MANUAL`) — a deliberate **L1b mirror** of human CANON, not an imported dump value.

---

## What exists today

### Layer A — normalized ORM (live DB scan)

| Artifact | Miner/pump extraction |
|----------|------------------------|
| `BuildingVariant` | `ExtractorDefaultInternalVariant`, `PumpDefaultInternalVariant` only (2 of 131) |
| `BuildingFootprintTile` | 1 tile each for extractor/pump |
| `BuildingGroup` | `ExtractorDefaultVariant`, `PumpDefaultVariant` |
| `ToolbarTreeNode` | `ShapeMinerExtractorsGroup`, `ShapeMinerChainsGroup`, `FluidMinerExtractorsGroup`, `FluidMinerChainsGroup` |
| `TransportBuildingRegistry` | belt/pipe kinds (transport identity) |
| `FluidColor` | 9 fluid palette rows (not extraction rate) |
| Extension variants | **0** `BuildingVariant` rows with Extension/Miner names |

### Layer B — simulation import (promoted scalars)

| Artifact | Finding |
|----------|---------|
| `SimulationSystem` | 180 rows; **no** `system_family` matching Miner/Pump |
| `SimulationSystemParameterKey` | **No** Throughput/Deposit/Miner keys |
| Promoted speed keys | `BeltSpeed`, `ConveyorSpeed`, `SpaceConveyorSpeed`, `JumpSpeed` only |
| `SimulationSystemParameterKey` registry | **Path/name only — no scalar values** |
| `ExtractorDefaultInternalVariant` in paths | Present in `definition_snapshot` / `simulation_parameters` **paths** only (grep in `docs/domain/game_data_json_deep/simulation_systems_paths_agg.tsv`) |

### Layer C — code (Lab RTTP)

| Artifact | Role |
|----------|------|
| `pattern_library._THROUGHPUT_BY_EXT` | `(4, 8, 12, 16)` == `4 + 4 * extension_count` |
| `gene_template.VALID_THROUGHPUT_FACTORS` | Same set |
| `shapez2_asteroid_space_transport_throughput.md` | CANON: 30 shapes/min, 300 L/min, ×4 steps, saturation ratios |

### Layer D — reflection (evidence only)

| Artifact | Finding |
|----------|---------|
| `ClrTypeRegistryEntry` | `ShapeMinerMetadata`, `FluidMinerExtensionMetadata`, `*PlacementHelper`, … |
| `UnknownProperty` | 3759 rows; **no** miner-keyed scalar promote |
| Blueprint `Layout_ShapeMiner` | Decode path; **not** `buildingvariant.internal_name` |

---

## Authority verdict table

| Question | Verdict |
|----------|---------|
| Is `30/min` or `300 L/min` reconstructible from DB import alone? | **No** → L1 + L1b (`CANON_MANUAL`) |
| Is extension +4 / max 3 in DB variants? | **No** → L2 code topology |
| Is `throughput_factor {4,8,12,16}` conflicting with DB? | **No conflict** (no rate enum in DB) |
| Can fluid pipe capacity live on extraction rule? | **No** — pump extraction vs pipe transport are separate; pipe infinite throughput is policy/CANON narrative, not this model |
| Should `MiningExtractionRule` link `import_batch`? | **No** — avoids “dump authority” confusion |

---

## Reproducibility commands

```powershell
python manage.py shell -c "from django_apps.game_data.models import BuildingVariant, SimulationSystemParameterKey; print(list(BuildingVariant.objects.filter(internal_name__icontains='DefaultInternal').values_list('internal_name', flat=True))); print([n for n in SimulationSystemParameterKey.objects.values_list('name', flat=True) if 'Speed' in n])"
```

```powershell
rg "ExtractorDefaultInternalVariant|ShapeMinerMetadata|runtime_reflection" game_data_backup/game_data_dump.json
```

---

## Follow-up (not this audit PR)

- **PR-1:** `MiningExtractionRule` + seed migration  
- **PR-2:** RTTP `output_per_min`, dethrone `throughput_budget_satisfied := pipeline_ok`  
- **PR-3:** Lab UI + validation  
- **Deferred:** Extension as `BuildingVariant` import; deep `simulation_systems.json` scalar mining
