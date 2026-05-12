# 03 — 데이터 스키마 · DTO

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 01, 02

> TransportKind, PlacementCommitState FSM, RouteZone·DTO 초안(§19.1), **Existing layout analysis(§E · STEP 0.5)**.

---

## A. TransportKind (§3.6 발췌)

수치·누적 유량 규칙의 정본은 [`01_project_overview.md`](./01_project_overview.md) §3.4·§3.6.

### 3.6 Belt vs Pipe 구분

belt와 pipe는 같은 `transport`로 뭉뚱그리면 안 된다.

```text
TransportKind.SHAPE_BELT
TransportKind.FLUID_PIPE
```

| 항목                  |                                     Belt |              Pipe |
| ------------------- | ---------------------------------------: | ----------------: |
| 대상                  |                           shape resource |    fluid resource |
| capacity (참고)     | **2 items/s per lane**; Space belt **12 lanes** → 합산 **24 items/s** 규모(1차 계산에서는 **상한 비교 없이** 참고값으로만 쓴다) | Space pipe **7,200 L/min**; 펌프 세트(4기) **1,800 L/min**(동일) |
| route geometry cost |                        RouteZone cost 사용 | RouteZone cost 사용 |
| **1차** 합산·constraint | **max capacity 무시**, edge·lane마다 **누적 합만** 산출·trace | 동일 |
| **후속** capacity 검증 | (선택) 누적 합 ≤ rated **max capacity**·overflow 분기 | 동일 |
| 누적 유량             | 구간(edge)·lane마다 upstream **합산 총량** 유지, 외부까지 전파 | 동일 |
| merge 가능 대상         |                              belt trunk만 |       pipe trunk만 |
| 서로 merge 가능 여부      |                                       불가 |                불가 |

RouteZone cost는 동일한 공간 비용 모델을 공유할 수 있지만, **merge / trunk topology** 판단은 transport kind별로 분리한다. **누적 합** 필드는 kind별 단위(items/s 또는 L/min)로 저장한다. **max capacity 대비 overflow**는 **1차 범위 밖**(후속 단계·플래그)으로 둔다.

---

## B. PlacementCommitState FSM (§9.6 발췌)

### 9.6 Pass1 / Pass2 placement commit과 STEP 4 실패

```text
- Pass2에서 placement-only commit은 route 확정 전이므로 아래 PlacementCommitState를 명시적으로 탄다.
- Pass1 placement도 STEP 4에서 라우팅·capacity 실패 시 동일하게 rollback·quarantine의 대상이 될 수 있다.
  구현은 Pass1/Pass2를 구분하는 `placement_pass` 태그만 두고 동일 enum을 쓰거나, 별도 타입으로 분리한다.
- Pass1 시점에는 아직 STEP 4 전이므로, 상태 의미상 Pass2의 PROVISIONAL_PLACED와 동일하게 “routing 미확정 배치”로 취급한다.
```

Pass2에서 placement는 route 확정 전의 provisional commit이다. STEP 4에서 route를 만들지 못하면 해당 placement는 유효하지 않다.

```text
PlacementCommitState:
- PROVISIONAL_PLACED
- ROUTED_CONFIRMED
- QUARANTINED_UNROUTED
- ROLLED_BACK
```

**상태 전이(FSM, 정본)**

```text
PROVISIONAL_PLACED
  → ROUTED_CONFIRMED      (STEP 4 routing·capacity 성공, route commit)
  → QUARANTINED_UNROUTED  (STEP 4 routing 실패 등 — 유지 가능 상태)
  → ROLLED_BACK           (recovery 실패 또는 명시적 rollback)

QUARANTINED_UNROUTED
  → ROUTED_CONFIRMED      (recovery 성공)
  → ROLLED_BACK           (recovery 실패)

ROLLED_BACK               (terminal — 동일 placement 재사용·candidate 풀 재진입 금지)
ROUTED_CONFIRMED          (terminal — placement 단위로는 정상 확정; §9.6 처리 규칙·route 재검증 참고)
```

