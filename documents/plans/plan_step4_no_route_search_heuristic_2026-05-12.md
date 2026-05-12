---
name: STEP4 no_route search heuristic audit (wide_search_exhausted)
overview: >
  dominant_blocker_category가 wide_search_exhausted일 때, STEP4 Dijkstra가 목표 집합·비용
  지형에서 넓게 퍼지며 소진되는 원인을 계측으로 먼저 확정하고, 전역 pop 상한을 무분별하게
  올리지 않는 범위에서만 탐색 순서·목표 축소 등 안전한 개선을 검토한다.
todos:
  - id: diag-spec
    content: search_stats·failure 행에 추가할 진단 필드 스펙 확정
    status: pending
  - id: diag-impl
    content: step4_dijkstra·merge_routing 계측 삽입(기본 동작 동일)
    status: pending
  - id: log-review
    content: latest.ndjson·solver_summary로 wide 샘플 2차 분석
    status: pending
  - id: heuristic-wave2
    content: 진단 결과에 따른 제한적 휴리스틱(선택)
    status: pending
---

# STEP4 `no_route` 탐색 휴리스틱 감사·개선 플랜 (2026-05-12)

## 0. 배경

- **관측:** `step4_no_route_exhausted_breakdown`에서 `dominant_blocker_category == wide_search_exhausted`.
- **의미(코드 정본):** `step4_route_failure_diagnostic._row_breaker_category_no_route_exhausted` 기준, `no_route_exhausted`이면서 **stub 이웃이 hard ring / 순수 geometry 막힘 / trunk-only union(trunk_unreachable)이 아니고**, `expanded_nodes >= 20`인 행이 **wide**로 분류된다.
- **가설:** (1) `goal_cells` union이 커서 유효 목표까지 **비용 지형상 먼** 경로를 넓게 탐색하거나, (2) **단일 스칼라 비용** Dijkstra가 `cheap_reuse`·지형 비용 때문에 **프런티어가 비목표 방향으로 팽창**하거나, (3) 실질적 목표는 가깝지만 **heap 타이브레이크·이웃 순서**로 늦게 닿는 경우 등.
- **목표:** 위 가설을 **진단으로 분리**한 뒤, **전역 `_MAX_STEP4_DIJKSTRA_POPS`(250_000)를 무분별 상향하지 않는** 선에서 순서·목표 집합만 조정할지 결정한다.

---

## 1. 현재 구현 정본 (감사 대상)

### 1.1 탐색 코어

| 항목 | 정본 위치 | 현재 동작 요약 |
|------|-----------|----------------|
| 알고리즘 | `django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_dijkstra.py` `dijkstra_route_step4` | **양의 스칼라 비용** Dijkstra. 힙 키는 **`(누적 거리 float, 셀 Coord)`** 한 쌍뿐 — **별도 lex tie 전용 튜플 없음**. |
| 목표 집합 | 인자 `goal_cells: frozenset[Coord] \| None` | `None`이면 `step4_is_routing_goal`만 사용. STEP4 merge 경로에서는 **`goal_cells`가 설정됨** → 종료 조건: `u != stub_cell` 이고 `(u in goal_cells 또는 legacy_goal)`. |
| **명시적 goal 순서** | 없음 | `frozenset`이므로 **목표 간 우선순위 리스트가 없다**. “첫 목표”는 **가장 먼저 pop되어 goal 조건을 만족한 셀**이다. |
| **프런티어 순서** | `heapq` 최소 힙 | 거리 `d` 최소 우선; **동거리 시 두 번째 키 `Coord`** 비교(튜플 `(x,y)` 등 정의에 따름). `neighbors4` 순서는 `step4_dijkstra` 고정. |
| **경로 비용** | `step4_routing_permission.step4_step_cost` | 스칼라: 동종 transport·`cheap_reuse` 시 trunk reuse 할인, mineable/asteroid/external 등 **계단식 상수**. **lex route cost tuple은 STEP4 Dijkstra에 없음**(Pass3 lex 라우터와 혼동 금지). |
| 방문/예산 통계 | 동 파일, `search_stats` | 종료 시 `expanded_nodes` = **`len(visited)`**(pop 후 방문 처리된 정점 수), `heap_pops`, `stop_reason` ∈ `success` \| `exhausted` \| `budget`, `search_time_ms`. **`max_frontier_size`·goal 거리 히스토그램은 미기록.** |
| 전역 pop 상한 | `_MAX_STEP4_DIJKSTRA_POPS = 250_000` | 초과 시 `stop_reason="budget"`, 경로 없음. |

