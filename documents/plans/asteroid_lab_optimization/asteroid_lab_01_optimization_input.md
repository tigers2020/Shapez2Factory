# Phase 1 — Optimization Input Contract

## 목적

Reconstruction 결과를 optimization layer가 안정적으로 사용할 수 있는 입력 DTO로 변환한다.

## 입력

Reconstruction engine이 만든 완성 asteroid topology.

필수 의미:

```text
extractor / extension 제거 좌표 = asteroid evidence
belt / pipe 제거 좌표 = asteroid evidence 아님
interior fill cell = asteroid field
void = 외부 또는 진짜 빈 공간
```

기존 레이아웃은 다음을 입력에 반영한다.

```text
existing belt / pipe / trunk / protected corridor
```

**belt vs pipe(kind)** 는 좌표만으로 재추론하지 않는다. `RouteCellDomain.transport_mask` 생성은 `existing_transport_cells`(또는 이에서 유도한 coord→kind)를 우선 소스로 한다 (Phase 4 빌더).

## 좌표 정본 (Server X/Y, 12L)

OptimizationInput 이후 모든 Coord는 Server X/Y dense coord이며, raw 좌표는 입력으로 허용하지 않는다. raw↔server 변환은 decode/import boundary 또는 final UI/export projection boundary에서만 허용된다.

## Route goal 계약

`frozenset[Coord]` 수준의 `external_goals`만 두면 trunk seed·corridor entry·margin·기존 부착점·soft corridor를 구분하지 못해 **STEP4류 재발**이 난다.

따라서 goal은 좌표가 아니라 **RouteGoal** 단위로 고정한다.

```python
# RouteGoalKind 예: trunk_seed | corridor_entry | external_margin |
# existing_transport_attachment | soft_corridor | (확장 시 추가)
```

```python
@dataclass(frozen=True)
class RouteGoal:
    coord: Coord
    goal_kind: RouteGoalKind
    transport_kind: TransportKind | None
    priority: int
    existing_trunk: bool
```

우선순위(비용·feasibility 해석의 기본 가정):

```text
existing trunk 연결
> soft corridor 연결
> external margin 연결
> asteroid carve
```

세부 비용은 Phase 4 `RouteCellDomain.traversal_cost`와 probe 정책이 맞춘다.

### `RouteGoal.priority` 정렬 규칙

**숫자가 작을수록 선호(우선 매칭·낮은 penalty)** 로 고정한다. 구현자가 “높은 값이 좋은지” 해석하지 않게 한다.

예시 밴드(프로젝트에서 조정 가능, 단 **방향**은 유지):

```text
0  = existing trunk 부착·trunk_seed 계열
10 = soft_corridor / existing_transport_attachment
20 = external_margin
30 = asteroid carve 허용 구간 등
```

`reached_goal` 선택 규칙(비용 vs `RouteGoal.priority` 충돌)은 **Phase 4**의 `route_selection_score`·tie-break로 단일화한다. Phase 1의 `priority`는 「작을수록 선호」**의미만** 고정한다.

## Topology graph 계약

셀 집합만으로는 라우팅·corridor·fitness가 반복해서 **Server 격자** 이웃 유틸(예: `neighbors4_server`)을 호출하게 된다.

**TopologyGraph**는 reconstruction 완료 시점에 한 번 만들고 `OptimizationInput`에 넣어, 이후 탐색·분석의 공통 입력으로 쓴다.

```python
@dataclass(frozen=True)
class TopologyNode:
    coord: Coord
    node_kind: TopologyNodeKind

@dataclass(frozen=True)
class TopologyEdge:
    a: Coord
    b: Coord
    edge_kind: EdgeKind
    traversal_cost: int
```

**무방향(undirected) 계약 (v0):** `TopologyGraph`의 엣지는 **논리적 무방향**이다. 저장은 (a,b)·(b,a) **양쪽 모두** 넣거나, 인접성 빌더가 한 쌍을 양방향 인접으로 확장한다. BFS·probe는 **adjacency를 무방향으로** 해석한다 (방향 그래프로 가정하지 않는다).