**Placement 상태 vs route 자원**: `ROUTED_CONFIRMED`는 **해당 placement의 라우팅 성공 확정**을 뜻한다. 인접 placement가 `ROLLED_BACK`되어 **이미 commit된 route가 점유하던 셀이 해제·차단 집합에서 빠지는** 등으로, 그 route가 더 이상 유효한 geometry·연결성을 만족하지 않으면 **route 단위 재검증·corrective reroute 또는 `cascade_corrective_recovery`**가 여전히 필요하다. “cascade 보정 대상에서 제외”는 **동일 placement를 다시 quarantine 대상으로 흔들지 않는다**는 의미이지, **고아·파손 route segment를 방치**한다는 뜻이 아니다.

처리 규칙:

```text
1. Pass2 commit 직후 placement는 PROVISIONAL_PLACED 상태다.
2. STEP 4에서 output route와 capacity가 확정되면 ROUTED_CONFIRMED가 된다.
3. STEP 4 routing 실패 시 해당 placement는 QUARANTINED_UNROUTED로 이동한다.
4. recovery가 성공하면 ROUTED_CONFIRMED로 승격한다.
5. recovery가 실패하면 ROLLED_BACK 처리하고 occupied cells를 해제한다.
6. Final validation에는 QUARANTINED_UNROUTED placement가 남아 있으면 안 된다.
7. ROLLED_BACK 또는 placement 해제 후 **연결성·geometry 재검증**: 다른 placement/route가 해제된 셀을
   waypoint·blocked 가정으로 사용했는지 확인한다. 연결이 깨지면 해당 route를 대상으로
   최소 corrective reroute 또는 **cascade_corrective_recovery**(§13.3)를 호출한다.
   overlap 제거는 deterministic tie-break로 하며 무작위 삭제는 금지한다.
8. 단순히 경로가 비효율적으로 남는 경우(더 짧은 우회가 생김)는 필수 수정 대상이 아니며,
   trace에 `suboptimal_route_after_neighbor_rollback` 등으로 기록할 수 있다.
```

cascade 보정은 Final validation의 `validation_recovery`와 **다른 컨텍스트**다. 시도 한도는 `MAX_CASCADE_CORRECTIVE_ATTEMPTS`(§4.2)이며 `MAX_TOTAL_RECOVERY_ATTEMPTS`와 별도 집계한다.

**`cascade_corrective_recovery` vs `validation_recovery`**

```text
- cascade_corrective_recovery: STEP 4 처리 중·직후 placement rollback으로 연결성·geometry가 깨진 경우에만 진입(§13.3).
- validation_recovery: STEP 9에서 hard invariant가 깨졌을 때만 진입; STEP 4 본 파이프라인 자동 재진입 없음.
- cascade가 성공하면 해당 rollback 직후 보정 시도는 종료된 것으로 본다. 이후 파이프라인을 진행해 STEP 9에 도달했을 때
  **새로** 드러난 불변 조건 위반은 별도 시도로 validation_recovery를 트리거할 수 있다(attempt 카운터 분리, §4.2).
  “동일 버그가 두 번”이 이상 징후면 구현·trace에서 원인 분석 대상이다.
```

`rejected_by_no_replacement_route`: **commit_reason이 아니다.** replacement route 확보 없이 corridor/셀을 비우려 할 때의 **route reject 사유**이며, 동일 결정이 placement 제거로 이어지면 **`rollback_reason`(또는 `rejected_reason`)**에 기록한다. `commit_reason`은 **성공 커밋 분류만** 담는다(§13.5).


## C. RouteZone 및 Transport kind별 cost (§11.1–§11.2 발췌)

