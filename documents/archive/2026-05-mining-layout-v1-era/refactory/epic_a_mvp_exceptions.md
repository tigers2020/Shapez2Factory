# Epic A — §4.3 MVP 예외 목록 (B-classified)

**스코프(필독):** 본 문서는 **`02_pipeline_control_flow.md` §4.3 canonical trigger** 행만 다룬다. **전역 “B = 코드 수정 금지” 모델이 아니다.** Placement `PlacementCommitState`·§9.6 등은 Algorithm `08_step4_routing.md` 및 [placement_fsm_drift_classification.md](./placement_fsm_drift_classification.md)를 본다. **B**는 “영구 면제”가 아니라 **정본과 구현 충돌이 보류된 상태(decision required)** 이며, 종착은 코드 회귀 또는 Algorithm 정본의 **명시적** 갱신이다.

**역할:** §4.3 정본 대비 구현 차이 중, **당장 Epic A control-flow PR에서 정렬하지 않기로 한** 행을 표로 고정한다(재분류 시 §5.3·본 표를 먼저 갱신).  
**정본 인용·감사 근거:** [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) §5.2–5.4(Expected = §4.3 인용 요약, PR #6 follow-up 분류).  
**범위:** 본 표의 **B** 행만 기술한다. **Info**(`post_reclaim_pass3_connectivity_break`, `reclaim_incremental_failure`)는 정합·관측 정리용이므로 여기서 다루지 않는다.  
**갱신:** 2026-05-12 — PR #4–#6 머지 후 고정 초안. **2026-05-12** — 스코프 노트·B 의미 정렬(거버넌스 PR).

---

## B-classified triggers (고정 표)

| Trigger | Classification | Canonical rule | Current behavior | Why accepted as MVP exception | Revisit condition |
|---|---|---|---|---|---|
| `step4_routing_failure` | **B** (MVP exception) | §4.3 표: Recovery 후 **STEP 4 재시도**; 실패 시 unrouted placement rollback 후 STEP 4 재시도. | `run_solver_timeline_pipeline`에서 STEP4는 **루프 밖 1회**. 부분 실패는 `finalize.py`의 `partial_success`·`step4_partial_failure` 등으로 정리되며, 표와 같은 **전용 STEP4 재시도 루프**는 없음. | 오케스트레이터가 표의 “STEP 4 재시도”와 1:1이 아님; 당장 제어 흐름을 바꾸면 회귀·범위가 커짐. | Epic A에서 “표의 STEP4 재시도”를 **명시적 계약**으로 구현할 때, 또는 상위 오케스트레이터가 별도 실행으로 흡수하는 설계가 확정될 때. |
| `step4_capacity_failure` | **B** (MVP exception) | §4.3 표: capacity 실패 시 **STEP 4 재시도**·trunk split 후보 변경·rollback. | `return_reason` 등으로 **capacity 전용 트리거**가 표와 1:1로 분리되어 있지 않음; `validation_recovery_allowed`가 용량을 루프 게이트에 넣지 않음(`recovery_policy.py`). | 정본 표에는 행이 있으나 구현 매핑이 희석됨; 시맨틱·게이트 정리 전에는 **문서화된 예외**로 두는 것이 안전. | `step4_routing_failure`와 capacity 경로가 **요약·트리거**에서 분리되고, §4.3 열과 소비 지점 표가 고정될 때. |
| `pass3_connectivity_break` | **B** (MVP exception; 부분 drift) | §4.3.1·**STEP 6 Reclaim** 복귀; 실패 시 Pass3 rollback·known-good. | Pass3 revert 시 `map_final`은 STEP4 스냅샷 유지 후 **동일 사이클에서 P4(reclaim 경로)**; §4.3.1의 **remedial STEP4 한 번** 등은 코드상 별도 분기로 명시되지 않음. | “STEP6 = reclaim 루프” 해석이면 경로는 근접하나, §4.3.1 세부(`reject_sample`·rollback·STEP6 return 등)와의 **1:1 대응**은 아직 미정렬. | §4.3.1 세부 semantics와 구현을 **normalization** 할 때(감사에서 향후 **A** 후보로 언급된 구간). |
| `final_validation_failure` | **B** (MVP exception; 부분 drift) | 표·직후 문장: recovery 후 **STEP 9 재검증**; **STEP 4 자동 재실행 없음**. | STEP4 **비재진입**은 정본과 **정합**. 다만 `validation_recovery_allowed` 시 **Pass3→P4→finalize 전체**를 추가 사이클로 반복(`recovery_orchestrator.py`). 표의 “STEP 9 재검증”을 **STEP9 단독 재실행**으로만 좁게 읽으면 불일치. | `validation_recovery` 루프는 **솔버 안정성 보완** 성격이 큼; §4.3를 “STEP9 only”로만 좁히면 **오탐 drift** 라벨 위험. | 정본에 validation_recovery 루프가 **허용 루프**로 명시되거나, 구현이 STEP9-only 좁은 해석과 맞춰질 때(정본·계약 합의 후). |

---

## 사용 방법 (팀)

- **Drift vs MVP:** 구현 변경 전에 본 표에 Trigger가 있는지 확인한다. **없으면** drift 매트릭스·mini-audit로 되돌아가 A/B를 재판정한다.
- **Epic A 구현 PR:** **A**로 재분류된 행만 코드 변경 대상으로 삼는다(본 문서 **B** 행은 예외로 유지하되, 주석·계약 테스트로 링크 가능).
- **정본 `master` 변경 시:** [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) §5.2 표 **재복제** 후, 본 표의 Canonical / Current / Revisit를 같이 갱신한다.

---

## 머지 게이트 (환경 메모)

PR **#4 / #5 / #6**은 GitHub에서 `master`로 병합하는 것이 정본이다. 로컬 `origin`에 해당 PR 전용 브랜치가 없거나 `gh` CLI가 없는 환경에서는 **자동 머지를 수행하지 못한다** — 웹에서 머지 완료 후 본 문서 상단 **갱신** 날짜만 맞추면 된다.
