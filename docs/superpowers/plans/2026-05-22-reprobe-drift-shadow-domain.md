---
status: CANCELLED
cancelled_date: 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
---
# Reprobe Drift Shadow Domain Parity ??Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase I??shadow domain parity ??selection uses the same route-domain builder and reprobe skip rules as Phase J so reference `copy-import-e954a2cb` reaches RD-GATE (24 selected, 24 confirmed, 0 probe_fail, 0 inlet).

**Architecture:** New `selection_shadow_state.py` maintains in-memory reservations/occupied/route cells; `commit_route_feasibility.py` shares J pre-confirm predicates; `candidate_selector` runs greedy with `shadow_try_confirm` runner-up policy when `SelectionShadowPolicy.SHADOW_DOMAIN_PARITY`; pipeline wires policy + summary keys.

**Tech Stack:** Python 3.12+, Django 5.2 app `django_apps/asteroid_lab`, pytest, ruff.

**Spec:** [`docs/superpowers/specs/2026-05-22-reprobe-drift-shadow-domain-design.md`](../specs/2026-05-22-reprobe-drift-shadow-domain-design.md)

**Revision:** 2026-05-22 architect review ??feasibility aggregator split, Task 3/4 test isolation, domain test via `committed_occupied`, `ShadowConfirmOutcome` in product module, call-site audit, M1 diagnostic-only.

**Execution:** **Subagent-Driven** (approved). One task per subagent; regression gate between tasks.

---

## File map

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/optimization/enums.py` | `SelectionShadowPolicy` StrEnum |
| `django_apps/asteroid_lab/optimization/commit_route_feasibility.py` | Shared path/inlet/transport skip checks (extracted from J) |
| `django_apps/asteroid_lab/optimization/selection_shadow_state.py` | Shadow state + reprobe + confirm |
| `django_apps/asteroid_lab/optimization/commit_best_candidates.py` | Import shared feasibility helpers |
| `django_apps/asteroid_lab/optimization/candidate_selector.py` | Shadow greedy loop + diagnostics |
| `django_apps/asteroid_lab/services/solver_runtime_pipeline.py` | Default policy ON, summary keys |
| `tests/unit/asteroid_lab/test_selection_shadow_state.py` | Shadow module unit tests |
| `tests/unit/asteroid_lab/test_candidate_selector.py` | Selector integration tests |
| `tests/unit/asteroid_lab/test_solver_runtime_pipeline.py` | Summary key test |
| `documents/Algorithm/solver_runtime/phase_i_candidate_selection.md` | Doc sync |

---

### Task 1: `SelectionShadowPolicy` + extended `SelectionDiagnostics`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/enums.py` (after `CommitOrderPolicy`)
- Modify: `django_apps/asteroid_lab/optimization/candidate_selector.py` (`SelectionDiagnostics`)
- Test: `tests/unit/asteroid_lab/test_solver_runtime_pipeline.py` (temporary import smoke ??optional)

- [ ] **Step 1: Add enum**

In `enums.py`:

```python
class SelectionShadowPolicy(StrEnum):
    """Phase I??shadow reprobe policy (predictive; J remains authoritative)."""

    OFF = "off"
    SHADOW_DOMAIN_PARITY = "shadow_domain_parity"
```

- [ ] **Step 2: Extend diagnostics dataclass**

In `candidate_selector.py`:

```python
@dataclass(frozen=True, slots=True)
class SelectionDiagnostics:
    selection_skipped_duplicate_anchor_count: int
    max_selected_variants_per_extractor: int
    selection_stopped_by_throughput_budget: bool = False
    selected_throughput_at_stop: int = 0
    selection_skipped_inlet_on_shared_transport_count: int = 0
    selection_skipped_shadow_probe_failed_count: int = 0
    selection_skipped_shadow_inlet_on_shared_transport_count: int = 0
    selection_shadow_reprobe_count: int = 0
    selection_shadow_policy: SelectionShadowPolicy = SelectionShadowPolicy.OFF
```

Update every `SelectionDiagnostics(...)` constructor in tests to pass new fields (defaults OK) or rely on defaults for new fields only.