**§3.5 설계 정본과의 관계**: 그리드 셀 단위 **Dijkstra** 기본 가중치·밀집 가산·output/stub/merge 정책은 [`01_project_overview.md`](./01_project_overview.md) §3.5가 정본이다(§0 구현 백지와 무관). **RouteZone 기본 cost 수치**는 아래 §11.1 표가 정본이며, Pass3 구현 시 §3.5 셀 비용과 단일 소스로 환산·정렬한다.

## 11. Pass3 Route Cost Model

### 11.1 Route Zone 정의

| Zone                 | 의미                          | 기본 cost |
| -------------------- | --------------------------- | ------: |
| OUTSIDE              | 소행성 bbox 밖                  |       1 |
| BOUNDARY_VOID        | 소행성 외곽 / boundary ring      |       5 |
| INTERNAL_VOID        | 소행성 내부 빈 공간                 |      50 |
| FILLABLE_INTERIOR    | 내부 배치 가능성이 높은 공간            |     150 |
| PLACEMENT_CANDIDATE  | extractor/extension 후보 셀    |     400 |
| PLACEMENT_OCCUPIED   | extractor/extension 점유 셀    |     900 |
| BLOCKED              | extractor으로 경로 관통 불가한 점유 셀 |     INF |

---

### 11.2 Transport kind별 cost override

기본 RouteZone cost는 공유하되, transport kind별 보정값을 둘 수 있다.

```python
route_cost = ROUTE_ZONE_COST[zone] * KIND_COST_MULTIPLIER[transport_kind]
```

초기값:

```python
KIND_COST_MULTIPLIER = {
    TransportKind.SHAPE_BELT: 1.0,
    TransportKind.FLUID_PIPE: 1.0,
}
```

초기에는 동일하게 두되, capacity / merge / load 계산은 반드시 kind별로 분리한다.

---

## D. SolverRunContext · Pass 결과 DTO (§19.1)

### 19.1 내부 DTO 스키마 초안 (`SolverRunContext` · Pass 결과)

구현체는 필드를 추가할 수 있으나, 아래는 trace·replay와 매핑할 **최소 공통 구조**다.

```yaml
SolverRunContext:
  run_id: string
  asteroid_signature: string | null        # 재현용 입력 해시 등
  limits:
    max_reclaim_iterations: int
    max_post_reclaim_pass3_reruns: int      # 소행성 1 solve 전체(§4.2)
    max_total_recovery_attempts: int
    max_validation_recovery_attempts: int
    max_cascade_corrective_attempts: int
    default_reclaim_gain_ratio_threshold: float
  reconstruction:
    mineable_placement_cells: list[tuple[int, int]]   # 정본: 격자 (row, col) 정수 튜플; trace 직렬화는 [row,col] 등 합의 포맷
    extraction_shell_cells: list[tuple[int, int]]
    full_barrier_cells: list[tuple[int, int]]
  routing_state:
    trunk_seed_candidates: list[tuple[int, int]]   # reconstruction과 동일 (row, col) 정본
    existing_trunk_cells_by_kind: dict      # TransportKind -> cells
    fixed_output_stub_by_extractor: dict
    final_route_cells: list
    hard_protected_corridors: list
    soft_protected_corridors: list
  metrics_snapshot:
    internal_transport_count: int | null
    baseline_internal_transport_at_reclaim_entry: int | null
    optimization_baseline_internal_transport: int | null   # §15.4; 계산 시점 trace에 명시
  placement_commit_by_id: dict             # placement_id -> PlacementCommitState
  termination: SUCCESS | PARTIAL_SUCCESS | SOLVER_FAILURE | null

Pass1Result:
  placements: list                         # extractor/extension/stub 엔티티
  occupied_cells: list
  beam_trace: list[object] | null        # Pass1 replay용 선택 필드; 비어 있으면 UI에서 beam 단계 생략 가능
  # beam_trace 최소 원소 권장(각 행 = 한 후보 또는 beam 레벨 스냅샷):
  #   beam_level: int
  #   candidate_rank: int
  #   bundle_score: float
  #   placement_ids: list[string]
  #   selected: bool
  #   reject_reason: string | null

Pass2Result:
  provisional_placements: list             # PROVISIONAL_PLACED 후보
  blocked_cells_delta: list

RoutingResult:
  routes_by_extractor: dict
  trunk_load: dict                         # 1차: edge·lane별 누적 합만(§3.6); max capacity 비교는 후속·선택
  routing_failures: list[object] | null   # 원소당 최소 필드(직렬화 시 키 고정):
  #   stub_cell: tuple[int, int]          # 해당 extractor의 fixed output stub (row, col)
  #   extractor_id: string | null
  #   recovery_trigger: string | null     # 연쇄 실패 시 상위 trigger
  #   attempt_count: int                  # 해당 stub·STEP에 대한 시도 횟수(또는 전역 partial)
  #   final_state: QUARANTINED_UNROUTED | ROLLED_BACK | failed | null
  #   last_error: string | null             # 용량·geometry·search_exhaust 등 요약

Pass3Result:
  routes_before: list | null               # 스냅샷 또는 route id
  routes_after: list | null
  internal_transport_saved: int | null

ReclaimResult:
  iterations_used: int
  commits: list
  rejects: list
  total_incremental_internal_transport_added: int

RecoveryResult:
  trigger: string | null
  context_chain: list[budget_recovery | terminal_overflow_recovery | merge_partial_failure
           | cascade_corrective_recovery | validation_recovery]   # trace·replay 정본: 한 recovery 세션당 1레코드, escalate 시 순서 append(길이≥1). 단일 컨텍스트면 길이 1.
  attempts_delta: int
```

