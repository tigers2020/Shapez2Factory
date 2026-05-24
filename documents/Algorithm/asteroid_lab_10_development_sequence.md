# Asteroid Lab Optimization — Development Sequence

> **Document baseline (2026-05-18):** After **Decode → Reconstruction** in code, the optimization sequence is **not started** in documentation. The `[ ]` checklists below are reset; pytest pass counts and fixture lists are **not updated** (historical citation preserved). Lab app: `django_apps/asteroid_lab/` · parent [`README.md`](README.md).
>
> **Solver button v0:** Merge, execution contract, and PR status are canonical in [`solver_runtime/`](solver_runtime/). **Status may differ** from this document's checkboxes — [`solver_runtime/ARCHITECTURE_RECONCILIATION.md`](solver_runtime/ARCHITECTURE_RECONCILIATION.md).
>
> **RTTP Hybrid C v0.1 gate sync (2026-05-23):** Checkboxes for **Sequence 2·3·3B·6·7 (partial)** updated per `django_apps/asteroid_lab/optimization/` + `tests/unit/asteroid_lab/test_rttp_*.py`. **Sequence 4·5 (GA/evolution)** are out of v0.1 scope (uses greedy-regret `PlacementGenome`). Canonical design: [`docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md`](../../docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md). Narrow gate: `python -m pytest tests/unit/asteroid_lab/ -k rttp`.
>
> **RTTP v1 MacroBundleT3 gates (2026-05-23):** PR-A..H merged on `master` — `optimization/macros/`, `selection/macro_greedy_regret.py`, `commit/incremental_macro_commit.py`, `macro_only_mode` pipeline branch. Gates **RTTP-G9..G16** in `test_rttp_macro_bundle_t3.py`, `test_rttp_pipeline_macro_greenfield.py`, `test_rttp_replay_parity.py` (`test_macro_pipeline_replay_parity`). Spec: [`2026-05-23-rttp-v1-macrobundle-t3-design.md`](../../docs/superpowers/specs/2026-05-23-rttp-v1-macrobundle-t3-design.md).

## Purpose

Implement the GA + local pattern compiler + route feasibility optimization layer in a safe order.

**Required:** Do not split `candidate generation → immediate route probe → normal pool` into a separate "attach later" sequence. Complete it in one block as Sequence 3, same as Phase 3 documentation.

### Implementation and verification notes (archived)

- **App boundary (intent):** Lab decode, replay, and ORM live in `django_apps/asteroid_lab/`. Optimization DTOs, GA, etc. were designed as a separate package; references to `django_apps/shapez_asteroid/optimization/` in docs are **historical** (that app was removed from the repo).
- **Test and fixture listings:** pytest paths, pass counts, and JSON fixture lists in this section are **documentation archive only**; not updated in the 2026-05-18 folder cleanup. Actual verification follows code and CI.

---

## Sequence 1A — Domain DTO contracts

Fix DTO and coordinate contracts first to keep PRs small. **Hole asteroid fixture and adapter verification are split to 1B.**

### Work

```text
[ ] RouteGoal / RouteGoalKind
[ ] TopologyNode / TopologyEdge / TopologyGraph (undirected contract)
[ ] OptimizationInput DTO (route_goals·topology_graph·existing_transport_cells·trunk·protected)
[ ] RouteProbeFailureReason / CandidateRejectReason / ValidationIssueCode / ValidationSeverity
[ ] EvolutionConvergenceReason / CommitConflictReason / OptimizationReplayEventType / ReservationState
[ ] RouteDomainSnapshotBuilder signature (single route_domain snapshot entry point)
[ ] RouteDomainCellTransition / RecoveryBudget DTO (sync with Phase 7)
[ ] GenomeDiversityMetrics / EvolutionConfig.forced_distant_mutation_period (sync with Phase 6)
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_optimization_input.py (DTO·coordinates·empty transport greenfield)
```

### Completion criteria

```text
[ ] Related DTOs and enums importable (no cycles)
[ ] Enum member names and values synced with Phase docs
[ ] All Coords in OptimizationInput, graph, and goals use Server X/Y canonical form
[ ] `neighbors4` island 4-neighbor unit test (includes copy `X==0` case)
[ ] Minimal factory satisfying route_goals kind·priority contract
[ ] greenfield = existing_transport_cells empty ∧ trunk·protected empty (no separate code path)
```

---

