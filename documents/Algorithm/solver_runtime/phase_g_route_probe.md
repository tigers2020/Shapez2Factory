---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: G
pr: 2
related_docs:
  - documents/Algorithm/asteroid_lab_04_route_probe.md
  - documents/Algorithm/solver_runtime/open_decisions.md
---

# Phase G — Route Probe

## 목적

candidate의 `route_probe_start`에서 `RouteGoal`까지 연결 가능한지 빠르게 평가한다. 전역 최적 routing이 아니라 **feasibility**다.

## 입력

```python
RouteProbeInput(
    start=projected.route_probe_start,
    goals=planned_route_goals,
    route_domain=route_domain,
    topology_graph=inp.topology_graph,
    max_expansions=config.route_probe_max_expansions,
    transport_kind=transport_kind,
    goal_priority_weight=10,
)
```

**레거시 차이:** [`asteroid_lab_04`](../asteroid_lab_04_route_probe.md)의 `output_stub` = **금지 alias**; Runtime·신규 코드는 **`route_probe_start`** 만 ([§0.6](00_core_principles.md), [OD-1](open_decisions.md)).

## 산출물

```python
RouteProbeResult(
    reachable=True/False,
    path=...,
    cost=...,
    expanded_nodes=...,
    reached_goal=...,
    goal_priority=...,
    failure_reason=...,
)
```

## 작업

### Route domain (candidate phase)

candidate 단계 `projected.occupied_cells`는 **확정(commit) 점유가 아님** — probe용 **provisional blocker**만 반영한다.

**권장 API (PR2):** `RouteDomainSnapshotBuilder.build_snapshot`에 candidate 전용 인자 추가.

```python
def build_route_domain_for_projected_gene_probe(builder, inp, projected):
    return builder.build_snapshot(
        inp,
        provisional_blocked_cells=projected.occupied_cells,
    )
```

**과도기 (현재 코드):** `committed_occupied_cells=` 이름으로 같은 집합을 넘길 수 있으나 **의미는 provisional only**. commit 단계의 `committed_occupied_cells`와 혼동 금지.

```python
# 과도기 — PR2에서 provisional_blocked_cells 로 이전
return builder.build_snapshot(
    inp,
    committed_occupied_cells=projected.occupied_cells,  # NOT a layout commit
)
```

wrapper·call site **필수 주석:**

```text
Candidate-phase provisional occupancy only. This does not commit placement.
```

`RouteDomainSnapshotBuilder` **단일** 진입 — in-place mutation 금지.

### Search

- bounded uniform-cost search
- `hard_blocked` skip
- `transport_mask` mismatch skip
- goal `transport_kind` filter

### Goal selection

```text
route_selection_score = path_cost + goal_priority_weight * goal.priority
```

Tie-break:

```text
path_cost asc
priority asc
goal.coord lexicographic
goal_kind fixed order
```

## 금지

- candidate probe 성공을 commit 증명으로 사용 ([§0.5](00_core_principles.md))
- probe가 layout에 belt/pipe materialize

## 완료 조건

- [ ] reachable 시 `reached_goal` non-null
- [ ] blocked·mask·budget exceeded가 enum `failure_reason`으로 기록
- [ ] `route_probe_start`에서만 탐색 시작 (fixed_output_transport 셀은 start 이전)

## 필수 테스트

```text
test_route_probe_reaches_goal_on_open_domain
test_route_probe_returns_no_goal_cells_when_filtered_goals_empty
test_route_probe_respects_hard_blocked_cells
test_route_probe_respects_transport_mask
test_route_probe_budget_exceeded
test_route_probe_selects_goal_by_priority_weighted_score
test_route_probe_uses_route_probe_start_not_fixed_output_transport
```

## 관련 코드·문서

- 예정: `django_apps/asteroid_lab/optimization/route_probe.py`
- [`asteroid_lab_04_route_probe.md`](../asteroid_lab_04_route_probe.md)

## 다음 Phase

→ [`phase_h_candidate_pool.md`](phase_h_candidate_pool.md)
