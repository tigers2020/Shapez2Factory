---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: J
pr: 5
related_docs:
  - documents/Algorithm/solver_runtime/00_core_principles.md
  - documents/Algorithm/asteroid_lab_07_incremental_commit.md
---

# Phase J — Incremental Commit

## 목적

선택된 candidate를 실제 layout 후보로 **확정**한다. commit-time probe가 유일한 연결 증명이다.

## 입력

```text
SelectedCandidatePlan
OptimizationInput (latest route_domain 누적)
```

## 산출물

```text
Confirmed placements
RouteReservation(s)
updated trunk / goal load
```

## 작업

```text
for candidate in selected_order:
    rebuild latest route_domain
    re-run route_probe from route_probe_start
    if failed:
        rollback / skip candidate
    else:
        create RouteReservation
        reserve path
        promote placement to confirmed
        update trunk load
```

### Commit-time probe is authoritative

```text
commit success proof = latest route_domain reprobe
```

candidate phase route result는 참고용만.

### Route sharing

- 허용: same transport kind path sharing
- 제한/금지: shape belt / fluid pipe **same cell** sharing

### Capacity

commit 이후 edge / goal load 누적. `load >= capacity`이면 동일 edge/goal 사용 후보에 high cost 또는 reject ([OD-3](open_decisions.md)).

## 금지

- candidate probe만으로 commit 확정 ([§0.5](00_core_principles.md))
- `route_domain` in-place mutation (`RouteDomainSnapshotBuilder` 재빌드만)
- validation에서 repair

## 완료 조건

- [x] confirmed candidate마다 최신 domain reprobe 성공
- [x] 실패 candidate rollback/skip deterministic
- [x] goal load·reservation 상태 갱신
- [x] shape/fluid domain 분리

## 필수 테스트

```text
test_incremental_commit_reprobes_latest_domain
test_incremental_commit_confirms_connected_candidate
test_incremental_commit_rolls_back_unreachable_candidate
test_incremental_commit_updates_goal_load
test_incremental_commit_separates_shape_and_fluid_domains
```

## RouteDomainSnapshotBuilder (commit)

| API | commit 사용 |
|-----|-------------|
| `build_snapshot(..., confirmed_reservations, committed_occupied_cells)` | **정본** — 매 시도 직전·성공 후 재빌드 |
| `build_seed_snapshot` | 시드만 |
| `build_commit_snapshot` | 미구현·선택 deprecated wrapper — semantics 금지 |

## 관련 코드·문서

- 구현: `commit_best_candidates.py` (`commit_selected_candidates`)
- 테스트: `tests/unit/asteroid_lab/test_incremental_commit.py`
- [`asteroid_lab_07_incremental_commit.md`](../asteroid_lab_07_incremental_commit.md)

## 다음 Phase

→ [`phase_k_route_materialization.md`](phase_k_route_materialization.md)
