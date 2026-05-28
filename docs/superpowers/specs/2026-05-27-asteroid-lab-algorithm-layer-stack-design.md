# Asteroid Lab — Algorithm Layer Stack — Design Spec

**Document type:** Architecture / runtime contract (post-decontamination greenfield stack)  
**Status:** **APPROVED (spec + plan patched 2026-05-27)** — ready for PR-1 execution  
**Implementation plan:** [`2026-05-27-asteroid-lab-algorithm-layer-stack.md`](../plans/2026-05-27-asteroid-lab-algorithm-layer-stack.md) (plan review patches applied)  
**Work classification:** contract change · documentation change · (follow-up) implementation change · refactoring (package layout)  
**Scope:** `django_apps/asteroid_lab/` — **`shapez_solver` and recipe-graph UI are OUT OF SCOPE**  
**Supersedes (for layer numbering only):** informal RTTP “Layer N” labels in frozen specs — see §6  
**Extends (does not replace):** [`2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`](2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md) · [`2026-05-26-reconstruction-complete-map-dto-design.md`](2026-05-26-reconstruction-complete-map-dto-design.md)

**Korean title (reference):** Asteroid Lab 알고리즘 Layer 스택 (L1 complete-map · L2–L5 · L6 deferred)

---

## Approval record (2026-05-27)

```text
§1–§6 APPROVED WITH AMENDMENTS + CONTRACT PATCHES (Solver Architecture Review Lead).

- Adopt Option 3: L1 labeled layer_01_reconstruction (facade); implementation stays in reconstruction/.
- L2–L5 under asteroid_lab/layers/ only — placement_stack forbidden (docs + AST gate).
- L2–L5 cumulative 60s owned solely by stack_runner; per-layer remaining_budget_ms only.
- Timeout: fail-closed + non-resumable diagnostic snapshots only.
- L2 ExteriorConnectionPlan minimum DTO + A vs C throughput fields.
- L3/L4 normal pool: route-probed SUCCEEDED only (typed).
- L5 internal subphases L5a commit, L5b validation (no route probe), L5c summary projection.
- L6 deferred — not registered in stack_runner.
```

---

## §1 — Layer table (normative)

| Layer | Slug | Package path | Primary outputs | Time budget |
|-------|------|--------------|-----------------|-------------|
| **1** | `layer_01_reconstruction` | `reconstruction/` (implementation) + `layers/layer_01_reconstruction/` (facade) | `Layer01ReconstructionOutput` | Outside L2–L5 60s cap |
| **2** | `layer_02_exterior_transport` | `layers/layer_02_exterior_transport/` | `ExteriorConnectionPlan` | Cumulative ≤ 60s (L2–L5) |
| **3** | `layer_03_rim_mining_bundles` | `layers/layer_03_rim_mining_bundles/` | `RimBundleCandidateSet` | Same |
| **4** | `layer_04_inner_pattern_fill` | `layers/layer_04_inner_pattern_fill/` | `InnerBundleCandidateSet` | Same |
| **5** | `layer_05_commit_validate` | `layers/layer_05_commit_validate/` | `CommittedPlacementSet`, `ValidationResult`, `StackRunSummary` | Same |
| **6** | `layer_06_floor2_space_link` | — | — | **Deferred** |

### Layer-1 — `layer_01_reconstruction`

**Identity:** Stack **Layer 1** is always referred to by slug `layer_01_reconstruction` in docs, `StackRunSummary`, replay step keys, and gates — even though implementation remains in `reconstruction/`.

**Facade (required):**

```text
layers/layer_01_reconstruction/run.py  → delegates to reconstruction/ pipeline
layers/layer_01_reconstruction/__init__.py  → exports run_layer_01, Layer01ReconstructionOutput
```

**No bulk move** of `reconstruction/**` into `layers/` in v1 (decontamination import stability).

**Pipeline:**

```text
decode → cleanup → reconstruction overlay
  → build_reconstruction_complete_map(cleanup, recon)
  → CapacityEnvelope
```

```python
@dataclass(frozen=True, slots=True)
class Layer01ReconstructionOutput:
    complete_map: ReconstructionCompleteMap
    capacity_envelope: CapacityEnvelope
```

**Normative:** `ReconstructionResult.cells` = overlay only. Layers 2–5 **MUST NOT** use overlay, replay frames, NDJSON, or prior `solver_summary` as input.

### Layer-2 — `layer_02_exterior_transport`

