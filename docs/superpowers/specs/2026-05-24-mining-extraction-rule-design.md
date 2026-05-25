# Mining Extraction Rule — Design Spec

**Date:** 2026-05-24  
**Status:** Approved (brainstorming closure)  
**PR-1:** `rttp-mining-extraction-rule-pr1` — model, seed, helper, docs (no RTTP wire)  
**PR-2:** RTTP read path (`output_per_min`, solver_summary, capacity placeholders)  
**PR-3:** UI + validation split (route vs rate)

**Audit (authority evidence):** [`documents/game_data/extraction_rate_authority_audit.md`](../../../documents/game_data/extraction_rate_authority_audit.md)

---

## Problem

Lab/RTTP need **queryable** shape/fluid extraction scalars. `game_data` import is **runtime reflection** (not full game-rules SoT). Today:

- `throughput_factor` `{4,8,12,16}` lives in code only.
- `30 shapes/min`, `300 L/min` live in CANON markdown only.
- `capacity_goals` / `throughput_budget_satisfied` can alias `pipeline_ok` without rate truth.

## Authority ladder (fixed)

| Tier | Source | Role |
|------|--------|------|
| L1 | `documents/game_rules/shapez2_asteroid_space_transport_throughput.md` | Human CANON narrative |
| L1b | `game_data.MiningExtractionRule` (`source_kind=CANON_MANUAL`) | Queryable CANON mirror |
| L2 | `gene_template` / `pattern_library` | Topology; `throughput_factor == effective_mini_units` |
| L3 | Imported geometry (`BuildingVariant`, `TransportBuildingRegistry`, …) | Identity / footprint |
| L4 | Promoted simulation speeds (`BeltSpeed`, …) | Transport belt scalars only |
| L5 | CLR / `definition_snapshot` paths | Evidence only — not algorithm input |

## Forbidden

- `import_batch` FK on `MiningExtractionRule`
- `fluid_pipe_capacity_per_min` (or any pipe transport capacity on this model)
- Fixture-based seed (use data migration)
- Treating CLR type names as domain entities
- Implying values came from `game_data_dump.json` import

## Model: `MiningExtractionRule`

Location: `django_apps/game_data/models/mining.py`

| Field | Shape row | Fluid row |
|-------|-----------|-----------|
| `resource_kind` | `shape` | `fluid` |
| `transport_kind` | `shape_belt` | `fluid_pipe` |
| `mini_unit_output_per_min` | `30` | `300` |
| `output_unit` | `shapes_per_min` | `liters_per_min` |
| `base_mini_units_per_miner` | 4 | 4 |
| `mini_units_per_extension` | 4 | 4 |
| `max_extension_count` | 3 | 3 |
| `source_kind` | `CANON_MANUAL` | `CANON_MANUAL` |

**Constraint:** one active row per `resource_kind`:

```python
UniqueConstraint(
    fields=["resource_kind"],
    condition=Q(is_active=True),
    name="unique_active_mining_extraction_rule_per_resource",
)
```

**Max output (derived, not stored):**

```text
effective_mini_units(n) = base_mini_units + mini_units_per_extension * n   # n in 0..3
max_output = mini_unit_output_per_min * effective_mini_units(max_extension_count)
shape → 480 shapes/min; fluid → 4800 L/min
```

## Service: `mining_extraction_rules.py`

Pure functions (no RTTP imports in PR-1):

- `get_active_rule(resource_kind) -> MiningExtractionRule`
- `effective_mini_units(extension_count: int) -> int`
- `output_per_min(rule, throughput_factor: int) -> Decimal`
- `max_output_per_miner(rule) -> Decimal`
- `assert_throughput_factor_matches_extensions(factor, extension_count) -> None`

`throughput_factor` must be one of `{4,8,12,16}` and equal to `effective_mini_units(extension_count)`.

## PR scope split

| PR | Delivers |
|----|----------|
| PR-1 | Model, migration+seed, helper, tests, audit, this spec, admin read-only |
| PR-2a | Reconstruction max throughput → `solver_summary.reconstruction_capacity` → Lab UI ([spec](2026-05-24-reconstruction-max-throughput-pr2a-design.md)) |
| PR-2b | `actual_committed_output_per_min` from committed candidates |
| PR-2c | Real `throughput_budget_satisfied`; demote `pipeline_ok` placeholder flags |
| PR-3 | Lab expected/actual output polish; validation split |

## Out of scope (PR-1)

- Extension `BuildingVariant` import
- `simulation_systems` miner rate promote
- Replay overlay / `capacity_goals` formula change
- `BuildingCatalogSlice` changes
