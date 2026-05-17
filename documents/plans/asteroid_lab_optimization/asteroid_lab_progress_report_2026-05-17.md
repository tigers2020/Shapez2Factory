---
status: REPORT
owner: solver-architecture
last_reviewed: 2026-05-17
branch_baseline: quality/repository-gate-cleanup
supersedes: []
superseded_by:
related_epics:
  - asteroid_lab_optimization
---

# Asteroid Lab / Optimization Layer 개발 진행 보고서

**역할**: Principal Solver System Architect

**기준 시점**: 2026-05-17

**브랜치 기준**: `quality/repository-gate-cleanup`

> 본 문서는 관측·진행 요약(REPORT)이다. 구현 계약의 정본은 각 시퀀스 CANON/ACTIVE 플랜과 코드·테스트를 우선한다.

---

## 1. 프로젝트 개요

### 목표

Asteroid Lab은 Shapez 2 asteroid mining 문제를 대상으로, 아래 전체 흐름을 통합하는 연구·실험용 optimization platform으로 개발 중이다.

```text
Decode
→ Reconstruction
→ Candidate Expansion
→ Route Feasibility
→ Evolutionary Optimization
→ Incremental Commit
→ Validation
→ Replay Visualization
```

---

## 2. 핵심 아키텍처 원칙

현재 구현은 아래 철학을 기준으로 고정되어 있다.

### 2.1 Placement ≠ Commit

핵심 원칙:

```text
Everything is provisional until connected to exterior trunk.
```

즉:

```text
candidate 생성
!=
실제 확정 배치
```

### 2.2 Routing-later 구조 금지

기존 v1/v2의 문제였던:

```text
placement first
routing later
```

구조를 폐기했다. 현재는:

```text
candidate generation
+
immediate route feasibility probe
```

를 강제한다.

### 2.3 Replay is output only

Replay / NDJSON / artifact는:

```text
디버그·출력 전용
```

이며 solver 입력으로 사용하지 않는다.

---

## 3. 완료된 핵심 시스템

### Sequence 1A–1B: Domain / Optimization Input / Route Domain

**완료 요약**

- **DTO·Enum 고정**: `RouteGoal`, `TopologyGraph`, `OptimizationInput`, `RouteProbeFailureReason`, `CandidateRejectReason`, `ValidationIssueCode`, `CommitConflictReason`, `OptimizationReplayEventType`, `ReservationState` 등 핵심 계약을 enum 기반으로 고정.
- **Server Dense Grid 정본화**: 최적화 계층 전체는 `Coord = Server X/Y`만 사용한다. 즉 `..., -1, 0, 1, ...` 밀집 좌표계를 정본으로 사용.
- **RouteDomainSnapshotBuilder 도입**: `route_domain`의 단일 생성 책임을 `RouteDomainSnapshotBuilder`로 고정하여 candidate / probe / commit / validation 간 drift를 줄였다.

### Sequence 2: Pattern Library

**완료 요약**

- Linear extractor-extension 패턴 생성기: `extractor only`, `+1 extension`, `+2 extension`, `+3 extension`, 4방향 회전 지원.
- **Throughput 계약**: `x4`, `x8`, `x12`, `x16`을 extension 개수와 deterministic하게 연결.

### Sequence 3: Candidate Generator + Route Probe

**완료 요약**

- **Bundle-level candidate 구조**: Cell-level GA를 금지하고 `gene = placement bundle` 구조 채택.
- **CandidateEquivalenceKey**: 후보 폭발 방지를 위한 deterministic dedupe.
- **Immediate route feasibility**: Candidate 생성 직후 bounded uniform-cost probe 실행. unreachable candidate는 normal pool에 진입하지 않음.
- **RouteGoal 기반 탐색**: 단순 external cell이 아니라 `RouteGoalKind`, priority, transport kind 계약 기반 탐색.

### Sequence 4: Genome / Fitness

**완료 요약**

