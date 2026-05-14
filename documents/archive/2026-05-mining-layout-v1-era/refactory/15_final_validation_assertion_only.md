# 목표: Final validation(STEP 9)은 assertion gate만 — 새 route/trunk 생성 금지

## 배경

- **정본(Authority)**: `documents/Algorithm/mining_solver_cursor_sessions/` §11(recovery)·§14(protected corridor)·§15(STEP9). 본 문서는 PR4-D 감사·결과 기록용이며 Algorithm을 대체하지 않는다.
- 저장소 스냅샷에서 Algorithm 세션 파일이 없을 수 있다. 경로 확보 절차는 [`01_canonical_doc_paths.md`](./01_canonical_doc_paths.md)를 따른다.

## PR4-D (2026-05-12) Algorithm drift 표

| File | Current behavior | Algorithm requirement | Drift | Change |
|------|------------------|------------------------|-------|--------|
| `validation/final_validation.py` | `validate_final_mining_layout(mining_map)`만 받아 geometry·connectivity 등 검사; belt를 쓰지 않음 | §15 assertion gate; routing_state 비접근 | **no** | 모듈 독스트링에 §14/§15 비변형·비승격 명시 |
| `solver_pipeline/finalize.py` | `routing_state_summary`를 읽어 요약·`before_return_validate`·타임라인에 **동일 참조**로 실음; hard/ELA 승격 없음 | §14/§15 read/report만 | **no** | 모듈·`routing_state` 대입부 주석으로 계약 고정 |
| `solver/recovery_policy.py` | `validation_recovery_allowed`는 `ok`·unfinalized·STEP9 필드만 사용; missing stub 시 retry 차단 | §11/§15 bounded recovery; optimization만으로 retry 금지; STEP9 hard invariant만 | **no** | `step9_reports_hard_invariant_failure_for_bounded_recovery`로 조건 명시화·독스트링 보강 |
| `solver/recovery_context.py` | P4 orchestration 체인·terminal reason만 | validation_recovery와 구분 | **no** | §11/§15 비STEP4 재진입 한 줄 명시 |
| `solver_pipeline/recovery_orchestrator.py` | `run_step4_stage`는 루프 **밖** 1회; 루프는 Pass3→P4→finalize | STEP4 자동 재진입 금지 | **no** | (코드 변경 없음) 테스트로 1회 호출 고정 |
| `solver_pipeline/validation_bridge.py` | `solver_service.validate_final_mining_layout` 위임만 | §15 레이어 분리 유지 | **no** | 변경 없음 |

## PR4-D 테스트(Algorithm invariant)

- `tests/unit/shapez_asteroid/test_pr4d_algorithm_final_validation_boundary.py`: STEP9 API가 `mining_map`만 받는지, partial success + STEP9 clean 시 validation_recovery 비활성, finalize가 `routing_state` 참조·ELA 비승격 유지, 타임라인에 `run_step4_stage` 단일 호출.

## 목표 상태(기존)

- 검증 모듈에 **라우팅 커밋 API를 import하지 않는다**는 레이어 규칙을 유지(또는 명시적 allowlist).
- `validation_recovery` 실행 경로가 실제로 맵에 transport를 추가한다면 §15.3과의 정합을 재검토한다.

## 작업 항목(잔여·선택)

1. Algorithm 원문이 워크스페이스에 생기면 위 표의 **Algorithm requirement** 열을 절 번호로 치환해 재대조한다.
2. capacity hard fail을 켠 후에도 “STEP9만으로 trunk 신설”이 없는지 회귀 테스트(선택).

## 참고 코드

- `validation/final_validation.py`, `solver_pipeline/validation_bridge.py`
- `solver_pipeline/recovery_orchestrator.py`, `solver/recovery_policy.py`