### 1.2 goal_cells 구성 (merge 측)

| 항목 | 정본 | 요약 |
|------|------|------|
| goal union | `step4_merge_routing.run_step4_merge_aware_routing` | `raw_goal = build_step4_goal_set(tk, committed_trunk_by_kind, margin_cells, trunk_seed_by_kind)` 후 `goal_cells = frozenset(raw_goal \| trunk_cells)`. `trunk_cells`는 **당시** `transport_cells_reaching_external(same_kind_transport, blocked, is_external)`. |
| 동종 trunk 우선(간접) | `step4_step_cost` + `cheap_reuse_cells` | merge에서 주입하는 `cheap_reuse_cells`로 **reuse 비용 할인**; “목표를 trunk부터 정렬”하는 코드는 **없음**. |

### 1.3 `route_length_ratio_exceeded`

- 진단기는 `search_stats.get("route_length_ratio_exceeded")`를 읽지만, **`step4_dijkstra` 본문에서는 해당 키를 설정하지 않는다**(레포 내 grep 기준). wide 감사와는 별도로 **계약 정리·설정 위치**가 필요할 수 있음(이번 플랜의 2차).

---

## 2. 추가 진단 필드 (하위 호환, `search_stats` 및 선택적 failure 샘플)

아래는 **기존 키 이름 변경 없이** 추가하는 것을 전제로 한다.

| 키 | 타입 | 정의·채움 시점 |
|----|------|----------------|
| `nearest_goal_distance_estimate` | `float \| null` | 탐색 **시작 전**: `stub_cell` 기준 `goal_cells` 각 점에 대한 **맨해튼 거리 최소값**, 또는 `cheap_reuse`·trunk만 따로 최소값. (휴리스틱이 아닌 **기하 추정**으로 문서화.) |
| `first_goal_candidate` | `[int,int] \| null` | 위 최소 거리를 달성하는 goal 중 **결정적 타이브레이크** `(dy, dx, y, x)` 최소 한 점. |
| `goal_count_by_distance_bucket` | `dict[str, int]` | 예: 맨해튼 구간 `0-4`, `5-8`, … 또는 `<=baseline_route_length` 대비 비율 버킷. |
| `frontier_stop_reason` | `str` | `search_stats.stop_reason`과 동일 의미를 유지하되, **세분**이 필요하면 `exhausted_empty_heap` vs `exhausted_all_blocked` 등 **추가 enum은 별 키**로 (`frontier_stop_detail`). 초기에는 **`stop_reason` 복제 + 상세 1키**로 최소화. |
| `max_frontier_size` | `int` | 루프 매 이터레이션 `len(heap)` 최대값(또는 push 직후). |

**선택(부하 주의):** 첫 N회 pop 시점의 `(d, u, heap_len)` 샘플을 `step4_wide_search_frontier_samples`에 최대 K개만(NDJSON 크기 제한).

**수집 위치 제안:**

1. **`dijkstra_route_step4`:** `max_frontier_size`, pop 루프 내부 샘플, 종료 시 `nearest_goal_distance_estimate` 등 **순수 기하**는 stub·goal만으로 **탐색 전** 계산 가능 → 여기서 `search_stats` 채움.
2. **`step4_merge_routing`:** `search_mode`, `goal_cells` 크기, `len(trunk_cells)` 등은 이미 인접; wide 전용으로 **`step4_wide_search_context`** 한 dict를 failure 행에 붙일지 결정.

---

## 3. 가능한 “좁은” 변경 후보 (2단계: 진단 이후)

