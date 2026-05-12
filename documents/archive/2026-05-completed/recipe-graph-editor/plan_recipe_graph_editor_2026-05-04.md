# Recipe Graph Editor — 플랜 (2026-05-04 개정)

## 제품 정의

**겉보기(Look & feel)**는 Lucidchart / draw.io / Figma flow / Node-RED와 같다.

- 노드 드래그, 선(엣지) 연결, 확대/축소·팬, 선택, 컨텍스트 메뉴, 블록 배치

**본질**은 그림 도구가 아니라 **실행 가능한 도메인 그래프 편집기(Domain-specific visual graph editor)**다.

- Lucidchart: “사람이 생각한 것을 그림으로 표현”
- 본 에디터: “사람이 그래프를 조작하면 **시스템이 recipe 의미를 계산·검증**하고, **중간 산출물과 수량·타깃 만족 여부를 재계산**한다”

비교 축: Node-RED / ComfyUI / Unreal Blueprint처럼 **연결이 의미(데이터 흐름)**를 갖되, 도메인은 **Shapez2 recipe + solver**다.

권장 명칭: **Recipe Graph Editor** (매크로 카탈로그 전용 UI의 상위 개념으로도 사용 가능).

**시각 편집 CRUD(추가·수정·삭제)** — 사용자가 기대하는 핵심 가치를 한 번 더 고정한다: 캔버스에서 **노드·엣지를 추가**하고, 속성·연결·배치를 **수정**하며, 불필요한 요소를 **삭제**한다. JSON·API만으로 그래프를 맞추는 것은 보조 수단이며, Lucidchart 감각의 본체는 이 CRUD 루프다.

---

## 아키텍처 4계층

### 1) Visual Layer (Lucidchart 감각)

- 노드 위치, 선택, 드래그, 연결 핸들, 줌/팬, (선택) 그룹
- **시각 편집 CRUD**: 노드·엣지 **추가**, 선택 항목 **수정**(속성/연결/좌표), **삭제** — 솔버 페이지 **Live preview**와 동일 계열의 그래프 타일·와이어 시각화 위에서 이루어진다.
- operation 노드 / shape 노드 시각 구분 — 기존 솔버 그래프 마크업(`renderSolverGraph`, `initGraphViewport`)을 **재사용·일반화**하는 방향 유지

### 2) Graph Model Layer (진실 데이터)

최소 개념(이름은 구현 시 DTO/TS 타입으로 정리):

- **ShapeNode**: `canonical_shape_code`, 수량, 역할(source / intermediate / target 후보)
- **OperationNode**: `OperationType`, 포트 정의(입력 수·출력 수)
- **Edge**: from/to, kind(input|output), slot/라벨(포트 식별)
- (확장) 배치·스타일: `node_positions` 등

저장소: 기존 `MacroRecipe` + `MacroRecipeStep`만으로는 **임의 DAG + 좌표**를 표현하기 부족하다. 아래 중 하나를 채택해야 한다.

- **A안(권장)**: `MacroRecipe.graph_document`(JSON) 하나에 **노드·엣지·좌표**를 넣고, `MacroRecipeStep`은 Pattern Lab 하위 호환용 **파생 스냅샷**으로 유지하거나 점진 폐기
- **B안**: 정규화 테이블 `GraphNode`, `GraphEdge` (마이그레이션 부담 큼)

본 개정안은 **A안**을 기본으로 서술한다.

### 3) Solver Layer (계산·검증)

