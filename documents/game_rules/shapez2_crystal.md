# Shapez 2: Crystal Generator (요약·링크)

상세 메커니즘·근거·솔버 규칙은 **[crystal_mechanics.md](crystal_mechanics.md)** 를 정본으로 본다.

## 구현 상태 (shapez2Solver)

- **Crystal Generator**: [`crystal_fill_gaps_and_pins`](../../django_apps/shapez_core/domain/crystal_geometry.py) + [`OperationEngine`](../../django_apps/shapez_solver/services/operation_engine.py). 색: **레시피 그래프**에서는 노드 `crystal_color`(한 글자) 또는 두 번째 입력 와이어의 균일 색 추론([`apply_operation`](../../django_apps/shapez_solver/services/operation_semantics.py)); 매크로 `OperationRecipe.color`로 넘길 때도 동일.
- **클러스터·shatter**: [`connected_crystal_cluster`](../../django_apps/shapez_core/domain/crystal_geometry.py), [`shatter_crystal_cluster`](../../django_apps/shapez_core/domain/crystal_geometry.py) — Cut/Swap/Stack에 자동 연결은 아직 없음.

## 위키 요약(참고용)

Crystal Generator는 입력 shape의 **빈 공간과 pin 위치**에 crystal을 채우고, **사용 중인 최상 레이어 범위**까지 적용된다는 설명이 있다.

## 신뢰도

- 위키·커뮤니티 혼합 — 세부는 게임 내 검증 권장.

## 관련

- [crystal_mechanics.md](crystal_mechanics.md)
- [shapez2_pin_support.md](shapez2_pin_support.md)
