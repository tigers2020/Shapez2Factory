---
name: STEP4 no_route_exhausted recovery (latest.ndjson 반영)
overview: >
  var/asteroid_mining_layout_debug/latest.ndjson 마지막 solver_summary를 파싱해
  dominant blocker를 확정하고, Pass3/P4/Reclaim·Pass2 라우팅 동작은 건드리지 않는
  다음 구현 웨이브(Case A)를 한정한다.
todos:
  - id: log-facts
    content: latest.ndjson 기반 breakdown·롤백·추출기 손실 정리
    status: completed
  - id: choose-strategy
    content: dominant trunk_union → Case A 복구 전략 확정
    status: completed
  - id: design-contract
    content: 복구 시도 조건·금지·추가 trace 키(하위 호환만) 정의
    status: pending
  - id: tests
    content: Case A 최소 회귀 테스트 설계
    status: pending
  - id: verify
    content: 구현 후 pytest/ruff/mypy/black
    status: pending
---

# STEP4 `no_route_exhausted` 복구 플랜 (2026-05-12, latest.ndjson 반영)

**본 문서 범위:** 로그 판독·복구 방향만. **라우팅 가중치·Pass2/Pass3/P4/Reclaim 동작 변경은 하지 않는다** (이번 태스크 및 비목표).

---

## 1. 로그 팩트 (`var/asteroid_mining_layout_debug/latest.ndjson`)

대상: `run_id` **d74e60416148**, `solver_summary`가 실린 **마지막** NDJSON 행(파일 내 `step4_no_route_exhausted_breakdown` 포함 행 1건).

| 항목 | 값 |
|------|-----|
| `solver_summary.step4_no_route_exhausted_breakdown.count` | **6** |
| `by_breaker_category` | **`trunk_union_goals_unreachable_from_stub`: 6** (전부 동일) |
| `dominant_blocker_category` | **`trunk_union_goals_unreachable_from_stub`** |
| `by_transport_kind` | `fluid_pipe`: 6 |
| `by_placement_pass` | `pass2`: 6 |
| `by_protected_hard_count` / `by_protected_soft_count` | 모두 `"0"`: 6 (hard_protected_ring 지배 아님) |
| `by_expanded_nodes_bucket` | `"33+"`: 5, `"2-7"`: 1 |
| `expanded_nodes` | min 6, max 45, mean 34.1667 |
| `by_goal_count` / `by_existing_trunk_goal_count` | `"93"`: 5, `"85"`: 1 |
| `step4_complete_commit_success` | **false** |
| `step4_partial_failure` | **true** |
| `step4_committed` | **false** |
| `after_pass2_extractor_count` | **66** |
| `final_extractor_count` | **56** |
| `post_step4_extractor_count` | 56 |
| `step4_rolled_back_placement_count` | **10** |
| `step4_quarantined_placement_count` | **10** |
| `extractor_loss_due_to_step4_rollback` | **10** |
| `route_loss_due_to_step4_rollback` | 10 |
| `step4_routing_failure_count` / `step4_failed_route_count` | 10 |
| `step4_known_good_route_count` / `step4_route_count` | 56 |
| `pass3_skip_reason` | **`step4_not_committed`** |
| `p4_reclaim_skip_reason` (단일 키) | 로그에 **없음** |
| P4 관련 실측 | `p4_reclaim_shadow_skip_reason` = **`pass3_not_eligible`**, `p4_reclaim_provisional_commit_skip_reason` = **`pass3_not_eligible`**, `p4_reclaim_incremental_route_skip_reason` = **null**, `p4_reclaim_incremental_route_attempted` = **false** |

### 1.1 최상위 vs `trunk_load` 일치

`finalize.py`에서 `solver_summary.step4_no_route_exhausted_breakdown`은 `trunk_load`에서 복사된다. 본 로그에서 **최상위 breakdown과 `solver_summary.trunk_load.step4_no_route_exhausted_breakdown`이 동일**함을 확인했다 (`==` 일치).

---

## 2. Dominant 블로커 분류

| 분류 후보 | 본 로그 |
|-----------|---------|
| `trunk_union_goals_unreachable_from_stub` | **6건 전부** → **지배** |
| `stub_local_geometry_or_corridor` | 0 |
| `wide_search_exhausted` / `narrow_search_exhausted` | 0 (breaker 축) |
| `hard_protected_ring` | 0 (`by_protected_hard_count` 전부 0) |
| `other_no_route_exhausted` | 0 |

**결론:** STEP4 `no_route_exhausted` 6건은 모두 **stub에서 trunk·외곽 goal 합집합에 도달 불가** 패턴으로 집계된다. 탐색이 소진된 것이 아니라, **goal은 많으나(85~93) stub 쪽에서 union에 연결되지 않는 케이스**가 표본 전체다.

