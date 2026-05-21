# Phase 4 — Fast Route Feasibility Probe

## 목적

BundleCandidate의 output_stub가 **RouteGoal** 집합까지 연결 가능한지 빠르게 평가한다.

이 단계는 최적 routing이 아니다.

```text
goal = feasibility
not global optimal route
```

## `TopologyGraph`와의 관계

`RouteProbeInput`은 **`route_domain`**(셀별 통과 규칙·비용)과 **`goals`**로 탐색을 제한한다.

**인접성 소스 (v0 계약):**

- 기본: `topology_graph`의 **무방향** 인접을 사용해 이웃을 enumerates한다 (Phase 1). `traversal_cost`는 엣지·노드 정책과 합치되게 domain과 조합한다.
- `route_domain`에 키가 없는 coord는 아래 **도메인 경계 정책**을 따른다.
- `topology_graph`가 비어 있거나 stub 구현이면 **fallback**: `neighbors4_server(coord)`로 이웃을 만들되, Phase 1 테스트와 **동일 인접(밀집 4방)** 을 보장해야 한다.

즉 “topology만 보고 domain을 무시” 또는 “domain만 보고 graph를 무시”가 되면 안 된다. **확장 후보 이웃은 graph 규칙, 셀 통과·비용·mask는 `RouteCellDomain`** 이다.

## 알고리즘

v0 기본 구현은 **bounded uniform-cost search (Dijkstra-lite)** 이다. `RouteCellDomain.traversal_cost`(및 엣지 가중)에 따라 **가중 비용 최단**을 찾는다. 모든 `traversal_cost == 1`인 fixture에서는 **BFS와 동일한 동작**을 한다.

추후 A* heuristic을 추가할 수 있다.

## `TransportMask`

`RouteCellDomain.transport_mask`의 정본 타입이다 (자유 dict 금지).

```python
class TransportMask(IntFlag):
    NONE = 0
    SHAPE_BELT = 1
    FLUID_PIPE = 2
    BOTH = SHAPE_BELT | FLUID_PIPE
```

또는 동등하게:

```python
@dataclass(frozen=True)
class TransportMaskStruct:
    allow_shape_belt: bool
    allow_fluid_pipe: bool
```

프로젝트는 **하나**를 채택한다. probe의 `transport_kind`와 불일치하면 해당 셀로는 확장하지 않는다.

## Route cell domain (allowed / preferred / blocked 대체)

`allowed_cells` + `preferred_cells` + `blocked_cells` 3분할만 두면 구현이 진행될수록 **route permission drift**가 나기 쉽다.

셀별 의미는 **`RouteCellDomain`** 으로 고정한다.

```python
@dataclass(frozen=True)
class RouteCellDomain:
    coord: Coord
    route_class: RouteClass
    traversal_cost: int
    hard_blocked: bool
    carve_allowed: bool
    transport_mask: TransportMask
```

```python
route_domain: Mapping[Coord, RouteCellDomain]
```

v0에서는 `OptimizationInput`과 점유 셀·transport kind로부터 domain 빌더가 **축소된 domain**을 만들어도 된다. v1에서 carve·reclaim·reserved path·혼잡을 넣을 때 **DTO를 갈아엎지 않도록** 이 계약을 유지한다.

**빌더 소유권:** `route_domain` 스냅샷 생성의 정본 진입점은 Phase 1 **`RouteDomainSnapshotBuilder`** 와 동일하다 (이름만 다른 래퍼 금지·단일 책임). probe·evolution이 셀 단위로 domain을 **제자리 수정**하지 않는다.

### 도메인 경계·goal 필터 (v0 정책)

아래를 **`RouteProbeFailureReason`·탐색 스킵 규칙**과 맞춘다.

```text
start not in route_domain -> invalid_route_domain (또는 start_blocked와 택일하되 문서·테스트로 하나만 고정)
neighbor coord not in route_domain -> 확장 스킵 (failure로 기록하지 않음)
goal.coord not in route_domain -> 해당 RouteGoal 제외 (goals 필터 단계)
필터 후 goals 비어 있음 -> no_goal_cells
```