- [ ] **Step 3: Run selector tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_candidate_selector.py -v
```

Expected: PASS (defaults preserve behavior).

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/optimization/enums.py django_apps/asteroid_lab/optimization/candidate_selector.py
git commit -m "feat(asteroid_lab): add SelectionShadowPolicy and diagnostics fields"
```

---

### Task 2: Extract `commit_route_feasibility` (J/shadow parity)

**Files:**
- Create: `django_apps/asteroid_lab/optimization/commit_route_feasibility.py`
- Modify: `django_apps/asteroid_lab/optimization/commit_best_candidates.py`
- Test: `tests/unit/asteroid_lab/test_incremental_commit.py` (regression only)

- [ ] **Step 1: Create shared module**

Move (copy then delete private copies in J) these functions from `commit_best_candidates.py` into `commit_route_feasibility.py` with **unchanged semantics**:

- `path_transport_conflict`
- `occupied_conflict`
- `equipment_cells_for_candidate`
- `inlet_on_shared_transport_conflict`
- `equipment_transport_overlap`
- `protected_corridor_conflict`
- `hard_blocked_conflict`

Add **two** aggregators ??do not put `occupied_conflict` inside `commit_skip_reason_for_path` (name must match scope):

```python
def commit_skip_reason_for_path(
    *,
    candidate: GeneCandidate,
    path: tuple[Coord, ...],
    inp: OptimizationInput,
    committed_equipment_cells: frozenset[Coord],
    committed_route_cells: frozenset[Coord],
    existing_reservations: tuple[RouteReservation, ...],
) -> CommitConflictReason | None:
    """Path + reservation conflicts only (matches J ``_attempt_commit_one`` post-reprobe chain)."""

    return (
        path_transport_conflict(path, candidate.transport_kind, existing_reservations)
        or protected_corridor_conflict(path, inp)
        or hard_blocked_conflict(path, inp)
        or inlet_on_shared_transport_conflict(candidate, committed_route_cells)
        or equipment_transport_overlap(
            candidate=candidate,
            path=path,
            committed_equipment_cells=committed_equipment_cells,
            committed_route_cells=committed_route_cells,
        )
    )


def commit_preconfirm_skip_reason(
    *,
    candidate: GeneCandidate,
    path: tuple[Coord, ...],
    inp: OptimizationInput,
    committed_occupied: frozenset[Coord],
    committed_equipment_cells: frozenset[Coord],
    committed_route_cells: frozenset[Coord],
    existing_reservations: tuple[RouteReservation, ...],
) -> CommitConflictReason | None:
    """Full pre-confirm skip (J order: occupied before reprobe; path checks after reprobe)."""

    return occupied_conflict(candidate.occupied_cells, committed_occupied) or commit_skip_reason_for_path(
        candidate=candidate,
        path=path,
        inp=inp,
        committed_equipment_cells=committed_equipment_cells,
        committed_route_cells=committed_route_cells,
        existing_reservations=existing_reservations,
    )
```

**J refactor rule:** `_process_candidate_attempt` keeps `occupied_conflict` **before** `run_route_probe`; `_attempt_commit_one` calls only `commit_skip_reason_for_path` after normalize. `shadow_try_confirm` mirrors that split (occupied ??reprobe ??`commit_skip_reason_for_path`).

- [ ] **Step 2: Rewire `commit_best_candidates.py`**

Replace private `_inlet_on_shared_transport_conflict` etc. with imports from `commit_route_feasibility`. `_attempt_commit_one` skip chain must produce identical `CommitConflictReason` for existing tests.

- [ ] **Step 3: Regression**

```bash
python -m pytest tests/unit/asteroid_lab/test_incremental_commit.py -v
```

