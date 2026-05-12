---
status: ACCEPTED
owner: solver-architecture
last_reviewed: 2026-05-12
supersedes: []
superseded_by:
related_epics: [routing, protected-corridor]
---

# ADR-002: Protected Corridor Lifecycle

## 결정

Protected corridor는 hard, soft, candidate 상태를 분리하고, soft corridor 변경은 replacement 계산 후 atomic replace로만 반영한다.

## 근거

Corridor 상태가 섞이면 routing, pass3 transport, reclaim이 같은 셀을 서로 다른 의미로 해석한다. hard 보호는 침범 금지 계약이고, soft 보호는 대체 가능하지만 부분 변경 중간 상태가 외부에 노출되면 안 된다.

## 결과

- hard corridor 침범은 reject한다.
- soft corridor는 replacement가 준비된 경우에만 교체한다.
- candidate corridor는 확정 전 상태이며 canonical occupancy로 취급하지 않는다.