`invalid_route_domain`과 `start_blocked`를 둘 다 쓸 경우: **start가 domain 밖이면 `invalid_route_domain`**, start는 domain 안이나 `hard_blocked`/mask로 막힌 경우 **`start_blocked`** 로 구분한다.

## 입력 DTO

```python
@dataclass(frozen=True)
class RouteProbeInput:
    start: Coord
    goals: frozenset[RouteGoal]
    route_domain: Mapping[Coord, RouteCellDomain]
    topology_graph: TopologyGraph
    max_expansions: int
    transport_kind: TransportKind
    goal_priority_weight: int
```

`goal_priority_weight`는 `route_selection_score`에 쓰인다. v0 기본값 `10`을 권장한다 (`CandidateGenerationConfig`에서 주입해도 된다).

`goals`는 `RouteGoal.transport_kind`가 probe의 `transport_kind`와 맞는 것만 사용한다 (미지정 goal은 정책으로 허용 여부를 문서화).

탐색은 `hard_blocked` 이거나 `transport_mask`가 현재 transport를 허용하지 않는 셀로는 확장하지 않는다.

## Goal 선택·`reached_goal` (비용 vs priority)

`RouteGoal.priority`는 **작을수록 선호**(Phase 1). 경로 탐색은 **비용 최소**를 먼저 최적화한다. 둘이 충돌할 때의 정본 규칙(v0):

### Probe selection score (가중 점수, v0 정본)

```text
route_selection_score(path, goal) = path_cost + goal_priority_weight * goal.priority
```

- `path_cost`: 도메인 `traversal_cost` 합(및 엣지 가중이 있으면 동일 규칙 합산).
- `goal_priority_weight`: `RouteProbeInput.goal_priority_weight` (비음수 정수). v0 기본 예: `10` (튜닝 가능).

**선택 규칙:** 도달 가능한 (path, goal) 후보 중 **`route_selection_score` 최소**를 선택한다.

**동점 tie-break (결정성 필수):** (1) `path_cost` 오름차순 (2) `goal.priority` 오름차순 (3) `goal.coord` lexicographic (4) `goal_kind` 고정 순서 — 구현은 하나의 전역 순서로 고정한다.

이 스코어가 `reached_goal`·`RouteProbeResult.cost`·fitness의 route penalty와 **모순 없이** 연결되도록 한다 (Phase 5).

## 실패 사유 타입

구현에서 `failure_reason`은 **`RouteProbeFailureReason | None`** 이다. 아래 텍스트 목록은 enum 멤버 이름과 동일하게 유지한다.

## 출력 DTO

```python
@dataclass(frozen=True)
class RouteProbeResult:
    reachable: bool
    path: tuple[Coord, ...]
    cost: int
    expanded_nodes: int
    reached_goal: RouteGoal | None
    goal_priority: int | None
    failure_reason: RouteProbeFailureReason | None
```

`reachable=True`이면 `reached_goal`은 위 **selection score·tie-break**로 선택된 `RouteGoal`이다.

`goal_priority`는 `reached_goal.priority`의 복사로, **작을수록 선호**인 `RouteGoal.priority` 규칙(Phase 1)과 동일하다. fitness·validation에서 trunk 부착 vs margin 스크래치 구분에 쓴다.

`reachable=False`이면 `reached_goal`·`goal_priority`는 `None`, `failure_reason`은 필수.

## Cost Model v0

도메인의 `traversal_cost`가 1차 값이다. 의미 예시:

```text
existing trunk cell = low cost
external void corridor = normal cost
asteroid carve = high cost or forbidden (carve_allowed)
occupied bundle cell = hard_blocked
hard protected = hard_blocked
wrong transport kind = transport_mask 불일치
```

## Failure Reason (`RouteProbeFailureReason`)

```text
start_blocked
no_goal_cells
exhausted
budget_exceeded
blocked_by_occupied
invalid_transport_kind
invalid_route_domain
```

### `blocked_by_occupied` 사용 시점