- **그래프 유효성**: DAG, 포트 arity, `OperationType`별 입력 개수, (필요 시) single-layer 등 기존 제약
- **연산 결과**: 입력 shape 코드(들) + 연산 → **출력 canonical 코드(들)** — 도메인은 `shapez_core` + `OperationEngine` / [`apply_operation`(../../../../django_apps/shapez_solver/services/operation_semantics.py) 계열로 통일
- **전파(propagation)**: 한 엣지/노드 변경 시 **하류 노드**를 위상순서로 재계산
- **검증**: 타깃 만족, (스코프에 있으면) throughput/quantity — 기존 solver 서비스와의 연계 지점을 명시적으로 “포트”로 둔다

**현실 제약(중요)**: `apply_operation`는 현재 **일부 연산만** 지원한다(회전, cutter, swapper, stacker 등). 카탈로그의 모든 `OperationType`을 에디터에서 열려면 **OperationEngine 경로로 확장**하거나 연산별 어댑터를 두는 **로드맵**이 필요하다. Phase 1은 “지원 연산만 에디터에서 활성”으로 가도 된다.

### 4) Sync Layer (UI ↔ Solver)

```text
사용자: 연결/이동/삭제/연산 변경
  → graph mutation (Graph Model)
  → validate + topological order
  → 각 OperationNode에 대해 apply_operation(OperationEngine)
  → 새 ShapeNode(중간 결과) 생성/갱신 + 엣지 자동 생성(“추가 연결”)
  → UI refresh (Visual)
```

사용자 요구를 한 줄로 고정:

> **베이스 도형 노드와 operation 노드를 연결하면 output이 자동 계산되어 노드(및 연결)로 추가되고, 그 output을 다음 operation에 연결하면 다음 결과도 자동으로 추가·연결되어야 한다.**

이는 **단순 JSON 슬롯 문자열 편집이 아니라**, 연결 그래프가 **실행 의미**를 갖고, **하류가 항상 엔진 결과와 동기**되어야 함을 의미한다.

---

## 동작 알고리즘(연결 시 자동 산출)

1. 사용자가 **입력 포트에 맞는 수의** Shape 노드(또는 이미 계산된 intermediate)를 operation의 **input 엣지**로 연결한다.
2. Sync Layer가 해당 OperationNode를 **준비됨(ready)**으로 표시할지 판단: 필수 입력 arity 충족, shape 코드 파싱 가능.
3. `OperationType`에 대해 **도메인 연산** 실행 → 출력 tuple of canonical codes.
4. 각 출력에 대해:
   - 기존 **출력 Shape 노드**가 있으면 갱신, 없으면 **새 Shape 노드 생성**
   - Operation **출력 포트 → Shape 노드** 엣지를 **자동 생성**(사용자가 “선을 그었다”기보다 **결과물이 생기며 연결된 것처럼** 보이게 할지, 아니면 고스트 엣지 후 확정할지 UX 결정 필요 — 기본은 **자동 실선 엣지 + 노드 스폰**이 요구사항에 부합)
5. 변경된 Shape 노드에 **연결된 하류 OperationNode**를 큐에 넣고 2~4 반복(고정점까지 또는 사이클/오류 시 중단).

**사이클·모호함**: solver DAG 전제와 같이 **사이클 금지**; 다중 입력 대기 시 부분 실행 금지 등 정책을 문서화한다.

---

## 기존 “매크로 스태프 카탈로그” 플랜과의 관계

- 이전 초안의 `graph_editor`(좌표만) + `steps` 이중 진실은, 본 개정에서 **Graph Model이 주 진실**이 되도록 재배치한다.
- Pattern Lab / DB 매크로 후보는 **graph_document에서 steps 요약을 파생**하거나, 초기에는 **graph만 저장**하고 Lab은 제한적으로 읽는 등 **호환 전략**을 별도 체크리스트로 둔다.

---

## 구현 단계(로드맵)

| Phase | 내용 |
|--------|------|
| P0 | 4계층 스펙 고정, `graph_document` 스키마 초안, 지원 `OperationType` 목록(엔진 기준) |
| P1 | Visual: 솔버 그래프 컴포넌트 재사용 + 포트/연결 UX + **시각 편집 CRUD(추가/수정/삭제)** 뼈대 |
| P2 | Sync: 연결 완료 시 `apply_operation`/Engine 호출 → 출력 노드·엣지 자동 생성·하류 재계산 |
| P3 | 검증: 타깃/수량, 에러 UI, 부분 그래프 invalid 표시 |
| P4 | 지원 연산 확대, throughput 연동(필요 시 별도 서비스) |

## 개발 진행 원칙

- **페이즈 순서(P0→P4)**를 기본으로 하고, 의존 관계상 일부 백엔드·스키마가 UI보다 먼저 올라가는 것은 허용하되, **시각 편집 CRUD**는 P1·P2에서 요구사항으로 명시적으로 채운다.
- 한 페이즈 안에서도 **작은 단위로 쪼개 검증**하고, 회귀를 막을 테스트·재계산 경로를 유지한 채 **순차적·보수적으로** 진행한다(급하게 다음 페이즈 표면만 넓히지 않는다).

---

## 산출물·승인

- 본 문서는 `documents/` 플랜 개정본이다. 구현 착수 전 **사람 승인** 게이트는 저장소 규칙([AGENTS.md](../../../../AGENTS.md))을 따른다.
- 구현 시 터치 예상 경로: `django_apps/shapez_solver/services/operation_semantics.py` 확장, (신규) `recipe_graph_*` 서비스/DTO, `django_apps/web/static/...` 그래프 모듈 일반화, `MacroRecipe` 마이그레이션.

---

## 오픈 이슈(승인 시 결정 권장)

1. **출력 자동 연결 UX**: 엔진이 낸 출력을 **항상 자동 노드+엣지로 스폰**할지, 사용자가 “확정”할 때까지 프리뷰만 할지.
2. **저장 단위**: 레시피당 하나의 `graph_document` vs 버전 히스토리.
3. **Pattern Lab 동기**: 읽기 경로는 `graph_document`에서 파생 스텝(`try_pattern_macro_step_rows_from_graph_document`)을 우선한다. DB `steps`와의 **쓰기** 일치는 선택 사항.

---

## 구현 진행 현황 (2026-05-04)

| Phase | 상태 | 비고 |
|--------|------|------|
| P0 | **부분 완료** | `MacroRecipe.graph_document` 필드 + 마이그레이션 `0003`, 스키마 상수 [`recipe_graph_constants.py`](../../../../django_apps/shapez_solver/services/recipe_graph_constants.py) |
| P2 | **부분 완료** | 서버 재계산 [`recipe_graph_recompute.py`](../../../../django_apps/shapez_solver/services/recipe_graph_recompute.py) (`validate_graph_document`, `recompute_graph_document`), 스태프 `POST .../recipes/<id>/graph/recompute/?` (`commit` 시 DB 저장), 카탈로그에 `recipe_graph_engine_operations` 노출 |
| P1 | **부분 완료** | 솔버 그래프: 연산·shape **포트**(와이어); 상세 **Copy node id**; `painter` `paint_color` 설명; 스태프 **엣지 append + 와이어**; **Pattern Lab 읽기 동기**: `graph_document`→파생 스텝 우선·`pattern_lab_steps` JSON. **시각 편집 CRUD(노드·엣지 추가/속성·연결 수정/삭제)는 미완 — P1·P2에서 순차 보강.** |
| P3 | **부분 완료** | 그래프 타깃 검증: `explain_pattern_family_mismatch`(Pattern Lab과 동일한 inventory + canonical 사분면 회전 시그니처 합집합); 문자열 순환 `_cyclic_signatures` 제거; 재계산 API·그래프 뱃지·스태프 이슈 목록 유지 |
| P4 | **부분 완료** | `painter` + **`color_mixer`**: `apply_operation` / `OperationEngine` / [`RECIPE_GRAPH_ENGINE_OPERATIONS`](../../../../django_apps/shapez_solver/services/recipe_graph_constants.py) / 재계산 2입력 분기; `paint_color`·[`color_mix_semantics`](../../../../django_apps/shapez_solver/services/color_mix_semantics.py)(MVP) |

**진행 스냅샷(별첨):** [`recipe_graph_editor_progress_2026-05-04.md`](recipe_graph_editor_progress_2026-05-04.md)

`apply_operation`이 지원하는 연산만 재계산에 사용한다(회전·cutter·swapper·stacker·**painter**·**color_mixer**).