**Purpose:** Plan **external outer-connection** transport from `ReconstructionCompleteMap` + throughput budget.

**Minimum DTO (normative):**

```python
class TransportKind(StrEnum):
    SHAPE = "shape"
    FLUID = "fluid"


class ExteriorConnectionShortfallReason(StrEnum):
    MISSING_EVTC_ROW = "missing_evtc_row"
    TARGET_EXCEEDS_TERRAIN_UPPER_BOUND = "target_exceeds_terrain_upper_bound"
    NO_FEASIBLE_CONNECTOR_SITES = "no_feasible_connector_sites"
    # extend via spec amendment + tests — no free-form strings


@dataclass(frozen=True, slots=True)
class ExteriorConnector:
    connector_id: str
    coords: tuple[Coord, ...]
    capacity_per_min: Decimal  # from EVTC per-connector cap


@dataclass(frozen=True, slots=True)
class ExteriorConnectionPlan:
    transport_kind: TransportKind
    terrain_upper_bound_per_min: Decimal  # A — observability + ceiling
    planning_target_per_min: Decimal  # C — sizing target (throughput_target_percent × A)
    per_connector_capacity_per_min: Decimal  # from EVTC resolver — no literals in layer code
    required_connector_count: int
    planned_connectors: tuple[ExteriorConnector, ...]
    unmet_reason: ExteriorConnectionShortfallReason | None
```

**Invariant (normative):**

```text
required_connector_count = ceil(planning_target_per_min / per_connector_capacity_per_min)
  when per_connector_capacity_per_min > 0
```

- **A** (`terrain_upper_bound_per_min`): max possible from complete-map capacity envelope — **not** used alone to size connectors when **C** is set.
- **C** (`planning_target_per_min`): sole input to `required_connector_count` for planning.
- Lane/per-connector caps: **EVTC resolver only** ([`exterior_transport_capacity.py`](../../../django_apps/game_data/services/exterior_transport_capacity.py)).

### Layer-3 / Layer-4 — route-probed candidate sets

**Typed candidate (normative):**

```python
class RouteProbeStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED_BUDGET = "skipped_budget"


@dataclass(frozen=True, slots=True)
class RouteProbedBundleCandidate:
    candidate: BundleCandidate
    route_probe_status: RouteProbeStatus
    route_probe_result: RouteProbeResult | None  # required non-None when SUCCEEDED


@dataclass(frozen=True, slots=True)
class RimBundleCandidateSet:
    normal_candidates: tuple[RouteProbedBundleCandidate, ...]
    diagnostic_rejected_candidates: tuple[RouteProbedBundleCandidate, ...]
```

`InnerBundleCandidateSet` — same shape as `RimBundleCandidateSet`.

**Pool invariant (normative):**

```text
normal_candidates contains only entries with route_probe_status == SUCCEEDED.
Unreachable / failed probes exist only in diagnostic_rejected_candidates.
Unprobed candidates MUST NOT appear in normal_candidates.
```

### Layer-5 — `layer_05_commit_validate` (internal subphases)

| Subphase | Name | Responsibility |
|----------|------|----------------|
| **L5a** | `incremental_commit` | `Gene.commit_order`; commit-time latest `route_domain` re-probe; `CommittedPlacementSet` |
| **L5b** | `read_only_validation` | Assert-only `ValidationResult` |
| **L5c** | `stack_run_summary_projection` | `StackRunSummary` from L1–L5 metadata |

**L5b prohibitions (normative):**

```text
L5b MUST NOT import or call route probe modules.
L5b MUST NOT mutate CommittedPlacementSet.
L5c MUST NOT alter ValidationResult or CommittedPlacementSet.
```

### Layer-6 — deferred

Not registered in `stack_runner`, no package, no tests.

---

## §2 — Package layout

```text
django_apps/asteroid_lab/
  reconstruction/                      # Layer 1 implementation (KEEP)
  layers/
    contracts/                         # StackRunStatus, layer I/O, StrEnums
    shared/
    layer_01_reconstruction/           # facade → reconstruction/
    layer_02_exterior_transport/
    layer_03_rim_mining_bundles/
    layer_04_inner_pattern_fill/
    layer_05_commit_validate/
      commit.py                        # L5a
      validate.py                    # L5b — no route_probe imports
      summary.py                     # L5c
    stack_runner.py
  services/solver_runtime_entry.py
```

**Forbidden token `placement_stack` (runtime):**

