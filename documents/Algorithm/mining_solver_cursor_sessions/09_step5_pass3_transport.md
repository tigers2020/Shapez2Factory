# 09 — STEP 5: Pass3 · Route cost (§10–§11, P3)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 08

---

## 10. STEP 5 — Pass3: Internal Transport Minimization

### 10.1 Pass3의 정확한 정의

Pass3는 단순 재연결 단계가 아니다.

정확한 목적은 다음이다.

```text
중앙 belt/pipe를 무조건 제거하는 것이 아니라,
줄일 수 있는 내부 transport를 줄이고,
transport line을 외곽 / void / 저가치 cell / 기존 trunk 쪽으로 밀어내는 단계다.
```

---

### 10.2 기존 문제

최단거리 중심 BFS/A*는 다음 문제를 만든다.

```text
- 중앙 spine 생성
- 내부 mineable 후보 공간 점유
- extractor/extension 후보 감소
- pipe/belt 과다 생성
- extractor가 route 위에 올라가는 overlap 문제
- isolated extractor + long route 패턴 증가
```

---

### 10.3 Pass3의 새 목적함수

```text
소행성 내부 transport 사용량 최소화
→ mining opportunity loss 최소화
→ route cost 최소화
→ congestion/load penalty 최소화
→ turn_count 최소화
→ path_length 최소화
```

---

### 10.4 Lexicographic routing priority

```python
priority = (
    asteroid_internal_transport_count,
    mining_opportunity_loss,
    total_route_cost,
    congestion_penalty,
    turn_count,
    path_length,
    cell_row,      # 최종 tie-break: 결정론적 탐색·replay 재현용
    cell_col,
)
```

**동점 해소**: 위 튜플이 전부 동일한 후보가 남으면 마지막에 **`(cell_row, cell_col)` 사전순**으로 한 칸을 고른다(일반적으로 frontier에서 현재 확장 노드 좌표). 구현은 동일 규칙을 고정하고 trace에 사용한 tie-break 키를 남긴다.

이 방식의 장점:

```text
- 내부 transport 최소화를 1순위로 고정할 수 있다.
- cost 숫자 튜닝이 흔들려도 의사결정 우선순위가 유지된다.
- 거리만 짧고 내부 공간을 망치는 route를 막을 수 있다.
- congestion을 turn_count와 분리해 trunk 과밀을 직접 제어할 수 있다.
```

---

### 10.5 A* admissibility 처리 방침

`asteroid_internal_transport_count` 같은 값은 불규칙한 소행성 형태에서 admissible heuristic을 만들기 어렵다. 따라서 최적성 보장이 필요하면 다음 방식을 우선한다.

```text
기본 구현:
lexicographic Dijkstra / uniform-cost search
```

**§3.5와의 관계**: 셀 단위 기본 가중치·void/기설치 transport/extractor·extension 회피·밀집 가산·output 회전 등 **pass 공통 Transport 설계**는 [`01_project_overview.md`](./01_project_overview.md) §3.5가 정본이다. Pass3는 위 목적함수 튜플(§10.4)로 **lexicographic** 확장을 얹어, 단순 스칼라 비용만의 Dijkstra와 혼동하지 않는다.

A*를 사용할 경우:

```text
- heuristic은 보수적 lower bound만 사용한다.
- internal_transport_count, opportunity_loss, congestion_penalty에 대해 안전한 lower bound가 없으면 0을 사용한다.
- path_length에 대해서만 Manhattan lower bound를 사용할 수 있다.
```

goal set이 여러 셀일 때 path_length 항의 Manhattan 휴리스틱은 **목표별 거리의 최소값**이어야 한다.

```text
manhattan_to_goal_set = min_{g in route_goal_set} manhattan(current, g)
```

권장 tuple heuristic:

```python
h = (
    0,
    0,
    0,
    0,
    0,
    manhattan_to_goal_set,
)
```

정확한 global optimal보다 속도가 더 중요하면 weighted A*를 사용할 수 있지만, 그 경우 문서와 trace에 `optimality_guarantee=false`를 남긴다.

A*·weighted 탐색에서 frontier 동점은 §10.4와 동일하게 **좌표 사전순**으로 해소해 결정론을 유지한다.

---

### 10.6 성능 제한 및 fallback

lexicographic Dijkstra는 정확성은 높지만 대형 맵에서 탐색 비용이 커질 수 있다. 웹 UI replay를 목표로 하므로 탐색 예산을 둔다.

```text
MAX_EXPANDED_NODES_PER_ROUTE = 20_000  # 초기 튜닝값
MAX_ROUTE_SEARCH_MS = 150~300ms        # interactive mode 기준
MAX_BATCH_SOLVE_MS = 3~10s             # full solver 기준
```

fallback 순서:

```text
1. lexicographic Dijkstra 시도
2. budget 초과 시 bounded weighted A*로 전환
3. 그래도 실패 시 baseline shortest feasible route 시도
4. baseline도 실패하면 recovery 또는 placement rollback
```

trace에는 다음을 남긴다.

```text
search_mode: lexicographic_dijkstra | weighted_astar | baseline_shortest | failed
expanded_nodes: int
search_time_ms: int
optimality_guarantee: bool
fallback_reason: string | null
```

정확도: 중간. node/time 예산은 튜닝 후보이며 실제 맵 크기 기준으로 조정한다.

---

## 11. Pass3 Route Cost Model

§11.1 **RouteZone 기본 cost** 수치는 [`03_data_schema_dto.md`](./03_data_schema_dto.md) §11.1과 동일(정본).