Expected: PASS (no behavior change).

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/optimization/commit_route_feasibility.py django_apps/asteroid_lab/optimization/commit_best_candidates.py
git commit -m "refactor(asteroid_lab): share commit route feasibility checks for shadow parity"
```

---

### Task 3: `selection_shadow_state` ??empty state + reprobe (no `shadow_try_confirm`)

**Scope:** Prove `RouteDomainSnapshotBuilder.build_snapshot` sees shadow `committed_occupied_cells`. **Do not** call `shadow_try_confirm` here (Task 4).

**Files:**
- Create: `django_apps/asteroid_lab/optimization/selection_shadow_state.py`
- Create: `tests/unit/asteroid_lab/test_selection_shadow_state.py`

- [ ] **Step 1: Write failing test ??domain reflects `committed_occupied`**

`tests/unit/asteroid_lab/test_selection_shadow_state.py`:

```python
from django_apps.asteroid_lab.optimization.selection_shadow_state import (
    SelectionShadowState,
    shadow_reprobe,
)
# Reuse _gene_candidate / _void_inp from test_candidate_selector (import or copy helpers)
```

Test `test_shadow_reprobe_uses_committed_occupied_in_domain`:

- **Do not** rely on same-transport reservation ?œblocking??a trunk cell (v0 overlays promote TRANSPORT; shared-kind paths may stay reachable).
- Build `inp` with void corridor to goal `(6, 0)`.
- Candidate `b` with `route_probe_start` and gen path through cell `(2, 0)`; assert `shadow_reprobe(b, inp, empty_state)` ??`reachable is True`.
- Construct `SelectionShadowState` **manually** (no confirm helper):

```python
blocked = frozenset({(2, 0)})  # blocks b's route_probe_start or first hop
state = SelectionShadowState(
    reservations=(),
    committed_occupied=blocked,
    committed_route_cells=frozenset(),
    committed_equipment_cells=frozenset(),
)
```

- Assert `shadow_reprobe(b, inp, state).reachable is False`.

Optional second case (transport mask): state with one `SHAPE_BELT` reservation on `(3,0)` and candidate `FLUID_PIPE` reprobe ??unreachable or wrong kind (document expected probe outcome in test comment).

- [ ] **Step 2: Run test ??expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_selection_shadow_state.py::test_shadow_reprobe_uses_committed_occupied_in_domain -v
```

- [ ] **Step 3: Implement minimal state + reprobe**

`selection_shadow_state.py`:

```python
@dataclass(frozen=True, slots=True)
class SelectionShadowState:
    reservations: tuple[RouteReservation, ...]
    committed_occupied: frozenset[Coord]
    committed_route_cells: frozenset[Coord]
    committed_equipment_cells: frozenset[Coord]

def empty_selection_shadow_state() -> SelectionShadowState:
    return SelectionShadowState((), frozenset(), frozenset(), frozenset())

def build_shadow_route_domain(
    inp: OptimizationInput,
    state: SelectionShadowState,
) -> dict[Coord, RouteCellDomain]:
    return RouteDomainSnapshotBuilder.build_snapshot(
        inp,
        confirmed_reservations=state.reservations,
        committed_occupied_cells=state.committed_occupied,
    )

def shadow_reprobe(
    candidate: GeneCandidate,
    inp: OptimizationInput,
    state: SelectionShadowState,
    *,
    max_expansions: int,
) -> RouteProbeResult:
    domain = build_shadow_route_domain(inp, state)
    return run_route_probe(
        RouteProbeInput(
            start=candidate.route_probe_start,
            goals=inp.route_goals,
            route_domain=domain,
            topology_graph=inp.topology_graph,
            max_expansions=max_expansions,
            transport_kind=candidate.transport_kind,
        )
    )
```

- [ ] **Step 4: Run test ??expect PASS**

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/optimization/selection_shadow_state.py tests/unit/asteroid_lab/test_selection_shadow_state.py
git commit -m "feat(asteroid_lab): selection shadow state and reprobe"
```

---

### Task 4: `shadow_try_confirm` + inlet path-drift test

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/selection_shadow_state.py` (add `ShadowConfirmOutcome` + `shadow_try_confirm`)
- Modify: `tests/unit/asteroid_lab/test_selection_shadow_state.py`

- [ ] **Step 1: Write failing test ??inlet on shadow reprobed path**

Define outcome type in **product** module `selection_shadow_state.py` (tests import only):

```python
# selection_shadow_state.py
@dataclass(frozen=True, slots=True)
class ShadowConfirmOutcome:
    kind: Literal["confirmed", "probe_failed", "skipped"]
    reason: CommitConflictReason | None = None
    state: SelectionShadowState | None = None
```