- **Genome 구조**: `Gene(candidate_id)`, `Genome(tuple[Gene])`.
- **FitnessBreakdown**: extractor score, extension score, route penalty, overlap penalty, corridor pressure, fragility penalty 등 세분화.
- **핵심 penalty**: overlap penalty, unreachable penalty가 throughput gain보다 강하도록 고정.

### Sequence 5: Evolutionary Search

**완료 요약**

- **Mutation-only v0**: mutation, repair, elitism 중심.
- **Deterministic evolution**: 동일 seed에서 동일 결과를 보장하도록 tie-break 및 sort key 고정.

### Sequence 6: Incremental Commit

**완료 요약**

- **Commit-time reprobe**: candidate 단계 reachable이라도 commit 시점 최신 `route_domain`으로 항상 재-probe.
- **RouteReservation**: `reservation_id`, path, `reserved_cells`, `reached_goal`, `goal_priority`, domain transitions.
- **Local rollback**: commit 실패 시 failed candidate만 rollback.

### Sequence 7: Validation

**완료 요약**

- Validation은 **read-only assert gate**로 구현.
- **금지**: 새 route 생성, placement 수정, topology 수정.

### Sequence 8–9: Replay / UI Integration

**완료 요약**

- **Optimization replay 이벤트**: `candidate.generated`, `route_probe.succeeded`, `genome.evaluated`, `route.committed`, `validation.completed`.
- **Dual-track replay 정책**: Lab replay ≠ Optimization replay. 암묵적 sync 금지.
- **Overlay projection**(Sequence 11A–11B): readonly overlay projection 및 overlay rendering.

### Sequence 12C–12E: POST Runtime Optimization Replay Persist

**완료 요약**

- Run Solver POST 이후: inspection replay → bounded GA → optimization replay attach 동기 흐름.
- **하드캡**: `max_candidates`, `route_probe_max_expansions`, `population_size`, `time_budget_ms` 등 상한 적용.

### Sequence 12H–12I: Optimization Replay HUD Hardening

**12H**

- HUD: Replay status, Truncation reason, Diagnostic reason. SSR + runtime replace 경로 모두 지원.

**12I**

- Vocabulary hardening: `status` / `reason` / `diagnostic` 3축 분리.
- const 기반 어휘 고정: `OPTIMIZATION_REPLAY_HUD_STATUS`, `OPTIMIZATION_REPLAY_HUD_REASON`, `OPTIMIZATION_REPLAY_DIAGNOSTIC_CODE`.
- **malformed matrix**: M1–M5 malformed replay contract 테스트 추가.
- **persist roundtrip**: persist → deserialize → `replaceOptimizationReplayPayload` → HUD 표시 보존 테스트 추가.

---

## 4. 테스트 현황

### 타깃 테스트

최근 12I-impl 기준:

```text
154 passed
```

### 포함 범위(예시)

- `test_asteroid_lab_page_context.py`
- `test_asteroid_miner_layout_solver.py`
- `test_optimization_replay_persist.py`

---

## 5. 현재 남은 리스크

### 5.1 Narrow corridor starvation

다음에 대한 fixture가 완전히 닫히지 않았다.

- shared corridor pressure
- late commit unreachable
- future expansion blockage

### 5.2 Replay scale growth

현재 replay는 full snapshot 기반이다. 활성 셀 증가 시 payload pressure, DOM pressure, memory growth 대응이 필요하다.

### 5.3 Full repository gate debt

전 저장소 `ruff` / `black` / `mypy` 전부 green 상태는 아직 아니다.

---

## 6. 현재 권장 다음 우선순위

1. **Sequence 10A**: narrow corridor regression fixtures
2. **Sequence 10B**: route fragility regression pack
3. **Sequence 14A**: repository gate cleanup

---

## 7. 최종 결론

현재 Asteroid Lab optimization layer는 DTO, candidate generation, route feasibility, evolutionary search, incremental commit, validation, optimization replay, dual-track UI, runtime replay persist, HUD hardening까지 구현된 상태로 보고한다.

가장 큰 구조 변화는 기존 v1/v2의 `placement first` + `routing later`를 제거하고, `candidate generation` + `immediate route feasibility` + `commit-time reprobe`로 전환한 것이다.
