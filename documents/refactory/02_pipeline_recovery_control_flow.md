# 목표: 파이프라인·Recovery 제어 흐름과 §4.3 정렬

## 배경

- 정본: `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` §4.1–§4.3, `11_step8_recovery.md` §13.2.
- 구현: `recovery_orchestrator.run_solver_timeline_pipeline`이 STEP4 이후 **고정 `routing_snapshot` 기준**으로 Pass3→P4→finalize를 반복하고, 실패 시 주로 `validation_recovery` 루프로 처리한다.

## Mini-audit 산출물 (구현 전)

- **1차 표·정본 인용:** [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) §5 (GitHub `master` §4.3 표 전문 + 구현 매핑 + PR 리뷰 A/B/Info).

## 현재 상태

- 트리거별 복귀(예: `pass3_connectivity_break` → Pass3 rollback 후 **STEP 6 Reclaim** 등)가 문서 표와 **1:1 대응**하지 않을 수 있다.
- 오케스트레이터 독스트링은 “bounded Pass3→P4→finalize”로 요약되어 있다.

## 목표 상태

- 다음 중 하나를 **명시적으로 선택**하고 문서 또는 코드에 반영한다.
  - **A)** 구현을 정본 표에 맞춘다(복귀 지점·rollback 순서·재진입 조건).
  - **B)** 현 구현을 “MVP 단순화”로 정본에 **공식 예외**로 한 절 기술한다(표 옆에 “구현 매핑” 열).

## 작업 항목

1. 트리거별 **현 코드 경로** 표: [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) **§5.3**(정본 §5.2 인용과 함께). PR 리뷰 **A/B/Info**는 **§5.4**에 확정.
2. 차이가 큰 항목부터: §4.3.1 Reclaim 복귀 vs 현 루프 — 의도 확인 후 A 또는 B.
3. `recovery_contract_phases` / replay에 “문서 표 행 ID”를 남길지 결정한다.

## 검증

- 단위 테스트: 최소 1개 트리거에 대해 “복귀 후 실행되는 스테이지 순서”를 고정 스냅샷으로 검증.

## 위험

- 제어 흐름 변경은 Pass3·P4·finalize 상호 의존이 크므로 **회귀 테스트·NDJSON 계약**을 함께 갱신해야 한다.

## 참고 코드

- `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/recovery_orchestrator.py`
- `solver_pipeline/pass3.py`, `p4_reclaim.py`, `finalize.py`