Test `test_shadow_confirm_rejects_inlet_on_reprobed_trunk`:
- Confirm `a` with path `((0,0),(1,0),(2,0),(3,0)...(6,0))`, `fot=(2,0)`.
- Candidate `b` with `fot=(1,0)` (on `a`'s reprobed path prefix, not on `b`'s gen-only mirror).
- `shadow_try_confirm(b, ...)` ??`kind == "skipped"`, `reason == CommitConflictReason.INLET_ON_SHARED_TRANSPORT`.

- [ ] **Step 2: Run ??expect FAIL**

- [ ] **Step 3: Implement `shadow_try_confirm`**

Flow (mirror J):
1. `occupied_conflict` ??`skipped` if set
2. `shadow_reprobe`
3. If not reachable ??`probe_failed`
4. `path = normalize_probe_path(candidate, probe.path)`
5. `reason = commit_skip_reason_for_path(...)` ??**not** `commit_preconfirm_skip_reason` (occupied already checked)
6. If `reason`: return `ShadowConfirmOutcome("skipped", reason, None)`
- Else build `RouteReservation` (CONFIRMED, ordinal from `len(state.reservations)`), return new state:

```python
committed_route_cells = state.committed_route_cells | frozenset(path)
committed_equipment = state.committed_equipment_cells | equipment_cells_for_candidate(candidate)
committed_occupied = state.committed_occupied | candidate.occupied_cells
```

- [ ] **Step 4: Run shadow tests ??PASS**

```bash
python -m pytest tests/unit/asteroid_lab/test_selection_shadow_state.py -v
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/optimization/selection_shadow_state.py tests/unit/asteroid_lab/test_selection_shadow_state.py
git commit -m "feat(asteroid_lab): shadow_try_confirm with J feasibility parity"
```

---

### Task 5: Wire `candidate_selector` ??shadow greedy loop

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/candidate_selector.py`
- Modify: `tests/unit/asteroid_lab/test_candidate_selector.py`
- Audit: all `select_gene_candidates_greedy` call sites (see Step 0)

- [ ] **Step 0: Call-site audit**

`select_gene_candidates_greedy` already requires keyword `inp=`. New kwargs are optional with defaults ??verify no positional breakage.

```bash
rg "select_gene_candidates_greedy" --glob "*.py"
```

Known call sites (must pass `inp=` explicitly after any signature change):

| Path |
|------|
| `django_apps/asteroid_lab/services/solver_runtime_pipeline.py` |
| `tests/unit/asteroid_lab/test_candidate_selector.py` |
| `tests/test_golden_candidate_selector.py` |

Fix any site missing `inp=` before green Task 5.

- [ ] **Step 1: Write failing test ??domain drift**

`test_shadow_reprobe_excludes_unreachable_after_prior_pick` in `test_candidate_selector.py`:
- Two candidates; first wins shadow confirm and blocks corridor.
- `select_gene_candidates_greedy(..., selection_shadow_policy=SHADOW_DOMAIN_PARITY, route_probe_max_expansions=256)`.
- Assert second id **not** in `plan.ordered_candidate_ids`.
- Assert `selection_skipped_shadow_probe_failed_count >= 1` OR second never picked (document which counter increments when runner-up exhausts).

- [ ] **Step 2: Write failing test ??policy OFF regression**

`test_selector_shadow_policy_off_matches_tier_1_2b`:
- Copy assertions from `test_selector_skips_stub_on_prefix_path_cell_before_normalized_tail` with `selection_shadow_policy=SelectionShadowPolicy.OFF`.

- [ ] **Step 3: Run both ??FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_candidate_selector.py::test_shadow_reprobe_excludes_unreachable_after_prior_pick tests/unit/asteroid_lab/test_candidate_selector.py::test_selector_shadow_policy_off_matches_tier_1_2b -v
```

- [ ] **Step 4: Implement selector branch**

Add parameters to `select_gene_candidates_greedy`:

```python
def select_gene_candidates_greedy(
    candidates: tuple[GeneCandidate, ...],
    *,
    inp: OptimizationInput,
    targets: BundleSelectionTargets | None = None,
    max_selected_variants_per_extractor: int = DEFAULT_MAX_SELECTED_VARIANTS_PER_EXTRACTOR,
    selection_shadow_policy: SelectionShadowPolicy = SelectionShadowPolicy.OFF,
    route_probe_max_expansions: int = 256,
) -> tuple[SelectedCandidatePlan, SelectionDiagnostics]:
```

