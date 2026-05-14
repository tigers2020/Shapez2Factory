# ACTIVE: Protected corridor lifecycle alignment (PR4)

**상태:** ACTIVE (구현 진행 중)  
**Epic:** C — [`documents/refactory/corridor-state-machine-refactor.md`](../refactory/corridor-state-machine-refactor.md)  
**범위:** Algorithm §14 / Epic C — **candidate / soft / hard 생명주기·가드만.** 라우팅 가중치·Placement FSM·recovery 복귀 경로·replay UI 재설계 제외.

**사람 승인:** 프로젝트 게이트상 의미 있는 계약 변경은 승인 후 본문에 날짜·승인자를 기록한다.

**PR4-A (1차, 완료):** STEP4 committed 스냅샷에서 `soft_protected_candidate_corridors` vs confirmed/compat 의미 분리 — 커밋 `947b671e`, **원격 `origin/master` 반영됨 (2026-05-12).** PR 제목 예: `refactor(solver): align committed corridor snapshot semantics` (본문에서 “PR4 전체 완료”가 아니라 **PR4-A 1차**임을 명시).

**PR4-B (이번 패치):** `hard_protected` 교집합·제거·치환 경로 가드 보강 및 회귀 테스트 — 아래 §6–§7.

**구현 반영(2026-05-12, PR4-A):** `step4_routing_state.py` — STEP4 committed-route `routing_state`에서 `soft_protected_candidate_corridors`를 빈 리스트로 직렬화. 단위 테스트: `test_protected_corridor_step4_snapshot.py`, `test_step4_merge_routing.py` 갱신.

**구현 반영(2026-05-12, PR4-B):** `routing/protected_corridor_replace.py` — 소프트 치환 시 `old_soft_corridor_cells ∩ hard`이면 `P4_REJECT_HARD_PROTECTED_CORRIDOR`로 즉시 거절. 테스트: `test_reclaim_shadow.test_soft_replace_rejects_hard_protected_corridor_map_unchanged`. 커밋 `c2a5d838`.

**구현 반영(2026-05-12, PR4-C):** `step4_routing_state` / `step4_merge_routing` — ELA trunk seed 관측 키 `ela_trunk_seed_candidate_corridors` 및 단위 테스트(§8).

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
| `ela_trunk_seed_candidate_corridors` | 관측·NDJSON(해시 제외); P4·Pass3·finalize 기본 경로 미소비 |

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

### 3.4 ELA trunk seed → 보호 코어 흐름 (PR4-C)

| Source (ELA) | 소비 경로 | hard 승격 |
|----------------|-----------|-----------|
| `solver_hints.trunk_seed_cell_union` (`main_trunk_candidate`) | Pass12 `pass12_existing_layout_barrier_meta` (mineable barrier), STEP4 `trunk_seed_union_from_existing_layout`·goal/cheap_reuse, P4 `existing_layout_solver_hints` → **soft 병합** | STEP4 `_routing_state_from_committed_routes`는 stub·`path[-1]`만 hard; trunk seed 본선은 `ela_trunk_seed_candidate_corridors`로만 직렬화(해시 미포함) |
| `solver_hints.cleanup_candidate_cell_union` | 동상 P4 soft 병합 | hard 자동 승격 없음 |
| `pass12_hard_protected_corridor_cells` 등 (선택 replay 오버레이) | `pass12_transport_related_block_extra_cells` | `routing_state` 생산과 별개; 수동 하드 증명 시에만 사용 |

**예외(geometry):** 커밋 route의 `stub_cell` 또는 `path[-1]`이 trunk seed와 겹치면 해당 좌표는 hard에 들어간다(끝점 규칙).

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

Algorithm §14 세부 문구는 저장소의 [`documents/refactory/04_protected_corridor_lifecycle.md`](../refactory/04_protected_corridor_lifecycle.md) 등 refactory 노트와 외부 세션 정본을 함께 본다.

---

## 6. PR4-B: `hard_protected` 가드 경로 맵 (코드 SSOT)

| 경로 | 모듈 | 거절/불변 |
|------|------|-----------|
| P3-E3 원자 precheck | `pass3/pass3_e3_guarded_atomic_map.py::_p3e3_build_atomic_candidate_map` | `cells_to_remove ∩ hard` → `P3E3_REJECT_HARD_PROTECTED_CORRIDOR`, candidate 비어 있음 |
| P3-E3 trial 맵 | `pass3/pass3_e3_guarded_transport_trial.py` | trial transport에 hard ⊆ 검증 |
| P4 후보 overlap | `reclaim/reclaim_map_ops.py::_p4_overlap_reject_reason` | `placed ∩ hard` → `P4_REJECT_HARD_PROTECTED_CORRIDOR` |
| P4 shadow stub 경로 | `reclaim/reclaim_shadow_scan_eval.py` | stub/anchor/extension ∈ hard → `P4_REJECT_HARD_PROTECTED_CORRIDOR` |
| §14.3 소프트 원자 치환 | `routing/protected_corridor_replace.py::try_atomic_replace_soft_corridor` | `old_cells ∩ hard` → `P4_REJECT_HARD_PROTECTED_CORRIDOR` (soft 풀 검사 전) |
| Pass3-F trace | `pass3/pass3_f_branch_candidate.py` | `p3f_hard_protected_preserved` 요약(원자 거절은 위 atomic_map) |

