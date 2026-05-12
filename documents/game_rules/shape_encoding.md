# 도형 코드 구조 (이 프로젝트 정본)

## 공식 viewer와의 차이 (참고)

공식 shape viewer 등에서는 레이어 문자열을 **우상단부터 시계방향**(NE → SE → SW → NW)으로 두 글자 토큰이 나열된다고 소개하는 경우가 많다.

**shapez2Solver 레포의 구현 정본은 그와 다르다.** 파서·`Shape.canonical_code`·[`django_apps/shapez_core/domain/shape_pattern.py`](../../django_apps/shapez_core/domain/shape_pattern.py)의 분면 순서는 아래 **프로젝트 표**를 따른다. 문자열을 공식 도구에 그대로 붙여 넣으면 동일 비주얼이 안 나올 수 있다.

## 이 프로젝트: 레이어 한 줄(8자) 토큰 순서

한 레이어는 네 개의 **두 글자 토큰**으로 이루어진다(형태 1자 + 색 1자). **토큰 인덱스와 나침반·내부 배열 인덱스**는 다음과 같다.

| 토큰 인덱스 (0~3) | `ShapeLayer.quadrants[i]` | `QuadrantPosition` |
| --- | --- | --- |
| 0 | `quadrants[0]` | SW |
| 1 | `quadrants[1]` | NW |
| 2 | `quadrants[2]` | NE |
| 3 | `quadrants[3]` | SE |

즉 레이어 문자열은 **SW → NW → NE → SE** 순으로 이어진다.

## 예시 문자열

```text
RuCw--Cw:----Ru--
```

## 해석 예 (이 프로젝트 좌표계)

```text
Layer 0 (아래층): SW=Ru, NW=Cw, NE=--, SE=Cw  →  RuCw--Cw
Layer 1 (위층):   SW=--, NW=--, NE=Ru, SE=--  →  ----Ru--
```

## 규칙 요약

| 요소 | 의미 |
| --- | --- |
| `:` | 레이어 구분 |
| 레이어 순서 | **아래층 → 위층** |
| 한 레이어 | **4개 quadrant**, 각각 **2글자 토큰** |
| 토큰 순서 | **SW, NW, NE, SE** (`shape_pattern.quadrant_at_index`와 동일) |
| `Ru` 등 | 형태 타입 문자 + 색 문자 |
| `--` | 빈 quadrant |

## 솔버 구현 메모

- 문자열 ↔ `Shape` 변환의 단일 축: [`django_apps/shapez_core/services/shape_code_parser.py`](../../django_apps/shapez_core/services/shape_code_parser.py), [`shape_codec.py`](../../django_apps/shapez_core/services/shape_codec.py).
- 회전·절단의 치환 정의는 [operation_rotater.md](operation_rotater.md), [`shape_operations` 모듈](../../django_apps/shapez_core/domain/shape_operations.py)와 테스트가 정본이다.
