---
status: ARCHIVED
do_not_use_as_authority: true
archived_reason: plans/asteroid_lab_optimization snapshot — use documents/Algorithm/asteroid_lab_10_development_sequence.md
authority_for_implementation: documents/Algorithm/asteroid_lab_10_development_sequence.md
superseded_by:
  - documents/index/document_inventory.md
  - documents/ai/current_plan.md
last_reviewed: 2026-05-24
---

# Asteroid Lab Optimization — Development Sequence


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_10_development_sequence.md`](../../Algorithm/asteroid_lab_10_development_sequence.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

> **Superseded by Unified Lab Replay Timeline:** *optimization track addition·dual-track* described under **Sequence 9** etc. differs from implementation authority. Optimization replay **appends frames only to existing Lab `ReplayTrack`**; no separate `optimizationReplayFrameIndex` / `optimization-replay-json` runtime path. Authority: `rollback_baseline_lab_replay_timeline.md`. *(When plan docs `asteroid_lab_12_runtime_replay_wiring.md`, `asteroid_lab_13_replay_payload_scalability.md` are added, follow same authority — “Lab / Optimization dual-track invariant” clause is retired.)*

## Purpose

Implement GA + local pattern compiler + route feasibility based optimization layer in a safe order.

**Required:** do not split `candidate generation → immediate route probe → normal pool` as a separate “attach later” sequence. Complete in Sequence 3 one block, same as Phase 3 doc.

---

## Sequence 1A — Domain DTO contracts

Fix DTO·coordinate contracts first to keep PRs small. **hole asteroid fixture·adapter validation split to 1B.**

### Work

```text
[ ] RouteGoal / RouteGoalKind
[ ] TopologyNode / TopologyEdge / TopologyGraph (undirected contract)
[ ] OptimizationInput DTO (route_goals·topology_graph·existing_transport_cells·trunk·protected)
[ ] RouteProbeFailureReason / CandidateRejectReason / ValidationIssueCode / ValidationSeverity
[ ] EvolutionConvergenceReason / CommitConflictReason / OptimizationReplayEventType / ReservationState
[ ] RouteDomainSnapshotBuilder signature (single route_domain snapshot creation entry point)
[ ] RouteDomainCellTransition / RecoveryBudget DTO (sync with Phase 7)
[ ] GenomeDiversityMetrics / EvolutionConfig.forced_distant_mutation_period (sync with Phase 6)
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_optimization_input.py (DTO·coords·empty transport greenfield)
```

### Completion criteria

```text
[ ] Related DTO·enum importable (no cycles)
[ ] enum member names·values synced with Phase docs
[ ] all Coord in OptimizationInput·graph·goal island-local (x, y) authority
[ ] `grid_contract.neighbors4` dense 4-neighbor unit test (copy JSON X==0 included)
[ ] minimal factory possible satisfying route_goals kind·priority contract
[ ] greenfield = existing_transport_cells empty ∧ trunk·protected empty sets (no separate code path)
```

---

## Sequence 1B — Reconstruction adapter + RouteCellDomain seed builder

Connect input to actual reconstruction output; produce domain draft for Phase 4 consumption.

### Work

```text
[ ] Reconstruction → OptimizationInput adapter
[ ] rim / interior / route_goals extraction
[ ] RouteCellDomain builder draft (**RouteDomainSnapshotBuilder**; existing_transport_cells → transport_mask, trunk·protected·blocked reflected)
[ ] topology_graph neighbors consistent with grid_contract.neighbors4 (graph builder test)
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_optimization_input.py (adapter·builder section)
pytest tests/unit/shapez_asteroid/test_route_cell_domain_builder.py (filename per implementation)
```

### Completion criteria

```text
[ ] hole asteroid fixture keeps interior fill mineable
[ ] adapter produces OptimizationInput via same path for greenfield·non-greenfield
[ ] builder output consistent with blocked/hard_blocked
```

---

## Sequence 2 — Pattern Library

### Work

```text
[ ] BundlePattern DTO (attachments·throughput_factor)
[ ] linear 0~3 extension pattern
[ ] rotation support
[ ] deterministic pattern id
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_pattern_library.py
```

### Completion criteria

```text
[ ] ExtensionAttachment·throughput_factor·canonical E (output_dir=E) contract
extractor + 0~3 extension linear pattern generation
output_stub not included in occupied_cells
```

---

## Sequence 3 — Candidate Generator + Route Probe (integrated)

Candidates **must** pass probe before entering normal pool.

### Work

```text
[ ] BundleCandidate DTO (topology_signature·probe snapshot; factory-only creation; normal has no rejection fields)
[ ] CandidateGenerationResult (normal vs rejected)
[ ] CandidateEquivalenceKey + dedupe (before max_candidates)
[ ] rim-only extractor **candidate generation only** — no commit·greedy rim install
[ ] extension mineable validation
[ ] reject reason tracking (enum)
[ ] RouteProbeInput / RouteProbeResult (route_domain·RouteGoal·reached_goal·topology_graph·goal_priority_weight)
[ ] bounded uniform-cost probe + transport mask
[ ] reachable → normal pool / unreachable → diagnostic or discard
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_bundle_candidate_generator.py
pytest tests/unit/shapez_asteroid/test_route_probe.py
pytest tests/unit/shapez_asteroid/test_candidate_route_probe_integration.py
```

### Completion criteria

```text
valid and rejected candidates deterministic
unconnectable candidates do not enter normal pool
Candidate Generator does not confirm placement (pool·probe only)
output_stub reachability evaluated per RouteGoal contract
blocked / hard_blocked passage forbidden
budget exceeded failure reason recorded
```

---

## Sequence 3B — Replay minimal skeleton (recommended, early)

If candidate/probe debugging is **deferred until Sequence 8**, implementation difficulty spikes sharply. Sequence 8 owns full UI timeline; here open **recording pipeline only** at minimum.

### Work

```text
[ ] OptimizationReplayEventType + OptimizationReplayFrame serialization (Phase 9 constants MAX_REPLAY_*·replay_truncated included)
[ ] record candidate.generated / candidate.rejected / route_probe.succeeded|failed events first
[ ] unit test replay artifact forbidden as algorithm input invariant
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_optimization_replay_skeleton.py (filename per implementation)
```

### Completion criteria

```text
[ ] Sequence 3 single run writes replay NDJSON (or equivalent binary); search result identical replay on/off (Phase 9 invariant)
```

---

## Sequence 4 — Genome / Fitness

### Work

```text
[ ] Gene / Genome DTO (Gene.commit_order)
[ ] FitnessBreakdown + FitnessMetrics
[ ] overlap penalty
[ ] unreachable penalty
[ ] route cost penalty
[ ] route_fragility_penalty / shared_corridor_pressure_penalty fields (0 allowed in v0)
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_genome_fitness.py
```

### Completion criteria

```text
same input + same seed = same fitness
overlap/unreachable penalty stronger than throughput gain
trunk vs margin etc.: route goal quality reflected in score even when equally reachable
hook (penalty fields) exists where greedy high-throughput advantage can break in narrow passage scenarios
```

---

## Sequence 5 — Evolution Search v0

### Work

```text
[ ] initial population
[ ] mutation
[ ] repair
[ ] elitism
[ ] forced_distant_mutation_period (None allowed) + GenomeDiversityMetrics slot (0 allowed)
[ ] EvolutionConvergenceReason enum + EvolutionResult
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_evolutionary_search.py
```

### Completion criteria

```text
same seed deterministic (population·mutation·fitness tie-break included)
best fitness non-decreasing under elitism
best genome returned
```

---

## Sequence 6 — Incremental Commit

### Work

```text
[ ] best genome candidate ordering (**Gene.commit_order** authority; candidate generation·rim order default forbidden)
[ ] route probe re-run (updated route_domain)
[ ] RouteReservation (reservation_id·reached_goal·goal_priority·state·domain_cell_transitions)
[ ] CommitConflictReason handling
[ ] commit / rollback + route_domain reflection
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_incremental_commit.py
```

### Completion criteria

```text
confirmed candidates have exterior trunk route
failed commit candidates locally rolled back
commit order matches genome `commit_order`, not bound to generation enumeration order
```

---

## Sequence 7 — Validation

### Work

```text
[ ] final validation result
[ ] confirmed candidate ↔ exactly one CONFIRMED RouteReservation validation
[ ] reserved_cells ↔ path consistency validation
[ ] ValidationIssue (ValidationIssueCode·route_goal_kind·transport_kind·optional route_reservation_id·path_index)
[ ] extractor output connectivity check
[ ] orphan transport check
[ ] overlap check
[ ] Coord·`grid_contract.neighbors4` dense grid validation
[ ] RouteGoal·transport consistency (read-only validation only)
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_optimization_validation.py
```

### Completion criteria

```text
validation is read-only
Validation must not invent new routes.
Validation must not mutate placement.
Validation must not fix topology.
```

(Authority narrative: `documents/plans/asteroid_lab_optimization/asteroid_lab_08_validation.md` — contract (forbidden))

---

## Sequence 8 — Replay Debug (full timeline·UI)

Extend **minimal skeleton** opened in Sequence 3B to complete all events·overlays·controllers.

### Work

```text
[ ] optimization replay event (OptimizationReplayEventType)
[ ] frame serializer
[ ] route probe overlay
[ ] generation metric frame
[ ] validation frame
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_optimization_replay.py
```

### Completion criteria

```text
optimization process viewable as timeline
replay artifact not used as algorithm input
```

---

## Sequence 9 — UI Integration

### Work

```text
[ ] verify optimization phase frames append to Lab single timeline (`lab-replay-frames-data`) (no separate optimization track·index)
[ ] candidate overlay
[ ] route probe overlay
[ ] best genome overlay
[ ] validation issue overlay
```

### Tests

```text
pytest tests/integration/shapez_asteroid/test_optimization_ui_payload.py
```

### Completion criteria

```text
candidate/probe/commit/validation frames viewable in UI
```

---

## Sequence 10 — Regression Fixtures

### Work

```text
[ ] simple asteroid fixture
[ ] hole asteroid fixture
[ ] narrow corridor asteroid fixture
[ ] shape/fluid mixed fixture
[ ] unreachable output fixture
[ ] existing trunk / protected corridor stub fixture (non-empty case)
```

### Completion criteria

```text
deterministic optimization result per fixture
```

---

## Sequence 11 — Quality Gates

### Work

```text
ruff check
black --check
mypy
targeted pytest
integration pytest
```

### Completion criteria

```text
all gates pass
```
