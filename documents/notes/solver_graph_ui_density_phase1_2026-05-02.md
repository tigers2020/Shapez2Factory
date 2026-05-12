# Solver 그래프 가시성·밀도 — Phase 1 구현 기록

## 상태

사용자 요청으로 Phase 1 구현 진행 (플랜: Solver 그래프 가시성·밀도 개선).

## 결정된 값

| 항목 | 값 | 비고 |
|------|-----|------|
| `NODE_HEIGHT` | 260 | Shape 카드 높이; 마크업 프리뷰·패딩 축소로 정합 |
| `ROW_GAP` | 276 | `NODE_HEIGHT + 16` (세로 겹침 방지) |
| `MULTI_INPUT_SPREAD_GAP` | `round(ROW_GAP * 0.65)` | 다중 입력 선행 노드 세로 벌림만 완화 |
| `COLUMN_STAGGER` | `min(26, floor(COLUMN_GAP * 0.05))` | COLUMN_GAP=270 → 13px; 동일 랭크 수평 계단 완화 |
| 엣지 색 | input: amber 계열, output: cyan 계열 | 기본은 cyan 유지 |

## 범위 외 (Phase 2)

연산 노드 전용 작은 레이아웃 박스는 레이아웃 엔진 이종 크기 확장이 필요해 본 문서 범위에서 제외.
