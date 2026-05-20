---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: C
pr: 2.5
related_docs:
  - documents/game_rules/shapez2_asteroid_space_transport_throughput.md
  - documents/Algorithm/solver_runtime/00_core_principles.md
---

# Phase C — Capacity Planner / RouteGoal Planner

## 목적

map 크기와 예상 candidate 수를 기준으로 필요한 external `RouteGoal` 수를 산정한다. **실제 belt/pipe를 설치하지 않는다.**

## 입력

```text
OptimizationInput
solver config (optional)
```

## 산출물

```text
PlannedRouteGoals
capacity_plan
```

**`OptimizationInput.route_goals` 정본:** Phase C에서 생성·보강한 planned goal 집합이 probe·commit·validation의 goal 소스이다. Phase B는 empty/seed만 허용 ([`phase_b_optimization_input.md`](phase_b_optimization_input.md)).

## 작업

### 처리량 정본

Shape:

```text
12 fully boosted miners = 1 saturated Space Belt
```

Fluid:

```text
72 fully boosted pumps = 1 saturated Space Pipe
```

CANON: [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md).

### 추정 (geometry 휴리스틱)

`mineable / 5` 단독은 게임 규칙이 아니다. 패턴 최대 footprint(추출기+확장+출구 stub ≈ 5 cells)와 소행성 형태 편차를 분리한다.

```python
PLATFORM_FOOTPRINT_CELLS = 5
DEFAULT_MINEABLE_PACKING_EFFICIENCY = 0.75  # v0; solver config로 튜닝 가능(v1)

estimated_extractor_groups = floor(
    mineable_cell_count * packing_efficiency / PLATFORM_FOOTPRINT_CELLS
)
```

OD-2: [`open_decisions.md`](open_decisions.md).

### Goal 수 (처리량 CANON)

```python
shape_goal_count = ceil(estimated_extractor_groups / 12)
fluid_goal_count = ceil(fluid_platform_count / 72)
```

`12` / `72` 는 Space Belt / Space Pipe 포화 비율 ([`shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md), 커뮤니티·위키와 정합).

### RouteGoal 생성

external margin / external void / existing trunk attachment 후보에서 goal 생성.

```python
RouteGoal(
    coord=coord,
    goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
    transport_kind=TransportKind.SHAPE_BELT,
    priority=20,
    existing_trunk=False,
)
```

### Goal 수 상한 (shape)

```python
throughput = ceil(estimated_extractor_groups / 12)
extractor_scaled = estimated_extractor_groups * 2
shape_goal_count = min(8, max(2, min(throughput, extractor_scaled)))
```

extractor 2개 수준에서는 throughput(1)보다 `groups*2` 쪽이 우선되어 goal이 과다하지 않게 한다.

### Goal 선택 정책 (v0)

전제: Phase B가 `route_domain_bbox = asteroid_bbox + OUTER_VOID_PADDING(10)` 및 padded `external_void_cells`를 제공한다.

1. `external_void_cells` 중 **mineable BFS 거리 `3 <= d <= 5`** (`route_domain_bbox` 내부 BFS)
2. **넓은 면 양쪽 분할** — side band·even spacing은 **`mineable_cells` / `asteroid_bbox` extent** 기준 (`width >= height` → **상/하 wide face** `y` band, even spread along `x`; else **좌/우 wide face** `x` band, spread along `y`; `side_band_width = max(2, wide_face_span//8)`)
3. `first_count = total // 2`, `second_count = total - first_count` — 각 wide face에서 **긴 rim 축** 기준 `span / (count + 1)` even target → 가장 가까운 void snap (바깥쪽 tie-break)
4. **shape goals** 먼저 bilateral 배치, **fluid**는 별도 bilateral pass (`used` 공유로 좌표 겹침 금지)
5. **폐기:** 단일 face·cardinal sector·한쪽 모서리 클러스터

`PlannedRouteGoals`는 `spread_axis`(`x`=긴 rim을 가로축 even spacing, `y`=세로), `shape_goals_shortfall` / `fluid_goals_shortfall` 를 기록한다.

**Replay:** `ROUTE_GOAL_GENERATED` 이후 모든 timeline frame의 `map_view.overlay_cells`에 `route_goal` 오버레이가 누적 유지된다 (`merge_overlay_cells` + recorder persistent layer).

## 금지

- void에 실제 belt/pipe pre-install ([§0.2](00_core_principles.md))
- 첫 goal 포화 후 두 번째 goal을 “순차 설치”하는 방식
- void에 임의 transport 깔고 전부 연결

처음부터 여러 goal을 열고 cost/load로 분산한다.

## 완료 조건

- [ ] `capacity_plan`에 shape/fluid goal count 산출 근거 기록
- [ ] `PlannedRouteGoals`가 transport materialization 없이 생성됨
- [ ] bilateral wide-face even spacing·rim 거리 정책이 deterministic

## 필수 테스트

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

## 관련 코드·문서

- 예정: `django_apps/asteroid_lab/optimization/capacity_planner.py`, `route_goal_planner.py`
- [`asteroid_lab_01_optimization_input.md`](../asteroid_lab_01_optimization_input.md) — `RouteGoal`

## 다음 Phase

→ [`phase_d_gene_templates.md`](phase_d_gene_templates.md)
