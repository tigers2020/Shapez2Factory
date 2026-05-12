# 연산: Rotater (회전)

## 역할

도형의 **4분면 구성**을 회전에 따라 재배열한다. 솔버에서는 보통 **단순 permutation**으로 표현한다.

## 이 프로젝트 분면 순서

한 레이어의 `quadrants` 인덱스는 **[SW, NW, NE, SE]** (= `[0]` … `[3]`). 공식 viewer 문자열 순서와 다를 수 있음 → [shape_encoding.md](shape_encoding.md).

구현 정본은 [`django_apps/shapez_core/domain/shape_operations.py`](../../django_apps/shapez_core/domain/shape_operations.py) 의 `rotate_cw` / `rotate_ccw` / `rotate_180` 와 단위 테스트다.

## 치환 (인덱스 0~3에 대한 재배열)

`new[i]` 가 오래된 어느 인덱스에서 오는지:

| 연산 | `new[0]` (SW) | `new[1]` (NW) | `new[2]` (NE) | `new[3]` (SE) |
| --- | --- | --- | --- | --- |
| CW | old[3] | old[0] | old[1] | old[2] |
| CCW | old[1] | old[2] | old[3] | old[0] |
| 180° | old[2] | old[3] | old[0] | old[1] |

## 예시(개념)

다른 좌표 순서를 쓰는 문서의 문자열 예시와 **바이트 단위로는 일치하지 않을 수 있다.** 회전 검증은 프로젝트 shape 코드로 한다 (예: `RuSuCuWu` → CW 시 `WuRuSuCu`).

## 메모

- 다층 도형이면 **층마다 동일한 permutation**을 적용한다.
- 회전과 절단 순서는 생산 라인 최적화에서 핵심이다 ([operation_cutter.md](operation_cutter.md)).