일반 확장에서 이웃이 `hard_blocked`/mask 불일치면 **스킵**할 뿐 `blocked_by_occupied`로 올리지 않는다. `blocked_by_occupied`는 다음에만 사용한다.

```text
start는 route_domain에 있으나 start 셀 자체가 occupied-derived hard_blocked이거나,
start의 모든 유효 이웃이 occupied-derived hard_blocked이라 한 건도 확장할 수 없을 때
```

그 외 탐색 소진은 `exhausted`.

### Budget·`expanded_nodes` 정의

- **`expanded_nodes`**: frontier에서 **pop되어 확정 처리된 coord** 수(동일 coord 재확정은 카운트하지 않음; 구현·테스트로 한 가지로 고정).
- **`max_expansions`**: 위 카운트가 `max_expansions`를 **초과**하면 탐색을 중단하고 `budget_exceeded`를 반환한다(유효 goal 미도달 시).

## Incremental commit과의 연결 (예고)

commit 성공 후 **reserved path**는 다음 probe를 위해 `RouteDomainSnapshotBuilder`가 만든 `route_domain` 스냅샷에 반영된다 (Phase 1·7). candidate 단계 probe는 “당시 스냅샷”이며, commit 후 재-probe 없이 drift하면 안 된다.

## Feasibility vs commitability (낙관성 경계)

`reachable=True`는 **해당 `RouteProbeInput.route_domain` 스냅샷**에서의 feasibility다. incremental commit 루프에서 **reservation 누적·corridor starvation·다른 transport mask**가 바뀌면 동일 후보가 실패할 수 있다.

따라서:

```text
candidate probe 성공 ≠ 최종 commit 성공의 논리적 함의
```

대응은 **Phase 7에서 항상 최신 domain으로 재-probe**, **Phase 5 fitness**에 route_fragility·shared corridor pressure 등 **보수적 프록시**(`PenaltyMode.CONSERVATIVE`; `OFF`에서만 0), **Phase 8 validation**으로 분산한다.

## Invariant

```text
[ ] uniform-cost 탐색은 hard_blocked 셀로 확장하지 않는다
[ ] 이웃 나열은 topology_graph 무방향 계약과 모순 없음 (fallback 시 neighbors4_server와 동일)
[ ] shape belt and fluid pipe route domains are separated
[ ] reachable=True requires path length > 0 unless start is goal
[ ] reachable=True 이면 reached_goal·goal_priority가 계약에 맞게 채워진다
[ ] reachable=False 이면 failure_reason은 RouteProbeFailureReason (필수)
[ ] goal_kind·priority는 “아무 외부 좌표 도달”이 아니라 계약된 목표만 매칭한다
[ ] reached_goal 선택은 route_selection_score·tie-break로 결정된다
[ ] expanded_nodes·max_expansions 정의가 구현·테스트와 일치한다
[ ] blocked_by_occupied는 문서화된 좁은 조건에서만 사용된다

## 테스트

```text
test_route_probe_reaches_prioritized_route_goal
test_route_probe_rejects_blocked_start
test_route_probe_never_crosses_hard_blocked_cells
test_route_probe_respects_server_cardinal_adjacency
test_route_probe_budget_exceeded
test_route_probe_transport_kind_separation
test_route_probe_respects_transport_mask_per_cell
test_route_probe_result_records_reached_goal_and_priority
test_route_probe_selection_score_prefers_lower_score_over_path_cost
test_route_probe_expanded_nodes_matches_definition
test_route_probe_blocked_by_occupied_only_at_start_trap
```

## 완료 조건

```text
[ ] bounded uniform-cost search (Dijkstra-lite) 구현
[ ] RouteProbeInput / RouteProbeResult (route_domain·RouteGoal·topology_graph) 구현
[ ] TransportMask 타입 정의
[ ] RouteProbeFailureReason enum + RouteProbeResult (reached_goal·goal_priority) 구현
[ ] route_selection_score·tie-break 문서화 및 테스트
[ ] candidate_generator에서 호출 가능
```
