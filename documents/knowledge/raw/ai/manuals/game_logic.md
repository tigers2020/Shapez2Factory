# Manual: Game Logic · Fixtures

**Purpose:** Fast agent index for **in-game rates**, **throughput math**, **blueprint classification**, and **test fixtures**.  
**Not design authority** — implement from CANON specs and code cited below.

## Authority (read order)

| Priority | Source | Use for |
| --- | --- | --- |
| 1 | [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md) | Asteroid miner/pump, Space Belt/Pipe, saturation (project-verified) |
| 2 | [`documents/game_rules/README.md`](../../game_rules/README.md) | Shape ops, encoding, solver domain |
| 3 | ORM + services | Queryable mirrors (`MiningExtractionRule`, `Exterior*TransportCapacity`) |
| 4 | This file | Numbers at a glance + fixture paths |

Trust levels: [`documents/game_rules/sources_and_trust.md`](../../game_rules/sources_and_trust.md).

---

## Asteroid extraction (mini unit)

| Resource | Base rate (`mini_unit_output_per_min`) | Unit | Max extensions |
| --- | ---: | --- | ---: |
| Shape (Asteroid Miner) | **30** | shapes/min | 3 |
| Fluid (Asteroid Pump) | **300** | L/min | 3 |

Seeded in DB: `django_apps/game_data/migrations/0026_mining_extraction_rule.py`  
Service: `django_apps/game_data/services/mining_extraction_rules.py`

### Extension / `throughput_factor`

Each extension adds **+4** to the effective mini-unit count (base miner/pump counts as **4** mini units).

| Extensions | Effective mini units | `throughput_factor` | Shape output (30 base) | Fluid output (300 base) |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 4 | 4 | 120/min | 1,200 L/min |
| 1 | 8 | 8 | 240/min | 2,400 L/min |
| 2 | 12 | 12 | 360/min | 3,600 L/min |
| 3 (max) | 16 | 16 | **480/min** | **4,800 L/min** (4.8 kL/min) |

```text
effective_mini_units(n) = 4 + 4*n   # n in 0..3
output_per_min = mini_unit_output_per_min × throughput_factor
VALID_THROUGHPUT_FACTORS = {4, 8, 12, 16}
```

