# Phase 2 — Pattern Library / Local DP Compiler

## 목적

Extractor + extension의 작은 로컬 패턴을 deterministic하게 생성한다.

이 단계의 DP/로컬 탐색은 전체 맵 최적화가 아니다.

```text
DP = local pattern compiler
```

## RouteGoal / probe와의 연결

패턴은 **offsets·`output_dir`·`output_stub_offset`** 로 기하를 고정한다. 오프셋·투영 후 절대 셀은 **Server X/Y** (`Coord`)이다. `RouteProbeInput.start`는 배치 후 `**output_stub` 절대 좌표**로 투영된다 (Phase 3). `RouteGoal` 집합·`RouteCellDomain`은 `OptimizationInput`에서 오며 패턴 DTO에 중복 저장하지 않는다.

확장기 부착 규칙(추출기·이전 확장기·R 방향 등)은 **v0 linear**에서는 암시적으로 복원 가능하지만, v1 분기·회전 후 facing 혼동을 막기 위해 **부착 그래프를 명시**한다.

## v0 패턴 범위

```text
extractor only
extractor + 1 extension
extractor + 2 extensions
extractor + 3 extensions
```

```text
T-shape
branch extension
ring pattern
nonlinear compact pattern
cross-resource pattern
```

**extractor 출구 방향 앞에는 항상 pipe/blet 가 붙는다.**  
*최대 크기 = pipe + extractor + 3 extension = 5*

## DTO

```python
@dataclass(frozen=True)
class ExtensionAttachment:
    extension_offset: Coord
    parent_offset: Coord
    required_facing: Direction
```

`v0 linear`: extractor가 parent이고, 각 extension은 직전 체인 셀을 parent로 둔다.

`required_facing`은 **extension 모듈 자신의 부착·출력 기준 방향**으로, **parent_offset 쪽을 바라보도록** 고정한다. 검증 시 `cardinal_unit_toward(extension_offset, parent_offset)`(또는 동일 의미의 `direction_from(extension → parent)`)와 **일치**해야 한다. Shapez2 게임 규칙이 반대 부호를 요구하면 구현은 그에 맞추되, **문서·테스트에 “어느 셀이 주체인지”**를 동일하게 고정한다.

```python
@dataclass(frozen=True)
class BundlePattern:
    pattern_id: str
    extension_count: int
    occupied_offsets: frozenset[Coord]
    extractor_offset: Coord
    extension_offsets: tuple[Coord, ...]
    attachments: tuple[ExtensionAttachment, ...]
    output_dir: Direction
    output_stub_offset: Coord
    throughput_factor: int
    topology_kind: str
```

### `throughput_factor` 의미 (고정)

게임 규칙: extractor base **×4**, extension당 **+×4**, 최대 extension 3 → 최대 **×16**.

`throughput_factor`는 **그 배수 정수**로만 취급한다: `4`, `8`, `12`, `16` (extractor-only=4, +1=8, …).

구현에서 `extension_count + 1` 등으로 **잘못 스케일링하지 않도록** 이름을 `throughput_multiplier`(모호) 대신 `throughput_factor`로 고정한다.

## Canonical 방향·회전

**Canonical 패턴:** 문서·라이브러리 기본 생성은 `**output_dir = E`(동쪽 출력)** 기준 오프셋을 만든다.

**회전:** canonical E 패턴을 `N/E/S/W`의 목표 `output_dir`로 변환한다 (좌표·`output_stub_offset`·`attachments.required_facing`·`occupied_offsets`를 동일 규칙으로 회전). 스프라이트·에디터 회전과 맞출 때도 이 기준을 따른다.

모든 패턴은 4방향 회전을 지원한다.

```text
N
E
S
W
```

## Throughput 모델

게임 처리량 **절대값 정본** (30 shapes/min, 300 L/min, Space Belt 480×12, Space Pipe 28.8kL/m×12, 포화 12/72): [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../game_rules/shapez2_asteroid_space_transport_throughput.md).

기본 모델:

```text
extractor base = x4
each extension = +x4
max extension = 3
max total = x16
```

즉:

```text
extractor only = x4
+1 extension = x8
+2 extension = x12
+3 extension = x16
```

## Invariant

```text
[ ] pattern_id deterministic
[ ] output_stub is not occupied
[ ] extractor_offset exactly one
[ ] extension_count <= 3
[ ] occupied_offsets contains extractor + extensions only
[ ] attachments 길이 == extension_count (v0 linear)
[ ] 회전 후 오프셋·투영이 Server 정수 격자에서 결정적
[ ] throughput_factor in {4, 8, 12, 16} and matches extension_count
```

## 테스트

```text
test_pattern_library_generates_linear_0_to_3_extensions
test_pattern_library_pattern_ids_are_deterministic
test_pattern_library_output_stub_not_occupied
test_pattern_library_rotations_deterministic_on_server_grid
test_pattern_library_throughput_factor_matches_extension_count
test_pattern_library_attachments_linear_chain
```

## 완료 조건

```text
[ ] linear pattern 0~3 extension 생성
[ ] 4방향 회전 지원
[ ] deterministic order 보장
[ ] output_stub 계산 완료
[ ] ExtensionAttachment·throughput_factor·canonical E 계약 반영
```

