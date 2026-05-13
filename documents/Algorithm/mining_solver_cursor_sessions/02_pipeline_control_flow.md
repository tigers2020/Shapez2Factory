# 02 — 파이프라인 제어 흐름 (§4)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 01

> **참고**: Transport(Dijkstra 기반 셀 가중·output당 stub 1개·외부 trunk merge·output 방향 회전) 설계 정본은 [`01_project_overview.md`](./01_project_overview.md) §3.5.

> **참고**: solve **진행 중** UI 실시간 streaming(계산 cycle **매 10회**마다 STEP 10 갱신)은 [`14_step10_replay_ui.md`](./14_step10_replay_ui.md) §16.1.

> **전제**: solver 구현 **백지**·문서 정본은 [`01_project_overview.md`](./01_project_overview.md) §0.

---

## 4. 전체 Solver Pipeline v5.10

v5에서는 Reclaim loop와 Recovery branch가 무한 루프를 만들지 않도록 **bounded control flow**를 명시한다.

```text
STEP 0. Shapez2 copy code decode
STEP 0.5. Existing layout analysis (read-only context; 배치 변경 없음)
STEP 1. Asteroid reconstruction
STEP 2. Pass1 outer-first placement
STEP 3. Pass2 internal fill placement
STEP 4. Merge-aware capacity-aware routing
STEP 5. Pass3 internal transport minimization
STEP 6. Reclaim placement loop
STEP 7. Optional post-reclaim Pass3 rerun
STEP 8. Recovery branch (비선형 분기; 매 solve마다 실행되는 선형 STEP 아님 — §13)
STEP 9. Final validation
STEP 10. Replay visualization
```

**STEP 8 번호 부여**: 목차상 슬롯 번호일 뿐이다. Recovery는 항상 실행되는 단계가 아니라 **실패·보정 조건에서만 진입하는 bounded branch**(§4.1, §13)다.

핵심:

```text
Pass3가 확보한 공간은 Reclaim loop에서 다시 활용한다.
단, Reclaim loop가 Pass3의 internal transport 절약분을 과도하게 되먹으면 reject한다.
Recovery는 branch이며, trigger별 복귀 지점과 attempt limit을 가진다.
```

---

### 4.1 Pipeline control flow

```text
Decode
→ Existing layout analysis (STEP 0.5; hint/context만 생성)
→ Reconstruction
→ Pass1 placement
→ Pass2 placement
→ Merge-aware routing
    ├─ routing/capacity 실패 → recovery(trigger=step4_routing_failure)
    └─ 성공 → Pass3
→ Pass3 internal transport minimization
    ├─ 연결성 파괴 → rollback 또는 recovery(trigger=pass3_connectivity_break)
    └─ 성공 → Reclaim loop
→ Reclaim placement loop
    ├─ 신규 placement 없음 → Final validation
    ├─ 신규 placement 있음 → incremental routing
    ├─ incremental routing 실패 → candidate rollback 또는 recovery(trigger=reclaim_incremental_failure)
    ├─ internal transport budget 초과 → 해당 후보만 reject(§12.6); loop은 다음 후보 계속
    └─ loop limit 도달 → Final validation
→ Optional post-reclaim Pass3 rerun (STEP 7)
    ├─ 연결성 파괴 → recovery(trigger=post_reclaim_pass3_connectivity_break) 또는 rerun 변경 rollback
    └─ 성공 → Final validation
→ Final validation
    ├─ success → Replay visualization
    └─ failure → bounded recovery(trigger=final_validation_failure)
```

---

### 4.2 Bounded loop 제한

```text
MAX_RECLAIM_ITERATIONS = 2 또는 3
MAX_POST_RECLAIM_PASS3_RERUNS = 1
MAX_VALIDATION_RECOVERY_ATTEMPTS = 1 또는 2
MAX_TOTAL_RECOVERY_ATTEMPTS = 3
MAX_CASCADE_CORRECTIVE_ATTEMPTS = 2  # 튜닝: STEP 4 rollback 직후 연결성 보정 한도
```

`MAX_CASCADE_CORRECTIVE_ATTEMPTS`(§9.6): placement rollback으로 인한 **즉시 연결성 보정**만 카운트한다.
**`MAX_TOTAL_RECOVERY_ATTEMPTS`에는 포함하지 않는다**(메인 recovery 예산 고갈 방지). 대신 이 상한으로 무한 cascade를 막는다.

