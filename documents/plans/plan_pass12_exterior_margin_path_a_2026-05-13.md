# Pass12 외부 마진 — 경로 A(진단·추적만) 채택

**상태**: ACTIVE (승인용 한 장)  
**날짜**: 2026-05-13

## 결정

- **경로 A**: `is_external` / `exterior_margin_cells`의 **기하 의미는 변경하지 않는다.** §15 최종 검증과의 계약을 유지한다.
- **경로 B**(마진을 mineable perimeter·BFS exit 등으로 재정의)는 **보류**. 별도 플랜에서 §08·§15 문서와 함께 승인 후에만 구현한다.

## 이번 구현 범위

1. Pass2 외부 마진 진단 문자열 보강(`pass12_route_probe`).
2. 보존 드롭 trace: `preserve_drop_blocker`, `preserve_drop_detail` (기존 `preserve_drop_reason` 유지).
3. `solver_summary`에 프레임/이벤트 카운터 용어 짧은 glossary.
4. 회귀 테스트·뷰 docstring 보강.

## 검증

- `python -m pytest tests/unit/shapez_asteroid/...` (변경 구간)
- `ruff check`, `black --check` (변경 파일)