```text
django_apps/asteroid_lab/**/*.py  — hard fail (identifier/path segment)
documents/ai/current_plan.md        — hard fail
docs/superpowers/specs/**         — NOT scanned (governance docs may describe the ban)
```

Enforced by **GATE-LS-TOKEN** — see implementation plan Task 3.

**Forbidden `optimization/` (narrow):**

```text
No django_apps/asteroid_lab/optimization/ package
No layers/** import of django_apps.asteroid_lab.optimization or .catalog
```

Does **not** forbid historical docs or unrelated apps.

### Import matrix

| From | May import |
|------|------------|
| `reconstruction/` | `cleanup/`, `snapshots/`, `contracts/game_data_snapshot*` — **not** `layers/` |
| `layers/layer_01_reconstruction/` | `reconstruction/*`, `layers/contracts` |
| `layers/layer_02` … `layer_05` | `layers/contracts`, `layers/shared`, `reconstruction/complete_map`, `game_data` EVTC — **not** `optimization/`, **not** `catalog/` |
| `layers/layer_05/validate.py` (L5b) | **not** `layers/shared/route_probe*` or equivalent |
| `layers/stack_runner` | `layer_01` … `layer_05` facades, `layers/contracts` |
| `services/solver_runtime_entry` | `layers/stack_runner` |

**Single `route_domain` owner:** `RouteDomainSnapshotBuilder` only (in `layers/shared` or `layer_05/commit.py`).

---

## §3 — Stack runtime, budget, timeout

### Execution order

```text
run_solver (target):
  stack_runner.run_full():
    1. layer_01_reconstruction.run_layer_01()  → Layer01ReconstructionOutput
    2. stack_runner.run_layers_02_to_05(
         input=complete_map,
         budget_ms=60_000,
       )
    3. emit replay / solver_summary (output-only artifacts)
```

### 60s budget ownership (normative)

```text
The 60s budget is owned exclusively by stack_runner.
Individual layers MUST NOT create independent full 60s timers.
Each layer receives remaining_budget_ms: int from stack_runner.
If remaining_budget_ms <= 0 before starting a layer, stack_runner fails closed
  without invoking that layer.
Layers MUST pass remaining_budget_ms into sub-loops and stop cooperatively.
```

- **Scope:** Layers **2–5** only; Layer 1 excluded.
- **Clock:** `LayerBudgetContext` uses injectable `now_fn` (default `time.monotonic`) for tests; `from_budget_ms(60_000)` at `run_layers_02_to_05` entry.

### Stack run status (normative)

```python
class StackRunStatus(StrEnum):
    SUCCESS = "success"
    TIMEOUT_FAIL_CLOSED = "timeout_fail_closed"
    LAYER_FAILED_CLOSED = "layer_failed_closed"
    VALIDATION_FAILED = "validation_failed"
```

Map to `SolverRuntimeEntryErrorCode` in `solver_runtime_entry` (e.g. `TIMEOUT_FAIL_CLOSED` → `SOLVER_TIME_BUDGET_EXCEEDED`) — no free-form strings.

### Stack run result (normative)

```python
@dataclass(frozen=True, slots=True)
class StackRunResult:
    status: StackRunStatus
    completed_layer_slugs: tuple[str, ...]
    failed_layer_slug: str | None  # set on TIMEOUT_FAIL_CLOSED / LAYER_FAILED_CLOSED
    diagnostic_snapshot: DiagnosticLayerSnapshot | None
```

### Timeout policy

| Rule | Value |
|------|-------|
| Product outcome | Fail-closed — no success / exterior-pass / validation-pass claims |
| Incomplete layer | Never committed |
| Diagnostic snapshot | Last **completed** layer only |

### Diagnostic snapshots — non-resumable (normative)

```text
Diagnostic snapshots are NOT resumable algorithm inputs.
They MAY be serialized for UI/debug/replay observability only.
A later solver execution MUST restart from Layer01ReconstructionOutput.complete_map,
  NOT from a diagnostic layer snapshot.
```

```python
@dataclass(frozen=True, slots=True)
class DiagnosticLayerSnapshot:
    layer_slug: str  # e.g. layer_02_exterior_transport
    layer_index: int  # 2..5
    payload: dict[str, object]  # JSON-serializable observability only
    # Type name documents non-resumable contract; no from_snapshot() on stack_runner.
```

**Forbidden:** `resume_from_diagnostic`, `stack_runner.run_from_layer_03`, passing `DiagnosticLayerSnapshot` into any `run_layer_*` input.

