# 목표: soft_protected 제거는 replacement 선계산 + atomic replace 없이 발생하지 않음

## 배경

- 정본: `12_protected_corridor.md` §14.3 — replacement 연결·용량·stub·score 조건 충족 후에만 해제; Pass3·recovery에서도 완화 없음.

## 현재 상태

- P4에 `P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE`, `_try_atomic_replace_soft_corridor` 등 계약·거절 사유가 있다(`reclaim_shadow.py` re-export).

## 목표 상태

- “구버전 제거 → 신규 미커밋” 중간 상태가 맵에 노출되지 않도록 **트랜잭션 경계**를 문서·테스트로 고정한다.
- `rejected_by_no_replacement_route`류는 §9.6·§13.5에 따라 **commit_reason이 아님**을 유지한다(03·07 문서와 정합).

## 작업 항목

1. soft replace 성공/실패 경로마다 맵 스냅샷 순서(전·후·롤백) 시퀀스 다이어그램.
2. Recovery ratio 완화(§11.4)와 §14.3 충돌이 없는지 회귀 시나리오 목록.
3. trace: `p4_soft_replace_*` 카운터와 §14.4 필드 정렬 여부 확인.

## 검증

- 통합/단위: replacement 없이 old corridor만 비우는 경로가 없음을 assert.

## 참고 코드

- `reclaim/reclaim_soft_replace.py`, `reclaim/reclaim_shadow.py`
- `foundation/constants.py` (P4 soft replace 상수)
