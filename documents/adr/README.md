# Architecture Decision Records

ADR은 "왜 이 설계를 선택했는가"를 남기는 문서다. `CANON` spec이 현재 계약의 "무엇"을 말한다면, ADR은 변경 불가에 가까운 결정의 이유와 트레이드오프를 기록한다.

## 규칙

- ADR은 승인된 아키텍처 결정을 기록한다.
- ADR은 실행 플랜이나 진행 보고서가 아니다.
- superseded된 ADR은 삭제하지 않고 `status: SUPERSEDED`와 `superseded_by`를 남긴다.
- 정본 spec을 바꾸는 결정은 관련 `CANON` 문서와 inventory 갱신을 동반한다.

## 목록

| ADR | 상태 | 결정 |
|-----|------|------|
| [`ADR-001-bounded-recovery.md`](ADR-001-bounded-recovery.md) | `ACCEPTED` | Recovery는 무한 재탐색이 아니라 제한된 branch로 다룬다 |
| [`ADR-002-protected-corridor-lifecycle.md`](ADR-002-protected-corridor-lifecycle.md) | `ACCEPTED` | hard/soft/candidate corridor 상태를 분리한다 |
| [`ADR-003-final-validation-assertion-gate.md`](ADR-003-final-validation-assertion-gate.md) | `ACCEPTED` | Final validation은 수정 단계가 아니라 assertion gate다 |
| [`ADR-004-replay-cycle-streaming.md`](ADR-004-replay-cycle-streaming.md) | `ACCEPTED` | Replay는 요약 행보다 solver cycle/event stream을 우선한다 |