---

## E. Existing layout analysis · `DecodedExistingLayoutContext` (STEP 0.5)

**정본 목적**: Shapez2 디코드 JSON이 **raw asteroid field**가 아니라 **이미 배치된 island blueprint**(예: `Layout_FluidMiner` + `SpacePipe_*`)인 경우를 구분하고, 이후 STEP 1·4·5·9·10이 공유하는 **읽기 전용 context**를 만든다.

**설계 문장**:

```text
Decoded existing layout은 reconstruction input이 아니라 solver context다.
```

이 절의 분석은 **배치를 변경하지 않는다**. Pass3 정책(보호·철거) **본문 구현**은 별도 단계이나 플랜에서 연결하되, 아래 **`ExistingLayoutSolverHints` 계약**은 선행 고정한다.

### E.1 `SourceKind`

```python
class SourceKind(str, Enum):
    RAW_ASTEROID_FIELD = "raw_asteroid_field"
    EXISTING_FLUID_LAYOUT = "existing_fluid_layout"
    EXISTING_SHAPE_LAYOUT = "existing_shape_layout"
    MIXED_EXISTING_LAYOUT = "mixed_existing_layout"
    UNKNOWN = "unknown"
```

### E.2 `BBox` · `Coord`

격자 좌표는 프로젝트 정본: **`x == 0` 열 없음**([`AGENTS.md`](../../../AGENTS.md) 블루프린트 좌표 전제). DTO에서 `Coord = tuple[int, int]` (블루프린트 X, Y).

### E.3 `ExistingLayoutAnalysis`

```python
@dataclass(frozen=True)
class ExistingLayoutAnalysis:
    source_kind: SourceKind
    island_bbox: BBox
    transport: ExistingTransportAnalysis
    equipment: ExistingEquipmentAnalysis
    issues: list[ExistingLayoutIssue]
    solver_hints: ExistingLayoutSolverHints
```

### E.4 `ExistingTransportAnalysis`

동일 kind 부분그래프에 대해 **기하학적 4-neighbor CC**(방향성 merger/splitter 유량 시뮬은 1차 범위 밖)를 전제로 한다.

