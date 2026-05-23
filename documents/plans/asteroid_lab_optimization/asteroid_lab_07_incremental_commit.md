# Phase 7 — Incremental Route Commit


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../../Algorithm/asteroid_lab_07_incremental_commit.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

## 목적

Evolutionary search가 선택한 best genome을 실제 layout candidate로 확정한다.

## 핵심 원칙

```text
Everything is provisional until connected to exterior trunk.
```

## 흐름

```text
best genome
→ candidate commit_order 순
→ re-run route probe (commit 시점 domain·reservation 반영)
→ reserve path
→ detect conflict
→ commit route + **route_domain 전면 재빌드(RouteDomainSnapshotBuilder)**
→ promote placement
→ rollback failed candidate
```

## Incremental commit 동작 (`commit_best_genome`)

```text
1) 각 candidate 처리 직전에 `RouteDomainSnapshotBuilder.build_snapshot(...)`로
   route_domain을 새로 만든다 (confirmed_reservations·committed_occupied_cells 반영).
2) candidate 생성 단계의 `BundleCandidate.route_probe_result`는 참고용일 뿐이며,
   commit 루프의 최종 증명이 아니다.
3) 각 commit 후보는 **항상 그 시점의 최신 route_domain**으로 `run_route_probe`를 다시 돌린다.
4) commit 성공 시 해당 예약 경로는 동일 `transport_kind`에 대해 trunk·preferred로 승격되고,
   다른 kind는 `transport_mask` 등으로 차단·제한된다 (`RouteDomainSnapshotBuilder.build_snapshot` 오버레이).
5) 확정된 placement의 `occupied_cells`는 이후 스냅샷에서 `hard_blocked`로 반영된다.
```

commit 코드는 `RouteCellDomain`을 **제자리(in-place) 패치하지 않는다**. 스냅샷은 빌더가 새 `dict[Coord, RouteCellDomain]`로 돌려준다.

## commit_order 출처 (greedy 순서 누수 방지)

실제 확정 순서는 **선택된 genome의 `Gene.commit_order`** 만이 정본이다. 기본값으로 다음을 **commit 순서로 쓰면 안 된다**.

```text
rim 스캔 순
candidate 생성·enumeration 순
좌표 lex 순 (단독 정본)
```

위는 **동률 tie-break** 등 문서화된 예외에서만 보조 키로 쓰고, 그 외에는 genome에 명시된 `commit_order`를 따른다. 그렇지 않으면 candidate 생성 순서가 사실상 **greedy 설치 순서**로 새어 들어간다.

## 상태

```python
class PlacementCommitState(Enum):
    PROVISIONAL = "provisional"
    FEASIBLE = "feasible"
    ROUTED = "routed"
    CONFIRMED = "confirmed"
    ROLLED_BACK = "rolled_back"
```

### 상태 전이 (v0)

```text
PROVISIONAL -> FEASIBLE: 후보가 commit 시도 큐에 올라 평가 대상이 됨
FEASIBLE -> ROUTED: 재-probe 성공 + RouteReservation 생성
ROUTED -> CONFIRMED: reservation·**route_domain 스냅샷**·점유 맵이 원자적으로 반영됨(구현은 단일 트랜잭션 또는 동등한 롤백 가능 단위)
FEASIBLE -> ROLLED_BACK: 재-probe 실패 또는 예비 검증 실패
ROUTED -> ROLLED_BACK: reservation 충돌·정책 위반으로 커밋 중단
CONFIRMED -> ROLLED_BACK: v0에서는 금지 (전체 트랜잭션 abort만 허용)
```

`CONFIRMED` 이후 단일 candidate만 롤백하는 요구가 생기면 v1 플랜에서 별도 트랜잭션 모델을 연다.

## Recovery budget (thrashing 상한)

corridor carve·rollback·재-probe 반복은 **무한 루프**로 이어질 수 있다. v0는 아래 **상한 DTO**를 두고 초과 시 `CommitConflictReason`·`ROLLED_BACK` 등으로 종료한다 (값은 `EvolutionConfig`와 분리 가능).

```python
@dataclass(frozen=True)
class RecoveryBudget:
    max_removed_candidates: int
    max_carve_cells: int
    max_reroute_attempts: int
```

## 예약(reservation) 상태

```python
class ReservationState(Enum):
    PROVISIONAL = "provisional"
    CONFIRMED = "confirmed"
    RELEASED = "released"
```

## Route domain transition (replay·debug 최소 계약)

`frozenset[Coord]`만으로는 **왜 blocked/preferred가 바뀌었는지** 복구하기 어렵다. 각 예약은 적용된 셀에 대해 **최소 before/after**를 남긴다.

