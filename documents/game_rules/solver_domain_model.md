# 솔버 내부 표현 (shapez_core 정본)

아래는 이 레포에서 실제로 쓰는 [`django_apps/shapez_core/domain/shape.py`](../../django_apps/shapez_core/domain/shape.py) 타입이다.

## ShapePart

| 필드 | 의미 |
| --- | --- |
| `kind` | 형태 코드 한 글자: `C` 원, `R` 사각, `S` 스파이크, `W` 마름모, `c` 크리스탈, `P` 핀, `-` 빈 칸 |
| `color` | 색 코드 한 글자 (`u`,`r`,`g`, … 또는 빈 칸 `-`) |
| `material` | 구현 메타: 예 `solid`, `empty`, `pin`, `crystal` |

빈 quadrant는 **`EMPTY_PART`** (`kind=="-"`, `color=="-"`)로 표현한다. `None`을 쓰지 않는다.

파서·카탈로그 매핑은 [`shape_catalog.py`](../../django_apps/shapez_core/domain/shape_catalog.py)를 본다.

## ShapeLayer

- `quadrants`: 길이 4 튜플, 순서 **SW, NW, NE, SE** ([shape_encoding.md](shape_encoding.md)).

## Shape

- `layers`: 아래층부터 위층까지의 `ShapeLayer` 튜플. 최소 1층.
- `canonical_code`: 각 층을 네 토큰을 이어붙이고, 층 사이에 `:`.

Crystal(`kind`=`c`)은 일반 도형과 다른 생성·파괴 규칙을 가진다 — [crystal_mechanics.md](crystal_mechanics.md), [`crystal_geometry.py`](../../django_apps/shapez_core/domain/crystal_geometry.py).

## 관련

- [shape_encoding.md](shape_encoding.md)
- [core_abstraction.md](core_abstraction.md)