---

## §4 — Tests and gates

### Test layout

```text
tests/unit/asteroid_lab/layers/
  test_stack_runner_invokes_l1_then_l2_to_l5.py
  test_stack_runner_time_budget.py
  test_stack_runner_timeout_fail_closed.py
  test_placement_stack_token_forbidden.py
  test_layer_import_matrix.py
  test_layer_02_exterior_connection_plan.py
  test_layer_03_04_probe_before_pool.py
  test_layer_05_subphases_read_only.py
  test_diagnostic_snapshot_not_resumable.py
  test_layer_input_forbidden_replay.py
```

### Gates

| Gate ID | Assertion |
|---------|-----------|
| **GATE-LS-TOKEN** | `placement_stack` absent in `django_apps/asteroid_lab/**` + `current_plan.md` (specs dir not scanned) |
| **GATE-LS-L1-FACADE** | `layer_01_reconstruction` exists; `reconstruction/` does not import `layers` |
| **GATE-LS-IMPORT** | Same as above + layer import matrix |
| **GATE-LS-BUDGET-OWNER** | Only `stack_runner` sets 60s deadline constant |
| **GATE-LS-60S** | Slow layer stub → `TIMEOUT_FAIL_CLOSED` |
| **GATE-LS-DIAG** | Diagnostic present; no resume API |
| **GATE-LS-L2-CEIL** | `required_connector_count` uses `ceil` on C |
| **GATE-LS-L2-CAP** | No belt/pipe cap literals in layer_02 |
| **GATE-LS-POOL** | `normal_candidates` all `SUCCEEDED` |
| **GATE-LS-L5B** | `validate.py` does not import route_probe |
| **GATE-LS-NO-L6** | No layer_06 in runner |
| **GATE-LS-INPUT** | No replay/summary in layer runner signatures |

---

## §5 — Documentation migration

| Document | Action |
|----------|--------|
| This spec | CANON |
| `documents/Algorithm/asteroid_lab_13_layer_stack.md` | NEW — layer_01..06 table |
| `documents/Algorithm/README.md` | Layer stack section |
| `document_inventory.md` | Row → this spec |
| `structure.md` | `layers/` + `layer_01_reconstruction` facade |

---

## §6 — RTTP frozen assets

Unchanged: greenfield `layers/`; EVTC via `game_data`; MEG FROZEN; old “RTTP Layer 4” ≠ `layer_04_inner_pattern_fill`.

---

## §7 — Non-goals

Layer-6; GA default; `optimization/` restoration; resumable diagnostics; shapez_solver scope.

---

## §8 — Contract checklist (implementation gate)

```text
[ ] stack_runner owns cumulative 60s timer
[ ] each layer receives remaining_budget_ms
[ ] StackRunStatus StrEnum exists
[ ] timeout snapshot is diagnostic-only, not resumable input
[ ] layer_01_reconstruction facade registered before L2
[ ] L2 ExteriorConnectionPlan has ceil connector count + A and C fields
[ ] L3/L4 normal pool type guarantees route_probe_status == SUCCEEDED
[ ] rejected candidates only in diagnostic_rejected_candidates
[ ] L5a / L5b / L5c separated; L5b no route probe import
[ ] L6 no package, tests, or registration
[ ] placement_stack forbidden by GATE-LS-TOKEN
[ ] replay / overlay / solver_summary forbidden as layer input
```

### Remaining open items (non-blocking)

1. HTTP body when L1 ok but stack `TIMEOUT_FAIL_CLOSED` — align with `SolverRuntimeEntryResult` in PR-4.
2. `StackRunSummary` nesting under existing `solver_summary` keys — PR-4.

---

## §9 — Spec self-review (2026-05-27, patched)

| Check | Result |
|-------|--------|
| Contract patches 1–5 | §3 budget, §3 diagnostic, §1 L2 DTO, §1 L3/L4 typed pool, §1 L5 subphases |
| layer_01 | Facade + slug; `reconstruction/` unmoved |
| Placeholders | §8 only bounded HTTP/summary nesting |

---

## References

- [Implementation plan](../plans/2026-05-27-asteroid-lab-algorithm-layer-stack.md)
- [Decontamination design](2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md)
- [Complete-map DTO](2026-05-26-reconstruction-complete-map-dto-design.md)
- [Throughput target PR-2c](2026-05-24-throughput-target-percent-pr2c-design.md)
