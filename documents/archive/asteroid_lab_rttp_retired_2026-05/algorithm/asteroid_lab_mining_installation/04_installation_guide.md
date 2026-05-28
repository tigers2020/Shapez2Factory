---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: en
related_docs:
  - asteroid_lab_mining_installation/README.md
  - asteroid_lab_mining_installation/00_source_of_truth.md
  - asteroid_lab_mining_installation/03_db_cross_reference.md
  - documents/game_rules/shapez2_asteroid_space_transport_throughput.md
---

# Installation Guide — Miner, Extension (Asteroid Lab)

End-to-end narrative of **miner and extension** flow in Shapez 2 in-game rules and this Lab. For rule verdicts see [`01_rule_reconciliation.md`](01_rule_reconciliation.md); for DB facts see [`03_db_cross_reference.md`](03_db_cross_reference.md).

Phase detail contracts (RESEARCH): [`asteroid_lab_02_pattern_library.md`](../asteroid_lab_02_pattern_library.md) · [`asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md) · [`asteroid_lab_07_incremental_commit.md`](../asteroid_lab_07_incremental_commit.md).

---

## Key distinction (Lab)

> **In Lab, miner/extension is not installed at candidate generation time.**  
> route feasibility pass → selection → **commit-time reprobe** + reservation pass → **confirmed placement**.

| Stage | Miner/extension visible on map? | Confirmed install? |
|------|--------------------------------|---------------|
| decode / pasted blueprint | Yes (user layout) | No — input only |
| cleanup | Removed | No |
| reconstruction | mineable field only | No |
| Candidate generation + route probe | No (in-memory geometry only) | **No** |
| selection / fitness | No | No |
| incremental commit | Yes after reprobe | **Yes** |
| replay scrub | Observation | Not algorithm input |

`rim-only` / `ExtractorPlacementPolicy.RIM_ONLY` restricts **extractor anchor coordinates ∈ rim_cells** at candidate generation, not a rim-walk install order. See [`01`](01_rule_reconciliation.md) *rim-only* row.

---

## 1. In-game rules (Shapez 2)

### Miner and pump platforms

- **Shape:** Asteroid Miner sends shapes to Space Belt.
- **Fluid:** Asteroid Pump sends fluid to Space Pipe.
- **Extension chain (v0 linear):** Max **3 extensions** per extractor; each extension adds +×4 throughput multiplier (accumulated from base ×4).

| Extension count | `throughput_factor` (Lab code) |
|-----------|-------------------------------|
| 0 | 4 |
| 1 | 8 |
| 2 | 12 |
| 3 | 16 |

Absolute throughput (base 30 shapes/min, belt saturation, etc.): CANON [`shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md).

### Facing and output transport

- Extensions attach to extractor or prior extension. **parent-facing** must match game attachment rules (Lab: `ExtensionAttachment.required_facing` in [`asteroid_lab_02`](../asteroid_lab_02_pattern_library.md)).
- **Output side:** First **belt or pipe** cell immediately after extractor output is required (`GeneTemplate` `fixed_output_transport`; not included in `occupied_offsets`).
- Path search starts **after** that transport stub (`route_probe_start_offset`).

### Blueprint type names vs DB

Paste code uses `Layout_ShapeMiner`, `Layout_FluidMiner`, `Layout_*MinerExtension`. Normalized `game_data` may use names like `ExtractorDefaultInternalVariant` — [`03`](03_db_cross_reference.md) § Blueprint vs DB.

---

## 2. Lab input pipeline

Product and solver top-level flow:

```text
POST blueprint copy_code (or open project slug)
  → decode (preserve raw X/Y at boundary)
  → cleanup: remove existing miner, extension, belt/pipe (policy)
  → reconstruction: mineable asteroid field + topology
  → OptimizationInput (Server X/Y only)
  → solver runtime (candidates → selection → commit)
  → replay timeline + result layout
```

### Cleanup (why existing miners disappear)

Before optimization, existing **extractor / extension** cells are removed. Coordinates may remain as **walls/barriers** (`wall_coords`) in flood-fill. belt/pipe are stripped by cleanup policy; `wall_coords` handling may differ — [`plan_asteroid_reconstruction_topology_2026-05-16.md`](../../ai/plan_asteroid_reconstruction_topology_2026-05-16.md).

### Coordinates

After normalization, the optimization layer uses **Server X/Y only**. No raw↔server re-conversion inside candidate/commit code ([`00`](00_source_of_truth.md), [`asteroid_lab_01`](../asteroid_lab_01_optimization_input.md)).

---

