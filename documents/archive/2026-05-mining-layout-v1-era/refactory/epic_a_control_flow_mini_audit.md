# Epic A — 제어 흐름 mini-audit (§4.3 vs 구현)

**성격:** 읽기 전용 감사 산출물. **코드·휴리스틱·검증 알고리즘 변경 없음.**  
**정본(표):** `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` §4.3 (`11_step8_recovery.md` §13.2와 연계). 로컬 미보유 시 **GitHub `master` 원문**을 인용한다(§5.1).  
**갱신:** 2026-05-12 — §5에 정본 표 전문·Expected 인용·PR 리뷰 **A/B/Info** 확정 반영.

---

## 1. Epic A 진입 조건 (이 문서의 역할)

| 조건 | 상태 |
|------|------|
| Epic B 시맨틱 필드·replay bridge 안정화 | 완료 관점(별도 PR·머지 기준은 리뷰어) |
| 본 mini-audit | **구현 전** 단계 산출물 |
| 다음 단계 | §5.4 **PR 리뷰 분류** 확정 후 `02_pipeline_recovery_control_flow.md` 목표(A/B)를 고정하고 Epic A **구현** PR 분리 |

---

## 2. 식별자 정규화(감사 전제)

**trace / summary / canonical trigger는 동일하지 않다.** Epic A 구현 시에도 아래 구분을 유지한다.

| 구분 | 역할 | 예시 |
|------|------|------|
| **Canonical trigger** | §4.3 표의 행 ID(계약·리뷰 언어) | `pass3_connectivity_break` |
| **Trace / debug** | Greedy·Pass3 내부 관측(제어 분기의 단독 근거로 쓰이면 안 됨) | `pass3_connectivity_reject_sample` |
| **Summary / contract 필드** | `solver_summary`·replay에 붙는 플래그·페이즈 | `recovery_post_reclaim_pass3_connectivity_break`, `recovery_contract_phases[]` |

### 2.1 혼동 주의 3종 세트

| Canonical(표 언어) | 코드에서 쓰는 실제 식별자 | 비고 |
|--------------------|---------------------------|------|
| `pass3_connectivity_break` | `pass3_connectivity_reject_sample`(greedy metrics), `pass3_reverted` + `pass3_rollback_reason` | “연결 실패 샘플”은 **탐색 중** 거절; 최종 맵 revert는 **bridge validation** 실패 블록과 결합 |
| (표와 별도) post-reclaim 연결 실패 | `post_reclaim_pass3_pass3_reverted`, `post_reclaim_pass3_skip_reason` | `recovery_post_reclaim_pass3_connectivity_break`는 **요약 태그** |
| `post_reclaim_pass3_connectivity_break`(canonical) | `RECOVERY_PHASE_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK`, `recovery_post_reclaim_pass3_connectivity_break` | `tag_post_reclaim_pass3_connectivity_break`가 `post_reclaim_pass3_pass3_reverted`를 본다 |

---

## 3. “실제 제어 흐름” 판별 기준

감사 시 **아래만** “복귀 경로”로 본다.

- 함수 **return**으로 넘겨지는 `mining_map` / `map_final`
- **rollback** 트랜잭션·`pass3_reverted` 등으로 이전 단계 맵으로 되돌아가는지
- `run_solver_timeline_pipeline`의 **for 루프**에서의 재실행(다음 사이클 진입 조건)
- `validation_recovery_allowed` 등 **게이트**로 인한 조기 종료

**제외:** trace dict에 값이 있다는 사실만으로 분기한 것처럼 서술하지 않는다.

---

## 4. 오케스트레이터 기준선(한 줄)

`recovery_orchestrator.run_solver_timeline_pipeline`:

1. **한 번:** Pass12 → STEP4 → `routing_snapshot` 고정  
2. **루프(`max_cycles`):** `routing_snapshot` 복사 → **Pass3 → P4 → finalize**  
3. `out["ok"]` 이면 종료. 아니면 `validation_recovery_allowed(out)`이면 `pass3_recovery_context=True`로 **동일 루프(전체 Pass3→P4→finalize)** 재실행.  
4. STEP4는 루프 안에서 **재호출되지 않음.**

근거: `recovery_orchestrator.py` `run_solver_timeline_pipeline`(약 339–467행), `pass3.py` `run_pass3_stage`, `p4_reclaim.py` `run_p4_reclaim_stage`, `finalize.py` `build_final_solver_output`.

---

## 5. §4.3 정본 인용 및 구현 대비 (PR 리뷰용)

### 5.1 정본 출처 (authoritative)

- **Blob(가독):** [github.com/tigers2020/Shapez2Factory/blob/master/documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md](https://github.com/tigers2020/Shapez2Factory/blob/master/documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md)  
- **Raw(복제 기준):** [raw.githubusercontent.com/.../02_pipeline_control_flow.md](https://raw.githubusercontent.com/tigers2020/Shapez2Factory/master/documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md)  
- 인용 시점: **`master` HEAD**와 동기. 정본이 이동·수정되면 본 절 표를 **재복제**해야 한다.

### 5.2 §4.3 Recovery trigger별 복귀 경로 (정본 표 전문)

아래는 정본 **§4.3 표**를 문자 그대로 옮긴 것이다(렌더링은 정본과 동일).

```text
| Trigger | 발생 지점 | Recovery 후 복귀 | 실패 시 |
| ----------------------------- | ----------------------------------------- | ------------------------------------------------------- | ---------------------------------------------- |
| `step4_routing_failure` | STEP 4 route 생성 실패 | STEP 4 재시도, 해당 placement rollback 또는 alternate trunk 사용 | unrouted placement rollback 후 STEP 4 재시도 |
| `step4_capacity_failure` | STEP 4 capacity split/additional trunk 실패 | STEP 4 재시도, trunk split 후보 변경 | offending placement rollback |
| `pass3_connectivity_break` | STEP 5 Pass3가 연결성 파괴 | **§4.3.1** 절차 적용 → 복귀 **STEP 6 Reclaim placement loop** | Pass3 변경 rollback 후 마지막 known-good 유지 |
| `post_reclaim_pass3_connectivity_break` | STEP 7 post-reclaim Pass3 rerun이 연결성 파괴 | rerun 변경 rollback → STEP 9(**추가 rerun 없음**, §4.3.2) | 기존 connected layout 유지, partial success 가능 |
| `reclaim_incremental_failure` | STEP 6 신규 placement routing 실패 | 해당 reclaim candidate rollback 후 STEP 6 계속 | 후보 exhausted 시 Final validation |
| `final_validation_failure` | STEP 9 invariant 실패 | recovery 후 STEP 9 재검증 (**STEP 4 재진입 없음**) | attempt 초과 시 partial success 또는 solver failure |
```

정본 표 직후 문장(동일 출처):

```text
`final_validation_failure` 복구로 STEP 4 본 파이프라인을 자동 재실행하지 않는다. 용량 재설계가 필요하면 상위 오케스트레이터가 별도 실행한다.
```

§4.3.2 요지(STEP 7 실패; 동일 출처 요약):

```text
- 연결성 파괴: trigger=post_reclaim_pass3_connectivity_break
- 복귀: STEP 6 재진입이 아니라, rerun으로 깬 Pass3 변경만 rollback하고 STEP 9 Final validation.
- 동일 rerun 블록 안에서 실패 → rollback 후 재탐색 루프를 또 도는 것이 아니라, 즉시 known-good으로 복구하고 STEP 9로 진행(추가 rerun 없음).
```

### 5.3 구현 대비 매핑표 (Expected = §5.2 인용 요약)

**판별:** return path·rollback·`run_solver_timeline_pipeline` 루프만 본다(trace 필드명만으로 제어 의미 추론 금지).

| Canonical Trigger | Expected §4.3 (인용 요약) | Current Return Path (구현) | Drift? | PR 리뷰 (A/B/Info) | Notes |
|--------------------|---------------------------|------------------------------|--------|-------------------|-------|
| `step4_routing_failure` | Recovery 후 **STEP 4 재시도** 등(표 “Recovery 후 복귀”·“실패 시” 열). | `run_solver_timeline_pipeline`에서 STEP4는 **루프 밖 1회**. 부분 실패는 `finalize.py`에서 `partial_success`·`step4_partial_failure` 등으로 정리; **전용 STEP4 재시도 루프 없음**. | **yes** | **B** | 오케스트레이터가 표의 “STEP 4 재시도”와 1:1이 아님 → **MVP 예외 문서화(B)** 권고. |
| `step4_capacity_failure` | STEP 4 capacity 실패 시 **STEP 4 재시도**·rollback(표). | 별도 `return_reason=…capacity…` 트리거 미분리; `validation_recovery_allowed`는 용량을 루프 게이트에 넣지 않음(`recovery_policy.py`). | **yes** | **B** | 정본 표에는 행이 있음 → **예외·매핑 문서화(B)**. |
| `pass3_connectivity_break` | §4.3.1·**STEP 6 Reclaim** 복귀; 실패 시 Pass3 rollback·known-good. | Pass3 revert 시 `map_final`은 STEP4 스냅샷 유지 후 **동일 사이클에서 P4(reclaim 경로)** 진행(`pass3.py`). §4.3.1의 **remedial STEP4 한 번** 등은 코드상 별도 분기로 명시되지 않음. | **부분** | **B** | “STEP6 = reclaim 루프” 해석이면 경로는 근접; §4.3.1 세부는 **정본 대비 예외(B)** 검토. |
| `post_reclaim_pass3_connectivity_break` | rerun rollback → **STEP 9**, 추가 rerun 없음(§4.3.2). | `_run_post_reclaim_pass3_once`가 검증 실패 시 **이전 맵 return** 후 P4 스테이지 종료·finalize(`solver_timeline.py`). **동일 rerun 블록** 내 재탐색 루프 없음. | **no** (STEP7 의미) | **Info** | STEP7 블록 의미에서는 정본과 정합. 이후 `validation_recovery`로 Pass3→P4→finalize가 **다시** 도는 것은 **별 트리거**(`final_validation_failure` 행)와 분리해 논의. |
| `reclaim_incremental_failure` | candidate rollback 후 **STEP 6 계속**; exhausted 시 Final validation. | P4 루프 내 롤백 후 루프 지속·태깅(`p4_reclaim.py`, `recovery_policy.py`). | **no** | **Info** | 정본과 방향 일치; 세부 한도는 §4.2·§12와 별도 대조. |
| `final_validation_failure` | recovery 후 **STEP 9 재검증**; **STEP 4 자동 재실행 없음**(표·직후 문장). | STEP4는 재진입하지 않음(**정합**). 다만 `validation_recovery_allowed` 시 **Pass3→P4→finalize 전체**를 추가 사이클로 반복(`recovery_orchestrator.py` 350–464행). 표의 “STEP 9 재검증만”을 **좁게** 읽으면(STEP9 단독 재실행) **불일치**. | **부분** | **B** | **가장 중요한 행:** “STEP4 없음”은 만족; “STEP9만” 좁은 해석과의 차이는 **MVP 예외·용어 정렬(B)** 로 문서화하는 편이 안전. |

### 5.4 PR #6 follow-up 게이트 (확정 분류)

| 게이트 | 상태 |
|--------|------|
| canonical §4.3 citation 확보 | **완료** (§5.1–5.2) |
| §5 Expected authoritative citation화 | **완료** (§5.3 “Expected” = §5.2 인용 요약) |
| 각 행 A/B/Info | **완료** (§5.3 마지막 열) |
| `final_validation_failure` 분류 | **B** (STEP4 비재진입은 Info 성격이나, **STEP9-only 좁은 해석**과의 차로 **B**로 예외 문서화 권고) |

**B 행 단일 출처(표):** [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md)

**Epic A 구현 브랜치:** §5.4가 본 저장소에 머지된 뒤, 팀이 **B 문구**를 정본 또는 본 `refactory` 플랜에 반영하기로 합의하면 연다(리뷰 코멘트와 동일).

---

## 6. A/B 분류 가이드 (감사 결론용)

| 분류 | 의미 | 다음 액션 |
|------|------|-----------|
| **A** | 정본 표가 맞고, 구현을 표에 맞출 계획이 현실적 | Epic A 구현 PR에서 **제어 흐름만** 조정(회귀·NDJSON·계약 동반) |
| **B** | 현 동작을 유지하되, 정본에 **MVP 예외** 절·표 열(“구현 매핑”) 추가 | 우선 [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md)에 **B** 행을 고정하고, 필요 시 `02_pipeline_control_flow.md`(저장소 외 정본) 또는 `02_pipeline_recovery_control_flow.md`에 **공식 deviation**을 동기한다. |

**Epic A에서 금지(리마인더):** reroute 휴리스틱·혼잡 튜닝·reclaim 전략·corridor 교체 정책·검증 알고리즘 재설계. **control-flow normalization / 문서·계약 정렬만.**

**PR 리뷰 게이트:** §5.3·§5.4의 분류가 팀 합의와 함께 머지되면, Epic A **구현** 착수 전 문서 단계는 종료로 본다(정본 `master` 변경 시 §5.2 재복제).

---

## 7. 권장 후속 (구현 아님)

1. **정본 동기:** `master`의 §4.3 표가 바뀌면 §5.2 **전문을 재복제**하고 §5.3 Expected 요약을 맞춘다.  
2. **B 분류 문서화:** 우선 [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md)에 **B** 행 표를 고정한다. 필요 시 `02_pipeline_recovery_control_flow.md` 또는 정본 저장소에 **MVP 구현 매핑** 절을 추가해 `step4_*`·`final_validation_failure`·`pass3_connectivity_break`의 **B** 근거를 정본 측과 동기한다.  
3. `step4_capacity_failure` 행이 정본 표에 실제로 있는지 주기적으로 확인한다(없으면 표·Expected를 정리해 혼동 방지).  
4. `recovery_contract_phases`에 **canonical trigger id**를 넣을지(옵션) 별도 티켓으로 결정한다.  
5. 단위 테스트: “한 트리거에 대해 **스테이지 순서** 스냅샷”은 `02_pipeline_recovery_control_flow.md` 검증 절에 정렬한다.

---

## 8. 참고 경로 (증거)

| 파일 | 용도 |
|------|------|
| `solver_pipeline/recovery_orchestrator.py` | 타임라인 루프·validation recovery |
| `solver_pipeline/pass3.py` | Pass3 accept/revert·`pass3_reverted` |
| `solver_pipeline/p4_reclaim.py` | P4 + post-reclaim Pass3 + 태깅 호출 |
| `solver/solver_timeline.py` | `_run_post_reclaim_pass3_once` revert |
| `solver/recovery_policy.py` | `tag_*`, `validation_recovery_allowed`, phases |
| `solver_pipeline/finalize.py` | `return_reason`, `step4_partial_failure`, termination |

---

## 9. `02_pipeline_recovery_control_flow.md`와의 관계

- **02:** 목표·위험·참고 코드(에픽 플랜).  
- **본 문서:** §4.3 **정본 인용**(§5.2)·구현 대비 표·**A/B/Info** 확정(§5.3–5.4).  
- Epic A 구현 착수 전에 **02**에 MVP 예외(B) 문단을 반영하고, 정본 측에도 필요 시 동일 **B** 근거를 기록한다.