`MAX_POST_RECLAIM_PASS3_RERUNS` **스코프(정본)**: 소행성 **1회 solve 전체**에서 post-reclaim Pass3 rerun **호출(블록 실행) 횟수** 상한이다. `MAX_RECLAIM_ITERATIONS`와 독립이며, Reclaim loop **iteration마다 리셋되지 않는다**. 한 번의 rerun 블록 안에서 실패 시 재탐색 루프가 아니라 §4.3.2대로 즉시 rollback 후 STEP 9로 진행한다.

**Canonical — Reclaim 내부 transport·gain 규칙**: 후보 채택·누적 budget·`gain / additional_route_cost` threshold 수치의 규범 정의는 **§12.2**다. §4.2 본 절은 **반복 한도·상한 상수**와 루프 수준의 계속/종료 요약만 둔다. §12.6의 “후보 reject”는 §12.2 budget 규칙의 직접 적용으로 읽는다.

Reclaim loop **계속** 요약(상세 조건·수식은 §12.2):

```text
- §12.2 후보 체크리스트·budget·gain ratio(DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD)를 만족하는 신규 후보가 남아 있음
- MAX_RECLAIM_ITERATIONS 미도달
```

**종료** 요약(위 조건의 부정 또는 한도 소진; 단일 후보 budget reject는 iteration 전체 종료가 아님):

```text
- §12.2를 만족하는 신규 후보 없음 / 동일 iteration에서 후보 소진 후 전역 지표 개선 없음
- MAX_RECLAIM_ITERATIONS 도달
```

`MAX_VALIDATION_RECOVERY_ATTEMPTS`·`MAX_TOTAL_RECOVERY_ATTEMPTS` 등 **파이프라인 전역 attempt 한도**는 Reclaim loop **내부** 종료 조건이 아니다. Final validation 이후 recovery·solver 종료 등은 **§4.4**·**§13.1**에서만 다룬다.

---

### 4.3 Recovery trigger별 복귀 경로

| Trigger                       | 발생 지점                                     | Recovery 후 복귀                                           | 실패 시                                           |
| ----------------------------- | ----------------------------------------- | ------------------------------------------------------- | ---------------------------------------------- |
| `step4_routing_failure`       | STEP 4 route 생성 실패                        | STEP 4 재시도, 해당 placement rollback 또는 alternate trunk 사용 | unrouted placement rollback 후 STEP 4 재시도       |
| `step4_capacity_failure`      | STEP 4 capacity split/additional trunk 실패 | STEP 4 재시도, trunk split 후보 변경                           | offending placement rollback                   |
| `pass3_connectivity_break`    | STEP 5 Pass3가 연결성 파괴                      | **§4.3.1** 절차 적용 → 복귀 **STEP 6 Reclaim placement loop**            | Pass3 변경 rollback 후 마지막 known-good 유지      |
| `post_reclaim_pass3_connectivity_break` | STEP 7 post-reclaim Pass3 rerun이 연결성 파괴 | rerun 변경 rollback → STEP 9(**추가 rerun 없음**, §4.3.2) | 기존 connected layout 유지, partial success 가능   |
| `reclaim_incremental_failure` | STEP 6 신규 placement routing 실패            | 해당 reclaim candidate rollback 후 STEP 6 계속               | 후보 exhausted 시 Final validation                |
| `final_validation_failure`    | STEP 9 invariant 실패                       | recovery 후 STEP 9 재검증 (**STEP 4 재진입 없음**)              | attempt 초과 시 partial success 또는 solver failure |

`final_validation_failure` 복구로 STEP 4 본 파이프라인을 자동 재실행하지 않는다. 용량 재설계가 필요하면 상위 오케스트레이터가 별도 실행한다.

#### 4.3.1 `pass3_connectivity_break` 복귀 결정 (STEP 5 전용)

STEP 7에서 동일 현상은 `post_reclaim_pass3_connectivity_break`로 분리한다.