**회귀 테스트 (PR4-B):** `test_pass3_transport.test_p3e3_build_rejects_hard_protected_corridor`, `test_reclaim_shadow` 내 hard reclaim·`test_soft_replace_rejects_hard_protected_corridor_map_unchanged`.

---

## 7. Phase 체크리스트

| Phase | 내용 | 상태 |
|-------|------|------|
| PR4-A | STEP4 committed 스냅샷 candidate `[]` / confirmed·compat 동일 soft 풀 | 완료 (`947b671e`, origin 반영) |
| PR4-B | Pass3·P4·소프트 치환에서 hard 제거/치환 시도 거절 + 테스트 | 완료 (`c2a5d838`: 소프트 치환 hard 교차; Pass3/P4 overlap 등 기존 가드 유지) |
| PR4-C | ELA trunk seed vs `routing_state` hard 경계 | 완료 (`ela_trunk_seed_candidate_corridors` + 단위 테스트) |

---

## 8. PR4-C: ELA trunk seed vs hard (구현 체크리스트)

**목표:** `ExistingLayoutAnalysis` / `solver_hints.trunk_seed_cell_union`(`main_trunk_candidate`)이 STEP4 commit 증명 **이전**에 `hard_protected_corridors`로 승격되지 않도록 계약·테스트로 고정한다.

### 8.1 코드 변경 (요약)

1. [`step4_routing_state.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_routing_state.py)  
   - `_routing_state_from_committed_routes(..., existing_layout_analysis=None)` 추가.  
   - `existing_layout_analysis is not None`이면 `trunk_seed_union_from_existing_layout`으로 집합을 구해 **`ela_trunk_seed_candidate_corridors`** 키에 좌표 리스트 직렬화(관측·§14 candidate와 hard 분리). **`hard` 집합에는 합치지 않음.**  
   - 모듈 상단 docstring에 §14 / `ROUTING_STATE_KEYS_STEP4_HASH` 비포함 명시.

2. [`step4_merge_routing.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_merge_routing.py)  
   - `_routing_state_from_committed_routes(..., existing_layout_analysis=existing_layout_analysis)` 전달.

### 8.2 테스트

- [`test_protected_corridor_step4_snapshot.py`](../../tests/unit/shapez_asteroid/test_protected_corridor_step4_snapshot.py) 또는 전용 모듈:  
  - path **중간** 셀이 ELA `trunk_seed_cell_union`에 있어도 `hard_protected_corridors`에 없고 `soft`에 있음.  
  - stub / `path[-1]`이 trunk_seed와 겹치면 hard에 있을 수 있음(geometry endpoint).  
  - ELA 전달 시 `ela_trunk_seed_candidate_corridors`가 `trunk_seed_cell_union`과 일치.  
  - `existing_layout_analysis=None`이면 키 `ela_trunk_seed_candidate_corridors` 없음(기존 호환).

- [`test_existing_layout_analysis.py`](../../tests/unit/shapez_asteroid/test_existing_layout_analysis.py):  
  - 고립 orphan belt 좌표는 `cleanup_candidate_cell_union`에만 있고 `trunk_seed_cell_union`에 없음(기존 `test_isolated_belt_component_is_orphan_issue` 픽스처 활용 가능).

### 8.3 검증 명령

`python -m pytest tests/unit/shapez_asteroid/` → `ruff check .` → `mypy .` → `black --check .`

### 8.4 완료 보고용 표

| Source | Flow target | Before | After | Test |
|--------|----------------|--------|--------|------|
| main_trunk_candidate | trunk_seed_cell_union | candidate; `routing_state`에 ELA 전용 키 없음 | candidate; `ela_trunk_seed_candidate_corridors`로 관측, `hard` 비포함 | `test_routing_state_el_trunk_seed_mid_path_not_hard`, `test_routing_state_el_trunk_seed_candidate_key` |
| orphan_component | cleanup_candidate_cell_union | cleanup | trunk_seed / hard 비포함 유지 | `test_ela_trunk_seed_excludes_orphan_belt_cells`, `test_ela_single_cell_belt_not_in_trunk_seed` |
| committed STEP4 route | soft/confirmed pool | confirmed | PR4-A와 동일 | `test_routing_state_from_committed_routes_leaves_soft_candidate_pool_empty` |
