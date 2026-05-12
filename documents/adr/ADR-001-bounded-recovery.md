---
status: ACCEPTED
owner: solver-architecture
last_reviewed: 2026-05-12
supersedes: []
superseded_by:
related_epics: [recovery, pipeline]
---

# ADR-001: Bounded Recovery

## 결정

Recovery는 무한 재탐색 루프가 아니라 제한된 branch와 명시적 실패 사유를 가진 복구 단계로 다룬다.

## 근거

채굴 레이아웃 솔버는 placement, routing, reclaim, validation이 같은 invariant를 공유한다. Recovery가 무제한으로 상태를 바꾸면 replay와 validation에서 원인 추적이 불가능해진다.

## 결과

- Recovery branch는 trigger와 rollback/reject reason을 trace에 남긴다.
- 실패는 숨기지 않고 bounded failure로 노출한다.
- 완료 조건은 final validation 통과이며, recovery 자체 성공 신호만으로 완료 처리하지 않는다.