## Sequence 1B — Reconstruction adapter + RouteCellDomain seed builder

Connect input to actual reconstruction output and build the domain draft consumed by Phase 4.

### Work

```text
[ ] Reconstruction → OptimizationInput adapter
[ ] rim / interior / route_goals extraction
[ ] RouteCellDomain builder draft (**RouteDomainSnapshotBuilder**; existing_transport_cells → transport_mask, trunk·protected·blocked)
[ ] topology_graph neighbors consistent with `neighbors4` (graph builder test)
```

### Tests

```text
pytest tests/unit/shapez_asteroid/test_optimization_input.py (adapter·builder section)
pytest tests/unit/shapez_asteroid/test_route_cell_domain_builder.py (filename per implementation)
```

### Completion criteria

```text
[ ] hole asteroid fixture keeps interior fill as mineable
[ ] adapter produces OptimizationInput via same path for greenfield and non-greenfield
[ ] builder output consistent with blocked/hard_blocked
```

---

## Sequence 2 — Pattern Library

> **RTTP v0.1 (merged):** `optimization/candidates/pattern_library.py` — no dedicated `test_pattern_library.py`; `test_rttp_candidate_generator.py`·`test_rttp_greedy_regret.py` gate consumption contract.

### Work

```text
[x] BundlePattern DTO (attachments·throughput_factor)
[x] linear 0~3 extension pattern
[x] rotation support (N/E/S/W)
[x] deterministic pattern id
```

### Tests

```text
python -m pytest tests/unit/asteroid_lab/test_rttp_candidate_generator.py tests/unit/asteroid_lab/test_rttp_greedy_regret.py -v
```

### Completion criteria

```text
[x] throughput_factor 4/8/12/16 · canonical E rotation (`build_pattern_library`)
[x] extractor + 0~3 extension linear pattern generation
[x] output_stub separate occupied cell (generator/probe path)
```

---

## Sequence 3 — Candidate Generator + Route Probe (integrated)

Candidates **must** pass probe before entering the normal pool.

> **RTTP v0.1 (merged):** `candidate_generator.py` + `routing/route_probe.py` + `lift_lane_domain` / `route_goals`.

### Work

```text
[x] BundleCandidate DTO (topology_signature·probe snapshot)
[x] CandidateGenerationResult (normal vs rejected)
[x] CandidateEquivalenceKey + dedupe (`selection/equivalence.py`; selection stage)
[x] INTERIOR_AND_RIM anchor ∈ rim ∪ inner (v0.1 default policy)
[x] extension mineable validation (generator)
[x] reject reason tracking (`CandidateRejectReason` StrEnum)
[x] RouteProbeResult (bounded BFS; lift + trunk mask)
[x] reachable → normal pool / unreachable → rejected
```

### Tests

```text
python -m pytest tests/unit/asteroid_lab/test_rttp_candidate_generator.py tests/unit/asteroid_lab/test_rttp_lift_lane_domain.py tests/unit/asteroid_lab/test_rttp_route_goals.py -v
```

### Completion criteria

```text
[x] unreachable → rejected (`test_interior_and_rim_unreachable_goes_to_rejected`)
[x] generator does not commit (`test_candidate_generator_does_not_commit`)
[x] reachable in normal pool (`test_reachable_candidate_in_normal_pool`)
[x] lift edge + trunk mask (`test_lift_edge_connects_stub_to_trunk_mask`)
[x] ring ports in probe goals (`test_probe_goal_coords_include_ring_ports`)
[ ] topology_graph·goal_priority_weight (legacy Phase doc; not implemented in v0.1)
[ ] dedicated budget exceeded failure reason test (not added)
```

---

## Sequence 3B — Replay minimal skeleton (recommended, early)

Deferring candidate/probe debugging **until Sequence 8** sharply increases implementation difficulty. Sequence 8 owns the full UI timeline; here only the **recording pipeline** is opened minimally.

> **RTTP v0.2 + 3B-S (merged, 2026-05-23):** Four milestones on **`{run_key}:rttp`**; Lab **`lab_replay_frames_json`** = inspection/reconstruction + **interleaved full-snapshot RTTP** (`lab_rttp_snapshot_compose`). Contracts: [`2026-05-23-rttp-v0.2-replay-parity-design.md`](../../docs/superpowers/specs/2026-05-23-rttp-v0.2-replay-parity-design.md), [`2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md`](../../docs/superpowers/specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md).

