# Epic A — Control flow & Recovery (§4.3 정렬)

**역할:** 파이프라인 제어 흐름·bounded recovery를 문서 정본 표와 맞춘다.  
**정본:** `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` §4.1–§4.4, `11_step8_recovery.md` §13.1–§13.2.

## 핵심 문제

- Recovery는 STEP 8 **선형 단계**가 아니라 **실패 시 진입하는 bounded branch**다.
- Trigger별 **복귀 위치**가 §4.3 표로 고정되어 있다. 오케스트레이터가 “Pass3→P4→finalize 재시도” 한 가지로 압축하면 표와 drift 난다.

## §4.3 복귀 표 (구현 매핑의 기준)

| Trigger | 복귀(정본 요약) |
|--------|-----------------|
| `step4_routing_failure` | STEP 4 재시도·placement rollback·alternate trunk 등 |
| `step4_capacity_failure` | STEP 4 재시도·offending placement rollback |
| `pass3_connectivity_break` | Pass3 rollback 후 **STEP 6 Reclaim** |
| `post_reclaim_pass3_connectivity_break` | rerun rollback → **STEP 9**, 추가 rerun 없음 |
| `reclaim_incremental_failure` | candidate rollback → **STEP 6** 계속 |
| `final_validation_failure` | recovery 후 **STEP 9 재검증**, STEP 4 자동 재진입 없음 |

## Attempt 카운터

- `MAX_CASCADE_CORRECTIVE_ATTEMPTS` vs `MAX_TOTAL_RECOVERY_ATTEMPTS` 등은 §4.2·§13.3대로 **별도 집계**해야 한다.

## 상세 티켓(하위 문서)

| 문서 | 내용 |
|------|------|
| [02_pipeline_recovery_control_flow.md](./02_pipeline_recovery_control_flow.md) | 오케스트레이터 vs §4.3 |
| [03_recovery_trace_namespaces.md](./03_recovery_trace_namespaces.md) | 트리거·필드명과 제어 흐름 교차 시 혼선 방지 |

## 완료 조건(요약)

- Trigger → 복귀 스테이지가 코드 경로·테스트·(선택) replay phase로 **추적 가능**하다.
- 문서와 구현이 다르면 **정본 수정** 또는 **코드 수정** 중 하나로만 남긴다(MVP 예외는 정본에 명시).