```python
@dataclass(frozen=True)
class ExistingTransportAnalysis:
    transport_kind: Literal["shape_belt", "fluid_pipe"]  # 또는 TransportKind와 동기
    component_count: int
    main_component_id: int | None
    components: list[TransportComponentSummary]
    orphan_component_ids: list[int]
    single_cell_artifacts: list[Coord]
```

### E.5 `TransportComponentSummary`

```python
@dataclass(frozen=True)
class TransportComponentSummary:
    component_id: int
    kind: Literal["shape_belt", "fluid_pipe"]
    cells: frozenset[Coord]
    cell_count: int
    bbox: BBox
    touches_external_margin: bool
    status: Literal[
        "main_trunk_candidate",
        "orphan_component",
        "single_cell_artifact",
        "cleanup_candidate",
    ]
```

### E.6 `ExistingEquipmentAnalysis`

```python
@dataclass(frozen=True)
class ExistingEquipmentAnalysis:
    miner_count: int
    extension_count: int
    miners_without_adjacent_transport: list[Coord]
    miners_attached_to_orphan_transport: list[Coord]
    equipment_attachment: list[EquipmentTransportAttachment]
```

### E.7 `EquipmentTransportAttachment`

```python
@dataclass(frozen=True)
class EquipmentTransportAttachment:
    equipment_coord: Coord
    equipment_kind: Literal["fluid_miner", "shape_miner", "extension"]
    adjacent_transport_coords: list[Coord]
    adjacent_component_ids: list[int]
    attached_to_main_component: bool
```

### E.8 `ExistingLayoutIssue`

```python
@dataclass(frozen=True)
class ExistingLayoutIssue:
    code: Literal[
        "TRANSPORT_DISCONNECTED",
        "ORPHAN_TRANSPORT_COMPONENT",
        "SINGLE_CELL_TRANSPORT_ARTIFACT",
        "MINER_NO_ADJACENT_TRANSPORT",
        "MINER_ATTACHED_TO_ORPHAN_TRANSPORT",
        "SOURCE_KIND_AMBIGUOUS",
    ]
    severity: Literal["info", "warning", "error"]
    coords: list[Coord]
    component_ids: list[int]
    message: str
```

### E.9 `ExistingLayoutSolverHints`

STEP 4 trunk seed·STEP 5 cleanup 후보·recovery 힌트에 **파생 값만** 담는다. 필드 추가는 trace·replay와 함께 합의한다.

```python
@dataclass(frozen=True)
class ExistingLayoutSolverHints:
    trunk_seed_cell_union: frozenset[Coord]
    cleanup_candidate_cell_union: frozenset[Coord]
```

**파생 규칙(정본, [`08_step4_routing.md`](./08_step4_routing.md)와 정렬)**:

```text
- main_trunk_candidate(및 정책상 허용 시 touches_external_margin 동 kind component) → trunk_seed_cell_union 후보.
- orphan_component, single_cell_artifact → cleanup_candidate_cell_union.
```

### E.10 `DecodedExistingLayoutContext`

디코드 직후 solver 파이프라인에 실리는 **최소 래퍼**(구현체는 `run_id`·입력 해시 등을 추가 가능).

```python
@dataclass(frozen=True)
class DecodedExistingLayoutContext:
    analysis: ExistingLayoutAnalysis
```

### E.11 `SolverRunContext` 연동(권장 필드)

§19.1 `SolverRunContext`에 다음을 **선택적으로** 추가한다(구현 시).

```yaml
decoded_existing_layout: DecodedExistingLayoutContext | null
```

`reconstruction.mineable_placement_cells`와 **동일 키로 덮어쓰지 않는다.**

### E.12 공통 기하 함수(권장)

```text
compute_transport_components(cells, transport_kind) -> components
```

`ExistingLayoutAnalysis`와 STEP 9 최종 레이아웃 검사는 **시점이 다르므로** 동일 필드명으로 보고서를 섞지 않는다([`13_step9_validation.md`](./13_step9_validation.md) §15.5).
