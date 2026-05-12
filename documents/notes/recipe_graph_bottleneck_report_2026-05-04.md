# 레시피 그래프 경로 병목 구간 보고서

작성일: 2026-05-04  
범위: `graph_document` 검증·재계산(`recompute_graph_document`) 및 스태프 API/뷰에서 이를 호출하는 경로.  
근거: 코드 정적 분석, `cProfile`로 확인된 핫스팟(대형 체인 문서·연산 다수 시나리오), 호출부 추적.

---

## 1. 요약

| 우선순위 | 구간 | 성격 |
|----------|------|------|
| 높음 | `validate_graph_document` → `copy.deepcopy` | 매 `recompute`·다수 API마다 문서 전체 깊은 복사 |
| 높음 | 스태프 재계산 API의 **이중 검증** | `validate_graph_document` 후 `recompute_graph_document`가 내부에서 다시 `validate` → `deepcopy` 2회 |
| 높음 | `apply_operation` → `parse_shape` → `shapez_core` 파서 | 연산마다 입력 `shape_code` 문자열 파싱(동일 코드 반복 시 중복) |
| 중간 | `operation_semantics` 내 `OperationEngine()` 반복 생성 | `rotate`/`cut`/`swap` 등 분기마다 엔진 인스턴스 할당 |
| 중간 | `assert_recipe_graph_edge_topology` | 엣지당 노드 조회·규칙 검사 `O(E)` (검증 단계에 포함) |
| 중간 | `_operation_dep_pairs_from_shape_links` | shape별 producer×consumer 전치(팬인·팬아웃이 크면 `O(P×C)` 폭증 가능) |
| 낮음~중간 | `validate_recipe_graph_context` | 노드 순회 + 타깃별 패밀리 정합(`explain_pattern_family_mismatch` 등) |
| 낮음 | `macro_pattern_staff_api_recipe_graph_recompute` 응답 조립 | `serialize_macro_recipe_visual`이 `enrich_react_flow_with_macro_visual_previews` 안에서 **재호출** 가능 |
| 낮음 | `graph_cost_hint_from_document` / `try_linear_operation_sequence` | 노드 리스트 선형 스캔 수준 |

---

## 2. 측정으로 확인된 항목 (재계산 루프)

대략 120개 연산의 선형 체인 `graph_document`에 대해 `recompute_graph_document`를 다수 반복 호출해 `cProfile`(cumtime)을 본 결과, **최적화 전**에는 다음이 상위에 있었다.

- `index_recipe_graph_nodes_by_id` (연산마다·입력 정렬마다 중복 호출)
- `_sorted_input_codes_for_operation` + 전체 엣지 스캔
- `_output_edges_for_operation` (연산마다 전체 엣지 스캔)

→ 해당 부분은 `recipe_graph_recompute.py`에서 **엣지 인접 리스트·`node_by_id` 재사용**으로 완화됨.

**최적화 후** 같은 시나리오에서 상위에 남은 것은 주로:

- `validate_graph_document` 경로의 `deepcopy`
- `apply_operation` → `parse_shape` / `shape_code_parser`

---

## 3. 경로별 상세

### 3.1 `recompute_graph_document` 내부

파일: `django_apps/shapez_solver/services/recipe_graph_recompute.py`

1. **`validate_graph_document(doc)`** (항상 1회)  
   - `copy.deepcopy(raw)`: 문서 크기에 비례 `O(|nodes|+|edges|)` 시간·메모리.  
   - 노드·엣지 형식 검사, `assert_recipe_graph_edge_topology`, `assert_delivery_targets_unique`.

2. **`index_recipe_graph_nodes_by_id(nodes)`**  
   - `O(N)`. 재계산 루프 안에서는 더 이상 연산마다 반복하지 않음.

3. **`_operation_dependency_edges`**  
   - 엣지 1패스 + `_operation_dep_pairs_from_shape_links`.  
   - 동일 intermediate에 다수 producer·consumer가 붙는 비정형 그래프에서 의존 쌍 수가 커질 수 있음.

4. **`_topological_operation_order`**  
   - 일반적으로 `O(|ops| + |dep_pairs|)`.

5. **`_edge_adjacency`**  
   - `O(E)` 1회.

6. **연산 루프**  
   - 입력 코드 정렬: 해당 연산의 입력 엣지 수에 비례(전체 `E` 매번 스캔은 제거됨).  
   - 출력 엣지 정렬: 해당 연산의 출력 엣지 수에 비례.  
   - **`_apply_recomputed_operation` → `apply_operation`**: 병목 후보(아래 3.3).

7. **`_apply_delivery_edges`**  
   - delivery 엣지 수에 선형. `node_by_id` 인자로 중복 인덱싱 제거됨.

### 3.2 HTTP: 스태프 그래프 재계산 API

파일: `django_apps/web/views.py` — `macro_pattern_staff_api_recipe_graph_recompute`