### Work

```text
[x] canonical `rttp.*` milestone event types (four snapshots)
[x] pipeline records four milestones + cell overlays (`rttp_replay_diagnostics`)
[x] replay on/off `PipelineResult` parity (G8 v0.2)
[x] replay sink not algorithm input; layers do not accept sink
[x] DbRttpReplaySink + solver entry persistence (integration)
[x] Lab product timeline interleave (3B-S; no inherited_snapshot)
```

### Tests

```text
python -m pytest tests/unit/asteroid_lab/test_rttp_replay_parity.py tests/unit/asteroid_lab/test_rttp_replay_sink.py tests/unit/asteroid_lab/test_rttp_db_replay_sink.py tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py -v
```

### Completion criteria

```text
[x] replay on/off same candidate/commit ids (`test_rttp_replay_on_off_parity`)
[x] four milestone events + descriptions/overlays
[ ] full Phase 9 event matrix (candidate.rejected per-frame, etc.) — v0.1 partial only
```

---

## Sequence 4 — Genome / Fitness

> **RTTP v0.1: out of scope.** Hybrid C Layer 3 uses **greedy-regret `PlacementGenome`** (`test_rttp_greedy_regret.py`). GA `Gene`/`FitnessBreakdown` sequence is v1 or a separate evolution track.

### Work

```text
[ ] Gene / Genome DTO (Gene.commit_order) — legacy GA track
[ ] FitnessBreakdown + FitnessMetrics
[ ] overlap penalty
[ ] unreachable penalty
[ ] route cost penalty
[ ] route_fragility_penalty / shared_corridor_pressure_penalty fields (0 allowed in v0)
```

### Tests

```text
# v0.1 alternate gate:
python -m pytest tests/unit/asteroid_lab/test_rttp_greedy_regret.py -v
```

### Completion criteria

```text
[x] explicit commit_order ≠ rim scan (`test_commit_order_is_explicit_not_rim_scan`) — RTTP v0.1
[x] regret/scarcity ordering (`test_regret_prefers_high_scarcity_candidate`) — RTTP v0.1
[ ] GA fitness same seed deterministic — not started
```

---

## Sequence 5 — Evolution Search v0

> **RTTP v0.1: out of scope** (MacroBundle / dense interior / GA evolution — [`rttp-hybrid-c-layout-design.md`](../../docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md) § v1).

### Work

```text
[ ] initial population
[ ] mutation
[ ] repair
[ ] elitism
[ ] forced_distant_mutation_period (None allowed) + GenomeDiversityMetrics placeholder (0 allowed)
[ ] EvolutionConvergenceReason enum + EvolutionResult
```

### Tests

```text
# (not started — v0.1 is single-pass greedy-regret + LNS only)
```

### Completion criteria

```text
[ ] (not started)
```

---

## Sequence 6 — Incremental Commit

> **RTTP v0.1 (merged):** `commit/incremental_commit.py` + bounded `local_lns.py`. Regression: `test_rttp_narrow_corridor.py` (probe≠commit, protected bridge).

### Work

```text
[x] PlacementGenome commit_order (greedy-regret; explicit order)
[x] route probe re-run at commit (`domain.version` increments)
[x] CommitConflictReason StrEnum (incl. INLET_ON_SHARED_TRANSPORT, REPROBE_FAILED, HARD_PROTECTED_CONFLICT)
[x] incremental commit + reservation merge into trunk mask
[x] local LNS after commit failure only
```

### Tests

```text
python -m pytest tests/unit/asteroid_lab/test_rttp_commit.py tests/unit/asteroid_lab/test_rttp_lns.py tests/unit/asteroid_lab/test_rttp_narrow_corridor.py tests/unit/asteroid_lab/test_rttp_greedy_regret.py -v
```

### Completion criteria

```text
[x] inlet on shared transport rejects (`test_commit_rejects_inlet_on_shared_transport`)
[x] commit reprobes domain (`test_commit_reprobes_latest_domain`)
[x] probe reachable ≠ commit success (`test_narrow_corridor_probe_vs_commit_regression`)
[x] protected corridor → HARD_PROTECTED_CONFLICT (`test_narrow_corridor_protected_bridge_regression`)
[x] commit_order explicit (`test_commit_order_is_explicit_not_rim_scan`)
[ ] RouteReservation DTO (all legacy Phase 7 fields) — v0.1 simplified
```

