# 목표: Recovery·Trace 필드 네임스페이스 정리

## 배경

- 정본: `11_step8_recovery.md` §13.5, `14_step10_replay_ui.md` §16.3.
- `recovery_trigger`는 recovery **분기 진입** 시에만 쓰인다는 취지와, `commit_reason`은 **성공 커밋 분류**, `rollback_reason`/`rejected_reason`은 실패·거절이 분리된다.

## 현재 상태

- `p4_reclaim.py`에서 P4 **정상 진입** 시에도 `pass3_summary["recovery_trigger_reason"]`을 기본값으로 채울 수 있어, “recovery 전용” 의미가 흐려진다.
- `recovery_policy.synthesize_recovery_validation_outcome`이 `commit_reason`에 `validation_ok` 또는 `pass3_commit_reason` 원문을 넣어 §13.5의 좁은 열거와 어긋날 수 있다.

## 목표 상태

- **의미론 고정**
  - `recovery_trigger` / `recovery_trigger_reason`: bounded recovery **진입** 또는 동등한 이벤트에만 설정.
  - 정상 P4/Pass3 진행: `phase`, `p4_entry_reason` 등 **별도 필드**로 분리하거나 트리거 필드를 비운다.
- `recovery_validation_outcome.commit_reason`: §13.5와 동일 집합으로 **normalize**하거나, 스키마에서 필드명을 바꿔 “rollup 요약”임을 드러낸다.

## 작업 항목

1. `RECOVERY_TRIGGER_*` 사용처 전수 조사: “정상 경로” vs “실패 복구 경로”.
2. `pass3_summary` / `solver_summary` / replay event payload에 대한 **필드 사전** 초안(한 표).
3. UI·테스트·외부 소비자가 `recovery_trigger_reason`에 의존하는지 확인 후 마이그레이션.

## 검증

- 계약 테스트: 정상 solve 1건에서 `recovery_trigger*`가 비어 있거나 문서화된 non-recovery 값만 허용.

## 위험

- 필드 의미 변경은 프론트(`asteroid_optimizer` 등)·저장된 NDJSON 해석에 영향.

## 참고 코드

- `solver_pipeline/p4_reclaim.py` (`recovery_trigger_reason` 설정)
- `solver/recovery_policy.py` (`recovery_validation_outcome`)
- `solver_pipeline/finalize.py` (summary 병합)
