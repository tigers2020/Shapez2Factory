# 14 — STEP 10: Replay · trace · UI (§16, P6)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 모든 선행 조각

> **전제**: [`01_project_overview.md`](./01_project_overview.md) §0과 같이 solver 구현 **백지**, 문서·trace 스키마가 정본이다.

---

## 16. Replay Visualization 목표

### 16.1 UI 요구사항

solver는 버튼 클릭 후 자동 실행된다.

**실시간 streaming(진행 중)**: 솔버 내부 **계산 cycle**을 카운트하고, **매 10 cycle마다** STEP 10(map visualization 단계)의 표시 상태를 갱신해 UI에 반영한다. 목적은 긴 탐색·배치 루프에서도 진행 상황이 끊기지 않고 스트리밍처럼 보이게 하는 것이다.

**cycle 정의(정본)**: “한 cycle”이 무엇인지(예: beam 평가 1회, 라우팅 frontier 확장 1회, reclaim 후보 시도 1회 등)는 구현에서 **단일 규칙**으로 고정하고, 재현·디버깅을 위해 trace에 `computation_cycle` 또는 동등 필드로 누적값을 남길 수 있다. UI 갱신은 **cycle % 10 == 0**일 때(0 포함) 또는 동등한 “10회마다 1회” 규칙으로 결정론적으로 수행한다.

**완료 후 replay**: solve가 끝나면 trace·pass 스냅샷을 기준으로 **step-by-step 재생**(슬라이더·play/pause 등)이 가능해야 한다. 위 streaming 간격은 **완료 후 재생 속도**와 별개다.

```text
decode 단계는 내부적으로 처리해도 되지만,
solver pass 결과는 사용자가 볼 수 있어야 한다.
```

---

### 16.2 권장 replay 단계

```text
0. Original decoded map
1. 기존 belt/pipe 제거 표시
2. 기존 extractor 제거 표시
3. 기존 extension 제거 표시
4. asteroid field / mineable mask 표시
5. Pass1 outer placement 표시
6. Pass2 internal fill placement 표시
7. merge-aware routing 결과 표시
8. Pass3 route optimization **before/after** 표시  
   - before 스냅샷: **Pass3 시작 직전**(STEP 4 routing 완료 후·STEP 5 진입 직전 동일 레이아웃).  
   - after 스냅샷: **Pass3 종료 직후**(STEP 5 성공 커밋 시점).  
   - trace에는 §16.3 `layout_snapshot_before_pass3` / `layout_snapshot_after_pass3`(또는 동등 필드)로 고정한다.
9. reclaim placement loop 표시
10. post-reclaim Pass3 rerun 표시, 발생 시
11. recovery / degraded commit 표시, 필요한 경우만
12. final layout 표시
```

---

### 16.3 trace event schema 초안

`placements_removed`는 항상 존재하는 필드가 아니다. placement 제거는 recovery demolition, rollback, quarantine 해제 실패 때만 기록한다.

`transport_kind`의 `batch_mixed`는 **혼합 trunk 허용**을 뜻하지 않는다. 하나의 trace event가 shape belt와 fluid pipe 작업을 batch로 함께 기록했을 때만 `batch_mixed`를 사용한다. 개별 route/trunk event는 반드시 `shape_belt` 또는 `fluid_pipe` 중 하나여야 한다.

```yaml
trace_event:
  run_id: string
  phase: string
  step_index: int
  computation_cycle: int | null   # 누적 계산 cycle(§16.1 정본); UI는 매 10 cycle마다 갱신
  event_type: string
  recovery_trigger: string | null  # 분기 진입 이유 (commit_reason 아님)
  layout_snapshot_before_pass3: object | null   # STEP 5 직전 동일 스냅샷(replay overlay 정본)
  layout_snapshot_after_pass3: object | null    # STEP 5 직후
  layout_snapshot_phase: string | null          # 스냅샷이 대응하는 phase enum
  placements_added: list
  placements_removed: list | null
  placements_quarantined: list | null
  routes_added: list
  routes_removed: list
  protected_corridors:
    hard: list
    soft: list
  transport_kind: shape_belt | fluid_pipe | batch_mixed | none
  search:
    search_mode: lexicographic_dijkstra | weighted_astar | baseline_shortest | failed | null
    expanded_nodes: int | null
    search_time_ms: int | null
    fallback_reason: string | null
  metrics:
    extractor_count: int
    extension_count: int
    route_cell_count: int
    internal_transport_count: int
    optimization_baseline_internal_transport: int | null   # §15.4 counterfactual baseline
    pass3_internal_transport_saved: int | null
    reclaim_internal_transport_added: int | null
    net_internal_transport_saved_after_reclaim: int | null
    placement_candidate_blocked_count: int
    transport_connected: bool
    capacity_safe: bool
    trunk_load: dict
    recovery_attempts_total: int
    validation_recovery_attempts: int
    cascade_corrective_attempts: int
    recovery_internal_transport_delta: int | null
    baseline_internal_transport_at_reclaim_entry: int | null  # §12.5 net 비교 기준선
    external_margin_bbox_source: mineable | shell | null      # §3.5
  decision:
    committed: bool
    commit_reason: string          # §13.5: 성공 커밋 분류만
    rejected_reason: string | null
    rollback_reason: string | null # §13.5: 제거·거절 사유
    optimality_guarantee: bool | null
```

`committed=false`인 이벤트에서는 `commit_reason`을 비우고 `rejected_reason` / `rollback_reason`만 사용한다(§13.5).

---

### 16.4 Existing layout analysis — replay 레이어

STEP 0.5 `ExistingLayoutAnalysis`가 있으면 replay·copy-preview UI에서 다음 **선택 레이어**를 노출할 수 있다(구현체는 `visible_by_default` 등을 별도 합의).

```yaml
existing_layout_layers:
  - original_main_trunk_component
  - original_orphan_transport_components
  - original_single_cell_transport_artifacts
  - original_miners_without_adjacent_transport
  - original_miners_attached_to_orphan_transport
  - existing_layout_issues_overlay
```

최종 최적 레이아웃(§16.2 step 12)과 **동시에** 켜서 비교할 수 있어야 한다.

---

## 부록: P6 체크리스트 (원문 §20)

### P6 — Replay UI 확장

```text
[ ] pass별 map snapshot 저장
[ ] solve 진행 중 계산 cycle **매 10회마다** visualization 갱신(실시간 streaming, §16.1)
[ ] before/after overlay 지원
[ ] rejected candidate debug layer 추가
[ ] hard/soft protected corridor layer 추가
[ ] STEP 0.5 existing layout 레이어(§16.4 `existing_layout_layers`) 추가
[ ] quarantine / rollback placement layer 추가
[ ] play / pause / slider UI
[ ] final score breakdown 표시
```
