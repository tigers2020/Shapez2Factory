# Crystal 시스템 (메커니즘 요약)

문서 목적: 솔버·UI에서 **Crystal을 일반 색칠 파트와 분리**하고, 생성·클러스터·파괴 전파를 동일 언어로 맞춘다. 게임과 1:1일 필요는 없으며, 규칙 세부는 패치·실측으로 교차 검증한다.

## 근거 신뢰도

| 근거 | 내용 | 신뢰도 |
| --- | --- | --- |
| Shapez 2 Wiki 검색 | Crystal Generator는 gap·pin에 crystal 생성, highest used layer까지 적용 | 높음(위키, 교차 검증 권장) |
| Shapez 2 Shapes Wiki 검색 | Crystal 연결 구조가 깨지면 연결된 crystal 전체가 함께 깨짐 | 높음(위키) |
| Steam 커뮤니티 | floating crystal, pin/gap, cluster breaking 논의 | 중간(유저 실험) |

---

## 핵심 정의

Crystal은 일반 Circle/Rectangle 등과 **다른 특수 fill material**이다. 솔버 관점:

```text
Crystal = 빈 칸(gap) 또는 pin 칸을 특정 색의 결정(kind=c, color=색코드)으로 채운 파트
```

코드 인코딩: 한 칸은 두 글자 토큰. Crystal은 `c` + 색 한 글자(예: cyan → `cc`). 일반 원 빨강은 `Cr` 등과 **구분**해야 한다.

---

## 1. Crystal Generator (생성)

입력: 가공 대상 **shape** + **색(color fluid의 색 코드)**.

### 레시피 그래프(와이어 타입)

그래프 검증에서 **material / fluid** 는 게임의 “크리스털 재료”가 아니라 **와이어 캐리어**다.

- **material**: 일반 **도형** 노드에서 오는 연결(`shape_code` 기하 흐름).
- **fluid**: `source_carrier=fluid` 인 **순색 유체** 노드에서 오는 연결.

Crystal Generator 노드는 다음 둘 중 하나다.

1. **`crystal_color`가 비어 있지 않음** → 입력 **1개**(도형 한 줄, material만). 색은 노드 필드.
2. **`crystal_color` 없음(또는 공백)** → **페인터와 동일**: 상단 `in-1`(슬롯 `1`)에 **fluid**, 하단 `in`에 가공 대상 **도형(material)**. 유체에서 색을 읽는다([`pure_fluid_color`](../../django_apps/shapez_solver/services/fluid_semantics.py)).

도메인 연산 시그니처는 여전히 “도형 + 확정 색 한 글자”이며, 2와선 경우 그래프가 유체·도형 두 와이어를 정렬해 [`apply_operation` … CRYSTAL_GENERATOR](../../django_apps/shapez_solver/services/operation_semantics.py)에 넘긴다.

동작(이 레포 구현, [`crystal_fill_gaps_and_pins`](../../django_apps/shapez_core/domain/crystal_geometry.py)):

1. `highest_used_layer_index(shape)`까지의 각 레이어를 대상으로 한다. 그 위에 **새 빈 레이어를 만들지 않는다**.
2. 각 분면이 **empty(`--`)이거나 pin(`P-`)** 이면 해당 색의 crystal 파트로 바꾼다.
3. 일반 도형 파트가 있는 칸은 유지한다.

예(레이어 문자열은 [shape_encoding.md](shape_encoding.md) 순서):

```text
입력 Layer 0: `Ru--Ru--` (SW=Ru, NW=--, NE=Ru, SE=--)에 cyan(`c`) 적용 시 토큰은 `RuccRucc`.
색: cyan → 색 코드 `c`, crystal 토큰 `cc`
```

주의:

```text
“사용 중인 최고 레이어”까지만 채운다 ≠ 빈 레이어를 위로 새로 쌓는다.
```

중간에 완전 빈 레이어가 끼어 있는 형태는 스택 모델에서 가능할 수 있다. 해당 레이어의 모든 `--`도 crystal 후보가 된다.

---

## 2. Gap filler 성격

Crystal은 소스에서 직접 채굴된 파트가 아니라, **기존 gap/pin을 채워** 만들어진다. 따라서 목표가 `RuccRucc`라면, 그 전 단계에 **gap/pin을 포함한 베이스 shape + 유체 색**이 선행되어야 한다.

---

## 3. Pin과 Crystal