Gene fixtures use `throughput_factor` **4** (solo) or **8** (+1 extension): see [Gene templates](#gene-templates-miner-topology).

---

## Shape transport (tier-1, Space Belt)

| Concept | Formula | Tier-1 value |
| --- | --- | ---: |
| **Inner belt** (4 mini miners on one belt segment) | `30 × 4` | **120** shapes/min |
| **Full boosted miner line** (export to exterior) | `30 × 16` | **480** shapes/min |
| **One Space Belt lane** (at full miner) | same as line | **480** shapes/min |
| **One Space Belt building** | `480 × 12` lines | **5,760** shapes/min |
| **Saturated belt cap** (wiki-style) | `120 × 48` inner-belt equivalents | **5,760** shapes/min |
| **Saturation ratio** | 12 fully boosted miners (×16) = 1 full Space Belt | 12 : 1 |

ORM fields: `ExteriorShapeTransportCapacity` — `buildings_per_regular_belt=4`, `miner_full_output_multiplier=16`, `lanes_per_line=12`, `lines_per_space_belt=12`, `space_belt_full_belt_count=48`.  
Rates corrected in `django_apps/game_data/migrations/0029_evtc_tier1_shapez2_miner_belt_rates.py`.  
Helpers: `django_apps/game_data/services/exterior_transport_capacity.py` (`inner_belt_throughput_per_min_from_row`, `space_belt_connector_capacity_per_min_from_row`, …).

---

## Fluid transport (tier-1, Space Pipe)

| Concept | Tier-1 value |
| --- | ---: |
| Pump base | **300** L/min |
| Fully boosted platform (×16) | **4,800** L/min |
| **One Space Pipe lane** (saturated) | **28.8 kL/min** (= 28,800 L/min) |
| **Full Space Pipe** (12 lanes) | **345.6 kL/min** (= 345,600 L/min) |
| **Saturation ratio** | 72 fully boosted pumps = 1 full Space Pipe | 72 : 1 |

ORM saturated cap: `fluid_launcher_output_per_min × space_pipe_full_fluid_launcher_count` → **1,200 × 288 = 345,600** L/min (`0027_exterior_transport_capacity_tier1.py`).  
The **1,200** row is the fluid analogue of inner-belt grouping (4 × 300 L/min mini units).

Live snapshot export (`build_game_data_snapshot_payload`) uses **345,600** for fluid `per_connector_capacity_per_min` (full pipe building).  
The frozen test fixture [`tests/fixtures/asteroid_lab/game_data_snapshot_min.json`](../../../tests/fixtures/asteroid_lab/game_data_snapshot_min.json) still has fluid **7200** — tests assert that value; do not treat it as live ORM export without checking [`test_layer_02_capacity_snapshot.py`](../../../tests/unit/shapez2_factory/test_layer_02_capacity_snapshot.py) and CLI parity notes in `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/`.

---

## Summary cheat sheet (tier-1)

| Item | Value |
| --- | ---: |
| Shape mini (base) | 30 shapes/min |
| Fluid mini (base) | 300 L/min |
| Extension step | +4 mini units each (max ×16) |
| Inner shape belt | 120 shapes/min |
| Full boosted shape platform | 480 shapes/min |
| Full Space Belt building | 5,760 shapes/min |
| Miners per saturated belt | 12 |
| Full boosted fluid platform | 4,800 L/min |
| Full Space Pipe building | 345,600 L/min |
| Pumps per saturated pipe | 72 |

---

## Blueprint `T` → lab classification

Top-level `BP.Entries[*].T` only (nested `B.Entries` classified separately).

| Game `T` | `cell_kind` | `transport_kind` |
| --- | --- | --- |
| `SpaceBelt*` | `space_belt` | `shape_belt` |
| `SpacePipe*` | `space_pipe` | `fluid_pipe` |
| `Layout_ShapeMiner`, `Layout_ProMiner` | `shape_miner` | `shape_belt` |
| `Layout_ShapeMinerExtension` | `shape_miner_extension` | `shape_belt` |
| `Layout_FluidMiner` | `fluid_miner` | `fluid_pipe` |
| `Layout_FluidMinerExtension` | `fluid_miner_extension` | `fluid_pipe` |
| (other) | `unknown` | `none` |

Code: `src/shapez2_factory/domain/asteroid_lab/cell_classifier.py`

Extensions are removed in reconstruction and replaced with synthetic asteroid field cells (`complete_map_merge.py`).

**Connectivity (topology):** Miners may share a belt segment in series; horizontal belts/pipes allow merger/splitter hubs; **Rift / Space Lift** is 1 input / 1 output only — see [`shapez2_space_transport_connectivity.md`](../../game_rules/shapez2_space_transport_connectivity.md).

---

## Shape algebra (factory solver)

| Topic | Document |
| --- | --- |
| Layer/quadrant encoding (project SW→NW→NE→SE) | [`shape_encoding.md`](../../game_rules/shape_encoding.md) |
| Cutter, stacker, rotater, painter, swapper, pin | [`documents/game_rules/README.md`](../../game_rules/README.md) index |
| `shapez_core` types | [`solver_domain_model.md`](../../game_rules/solver_domain_model.md) |
| Solver manual (paths, no web import) | [`solver.md`](solver.md) |

---

## Fixtures

### `tests/fixtures/asteroid_lab/`

| File | Role |
| --- | --- |
| `game_data_snapshot_min.json` | Frozen `game_data_snapshot_v1`: shape connector **5760**, mining rules **30** / **300**, `throughput_factor` gene support |
| `gene_templates/minimal_extractor_e.json` | Solo miner E, `throughput_factor`: **4** |
| `gene_templates/ext1_n.json` | Miner + N extension, `throughput_factor`: **8** |
| `gene_templates/ext1_w.json` | Miner + W extension, `throughput_factor`: **8** |
| `reconstruction_complete_solved.txt` | Reconstruction-complete map golden |
| `reconstruction_required_.txt` | Map needing reconstruction |
| `test_map.txt` | General lab map |
| `golden_map_origin.txt`, `golden_map_result.txt` | Layer golden map I/O |
| `miner_extension_column_dup_cleanup.txt` | Extension column duplicate cleanup regression |
| `connected_branch_fluid_pipe.txt`, `spread_branch_fluid_pipe_bug.txt` | Fluid pipe branch cases |
| `regression_narrow_external_channels.txt` | Narrow external channel regression |
| `macro_e2e_copy.code` | Macro E2E copy-paste code |

### `tests/fixtures/pass12_telemetry_trace_pack/`

NDJSON traces + striped greenfield BPs for Pass-12 telemetry (shape/fluid/unknown mixes).

### `tests/fixtures/game_data/`

| File | Role |
| --- | --- |
| `simulation_systems_min.json` | Minimal simulation systems slice |

### `tests/fixtures/recipe_connection_rule_scenarios.json`

Recipe connection rule scenarios (shapez_solver).

### `tests/fixtures/layer04/`

| File | Role |
| --- | --- |
| `run286_strip_probes.json` | Layer 04 strip probe data |

### Code-backed layer/replay fixtures

Under `tests/unit/asteroid_lab/layers/fixtures/` and `tests/unit/asteroid_lab/replay/fixtures/` (Python factories, not static JSON).

---

## Code pointers (no magic numbers in app layer)

| Concern | Module |
| --- | --- |
| Mining rates + extension math | `django_apps/game_data/services/mining_extraction_rules.py` |
| EVTC belt/pipe caps | `django_apps/game_data/services/exterior_transport_capacity.py` |
| Snapshot export | `django_apps/game_data/services/game_data_snapshot_export.py` |
| CLI / no-DB adapter | `src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py` |
| Layer 02 capacity | `src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/` |

Tests that guard against hard-coded caps in Layer 02: `tests/unit/asteroid_lab/layers/test_layer_02_evtc_no_literals.py`.

---

## Related specs

- EVTC contract: `docs/superpowers/specs/2026-05-26-rttp-external-void-transport-capacity-contract.md`
- Asteroid pattern library (`throughput_factor` genes): `documents/Algorithm/asteroid_lab_02_pattern_library.md`
- Asteroid lab invariants: `.cursor/rules/asteroid-lab-invariants.mdc`
