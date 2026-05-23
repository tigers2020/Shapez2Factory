# Phase 8 — Final Validation


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_08_validation.md`](../../Algorithm/asteroid_lab_08_validation.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

## 목적

최종 layout이 solver contract를 만족하는지 assert한다.

## 계약 (금지, read-only)

아래는 **검증 단계가 절대 하지 않는 것**이다. 위반 시 검증이 아니라 **다른 시퀀스**(candidate·probe·commit·recovery·수동 편집)의 책임이다.

```text
Validation must not invent new routes.
Validation must not mutate placement.
Validation must not fix topology.
```

- **새 route 금지**: `run_route_probe`로 경로를 새로 찾거나, 없던 예약을 만들어 채우지 않는다. 이미 확정된 `RouteReservation`·배치·`TopologyGraph`만 **읽어** 일관성을 검사한다.
- **placement 변이 금지**: extractor·extension·점유 셀 등 확정 배치를 추가·삭제·이동하지 않는다.
- **topology 수정 금지**: `TopologyGraph` 노드·엣지를 추가·삭제·비용 조정하지 않는다.

## DTO

`issue_code`는 구현에서 **`ValidationIssueCode`** enum으로 고정한다 (자유 문자열 금지). 문서·테스트의 코드 문자열은 enum 값과 동일하게 유지한다.

```python
@dataclass(frozen=True)
class ValidationIssue:
    issue_code: ValidationIssueCode
    severity: ValidationSeverity
    coord: Coord | None
    candidate_id: str | None
    route_reservation_id: str | None
    path_index: int | None
    route_goal_kind: RouteGoalKind | None
    transport_kind: TransportKind | None
    message: str
```

`route_reservation_id`·`path_index`는 UI 셀 클릭·경로 세그먼트 디버깅용 **선택** 필드다. 없으면 `None`. `route_reservation_id`가 있으면 **Phase 7 `RouteReservation.reservation_id`와 동일 문자열**이어야 한다.

```python
@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    issues: tuple[ValidationIssue, ...]
```

## Severity

구현에서는 **`ValidationSeverity`** enum으로 고정한다. 아래 텍스트는 멤버 이름과 동일하게 유지한다.

```text
error
warning
info
```

`error`는 validation 실패, `warning`·`info`는 실패로 치지 않는다 (Phase invariant 참조).

## 검증 항목

```text
all extractor outputs connected
all routes reach a RouteGoal that matches trunk/margin/attachment contract (not “any void cell”)
no orphan transport
no invalid overlap
all Coord satisfy island map grid contract (Phase 1)
transport kind consistency
extension attached to extractor/extension chain
max 3 extensions per extractor
route_domain / reserved path와 최종 배치의 모순 없음 (read-only 비교만)
reserved_cells와 각 confirmed reservation의 path가 집합적으로 일치한다
각 confirmed candidate에 대해 정확히 하나의 CONFIRMED RouteReservation이 존재한다 (Phase 7)
각 committed placement의 candidate_id는 candidate_pool에 존재한다 (없으면 CANDIDATE_POOL_MISSING)
coord 계약 검사 시 셀 집합 정렬은 ``_coord_sort_key`` 등으로 수행해, 비정상 객체에서도 정렬 단계에서 예외가 나지 않게 한다
```

## v1+ 확장 (문서만, v0 필수 아님)

다음은 **미래 deadlock·corridor starvation·reclaim 불가**를 줄이기 위한 후보 검사다. v0에서는 구현하지 않아도 되나, Overview·Phase 5와의 정렬을 위해 남긴다.

```text
corridor residual capacity (공유 복도 잔여 통과 슬롯 추정)
trunk redundancy (단일 trunk 단절 시 위험)
route isolation risk (외부 목표까지 대체 경로 존재 여부 등)
```

## Invariant

```text
[ ] validation is read-only
[ ] Validation must not invent new routes
[ ] Validation must not mutate placement
[ ] Validation must not fix topology
[ ] error severity fails validation
[ ] warning/info does not fail validation
[ ] every issue has explicit issue_code (ValidationIssueCode)
```

## 테스트

```text
test_validation_passes_connected_layout
test_validation_fails_unconnected_extractor
test_validation_fails_orphan_transport
test_validation_fails_invalid_coord_contract
test_validation_read_only
test_validation_issue_codes_explicit
test_validation_issue_includes_route_goal_and_transport_context
test_validation_fails_candidate_without_confirmed_reservation
test_validation_fails_reserved_cells_path_mismatch
test_validate_coord_contract_safe_sort_malformed_cell_no_raise
test_validation_fails_committed_candidate_missing_from_pool
```

## 완료 조건

```text
[ ] ValidationResult DTO 구현
[ ] final assert gate 구현
[ ] validation read-only 테스트 통과
```
