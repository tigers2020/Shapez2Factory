# 블루프린트 격자 좌표 (정수 X/Y) — 프로젝트 전제

**상태**: 규약 고정 (플랜 실험용 초안 아님)

## 명제

게임 블루프린트(Island **`Entries`**)에서 쓰는 정수 **열 X** 가운데 **`X == 0`인 타일·열은 존재하지 않는다.**

코드에서 타일 좌표를 `(x, y)`로 둘 때도 마찬가지로 **`x == 0`인 칸은 없다.** 이것은 디코드 실수 방어용 규칙이 아니라 **격자 모델 자체의 명제**이다.

## 동서 방향·인접

- 양의 열과 음의 열 사이에 **0열이 없으므로**, 서쪽으로 가장 가까운 양수 열 `x == 1`과 동쪽 음수 열 `x == -1`은 **좌표상 연속된 두 칸이 아니라**, 블루프린트 물리에서는 **서로 동서로 인접한 이웃**으로 취급한다.
- 즉 동서 한 칸 이동으로 **`1 ↔ -1` 점프**가 가능하고, 그 경로는 **`0`을 거치지 않는다.**

구현상 기준: [`django_apps/shapez_asteroid/extraction/shapez_grid.py`](../../django_apps/shapez_asteroid/extraction/shapez_grid.py) 의 `step_cardinal`·`neighbors4`·`is_legal_xy` 가 위 명제를 따른다.

## 남북 방향 주의

`step_cardinal` 구현에 따라 **`x == 0`인 세로선 위에서는 북·남 이동이 불가**하다(존재하지 않는 열을 “지나갈” 수 없음). 라우팅·가시화·테스트 좌표를 잡을 때 **`x = 0` 근처에서 남북 복도를 가정하지 않는다.**

## 서버·API

디코드 후 **`X == 0`인 엔트리는 계산·요약·API 출력에서 제외**한다. 상위 레이어 규약은 [`.cursor/rules/architecture.mdc`](../../.cursor/rules/architecture.mdc) 의 Asteroid·blueprint 격자 절을 본다.

## 관련 문서·코드

- 규칙 요약: [`AGENTS.md`](../../AGENTS.md) (블루프린트 좌표 한 줄)
- 아키텍처: [`.cursor/rules/architecture.mdc`](../../.cursor/rules/architecture.mdc)
- 구현: `django_apps/shapez_asteroid/extraction/shapez_grid.py`
