# 13 — STEP 9: Final validation (§15)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 08–12

---

## 15. Final Validation

최종 결과를 반환하기 전 반드시 검증해야 할 항목이다.

Final validation은 문제를 처음 해결하는 단계가 아니라, 앞 단계가 만든 결과를 확인하는 **assertion gate**다.

---

### 15.1 Geometry validation

```text
[ ] extractor와 extension이 겹치지 않는다.
[ ] extractor/extension 위에 belt/pipe가 없다.
[ ] belt/pipe 위에 extractor/extension이 없다.
[ ] output stub는 모든 extractor에 존재한다.
[ ] fixed output stub가 Pass3에서 제거되지 않았다.
[ ] QUARANTINED_UNROUTED placement가 남아 있지 않다.
```

---

### 15.2 Connectivity validation

```text
[ ] 모든 extractor output이 외부 route에 연결되어 있다(각 output **stub 1개**에서 나온 경로가 외부 trunk에 merge되는지, [`01_project_overview.md`](./01_project_overview.md) §3.5와 일치).
[ ] transport graph가 하나의 connected component로 이어져 있다.
[ ] 모든 transport cell이 “외부 trunk 도달 가능” 영역에 속한다:
      ∀ transport cell c, ∃ path c → … → 어떤 external_margin 도달 셀 e (동일 TransportKind subgraph).
      (단순히 extractor별 외부 연결만 보는 것과 별개로, orphan belt/pipe 덩어리를 금지한다.)
[ ] external margin까지 도달하는 trunk가 존재한다.
```

**구현 참고**: 위 항목은 단일 undirected component 검사와 동일하지 않을 수 있다. extractor output에서 outward BFS와 전역 transport adjacency 검사를 함께 쓰거나, “임의 external trunk 셀 집합에서 도달 가능한 transport 전체 = 배치된 transport 전체”로 명시 검사한다.

---

### 15.3 Capacity validation

[`01_project_overview.md`](./01_project_overview.md) §3.6: **1차(우선)** 구현에서는 **max capacity(rated)와의 비교를 하지 않고**, 아래 항목은 **선택·후속**으로 둔다. `trunk_load` **합산 총량**은 §15.2 연결성과 별도로 trace에 남긴다.

```text
[ ] (후속) trunk capacity가 extractor output 총량(rated)을 넘지 않는다.
[ ] (후속) shape belt lane별 초과가 없다.
[ ] (후속) fluid pipe 구간별 초과가 없다.
[ ] (후속) overflow가 발견되면 validation failure이며, bounded recovery로만 되돌아간다.
```

중요:

```text
capacity overflow 해결책인 routing split / additional trunk 생성은 STEP 4에서 수행한다.
Final validation에서는 새 route를 만들지 않는다.
Final validation recovery는 MAX_VALIDATION_RECOVERY_ATTEMPTS를 초과할 수 없다.
```

---

### 15.4 Optimization validation

아래는 **품질·최적화 목표**다. §15.1–15.3 hard invariant와 구분한다.

**`baseline BFS/A*` (정본)**: 아래 조건으로 **한 번** 라우팅한 counterfactual 레이아웃의 `asteroid_internal_transport_count`를 `optimization_baseline_internal_transport`로 저장한다.

**기본 측정 시점(정본, v5.3)**: **Pass1·Pass2 placement 확정 직후, STEP 4 merge-aware routing 이전**의 occupied/blocked 맵을 입력으로 쓴다. 구현체 간 수치 비교 가능성을 위해 **이 시점을 기본값으로 고정**한다. 연구·A/B용으로 STEP 4 직후 맵을 쓰는 변형이 필요하면 **별도 필드**(예: `optimization_baseline_phase: pre_step4 | post_step4`)와 별도 수치를 trace에 **추가**하고, 본 문서 §15.4 첫 항목 checklist는 **pre_step4**만을 말한다.

```text
- 입력 레이아웃: 위 기본 시점의 동일 occupied/blocked 맵.
- goal set: STEP 4 첫 extractor와 **동일 규칙**의 exterior margin ∪ trunk_seed(§9.2)만 사용한다. merge·capacity는 적용하지 않는다.
- 라우팅: RouteZone penalty·lexicographic tuple **없이**, geometry blocked만 적용한 **단순 BFS**(또는 동일 비용의 uniform-cost)로 각 stub→goal set 최단에 가까운 feasible route를 구성.
- 집계: §12.2·§12.5와 **동일한** “소행성 내부 transport 셀” 정의로 내부 칸 수를 센다.
```

최종 solver 결과의 내부 transport가 이 baseline보다 **감소**했는지를 §15.4 첫 항목으로 본다(미달이면 optimization warning, §15.4 하단).

```text
[ ] optimization_baseline_internal_transport 대비 asteroid_internal_transport_count가 감소한다.
[ ] placement_candidate 위 transport 점유가 감소한다.
[ ] route length 증가율이 단계별 허용 범위 안에 있다.
[ ] Reclaim loop 이후에도 net_internal_transport_saved_after_reclaim > 0 이다.
[ ] Reclaim loop가 Pass3 절약분의 허용 budget 이상을 되먹지 않는다.
[ ] Pass3 이후 reclaim placement loop가 실행되었거나 불필요 사유가 trace에 기록된다.
```

**실패 시 종료 등급**: 위 항목만 불충족이고 §15.1–15.3이 모두 통과하면 **SOLVER_FAILURE가 아니다**.
기본 권장: **SUCCESS** 또는 **PARTIAL_SUCCESS**(내부 transport 목표 미달 시) + `optimization_warnings` trace.
bounded recovery(`validation_recovery`)로 묶지 않는다. recovery는 hard invariant 실패(§15.1–15.3)에만 연결한다.

Recovery routing(§11)은 길이 비율 완화로 내부 transport를 다시 늘릴 수 있다. optimization 목표와 별개로 trace에 `recovery_internal_transport_delta`(recovery 직전·직후 내부 transport 칸 수 차이)를 남긴다(§16.3).

---

### 15.5 Existing layout analysis vs final validation (필드 분리)

**시점이 다르다.**

```text
- ExistingLayoutAnalysis의 connected-component·연결 요약은 decode 직후 **원본 blueprint / STEP 0.5** 기준이다.
- Final validation의 connectivity 검사는 solver가 만든 **최종 레이아웃** 기준이다.
```

**같은 필드명으로 보고서를 섞지 않는다.** 예:

```text
existing_layout_transport_component_count
existing_layout_orphan_transport_cell_count   # 또는 issue·component별 세부

final_transport_connected                    # 최종 레이아웃 assertion
final_orphan_transport_count
final_external_reachable_transport_count     # (구현체가 쓰는 명칭과 동기)
```

**공통 기하 함수**는 허용한다.

```python
compute_transport_components(cells, transport_kind)
```

단, **`ExistingLayoutAnalysis` 산출물과 `FinalValidationReport`는 별도 타입·별도 trace 키**로 유지한다. ([`03_data_schema_dto.md`](./03_data_schema_dto.md) §E.12)

---
