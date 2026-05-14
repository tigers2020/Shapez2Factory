# 플랜: merge `repair not_found` escalation (2026-05-09)

## 목표

`find_min_demolition_path`가 **`None`**을 반환한 outlet에 대해서도, 기존 **demolition cap 초과** 시와 동일한 **merge budget escalation(레벨 1~4) + `budget_recovery` Pass3**를 시도한 뒤, 그래도 막히면 partial failure로 내린다.

## 비목표 (이번 패치에서 하지 않음)

- placement 단계 stub escape gate (P2).
- `find_merge_path` 자체의 void-only 정책 변경.

## 승인 요약

사용자 요청(현재 플랜·리서치 작성 후 진행)에 따라 **P0 구현 진행**으로 본다.

## 구현 요약 (P0)

1. **`repair is None` 분기**
   - 기존: `merge_repair_not_found` trace 후 즉시 `return_merge_partial_failure`.
   - 변경: `merge_budget_escalation[outlet]` 증가 후 **레벨 1~4**는 cap 초과 분기와 **동일한 unblock / combo / rail / owner-drop + Pass3** 시퀀스 실행.
   - **레벨 ≥ `MERGE_BUDGET_ESCALATION_GIVE_UP_LEVEL`**: demolition repair가 없으므로 **terminal overflow 적용 분기는 타지 않음** → 명시적 메시지로 `return_merge_partial_failure` (기존 cap 경로의 `return_merge_budget_blocked`와 구분).
2. **`find_min_demolition_path` `not_found` trace**
   - `explored_cells`, `bounds`, `allow_mineable_route`, 시작점 4-neighbor에 대한 **요약 비용 라벨** 추가 (Pass3 `not_found`와 유사한 진단 목적).

## 검증

- `python -m pytest tests/unit/shapez_asteroid/test_asteroid_mining_layout.py` (및 필요 시 전체 unit).
- `ruff check` 대상 파일.

## 위험·회귀

- 동일 outlet에 대해 cap 경로와 not_found 경로가 **같은 `merge_budget_escalation` 카운터**를 공유하므로, 한 outlet이 번갈아 두 경로를 탈 이론적 가능성은 낮으나 레벨 소비는 단조 증가로 이해한다.

## 관련 문서

- [`research_merge_repair_not_found_2026-05-09.md`](../../research/research_merge_repair_not_found_2026-05-09.md)
- P1 mineable 2차 탐색·고비용: [`merge_repair_mineable_route_p1_2026-05-09.md`](merge_repair_mineable_route_p1_2026-05-09.md) (구현 완료 시 본 문서 비목표 항목은 P1로 이관됨)
