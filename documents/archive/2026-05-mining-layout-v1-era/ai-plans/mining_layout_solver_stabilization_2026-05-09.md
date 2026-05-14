# Mining Layout Solver 안정화 플랜

**날짜**: 2026-05-09  
**상태**: 승인됨 (정식 반영)  
**브랜치 제안**: `fix/mining-solver-preserve-production`

## 요약

| 항목 | 내용 |
|------|------|
| **목표** | 연결 성공만 보는 solver를 **생산 설비 보존형** solver로 전환한다. |
| **우선순위** | P0 안정화 → P1 route-probe commit → P2 Pass3 transport-only → P3 merge/trunk 검증 |

### 근거·신뢰도 (기획 시점)

| 근거 | 판단 | 신뢰도 |
|------|------|--------|
| 체크리스트 최종 목표 | 성공 기준은 단순 연결이 아니라 **생산 설비 보존 + 외부 연결 + 내부 transport 최소화** | 높음 |
| trace | `after_pass2_scan = 241`, 종료 `234`로 **−7칸**; 권장 허용치 `0~4` 초과 | 높음 |
| destructive recovery | owner drop류는 꺼졌으나 `merge_repair_applied` 등 **철거 기반 repair** 잔존 | 높음 |
| 미완료 | route probe, final extractor/extension count, solver_summary, Pass3 snapshot, trunk validation, 테스트 | 높음 |
| 핵심 파일 | `solver_service.py`, `pass3_transport.py`, `routing.py`, `weighted_routing.py`, `cost_grid.py` | 높음 |

---

## 0. 문제 정의

### 좋아진 점

- premerge bundle 제거류 대부분 off
- owner drop 류 `cap=0` 차단
- `return_ok_true`가 생산 손실 상태에서 바로 나오지는 않음

### 남은 문제

- `merge_repair`가 아직 **철거 기반**으로 동작할 수 있음
- **route 가능한 bundle만 commit**하는 구조가 아님
- final extractor/extension **보존 검증** 없음
- Pass3가 **transport-only**인지 snapshot으로 증명하지 못함
- **solver_summary** 없어 실패 원인 분석이 불완전

### 핵심 방향

**기존**: 배치 많이 → 연결 실패 → merge repair / demolition 땜질  

**수정**: bundle 후보 → **route probe** → 연결 가능한 bundle만 commit → Pass3는 transport만 재구성 → final validation에서 생산 손실 감지

---

## P0 — Final Validation / Summary 먼저 고정

**목표**: 성공/실패 판정 기준을 먼저 고정한다. 이후 개선 여부를 판단 가능하게 한다.

### 수정 대상

- `shapez_asteroid/services/asteroid_mining_layout/solver_service.py`
- `shapez_asteroid/services/asteroid_mining_layout/solver_trace.py`

### 구현 체크리스트

- [ ] `after_pass2_baseline_counts`를 `SolverRunContext`에 저장
- [ ] `final_counts`를 return 직전 항상 계산
- [ ] `solver_summary` 이벤트를 **모든 종료 경로**에서 emit
- [ ] `final_buildings`, `final_extractors`, `final_extensions` 기록
- [ ] `removed_extractors`, `removed_extensions`, `removed_bundles` 기록
- [ ] `destructive_recovery_events` 기록
- [ ] `disconnected_stub_count` 기록
- [ ] `production_score_before_routing` 기록
- [ ] `production_score_final` 기록
- [ ] `layout_degraded` 기록
- [ ] `return_reason` 기록

### 실패·저하 조건 (개념)

```python
if final_buildings < after_pass2_buildings - allowed_demolition_cells:
    return failure_or_degraded

if final_extractors < after_pass2_extractors:
    return failure

if destructive_recovery_events > 0:
    return degraded_or_failure

if connected and production_score_final < production_score_before_routing:
    return degraded_or_failure
```

### 권장 기본값

```python
ALLOWED_DEMOLITION_CELLS = 0
ALLOWED_EXTENSION_LOSS = 0
ALLOW_DEGRADED_SUCCESS = False
```

처음에는 엄격하게; 필요 시에만 완화.

---

## P1 — 철거 기반 merge repair 완전 차단

**목표**: trace 상 `merge_repair_applied`와 `n_buildings` 감소(예: 241→234)의 주원인인 **철거 기반 repair commit**을 막는다.

### 수정 대상

- `solver_service.py`
- `routing.py`
- `weighted_routing.py`

### 즉시 적용 방향

```python
MERGE_REPAIR_ALLOW_DEMOLITION = False
MERGE_REPAIR_MAX_DEMOLITION_CELLS = 0
MERGE_REPAIR_TERMINAL_OVERFLOW_CELL_CAP = 0
```

