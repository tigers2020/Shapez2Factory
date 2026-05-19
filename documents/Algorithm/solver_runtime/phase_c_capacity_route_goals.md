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

### 추정

```python
estimated_max_samples = floor(len(mineable_cells) / avg_gene_footprint)
```

v0 기본: `avg_gene_footprint = 5` ([`open_decisions.md`](open_decisions.md) OD-2).

### Goal 수

```python
shape_goal_count = ceil(estimated_shape_platforms / 12)
fluid_goal_count = ceil(estimated_fluid_platforms / 72)
```

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

### Goal 선택 정책 (v0)

1. `external_void_cells` 중 bbox margin에 가까운 셀 우선
2. 방향 분산: N/E/S/W 또는 quadrant별 균등
3. `transport_kind`별 별도 goal set
4. 동일 좌표에 shape/fluid goal 가능 — `route_domain`에서 mask 분리

## 금지

- void에 실제 belt/pipe pre-install ([§0.2](00_core_principles.md))
- 첫 goal 포화 후 두 번째 goal을 “순차 설치”하는 방식
- void에 임의 transport 깔고 전부 연결

처음부터 여러 goal을 열고 cost/load로 분산한다.

## 완료 조건

- [ ] `capacity_plan`에 shape/fluid goal count 산출 근거 기록
- [ ] `PlannedRouteGoals`가 transport materialization 없이 생성됨
- [ ] quadrant/방향 분산 정책이 deterministic

## 필수 테스트

```text
test_capacity_planner_estimates_shape_goal_count_by_12
test_capacity_planner_estimates_fluid_goal_count_by_72
test_route_goal_planner_creates_multiple_external_margin_goals
test_route_goal_planner_does_not_materialize_transport
test_route_goal_planner_distributes_goals_by_quadrant
```

## 관련 코드·문서

- 예정: `django_apps/asteroid_lab/optimization/capacity_planner.py`, `route_goal_planner.py`
- [`asteroid_lab_01_optimization_input.md`](../asteroid_lab_01_optimization_input.md) — `RouteGoal`

## 다음 Phase

→ [`phase_d_gene_templates.md`](phase_d_gene_templates.md)
