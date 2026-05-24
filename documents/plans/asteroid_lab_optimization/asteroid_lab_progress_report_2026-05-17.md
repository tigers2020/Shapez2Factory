---
status: REPORT
owner: solver-architecture
last_reviewed: 2026-05-24
do_not_use_as_authority: true
branch_baseline: quality/repository-gate-cleanup
supersedes: []
superseded_by:
  - documents/ai/current_plan.md
  - documents/index/document_inventory.md
related_epics:
  - asteroid_lab_optimization
---

# Asteroid Lab / Optimization Layer Development Progress Report

> **Plans snapshot (REPORT, 2026-05-17):** Historical progress only. Coordinate canon: [`documents/Algorithm/asteroid_lab_00_overview.md`](../../Algorithm/asteroid_lab_00_overview.md). **PR-F (2026-05):** dense server coords removed; do not treat “Server Dense Grid” statements below as current.

**Role**: Principal Solver System Architect

**As-of**: 2026-05-17

**Branch baseline**: `quality/repository-gate-cleanup`

> This document is observation·progress summary (REPORT). Implementation contract authority prioritizes each sequence CANON/ACTIVE plan and code·tests.

---

## 1. Project overview

### Goal

Asteroid Lab is under development as a research·experiment optimization platform integrating the full flow below for Shapez 2 asteroid mining problems.

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

## 2. Core architecture principles

Current implementation is fixed to the philosophy below.

### 2.1 Placement ≠ Commit

Core principle:

```text
Everything is provisional until connected to exterior trunk.
```

That is:

```text
candidate generation
!=
actual confirmed placement
```

### 2.2 Routing-later structure forbidden

Discarded v1/v2 problem:

```text
placement first
routing later
```

Current enforcement:

```text
candidate generation
+
immediate route feasibility probe
```

### 2.3 Replay is output only

Replay / NDJSON / artifact:

```text
debug·output only
```

Not used as solver input.

---

## 3. Completed core systems

### Sequence 1A–1B: Domain / Optimization Input / Route Domain

**Completion summary**

- **DTO·Enum fixed**: core contracts such as `RouteGoal`, `TopologyGraph`, `OptimizationInput`, `RouteProbeFailureReason`, `CandidateRejectReason`, `ValidationIssueCode`, `CommitConflictReason`, `OptimizationReplayEventType`, `ReservationState` fixed enum-based.
- **Island map grid (historical note, PR-F):** was Server Dense; now `CoordFrame.ISLAND_RAW`.
- **RouteDomainSnapshotBuilder introduced**: fixed single ownership of `route_domain` creation to `RouteDomainSnapshotBuilder`, reducing drift between candidate / probe / commit / validation.

### Sequence 2: Pattern Library

**Completion summary**

- Linear extractor-extension pattern generator: `extractor only`, `+1 extension`, `+2 extension`, `+3 extension`, 4-direction rotation support.
- **Throughput contract**: `x4`, `x8`, `x12`, `x16` deterministically linked to extension count.

### Sequence 3: Candidate Generator + Route Probe

**Completion summary**

- **Bundle-level candidate structure**: forbid cell-level GA; adopt `gene = placement bundle` structure.
- **CandidateEquivalenceKey**: deterministic dedupe to prevent candidate explosion.
- **Immediate route feasibility**: bounded uniform-cost probe immediately after candidate generation. unreachable candidates do not enter normal pool.
- **RouteGoal-based search**: search per `RouteGoalKind`, priority, transport kind contract, not simple external cell.

### Sequence 4: Genome / Fitness

**Completion summary**

- **Genome structure**: `Gene(candidate_id)`, `Genome(tuple[Gene])`.
- **FitnessBreakdown**: extractor score, extension score, route penalty, overlap penalty, corridor pressure, fragility penalty etc. subdivided.
- **Core penalties**: overlap penalty, unreachable penalty fixed stronger than throughput gain.

### Sequence 5: Evolutionary Search

**Completion summary**

- **Mutation-only v0**: mutation, repair, elitism centered.
- **Deterministic evolution**: tie-break and sort key fixed for same result on same seed.

### Sequence 6: Incremental Commit

**Completion summary**

- **Commit-time reprobe**: even if reachable at candidate stage, always re-probe with latest `route_domain` at commit.
- **RouteReservation**: `reservation_id`, path, `reserved_cells`, `reached_goal`, `goal_priority`, domain transitions.
- **Local rollback**: on commit failure, rollback failed candidate only.

### Sequence 7: Validation

**Completion summary**

- Validation implemented as **read-only assert gate**.
- **Forbidden**: new route creation, placement modification, topology modification.

### Sequence 8–9: Replay / UI Integration

**Completion summary**

- **Optimization replay events**: `candidate.generated`, `route_probe.succeeded`, `genome.evaluated`, `route.committed`, `validation.completed`.
- **Dual-track replay policy**: Lab replay ≠ Optimization replay. implicit sync forbidden.
- **Overlay projection**(Sequence 11A–11B): readonly overlay projection and overlay rendering.

### Sequence 12C–12E: POST Runtime Optimization Replay Persist

**Completion summary**

- After Run Solver POST: inspection replay → bounded GA → optimization replay attach synchronous flow.
- **Hard caps**: `max_candidates`, `route_probe_max_expansions`, `population_size`, `time_budget_ms` etc. applied.

### Sequence 12H–12I: Optimization Replay HUD Hardening

**12H**

- HUD: Replay status, Truncation reason, Diagnostic reason. SSR + runtime replace paths both supported.

**12I**

- Vocabulary hardening: `status` / `reason` / `diagnostic` 3-axis separation.
- const-based vocabulary fixed: `OPTIMIZATION_REPLAY_HUD_STATUS`, `OPTIMIZATION_REPLAY_HUD_REASON`, `OPTIMIZATION_REPLAY_DIAGNOSTIC_CODE`.
- **malformed matrix**: M1–M5 malformed replay contract tests added.
- **persist roundtrip**: persist → deserialize → `replaceOptimizationReplayPayload` → HUD display preservation tests added.

---

## 4. Test status

### Target tests

Recent 12I-impl baseline:

```text
154 passed
```

### Included scope (examples)

- `test_asteroid_lab_page_context.py`
- `test_asteroid_miner_layout_solver.py`
- `test_optimization_replay_persist.py`

---

## 5. Remaining risks

### 5.1 Narrow corridor starvation

Fixtures not fully closed for:

- shared corridor pressure
- late commit unreachable
- future expansion blockage

### 5.2 Replay scale growth

Current replay is full snapshot based. Active cell growth needs payload pressure, DOM pressure, memory growth mitigation.

### 5.3 Full repository gate debt

Full-repo `ruff` / `black` / `mypy` all green not yet achieved.

---

## 6. Recommended next priorities

1. **Sequence 10A**: narrow corridor regression fixtures
2. **Sequence 10B**: route fragility regression pack
3. **Sequence 14A**: repository gate cleanup

---

## 7. Final conclusion

This report states Asteroid Lab optimization layer has implemented DTO, candidate generation, route feasibility, evolutionary search, incremental commit, validation, optimization replay, dual-track UI, runtime replay persist, HUD hardening.

Largest structural change: removed v1/v2 `placement first` + `routing later`, transitioned to `candidate generation` + `immediate route feasibility` + `commit-time reprobe`.