---

## Sequence 7 — Validation

> **RTTP v0.1 (partial):** `validation/final_validation.py` read-only asserts; pipeline `validation_passed`. Full `ValidationIssue` matrix not implemented.

### Work

```text
[x] final validation read-only (`validate_final_layout`)
[x] overlap / mineable subset / reserved route checks (minimal)
[ ] ValidationIssue enum + per-issue reporting (legacy Phase 8)
[ ] orphan transport / full connectivity matrix
```

### Tests

```text
python -m pytest tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py tests/unit/asteroid_lab/test_rttp_reconstruction_fixture_e2e.py tests/unit/asteroid_lab/test_rttp_existing_trunk.py -v
```

### Completion criteria

```text
[x] validation read-only (no repair imports in validation module)
[x] pipeline reports validation_passed on green paths (E2E tests)
[ ] Validation must not invent routes / mutate placement — module-level; no dedicated negative suite
```

(Canonical description: `documents/plans/asteroid_lab_optimization/asteroid_lab_08_validation.md` — contract (forbidden))

---

## Sequence 8 — Replay Debug (full timeline·UI)

Extend the **minimal skeleton** opened in Sequence 3B to complete all events, overlays, and controllers.

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
[ ] optimization process viewable as timeline
[ ] replay artifact is not used as algorithm input
```

---

## Sequence 9 — UI Integration

### Work

```text
[ ] add optimization track to replay controller
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
[ ] candidate/probe/commit/validation frames visible in UI
```

---

## Sequence 10 — Regression Fixtures

> **Status (2026-05-18 reset):** Checklists below are **not started**. Sentences that read as "complete·reflected" are archive-only; pytest and fixture paths were not updated. Lab UI `10A–10F` numbering and this `Sequence 10` are **different layers**.

### Work

```text
[ ] simple asteroid fixture
[ ] hole asteroid fixture
[ ] narrow corridor asteroid fixture — test helper based narrow bridge
[ ] shape/fluid mixed fixture
[ ] unreachable output fixture
[ ] existing trunk / protected corridor stub fixture
```

### 10A reference list (archived)

```text
[ ] 3-cell narrow bridge OptimizationInput builder
[ ] dual-goal symmetric narrow bridge builder (`build_symmetric_narrow_bridge_optimization_input`)
[ ] rim competition candidate pool
[ ] candidate probe reachable → commit-time reprobe failure regression
[ ] shared bridge rollback regression
[ ] shape/fluid transport conflict regression
[ ] protected ∩ existing trunk seed-domain precedence regression
[ ] replay event order deterministic regression
[ ] targeted pytest / ruff / mypy green
```

### Remaining scope

```text
[ ] JSON fixture under tests/fixtures/shapez_asteroid/optimization/ (narrow corridor asymmetric + symmetric rim competition v0)
[ ] same seed → same best genome on full narrow evolution run
```

### Sequence 10B — Commit Survivability Metrics v0 (under Regression Fixtures; not Lab UI 10B)

> **Status:** Contract and observability goals documented only. Implementation and fixtures are **not started** (checklist reset).

**Spec draft (v0):**

- `PenaltyMode.OFF` / `PenaltyMode.CONSERVATIVE`
- `CommitSurvivabilityMetrics` contract and `summarize_incremental_commit`
- JSON-safe replay metrics adapter
- `COMMIT_SURVIVABILITY_SUMMARY` replay frame
- Conservative mode minimum heuristics for `route_fragility` / `shared_corridor_pressure` (includes dual-path logic based on `route_domain` presence)
- narrow bridge penalty off/on comparison · targeted pytest / ruff / scoped mypy green

**Remaining scope (expansion):**

- reservation accumulation fixture
- corridor starvation replay fixture
- late-generation unreachable fixture
- penalty stitching between evolution fitness snapshot and commit summary frame
- global quality gates (see `## Sequence 11`)

#### Metrics contract

- **Post-commit (observation only):** `CommitSurvivabilityMetrics` — `commit_attempt_count`, `commit_confirmed_count`, `commit_rolled_back_count`, `commit_success_ratio`, `rollback_reason_counts` (enum value keys), `route_probe_failed_count`, `transport_kind_conflict_count`. **Forbidden** as evolution search input.
- **Pre-commit (fitness):** `PenaltyMode.OFF` / `PenaltyMode.CONSERVATIVE`. Conservative mode applies deterministic heuristics only to `route_fragility_penalty`·`shared_corridor_pressure_penalty`; other breakdown slots may remain 0 as in v0.
- **CONSERVATIVE:** Deterministic **local** heuristic; **not** a global commit success predictor.

