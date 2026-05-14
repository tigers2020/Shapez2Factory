# Epic B — Semantic fields (recovery / commit / reject)

**역할:** trace·summary·이벤트의 **의미 네임스페이스**를 §13.5·§16.3과 일치시킨다.

## 목표 스키마(정본 취지)

```text
recovery_trigger / event_type  → recovery 분기·이벤트 종류
commit_reason                    → committed=true 인 성공 커밋 분류만
rollback_reason                  → 제거·rollback 사유
rejected_reason                  → 후보 거절(committed=false)
```

## 금지(의미 혼합 예시)

```text
commit_reason = post_reclaim_pass3_connectivity_break   # → recovery_trigger / event_type
commit_reason = rejected_by_no_replacement_route       # → rejected_reason / rollback_reason
commit_reason = final_validation_failure               # → recovery_trigger
```

정본상 성공 `commit_reason` 예: `normal_gain`, `degraded_connected_recovery` 등(§13.5). 확장이 필요하면 **정본·계약 버전**을 먼저 갱신한다.

## 상세 티켓

| 문서 | 내용 |
|------|------|
| [03_recovery_trace_namespaces.md](./03_recovery_trace_namespaces.md) | `recovery_trigger_reason` 등 실제 코드 필드 정리 |
| [07_pass3_commit_reason_contract.md](./07_pass3_commit_reason_contract.md) | Pass3·guarded atomic vs §13.5 |

## 완료 조건(요약)

- `committed=false` 이벤트에 `commit_reason` 비어 있음(또는 null)을 회귀 테스트로 고정.
- UI/replay 소비자가 올바른 필드만 읽도록 한 페이지 “필드 사전” 유지.
