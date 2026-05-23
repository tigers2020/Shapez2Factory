---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: C
pr: 2.5
related_docs:
  - documents/game_rules/shapez2_asteroid_space_transport_throughput.md
  - documents/Algorithm/solver_runtime/00_core_principles.md
---

# Phase C ??Capacity Planner / RouteGoal Planner

## ëª©ì 

map ?¬ê¸°?€ ?ˆìƒ candidate ?˜ë? ê¸°ì??¼ë¡œ ?„ìš”??external `RouteGoal` ?˜ë? ?°ì •?œë‹¤. **?¤ì œ belt/pipeë¥??¤ì¹˜?˜ì? ?ŠëŠ”??**

## ?…ë ¥

```text
OptimizationInput
solver config (optional)
```

## ?°ì¶œë¬?
```text
PlannedRouteGoals
capacity_plan
```

**`OptimizationInput.route_goals` ?•ë³¸:** Phase C?ì„œ ?ì„±Â·ë³´ê°•??planned goal ì§‘í•©??probeÂ·commitÂ·validation??goal ?ŒìŠ¤?´ë‹¤. Phase B??empty/seedë§??ˆìš© ([`phase_b_optimization_input.md`](phase_b_optimization_input.md)).

## ?‘ì—…

### ì²˜ë¦¬???•ë³¸

Shape:

```text
12 fully boosted miners = 1 saturated Space Belt
```

Fluid:

```text
72 fully boosted pumps = 1 saturated Space Pipe
```

CANON: [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md).

### ì¶”ì • (geometry ?´ë¦¬?¤í‹±)

`mineable / 5` ?¨ë…?€ ê²Œì„ ê·œì¹™???„ë‹ˆ?? ?¨í„´ ìµœë? footprint(ì¶”ì¶œê¸??•ì¥+ì¶œêµ¬ stub ??5 cells)?€ ?Œí–‰???•íƒœ ?¸ì°¨ë¥?ë¶„ë¦¬?œë‹¤.

```python
PLATFORM_FOOTPRINT_CELLS = 5
DEFAULT_MINEABLE_PACKING_EFFICIENCY = 0.75  # v0; solver configë¡??œë‹ ê°€??v1)

estimated_extractor_groups = floor(
    mineable_cell_count * packing_efficiency / PLATFORM_FOOTPRINT_CELLS
)
```

OD-2: [`open_decisions.md`](open_decisions.md).

### Goal ??(ì²˜ë¦¬??CANON)

```python
shape_goal_count = ceil(estimated_extractor_groups / 12)
fluid_goal_count = ceil(fluid_platform_count / 72)
```

`12` / `72` ??Space Belt / Space Pipe ?¬í™” ë¹„ìœ¨ ([`shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md), ì»¤ë??ˆí‹°Â·?„í‚¤?€ ?•í•©).

### RouteGoal ?ì„±

external margin / external void / existing trunk attachment ?„ë³´?ì„œ goal ?ì„±.

```python
RouteGoal(
    coord=coord,
    goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
    transport_kind=TransportKind.SHAPE_BELT,
    priority=20,
    existing_trunk=False,
)
```

### Goal ???í•œ (shape)

```python
throughput = ceil(estimated_extractor_groups / 12)
extractor_scaled = estimated_extractor_groups * 2
shape_goal_count = min(8, max(2, min(throughput, extractor_scaled)))
```

extractor 2ê°??˜ì??ì„œ??throughput(1)ë³´ë‹¤ `groups*2` ìª½ì´ ?°ì„ ?˜ì–´ goal??ê³¼ë‹¤?˜ì? ?Šê²Œ ?œë‹¤.

### Goal ? íƒ ?•ì±… (v0)

?„ì œ: Phase Bê°€ `route_domain_bbox = asteroid_bbox + OUTER_VOID_PADDING(10)` ë°?padded `external_void_cells`ë¥??œê³µ?œë‹¤.

1. `external_void_cells` ì¤?**mineable BFS ê±°ë¦¬ `3 <= d <= 5`** (`route_domain_bbox` ?´ë? BFS)
2. **?“ì? ë©??‘ìª½ ë¶„í• ** ??side bandÂ·even spacing?€ **`mineable_cells` / `asteroid_bbox` extent** ê¸°ì? (`width >= height` ??**????wide face** `y` band, even spread along `x`; else **ì¢???wide face** `x` band, spread along `y`; `side_band_width = max(2, wide_face_span//8)`)
3. `first_count = total // 2`, `second_count = total - first_count` ??ê°?wide face?ì„œ **ê¸?rim ì¶?* ê¸°ì? `span / (count + 1)` even target ??ê°€??ê°€ê¹Œìš´ void snap (ë°”ê¹¥ìª?tie-break)
4. **shape goals** ë¨¼ì? bilateral ë°°ì¹˜, **fluid**??ë³„ë„ bilateral pass (`used` ê³µìœ ë¡?ì¢Œí‘œ ê²¹ì¹¨ ê¸ˆì?)
5. **?ê¸°:** ?¨ì¼ faceÂ·cardinal sectorÂ·?œìª½ ëª¨ì„œë¦??´ëŸ¬?¤í„°

`PlannedRouteGoals`??`spread_axis`(`x`=ê¸?rim??ê°€ë¡œì¶• even spacing, `y`=?¸ë¡œ), `shape_goals_shortfall` / `fluid_goals_shortfall` ë¥?ê¸°ë¡?œë‹¤.

**Replay:** `ROUTE_GOAL_GENERATED` ?´í›„ ëª¨ë“  timeline frame??`map_view.overlay_cells`??`route_goal` ?¤ë²„?ˆì´ê°€ ?„ì  ? ì??œë‹¤ (`merge_overlay_cells` + recorder persistent layer).

## ê¸ˆì?

- void???¤ì œ belt/pipe pre-install ([Â§0.2](00_core_principles.md))
- ì²?goal ?¬í™” ????ë²ˆì§¸ goal???œìˆœì°??¤ì¹˜?í•˜??ë°©ì‹
- void???„ì˜ transport ê¹”ê³  ?„ë? ?°ê²°

ì²˜ìŒë¶€???¬ëŸ¬ goal???´ê³  cost/loadë¡?ë¶„ì‚°?œë‹¤.

## ?„ë£Œ ì¡°ê±´

- [ ] `capacity_plan`??shape/fluid goal count ?°ì¶œ ê·¼ê±° ê¸°ë¡
- [ ] `PlannedRouteGoals`ê°€ transport materialization ?†ì´ ?ì„±??- [ ] bilateral wide-face even spacingÂ·rim ê±°ë¦¬ ?•ì±…??deterministic

## ?„ìˆ˜ ?ŒìŠ¤??
```text
test_capacity_planner_estimates_extractor_groups_with_packing
test_capacity_planner_estimates_shape_goal_count_by_12
test_capacity_planner_estimates_fluid_goal_count_by_72
test_route_goal_distance_band_excludes_near_and_far_void
test_route_goals_bilateral_wide_faces_top_bottom_even_x
test_capacity_shape_goals_capped_by_extractor_scale
test_route_goal_planner_creates_multiple_external_margin_goals
test_route_goal_planner_does_not_materialize_transport
```

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- ?ˆì •: `django_apps/asteroid_lab/optimization/capacity_planner.py`, `route_goal_planner.py`
- [`asteroid_lab_01_optimization_input.md`](../asteroid_lab_01_optimization_input.md) ??`RouteGoal`

## ?¤ìŒ Phase

??[`phase_d_gene_templates.md`](phase_d_gene_templates.md)
