# ACTIVE: Protected corridor lifecycle alignment (PR4)

**상태:** ACTIVE (구현 진행 중)  
**Epic:** C — [`documents/refactory/corridor-state-machine-refactor.md`](../refactory/corridor-state-machine-refactor.md)  
**범위:** Algorithm §14 / Epic C — **candidate / soft / hard 생명주기·가드만.** 라우팅 가중치·Placement FSM·recovery 복귀 경로·replay UI 재설계 제외.

**사람 승인:** 프로젝트 게이트상 의미 있는 계약 변경은 승인 후 본문에 날짜·승인자를 기록한다.

**구현 반영(2026-05-12, 1차):** `step4_routing_state.py` — STEP4 committed-route `routing_state`에서 `soft_protected_candidate_corridors`를 빈 리스트로 직렬화. 단위 테스트: `test_protected_corridor_step4_snapshot.py`, `test_step4_merge_routing.py` 갱신.

---

## 1. 개요 (YAML)

```yaml
name: Protected corridor lifecycle alignment
overview: >
  Align protected corridor lifecycle with Algorithm §14 / Epic C.
  This PR is limited to candidate/soft/hard corridor lifecycle and guard behavior.
  It must not change routing heuristics, PlacementCommitState FSM, recovery return paths,
  or replay UI behavior.

canonical_documents:
  - documents/Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md
  - documents/Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md
  - documents/Algorithm/mining_solver_cursor_sessions/10_step6_reclaim_loop.md
  - documents/refactory/corridor-state-machine-refactor.md
  - documents/refactory/04_protected_corridor_lifecycle.md
  - documents/refactory/14_soft_corridor_atomic_replace.md

known_drift:
  - file: django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_routing_state.py
    issue: soft_protected_candidate_corridors and soft_protected_confirmed_corridors were serialized from the same soft_cells set.
    expected: At STEP4 committed-route snapshot, candidate pool is empty; confirmed matches committed soft pool.

scope:
  include:
    - candidate_corridor lifecycle
    - soft_protected promotion/removal conditions
    - hard_protected mutation rejection
    - replacement route prevalidation
    - atomic soft corridor replacement guard fields
    - ExistingLayoutAnalysis seed protection boundary
  exclude:
    - route scoring or Dijkstra/A* weights
    - Pass3 lexicographic priority
    - PlacementCommitState FSM
    - recovery trigger return paths
    - replay UI redesign
```

---

## 2. 필드 전략 결정 (소비자 맵 이후)

| 키 | 소비자(요약) |
|----|----------------|
| `hard_protected_corridors` | Pass3 guarded / P4 reclaim / finalize 요약 / replay overlay / spatial_authority / reclaim_corridors merge |
| `soft_protected_corridors` | 동상 + `pass3_e3_guarded_atomic_map` / `reclaim_map_ops` |
| `soft_protected_candidate_corridors` | `reclaim_corridor_read_factory` replay overlay 병합, `finalize` 후보 카운트(overlay `counts.candidate`) |
| `soft_protected_confirmed_corridors` | `test_step4_merge_routing` 등 STEP4 계약 검증 |

**결정 (STEP4 `_routing_state_from_committed_routes` 한정):**

- **진짜 분리:** 이 함수는 **이미 commit된** route만 입력으로 받으므로, 미검증 probe/shadow 후보는 존재하지 않는다.
- 따라서 `soft_protected_candidate_corridors`는 **빈 리스트**로 직렬화한다.
- `soft_protected_confirmed_corridors`와 `soft_protected_corridors`는 기존과 같이 **동일 집합(soft_cells)** — P4·finalize·Pass3가 읽는 평면 `soft` 키는 유지.
- `soft_protected_corridors`를 confirmed와 다른 의미로 쓰는 소비자는 없으므로 **legacy alias 불필요**; candidate만 분리.

---

## 3. Call-site map (읽기/쓰기·직렬화)

### 3.1 쓰기(생산)

| 위치 | 동작 |
|------|------|
| [`step4_routing_state.py::_routing_state_from_committed_routes`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_routing_state.py) | STEP4 commit 스냅샷에서 flat·nested `protected_corridors` 및 candidate/confirmed/hard 채움 |

### 3.2 읽기(주요)

| 위치 | 사용 키 |
|------|---------|
| [`finalize.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/finalize.py) | `hard`/`soft` 리스트 길이, `protected_corridors_overlay_from_routing_state`로 `candidate` 카운트 |
| [`reclaim_corridor_read_factory.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridor_read_factory.py) | hard, soft, **candidate** (replay overlay) |
| [`reclaim_corridors.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridors.py) | hard, soft (P4 merge; candidate 키 미사용) |
| [`pass3_e3_guarded.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3/pass3_e3_guarded.py) | hard/soft frozenset 병합 |
| [`pass3_e3_guarded_atomic_map.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3/pass3_e3_guarded_atomic_map.py) | hard/soft + replacement 가드 |
| [`placement/spatial_authority.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/spatial_authority.py) | hard, soft |
| [`existing_layout/pass12_existing_layout_hints.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/existing_layout/pass12_existing_layout_hints.py) | ELA는 `pass12_*` 별도 키; `routing_state`와 직접 합치지 않음 |

### 3.3 테스트·픽스처

- `test_step4_merge_routing.py`, `test_solver_replay_corridors.py`, `test_pass3_transport.py`, `test_reclaim_shadow.py`, `test_mining_solver_stabilization.py` 등.

---

## 4. PR4 리뷰 체크리스트 (6)

1. candidate와 confirmed soft가 **의미 없이** 동일 집합으로 뭉개이지 않는가 (STEP4 스냅샷: candidate 비어 있음).
2. failed probe candidate가 confirmed로 새지 않는가 (본 PR은 STEP4 생산 경로만; P4 probe는 별 trace).
3. soft 제거 전 replacement 검증 — 기존 `P3E3_REJECT_*`·P4 soft replace 유지.
4. atomic replace 순서 — 기존 guarded / P4 경로 유지.
5. hard 제거 거절 — Pass3 precheck 등 기존 유지.
6. ELA trunk seed는 `pass12_*` 힌트로만 존재하고 STEP4 `routing_state` hard와 혼동되지 않는가.

---

## 5. 구현 프롬프트 (승인 후 참고)

```yaml
name: Implement protected corridor lifecycle guards
overview: >
  Implement the approved ACTIVE plan for protected corridor lifecycle alignment.
preconditions:
  - This ACTIVE document committed under documents/plans/.
  - Branch includes PR3 semantic namespace work (already on master).
validation:
  - python -m pytest tests/unit/shapez_asteroid/
  - ruff check .
  - mypy .
  - black --check .
commit:
  message: "refactor(solver): align protected corridor lifecycle with Algorithm §14"
```
