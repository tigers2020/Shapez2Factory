# Epic C — Protected corridor state machine (§14)

**역할:** `candidate_corridor` / `soft_protected` / `hard_protected` 생명주기와 **atomic soft replace**를 정본과 맞춘다.

## 정본 규칙(요약)

```text
candidate  → replacement 검증·commit 후 soft 승격(정책에 따라 hard는 드묾)
soft 제거  → replacement route 선계산 + 검증 + atomic replace만
hard       → Pass3 / Reclaim / Recovery에서 임의 제거 금지
STEP 9     → 새 hard corridor “발명” 금지(불일치면 버그 또는 validation_recovery)
```

## 현재 drift 포인트

- STEP4 요약에서 `candidate`와 `confirmed`에 동일 집합을 넣는 식의 **축약**은 문서 §14.2.1과 어긋날 수 있다 → 상세는 [04](./04_protected_corridor_lifecycle.md), [14](./14_soft_corridor_atomic_replace.md).

## 상세 티켓

| 문서 | 내용 |
|------|------|
| [04_protected_corridor_lifecycle.md](./04_protected_corridor_lifecycle.md) | hard/soft/candidate·STEP4 블록 |
| [14_soft_corridor_atomic_replace.md](./14_soft_corridor_atomic_replace.md) | §14.3 atomic·`rejected_by_no_replacement_route` |

## 완료 조건(요약)

- 상태 전이가 표·trace에 남고, replacement 없는 soft 제거 경로가 **없음**을 테스트로 고정.