대안으로 동일 의미를 유지하려면 필드명을 `src`/`dst`로 두되, 위와 같이 **무방향**임을 문서·테스트로 고정한다.

```python
@dataclass(frozen=True)
class TopologyGraph:
    nodes: frozenset[TopologyNode]
    edges: frozenset[TopologyEdge]
```

`TopologyNodeKind` / `EdgeKind`는 프로젝트 도메인에 맞게 좁게 시작하고 확장한다.

## 출력 DTO

`@dataclass(frozen=True)`와 **스냅샷·해시·직렬화 안정성**을 맞추려면, `existing_transport`는 **가변 `dict`를 그대로 넣지 않는다**. 표준 `FrozenMapping`이 없으므로 아래 중 하나로 고정한다 (프로젝트에서 하나만 채택).

```python
@dataclass(frozen=True)
class ExistingTransportCell:
    coord: Coord
    transport_kind: TransportKind
```

권장:

```python
existing_transport_cells: frozenset[ExistingTransportCell]
```

**Trunk 정본:** `existing_trunk_cells: frozenset[Coord]`만 trunk 멤버십의 근거로 쓴다. `ExistingTransportCell`에 trunk 플래그를 두지 않는다 (Overview와 동일).

빌더는 `OptimizationInput` 생성 시 `coord`당 하나의 `TransportKind`를 보장한다. 뷰·probe가 `coord -> kind`가 필요하면 **파생** `Mapping`을 만들되, **DTO 본문은 불변 집합**을 우선한다.

```python
@dataclass(frozen=True)
class OptimizationInput:
    asteroid_cells: frozenset[Coord]
    mineable_cells: frozenset[Coord]
    rim_cells: frozenset[Coord]
    interior_cells: frozenset[Coord]
    external_void_cells: frozenset[Coord]
    route_goals: frozenset[RouteGoal]
    existing_transport_cells: frozenset[ExistingTransportCell]
    existing_trunk_cells: frozenset[Coord]
    protected_corridor_cells: frozenset[Coord]
    blocked_cells: frozenset[Coord]
    topology_graph: TopologyGraph
    bbox: BBox
```

**하위 호환(문서만):** 기존 이름 `existing_transport_by_coord`를 코드에 남길 경우, 내용은 `MappingProxyType` 등 **읽기 전용 뷰**이거나 `existing_transport_cells`에서만 유도해야 한다.

`blocked_cells`는 v0에서도 **hard no-go** 집약 표현으로 유지할 수 있다. 단, Phase 4의 `RouteCellDomain.hard_blocked`와 **모순 없이** 동기화할 책임은 adapter / domain 빌더에 있다.

### `protected_corridor_cells`와 `route_domain`

`protected_corridor_cells`의 모든 coord는 **후속 `route_domain` 빌더가 만드는 `RouteCellDomain` 키 집합에 포함**되어야 한다 (없는 coord만 나열해 두는 형태 금지). 세부 반영은 Phase 4 빌더 계약을 따른다.

## `route_domain` 스냅샷 소유권 (drift 방지)

`Mapping[Coord, RouteCellDomain]` 형태의 **탐색용 route_domain 정본 스냅샷**은 **`RouteDomainSnapshotBuilder`(단일 진입점)** 만 생성한다.

```text
입력: OptimizationInput 기반 불변 스냅샷 + (commit 루프에서) CONFIRMED RouteReservation·placement occupied 등 문서화된 누적 상태
금지: candidate generator·probe·evolution이 RouteCellDomain을 제자리(in-place)로 패치하는 것
권장: reservation append / commit 성공 후에는 항상 전면 재빌드로 다음 스냅샷을 만든다
```

예외 없이 **한 빌더**가 `hard_blocked`·`transport_mask`·`traversal_cost` 일관성을 책임진다. Phase 4 입력 계약·Phase 7 commit 루프와 교차 참조한다.

## 좌표 규칙

