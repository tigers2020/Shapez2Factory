---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: I
pr: 4
related_docs:
  - documents/Algorithm/solver_runtime/open_decisions.md
  - documents/Algorithm/asteroid_lab_06_evolutionary_search.md
---

# Phase I — Candidate Selection v0

## 목적

**Solver Button v0 정본 선택기** — capacity-aware **greedy** only. Candidate pool에서 **commit 시도 순서**를 만든다. 아직 확정 배치가 아니다.

> **GA 미사용:** [`asteroid_lab_06_evolutionary_search.md`](../asteroid_lab_06_evolutionary_search.md) · `Genome`/`Gene.commit_order` 는 **legacy reference** ([`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) §3).

## 입력

```text
CandidatePool (normal)
PlannedRouteGoals / capacity_plan
OptimizationInput
```

## 산출물

```text
SelectedCandidatePlan
ordered candidate ids
```

## 작업

### v0 Score

```text
score =
    + throughput_factor * 100
    - route_cost * 5
    - goal_priority * 20
    - estimated_corridor_pressure
    - trunk_load_pressure
```

### Capacity-aware trunk load

Shape:

```text
trunk capacity = 12 fully boosted platforms
```

Fluid:

```text
trunk capacity = 72 fully boosted platforms
```

```python
load_ratio = assigned_platform_count / capacity_by_transport_kind
```

포화에 가까운 goal은 penalty 증가. **v1 (OD-3):** alternate trunk가 있으면 hard reject; 전부 overflow면 penalty pool fallback ([OD-3](open_decisions.md)).

### 정책

- capacity-aware **greedy** selector (v0)
- GA는 v1 ([OD-4](open_decisions.md))

## 금지

- selection 단계에서 layout commit
- candidate 생성 enumeration 순서를 commit order로 사용

## 완료 조건

- [x] 동일 pool·plan에서 선택 순서 deterministic
- [x] 고 throughput·저 route cost 후보가 우선
- [x] saturated goal에 penalty 반영

## 필수 테스트

```text
test_candidate_selector_prefers_high_throughput_low_cost
test_candidate_selector_penalizes_saturated_goal
test_candidate_selector_is_deterministic
```

## 관련 코드·문서

- 구현: `candidate_score.py`, `candidate_selector.py` (`select_gene_candidates_greedy`)
- 테스트: `tests/unit/asteroid_lab/test_candidate_selector.py`
- 레거시 GA: [`asteroid_lab_06_evolutionary_search.md`](../asteroid_lab_06_evolutionary_search.md)

## 다음 Phase

→ [`phase_j_incremental_commit.md`](phase_j_incremental_commit.md)