또는 함수 레벨:

```python
if repair_path.requires_demolition:
    trace("merge_repair_rejected_requires_demolition")
    continue
```

### 차단 이벤트·경로

- [ ] `merge_repair_applied` with `n_expanded_applied > 0` (철거 확장 적용)
- [ ] `merge_demolition_budget_block` 이후 unblock attempt
- [ ] `find_min_demolition_path` 결과를 commit에 사용
- [ ] demolition path가 connected improvement로 인정되는 경로

### 대체 동작

merge path 실패 → `failed_stub`, `owner_bundle_id` 기록 → 해당 bundle을 rollback candidate로 표시 → 주변 bundle/extension/extractor는 **비변경**.

---

## P2 — Bundle Commit 전 Route Probe

**목표**: 중앙 extractor/extension을 만들었다가 나중에 지우는 구조를 끊는다.

**원칙**: route probe 실패 bundle = **처음부터 commit 금지**.

### 수정 대상

- `placement.py`
- `solver_service.py`
- `routing.py`
- `weighted_routing.py`

### Commit 절차

1. bundle 후보 생성  
2. extractor core / extension cells 검증  
3. output stub 생성  
4. 임시 occupied state  
5. output stub → existing trunk/exterior **route probe**  
6. 성공: bundle commit, stub 보호, route corridor reserve  
7. 실패: candidate reject, trace만, **demolition recovery로 넘기지 않음**

### 제안 API

```python
def probe_bundle_route_feasibility(
    candidate_bundle,
    current_buildings,
    current_transport,
    asteroid_cells,
    external_anchor_cells,
    protected_corridors,
) -> RouteProbeResult:
    ...
```

```python
@dataclass
class RouteProbeResult:
    ok: bool
    path: list[Coord]
    failed_stub: Coord | None
    blocked_by: dict[Coord, str]
    path_length: int
    internal_transport_count: int
    would_block_candidate_count: int
    reason: str
```

### Trace 이벤트

- `bundle_route_probe_start`
- `bundle_route_probe_success`
- `bundle_route_probe_reject`
- `bundle_commit`
- `bundle_reject_no_route`

---

## P3 — Protected Corridor

**문제**: stub에서 1칸 탈출 가능해도 이후 다른 bundle이 통로를 막을 수 있음.

**방향**: route probe 성공 시 경로 중 **최소 구간**을 보호.

### 보호 우선순위 (최소 권장)

1. output stub  
2. stub 바로 다음 1~2칸  
3. cut-vertex 성격의 병목 cell  

### 구현 스케치

```python
protected_transport_corridors: set[Coord]
```

placement 후보 검사:

```python
if candidate_building_cell in protected_transport_corridors:
    reject_candidate("would_block_protected_corridor")
```

전체 route를 hard-block으로 보호하면 배치가 과도하게 줄 수 있으므로 **최소 보호**부터.

---

## P4 — Pass3 Transport-Only Contract

**목표**: Pass3가 building을 바꾸지 않음을 코드·trace로 증명.

### 수정 대상

- `pass3_transport.py`
- `solver_service.py`

### 구현 개념

```python
before_buildings = dict(buildings)
before_extractors = set(extractor_facing.keys())
before_extensions = set(extension_parents.keys())

result = reconstruct_mining_priority_transport(...)
```

운영 코드에서는 assert 대신 비교·trace·rollback:

```python
if buildings_changed:
    trace("pass3_contract_violation_buildings_changed")
    rollback()
    return Pass3Result(committed=False, reason="building_mutation_forbidden")
```

### Trace

- `pass3_contract_snapshot`
- `pass3_contract_ok`
- `pass3_contract_violation_buildings_changed`

### 성공 조건

- Pass3 전/후 `buildings` 동일  
- `extractor_facing` 동일  
- `extension_parent` 동일  
- `transport_cells`만 변경 가능  

---

## P5 — Pass3 Score 확장

체크리스트 기준 보강 필드 예:

- baseline / weighted route length  
- `placement_candidate_blocked_count`  
- `opportunity_loss`  
- `turn_count`  

### 수정 대상

- `pass3_transport.py`
- `weighted_routing.py`
- `cost_grid.py`

### 제안 `RouteScore`

```python
@dataclass
class RouteScore:
    internal_transport_count: int
    opportunity_loss: int
    placement_candidate_blocked_count: int
    total_route_cost: int
    turn_count: int
    path_length: int
```

### Commit 조건 예

```python
if weighted_score.internal_transport_count > baseline_score.internal_transport_count:
    reject("internal_transport_not_improved")

if weighted_path_length > baseline_path_length * 1.35:
    reject("route_length_ratio_exceeded")

if opportunity_loss > baseline_opportunity_loss:
    reject("opportunity_loss_increased")
```

