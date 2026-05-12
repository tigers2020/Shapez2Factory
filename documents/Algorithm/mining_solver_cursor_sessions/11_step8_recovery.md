# 11 — Recovery branch — STEP 8 슬롯 (§13, P5)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 08, 09, 10

---

## 13. Recovery Branch (파이프라인 목차 슬롯 STEP 8, 비선형)

### 13.1 Recovery는 선형 단계가 아니라 bounded branch다

Recovery는 항상 실행되는 STEP이 아니다(§4 STEP 8 슬롯 참고). 다음 실패가 발생했을 때만 진입한다.

```text
Recovery trigger:
1. STEP 4 merge-aware routing에서 output route를 만들 수 없음
2. STEP 4 capacity-aware routing에서 capacity split/additional trunk가 실패함
3. STEP 5 Pass3가 기존 connected transport를 깨뜨림
4. STEP 6 Reclaim placement의 incremental routing이 전체 연결성을 깨뜨림
5. STEP 7 post-reclaim Pass3 rerun이 기존 connected transport를 깨뜨림
6. STEP 9 Final validation에서 connectivity/capacity invariant가 깨짐
```

Recovery는 반드시 attempt limit을 가진다.

```text
MAX_TOTAL_RECOVERY_ATTEMPTS = 3
MAX_VALIDATION_RECOVERY_ATTEMPTS = 1 또는 2
```

attempt 초과 시 solver는 다음 중 하나로 종료한다.

```text
- PARTIAL_SUCCESS: offending placement/reclaim을 rollback하고 valid layout 반환
- SOLVER_FAILURE: connected/capacity-safe layout 자체를 만들 수 없음
```

---

### 13.2 Recovery trigger별 복귀 경로

**정본**: trigger별 **표 형태의 복귀 경로는 §4.3만** 유지한다. 본 절은 표를 다시 만들지 않고, 구현·리뷰용 **글머리 요약**만 둔다(§4.3·§4.3.1·§4.3.2와 문구가 다르면 §4.3이 이긴다).

```text
- STEP 4 계열 trigger: STEP 4 재시도·rollback·alternate trunk 등(§4.3 표).
- pass3_connectivity_break: Pass3 rollback → §4.3.1 절차 → **STEP 6 Reclaim placement loop**로 복귀.
- post_reclaim_pass3_connectivity_break: rerun 변경 rollback → **STEP 9**(추가 rerun 없음, §4.3.2).
- reclaim_incremental_failure: 후보 rollback → **STEP 6** 계속.
- final_validation_failure: recovery 후 **STEP 9 재검증**(STEP 4 자동 복귀 없음).
```

---

### 13.3 Recovery context 정의

