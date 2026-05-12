---
status: ACCEPTED
owner: solver-architecture
last_reviewed: 2026-05-12
supersedes: []
superseded_by:
related_epics: [validation, replay]
---

# ADR-003: Final Validation As Assertion Gate

## 결정

Final validation은 새 route나 trunk를 만드는 수정 단계가 아니라, 이미 생성된 layout을 검증하는 assertion gate다.

## 근거

검증 단계가 상태를 수정하면 실패 원인, replay frame, summary field가 실제 solver decision과 어긋난다. 수정은 placement/routing/recovery/reclaim 단계에서 끝나야 하며, final validation은 최종 계약 위반을 드러내는 역할에 머문다.

## 결과

- final validation은 layout mutation을 하지 않는다.
- 실패는 skip/reject/validation reason으로 남긴다.
- validation 통과 전 summary나 replay에서 완료 상태로 보이지 않게 한다.