When `selection_shadow_policy is SelectionShadowPolicy.SHADOW_DOMAIN_PARITY`:
- Init `shadow = empty_selection_shadow_state()`
- Counters: `shadow_probe_failed`, `shadow_inlet`, `shadow_reprobe_count`
- In loop, **do not** update `selected_route_cells` / `selection_mirror_route_cells`
- Inlet pre-filter: `candidate.fixed_output_transport not in shadow.committed_route_cells`
- After building `pool` (eligible list), sort by `_selection_sort_key` descending, iterate:

```python
picked: GeneCandidate | None = None
for c in sorted(pool, key=..., reverse=True):
    shadow_reprobe_count += 1
    outcome = shadow_try_confirm(c, inp, shadow, max_expansions=route_probe_max_expansions)
    if outcome.kind == "confirmed":
        picked = c
        shadow = outcome.state
        break
    if outcome.kind == "probe_failed":
        shadow_probe_failed += 1
    elif outcome.kind == "skipped" and outcome.reason == INLET_ON_SHARED_TRANSPORT:
        shadow_inlet += 1
if picked is None:
    break  # same break semantics as today when no progress
# else append picked, update goal_load / occupied (occupied still uses footprint set, not shadow)
```

When `OFF`: keep existing loop body unchanged (Tier 1.2b mirror).

Set `selection_shadow_policy` on returned `SelectionDiagnostics`.

- [ ] **Step 5: Run selector tests ??PASS**

```bash
python -m pytest tests/unit/asteroid_lab/test_candidate_selector.py -v
```

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/optimization/candidate_selector.py tests/unit/asteroid_lab/test_candidate_selector.py
git commit -m "feat(asteroid_lab): shadow domain parity in greedy selection"
```

---

### Task 6: Pipeline wiring + summary keys

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_pipeline.py`
- Modify: `django_apps/asteroid_lab/management/commands/run_solver.py` (optional stdout gate keys)
- Test: `tests/unit/asteroid_lab/test_solver_runtime_pipeline.py`

- [ ] **Step 1: Write failing pipeline test**

```python
def test_pipeline_summary_includes_shadow_diagnostics(monkeypatch):
    # Run minimal pipeline or call _build_solver_summary / _anchor_diversity_metrics with SelectionDiagnostics(
    #   selection_shadow_policy=SelectionShadowPolicy.SHADOW_DOMAIN_PARITY, ...
    # )
    assert summary["selection_shadow_policy"] == "shadow_domain_parity"
    assert "selected_candidate_count" in summary
    assert "selection_shadow_reprobe_count" in summary
```

Prefer patching `select_gene_candidates_greedy` to return known diagnostics if full pipeline is heavy.

- [ ] **Step 2: Add pipeline constants**

```python
from django_apps.asteroid_lab.optimization.enums import SelectionShadowPolicy

DEFAULT_SELECTION_SHADOW_POLICY = SelectionShadowPolicy.SHADOW_DOMAIN_PARITY
```

Call:

```python
plan, selection_diag = select_gene_candidates_greedy(
    pool.normal_candidates,
    inp=inp,
    targets=targets,
    selection_shadow_policy=DEFAULT_SELECTION_SHADOW_POLICY,
    route_probe_max_expansions=config.route_probe_max_expansions,
)
```

- [ ] **Step 3: Extend `_anchor_diversity_metrics`**

```python
"selection_shadow_policy": selection_diag.selection_shadow_policy.value,
"selected_candidate_count": len(plan.ordered_candidate_ids),
"selection_skipped_shadow_probe_failed_count": selection_diag.selection_skipped_shadow_probe_failed_count,
"selection_skipped_shadow_inlet_on_shared_transport_count": (
    selection_diag.selection_skipped_shadow_inlet_on_shared_transport_count
),
"selection_shadow_reprobe_count": selection_diag.selection_shadow_reprobe_count,
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_solver_runtime_pipeline.py -v
python -m ruff check django_apps/asteroid_lab/optimization/selection_shadow_state.py django_apps/asteroid_lab/optimization/commit_route_feasibility.py django_apps/asteroid_lab/optimization/candidate_selector.py django_apps/asteroid_lab/services/solver_runtime_pipeline.py
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/services/solver_runtime_pipeline.py tests/unit/asteroid_lab/test_solver_runtime_pipeline.py
git commit -m "feat(asteroid_lab): wire shadow selection policy and summary keys"
```

