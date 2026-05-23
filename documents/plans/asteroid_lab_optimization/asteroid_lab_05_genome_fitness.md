# Phase 5 — Genome and Fitness


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_05_genome_fitness.md`](../../Algorithm/asteroid_lab_05_genome_fitness.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

> Fitness input contract·predictive vs observed 분리 — Algorithm [`asteroid_lab_05_genome_fitness.md`](../../Algorithm/asteroid_lab_05_genome_fitness.md) 정본.

## 목적

Candidate pool에서 어떤 bundle 조합을 선택할지 평가하는 genome 구조와 fitness 함수를 정의한다.

## 금지

Cell-level genome 금지.

나쁜 구조:

```python
dict[Coord, CellState]
```

권장 구조:

```python
tuple[CandidateId, ...]
```

## 확장성 주의

`Gene = candidate_id`만으로 장기 운용 시 mutation 공간이 부족해질 수 있다. v1+에서는 `topology_signature`·routing preference를 genome 측에서 참조할지 검토한다. v0는 후보 ID 조합으로 충분하다고 가정한다.

## DTO

```python
@dataclass(frozen=True)
class Gene:
    candidate_id: str
    enabled: bool
    commit_order: int
```

`commit_order`는 genome 내 **확정·재배치 순서** 등에 쓰인다. `RouteGoal.priority`와 이름이 충돌하지 않게 `priority`라는 필드명은 쓰지 않는다.

```python
@dataclass(frozen=True)
class Genome:
    genome_id: str
    genes: tuple[Gene, ...]
    seed: int
```

```python
@dataclass(frozen=True)
class FitnessMetrics:
    selected_candidate_count: int
    extractor_count: int
    extension_count: int
    overlap_count: int
    unreachable_count: int
    total_route_cost: int
    max_trunk_sharing: int
    narrow_passage_occupied_count: int
```

`unreachable_count`는 **candidate generation 단계에서 normal pool에 걸러진 수**가 아니라, **현재 fitness 평가 시점**에 선택된 gene·후보를 대상으로 재평가(또는 diagnostic 규칙)했을 때 unreachable로 간주된 수다.

```python
@dataclass(frozen=True)
class FitnessBreakdown:
    extractor_score: float
    extension_score: float
    throughput_score: float
    route_cost_penalty: float
    overlap_penalty: float
    unreachable_penalty: float
    congestion_penalty: float
    orphan_penalty: float
    corridor_block_penalty: float
    future_expansion_penalty: float
    narrow_passage_penalty: float
    trunk_sharing_penalty: float
    dead_end_penalty: float
    route_goal_quality_score: float
    route_goal_priority_penalty: float
    route_fragility_penalty: float
    shared_corridor_pressure_penalty: float
    total: float
    metrics: FitnessMetrics
```

`route_goal_quality_score` / `route_goal_priority_penalty`는 **같은 reachable이라도** trunk 부착·soft corridor·margin·carve 필요 여부를 구분한다. 입력은 candidate에 저장된 `route_probe_result.reached_goal`·`goal_priority`를 사용한다.

`route_fragility_penalty` / `shared_corridor_pressure_penalty`는 **candidate 시점 reachable이 commit에서 깨질 위험**을 줄이기 위한 보수적 항목이다. v0에서는 **0 또는 단순 휴리스틱**(예: path가 공유 복도 셀을 몇 번 지나는지, narrow `RouteClass` 구간 길이)으로 시작하고, **필드는 breakdown에 고정**해 구현 drift를 막는다 (Phase 4 feasibility vs commitability 절 참조).

### `unreachable_penalty`가 필요한 이유

Phase 3에서 unreachable 후보는 **normal pool에 들어가지 않는다**. 그럼에도 fitness에 `unreachable_penalty`를 두는 이유:

```text
1. diagnostic / 실험 모드에서 genome이 비정상 후보를 참조할 수 있음
2. genome 조합·commit sequence 이후 route_domain / reservation 충돌로 재평가 시 unreachable이 되는 경우
3. stale probe 스냅샷 방어 (재-probe 전 단계)
```

구현자가 “candidate 단계에서 걸렀는데 왜 penalty?”로 제거하지 않도록 본 절을 유지한다.

## Fitness v0

기본식(가중치는 튜닝 대상):

```text
fitness =
    + extractor_count * 1000
    + extension_count * 250
    + throughput_score
    + route_goal_quality_score
    - route_cost * 5
    - route_goal_priority_penalty
    - overlap_count * 10000
    - unreachable_count * 20000
    - congestion_penalty
    - orphan_penalty
    - corridor_block_penalty
    - future_expansion_penalty
    - narrow_passage_penalty
    - trunk_sharing_penalty
    - dead_end_penalty
    - route_fragility_penalty
    - shared_corridor_pressure_penalty
```

### Route goal 품질 (정성)

예시 가중치는 튜닝 대상이다.

```text
existing_trunk 연결: priority penalty 낮음 / quality 높음
soft_corridor: 소량 penalty
external_margin: 중간 penalty
asteroid_carve 필요: 높은 penalty (또는 carve_allowed False면 unreachable과 동급 처리)
```

### 평면(flat) 점수의 위험

좁은 corridor를 고처리량 후보가 전부 점유하면 **pass2 blockage·이후 unreachable**이 재발할 수 있다.

위 penalty 항목은 v0에서 **0 또는 보수적 휴리스틱**으로 시작해도 되지만, **필드는 미리 노출**해 구현 drift를 막는다.

권장 지배 관계(정성):

```text
narrow_passage / corridor_block / future_expansion
> 단순 throughput 증가분 (특히 단일 corridor 붕괴 시나리오)
```

## Overlap 처리

두 candidate가 같은 occupied cell을 사용하면 conflict다.

v0에서는 conflict genome을 허용하되 큰 penalty를 준다.

repair 단계에서 제거한다.

## Route Cost

각 후보의 비용은 **`route_probe_result.cost`**(Phase 3 스냅샷)에서 읽는다.

단, 최종 commit 단계에서는 다시 probe해야 한다.

## Invariant

```text
[ ] genome stores candidate ids, not cells
[ ] fitness must be deterministic for same input
[ ] overlap penalty dominates throughput gain
[ ] unreachable penalty dominates extractor gain
[ ] all score components are exposed in breakdown (v0에서 0이어도 합산식에 포함)
[ ] route_goal_quality_score·route_goal_priority_penalty가 probe 스냅샷과 결정적으로 연결된다
[ ] FitnessMetrics가 카운트·합 등 집계 값을 보존한다 (replay·디버그)
```

## 테스트

```text
test_genome_uses_candidate_ids
test_fitness_deterministic
test_fitness_penalizes_overlap
test_fitness_penalizes_unreachable
test_fitness_prefers_more_throughput_when_feasible
test_fitness_breakdown_total_matches_components
test_fitness_metrics_populated
test_fitness_route_goal_quality_prefers_trunk_over_margin_when_reachable_both
test_fitness_narrow_corridor_dominates_high_throughput_greed
```

## 완료 조건

```text
[ ] Gene/Genome DTO 구현
[ ] FitnessBreakdown + FitnessMetrics 구현
[ ] deterministic evaluator 구현
[ ] route_fragility_penalty·shared_corridor_pressure_penalty가 breakdown에 존재 (v0는 0 허용)
[ ] overlap/unreachable penalty 테스트 통과
```
