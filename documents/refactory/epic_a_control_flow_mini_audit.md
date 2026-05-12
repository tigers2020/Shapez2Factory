# Epic A — 제어 흐름 mini-audit (§4.3 vs 구현)

**성격:** 읽기 전용 감사 산출물. **코드·휴리스틱·검증 알고리즘 변경 없음.**  
**정본(표):** `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` §4.3, `11_step8_recovery.md` §13.2 (저장소에 파일이 없을 수 있음 → 인용 경로만 정본으로 둔다).  
**갱신:** 2026-05-12.

---

## 1. Epic A 진입 조건 (이 문서의 역할)

| 조건 | 상태 |
|------|------|
| Epic B 시맨틱 필드·replay bridge 안정화 | 완료 관점(별도 PR·머지 기준은 리뷰어) |
| 본 mini-audit | **구현 전** 단계 산출물 |
| 다음 단계 | 표의 **A/B 결정** 후 `02_pipeline_recovery_control_flow.md` 목표 상태(A 또는 B)를 확정하고 구현 PR 분리 |

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

## 5. §4.3 트리거 × 구현 대응표 (1차 감사)

**Expected §4.3 Path** 열은 리뷰·계획에서 합의된 정본 의도를 요약한 것이다. 정본 파일 미보유 시 **문서 합의 후 수정**.

| Canonical Trigger | Current Identifier(s) | Current Return Path | Expected §4.3 Path | Drift? | A / B 초안 | Notes |
|-------------------|----------------------|---------------------|-------------------|--------|------------|-------|
| `step4_routing_failure` | `step4_routing_failure_count`, `step4_result.routing_failures`, `step4_partial_failure`, `return_reason=step4_partial_failure` | STEP4는 파이프라인에서 **단일 실행**. 부분 실패 시에도 `map_after_routing`이 나오면 이후 **Pass3→P4→finalize**가 같은 사이클에서 진행. STEP4 전용 “재시도 루프” 없음. | STEP4 retry / rollback 등 표 기재 | **yes** | **B** 후보 | `finalize.py`가 `solver_termination=partial_success`와 `step4_returned_layout_source`로 의미를 쪼갬(약 275–335행). 표가 “STEP4만 재실행”을 요구하면 오케스트레이터 구조와 불일치. |
| `step4_capacity_failure` | Pass3 trace의 `pass3_over_capacity_segments` 등; `validation_recovery_allowed`는 용량을 루프 게이트에 **포함하지 않음**(`recovery_policy.py` 주석·200–228행). | 별도 `return_reason=…capacity…` **트리거 미분리**. | 표에 행이 있으면 STEP4/Pass3 정책과 매핑 필요 | **yes** (또는 표에서 제외) | **B** 후보 | “용량”이 trace-only인지 정본에서 명시 필요. |
| `pass3_connectivity_break` | Greedy: `pass3_connectivity_reject_sample`. 최종 revert: `pass3_reverted`, `pass3_rollback_reason=final_validation_failed_after_pass3` | Greedy 실패 샘플은 **지표**. 맵 revert 시 `map_final`은 **STEP4 라우팅 맵**으로 유지(`pass3.py` 227–293행). 이어서 **동일 사이클에서 P4 reclaim** 실행. | rollback → STEP6(reclaim) 등 | **부분 일치 / 명명 drift** | **B** 후보 | 구조상 “Pass3 롤백 후 P4”는 한 사이클 안에서 성립. 표의 “STEP6”이 P4 reclaim을 가리키면 **기능은 근접**, 트리거 이름·단계 번호는 **정렬 필요**. |
| `post_reclaim_pass3_connectivity_break` | `post_reclaim_pass3_pass3_reverted`, `recovery_post_reclaim_pass3_connectivity_break`, `recovery_contract_phases`에 `post_reclaim_pass3_connectivity_break` | `solver_timeline._run_post_reclaim_pass3_once`: 검증 실패 시 **입력 `mining_map`으로 return**(약 179–183행). 이후 **같은 P4 스테이지**가 끝나고 finalize로 진행. | rollback → STEP9 only, no extra rerun | **yes** | **B** 후보 | “STEP9 only”가 **finalize 한 번**을 뜻하면 부분 일치. **validation_recovery**가 켜지면 다음 사이클에서 **전체 Pass3→P4→finalize**가 다시 돈다(정본이 금지하면 drift). |
| `reclaim_incremental_failure` | `p4_reclaim_incremental_route_rollback_performed`, `recovery_reclaim_incremental_failure`, phase `reclaim_incremental_failure` | P4 루프 내부에서 후보 롤백 후 **루프 지속**(`p4_reclaim.py`에서 `run_p4_reclaim_loop_after_pass3` 호출, `tag_reclaim_incremental_failure_from_summary`). | candidate rollback → STEP6 루프 지속 | **대체로 align** | **A** 후보 | 세부는 `reclaim` shadow 구현과 정본 문장 1:1 대조 필요. |
| `final_validation_failure` | `final_validation` dict, `return_reason` (`validation_geometry_failed` 등), `validation_recovery_allowed` | `ok`가 아니고 게이트 통과 시 **추가 사이클**: `pass3_recovery_context=True`로 **Pass3→P4→finalize 전체 반복**(`recovery_orchestrator.py` 453–464행). `recovery_action_plan`은 **계획·가시성**(`route_validation_recovery_actions`). | recovery → STEP9 revalidation only | **yes** | **B** 후보 | 현 MVP는 “STEP9에서 파생된 액션만 단독 재실행”이 아니라 **동일 거대 스테이지 블록** 재실행. |

---

## 6. A/B 분류 가이드 (감사 결론용)

| 분류 | 의미 | 다음 액션 |
|------|------|-----------|
| **A** | 정본 표가 맞고, 구현을 표에 맞출 계획이 현실적 | Epic A 구현 PR에서 **제어 흐름만** 조정(회귀·NDJSON·계약 동반) |
| **B** | 현 동작을 유지하되, 정본에 **MVP 예외** 절·표 열(“구현 매핑”) 추가 | `02_pipeline_control_flow.md`(저장소 외 정본) 또는 본 저장소 요약 문서에 **공식 deviation** 기록 |

**Epic A에서 금지(리마인더):** reroute 휴리스틱·혼잡 튜닝·reclaim 전략·corridor 교체 정책·검증 알고리즘 재설계. **control-flow normalization / 문서·계약 정렬만.**

---

## 7. 권장 후속 (구현 아님)

1. 정본 `02_pipeline_control_flow.md` §4.3 **원문 표**를 복사해 “Expected” 열을 **인용 기반**으로 고친다.  
2. `step4_capacity_failure` 행을 정본에 실제로 두는지 확인; 없으면 표에서 제거해 혼동 방지.  
3. `recovery_contract_phases`에 **canonical trigger id**를 넣을지(옵션) 별도 티켓으로 결정.  
4. 단위 테스트: “한 트리거에 대해 **스테이지 순서** 스냅샷”은 `02_pipeline_recovery_control_flow.md` 검증 절에 정렬.

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
- **본 문서:** §4.3 대비 **1차 표·식별자 사전·A/B 초안**.  
- Epic A 구현 착수 전에 **02의 “작업 항목 1”을 본 표로 대체·동기화**하면 된다.