#### Replay

- `OptimizationReplayEventType.COMMIT_SURVIVABILITY_SUMMARY` — scalar·JSON-safe `rollback_reason_counts`; **forbidden** as solver/GA input.
- In **commit-only** summary frames, `route_fragility_penalty` / `shared_corridor_pressure_penalty` are **0.0 placeholders** — meaning **this frame does not own the fitness breakdown**, not "no penalty". Values may be filled only when evolution+commit stitching exists.

#### Tests

- Paths and case names are **documentation archive only**. Actual test tree and verification follow code and CI.

---

## Sequence 11 — Quality Gates

### Work

```text
[ ] ruff check .
[ ] black --check .
[ ] mypy .
[ ] targeted pytest
[ ] integration pytest
```

### Completion criteria

```text
[ ] all gates pass (ruff / black / mypy / pytest — specific pass counts out of doc update scope)
```

> **Note:** Records of past local green runs are **archive only**. The 2026-05-18 folder cleanup did not update pytest·pass counts·paths.

> **Note (after 12E):** POST·persist paths follow code and CI. Full-repo gates are tracked under `### Known debt (global gates)` below.

---

## Asteroid Lab — Run Solver POST · optimization replay persistence (sequences 12C–12H)

After Lab **inspection (decode) replay** succeeds, run **POST synchronous** bounded GA in the same request and merge optimization replay frames into `SolverRun.config_json`. Attach must run **before** placing the inspection bundle in the Lab response JSON so the same response includes the optimization track (`django_apps/web/views/public_pages.py`, `django_apps/web/services/asteroid_lab_post_inspection_evolution.py`). `replay_pipeline_service` maintains the boundary of not importing `shapez_asteroid`.

### Progress table (12C–12H)

| Sequence | Status | Summary |
|--------|------|------|
| 12C | Not started | `optimization_replay_persist` — record frames to `SolverRun.config_json` only after successful inspection replay build (output-only) |
| 12D | Not started | Post-inspection evolution + attach immediately after inspection replay `ok` for synchronous UI optimization track |
| 12E | Not started | POST-only hard caps (`max_candidates`, `route_probe_max_expansions`, `time_budget_ms`, `population_size`, etc.), `empty_candidate_pool` / `evolution_failed` separation, JSON `optimization_replay_attach` `{attached, reason}`, `_finalize_attach` INFO log, `event_type`·prefix smoke and attach contract integration tests |
| 12F | Not started | Persist frame list guard: `validate_optimization_replay_frame_list_payload` + truncation pair·continuous `frame_index`·known `event_type` on deserialize; malformed → read empty track·write skip (`invalid_replay_payload`); `build_optimization_replay_track_payload` aggregates first `truncation_reason` on truncation; schema/truncation **sibling·envelope·cap·migration** out of scope (canonical: `asteroid_lab_12_runtime_replay_wiring.md`) |
| 12G | Not started | Read failure → empty track + `metrics.optimization_replay_diagnostic_reason` only (`optimization_ui_payload` classification + `optimization_replay_payload_for_project`); key absent on normal payload; solver·replay semantics·schema/truncation sibling unchanged (canonical: `asteroid_lab_12_runtime_replay_wiring.md` §7) |
| 12H | Not started | Optimization replay panel HUD: display-only `replay_truncated` / `truncation_reason` / `optimization_replay_diagnostic_reason` (`asteroid_miner_layout_solver.html` SSR + `asteroid_miner_layout_lab.js`); no replay semantics·Lab timeline control·implicit sync |

### 12E implementation summary

- **Response latency:** Synchronous upper bound on POST inline GA (v0 prioritizes response stability).
- **Observability:** On skip/failure, UI·tests·logs share the same vocabulary via `optimization_replay_attach.reason`. (Semantically `empty_candidate_pool` is closer to orchestration result and `empty_frames` to attach result; v1 may split types but 12E keeps both in single `OptimizationReplayAttachReason`.)
- **Verification:** Per code·CI (pytest sections not listed in doc).

### Known debt (global gates)

