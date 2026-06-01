# Space Belt / Space Pipe identifiers (`documents/game_data`)

Canonical index of **island** space transport names found in the game-data JSON dump beside this file.  
Dump provenance: `manifest.json` (`game_version`: `unknown+1.0.3-rc3`, `dump_schema_version`: `1.0.0`).

## Scope

| In scope | Out of scope |
| -------- | ------------ |
| `SpaceBelt_*`, `SpacePipe_*`, `SpaceBeltsGroup`, `SpacePipesGroup`, related CLR/wiki keys in `documents/game_data/*.json` | Factory-floor belts/pipes in `belts_pipes_transport.json` (`ForwardBelt`, `PipeForward`, …) — see [`documents/game_data_analysis/belts_pipes_transport/`](../game_data_analysis/belts_pipes_transport/00_summary.md) |
| Blueprint copy field `T` (island layout type) | Project solver `cell_kind` (`space_belt`, `space_pipe`) — defined in code/canonical manuals, not in this JSON |
| Strings embedded in reflection dumps inside building JSON | Live DB rows (`django_apps/game_data`) |

**Note:** There is **no** literal `space_belt` / `space_pipe` snake_case string anywhere under `documents/game_data/`. Those names are **project domain** labels; see [Lab classification](#lab-classification-project).

---

## Layout types (`T` / island definition id)

27 shape-belt variants and 27 fluid-pipe variants. Symmetric naming: replace `SpaceBelt` ↔ `SpacePipe`.

### Straight, turn, merge/split

| Kind | `SpaceBelt_*` | `SpacePipe_*` |
| ---- | ------------- | ------------- |
| Forward | `SpaceBelt_Forward` | `SpacePipe_Forward` |
| Turn | `SpaceBelt_LeftTurn`, `SpaceBelt_RightTurn` | `SpacePipe_LeftTurn`, `SpacePipe_RightTurn` |
| Forward merge/split | `SpaceBelt_LeftFwdMerger`, `SpaceBelt_LeftFwdSplitter`, `SpaceBelt_RightFwdMerger`, `SpaceBelt_RightFwdSplitter` | same with `SpacePipe_` |
| Y | `SpaceBelt_YMerger`, `SpaceBelt_YSplitter` | `SpacePipe_YMerger`, `SpacePipe_YSplitter` |
| Triple | `SpaceBelt_TripleMerger`, `SpaceBelt_TripleSplitter` | `SpacePipe_TripleMerger`, `SpacePipe_TripleSplitter` |

### Lifts (×2 height × down/up × 4 horizontals + backward)

| Tier | Belt examples | Pipe examples |
| ---- | ------------- | ------------- |
| Lift1 down | `SpaceBelt_Lift1DownForward`, `…Left`, `…Right`, `…Backward` | `SpacePipe_Lift1Down*` (same suffixes) |
| Lift1 up | `SpaceBelt_Lift1UpForward`, … | `SpacePipe_Lift1Up*` |
| Lift2 down | `SpaceBelt_Lift2DownForward`, … | `SpacePipe_Lift2Down*` |
| Lift2 up | `SpaceBelt_Lift2UpForward`, … | `SpacePipe_Lift2Up*` |

Full flat list (54 ids): all strings matching `^Space(Belt|Pipe)_[A-Za-z0-9_]+$` in `research_unlocks.json` → `…Mode.Islands.DefinitionsById.<id>`.

---

## Groups and collections

| Identifier | Role | Primary JSON |
| ---------- | ---- | ------------ |
| `SpaceBeltsGroup` | Island toolbar / definition group (shape transport) | `research_unlocks.json`, `simulation_systems.json`, `toolbar_entries.json` |
| `SpacePipesGroup` | Island toolbar / definition group (fluid transport) | same |
| `SpaceBelts` | Ordered list of belt layout ids (27) under research island mode | `research_unlocks.json` → `…Mode.Islands.SpaceBelts` |
| `SpacePipes` | Ordered list of pipe layout ids (27) | `…Mode.Islands.SpacePipes` |

### Registry paths (`research_unlocks.json`)

Typical prefix: `[0].manager_snapshot.Mode.`

| Path suffix | Keys |
| ----------- | ---- |
| `IslandGroupDefinitionIdRegistry.GroupIdToSerialMap.<group>` | `SpaceBeltsGroup`, `SpacePipesGroup` |
| `IslandGroupDefinitionIdRegistry.GroupImplementationMap.<group>` | same |
| `IslandGroupDefinitionIdRegistry.GroupSerialToIdMap.<group>` | same |
| `Islands.DefinitionGroupsById.<group>` | same |
| `Islands.DefinitionsById.<SpaceBelt_* \| SpacePipe_*>` | all 54 layout types |
| `Islands.Groups.<group>` | group payloads |

---

## Wiki and UI text keys

| Key | LazyText / wiki |
| --- | ---------------- |
| `WKIslands_SpaceBelts` | `LazyText[wiki.WKIslands_SpaceBelts.title]` |
| `WKIslands_SpaceBeltLifts` | `LazyText[wiki.WKIslands_SpaceBeltLifts.title]` |
| `WKFluids_SpacePipes` | `LazyText[wiki.WKFluids_SpacePipes.title]` |
| `SpaceBeltsGroup` | `LazyText[island-group.SpaceBeltsGroup.title]`, `.description` |
| `SpacePipesGroup` | `LazyText[island-group.SpacePipesGroup.title]`, `.description` |

Paths: `…Mode.WikiDatabase.Entries.<key>`, `…WikiDatabase._KnowledgePanelEntries.<key>`.

`translations.json` in this dump does **not** contain these strings directly (keys live inside snapshot blobs).

---

## Simulation / CLR identifiers

### Island tenant systems (`simulation_systems.json`)

Each layout type is registered under:

```text
[*].definition_snapshot.ISimulationSystem.OnSimulationCreated.Listeners[].Target.SpecializedIslandTenantSystemsByType.<SpaceBelt_*|SpacePipe_*>
```

Placed instances also appear as map keys (chunk + rotation):

```text
…IslandIds.<SpaceBelt_Forward| @ (GlobalChunkCoordinate(x, y, z);Rotate…)>
```

### Port and connector types

| Belt-related | Pipe-related |
| ------------ | ------------ |
| `Game.Content.Features.SpacePaths.IslandIO.SpaceBeltInputConnector` | `Game.Content.Features.SpacePaths.IslandIO.SpacePipeInputConnector` |
| `Game.Content.Features.SpacePaths.IslandIO.SpaceBeltOutputConnector` | `Game.Content.Features.SpacePaths.IslandIO.SpacePipeOutputConnector` |
| `SpaceBeltPortSystem`, `SpaceBeltPortSenderSimulation`, `SpaceBeltPortReceiverSimulation` | `SpacePipePortSystem`, … |
| `SpaceBeltResources`, `SpaceBeltNodeMetadata`, `SpaceBeltSidePanelModuleDataProvider` | `SpacePipeResources`, `SpacePipeNodeMetadata`, `SpacePipeSidePanelModuleDataProvider` |
| `BeltPortSenderToSpaceBeltSimulationRenderer`, `BeltPortSenderToSpaceBeltResources` | `FluidPortSenderToSpacePipeSimulationRenderer`, `FluidPortSenderToSpacePipeResources` |
| `SpaceBeltToBeltPortReceiverResources` | `SpacePipeToFluidPortReceiverResources`, `SpacePipeToFluidPortReceiverSimulationRenderer` |
| `Game.Content.SpacePorts.Prediction.PredictionSpaceBeltPortSystem` | (pipe port systems in `BuiltinPredictionSimulationSystems+<SpacePipePortSystems>d__38`) |

### Layout node types (building graph)

| Id | Use |
| -- | --- |
| `Layout_SpaceBeltNode` | Island belt node in building definitions |
| `Layout_SpacePipeNode` | Island pipe node |
| `IslandLayoutSpaceBelt` | Island layout belt binding |
| `IslandLayoutSpacePipe` | Island layout pipe binding |
| `StructureStatPlatformsPerSpaceBelt` | Stat platform count (belt) |
| `StructureStatPlatformsPerSpacePipe` | Stat platform count (pipe) |

These repeat inside reflection-heavy files: `belts_pipes_transport.json`, `building_groups.json`, `building_variants.json`, `buildings.json` (audit payloads, not separate island catalog rows).

---

## Per-file presence

| File | Space belt/pipe content |
| ---- | ------------------------ |
| `research_unlocks.json` | **Authoritative** island `DefinitionsById`, groups, wiki entries |
| `simulation_systems.json` | Tenant systems, `IslandIds`, connector type keys |
| `toolbar_entries.json` | `SpaceBeltsGroup` / `SpacePipesGroup` in toolbar tree |
| `raw_type_index.json` | CLR type name index (includes port/sim types above) |
| `belts_pipes_transport.json` | Factory transport registry + embedded CLR strings mentioning SpaceBelt/SpacePipe ports |
| `building_groups.json`, `building_variants.json`, `buildings.json` | Same CLR strings inside `definition_snapshot` dumps |
| `sprites.json`, `items.json`, `shapes.json`, `fluids.json`, `materials.json`, `prefabs.json`, `asset_references.json`, `translations.json` | No dedicated space transport catalog in this dump |

---

## Lab classification (project)

When decoding blueprint `BP.Entries[*].T` (top-level only):

| Game `T` | `cell_kind` | `transport_kind` |
| -------- | ----------- | ---------------- |
| `SpaceBelt*` | `space_belt` | `shape_belt` |
| `SpacePipe*` | `space_pipe` | `fluid_pipe` |

Code: `src/shapez2_factory/domain/asteroid_lab/cell_classifier.py`  
Manual: [`documents/ai/manuals/game_logic.md`](../ai/manuals/game_logic.md) (Blueprint `T` → lab classification).

UI sprites: `django_apps/web/static/web/assets/sprites/SpaceBelt/`, `SpacePipe/` — filename = layout id + `.svg`.

---

## Factory vs island transport (do not confuse)

| Layer | Example ids in dump | Imported as |
| ----- | ------------------- | ----------- |
| **Factory** | `ForwardBelt`, `PipeForward`, `BeltPortSender`, `FluidPortSender` | `transport_building_registry` + `building_variant` |
| **Island** | `SpaceBelt_Forward`, `SpacePipe_Forward`, … | Research/simulation keys; **not** rows in `BuildingVariant` with those `internal_name` values |

Throughput numbers for space belts (tier-1) live in Django `ExteriorShapeTransportCapacity`, not in these JSON files.

---

## Related documentation

- [`documents/game_data_analysis/belts_pipes_transport/`](../game_data_analysis/belts_pipes_transport/00_summary.md) — factory `belts_pipes_transport.json` ORM mapping  
- [`documents/game_data_analysis/toolbar_entries/00_summary.md`](../game_data_analysis/toolbar_entries/00_summary.md) — `SpaceBeltsGroup` toolbar note  
- [`documents/ai/manuals/game_logic.md`](../ai/manuals/game_logic.md) — throughput + lab `cell_kind` rules  

---

## Maintenance

Re-scan after dump refresh:

```bash
# Keys whose names contain SpaceBelt / SpacePipe (representative files)
rg -l 'SpaceBelt|SpacePipe' documents/game_data/*.json
```

Expect **54** layout ids, **2** group ids, **3** wiki entry ids, plus CLR/port strings listed above.