Generator는 **pin도 crystal로 바꿀 수 있다.** 최종적으로 pin을 유지해야 한다면:

- Crystal Generator **이후**에 Pin Pusher 등으로 pin을 다시 만들거나,
- pin이 crystal로 바뀌어도 되는 **중간 단계**에서만 crystalize 한다.

---

## 4. Crystal cluster와 Shattering

위키·커뮤니티 요지: **한 crystal이 구조적으로 깨지면, 연결된 crystal 클러스터 전체가 함께 깨진다.**

이 레포의 **근사 모델** ([`crystal_geometry`](../../django_apps/shapez_core/domain/crystal_geometry.py)):

- **같은 레이어**: 한 레이어에서 분면은 링으로 인접(SW–NW–NE–SE 둘레).
- **수직**: 같은 분면 인덱스의 위·아래 레이어.

이 인접 그래프에서 crystal만 통과하는 BFS로 `connected_crystal_cluster`를 구하고, `shatter_crystal_cluster`는 클러스터 전체를 `--`로 바꾼다.

정확한 인접·파괴 트리거(절단선이 어디를 “건드렸는지”)는 **게임 확정 전 근사**다. Cut/Swap/Stack 직후 전역 shatter 연결은 향후 `OperationEngine` 정책 단계에서 붙인다.

---

## 5. Floating crystal

위층 crystal이 아래층 gap 위에만 얹힌 형태 등은 **생성·유지가 매우 제한적**일 수 있다. 솔버에서는 기본적으로 **도달 후보에서 제외하거나** 고비용·별도 탐색 레이어로 두는 편이 안전하다.

---

## 6. 연산별 메모 (설계)

| 연산 | Crystal 관련 |
| --- | --- |
| Cutter | 절단이 클러스터를 나누면 shatter 가능 — 구현 시 규칙 확정 필요 |
| Swapper | 반쪽 교환으로 클러스터 분리·충돌 시 위험 — 후보 pruning 권장 |
| Stacker | crystal·지지 구조 충돌 시 깨짐 가능 — 스택 후 검증·가지치기 |
| Pin Pusher | crystalize 순서와 조합 시 핀 보존 전략 필요 |

현재 **연산 엔진**은 Generator fill과 클러스터·shatter **순수 함수**를 제공하며, Cut/Swap/Stack에 자동 shatter를 붙이지는 않았다.

---

## 7. 그래프·매칭

미리보기·타깃 매칭에서 normal part / pin / crystal / gap을 **시각·식별자 모두 구분**한다. `gap == pin`은 항상 성립하지 않는다.

---

## 8. 구현 파일 맵 (이 레포)

| 구분 | 경로 |
| --- | --- |
| 생성·클러스터·shatter | [`django_apps/shapez_core/domain/crystal_geometry.py`](../../django_apps/shapez_core/domain/crystal_geometry.py) |
| Generator 연산 | [`OperationEngine`](../../django_apps/shapez_solver/services/operation_engine.py), [`apply_operation` … CRYSTAL_GENERATOR](../../django_apps/shapez_solver/services/operation_semantics.py) — 색은 노드 `crystal_color` 또는 **2와선 시 상단 유체(`pure_fluid_color`)** |
| 레시피 그래프 재계산 | [`recipe_graph_recompute`](../../django_apps/shapez_solver/services/recipe_graph_recompute.py) — `crystal_generator`는 `crystal_color` 유무에 따라 **1입력 또는 2입력**(2입력은 fluid+material, 페인터와 동일 핸들 규칙) |
| 파트 타입 | [`ShapePart.is_crystal`](../../django_apps/shapez_core/domain/shape.py), [`SHAPE_KINDS["c"]`](../../django_apps/shapez_core/domain/shape_catalog.py) |

---

## 9. 요약 네 줄

1. Crystal Generator는 highest used layer까지 **gap/pin**을 지정 색 crystal로 채운다.
2. Crystal은 일반 도형 파트가 아니라 **fill material**이다.
3. 깨짐 시 **연결 crystal 클러스터**가 함께 제거되는 규칙을 쓰려면 cluster 그래프가 필요하다.
4. Pin·gap·floating 조합은 난이도가 높아 **단계별 솔버**로 나누는 것이 안전하다.

## 관련 문서

- [shapez2_crystal.md](shapez2_crystal.md) — 위키 참고·링크
- [shapez2_pin_support.md](shapez2_pin_support.md)
- [solver_operation_interface.md](solver_operation_interface.md)