| 후보 | 요지 | 리스크 |
|------|------|--------|
| **Nearest same-kind trunk goal first** | 첫 패스에서 `goal_cells`를 **근접 trunk 부분집합**만으로 제한한 Dijkstra(실패 시에만 기존 union 재시도). `plan_step4_local_bridge_recovery`와 중복 가능 → **역할 분리**: bridge=롤백 직전 복구, 여기서는 **주 탐색 1차 패스**로 둘지 통합 설계 필요. |
| **Exterior goal fallback** | `exterior_goal_count > 0`인 wide에서 margin goal만 2차 패스. trunk-only wide와 분리. |
| **Bounded A\*** | 허용 가능 휴리스틱이면 `f = g + h`; 비용이 계단식이라 **부적합 허리스틱은 최단 경로 깨짐** → `h≡0`(현상 유지) 또는 **독립된 상한 보조 탐색**으로 제한. |
| **Path length cap 조정** | `MAX_ROUTE_LENGTH_RATIO`·`baseline_route_length`는 **분류/진단**에 강하게 연결됨(`foundation.constants`). **의미 변경은 보호 구역과 동급 주의**; “조정” 전 **replay·finalize 불변식** 회귀 필수. |

**원칙:** 위 변경은 **진단으로 wide 원인이 “goal 과다” vs “프런티어 팽창” vs “타이브레이크”로 나뉜 뒤**에만 착수.

---

## 4. 명시적 비목표

- **`_MAX_STEP4_DIJKSTRA_POPS` 무분별 상향** (로그 없이 완화 금지).
- **`hard_protected` / soft corridor 의미·집합** 변경.
- **Pass3 / P4 / Reclaim** 동작·계약 변경.
- **기존 `search_stats` 필드 이름·의미 변경** (`expanded_nodes`, `stop_reason` 등).

---

## 5. 권장 로드맵: **1단계 진단만 → 2단계 안전 휴리스틱**

| 단계 | 내용 | 산출 |
|------|------|------|
| **1단계 (권장 즉시)** | §2 필드를 wide 샘플·`no_route_exhausted` failure 행에 넣고, `latest.ndjson` / `solver_summary`에서 **히스토그램·상관** 확인 | wide가 **진짜 “목표 멀리”**인지, **heap이 비정상적으로 깊은지**, **goal 수와 expanded_nodes** 관계인지 확정 |
| **2단계 (조건부)** | 데이터가 “union 과다”면 **근접 goal 서브패스** 또는 merge 측 **단계적 goal_cells**; “동거리 팽창”이면 **결정적 tie-break 키 확장** `(d, tie_key, coord)` | 변경은 **한 축씩**, 단위 테스트·회귀 고정 |

**결론:** 본 이슈에는 **진단 전용 1단계를 먼저** 권장한다. wide가 **실제로 topology 한계**이면 휴리스틱만으로는 한계가 있고, **계측으로 한계 vs 예산 vs goal 설계**를 가른 뒤 2단계를 택한다.

---

## 6. 구현 시 수정 파일 (코딩 태스크 체크리스트)

| 파일 | 작업 |
|------|------|
| `step4/step4_dijkstra.py` | `max_frontier_size` 추적; goal 거리 사전 계산·버킷; 선택 샘플; `search_stats` 확장 |
| `step4/step4_merge_routing.py` | 필요 시 wide 컨텍스트를 failure dict에 전달; (2단계) goal 서브패스 루프 |
| `step4/step4_route_failure_diagnostic.py` | `build_step4_route_failure_diagnostic`에 `search_stats` 신규 키 전달·replay 호환 |
| `solver_pipeline/finalize.py` | `solver_summary` 미러 누락 시 `setdefault`만 |
| `tests/unit/shapez_asteroid/test_step4_merge_routing.py` 등 | 진단 키 존재·타입, 동작 동일(비용 경로 불변) 회귀 |

---

## 7. 검증 (구현 후)

```text
python -m pytest tests/unit/shapez_asteroid/test_step4_merge_routing.py
python -m pytest tests/unit/shapez_asteroid/test_step4_route_failure_diagnostics.py
ruff check .
mypy <변경 파일>
black --check .
```

---

## 8. 문서·정본 참고

- STEP4 라우팅 개념: `documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md` (존재 시).
- 로컬 bridge 복구(롤백 직전): `documents/plans/plan_step4_local_bridge_recovery_2026-05-12.md` — **주 탐색 휴리스틱**과 책임 중복을 피할 것.

본 문서는 **플랜 전용**이며, 사용자 승인 후 구현 단계로 넘긴다.