```text
budget_recovery:
- demolition / reroute / corridor 변경 예산 때문에 정상 commit이 막힌 경우
- 목표: 최소 변경으로 connected route 회복

terminal_overflow_recovery:
- terminal 또는 external margin 주변에서 route/capacity overflow가 발생한 경우
- 목표: additional trunk 또는 split route 확보

merge_partial_failure:
- 일부 output stubs는 trunk에 merge되었지만, 하나 이상의 stub가 merge되지 못한 상태
- 감지 조건(정본): `routed_stub_count < total_stub_count` 이고,
  **어떤 stub s에 대해** “s에서 시작한 transport가 외부 trunk·external margin 도달 영역(§15.2)에 들어가지 못함”이 참일 때.
  (`transport_connected == false`만으로는 부족하다: 일부 stub만 trunk에 붙고 나머지는 고립인데 그래프 전체가 connected로 보일 수 있음.)
- 목표: 실패한 stub만 우회 routing하거나 soft corridor를 교체해서 전체 연결성 회복

cascade_corrective_recovery:
- STEP 4 라우팅 도중 placement rollback(§9.6) 직후 연결성·geometry가 깨진 경우에만 진입한다.
- 목표: 최소 corrective reroute 또는 국소 rollback으로 invariant 회복. Final validation(STEP 9)과 무관하다.
- 한도: MAX_CASCADE_CORRECTIVE_ATTEMPTS(§4.2). MAX_TOTAL_RECOVERY_ATTEMPTS와 별도 집계한다.

validation_recovery:
- Final validation에서 geometry/connectivity/capacity **hard invariant**가 깨진 경우에만 진입한다.
- 목표: 새 최적화(Pass3 재탐색 등)를 하지 않고 invalid 원인만 rollback 또는 최소 repair.
- invariant 유형별 처리:
  - overlap / geometry: 관련 엔티티 중 **최근 commit·낮은 우선순위 placement**부터 제거한다.
    동점이면 deterministic tie-break(예: reclaim > pass2 > pass1, 또는 placement_id).
  - connectivity 파손: 해당 구간을 사용하는 route에 대해 **replacement route가 먼저** 확보될 때만
    corridor/셀을 제거한다(§14.3 soft/hard 규칙 준수). replacement 없이 통로만 삭제하지 않는다.
  - capacity: 이 컨텍스트는 **STEP 4를 재호출하지 않는다**(§15.3: Final validation에서 새 route/trunk 생성 금지).
    routing split / additional trunk가 필요한 수준의 overflow면 근본 해결은 STEP 4 시점의 재실행·상위 오케스트레이터로 미루고,
    여기서는 **낮은 우선순위 출구를 quarantine** 하거나 이미 존재하는 할당·soft corridor만 롤백한다.
- repair 후에도 깨지면 다음 rollback 대상으로 진행하거나 attempt 소진 시 종료한다.
```

---

### 13.4 Recovery commit의 목적

일반 commit은 gain/length 조건을 엄격하게 본다.

```text
normal commit:
- gain 충분
- length 허용
- connected true
- capacity safe
```

recovery context에서는 다음 기준을 사용한다.

```text
recovery commit:
- gain/length 조건이 약해도
- 전체 연결성을 회복하고
- capacity invariant를 깨뜨리지 않으면
- 제한적으로 commit 허용
```

---

### 13.5 `commit_reason` · `rollback_reason` · `recovery_trigger` 분리

세 네임스페이스를 혼용하지 않는다.

```text
recovery_trigger:
  - STEP 4~9에서 recovery 분기로 들어갈 때만 설정(예: step4_routing_failure, pass3_connectivity_break, …).

rollback_reason / rejected_reason (committed=false 또는 placement 제거 시):
  - rollback_unrouted_placement
  - rollback_reclaim_candidate
  - rejected_by_gain_or_length
  - rejected_by_connectivity
  - rejected_by_overlap
  - rejected_by_capacity
  - rejected_by_internal_transport_budget
  - rejected_by_hard_protected_corridor
  - rejected_by_no_replacement_route   # replacement 없는 corridor 삭제 시도·실패 등
  - solver_failure_attempt_limit

commit_reason (committed=true 인 성공 커밋 분류만):
  - normal_gain
  - degraded_connected_recovery
```

`post_reclaim_pass3_connectivity_break` 같은 문자열은 **recovery_trigger**(또는 `event_type`) 전용이다. `commit_reason`에 넣지 않는다(§16.3).

---

---

## 부록: P5 체크리스트 (원문 §20)

### P5 — Recovery Context 표준화

```text
[ ] budget_recovery context 정의
[ ] terminal_overflow_recovery context 정의
[ ] merge_partial_failure context 구현
[ ] validation_recovery context 구현
[ ] trigger별 복귀 경로 구현
[ ] MAX_TOTAL_RECOVERY_ATTEMPTS 적용
[ ] MAX_VALIDATION_RECOVERY_ATTEMPTS 적용
[ ] degraded_connected_commit 허용 조건 제한
[ ] commit_reason enum 고정
[ ] hard/soft protected corridor replacement 검증
```

