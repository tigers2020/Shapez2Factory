---
name: STEP4 bounded local bridge recovery
overview: >
  Pass2 provisional + STEP4 주 Dijkstra 실패 후, 기존 pass2_recovery(회전·goal ablation)까지
  소진된 경우에 한해, 동종 transport로 목표를 축소한 제한 탐색(local bridge)을 최대 1회 시도한다.
  Pass3/P4/Reclaim·전역 비용 튜닝·finalize 불변식은 건드리지 않는다.
todos:
  - id: trigger-api
    content: 진입 조건·breaker OR·no_route_exhausted 판별 헬퍼 확정
    status: pending
  - id: bridge-module
    content: step4_local_bridge_recovery 모듈 + Dijkstra goal subset·pop cap
    status: pending
  - id: merge-insert
    content: step4_merge_routing 병합·trace·failure dict 확장
    status: pending
  - id: finalize-trace
    content: finalize trunk_load 복사 경로에 신규 키 전달 확인
    status: pending
  - id: tests
    content: 회귀 4 fixture + 기존 STEP4 테스트
    status: pending
---

# STEP4 bounded local bridge recovery — 구현 계획 (2026-05-12)

## 0. 배경·목표

- **문제:** `failure_reason == no_route_exhausted` 이고 breakdown 상 `trunk_union_goals_unreachable_from_stub` / `stub_local_geometry_or_corridor` / `narrow_search_exhausted` 인 경우, **full `goal_cells` union**에 대한 주 탐색이 막히거나 조기 소진되어도, **근접 trunk·외곽 goal 소집합**으로는 연결될 여지가 있다.
- **목표:** 롤백·격리 직전, **동일 placement에 대해 local bridge 탐색을 정확히 1세션**(내부 Dijkstra 호출·pop 예산은 설계값으로 상한)만 추가한다.
- **비목표:** Pass3/P4/Reclaim 변경, `dijkstra_route_step4` 전역 비용·`_MAX_STEP4_DIJKSTRA_POPS` 기본값 변경, finalize 검증 완화, 기존 trace 키/DTO 필드 이름 변경.

---

## 1. 현재 롤백·격리가 나는 정확한 위치

**파일:** `django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_merge_routing.py`  
**함수:** `run_step4_merge_aware_routing`

| 단계 | 대략 라인 | 내용 |
|------|-----------|------|
| 주 경로 | 266–288 | `build_step4_goal_set` + `goal_cells`, `dijkstra_route_step4` (`_dijkstra_route`) |
| 실패 상세 | 291–310 | `path is None` → `build_step4_route_failure_detail` → `detail` |
| 기존 Pass2 복구 | 318–368 | `rec0.placement_pass == "pass2"` 및 `PROVISIONAL_PLACED` 이면 `try_step4_failed_pass2_route_recovery` (`step4_failed_pass2_route_recovery.py`) |
| **롤백·격리** | **373–418** | `if not recovered:` → `_rollback_placement_cells` → `QUARANTINED_UNROUTED` → `failures.append` + `step4_route_failure_diagnostic` |
| 성공 시 페인트 | 459–508 | `apply_pass2_recovery_path_paint` 등 |

**정리:** Pass2 provisional에 대한 “최종 실패” 분기는 **`if not recovered:` (373행 근처)** 이다. 이 블록에 들어가기 **직전**이 local bridge의 **가장 작고 안전한 삽입점**이다.

---

## 2. 최소 삽입점 (코딩 태스크 기준)

### 2.1 권장 구조

1. **`step4_merge_routing.py` (동일 루프, 318–372 블록 내부)**  
   - `try_step4_failed_pass2_route_recovery`가 `(None, eval_count)`를 반환한 뒤,  
   - **`if not recovered:`에 진입하기 전**에 다음을 호출한다.  
   - 의사코드: `bridge_out = try_step4_local_bridge_recovery(...)` → 성공 시 `path`, `stub_cell`, `recovered`, `recovery_out` 유사 객체 설정, `search_stats` 갱신.

2. **신규 모듈 (권장):**  
   `django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_local_bridge_recovery.py`  
   - 기존 `step4_failed_pass2_route_recovery.py`와 대칭: **맵 스냅샷/복원**, **동일 `dijkstra_fn` 주입**, **성공 시에만** `cells` 유지.  
   - 이유: `step4_merge_routing`은 이미 장문이며, 복구 정책·단위 테스트를 모듈로 분리하는 편이 회귀 추적에 유리하다.