---

## 3. 추출기 손실·롤백 요약

- Pass2 직후 추출기 **66** → 최종 **56** → **순손실 10** (`66 - 56 = 10`).
- `step4_rolled_back_placement_count`·`extractor_loss_due_to_step4_rollback`·`route_loss_due_to_step4_rollback`가 모두 **10**으로 정합.
- `no_route_exhausted` 집계 **6**과 라우팅 실패 **10**의 차이는, breakdown이 **`no_route_exhausted` stop에 한정**된 카운트이고 나머지 실패는 다른 `Step4RouteFailureReason` 등으로 잡힐 수 있음을 전제로 두고, **복구 설계의 축은 `dominant_blocker_category` (6건 전원 Case A)** 로 둔다.

---

## 4. 선택한 복구 전략 (다음 구현 웨이브)

**Case A — `trunk_union_goals_unreachable_from_stub`**

- **요지:** STEP4에서 `no_route_exhausted`로 끝난 stub에 대해, **롤백 직전 한 번** 같은 종류 transport로 **trunk/외곽 goal까지 제한 길이·제한 예산의 “local bridge”** 탐색을 시도한다. (기존 플랜 문서의 “STEP4 bounded local bridge recovery”와 동일 계열.)
- **좁게 유지:** Pass2 배치 생성·Pass3·P4/Reclaim 정책은 **변경하지 않는다**. bridge는 **STEP4 merge routing 경로** 안에서만 시도·검증.
- **우선순위:** `by_expanded_nodes_bucket`에서 `"33+"`가 5/6이므로, 구현 시 **고비용 Dijkstra 전에** “union 도달 가능성”을 빠르게 판별하는 **저비용 선검사** 또는 bridge 후보 축소를 검토할 수 있다 (동작 동일·조기 실패만이면 telemetry 위주).

---

## 5. 비목표

- Pass2 spine / probe / placement 루프 변경.
- Pass3 라우팅·커밋 조건 변경.
- P4 Reclaim·shadow·incremental route **동작** 변경 (이번 로그도 `pass3_not_eligible`로 P4 미기동).
- `no_route_exhausted` 분류기(`step4_route_failure_diagnostic.py`)의 **기존 trace 키·DTO 필드 이름 변경** 또는 기존 값 의미 변경.
- 라우팅 가중치·전역 탐색 budget 임의 상향 (증거 없이 **최후 수단**으로만 문서화).

---

## 6. 추가 trace 키 (하위 호환만, 구현 시)

기존 키는 유지하고 **옵션 객체·카운터만 추가**한다.

| 제안 키 (예시) | 목적 |
|----------------|------|
| `step4_local_bridge_recovery_attempted_count` | bridge 시도 횟수 |
| `step4_local_bridge_recovery_success_count` | 성공 커밋 수 |
| `step4_local_bridge_recovery_reject_reason_counts` | 거절 사유 히스토그램 |
| `step4_local_bridge_recovery_sample` | 최대 N건 샘플 (stub_cell, goal_count, path_len, reason) |

---

## 7. 테스트 계획

- 기존: `tests/unit/shapez_asteroid/test_step4_remaining_partial_failure_diagnostics.py` 유지.
- 추가(구현 시): Case A 단위 테스트 — (1) union 도달 가능한 소형 격자에서 bridge 성공, (2) hard/계약 위반 시 시도 0 또는 거절 카운트만 증가, (3) 롤백 전후 `missing_stub_count` 등 **finalize 불변식** 회귀.

---

## 8. 검증 명령 (구현 후)

```text
python -m pytest tests/unit/shapez_asteroid/test_step4_remaining_partial_failure_diagnostics.py
python -m pytest tests/unit/shapez_asteroid/
ruff check .
mypy .
black --check .
```

**이번 커밋:** 문서만 변경 → **pytest/ruff 불필요**.

---

## 9. 다음 액션

1. Case A local bridge의 **시도 조건**(예: `dominant_blocker_category`가 이미 trunk_unreachable로만 찍힌 행만, 또는 routing failure reason 필터)을 코드·계약으로 고정한다.
2. 위 trace 키를 `solver_summary` / `trunk_load`에 **복사 규칙(`finalize.py`)과 동일하게** 노출할지 결정한다.
3. 구현 후 §8 전체 실행.

---

## 10. 잔여 리스크

- `no_route_exhausted` 6건 외 **4건** 라우팅 실패는 본 breakdown으로는 세분되지 않음 → bridge 도입 후에도 일부는 여전히 실패할 수 있음.
- Local bridge가 **geometry_valid / connectivity_valid**를 깨지 않도록, 기존 STEP4 재검증·롤백 경로에 **반드시 태운다**.
