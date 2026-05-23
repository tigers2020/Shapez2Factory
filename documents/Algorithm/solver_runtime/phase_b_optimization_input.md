---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: B
pr: 1B
related_docs:
  - documents/Algorithm/solver_runtime/00_core_principles.md
  - documents/Algorithm/asteroid_lab_01_optimization_input.md
---

# Phase B ??Build OptimizationInput

## ëª©ì 

reconstruction snapshot??optimization layer???•ë³¸ DTOë¡?ë³€?˜í•œ?? Â§0.3 extension kind ??field kind ?•ê·œ?”ëŠ” **ë³?adapter ê²½ê³„**?ì„œ ?˜í–‰?œë‹¤.

## ?…ë ¥

```text
LoadedReconstructionSnapshot
```

## ?°ì¶œë¬?

```python
OptimizationInput(
    asteroid_cells=...,
    mineable_cells=...,
    rim_cells=...,
    interior_cells=...,
    external_void_cells=...,
    route_goals=...,              # seed only ??see below
    existing_transport_cells=...,
    existing_trunk_cells=...,
    protected_corridor_cells=...,
    blocked_cells=...,
    topology_graph=...,
    asteroid_bbox=...,
    route_domain_bbox=...,
    bbox=...,  # deprecated alias == route_domain_bbox
)
```

### Dual bbox (Phase B adapter)

| Field | Meaning |
|-------|---------|
| `asteroid_bbox` | Tight inclusive bbox over `mineable_cells` (fallback: all decoded server coords if empty) |
| `route_domain_bbox` | `expand_bbox(asteroid_bbox, OUTER_VOID_PADDING)` with `OUTER_VOID_PADDING = 10` |
| `bbox` | Legacy alias; must equal `route_domain_bbox` |

`external_void_cells` = all coords in `route_domain_bbox` that are **not** occupied decoded cells (`all_sv`). Reconstruction topology compare bbox stays tight (see `topology_contract`); only optimization routing expands.

### `route_goals` ê²½ê³„ (Phase B vs C)

| Phase | `route_goals` ??•  |
|-------|-------------------|
| **B** | **seed / basic only** ??ë¹„ì–´ ?ˆê±°??`frozenset()`), ê¸°ì¡´ trunkÂ·transport?ì„œ ì¶”ì¶œ??ìµœì†Œ goal. **planned set ?„ì„± ì±…ì„ ?†ìŒ.** |
| **C** | **planned `RouteGoal` ?•ë³¸** ??capacity plannerÂ·external margin/void ? íƒ?¼ë¡œ ?ì„±Â·ë³´ê°•. PR2 probeÂ·PR3+??**C ?´í›„** goal ì§‘í•© ?¬ìš©. |

Phase B ?„ë£Œ ì¡°ê±´???œëª¨??external margin goal??ì±„ì›Œì§â€ì„ **?£ì? ?ŠëŠ”??**

## ?‘ì—…

1. extractor / miner / extension ?œê±° ì¢Œí‘œ ??asteroid evidence ??`asteroid_cells` + `mineable_cells`
2. `asteroid_shape_field` / `asteroid_fluid_field` ??????mineable asteroid field
3. belt / pipe ?œê±° ì¢Œí‘œ ??asteroid evidence ?„ë‹˜ ??`existing_transport_cells` ?ëŠ” route domain evidence
4. `shapeMinerExtension` / `fluidMinerExtension` ????field kind ?•ê·œ??([`00_core_principles.md`](00_core_principles.md) Â§0.3)
5. ëª¨ë“  coordë¥?Server X/Yë¡??•ì •
6. `asteroid_bbox` / `route_domain_bbox` ë¶„ë¦¬ ë°?padded `external_void_cells` ?ì„± (`reconstruction_adapter`)

## ê¸ˆì?

- optimizerÂ·candidate_geometryÂ·route_probe ?´ë??ì„œ cell.kindë¡?mineable ?ì •
- optimization ?´ë? raw?”server ?¬ë???
- DB ?ë³¸ ?˜ì •

## ?„ë£Œ ì¡°ê±´

- [ ] all coords are Server X/Y
- [ ] mineable field kind does not depend on strict fluid kind in optimizer
- [ ] extension/miner evidence is represented as mineable asteroid field sets
- [ ] `RouteDomainSnapshotBuilder` ?¨ì¼ ì§„ì…?¼ë¡œ `route_domain` ?œë“œ ê°€??
- [ ] `route_goals`??empty ?ëŠ” seedë§???planned goal?€ Phase C ì±…ì„

## ?„ìˆ˜ ?ŒìŠ¤??

PR1B ??`tests/unit/asteroid_lab/test_optimization_input.py` (DTOÂ·adapterÂ·ì¢Œí‘œ) ??[`implementation_sequence.md`](implementation_sequence.md).

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- [`asteroid_lab_01_optimization_input.md`](../asteroid_lab_01_optimization_input.md)
- `django_apps/asteroid_lab/optimization/` ??`OptimizationInput` DTO
- **PR1B ë¶€ë¶??„ë£Œ:** `reconstruction_adapter.optimization_input_from_reconstruction`, `route_domain.py` ([`implementation_sequence.md`](implementation_sequence.md))
- **?¨í‚¤ì§€ ?•ë³¸:** `asteroid_lab/optimization` only ??`shapez_asteroid` ?œê±°??([`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) Â§2)

## ?¤ìŒ Phase

??[`phase_c_capacity_route_goals.md`](phase_c_capacity_route_goals.md)
