# 08 — STEP 4: Merge-aware routing (§9, P2)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 07

---

## 9. STEP 4 — Merge-Aware Capacity-Aware Routing

### 9.1 목적

모든 extractor output stub를 소행성 외부 trunk와 연결한다.

```text
extractor
→ output stub
→ local route
→ merge-aware trunk
→ exterior margin
```

**설계 정본(Transport)**: 그리드 **Dijkstra** 기본 가중치·밀집 가산·**output당 stub 1개**·**외부 trunk merge**·**output 방향 회전**(다방향 void 시 후보별 최소 비용 비교)은 [`01_project_overview.md`](./01_project_overview.md) §3.5와 동일하다. STEP 4는 그 위에 본 절의 merge-aware goal set·capacity 제약을 얹는다.

---

### 9.2 Trunk seed 정의

```text
trunk_seed = 여러 output route가 합류할 수 있는 초기 연결 후보 셀 또는 셀 집합
```

trunk seed 후보는 다음에서 생성한다.

```text
1. external margin에 인접하거나 margin 바깥에 있는 candidate exit cells
2. Pass1/Pass2 output stub들이 공통으로 접근하기 쉬운 boundary ring cells
3. 기존 blueprint에서 보존 가능한 같은 TransportKind trunk cells
4. RouteZone cost가 낮고 capacity 확장이 가능한 boundary / outside cells
```

#### 9.2.1 `ExistingLayoutAnalysis`가 있을 때 trunk seed·cleanup 후보

STEP 0.5 [`ExistingLayoutAnalysis`](./03_data_schema_dto.md)가 `SolverRunContext` 등에 실려 있으면, **같은 TransportKind**에 한해 trunk seed 후보에 다음을 **추가**한다.

```text
- main_transport_component의 cells (main_trunk_candidate)
- touches_external_margin == true 인 동일 kind component (정책상 trunk 후보로 쓸 때만)
- source_kind == existing_fluid_layout 이면 SpacePipe 기반 main component만 FLUID_PIPE trunk seed 후보로 사용
```

**trunk seed로 승격하지 않는 것**:

```text
- orphan_component
- single_cell_artifact
```

**파생 집합(정본, DTO와 동일 의미)**:

```python
if existing_layout.transport.main_component_id is not None:
    trunk_seed_candidates |= main_component.cells

for component in existing_layout.transport.components:
    if component.status in {"orphan_component", "single_cell_artifact"}:
        cleanup_candidates |= component.cells
```

**정책 문장**:

```text
기존 pipe/belt라고 해서 전부 trunk seed가 아니다.
main component만 trunk seed 후보로 올릴 수 있다.
orphan component는 cleanup / reroute 후보다.
```

trunk seed가 아닌 것:

```text
- 모든 output stub의 단순 집합
- cheap_transport_escape_exists()가 사용한 임시 path
- belt와 pipe가 섞인 mixed trunk
```

trunk seed와 **route goal set**은 역할이 다르다.

```text
- trunk_seed: merge가 일어날 수 있는 후보 좌표(탐색 힌트·중립 연결점).
- route goal set: 단일 목적지가 아니라 “도달하면 성공인 셀 집합”.
```

첫 번째 extractor를 라우팅할 때는 **existing trunk cells가 비어 있다**. 이 경우 goal set은 `exterior margin cells ∪ trunk_seed_candidates`(해당 output의 TransportKind에 맞는 것만)로 둔다. 첫 route가 commit되면 그 결과 trunk 경로·merge 지점이 **existing trunk**로 승격되고, 이후 bundle은 기존 문장대로 `existing trunk cells + exterior margin`을 goal로 사용한다.

첫 route가 **commit되지 않고** `QUARANTINED_UNROUTED` 또는 `ROLLED_BACK`으로 끝나면 **existing trunk 승격은 발생하지 않는다**. `trunk_seed_candidates`·exterior margin 기반 goal set 구성은 유지되며, 이후 extractor 라우팅도 동일 규칙(빈 trunk일 때의 goal set)을 따른다.

---

### 9.3 Routing과 Merge의 내부 순서

```text
1. trunk seed 후보 생성
2. route goal set 구성 (§9.2 trunk seed와의 관계 참고):
   - existing trunk가 비어 있으면 exterior margin ∪ trunk_seed_candidates
   - 이후에는 existing trunk cells + exterior margin cells
3. extractor bundle을 priority 순서로 정렬
   - 동점 해소(위에서 아래 순): cheap_escape/외부 도달 예상 비용 ↓,
     stub에서 exterior margin까지 맨하탄 거리 ↓, bundle slot 수(생산량) ↑ (큰 bundle이 trunk 선점),
     Pass1 출처 bundle을 Pass2보다 우선, 같은 pass 내에서는 안정 정렬(스캔 인덱스 등)
4. 각 output stub에서 가장 좋은 merge target 또는 exterior target까지 route 탐색
5. route commit 시 trunk load와 capacity를 즉시 갱신
6. capacity 초과 시 alternate trunk, split route, additional trunk 후보를 탐색
7. 모든 route가 connected + capacity-safe이면 STEP 4 성공
```

priority 순서는 라우팅 선점 효과가 있으므로, 구현은 위 튜플을 **고정**하고 trace에 사용한 키를 남긴다.

즉, 기본 전략은 다음이다.

```text
Routing 후 Merge가 아니라,
Merge-aware Routing을 우선한다.
```

---

### 9.4 Capacity와 누적 합산(1차 우선)