흐름 요약:

1. `validate_graph_document(...)` (클라이언트 페이로드) → **`deepcopy` 1회**
2. `recompute_graph_document(validated)` → 내부에서 **`validate_graph_document` 다시** → **`deepcopy` 2회째** (동일 논리 문서에 대해 연속)

추가로 같은 요청에서 대략:

- `serialize_macro_recipe_visual(doc)`
- `validate_recipe_graph_context(...)`
- `graph_cost_hint_from_document(doc)` / `try_linear_operation_sequence(doc)`
- `domain_graph_to_react_flow(doc)`
- `enrich_react_flow_with_macro_visual_previews(react_flow, doc)` → 내부에서 **`serialize_macro_recipe_visual(graph_doc)` 재호출**

→ UI 응답 한 번에 검증·시각화·직렬화가 겹칠 수 있음.

### 3.3 `apply_operation` / `OperationEngine` 인스턴스화

파일: `django_apps/shapez_solver/services/operation_semantics.py`

- 대부분의 분기에서 `parse_shape(shape_code)`로 문자열 → `Shape` 변환.
- `rotate`, `cut`, `swap`, `stack` 등에서 **`OperationEngine()`을 호출마다 새로 생성**.  
  - 할당·초기화 비용이 연산 수×호출에 누적(프로파일에서 회전 연산이 두드러졌던 원인 중 하나).

파서·도메인 로직: `django_apps/shapez_core/services/shape_code_parser.py`, `shape_codec.py` 등.

### 3.4 검증·토폴로지

파일: `django_apps/shapez_solver/services/recipe_graph_topology.py`

- `assert_recipe_graph_edge_topology`: 노드 인덱스 1회 + 엣지 `O(E)`.
- `assert_delivery_targets_unique`: delivery 엣지 `O(E)`.

### 3.5 패턴 매크로 스텝 추출

`try_pattern_macro_step_rows_from_graph_document`:  
`validate_graph_document` 1회(또는 매크로 경로의 선행 검증) + 위와 유사한 토포·인접 구축. 엣지/노드 규모에 선형.

### 3.6 기타 호출부에서의 `validate_graph_document`

- `macro_recipe_staff_catalog` 저장 시  
- `macro_recipe_graph_visual` (`document_to_solver_graph` 등)  
- GET 그래프 페이지: `macro_pattern_graph`에서 `validate_graph_document` + `domain_graph_to_react_flow` + `enrich_...`

각각 `deepcopy` 비용이 붙을 수 있음.

---

## 4. 이미 완화된 병목 (참고)

- 연산 루프에서 **전체 엣지 반복 스캔** 제거 (`_edge_adjacency`, `_sorted_output_edges_for_operation`).
- `_sorted_input_codes_for_operation`에서 **연산마다 `index_recipe_graph_nodes_by_id` 재구축** 제거.
- `_apply_delivery_edges`에서 **불필요한 노드 인덱스 재구축** 제거.

---

## 5. 권장 후속 (우선순위)

1. **`recompute_graph_document` 입구**: 이미 `validate_graph_document`를 통과한 dict만 받는 오버로드 또는 “복사 생략” 옵션(호출 계약·보안·변조 방지와 함께 설계).  
2. **스태프 API**: `validate` 1회만 수행하도록 호출 순서 조정(내부 전용 `recompute` 경로).  
3. **파싱 캐시**: 한 번의 `recompute` 호출 범위에서 `shape_code` → 파싱 결과(또는 canonical) 캐시.  
4. **`OperationEngine`**: 모듈 수준 단일 인스턴스 또는 재사용(스레드 안전성 확인 후).  
5. **응답 조립**: `serialize_macro_recipe_visual` 결과를 `enrich_*`에 재전달해 이중 계산 방지.  
6. **드문 최악**: `_operation_dep_pairs_from_shape_links` 폭증 그래프는 도메인 제약 또는 알고리즘 재검토.

---

## 6. 관련 파일 목록

| 파일 | 역할 |
|------|------|
| `django_apps/shapez_solver/services/recipe_graph_recompute.py` | 검증·재계산·패턴 스텝 추출 |
| `django_apps/shapez_solver/services/recipe_graph_topology.py` | 엣지 토폴로지·인덱스 |
| `django_apps/shapez_solver/services/operation_semantics.py` | `apply_operation`·파싱·엔진 호출 |
| `django_apps/shapez_core/services/shape_code_parser.py` | shape 코드 파싱 |
| `django_apps/web/views.py` | 스태프 그래프 API·페이지 |
| `django_apps/shapez_solver/services/macro_recipe_graph_visual.py` | 시각 그래프·React Flow 보강 |
| `django_apps/shapez_solver/services/recipe_graph_recipe_validation.py` | 패밀리 맥락 검증 |

---

문서 끝.
