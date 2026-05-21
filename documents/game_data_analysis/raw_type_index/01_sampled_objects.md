# Random Sampling — `raw_type_index.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Indices `0 .. 6496` |
| Sample size | **3** |
| Method | `random.Random(20260521).sample(range(6497), 3)` |
| Selected indices | **`524`**, **`3325`**, **`3710`** |

---

## Sample A — index 524 (`ShapeOperationPaintPayload`)

```json
{
  "stable_id": "904222d4da6e0b7ee2ca6e2d308bf4fbe51d94efe012ef196271b7ecaa8c2507",
  "source_type_name": "ShapeOperationPaintPayload",
  "source_guid": "",
  "source_path": "",
  "display_name_key": "",
  "type_name": "ShapeOperationPaintPayload",
  "assembly_name": "Game.Content.Features"
}
```

**Interest:** Domain-adjacent content type in `Game.Content.Features`; links shape paint operations to items/shapes dumps.

---

## Sample B — index 3325 (`HUDDebugStats+<>c__DisplayClass5_0`)

```json
{
  "stable_id": "1dae5072ee3caf5808a482b2a7147cfa10f442768fcbf8df7961a11adf2ea64a",
  "source_type_name": "HUDDebugStats+<>c__DisplayClass5_0",
  "source_guid": "",
  "source_path": "",
  "display_name_key": "",
  "type_name": "HUDDebugStats+<>c__DisplayClass5_0",
  "assembly_name": "SPZGameAssembly"
}
```

**Interest:** Compiler-generated closure type — **runtime/reflection noise**; should not drive planner models.

---

## Sample C — index 3710 (`SpaceConveyorSimulationRenderer`)

```json
{
  "stable_id": "848960e19026558a42e2c8e64d4872371d0632ac34a8a83e370bbccefbe995ba",
  "source_type_name": "SpaceConveyorSimulationRenderer",
  "source_guid": "",
  "source_path": "",
  "display_name_key": "",
  "type_name": "SpaceConveyorSimulationRenderer",
  "assembly_name": "SPZGameAssembly"
}
```

**Interest:** Simulation/renderer type in main game assembly — relates to `simulation_systems.json` by name, not by `stable_id`.

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| `source_type_name == type_name` | 6497/6497 |
| Empty path fields | 6497/6497 |
| UNIQUE (`type_name`, `assembly_name`) | 6497 composite |
| Duplicate `stable_id` | 114 rows / 8 hash values |
| `ShapeItem` present | maps `items.json` envelope |

## Traceability

Samples → `clr_type_registry_entry` rows; B flagged `is_compiler_generated` on import.
