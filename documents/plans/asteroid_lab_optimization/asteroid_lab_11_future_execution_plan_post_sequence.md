# Asteroid Lab — Future Execution Plan (Post Sequence 11)


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md`](../../Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

Role: Principal Solver System Architect

---

# 목적

현재까지 완료된:

```text
Sequence 1A–11B
12C–12E
```

이후의 개발 우선순위·범위·금지사항·검증 조건을 정본 수준으로 고정한다.

본 문서는:

```text
Optimization replay
Evolutionary optimization
Incremental commit
UI replay
Regression stability
```

를 장기적으로 유지 가능한 형태로 확장하기 위한 후속 계획이다.

---

# 현재 상태 요약

현재 구현 상태:

```text
[x] DTO / topology / route domain
[x] pattern library
[x] candidate + probe
[x] genome / fitness
[x] evolutionary search v0
[x] incremental commit
[x] validation
[x] optimization replay
[x] dual-track replay UI
[x] readonly overlay projection
[x] overlay rendering
[x] POST optimization replay persist
```

남은 핵심 리스크:

```text
- narrow corridor starvation
- replay scale growth
- overlay lifecycle drift
- commit survivability under congestion
- route fragility after reservation accumulation
- full-repository gate debt
```

---

# 핵심 원칙 (계속 유지)

## 1. Replay is output only

```text
Replay / artifact / metrics / NDJSON
must never become solver input.
```

---

## 2. No implicit replay synchronization

```text
Lab replay
!=
Optimization replay
```

명시적 정책 없이:

```text
- frame index coupling
- autoplay coupling
- timeline ownership merge
```

금지.

---

## 3. Placement never bypasses feasibility

계속 유지:

```text
candidate generation
+
immediate route feasibility
```

---

## 4. Commit-time probe is authoritative

candidate 단계 reachable은:

```text
commit success guarantee 아님
```

항상:

```text
latest route_domain snapshot
```

기준 재-probe.

---

# 다음 우선순위

# Priority 1 — Sequence 10 Completion

**상태 정리 (2026-05-21, 실제 트리 기준 재정렬):** [`asteroid_lab_10_development_sequence.md`](../../Algorithm/asteroid_lab_10_development_sequence.md) §10B — **계약·관측 목표만 문서화, 구현·fixture 미착수**. 아래 경로는 **설계·계획용**이며 현재 저장소에 없을 수 있다: `tests/fixtures/shapez_asteroid/`, `tests/unit/shapez_asteroid/`. **실제 v0 검증**은 `tests/unit/asteroid_lab/`. **10B narrow corridor / survivability 회귀 팩·JSON 골든·replay_long 봉투**는 후속. **Lab unified replay** truncation 짝은 런타임 **프레임 `metrics` → 트랙 `metrics`**; fixture 봉투 최상위 `truncation_reason`은 **골든 전용**. “Sequence 10 전부 완료”로 읽지 말 것.

## 목표

```text
corridor / congestion / route fragility
```

회귀 검증 기반 확보.

---

# Sequence 10A — Narrow Corridor Fixture

## 목적

좁은 corridor 환경에서:

```text
- trunk sharing
- congestion
- unreachable after commit
- route starvation
```

을 재현 가능하게 만든다.

---

## Fixture 요구사항

```text
single narrow corridor
multiple extractor competition
mixed transport kinds
existing trunk attachment
protected corridor overlap risk
```

---

## 포함해야 하는 상황

### 상황 1

```text
candidate probe reachable
→ commit 단계 unreachable
```

---

### 상황 2

```text
high throughput candidate
blocks future expansion
```

---

### 상황 3

```text
shared corridor pressure
causes rollback
```

---

### 상황 4

```text
shape belt corridor
fluid pipe conflict
```

---

## 테스트

```text
test_narrow_corridor_probe_vs_commit_regression
test_shared_corridor_pressure_regression
test_future_expansion_penalty_regression
test_trunk_sharing_penalty_regression
test_transport_kind_corridor_conflict_regression
```

---

## 완료 조건

```text
[ ] deterministic optimization result
[ ] replay stable across same seed
[ ] congestion regression reproducible
[ ] commit rollback reproducible
```

---

# Sequence 10B — Route Fragility Regression Pack

```text
10B-v0: metrics contract + PenaltyMode — spec only (see asteroid_lab_10 §10B, not implemented)
10B narrow corridor expansion (#14): [ ] planned under tests/unit/asteroid_lab/ or future shapez_asteroid fixtures
10B symmetric dual-goal narrow bridge: [ ] planned
JSON fixture pack (shapez_asteroid/replay/, replay_long/): [ ] planned; fixture envelope ≠ runtime persist
```

> **구현 교차 참조 (2026-05-21):** `CommitSurvivabilityMetrics`·`PenaltyMode`·`COMMIT_SURVIVABILITY_SUMMARY`는 **문서 계약만** 존재. Python DTO·골든·`summarize_incremental_commit`는 미착수. **Predictive** penalties는 Phase 5; **observed** survivability는 replay·post-commit 전용(솔버/GA 입력 금지).

## 목적

fitness의:

```text
route_fragility_penalty
shared_corridor_pressure_penalty
```

가 실제 commit survivability와 연결되는지 검증.

---

## 작업

```text
[ ] reservation accumulation fixture
[ ] corridor starvation replay fixture
[ ] late-generation unreachable fixture
```

---

## 완료 조건

```text
[ ] fragility penalty 없는 경우 regression 재현 가능
[ ] penalty 적용 시 regression 감소 확인
```

---

# Priority 2 — Sequence 11C

# Sequence 11C — Explicit Replay Sync Policy

## 상태

```text
optional
not default
```

현재 기본 정책:

```text
no implicit sync
```

유지.

---

## 이 시퀀스를 시작하는 조건

다음 UX 요구가 실제로 필요할 때만:

```text
- coupled playback
- lockstep timeline mode
- jump-to-related-frame
- synchronized scrubber
```

---

## 금지

다음은 절대 자동 연결 금지:

```text
same frame number
same event order
same playback speed
```

---

## 허용 방식

반드시:

```text
explicit sync mode
```

를 사용자 toggle로 둔다.

예:

```text
[ ] Sync optimization timeline with lab replay
```

---

## 요구 사항

### Sync ownership

동기화 상태에서도:

```text
Lab replay owns map rendering
Optimization replay owns optimization metadata
```

유지.

---

### One-way sync 우선

v0 권장:

```text
optimization frame
→ optional lab replay jump
```

단방향.

역방향 autoplay coupling 금지.

---

## 테스트

```text
test_explicit_sync_mode_disabled_by_default
test_explicit_sync_mode_does_not_mutate_lab_state_when_disabled
test_explicit_sync_mode_preserves_overlay_ownership
```

---

## 완료 조건

```text
[ ] sync mode optional
[ ] disabled by default
[ ] no implicit coupling remains
```

---

# Priority 3 — Overlay Lifecycle Stability

주의:

```text
현재 정본 시퀀스에는 없음
```

필요 시:

```text
11D
```

로 확장.

---

# Proposed Sequence 11D — Overlay Lifecycle Stability

## 목적

overlay replay가:

```text
large replay
rapid scrub
zoom/pan
DOM rebuild
```

상황에서 안정적으로 유지되게 한다.

---

## 작업

```text
[ ] projection cache
[ ] stale render guard
[ ] replay_truncated HUD
[ ] overlay partial repaint
[ ] transform ownership invariant
```

---

## 핵심 invariant

```text
Overlay never owns viewport transform.
```

viewport transform owner:

```text
Lab stage only
```

---

## 테스트

```text
test_overlay_projection_cache_deterministic
test_overlay_stale_render_guard
test_overlay_transform_ownership
test_overlay_partial_repaint
```

---

## 완료 조건

```text
[ ] overlay redraw deterministic
[ ] rapid scrub race 없음
[ ] zoom drift 없음
[ ] replay_truncated visible
```

---

# Priority 4 — Evolution Search v1

현재는:

```text
mutation-only + repair
```

중심.

다음 단계는:

```text
diversity stabilization
```

이다.

---

# Sequence 12A — Diversity Stabilization

## 목적

국소 최적 붕괴 방지.

---

## 작업

```text
[ ] topology diversity metrics
[ ] rim entropy metrics
[ ] distant mutation scheduler
[ ] population collapse detector
```

---

## 테스트

```text
test_population_diversity_survives_long_run
test_forced_distant_mutation_breaks_local_optimum
```

---

## 완료 조건

```text
[ ] repeated same-topology collapse 감소
[ ] deterministic under same seed
```

---

# Sequence 12B — Commit Survivability Fitness

**타임라인:** **v0.1 (선행)** — Phase 5 `PenaltyMode.CONSERVATIVE` + predictive penalties (candidate domain). **v1+ (본 절)** — post-commit survivability estimation (observed metrics는 solver 입력 금지).

## 목적

fitness **predictive** 추정과 실제 commit 성공률의 정렬(전역 commit 예측기 아님).

---

## 작업

```text
[ ] v0.1: conservative fragility/corridor penalties in FitnessBreakdown (Phase 5)
[ ] v1+: post-commit survivability estimation (observability / replay only)
[ ] reservation pressure heuristic
[ ] future expansion survivability scoring
```

---

## 완료 조건

```text
[ ] reachable-but-uncommittable candidate 감소
```

---

# Priority 5 — Replay Scalability

현재:

```text
full snapshot replay
```

전제.

활성 셀 증가 시:

```text
memory / payload / DOM pressure
```

대응 필요.

---

# Sequence 13A — Replay Compression Research

## 목적

large replay artifact 대응.

---

## 작업

```text
[ ] delta frame prototype
[ ] immutable snapshot reuse
[ ] overlay diff serialization
[ ] binary replay experiment
```

---

## 중요

v0 replay contract 깨지면 안 된다.

즉:

```text
serialization optimization
!=
semantic replay mutation
```

---

## 테스트

```text
test_compressed_replay_equivalent_to_full_snapshot
test_replay_deterministic_after_compression
```

---

## 완료 조건

```text
[ ] replay semantic equivalence 유지
[ ] payload 감소 확인
```

---

# Sequence 13B — Lab replay payload attribution (reduction design only)

**범위:** ``measure_json_sections`` Lab 전용 확장, POST 회귀에서 중복·상위 프레임 메타 키 존재, ``asteroid_lab_09_replay_debug.md`` 「Sequence 13B」·본 절 동기화. **페이로드 축소 구현은 13C.**

## 완료 조건

```text
[x] Lab replay 기여도·중복 프로파일을 테스트 헬퍼로 측정 가능
[x] optimization ``MAX_REPLAY_*`` vs Lab 미캡 경계 문서화
[x] 13C 옵션 순위·시맨틱 리스크·동등성 테스트 설계 초안
```

---

# Sequence 13C — Lab replay payload reduction (implementation TBD)

13B 설계·계측 승인 후: delta·intern·엔드포인트 분리·HTTP 압축 등 **별도 구현 PR**. 본 문서는 13C 착수 시 ``asteroid_lab_09`` 「13C」절과 실행 순서를 갱신한다.

---

# Priority 6 — Full Repository Quality Gates

**2026-05-17 로컬 확인:** `python -m ruff check .` · `python -m black --check .` · `python -m mypy .` · `python -m pytest` 전부 green (792 tests, 코드 변경 없음). CI·타 환경에서의 재현은 별도 관측.

과거 메모(병합 전 known debt로 남기던 항목):

```text
ruff
mypy
black --check
```

---

# Sequence 14A — Repository Gate Cleanup

## 작업

```text
[x] 전 저장소 `ruff check .` 실행·green (2026-05-17 로컬)
[x] 전 저장소 `black --check .` 실행·green (동일)
[x] 전 저장소 `mypy .` 실행·green (동일)
[x] 전 저장소 `pytest` 실행·green (792 passed, 동일; 코드 변경 없음)
```

> 본 스윕에서는 위 게이트가 이미 green이라 **추가 기계적 수정 PR 본문은 없음**. 향후 드리프트 시 E501·스텁·포맷 이슈를 다시 이 표로 추적한다.

---

## 금지

optimization architecture 변경 금지.

이 시퀀스는:

```text
repository hygiene only
```

이다.

---

## 완료 조건

```text
[x] ruff check . green (2026-05-17 로컬)
[x] black --check . green (2026-05-17 로컬)
[x] mypy . green (2026-05-17 로컬)
[x] pytest full suite green (792 passed, 동일 날짜 로컬)
```

---

# 장기 계획 (v2+)

다음은 v0/v1 이후.

---

# Sequence 20+ — Advanced Optimization

## 후보

```text
CP-SAT hybrid refinement
corridor balancing
trunk redundancy scoring
multi-objective Pareto search
advanced reroute planner
```

---

## 금지

다음은 여전히 금지:

```text
cell-level GA
replay-driven algorithm
implicit replay coupling
```

---

# 최종 우선순위 요약

## Immediate

```text
1. Sequence 10A narrow corridor fixture
2. Sequence 10B route fragility regression
```

---

## Optional / Conditional

```text
3. Sequence 11C explicit sync policy
4. Sequence 11D overlay lifecycle stability
```

---

## Mid-term

```text
5. Sequence 12A diversity stabilization
6. Sequence 12B commit survivability fitness
7. Sequence 13A replay scalability — 연구/계측 단계(13A): ``tests/support/measure_json_sections.py``,
   통합 테스트 ``test_post_projects_json_size_attribution_and_optimization_replay_hard_caps``,
   근거·갭·후보 전략은 ``asteroid_lab_09_replay_debug.md`` 「Sequence 13A」 참고.
   (즉시 delta 구현·DTO 의미 변경은 범위 밖)
8. Sequence 13B Lab replay payload attribution — 13A 계측 확장(Lab 중복·상위 프레임·``lab_total_bytes``),
   동일 통합 테스트에서 13B 키 회귀, 설계·13C 로드맵은 ``asteroid_lab_09_replay_debug.md`` 「Sequence 13B」.
   (POST 페이로드 실제 축소는 13C)
```

---

## Infrastructure

```text
9. Sequence 14A repository gate cleanup
```

---

# 최종 결론

현재 가장 중요한 건:

```text
route feasibility
!=
commit survivability
```

상황을 regression fixture 수준에서 안정적으로 재현·검증 가능하게 만드는 것이다.

따라서 다음 실질 우선순위는:

```text
narrow corridor
shared corridor pressure
reservation accumulation
```

fixture 기반 regression 강화다.

그 이후에만:

```text
explicit replay sync
advanced overlay lifecycle
replay scaling
```

으로 가는 것이 안전하다.