```python
@dataclass(frozen=True)
class RouteDomainCellTransition:
    coord: Coord
    route_class_before: RouteClass
    route_class_after: RouteClass
```

`RouteClass`는 Phase 4 `RouteCellDomain.route_class`와 동일 enum·의미를 쓴다. hard_blocked·mask·비용 변화까지 전부 넣지 않아도 되나, **v0는 위 두 필드 이상을 잘리지 않게** 직렬화한다.

## Route Reservation

```python
@dataclass(frozen=True)
class RouteReservation:
    reservation_id: str
    candidate_id: str
    transport_kind: TransportKind
    path: tuple[Coord, ...]
    reserved_cells: frozenset[Coord]
    cost: int
    reached_goal: RouteGoal
    goal_priority: int
    reservation_state: ReservationState
    domain_cell_transitions: tuple[RouteDomainCellTransition, ...]
```

- `reservation_id`: Phase 8 `ValidationIssue.route_reservation_id`와 **동일 문자열**을 쓴다. **UUID 금지.** v0 정본 예: `f"{candidate_id}:route:{ordinal}"` — `ordinal`은 한 번의 incremental commit 패스 안에서 **0부터 증가**하는 정수(결정적).
- `reached_goal` / `goal_priority`: trunk·margin·attachment 구분·validation·replay에 필요 (Phase 4 `RouteProbeResult`와 모순 없게 복사).
- `domain_cell_transitions`: 해당 commit으로 **달라진** `RouteCellDomain.route_class`만 기록하면 된다(변화 없는 coord는 생략). 빌더가 전면 재빌드하더라도, **디버그·replay는 이 튜플로 “무엇이 바뀌었는지”를 복원**할 수 있어야 한다.
- `reservation_state`: commit 단계에서 provisional vs confirmed 구분.

**폐기:** `reserved_domain_delta: frozenset[Coord]`만 두는 형태는 디버그 유용성이 부족하므로 본 문서에서는 **정본에서 제외**한다.

## Commit 후 `route_domain`·trunk 갱신 계약 (P0)

commit이 **성공(CONFIRMED)** 하면:

```text
1) 해당 transport_kind에 대해 reserved path 셀은 이후 candidate의 probe에서
   동일 kind의 trunk·preferred 영역으로 취급되거나, 정책상 허용 통로로 남는다.
2) 다른 transport_kind 후보에 대해서는 동일 셀이 blocked·높은 비용·mask 불일치로 반영될 수 있다.
3) 다음 candidate의 RouteProbeInput.route_domain은 **이전까지 CONFIRMED된
   reservation + placement occupied**를 반영해 재빌드된다.
```

이 계약이 없으면 candidate 단계 “reachable”과 최종 commit 충돌이 **다시 분리**된다. Phase 3의 즉시 probe는 **그 시점 스냅샷**이고, commit 루프 안에서는 **항상 최신 domain**으로 재-probe한다.

## RouteDomainSnapshotBuilder — route_domain 스냅샷 정본 API

Algorithm 정본과 동일 — [`asteroid_lab_07_incremental_commit.md`](../../Algorithm/asteroid_lab_07_incremental_commit.md) §RouteDomainSnapshotBuilder API 표 참조. 요약: `build_snapshot` 정본; `build_commit_snapshot`은 선택 deprecated wrapper(별도 semantics 금지); 구현 `commit_selected_candidates`.

## `blocked_cells` vs `protected_corridor_cells` (의미 분리)

- **`blocked_cells`** (`OptimizationInput`): 일반 **hard no-go** 셀 집합.  
  - commit 경로 검사(`incremental_commit._path_conflict_reason`)에서 경로가 `blocked_cells`와 교차하면 **`CommitConflictReason.HARD_BLOCKED_CONFLICT`** (`"hard_blocked_conflict"`).
- **`protected_corridor_cells`**: 보호·정책 민감 **복도** 셀.  
  - **정책 위반**으로 commit을 거절할 때는 **`HARD_PROTECTED_CONFLICT`** (`"hard_protected_conflict"`)를 쓴다 (일반 hard no-go와 구분).  
  - 복도를 **허용된 통로**로 통과·비용·mask 제어하는 것은 `RouteDomainSnapshotBuilder` / `RouteCellDomain` 정책(시드·오버레이)의 책임이며, `blocked_cells`와 동일 취급하지 않는다.

## Conflict

충돌 사유는 **`CommitConflictReason` StrEnum** 과 1:1 (자유 문자열 금지).