### 2.2 대안 (비권장)

- `try_step4_failed_pass2_route_recovery` **내부**에 variant로 넣기: 이미 `_MAX_RECOVERY_VARIANT_EVALS = 16` 예산과 회전·goal subset이 있어 **책임 혼합**되기 쉽다. 계획상 **2단계(기존 복구 → bridge)** 로 명확히 나눈다.

---

## 3. 트리거 조건 (모두 만족 시 1회 시도)

다음은 **구현 시** `detail` / `search_stats` / `rec0` / 주 탐색과 동일 입력으로 판별한다.

| # | 조건 |
|---|------|
| 1 | `rec0.placement_pass == "pass2"` |
| 2 | `rec0.state == PlacementCommitState.PROVISIONAL_PLACED` |
| 3 | `tk`(`transport_kind`)가 `want_role = _want_role(tk)` 로 알려진 종류(기존 STEP4와 동일) |
| 4 | 주 탐색 실패 후 `build_step4_route_failure_diagnostic`에 넣을 수 있는 입력으로 **`failure_reason == no_route_exhausted`** (이미 `classify_step4_route_failure_reason` 규약과 동일) |
| 5 | `step4_route_failure_diagnostic.py`의 **`_row_breaker_category_no_route_exhausted(diag, detail)`** 결과가 다음 **하나라도** 일치: `trunk_union_goals_unreachable_from_stub`, `stub_local_geometry_or_corridor`, `narrow_search_exhausted`  
   - 구현 편의: `_row_breaker_category_*`는 현재 비공개이므로, **공개 thin 래퍼** `breaker_category_for_no_route_exhausted(diag, detail) -> str` 를 같은 파일에 추가하거나, bridge 모듈에서 동일 로직을 **한 번만** 복제하지 않도록 export 함수 1개로 고정한다. |
| 6 | 기존 `try_step4_failed_pass2_route_recovery`가 **이미 실패**(`None`) — 즉 “그렇지 않으면 롤백될” 상태 |
| 7 | **동일 `placement_id`당 런당 bridge 시도 1회** (이 루프에서만 호출되면 자동 만족; 재진입 방지 플래그는 `work_records` 또는 지역 `set`으로 명시) |

**제외(명시적 비트리거):** `search_budget_exhausted`(stop_reason `budget`), `hard_protected_ring`, `wide_search_exhausted`만 있는 케이스 등은 **플랜 1차에서 제외**하고, 필요 시 Series 3 후속에서 데이터로 재평가한다. (요구사항 3분류에 맞춤.)

---

## 4. 하드 제약

| 제약 | 구현 근거 |
|------|-----------|
| 동종 transport만 | `want_role` 고정, `dijkstra_route_step4(..., want_role=want_role)`, `step4_step_cost` 재사용 |
| `hard_protected` 관통 금지 | 기존과 동일: `blocked = frozenset(_blocked_cells(cells) | hard_extras)` 에서 stub만 `discard` |
| extractor/extension 발 밟기 금지 | `_blocked_cells`가 miner/extension 점유를 이미 포함 (`routing_cells.blocked_cells`) |
| wrong-kind transport 금지 | STEP4 비용·goal 판정이 `want_role`에 묶여 있음; 페인트는 `apply_pass2_recovery_path_paint`와 동일 패턴 |
| **placement당 bridge 최대 1세션** | merge 루프에서 `try_step4_local_bridge_recovery` 최대 1회; 내부에서 Dijkstra는 goal subset 분할 시에도 **총 heap pop 상한** 공유 |
| 결정적 타이브레이크 | 기존 pass2_recovery와 동일하게 **경로 키 `(신규 내부 transport 수, 총비용, len(path), lex path)`** 정렬; goal 후보 정렬은 **(맨해튼 거리, y, x, goal 좌표)** 등 고정 키 |

---

## 5. 복구 탐색 설계

### 5.1 소스

- **시작 셀:** 주 탐색 실패 시점의 **`stub_cell`** (기존 recovery가 `None`을 반환할 때 `_restore_cells`로 원상이므로 **원 stub**과 일치).
- 회전 복구가 성공한 경로는 이 분기에 오지 않음.