Full-repo lint·type·test gates may vary with environment and drift. This section is **for tracking**; pass counts and dates were not updated in the 2026-05-18 doc cleanup.

---

## Sequence 13 — Replay payload scalability (roadmap, implementation gate)

**Canonical:** [`asteroid_lab_13_replay_payload_scalability.md`](asteroid_lab_13_replay_payload_scalability.md)  
Instrumentation·13A·13B history: [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md) · **Product replay:** [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md) (single replay timeline; dual-track **deprecated**). Lab/optimization **attribution** names in 13A·13B are historical labels from instrumentation time.

| Sub | Status | Summary |
|------|------|------|
| 13A | Not started | Top-level JSON section instrumentation, optimization replay hard cap regression, HAR evidence |
| 13B | Not started | Lab replay attribution·`largest_lab_frames`·redundancy, Lab uncapped gap documentation |
| 13C | **Awaiting approval** | Full Lab replay **lazy-load endpoint** (preferred first implementation); semantic equivalence with inline |
| 13D | Roadmap | UI lazy-load·loading/error·ownership preservation·inline fallback allowed |
| 13E | Roadmap | Delta prototype — when lazy-load insufficient, reconstruction equivalence tests required |
| 13F | Roadmap | Cell interning — after redundancy evidence, render·lookup equivalence |
| 13G | Roadmap | gzip/Brotli transport — must not replace semantic work |

**Forbidden (doc stage):** Response contract·JS loading·delta full implementation·solver semantics preemptive changes. 13C implementation **after explicit approval**.

---

## Asteroid Lab — Optimization replay UI (sequences 10A–10F) — **migration target**

> **2026-05-19:** Product canonical is [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md). 10A–10F·11A–11B below (dual-track·separate optimization controller·HUD-only) are **obsolete**. New work follows **Phase 9 sequences 9A–9H**. **9E** (product replay = `lab_replay_frames_json` single timeline, feature flag·Optimization Replay panel removal) completed 2026-05-19.

**Numbering note:** `10A–10F` below are Lab page **optimization replay UI** progress numbers (historical). Not the same "10" layer as `## Sequence 10 — Regression Fixtures` at the top of this document.

<details>
<summary>Deprecated historical: sequences 10A–11B (dual-track·separate optimization controller) — expand</summary>

### Progress table (10A–10F)

| Sequence | Status | Summary |
|--------|------|------|
| 10A | Not started | parse-only — optimization replay JSON parsing only |
| 10B | Not started | metadata summary — summary metadata display |
| 10C | Not started | summary panel — summary panel UI |
| 10D | Not started | selected frame metadata — selected frame metadata |
| 10E | Not started | independent metadata navigation — clamp·update `optimizationReplayFrameIndex` only, Lab replay timeline untouched |
| 10F | Not started | dual-track sync policy document — dual-track·desync contract documented in `asteroid_lab_09_replay_debug.md` |

### Future (overlay·sync)

| Sequence | Status | Summary |
|--------|------|------|
| 11A | Not started | readonly overlay projection — `projectOptimizationReplayFrameToLabOverlay(frame)` → `{ cells, diagnostics }`; Lab/optimization index·Lab payload unchanged; bbox from `metrics` only |
| 11B | Not started | overlay rendering — **no env flag** (not implemented); 11A projection + separate `#lab-optimization-overlay-layer`; Lab cell DOM·payload immutable·index desync preserved. Register canonical name in [`environment.md`](../ai/manuals/environment.md) on implementation |
| 11C | Not started | frame sync policy — review explicit sync policy **only when needed** (default desync, see `09` canonical) |

#### 11B completion criteria (summary)

```text
[ ] Document Sequence 11B policy (flag·separate layer·forbidden) in asteroid_lab_09
[ ] Template: lab-optimization-overlay-layer / lab-optimization-overlay-diagnostics
[ ] asteroid_miner_layout_lab.js: flag, clear/render, grid style synced with Lab grid, panel·applyFrame·zoom hooks
[ ] test_asteroid_lab_page_context.py 11B static contract test
```

#### 11A completion criteria (summary)

```text
[ ] Document Sequence 11A contract (I/O·forbidden·bbox·drop) in asteroid_lab_09
[ ] Implement projectOptimizationReplayFrameToLabOverlay in asteroid_miner_layout_lab.js (no render/DOM/index sync)
[ ] 11A static contract test in test_asteroid_lab_page_context.py
```

</details>