### 우선순위

1. `internal_transport_count`  
2. `opportunity_loss`  
3. `placement_candidate_blocked_count`  
4. route_cost  
5. `turn_count`  
6. `path_length`  

---

## P6 — Merge / Trunk Validation

**목표**: merge 성공 후에도 transport graph가 올바른지 검증.

### 수정 대상

- `routing.py`
- `solver_service.py`

### 구현 항목

- [ ] 모든 extractor output stub 수집  
- [ ] transport graph component 계산  
- [ ] 각 stub가 transport graph에 포함되는지  
- [ ] 각 stub component가 external margin까지 연결되는지  
- [ ] isolated transport component 탐지  
- [ ] stub-only dead end 탐지  
- [ ] trunk capacity 계산  

### 제안 API

```python
def validate_transport_graph(
    transport_cells,
    output_stubs,
    external_cells,
) -> TransportGraphValidation:
    ...
```

```python
@dataclass
class TransportGraphValidation:
    all_outputs_connected: bool
    connected_to_external: bool
    disconnected_stubs: list[Coord]
    isolated_components: list[set[Coord]]
    stub_dead_ends: list[Coord]
    component_count: int
```

---

## P7 — 테스트 케이스

### 제안 파일

- `tests/unit/shapez_asteroid/test_mining_solver_validation.py`
- `tests/unit/shapez_asteroid/test_mining_solver_route_probe.py`
- `tests/unit/shapez_asteroid/test_pass3_transport_contract.py`
- `tests/unit/shapez_asteroid/test_transport_graph_validation.py`

### Case 요약

| Case | 내용 |
|------|------|
| A | 동일 입력 재현: after_pass2 vs final, `destructive_recovery_count == 0`, building loss 시 `return_ok` 금지 |
| B | 중앙 extractor: probe 성공 → commit → Pass3 후 유지, `removed_extractors == 0` |
| C | 연결 불가 bundle: probe 실패 → reject, 주변/owner 삭제 없음 |
| D | Pass3 transport-only: 전후 buildings 동일, transport만 변경 |
| E | merge repair demolition 차단: `find_min_demolition_path` found여도 commit 금지, trace, buildings 감소 없음 |

---

## 작업 순서·완료 기준

### 1차 — 안전장치

1. solver_summary 추가  
2. final validation 추가  
3. merge_repair demolition commit 차단  
4. destructive event 카운터 추가  

**완료 기준**: 241→234 유사 감소 시 성공 처리 불가; demolition 동반 `merge_repair_applied` 없음; 모든 종료 경로 `solver_summary`.

### 2차 — commit 구조

1. route probe 함수  
2. placement commit 전 probe  
3. 실패 reject  
4. protected corridor 최소 구현  

**완료 기준**: probe 실패 bundle 미commit; 나중 bundle 삭제 복구 없음; route 가능 시 중앙 extractor 보존.

### 3차 — Pass3

1. building snapshot  
2. transport-only contract  
3. score 확장  
4. weighted route commit 조건 강화  

**완료 기준**: Pass3 전후 building set 동일; internal transport 악화 시 미commit; route length 비율 제한(예: 1.35).

### 4차 — Graph validation

1. output stub graph validation  
2. external 연결  
3. isolated / dead end  
4. final validation 연동  

**완료 기준**: 모든 output stub가 external graph에 연결; isolated component 시 실패; `connected` 의미 명확.

---

## 커밋 분리 제안

1. solver summary + final production validation  
2. demolition-based merge repair commit 비활성  
3. route probe before bundle commit  
4. protected transport corridors  
5. Pass3 transport-only contract  
6. transport graph validation  
7. destructive recovery 회귀 테스트  

---

## 최종 목표 상태

- solver가 **연결을 위해 생산 설비를 삭제**하지 않음.  
- 연결 불가 bundle은 **삭제가 아니라 처음부터 reject**.  
- Pass3는 **extractor/extension 비변경**, transport만 재구성.  
- 최종 성공: `connected` + extractor/extension 보존 + destructive recovery 0 + production_score 보존 + external graph 연결.

---

## 결론

다음 수정은 route 최적화보다 먼저 **성공 판정과 삭제 방지**를 고정한다.

1. **1순위**: solver_summary + final validation + merge demolition 차단  
2. **2순위**: route probe before commit  
3. **3순위**: Pass3 transport-only contract  
4. **4순위**: transport graph validation + regression tests  

## 관련 문서

- [`../current_plan.md`](../current_plan.md) — 진행 중 목표·게이트  
- [`../../research/research_shapez2_game_systems_2026-05-01.md`](../../research/research_shapez2_game_systems_2026-05-01.md) — 게임 규칙 참고