[`01_project_overview.md`](./01_project_overview.md) §3.6에 따라 **1차(우선)** STEP 4에서는 **lane·pipe max capacity(rated 상한)와의 비교를 하지 않고**, trunk·edge별 **upstream 출하량 합산(총합)** 만 계산·trace한다.

**후속(선택)**: 아래 **trunk capacity 초과 없음** 등을 hard constraint로 켜면, commit·recovery에서 overflow를 처리한다.

용량 검증을 **완전히 생략**한 채 STEP 9만 두면 문제가 늦게 드러날 수 있으므로, **후속 단계에서 capacity를 켤 때**에는 STEP 4에서 즉시 처리하는 편이 낫다.

```text
route candidate commit 조건(1차 — geometry·연결성):
- geometry valid
- output stub connected
- target trunk 또는 exterior connected
- transport kind 일치
- trunk_load 합산 필드 갱신(총량만; max capacity 미검사)

route candidate commit 조건(후속 — capacity 검증 활성 시 추가):
- trunk capacity 초과 없음
- capacity 초과 시 split/additional trunk 대안 존재
```

Final validation은 **후속 단계에서 capacity 검증을 켠 경우**에만 capacity를 assertion gate로 다시 확인한다(1차만 구현이면 합산·연결성 중심으로 완화).

---

### 9.5 Transport kind별 routing

```text
shape extractor output → TransportKind.SHAPE_BELT route만 허용
fluid extractor output → TransportKind.FLUID_PIPE route만 허용
```

서로 다른 transport kind는 같은 trunk로 merge하지 않는다.

```text
1차: belt/pipe trunk_load는 §3.6에 따라 **누적 합(총량)** 만 갱신한다(max capacity 미검사).
후속: 동일 필드에 대해 rated capacity·overflow 판단을 붙일 수 있다.
```

---

### 9.6 Pass1 / Pass2 placement commit과 STEP 4 실패

```text
- Pass2에서 placement-only commit은 route 확정 전이므로 아래 PlacementCommitState를 명시적으로 탄다.
- Pass1 placement도 STEP 4에서 라우팅·**(후속)** capacity 실패 시 동일하게 rollback·quarantine의 대상이 될 수 있다.
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

**Stub가 이미 external trunk에 포함된 경우:** 해당 stub 셀은 같은 transport kind의 trunk로 **이미 외부까지 연결된 것으로 확정**된다. STEP4에서는 별도 Dijkstra 확장 없이 **no-op route commit**(예: path를 stub 단일 셀로 기록)으로 `PROVISIONAL_PLACED` → `ROUTED_CONFIRMED` 승격할 수 있다. 이는 처리 규칙 2의 “output route와 capacity가 확정”과 **동일 의미의 최적화**다(탐색 생략 ≠ 규칙 위반).

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

---

### 9.7 구현 스펙 범위(백지 전제)

STEP 4 routing은 **최소 목표인 “외부로 연결되는가”만으로는 부족**하다. 다음을 **동시에** 다루는 설계를 전제로 한다(구현 백지: `01_project_overview.md` §0).

```text
- 연결성
- route 길이
- 내부 transport cell 수
- mineable candidate 점유 손실
- trunk merge 가능성
- throughput/capacity
- 회전 수
- congestion
```

---

## 9.6 State authority · 필드 의미 (Pass3 게이트·종료 tier)

NDJSON/요약에서 **서로 다른 소스**를 섞으면 `step4_committed` 오판 같은 회귀가 난다. 아래를 정본으로 한다.

### `step4_state_source` (트레이스)

| 키 | 의미 |
|----|------|
| `committed_from` | **`Step4RoutingResult`** — STEP4 라우팅 결과 객체가 권위다. |
| `pass3_gate_source` | **`explicit_arg`** — Pass3는 `trunk_load.get("step4_committed", default)`로 추론하지 않는다. |
| `trunk_load_mirrors_result` | `trunk_load["step4_committed"]`는 결과와 동일 값을 **복제**할 뿐, 추론 근거가 아니다. |

### 필드 의미 표

| 필드 | 의미 |
|------|------|
| `step4.committed` / `complete_routing_success` | 라우팅 실패 0·비복구 0·**롤백된 placement 0**인 완전 성공. |
| `step4.degraded` | 실패 레코드는 없으나 **P2-C cascade 등으로 롤백만** 발생한 부분 성공 힌트. |
| `layout_ok` | 최종 맵에 대해 `geometry_valid ∧ connectivity_valid` (원본 `report`). |
| `termination.tier` | 상위 계약용 등급 (`SUCCESS` / `PARTIAL_SUCCESS` / `SOLVER_FAILURE`). |
| `geometry_valid` (summary) | `report.geometry_valid ∧` (최종 맵 기준) **unfinalized 행 0** — `finalize`는 맵의 provisional/quarantined 행 합과 정렬한다. |
| `connectivity_valid` | stub→external·orphan transport 불변식 통과. |

`quarantined_placement_ids_peak`는 격리 직후·터미널 롤백 전 피크 ID를 보존한다(디버그·계약).

---

## 부록: P2 체크리스트 (원문 §20)

### P2 — Merge-Aware Capacity-Aware Routing 구현

```text
[ ] TransportKind enum 추가
[ ] trunk seed 정의 및 후보 생성
[ ] goal set = existing trunk + exterior margin 구성
[ ] fixed output stub를 route start point로 고정
[ ] route commit 시 trunk_load 갱신
[ ] capacity overflow 시 split/additional trunk 시도
[ ] belt/pipe merge 분리
[ ] merge_partial_failure 감지
[ ] PROVISIONAL_PLACED → ROUTED_CONFIRMED / QUARANTINED_UNROUTED / ROLLED_BACK 상태 전이 구현
```