```python
from enum import StrEnum


class CommitConflictReason(StrEnum):
    OCCUPIED_CELL_CONFLICT = "occupied_cell_conflict"
    ROUTE_CELL_CONFLICT = "route_cell_conflict"
    TRANSPORT_KIND_CONFLICT = "transport_kind_conflict"
    HARD_BLOCKED_CONFLICT = "hard_blocked_conflict"
    HARD_PROTECTED_CONFLICT = "hard_protected_conflict"
    TRUNK_DEADLOCK = "trunk_deadlock"
    ROUTE_PROBE_FAILED = "route_probe_failed"
```

문서·테스트의 코드 문자열은 멤버 이름과 동일하게 유지한다.

## Rollback

candidate가 commit 실패하면 해당 candidate만 rollback한다.

다른 confirmed candidate는 건드리지 않는다.

## Invariant

```text
[ ] confirmed placement must have connected route (재-probe 성공 스냅샷)
[ ] failed commit must not mutate confirmed routes
[ ] shape belt and fluid pipe reservations are separated
[ ] route reservation does not occupy extractor/extension cells
[ ] rollback is local and reversible
[ ] RouteReservation.reservation_id가 Phase 8 route_reservation_id와 동일 규칙으로 생성된다
[ ] CONFIRMED 후 route_domain 재빌드가 후속 probe 입력에 반영된다
[ ] commit 시도 순서는 선택 genome의 `Gene.commit_order` 정본 (rim 스캔·candidate 생성 순을 기본 commit 순서로 쓰지 않음)
[ ] reserved_cells 집합이 path와 모순 없이 동기화된다 (Validation Phase 8 교차)
[ ] domain_cell_transitions의 각 원소가 RouteClass 계약과 모순 없다 (빈 튜플은 “route_class 변경 없음”을 의미할 수 있음)
[ ] RecoveryBudget 초과 시 thrashing이 무한 반복되지 않는다
[ ] `blocked_cells` 경로 교차는 `HARD_BLOCKED_CONFLICT`, 보호 복도 **정책 위반**은 `HARD_PROTECTED_CONFLICT`로 구분한다 (의미 혼선 금지)
```

## 테스트

`tests/unit/asteroid_lab/test_incremental_commit.py`:

```text
test_incremental_commit_confirms_connected_candidate
test_incremental_commit_rolls_back_unreachable_candidate
test_incremental_commit_does_not_mutate_existing_confirmed_routes
test_incremental_commit_transport_kind_conflict
test_incremental_commit_route_reservation_excludes_occupied_cells
test_incremental_commit_route_domain_reflects_prior_reservations
test_incremental_commit_reservation_id_deterministic
test_incremental_commit_uses_gene_commit_order_not_candidate_id
test_incremental_commit_reprobes_latest_route_domain
test_incremental_commit_failed_candidate_does_not_remove_prior_confirmed
test_incremental_commit_reserved_cells_match_path
test_incremental_commit_domain_cell_transitions_serialized
test_incremental_commit_conflict_reason_enum_only
test_incremental_commit_shape_and_fluid_domains_separated
test_incremental_commit_confirmed_occupied_cells_become_hard_blocked
test_incremental_commit_recovery_budget_exceeded
test_incremental_commit_route_cell_conflict
test_incremental_commit_hard_blocked_conflict
test_incremental_commit_occupied_cell_conflict_on_path
```

- **`HARD_BLOCKED_CONFLICT`**: `test_incremental_commit_hard_blocked_conflict`
- **`build_snapshot` 단일 진입**: `commit_selected_candidates` → `build_snapshot` only. `test_incremental_commit_reprobes_latest_domain` 등 — Algorithm 정본 참조.

본 문서 범위는 Sequence 6 incremental commit 계약 동기화이며, **Sequence 7 validation (`ValidationIssueCode` 등) 구현·UI·CP-SAT·replay·recovery 로직은 추가하지 않는다.**

## 완료 조건

```text
[ ] best genome commit pipeline 구현
[ ] RouteReservation (reservation_id·reached_goal·goal_priority·state·domain_cell_transitions) 구현
[ ] RecoveryBudget 계약 및 초과 시 종료 경로
[ ] CommitConflictReason StrEnum (`HARD_BLOCKED_CONFLICT`·`HARD_PROTECTED_CONFLICT` 등)
[ ] commit 후 route_domain 갱신 계약 구현·테스트
[ ] commit 시도 순서가 genome `Gene.commit_order` 정본(생성·rim 순 기본값 아님)
[ ] local rollback 구현
[ ] confirmed route invariant 테스트 통과
```
