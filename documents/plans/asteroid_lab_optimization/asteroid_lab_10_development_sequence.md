# Asteroid Lab Optimization — Development Sequence

## 목적

GA + local pattern compiler + route feasibility 기반 optimization layer를 안전한 순서로 구현한다.

**필수:** `candidate 생성 → 즉시 route probe → normal pool` 은 분리된 “나중에 붙이기” 시퀀스로 두지 않는다. Phase 3 문서와 동일하게 Sequence 3 한 블록에서 완료한다.

---

## Sequence 1A — Domain DTO contracts

DTO·좌표 계약만 먼저 고정해 PR을 작게 유지한다. **hole asteroid fixture·adapter 검증은 1B로 분리**한다.

### 작업

```text
[ ] RouteGoal / RouteGoalKind
[ ] TopologyNode / TopologyEdge / TopologyGraph (무방향 계약)
[ ] OptimizationInput DTO (route_goals·topology_graph·existing_transport_cells·trunk·protected)
[ ] RouteProbeFailureReason / CandidateRejectReason / ValidationIssueCode / ValidationSeverity
[ ] EvolutionConvergenceReason / CommitConflictReason / OptimizationReplayEventType / ReservationState
[ ] RouteDomainSnapshotBuilder 시그니처(단일 route_domain 스냅샷 생성 진입점)
[ ] RouteDomainCellTransition / RecoveryBudget DTO (Phase 7과 동기)
[ ] GenomeDiversityMetrics / EvolutionConfig.forced_distant_mutation_period (Phase 6과 동기)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_input.py (DTO·좌표·빈 transport greenfield)
```

### 완료 기준

```text
[ ] 관련 DTO·enum import 가능 (순환 없음)
[ ] enum 멤버 이름·값이 Phase 문서와 동기화됨
[ ] OptimizationInput·그래프·goal의 모든 Coord가 Server X/Y 정본
[ ] `neighbors4_server` 밀집 4방 이웃 단위 테스트 (server x=0 포함 케이스)
[ ] route_goals가 kind·priority 계약을 만족하는 최소 factory 가능
[ ] greenfield = existing_transport_cells 비어 있음 ∧ trunk·protected 공집합 (별도 코드 경로 없음)
```

---

## Sequence 1B — Reconstruction adapter + RouteCellDomain seed builder

입력을 실제 reconstruction 출력과 연결하고, Phase 4가 소비할 domain 초안을 만든다.

### 작업

```text
[ ] Reconstruction → OptimizationInput adapter
[ ] rim / interior / route_goals 추출
[ ] RouteCellDomain 빌더 초안 (**RouteDomainSnapshotBuilder**; existing_transport_cells → transport_mask, trunk·protected·blocked 반영)
[ ] topology_graph 이웃이 neighbors4_server와 모순 없음 (그래프 빌더 테스트)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_input.py (adapter·builder 구간)
pytest tests/unit/shapez_asteroid/test_route_cell_domain_builder.py (파일명은 구현에 맞게)
```

### 완료 기준

```text
[ ] hole asteroid fixture에서 interior fill이 mineable로 유지됨
[ ] adapter가 greenfield·비-greenfield 동일 경로로 OptimizationInput을 생산
[ ] 빌더 출력이 blocked/hard_blocked와 모순 없음
```

---

## Sequence 2 — Pattern Library

### 작업

```text
[ ] BundlePattern DTO (attachments·throughput_factor)
[ ] linear 0~3 extension pattern
[ ] rotation support
[ ] deterministic pattern id
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_pattern_library.py
```

### 완료 기준

```text
[ ] ExtensionAttachment·throughput_factor·canonical E (output_dir=E) 계약
extractor + 0~3 extension linear pattern 생성
output_stub가 occupied_cells에 포함되지 않음
```

---

## Sequence 3 — Candidate Generator + Route Probe (통합)

후보가 normal pool에 들어가기 전 **반드시** probe를 통과한다.

### 작업

```text
[ ] BundleCandidate DTO (topology_signature·probe 스냅샷; factory만 생성; normal은 rejection 필드 없음)
[ ] CandidateGenerationResult (normal vs rejected)
[ ] CandidateEquivalenceKey + dedupe (max_candidates 전)
[ ] rim-only extractor **후보 생성만** — commit·greedy rim 설치 없음
[ ] extension mineable validation
[ ] reject reason tracking (enum)
[ ] RouteProbeInput / RouteProbeResult (route_domain·RouteGoal·reached_goal·topology_graph·goal_priority_weight)
[ ] bounded uniform-cost probe + transport mask
[ ] reachable → normal pool / unreachable → diagnostic 또는 폐기
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_bundle_candidate_generator.py
pytest tests/unit/shapez_asteroid/test_route_probe.py
pytest tests/unit/shapez_asteroid/test_candidate_route_probe_integration.py
```

### 완료 기준

```text
valid candidate와 rejected candidate가 deterministic
연결 불가능 candidate가 normal pool에 들어가지 않음
Candidate Generator가 placement를 확정하지 않음 (풀·probe만)
output_stub에서 RouteGoal 계약에 맞는 도달성 평가
blocked / hard_blocked 통과 금지
budget exceeded failure reason 기록
```

---

## Sequence 3B — Replay 최소 골격 (권장, 조기)