### 5.2 목표 집합 (union 축소)

- 이미 계산된 `trunk_cells`, `goal_cells`, `margin_cells`를 사용.
- **Bridge 전용 goal 후보:**  
  - `G_trunk = trunk_cells` 중 `stub_cell`으로부터 **그래프 거리 또는 맨해튼** 기준으로 정렬해 상위 `K_trunk` (예: 8~16, 구현 상수로 고정).  
  - `G_ext = (goal_cells & margin_cells)` 가 비어 있지 않으면 동일 방식으로 상위 `K_ext` (예: 4).  
  - `G_bridge = frozenset(G_trunk | G_ext)` 가 비면 시도 **스킵**(거절 카운트 + 사유 `no_bridge_goals`).
- 주 탐색과의 차이: **`goal_cells` 전체 union이 아니라 `G_bridge`** 만 `dijkstra_route_step4(..., goal_cells=G_bridge, trunk=trunk_cells)` 에 넘긴다 (기존 API 그대로).

### 5.3 상한

- **Heap pop 상한:** `step4_dijkstra.py`의 `dijkstra_route_step4`에 **옵션 인자** `max_heap_pops: int | None = None` 추가. 미지정 시 기존 `_MAX_STEP4_DIJKSTRA_POPS` (전역 동작 불변). bridge만 예: `8000` 또는 `min(8000, 200 * len(G_bridge))` 처럼 **상수·간단 식**으로 고정.  
- **최대 경로 길이:** `MAX_ROUTE_LENGTH_RATIO`·`nearest_hops` 기반 기존 규약이 `step4_step_cost` / goal에 이미 있다면 중복 금지; 추가로 **물리 길이 상한**이 필요하면 `detail`의 `nearest_existing_transport_distance`에 **고정 가산 마진**(예: +6)만 허용하는 쪽이 “전역 튜닝”이 아니다.

### 5.4 성공 시

- `path`가 `stub`에서 `G_bridge` 내 한 goal까지 이어지면, **기존과 동일하게** `apply_pass2_recovery_path_paint` + 이후 `routes_out` / `ROUTED_CONFIRMED` 갱신 분기(459행 이하)로 **합류**.  
- `search_stats["search_mode"]` 예: `"local_bridge:subset_goals"`.

### 5.5 실패 시

- `cells`를 bridge 진입 전 스냅샷으로 복원 후 `None` 반환 → **기존 롤백·격지 분기와 동일** (373행 이하 변경 없음).

---

## 6. Trace 키 (하위 호환 추가)

`step4_merge_routing.py`의 `trace_tl` (`step4_trunk_load`에 병합)에 다음 **신규** 키를 추가한다. 기존 `step4_failed_route_recovery_*`는 유지.

| 키 | 타입 | 의미 |
|----|------|------|
| `step4_local_bridge_recovery_attempted_count` | int | 트리거를 통과해 bridge 함수에 진입한 횟수 |
| `step4_local_bridge_recovery_success_count` | int | bridge로 `ROUTED_CONFIRMED`까지 연결된 횟수 |
| `step4_local_bridge_recovery_rejected_count` | int | 트리거 미통과·goal 비어·pop cap·무경로 등 |
| `step4_local_bridge_recovery_failure_reasons` | `dict[str, int]` | 거절/실패 사유 히스토그램 (예: `not_no_route_exhausted`, `breaker_out_of_scope`, `no_subset_goals`, `budget`, `exhausted`) |
| `step4_local_bridge_recovery_samples` | `list[dict]` (최대 N) | `placement_id`, `breaker_category`, `G_bridge_size`, `stop_reason`, `expanded_nodes` |

**실패 행 페이로드:** `fd["step4_failed_route_recovery"]` 옆에 `fd["step4_local_bridge_recovery"] = {"attempted": bool, "success": bool, "reason": str | None, ...}` 형태로 **추가** (기존 키 덮어쓰기 금지).

**finalize:** `finalize.py`에서 `trunk_load`를 `solver_summary`로 복사하는 기존 경로가 있으면, **신규 키는 trunk_load에만 넣어도** 상위로 전달되는지 확인; 누락 시 `setdefault` 수준의 **미러 추가만** (필드 rename 없음).

---

## 7. 테스트 계획