### 11.1 Route Zone 정의

| Zone                 | 의미                          | 기본 cost |
| -------------------- | --------------------------- | ------: |
| OUTSIDE              | 소행성 bbox 밖                  |       1 |
| BOUNDARY_VOID        | 소행성 외곽 / boundary ring      |       5 |
| INTERNAL_VOID        | 소행성 내부 빈 공간                 |      50 |
| FILLABLE_INTERIOR    | 내부 배치 가능성이 높은 공간            |     150 |
| PLACEMENT_CANDIDATE  | extractor/extension 후보 셀    |     400 |
| PLACEMENT_OCCUPIED   | extractor/extension 점유 셀    |     900 |
| BLOCKED              | extractor으로 경로 관통 불가한 점유 셀 |     INF |

**정본 교차**: STEP1 ``mineable_placement_cells``·``interior_patch_cells``는 소행성 채굴 필드이며 ``INTERNAL_VOID``와 동일시하면 안 된다. 상세는 [`03_data_schema_dto.md`](./03_data_schema_dto.md) §11.1 표 직후 CANON 단락.

---

### 11.2 Transport kind별 cost override

기본 RouteZone cost는 공유하되, transport kind별 보정값을 둘 수 있다.

```python
route_cost = ROUTE_ZONE_COST[zone] * KIND_COST_MULTIPLIER[transport_kind]
```

초기값:

```python
KIND_COST_MULTIPLIER = {
    TransportKind.SHAPE_BELT: 1.0,
    TransportKind.FLUID_PIPE: 1.0,
}
```

초기에는 동일하게 두되, capacity / merge / load 계산은 반드시 kind별로 분리한다.

---

### 11.3 중요한 예외: output stub는 fixed start point

extractor output 앞 1칸은 필수 stub다.

```text
extractor → output stub → route search 시작
```

```text
output stub는 route search의 fixed start point다.
```

처리 규칙:

```text
- output stub는 candidate route가 반드시 포함해야 한다.
- 다른 route가 optional하게 통과하는 일반 cost 0 cell이 아니다.
- route search의 start node는 extractor core가 아니라 output stub다.
- Pass3도 fixed output stub를 제거하거나 우회할 수 없다.
```

구현 형태:

```python
start = fixed_output_stub[cell_for_extractor]
route = find_route(start=start, goals=goal_set, ...)
assert route[0] == start
```

---

### 11.4 baseline_route_length 정의 및 단계별 ratio

`baseline_route_length`는 다음처럼 정의한다.

```text
baseline_route_length = 같은 start stub와 같은 goal set에 대해,
geometry constraint만 적용한 shortest feasible route length
```

기준 route:

```text
- extractor/extension/hard barrier는 blocked
- fixed output stub에서 시작
- RouteZone penalty는 사용하지 않음
- capacity penalty는 사용하지 않음
- 같은 TransportKind goal set 사용
```

단계별 ratio는 동일하게 두지 않는다.

| 단계                                 |                   제한 | 이유                                            |
| ---------------------------------- | -------------------: | --------------------------------------------- |
| STEP 4 initial merge-aware routing | `<= baseline * 1.50` | trunk merge와 capacity split 때문에 약간 긴 route 허용 |
| STEP 5 Pass3 rerouting             | `<= baseline * 1.35` | 내부 transport 최적화 목적이지만 과도한 우회 방지              |
| STEP 6 Reclaim incremental routing | `<= baseline * 1.20` | 추가 extractor 하나 때문에 긴 내부 route가 생기는 것을 강하게 제한 |
| Recovery routing                   | `<= baseline * 2.00` | 연결성 회복이 우선이므로 예외적으로 완화                        |

Recovery routing에서 길이 비율을 완화하더라도 **soft_protected corridor 교체는 §14.3의 atomic replace 규칙을 따른다**(replacement 없이 기존 통로만 버려 orphan trunk를 만들지 않음). recovery 전용 추가 규칙은 §14.3 참고.

**`baseline_route_length` 재계산(정본)**: `baseline_route_length`의 **정의**(§11.4 본문)는 고정이다. Reclaim commit으로 `all_committed_placements`·`final_route_cells`·blocked 집합이 바뀌면, **ratio 검사 직전**마다 해당 stub·goal set에 대해 baseline을 **다시 계산**한다(이전 스냅샷 baseline을 그대로 쓰지 않는다). **Post-reclaim Pass3 rerun(§12.5)**: rerun **직전** 스냅샷의 placements·blocked·goal set으로 baseline을 구한 뒤, rerun 산출 route와 비교한다. `baseline_internal_transport_at_reclaim_entry` 같은 **metric 스냅샷**과 혼동하지 않는다(내부 transport 지표 vs route geometry baseline).

정확도: 중간. ratio는 튜닝 후보이며 QA 결과로 조정한다.

---


---

## 부록: P3 체크리스트 (원문 §20)

### P3 — Pass3 Weighted / Lexicographic Routing 구현

```text
[ ] RouteZone enum 추가
[ ] route_zone_map 생성
[ ] fixed_output_stub를 start point로 처리
[ ] hard/soft protected corridor 처리
[ ] lexicographic Dijkstra 우선 구현
[ ] A* 사용 시 admissible heuristic 제한 명시
[ ] expanded_nodes / search_time_ms budget 추가
[ ] fallback search mode 구현
[ ] baseline_route_length 계산
[ ] 단계별 route length ratio 적용
[ ] asteroid_internal_transport_saved 계산
```