## 3. Candidate generation (not installation)

**Package:** `django_apps/asteroid_lab/optimization/`

1. **GeneTemplate library** — canonical **E** local topology: extractor `(0,0)`, linear extension chain, `throughput_factor` 4/8/12/16 ([`gene_template.py`](../../../django_apps/asteroid_lab/optimization/gene_template.py)).
2. **Projection** — rotate/translate template to map rim (or policy) anchor.
3. **BundleCandidate** — occupied = extractor + extensions only; output stub and first transport cell are defined but **not committed**.
4. **Route probe (immediate)** — `run_route_probe` from `output_stub`; unreachable excluded from normal pool.

```text
Candidate generation → local geometry validation → route probe → normal pool | rejected
```

**Wrong mental model:** "The solver lays miners as it explores." In reality it **enumerates provisional bundles** and checks reachability to external `RouteGoal` only.

**Tests:** `test_candidate_generator_does_not_commit_placements`, `test_candidate_generator_reachable_only_enters_normal_pool`.

---

## 4. Selection

v0 solver may use **candidate selection** (throughput budget, scoring) and **genome / fitness** ordering — [`asteroid_lab_05_genome_fitness.md`](../asteroid_lab_05_genome_fitness.md), [`solver_runtime/README.md`](../solver_runtime/README.md).

- **Fitness / penalty** is predictive (probe-time).
- **Commit survivability** is observed at commit time — do not infer from replay ([`asteroid_lab_10`](../asteroid_lab_10_development_sequence.md) §10B).

Selection picks **which bundle to attempt commit**, not the final layout alone.

---

## 5. Confirmed installation (incremental commit)

**Package:** incremental commit + `RouteDomainSnapshotBuilder`

Order follows **`Gene.commit_order` only** — not rim scan order or candidate enumeration order ([`asteroid_lab_07`](../asteroid_lab_07_incremental_commit.md)).

Per `commit_order`:

```text
1. Rebuild route_domain snapshot (latest reservation + committed occupancy)
2. Re-run route probe (candidate-stage probe is reference only)
3. On success: reserve path, materialize equipment cells
4. On failure: rolled_back (v0: abort/rollback per implementation)
```

Principle ([`asteroid_lab_00`](../asteroid_lab_00_overview.md)):

```text
Everything is provisional until connected to the external trunk.
```

**Test canon:** `test_incremental_commit_reprobes_latest_domain`.

States (conceptual): `PROVISIONAL` → `FEASIBLE` → `ROUTED` → `CONFIRMED` | `ROLLED_BACK` — Phase 7 docs.

---

## 6. Replay (observation only)

Replay is a **single lab timeline** ([`asteroid_lab_09_replay_timeline.md`](../asteroid_lab_09_replay_timeline.md) ACTIVE). Frames are **not algorithm input** ([`asteroid_lab_00`](../asteroid_lab_00_overview.md)).

wire `event_type` (enum): `django_apps/asteroid_lab/replay/replay_enums.py` · [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md).

| phase (representative) | `ReplayEventType` (examples) | Miner/extension perspective |
|--------------|------------------------|----------------------|
| reconstruction | `reconstruction.*` | Field ready; existing miners already stripped in replay story |
| optimization | `optimization.input_loaded` | topology + goals ready |
| candidate | `candidate.generated` / `candidate.rejected` | bundle evaluation, **not installed** |
| probe | `route_probe.succeeded` / `route_probe.failed` | reachability at generation time |
| selection | `candidate_selection.completed`, `genome.evaluated` | ordering and pool stats |
| commit | `route.commit_attempted`, `route.committed`, `route.rolled_back` | **install attempt** |
| materialize | `route.materialized` | confirmed path cell record |
| end | `result.layout` | final map |

UI: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` — single scrub index; maps `event_type` to grid overlay (UI string details not duplicated here).

---

## Quick links

| Need | Document |
|------|------|
| Source-of-truth priority | [`00`](00_source_of_truth.md) |
| Rules vs DB vs code | [`01`](01_rule_reconciliation.md) |
| Existing document status | [`02`](02_doc_drift_matrix.md) |
| dump / ORM listing | [`03`](03_db_cross_reference.md) |
| Throughput CANON | [`game_rules/...throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md) |

---

## Reader self-check

After reading **this file only**, you should be able to answer:

1. Does cleanup remove miners from pasted blueprint? → **Yes**
2. Does candidate generation install miners on the map? → **No**
3. Does commit-time reprobe use the same snapshot as candidate time? → **No** (always latest `route_domain`)
4. Can replay be used as optimization input? → **No**
