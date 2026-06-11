# Random Sampling — `simulation_systems.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | `0 .. 179` |
| Sample size | **3** |
| Selected indices | **`16`**, **`103`**, **`115`** |

```python
random.Random(20260521).sample(range(180), 3)  # [16, 103, 115]
```

---

## Sample A — index 16 (building splitter system stub)

```json
{
  "source_type_name": "AtomicStatefulBuildingSimulationSystem`2[[SplitterTShapeSimulation, Game.Content, …],[PrioritySplitterSimulationState, …]]",
  "display_name_key": "AtomicStatefulBuildingSimulationSystem`2",
  "definition_snapshot": { "SimulationFactory": { "…" }, "$type": "…" },
  "simulation_parameters": { "SimulationFactory": { "…" } }
}
```

**Parsed kind:** `SplitterTShapeSimulation`  
**Interest:** Typical **143-row profile** — factory-only payload; generic CLR envelope; planner cares about kind name, not generic arity-2 string.

---

## Sample B — index 103 (`SpaceConverterSystem`)

```json
{
  "source_type_name": "Game.Content.AtomicIslands.Converters.SpaceConverterSystem",
  "display_name_key": "SpaceConverterSystem",
  "definition_snapshot": {
    "IslandId": "…",
    "Config": { "…" },
    "ConnectableSimulationsByPosition": { "…" },
    "ISimulationSystem.OnSimulationCreated": "…",
    "Simulations": [ "…" ]
  },
  "simulation_parameters": { "…parallel runtime fields…" }
}
```

**Interest:** **Heavy runtime capture** (18-row class) — delegate hooks, registries, interlocks; must classify as audit/reflection, not normalized domain columns.

---

## Sample C — index 115 (island conveyor system stub)

```json
{
  "source_type_name": "AtomicStatefulIslandSimulationSystem`2[[SpaceConveyorSimulation, Game.Content, …],[SpaceConveyorSimulationState, …]]",
  "display_name_key": "AtomicStatefulIslandSimulationSystem`2",
  "definition_snapshot": { "SimulationFactory": { "…" } },
  "simulation_parameters": { "SimulationFactory": { "…" } }
}
```

**Parsed kind:** `SpaceConveyorSimulation` (38 rows in file)  
**Interest:** Transport island simulation — ties to `belts_pipes_transport.json` / wire-belt kinds by name.

---

## Additional anchor (not sampled): index 0

`TrashSimulationSystem` with `BeltSpeed` (`BuffableBeltSpeed`, `ResearchId: BeltSpeed`) and `ConnectableSimulations` (47 entries) — **global belt policy + graph**.

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| 180 unique `stable_id` | 180/180 |
| 61 parsed simulation kinds | counter on short names |
| 143 factory-only rows | minimal parameters |
| 38 MB file size | converter + connectable graphs |

## Traceability

Samples → `simulation_system_entry` + profile flag; B → audit-only path; A/C → `simulation_factory_stub`.