```text
1. Pass3 시도를 rollback하여 직전 known-good transport로 복원한다.
2. STEP 5 직후 파이프라인 순서상 Reclaim은 아직 실행 전이므로,
   복귀 지점은 STEP 6 Reclaim placement loop다.
3. (선택 remedial) Pass3 실패 원인이 STEP 4 배치/merge·trunk goal 불일치로 판단되면:
   **§4.3 표 `step4_routing_failure` 행의 “Recovery 후 복귀” 절차를 한 번만 인플레이스 재사용**한다
   (별도 trigger 문자열을 붙이지 않아도 된다; trace에는 `remedial_after_pass3_connectivity_break=true` 등으로 구분).
   - 성공 시: 갱신된 transport로 Pass3를 **한 번** 재시도할 수 있다(3번 경로당 Pass3 재시도 **최대 1회**).
   - 위 remedial Pass3 재시도가 연결성·hard invariant를 깨면 **§4.3.1 1번과 동일하게 해당 Pass3 시도를 rollback**하여 직전 known-good으로 복원한다. **그 뒤로 Pass3를 또 재시도하지 않는다**(무한 재시도 금지).
   - 실패 시: **§4.3 표 `pass3_connectivity_break` “실패 시” 열**과 동일하게 Pass3 변경은 rollback된 채 known-good을 유지하고,
     이어서 **`step4_routing_failure`와 동일한** unrouted quarantine·STEP 4 재시도 루틴(표 1행)으로 넘긴다.
```

**§4.3.1 3번 remedial 경로 — attempt 귀속**: 전체 표·`recovery_return_policy` 코드 매핑은 [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md) §4.3.1과 동일하다(본 조각은 중복을 피해 링크만 둔다).

**§4.3.1 3번 vs 표 “실패 시”**: 표의 “실패 시”는 **Pass3 rollback·연결성 회복 시도 전부가 소진된 뒤**의 최종 상태다. 3번은 그 **이전**에 허용하는 **한 번의 STEP 4 remedial**이다. 3번이 성공해 Pass3가 통과하면 표의 “실패 시” 열은 적용되지 않는다.

“Reclaim 종료 후” 연결성 깨짐은 STEP 5 시점에 발생할 수 없다. 그 경우는 STEP 7에서 `post_reclaim_pass3_connectivity_break`(§4.3.2)로 처리한다.

#### 4.3.2 STEP 7(post-reclaim Pass3 rerun) 실패 처리

```text
- 연결성 파괴: trigger=post_reclaim_pass3_connectivity_break (trace·rollback_reason 등에 기록).
- 복귀: STEP 6 재진입이 아니라, rerun으로 깬 Pass3 변경만 rollback하고 STEP 9 Final validation.
- 재시도 정책(정본):
  - MAX_POST_RECLAIM_PASS3_RERUNS = 1 이면 “소행성 1회 solve당 post-reclaim Pass3 rerun 호출은 최대 1번”이다.
  - 동일 rerun 블록 안에서 실패 → rollback 후 재탐색 루프를 또 도는 것이 아니라,
    즉시 known-good으로 복구하고 STEP 9로 진행한다(추가 rerun 없음).
  - 호출 자체를 0으로 두고 조건만 만족할 때 1회 실행하는 구현이 이와 동치다.
```

---

### 4.4 Solver 종료 상태

```text
SUCCESS:
- geometry/connectivity/capacity invariant 모두 통과
- (선택) §15.4 optimization 목표까지 통과한 경우 “full success”로 trace 구분 가능

PARTIAL_SUCCESS:
- 기존 connected layout은 유지했지만 신규 reclaim placement 일부 rollback
- 또는 일부 low-priority placement를 제거하고 valid layout 반환
- invariant는 통과했으나 §15.4 optimization 항목만 미달인 경우: **solver 실패가 아니라**
  PARTIAL_SUCCESS 또는 SUCCESS + `optimization_warnings`(정책에 따라 택일)

SOLVER_FAILURE:
- connected transport를 만들 수 없음
- capacity-safe trunk를 만들 수 없음
- attempt limit 초과
```

**§4.4 ↔ §9.6 `QUARANTINED_UNROUTED`**: §9.6 규칙 6에 따라 **Final validation(STEP 9) 시점**에는 `QUARANTINED_UNROUTED` placement가 **남아 있으면 안 된다.** `PARTIAL_SUCCESS`로 종료하려면 그 **이전** 단계에서 `ROUTED_CONFIRMED` 또는 `ROLLED_BACK`으로 정리한다. 상세는 [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md) §4.4 본문.

§15.4의 항목은 **hard invariant(§15.1–15.3)** 와 **soft optimization(품질 목표)** 을 분리해 해석한다. optimization만 실패하면 Final validation을 “실패 → validation_recovery”로 보내지 않고,
결과 등급과 trace 경고로 처리한다(§15.4 참고).

---