candidate/probe 디버깅을 **Sequence 8까지 미루지 않으면** 구현 난이도가 급증한다. UI timeline 전체는 Sequence 8이 담당하고, 여기서는 **기록 파이프라인만** 최소로 연다.

### 작업

```text
[ ] OptimizationReplayEventType + OptimizationReplayFrame 직렬화 (Phase 9 상수 MAX_REPLAY_*·replay_truncated 포함)
[ ] candidate.generated / candidate.rejected / route_probe.succeeded|failed 이벤트만 우선 기록
[ ] replay artifact는 algorithm input 금지 invariant 단위 테스트
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_replay_skeleton.py (파일명은 구현에 맞게)
```

### 완료 기준

```text
[ ] Sequence 3에서 한 번의 run에 대해 replay NDJSON(또는 동등 바이너리)이 쓰이고, 탐색 결과는 replay on/off 동일(Phase 9 invariant)
```

---

## Sequence 4 — Genome / Fitness

### 작업

```text
[ ] Gene / Genome DTO (Gene.commit_order)
[ ] FitnessBreakdown + FitnessMetrics
[ ] overlap penalty
[ ] unreachable penalty
[ ] route cost penalty
[ ] route_fragility_penalty / shared_corridor_pressure_penalty 필드 (v0는 0 허용)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_genome_fitness.py
```

### 완료 기준

```text
same input + same seed = same fitness
overlap/unreachable penalty가 throughput gain보다 강함
trunk vs margin 등 동일 reachable이라도 route goal 품질이 점수에 반영됨
좁은 통로 점유 시나리오에서 탐욕적 고처리량 우위가 깨질 수 있는 훅(패널티 필드) 존재
```

---

## Sequence 5 — Evolution Search v0

### 작업

```text
[ ] initial population
[ ] mutation
[ ] repair
[ ] elitism
[ ] forced_distant_mutation_period (None 허용) + GenomeDiversityMetrics 자리(0 허용)
[ ] EvolutionConvergenceReason enum + EvolutionResult
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_evolutionary_search.py
```

### 완료 기준

```text
same seed deterministic (population·mutation·fitness tie-break 포함)
best fitness non-decreasing under elitism
best genome 반환
```

---

## Sequence 6 — Incremental Commit

### 작업

```text
[ ] best genome candidate 정렬 (**Gene.commit_order** 정본; candidate 생성·rim 순 기본 금지)
[ ] route probe 재실행 (갱신된 route_domain)
[ ] RouteReservation (reservation_id·reached_goal·goal_priority·state·domain_cell_transitions)
[ ] CommitConflictReason 처리
[ ] commit / rollback + route_domain 반영
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_incremental_commit.py
```

### 완료 기준

```text
confirmed candidate는 exterior trunk route를 가진다
commit 실패 candidate는 local rollback된다
commit 순서가 genome `commit_order`와 일치하고 생성 enumeration 순에 묶이지 않는다
```

---

## Sequence 7 — Validation

### 작업

```text
[ ] final validation result
[ ] confirmed candidate ↔ 정확히 하나의 CONFIRMED RouteReservation 검증
[ ] reserved_cells ↔ path 일관성 검증
[ ] ValidationIssue (ValidationIssueCode·route_goal_kind·transport_kind·optional route_reservation_id·path_index)
[ ] extractor output connectivity check
[ ] orphan transport check
[ ] overlap check
[ ] Coord·`neighbors4_server` 밀집 격자 검증
[ ] RouteGoal·transport 일관성 (read-only 검증만)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_validation.py
```

### 완료 기준

```text
validation은 read-only
Validation must not invent new routes.
Validation must not mutate placement.
Validation must not fix topology.
```

(정본 서술: `documents/plans/asteroid_lab_optimization/asteroid_lab_08_validation.md` — 계약(금지))

---

## Sequence 8 — Replay Debug (전체 timeline·UI)

Sequence 3B에서 연 **최소 골격**을 확장해 전 이벤트·오버레이·컨트롤러를 완성한다.

### 작업

```text
[ ] optimization replay event (OptimizationReplayEventType)
[ ] frame serializer
[ ] route probe overlay
[ ] generation metric frame
[ ] validation frame
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_replay.py
```

### 완료 기준

```text
optimization 과정을 timeline으로 확인 가능
replay artifact는 algorithm input으로 사용되지 않음
```

---

## Sequence 9 — UI Integration

### 작업

```text
[ ] replay controller에 optimization track 추가
[ ] candidate overlay
[ ] route probe overlay
[ ] best genome overlay
[ ] validation issue overlay
```

### 테스트

```text
pytest tests/integration/shapez_asteroid/test_optimization_ui_payload.py
```

### 완료 기준

```text
UI에서 candidate/probe/commit/validation frame 확인 가능
```

---

## Sequence 10 — Regression Fixtures

### 작업

```text
[ ] simple asteroid fixture
[ ] hole asteroid fixture
[ ] narrow corridor asteroid fixture
[ ] shape/fluid mixed fixture
[ ] unreachable output fixture
[ ] existing trunk / protected corridor 스텁 fixture (비어 있지 않은 케이스)
```

### 완료 기준

```text
각 fixture에서 deterministic optimization result 생성
```

---

## Sequence 11 — Quality Gates

### 작업

```text
ruff check
black --check
mypy
targeted pytest
integration pytest
```

### 완료 기준

```text
all gates pass
```