---

### Task 7: Documentation sync

**Files:**
- Modify: `documents/Algorithm/solver_runtime/phase_i_candidate_selection.md`
- Modify: `docs/superpowers/specs/2026-05-22-reprobe-drift-shadow-domain-design.md` (Status ??Implemented after RD-GATE)

- [ ] **Step 1: Update phase I doc**

Add section **Phase I??shadow domain parity** after Tier 1.2b:
- `SelectionShadowPolicy.SHADOW_DOMAIN_PARITY`
- Shadow state uses `RouteDomainSnapshotBuilder` + `shadow_try_confirm`
- Inlet uses `committed_route_cells` from shadow reprobed paths
- `OFF` restores gen-path mirror

- [ ] **Step 2: Commit**

```bash
git add documents/Algorithm/solver_runtime/phase_i_candidate_selection.md
git commit -m "docs: Phase I prime shadow domain parity"
```

---

### Task 8: RD-GATE manual verification

**Files:** none (verification only)

- [ ] **Step 1: Unit regression**

```bash
python -m pytest tests/unit/asteroid_lab/test_selection_shadow_state.py tests/unit/asteroid_lab/test_candidate_selector.py tests/unit/asteroid_lab/test_incremental_commit.py tests/unit/asteroid_lab/test_solver_runtime_pipeline.py -v
```

Expected: PASS.

- [ ] **Step 2: Reference smoke**

```bash
python manage.py run_solver --slug copy-import-e954a2cb --run-key agent-smoke
```

Record and compare:

| Key | RD-GATE |
|-----|---------|
| `validation_passed` | `True` |
| `commit_inlet_on_shared_transport_count` | `0` |
| `commit_route_probe_failed_count` | `0` |
| `selected_candidate_count` | `>= 24` |
| `confirmed_count` | `>= 24` |
| `selection_shadow_policy` | `shadow_domain_parity` |

- [ ] **Step 3: Shadow/J parity check**

If any candidate is ordered but fails at J with `ROUTE_PROBE_FAILED` or `INLET_ON_SHARED_TRANSPORT`:
- Treat as **shadow parity bug** (inspect `commit_route_feasibility` vs J, domain builder inputs).
- Do **not** weaken RD-GATE thresholds.

- [ ] **Step 4: Update spec status**

Set spec **Status:** Implemented YYYY-MM-DD only when all RD rows pass.

---

## Spec coverage self-review

| Spec requirement | Task |
|------------------|------|
| `SelectionShadowPolicy` | 1 |
| `SelectionShadowState` + operations | 3?? |
| J/shared skip predicates (`for_path` + `preconfirm`) | 2, 4 |
| Phase I shadow loop | 5 |
| Pipeline default ON + summary keys | 6 |
| Tests listed in spec | 3?? |
| RD-GATE manual | 8 |
| Doc sync | 7 |
| Phase J unchanged | 2 regression only |
| Forbidden replay input | 6 (no new imports); code review in 8 |
| Rollback `OFF` | 5 test + `DEFAULT_SELECTION_SHADOW_POLICY` doc |

**Milestone M1 (`confirmed >= 23`):** diagnostic-only during Task 8 iteration. **Do not** mark implementation or spec ?œImplemented??unless **full RD-GATE** passes (24/24/0/0).

---

## Execution handoff

**Approved:** Subagent-Driven execution of Tasks 1?? in order.

Per task: implement ??narrow pytest ??ruff on touched paths ??parent review before next task.

Plan: [`docs/superpowers/plans/2026-05-22-reprobe-drift-shadow-domain.md`](2026-05-22-reprobe-drift-shadow-domain.md)

To start implementation in this session, reply **?ŒTask 1 ?œìž‘??* (or spawn subagent with Task 1 prompt from this file).
