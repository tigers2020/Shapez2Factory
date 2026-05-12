# Shapez 2: Cutter 출력 순서 (east / west)

## 이 레포 구현 (`OperationEngine.cut` / `cut_vertical_halves`)

분면 인덱스는 [shape_encoding.md](shape_encoding.md) 기준 **SW, NW, NE, SE** 이다. 수직 절단은 **서쪽 반(west)** 과 **동쪽 반(east)** 으로 나뉜다.

| 출력 | 유지되는 분면 | 의미 |
| --- | --- | --- |
| 튜플 `[0]` | `quadrants[0]`, `quadrants[1]` | **west** (SW+NW) |
| 튜플 `[1]` | `quadrants[2]`, `quadrants[3]` | **east** (NE+SE) |

반환값은 **`(west_half, east_half)`** 순서다. Shapez 2 위키에서 말하는 “east가 메인 출력”과 **순서가 다를 수 있으므로**, 그래프에서 cutter 출력 포트를 연결할 때 이 순서를 기준으로 한다.

## 위키 참고 (게임 쪽 주장)

wiki.gg 검색 스니펫·요약에 따르면, Cutter는 도형을 수직으로 반절 자르고:

- **east half → main output**
- **west half → secondary output**

으로 나온다는 설명이 있다.

```text
게임 UI 관점 (참고) — 레포 튜플 순서와 혼동 금지
```

## 프로젝트 주의

출력 순서가 레시피 그래프의 **포트 번호·배선 방향**과 다르면 전체 DAG가 잘못 연결된다.

## 신뢰도·확인 필요

- 위키 **중간**. 원문 페이지 접근이 제한되거나 스니펫만 본 경우가 있다.
- 구현 시에는 **실제 게임 내 관측** 또는 공식 패치노트로 확인하는 것을 권장한다.

## 관련

- [operation_cutter.md](operation_cutter.md)