**디렉터리:** `tests/unit/shapez_asteroid/`

| 케이스 | 파일(신규 권장) | 기대 |
|--------|-----------------|------|
| Recoverable bridge | `test_step4_local_bridge_recovery.py` | 작은 격자에서 full union 실패를 가짜로 유도하거나 goal subset만 열리게 구성 → bridge 성공 후 `ROUTED_CONFIRMED`, 롤백 ID 없음 |
| Hard protected 거절 | 동상 | `hard_extras`가 유일 통로를 막음 → bridge `None`, 롤백·failure 이전과 동일 |
| Wrong-kind | 동상 | 다른 종류 belt/pipe가 막는 셀은 `step4_step_cost`/blocked로 이미 불가; **다 kind extractor 인접** fixture로 “페인트 불가” 검증 |
| Fallback 롤백 불변 | 동상 | bridge 트리거 off 또는 실패 시, **기존** `rolled_back_placement_ids`·`routing_failures` 길이가 bridge 없을 때와 동일 패턴 |

**기존 테스트:** `test_step4_failed_pass2_route_recovery.py`, `test_step4_merge_routing.py`, `test_step4_route_failure_diagnostics.py` 전체 회귀.

---

## 8. 다음 코딩 태스크에서 수정·추가할 파일·심볼 (체크리스트)

| 파일 | 작업 |
|------|------|
| `step4/step4_local_bridge_recovery.py` | **신규** `try_step4_local_bridge_recovery(...) -> Pass2RouteRecoveryOutcome \| None` 유사 타입, 스냅샷/복원, goal subset, pop cap |
| `step4/step4_dijkstra.py` | `dijkstra_route_step4`에 **`max_heap_pops: int \| None`** (기본 `None` = 기존 상수만 사용) |
| `step4/step4_merge_routing.py` | 318–372 사이 bridge 호출; `trace_tl` 카운터·샘플; `fd` 보조 dict |
| `step4/step4_route_failure_diagnostic.py` | `breaker_category_for_no_route_exhausted` 공개 래퍼(또는 기존 함수 re-export) — **rename 없이 추가만** |
| `step4/step4_trunk_load.py` | 필요 시 신규 키를 누락 없이 직렬화하는지 확인 (기본 dict 복사면 생략 가능) |
| `solver_pipeline/finalize.py` | `solver_summary` 미러 누락 시 `setdefault` |
| `tests/unit/shapez_asteroid/test_step4_local_bridge_recovery.py` | **신규** 4 fixture |

---

## 9. 검증 명령 (구현 후)

```text
python -m pytest tests/unit/shapez_asteroid/test_step4_local_bridge_recovery.py
python -m pytest tests/unit/shapez_asteroid/test_step4_merge_routing.py
python -m pytest tests/unit/shapez_asteroid/test_step4_failed_pass2_route_recovery.py
python -m pytest tests/unit/shapez_asteroid/test_step4_route_failure_diagnostics.py
ruff check .
mypy <변경 파일 경로>
black --check .
```

---

## 10. 잔여 리스크

- Goal subset이 **실제 연결 가능한 trunk와 다른 컴포넌트**만 고르면 여전히 실패 → 거절·롤백은 동일; 샘플 trace로 튜닝.
- `narrow_search_exhausted`와 subset bridge의 상호작용: 이미 적은 expanded_nodes면 **pop cap을 더 낮추면** 오히려 성공률 하락 가능 → 상수는 보수적으로 시작.
- P2-C (`step4_p2c_corrective.py`) 이후 끊김은 본 플랜 범위 밖; bridge 성공 경로가 P2-C에서 깨지지 않는지 **통합 테스트 1건** 권장.

---

## 11. Series 3 구현 순서 권고

1. `breaker_category` 공개 헬퍼 + 단위 테스트 (diagnostic만).  
2. `dijkstra_route_step4`의 `max_heap_pops` + 기존 테스트 비회귀.  
3. `step4_local_bridge_recovery.py` + 단독 테스트.  
4. `step4_merge_routing` 연결 + trace + failure dict.  
5. finalize 미러 확인 + 전역 STEP4 pytest 구간.

본 문서는 **구현 전 플랜**이며, 사용자 승인 후 코딩 단계로 넘긴다 (`protocols/README.md` 게이트 준수).
