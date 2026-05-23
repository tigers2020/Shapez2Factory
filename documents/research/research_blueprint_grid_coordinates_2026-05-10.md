# Asteroid / world map grid coordinates (no `x == 0` column)

**상태**: 규약 고정 (플랜 실험용 초안 아님)

## Copy JSON vs world map (do not mix)

**Shapez2 copy JSON** `BP.Entries` `X`/`Y` are **island blueprint local** coordinates (omitted → `0`; `X==0` is valid). See [`research_shapez2_copy_json_island_local_coords_2026-05-23.md`](research_shapez2_copy_json_island_local_coords_2026-05-23.md).

**This document** applies to the **asteroid / lab world map** after reconstruction (`asteroid_map_coords`, transport BFS): integer column **`x == 0` does not exist**.

## 명제 (world map)

소행성·랩 월드 격자에서 정수 **열 x** 가운데 **`x == 0`인 타일·열은 존재하지 않는다.**

코드에서 타일 좌표를 `(x, y)`로 둘 때도 마찬가지로 **`x == 0`인 칸은 없다.** 디코드 실수 방어가 아니라 **월드 격자 모델**의 명제이다.

## 동서 방향·인접

- 양의 열과 음의 열 사이에 **0열이 없으므로**, 서쪽으로 가장 가까운 양수 열 `x == 1`과 동쪽 음수 열 `x == -1`은 **좌표상 연속된 두 칸이 아니라**, 블루프린트 물리에서는 **서로 동서로 인접한 이웃**으로 취급한다.
- 즉 동서 한 칸 이동으로 **`1 ↔ -1` 점프**가 가능하고, 그 경로는 **`0`을 거치지 않는다.**

구현 참조 코드는 저장소에서 제거되었다. 좌표 이동·합법성 검사를 새로 넣을 때는 본 문서의 명제를 그대로 만족시켜야 한다.

## 남북 방향 주의

**`x == 0`인 세로선은 존재하지 않는다**고 가정한다. 라우팅·가시화·테스트 좌표를 잡을 때 **`x = 0` 근처에서 남북 복도를 가정하지 않는다.**

## 서버·API

디코드 후 **`X == 0`인 엔트리는 계산·요약·API 출력에서 제외**한다. 상위 레이어 규약은 [`.cursor/rules/architecture.mdc`](../../.cursor/rules/architecture.mdc) 를 본다.

## 관련 문서·코드

- 규칙 요약: [`AGENTS.md`](../../AGENTS.md) (블루프린트 좌표 한 줄)
- 아키텍처: [`.cursor/rules/architecture.mdc`](../../.cursor/rules/architecture.mdc)
