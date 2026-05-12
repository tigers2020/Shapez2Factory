# 솔버 연산 인터페이스·코드 매핑

## 도메인 Protocol (`shapez_core`)

[`django_apps/shapez_core/domain/operation.py`](../../django_apps/shapez_core/domain/operation.py):

```python
class Operation(Protocol):
    name: str
    input_count: int
    output_count: int

    def apply(self, inputs: tuple[Shape, ...]) -> tuple[Shape, ...]:
        ...
```

`Shape` 타입은 [solver_domain_model.md](solver_domain_model.md).

## 실행 엔진 (`shapez_solver`)

레시피·매크로에서 실제로 쓰는 진입점은 [`OperationEngine.apply`](../../django_apps/shapez_solver/services/operation_engine.py)(`OperationType` + `Recipe.color` 등). UI 메타(라벨·아이콘·입출력 개수)는 [`operation_catalog.py`](../../django_apps/shapez_solver/domain/operation_catalog.py)의 `OPERATION_CATALOG`.

## `OperationType` ↔ 동작 (요약)

| `OperationType` 값 | 입·출 (정의) | 구현 / 비고 |
| --- | --- | --- |
| `cutter` | 1 → 2 | `cut_vertical_halves` → `(west, east)` ([shape_encoding.md](shape_encoding.md)) |
| `half_destroyer` | 1 → 1 | west만 유지 |
| `splitter` | 1 → 2 | 동일 shape 복제 |
| `swapper` | 2 → 2 | 단일 층만: `swap_half_planes_single_layer` (동쪽 반(NE+SE) 교환) |
| `rotate_cw` / `rotate_ccw` / `rotate_180` | 1 → 1 | [`shape_operations`](../../django_apps/shapez_core/domain/shape_operations.py) |
| `stacker` | 2 → 1 | bottom+top, 병합 실패 시 층 쌓기 + 중력·상한([`operation_engine`](../../django_apps/shapez_solver/services/operation_engine.py)) |
| `painter` | 1 → 1 | `color` 인자 필수 |
| `color_mixer` | 2 → 1 | `color_mix_semantics` |
| `pin_pusher` | 1 → 1 | 핀 층 + 후처리 |
| `crystal_generator` | 2 → 1 (카탈로그) | [`crystal_fill`](../../django_apps/shapez_core/domain/crystal_geometry.py); 엔진은 첫 shape만 사용. 색: `apply_operation`의 `crystal_color`, 또는 그래프 노드 `crystal_color`, 또는 **두 번째 입력 shape 균일 색** 추론 — [crystal_mechanics.md](crystal_mechanics.md) |

## 순수 변환 vs 솔버 정책

- **순수(좌표만)**: 회전·수직 절반·동쪽 반 교환·같은 층 비연속 병합 → [`shape_operations.py`](../../django_apps/shapez_core/domain/shape_operations.py).
- **Crystal**: 생성·클러스터·shatter → [`crystal_geometry.py`](../../django_apps/shapez_core/domain/crystal_geometry.py).
- **정책·근사**: 적층 후 중력, 최대 4층, Painter, Color mixer, Pin → [`operation_engine.py`](../../django_apps/shapez_solver/services/operation_engine.py).

## 원칙

- I/O·DB·HTTP는 도메인 밖으로 분리한다 ([architecture.mdc](../../.cursor/rules/architecture.mdc)).
