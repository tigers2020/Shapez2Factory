# Pass2 확장 트리·채굴 방향 휴리스틱 (운송 비용 근사)

**날짜**: 2026-05-08

## 맥락

2차 스캔(`use_tree_bundle=True`)은 동일 `outward_dir`에 대해 55개의 3-확장 트리 후보가 있고, 이전 구현은 **첫 유효 트리**만 골랐다. 방향은 **출구–앵커 맨해튼**만 보고 `CARDINAL_ORDER`로 동점을 깼다. 그 결과 출구는 앵커에 맞추기 쉬우나, 확장기가 **내부 mineable**을 덜 남기거나, 머지 단계에서 **void 경로**가 길어지는 조합이 자주 나올 수 있다.

## 가정

- 머지는 `django_apps/shapez_asteroid/services/asteroid_mining_layout/routing.py`의 `find_merge_path`와 동일하게, **앵커만**을 목표 트리로 둔 BFS로 **첫 아웃렛**이 실제로 연결될 때의 난이도를 근사할 수 있다(탐욕적이지만 계산 비용이 작음).
- 소행성 경계 `cells_touching_void` (`boundary.py`) 위에 확장기를 두면 내부 후보가 더 남을 가능성이 있다(`boundary` 선호).

## 목표 함수 (동점은 튜플 순서로 처리)

같은 후보 셀에서 가능한 각 방향 `d`에 대해, 유효한 트리들 중 다음을 최소화한다.

1. **출구–앵커 맨해튼** (`ma`): 기존과 동일하게 운송 거리의 1차 프록시.
2. **머지 경로 길이 추정** (`mb`): `find_merge_path(출구, {앵커}, asteroid_frozen, 현재 건물 ∪ 추출기 ∪ 확장기)`. 실패 시 큰 상수(`10**6`)로 처리.
3. **경계 확장기 개수** (`-ext_on_boundary`): 경계에 놓인 확장 칸 수가 많을수록 튜플이 작아지도록 **마이너스** 부호로 넣어 선호.
4. 방향 간 최종 비교: `(ma, mb, -ext_on_boundary, dir_rank[d], ti)` — `ti`는 열거 순서 인덱스.

## 한계

- 전역 최적이 아니며, 여러 아웃렛이 서로 먼저 깔린 운송선을 공유하는 실제 머지 순서는 반영하지 않는다.
- `mb`는 **배치 직전** 건물 집합 기준이며, 이후 번들이 경로를 바꿀 수 있다.
- 상수 가중치 튜닝은 포함하지 않았다(순수 어휘 순서).

## 코드 위치

- 트리 순위: `placement.select_best_extension_tree_for_pass2`, `place_tree_bundle(..., extension_tree_override=...)`.
- 방향·트리 결합 선택: `solver_service._place_scan_pass`에서 `use_tree_bundle`일 때만 분기.