본 플랜과 `OptimizationInput` 이후 전 계층에서 **`Coord` = (Server X, Server Y)** 만을 쓴다. 정수 **밀집 격자**(…, -1, 0, 1, …)이며, 카테인 이웃은 `(x±1, y)`, `(x, y±1)`이다.

Reconstruction·스냅샷 adapter는 이 계약을 만족하는 `Coord`만 `OptimizationInput`에 넣는다.

필수 utility (`Coord` = Server 전용):

```python
neighbors4_server(coord: Coord) -> tuple[Coord, ...]
cardinal_unit_toward(src: Coord, dst: Coord) -> Direction
```

`neighbors4_server`는 **표준 4방향** 밀집 규칙이다. `topology_graph` 엣지·probe fallback 이웃 나열과 **동일 계약**으로 맞춘다. 엣지 집합과 이웃 유틸은 **단일 출처**를 가진다.

## Invariant

```text
[x] 모든 Coord·셀 집합이 Server X/Y (`neighbors4_server` 밀집 4방 계약)
[x] topology_graph·probe의 이웃이 `neighbors4_server`와 동일 계약
[x] inferred interior fill must be mineable asteroid field
[x] external void must not be mineable
[x] belt/pipe removed positions must not become asteroid evidence by default
[x] extractor/extension removed positions must become asteroid evidence
[x] route_goals: 각 goal은 goal_kind·priority·existing_trunk 의미를 가진다
[x] topology_graph: 노드 coord가 asteroid / void 계약과 모순 없다
[x] existing_transport_cells: 각 coord에 최대 하나의 셀 레코드 (빈 frozenset = greenfield 운송 없음)
[x] existing_trunk_cells ⊆ { c.coord for c in existing_transport_cells } (trunk인데 운송 kind가 없는 coord 금지)
[x] `RouteGoalKind.existing_transport_attachment` 계열 goal은 `existing_transport_cells`의 kind와 모순되지 않는다
[x] protected_corridor_cells의 모든 coord는 route_domain 빌더 출력 키에 존재한다 (Phase 4)
[x] existing_trunk / protected 가 mineable 과 불가능한 중복이면 adapter가 명시 정책으로 해결한다
```

## 테스트

```text
test_optimization_input_preserves_inferred_fill_as_mineable
test_optimization_input_marks_rim_cells
test_optimization_input_route_goals_touch_external_void_or_trunk_contract
test_optimization_input_transport_removed_not_asteroid_evidence
test_optimization_input_topology_graph_adjacency_matches_neighbors4_server
test_optimization_input_existing_transport_sets_transport_mask_inputs
test_optimization_input_existing_transport_unique_coord
test_optimization_input_greenfield_is_empty_transport_and_trunk_and_protected
test_optimization_input_trunk_cells_subset_of_transport_cells
```

## 완료 조건

```text
[x] OptimizationInput DTO 구현 (route_goals·topology_graph·existing_transport_cells·trunk·protected 포함)
[x] Reconstruction → OptimizationInput adapter + **RouteDomainSnapshotBuilder** 시드 경로 (개발 시퀀스 1B와 동일 범위)
[x] Server 밀집 이웃(`neighbors4_server`) 테스트 통과
[x] hole asteroid 등 topology 어댑터 검증은 시퀀스 1B 완료 기준(개발 시퀀스 10)으로 분리
```

## 구현 계약 — 문자열 대신 enum

다음 값은 **자유 문자열이 아니라 enum**으로 고정한다. 문서의 텍스트 목록(Phase 3·4·8)은 멤버 이름과 동일하게 유지한다.

```text
RouteGoalKind
RouteProbeFailureReason
CandidateRejectReason
ValidationIssueCode
ValidationSeverity
EvolutionConvergenceReason
CommitConflictReason
OptimizationReplayEventType
ReservationState
PlacementCommitState
TransportMask
RouteClass
```

Phase 4·6·7·9 문서가 각 타입·enum의 정본이다. Phase 1은 **자유 문자열 금지** 원칙과 교차 참조만 유지한다.
