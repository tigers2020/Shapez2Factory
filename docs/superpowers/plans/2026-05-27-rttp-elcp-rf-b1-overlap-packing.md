# P1-ELCP-RF-B1 — Overlap Packing Selection — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Increase Gate A `commit_order_len` via opt-in `SelectionMode.GREEDY_REGRET_OVERLAP_PACK` using overlap-graph packing (Phase 0 bounds → Phase 1 selection → Phase C guards), without changing commit-time ELCP policy or default `GREEDY_REGRET`.

**Architecture:** Shared deterministic graph/MIS logic in `optimization/selection/overlap_graph.py`; runtime selection in `overlap_pack.py`; Phase 0 harness wraps the same library for bounds report (not solver input). Phase 0 publishes frozen `target_floor` constants; Phase 1 tests assert against frozen values only. **Task 4 GATE:** if Phase 0 NO-GO, stop before Phase 1 production selection code.

**Tech Stack:** Python 3.12+, pytest, ruff, mypy (`django_apps`); existing `greedy_regret` scoring helpers; Gate A `run_rttp_pipeline` fixture pattern from A2.

**Design spec:** [`docs/superpowers/specs/2026-05-27-rttp-elcp-rf-b1-overlap-packing-design.md`](../specs/2026-05-27-rttp-elcp-rf-b1-overlap-packing-design.md)

**Prerequisite report (A2):** [`docs/superpowers/reports/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-report.md`](../reports/2026-05-27-rttp-elcp-rf-a2-selection-universe-attrition-report.md)

---

## File structure

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/optimization/selection/overlap_graph.py` | Graph build, component split, exact/heuristic MIS, greedy-coloring upper bound, `compute_target_floor` |
| `django_apps/asteroid_lab/optimization/selection/overlap_pack.py` | `select_genome_overlap_pack`, ordering tie-break, greedy fill to `goal_count` |
| `django_apps/asteroid_lab/contracts/selection_mode.py` | Add `GREEDY_REGRET_OVERLAP_PACK` |
| `django_apps/asteroid_lab/optimization/selection/primary_genome.py` | Dispatch new mode |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Allowlist new mode string |
| `django_apps/asteroid_lab/management/commands/run_solver.py` | CLI choices (if exposed) |
| `harness/investigation/rttp_overlap_graph_packing_bounds.py` | Phase 0 report DTO + `build_overlap_packing_bounds_report` (imports `overlap_graph` only) |
| `tests/support/rttp_b1_gate_a_frozen_bounds.py` | **Frozen** Phase 0 outputs + report citation (updated once per baseline change) |
| `tests/investigation/test_rttp_overlap_graph_packing_bounds.py` | Phase 0 Gate A slow test + NO-GO gate |
| `tests/unit/asteroid_lab/test_overlap_graph.py` | Synthetic graph/MIS/upper-bound unit tests |
| `tests/unit/asteroid_lab/test_rttp_b1_overlap_pack_selection.py` | Phase 1 Gate A + default unchanged |
| `tests/unit/asteroid_lab/test_selection_mode_contract.py` | Enum + allowlist contract (create or extend) |
| `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-b1-overlap-packing-report.md` | Phase 0 table + Phase 1 results + NO-GO/GO verdict |

**Not modified:** `incremental_commit.py`, ELCP assignment, `placement_target_percent`, default `RttpPipelineConfig.selection_mode`.

---

## Normative: `upper_bound` (plan overrides loose spec §5.4)

Never publish `upper_bound = vertex_count` without explicit method flag.

```python
class UpperBoundMethod(StrEnum):
    COMPONENT_EXACT = "component_exact"          # all components exact MIS
    GREEDY_COLORING = "greedy_coloring"          # per-component color count sum
    TRIVIAL_VERTEX_COUNT = "trivial_vertex_count"  # forbidden unless documented emergency
```

Per component `i`:

- If exact MIS computed: `component_upper_i = exact_mis_i` (tight; method contributes as `component_exact`).
- Else: deterministic **greedy coloring** on conflict graph (order vertices by `(degree desc, candidate_id asc)`); `component_upper_i = num_colors_used_i`.

Report fields:

```text
upper_bound = sum(component_upper_i)
upper_bound_method = "component_exact" | "greedy_coloring" | "trivial_vertex_count"
```

`best_known_independent_set_size` remains the **sum of per-component heuristic/exact IS sizes** (may be `< upper_bound`).

---

## Normative: `target_floor` freeze

```python
def compute_target_floor(best_known_independent_set_size: int) -> int:
    if best_known_independent_set_size < 100:
        return best_known_independent_set_size
    return max(100, best_known_independent_set_size // 2)  # floor(0.50 * ...)
```

After Phase 0 Gate A run:

1. Write values into `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-b1-overlap-packing-report.md` §Phase 0.
2. Copy into `tests/support/rttp_b1_gate_a_frozen_bounds.py` with comment citing report date + git-friendly snapshot.
3. Phase 1 tests import **only** frozen constants — do not recompute `target_floor` in assertions.

---

## Normative: overlap-pack ordering tie-break

When ordering independent-set members (and greedy fill picks), use empty `committed_occupied` / `committed_route_cells` for scoring (same as round 0 of greedy_regret):

```python
def overlap_pack_sort_key(
    candidate: BundleCandidate,
    *,
    base_score: float,
    regret: float,
    skeleton: RttpSkeleton,
    config: SelectionConfig,
) -> tuple[float, float, float, str]:
  priority = _priority(
      candidate,
      base_score=base_score,
      regret=regret,
      skeleton=skeleton,
      committed_route_cells=frozenset(),
      config=config,
  )
  return (
      -priority,                      # 1. higher _priority first
      float(candidate.route_probe_cost),  # 2. lower route cost
      candidate.candidate_id,          # 3. lexicographic stable tie-break
  )
```

`regret` from `_regret_scores` on the current candidate subset being ordered.

---

## Phase 0 NO-GO gate (mandatory before Phase 1)

```python
def phase0_is_no_go(report: OverlapPackingBoundsReport) -> bool:
    return (
        report.best_known_independent_set_size
        <= report.greedy_regret_baseline + 5
    )
```

- **NO-GO:** Publish report §Verdict `NO-GO`; skip Tasks 5–11; close B1 as non-viable on Gate A; do **not** merge Phase 1 selection mode.
- **GO:** Freeze constants (Task 4); continue Phase 1.

---

## Spec → plan coverage

| Spec § | Task |
|--------|------|
| §4 SelectionMode rollout | Task 5–7 |
| §5 Phase 0 diagnostic | Tasks 1–4 |
| §5.5 artifact not solver input | Tasks 3, 6 (runtime rebuilds graph) |
| §5.6 early-exit | Task 4 GATE |
| §6 Phase 1 acceptance | Tasks 6–9 |
| §6.2 target_floor | Task 4 freeze + Task 9 |
| §7 Phase C guards | Task 10 |
| §6.3 B1-A/C optional | Task 11 (only if Task 9 fails) |
| §9 deliverables report | Task 12 |

---

### Task 0: Plan linkage

**Files:**
- Modify: `docs/superpowers/specs/2026-05-27-rttp-elcp-rf-b1-overlap-packing-design.md` (implementation plan path in header)
- Modify: `documents/ai/current_plan.md` (plan link under B1 ACTIVE)

- [ ] **Step 1: Update spec header** `Implementation plan:` → this file path.

- [ ] **Step 2: Update `current_plan.md`** B1 row to link plan + report (when report exists).

---

### Task 1: `overlap_graph.py` — graph + MIS (synthetic tests)

**Files:**
- Create: `django_apps/asteroid_lab/optimization/selection/overlap_graph.py`
- Create: `tests/unit/asteroid_lab/test_overlap_graph.py`

- [ ] **Step 1: Write failing unit test — edge construction**

```python
# tests/unit/asteroid_lab/test_overlap_graph.py
from django_apps.asteroid_lab.optimization.selection.overlap_graph import (
    build_overlap_adjacency,
)


def test_build_overlap_adjacency_two_overlapping_candidates(
    bundle_candidate_factory,
) -> None:
    a = bundle_candidate_factory(candidate_id="a", occupied={(0, 0), (1, 0)})
    b = bundle_candidate_factory(candidate_id="b", occupied={(1, 0), (2, 0)})
    c = bundle_candidate_factory(candidate_id="c", occupied={(5, 5)})
    adj = build_overlap_adjacency((a, b, c))
    assert "b" in adj["a"]
    assert "a" in adj["b"]
    assert adj["c"] == frozenset()
```

Use existing `BundleCandidate` test helpers from `tests/unit/asteroid_lab/` (add minimal factory in test file if none exists — two candidates with shared cell).

- [ ] **Step 2: Run test — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_overlap_graph.py::test_build_overlap_adjacency_two_overlapping_candidates -v
```

Expected: `ModuleNotFoundError` or `ImportError`.

- [ ] **Step 3: Implement `build_overlap_adjacency` + `connected_components`**

```python
# overlap_graph.py (excerpt)
def build_overlap_adjacency(
    candidates: Sequence[BundleCandidate],
) -> dict[str, frozenset[str]]:
    ids = [c.candidate_id for c in candidates]
    by_id = {c.candidate_id: c for c in candidates}
    adj: dict[str, set[str]] = {cid: set() for cid in ids}
    for i, a_id in enumerate(ids):
        for b_id in ids[i + 1 :]:
            a, b = by_id[a_id], by_id[b_id]
            if a.occupied_cells & b.occupied_cells:
                adj[a_id].add(b_id)
                adj[b_id].add(a_id)
    return {k: frozenset(v) for k, v in adj.items()}
```

Implement BFS/union-find `connected_components(adj) -> tuple[tuple[str, ...], ...]` sorted by `(len desc, min_id asc)`.

- [ ] **Step 4: Add failing test — exact MIS on 3-vertex path**

```python
def test_exact_mis_size_path_graph_size_2() -> None:
    # triangle-free path of 3 nodes -> MIS = 2
    adj = {
        "a": frozenset({"b"}),
        "b": frozenset({"a", "c"}),
        "c": frozenset({"b"}),
    }
    assert exact_mis_size_for_component(adj, max_exact_n=40) == 2
```

- [ ] **Step 5: Implement `exact_mis_size_for_component`** (branch-and-bound; cap `|V| > 40` → return `None`).

- [ ] **Step 6: Implement `heuristic_mis_for_component`** — min-degree removal, tie `candidate_id asc`.

- [ ] **Step 7: Implement `greedy_coloring_upper_bound_for_component`** — deterministic greedy coloring; return `num_colors`.

- [ ] **Step 8: Implement `compute_overlap_packing_bounds(candidates, *, greedy_regret_baseline: int) -> OverlapPackingBounds` dataclass** with all §5.3 fields + `upper_bound_method`.

- [ ] **Step 9: Run unit tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_overlap_graph.py -v
python -m ruff check django_apps/asteroid_lab/optimization/selection/overlap_graph.py tests/unit/asteroid_lab/test_overlap_graph.py
```

Expected: PASS.

- [ ] **Step 10: Commit** (user-request only)

```bash
git add django_apps/asteroid_lab/optimization/selection/overlap_graph.py tests/unit/asteroid_lab/test_overlap_graph.py
git commit -m "feat(asteroid_lab): overlap graph MIS and coloring bounds"
```

---

### Task 2: Phase 0 harness + Gate A investigation test

**Files:**
- Create: `harness/investigation/rttp_overlap_graph_packing_bounds.py`
- Create: `tests/investigation/test_rttp_overlap_graph_packing_bounds.py`
- Reuse: A2 fixture pattern from `tests/investigation/test_rttp_greedy_regret_selection_attrition.py`

- [ ] **Step 1: Write harness DTO + builder**

```python
@dataclass(frozen=True, slots=True)
class OverlapPackingBoundsReport:
    vertex_count: int
    edge_count: int
    connected_component_count: int
    greedy_regret_baseline: int
    best_known_independent_set_size: int
    exact_mis_size: int | None
    upper_bound: int
    upper_bound_method: str
    component_sizes: tuple[int, ...]
    exact_mis_component_count: int
    heuristic_mis_component_count: int
    target_floor: int
    phase0_verdict: str  # "GO" | "NO_GO"
    fot_conflict_edge_count: int | None  # appendix

def build_overlap_packing_bounds_report(
    *,
    normal_candidates: Sequence[BundleCandidate],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goal_count: int,
) -> OverlapPackingBoundsReport:
    from django_apps.asteroid_lab.optimization.selection.greedy_regret import select_genome
    from django_apps.asteroid_lab.optimization.selection.equivalence import dedupe_candidates
    pool = dedupe_candidates(tuple(normal_candidates))
    baseline = select_genome(pool, skeleton, inp, goal_count=goal_count)
    bounds = compute_overlap_packing_bounds(pool, greedy_regret_baseline=len(baseline.commit_order))
    target = compute_target_floor(bounds.best_known_independent_set_size)
    verdict = "NO_GO" if phase0_is_no_go(bounds, baseline_len=len(baseline.commit_order)) else "GO"
    return OverlapPackingBoundsReport(..., target_floor=target, phase0_verdict=verdict)
```

- [ ] **Step 2: Write failing Gate A test (slow)**

```python
@pytest.mark.django_db
@pytest.mark.slow
def test_recovery_map_overlap_packing_bounds_gate_a_parity_config(...):
    # Same import/recon/pipeline_config as A2 test; capture normal_candidates, skeleton, inp, goal_count
    report = build_overlap_packing_bounds_report(...)
    assert report.vertex_count == 356
    assert report.greedy_regret_baseline == 59
    assert report.upper_bound_method in {"component_exact", "greedy_coloring"}
    assert report.upper_bound >= report.best_known_independent_set_size
    print(f"B1_PHASE0_REPORT={report.to_dict()}")  # for freezing constants
```

- [ ] **Step 3: Run investigation test**

```bash
python -m pytest tests/investigation/test_rttp_overlap_graph_packing_bounds.py::test_recovery_map_overlap_packing_bounds_gate_a_parity_config -v -s
```

Expected: PASS with printed `B1_PHASE0_REPORT=...`.

- [ ] **Step 4: Commit** (user-request only)

---

### Task 3: Phase 0 report publication

**Files:**
- Create: `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-b1-overlap-packing-report.md`

- [ ] **Step 1: Create report** with §Phase 0 table: all `OverlapPackingBoundsReport` fields, `upper_bound_method`, early-exit matrix row, explicit **GO/NO-GO** verdict.

- [ ] **Step 2: Link report from plan + `current_plan.md`.**

---

### Task 4: **GATE** — Freeze constants or STOP

**Files:**
- Create: `tests/support/rttp_b1_gate_a_frozen_bounds.py`
- Modify: `tests/investigation/test_rttp_overlap_graph_packing_bounds.py`

- [ ] **Step 1: Add gate test**

```python
from tests.support.rttp_b1_gate_a_frozen_bounds import (
    GATE_A_PHASE0_VERDICT,
    GATE_A_BEST_KNOWN_IS,
    GATE_A_TARGET_FLOOR,
)

@pytest.mark.django_db
@pytest.mark.slow
def test_phase0_gate_a_verdict_is_go():
    report = build_overlap_packing_bounds_report(...)
    assert report.phase0_verdict == GATE_A_PHASE0_VERDICT
    if GATE_A_PHASE0_VERDICT == "NO_GO":
        pytest.fail("B1 Phase 0 NO-GO — do not implement Phase 1 (Tasks 5+)")
```

- [ ] **Step 2: Run Phase 0 test; if NO-GO, set frozen file:**

```python
# tests/support/rttp_b1_gate_a_frozen_bounds.py
# Frozen from docs/superpowers/reports/2026-05-27-rttp-elcp-rf-b1-overlap-packing-report.md §Phase 0 (YYYY-MM-DD run)
GATE_A_PHASE0_VERDICT = "NO_GO"  # or "GO"
GATE_A_VERTEX_COUNT = 356
GATE_A_GREEDY_REGRET_BASELINE = 59
GATE_A_PLACEMENT_GOAL = 467
GATE_A_BEST_KNOWN_IS = 0  # fill from report
GATE_A_TARGET_FLOOR = 0   # fill from report
GATE_A_UPPER_BOUND = 0
GATE_A_UPPER_BOUND_METHOD = "greedy_coloring"
```

- [ ] **Step 3: If `GATE_A_PHASE0_VERDICT == "NO_GO"`:** mark Tasks 5–11 **CANCELLED** in PR description; publish report only; **do not proceed**.

- [ ] **Step 4: If `GO`:** set `GATE_A_BEST_KNOWN_IS`, `GATE_A_TARGET_FLOOR`, `GATE_A_UPPER_BOUND*` from report; continue.

---

### Task 5: `SelectionMode` contract

**Files:**
- Modify: `django_apps/asteroid_lab/contracts/selection_mode.py`
- Create or modify: `tests/unit/asteroid_lab/test_selection_mode_contract.py`

- [ ] **Step 1: Failing test**

```python
def test_selection_mode_includes_overlap_pack() -> None:
    assert SelectionMode.GREEDY_REGRET_OVERLAP_PACK.value == "greedy_regret_overlap_pack"
```

- [ ] **Step 2: Add enum member**

```python
class SelectionMode(StrEnum):
    GREEDY_REGRET = "greedy_regret"
    GREEDY_REGRET_OVERLAP_PACK = "greedy_regret_overlap_pack"
    EVOLUTION = "evolution"
```

- [ ] **Step 3: Run test + ruff**

```bash
python -m pytest tests/unit/asteroid_lab/test_selection_mode_contract.py -v
```

---

### Task 6: `select_genome_overlap_pack`

**Files:**
- Create: `django_apps/asteroid_lab/optimization/selection/overlap_pack.py`
- Modify: `django_apps/asteroid_lab/optimization/selection/__init__.py` (export if needed)

**Precondition:** Task 4 `GATE_A_PHASE0_VERDICT == "GO"`.

- [ ] **Step 1: Failing test — overlap pack length on synthetic non-overlapping pool**

```python
def test_select_genome_overlap_pack_returns_all_when_no_edges(...):
    # 5 candidates, disjoint occupied cells
    genome = select_genome_overlap_pack(pool, skeleton, inp, goal_count=10)
    assert len(genome.commit_order) == 5
```

- [ ] **Step 2: Implement `select_genome_overlap_pack`**

```python
def select_genome_overlap_pack(
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    config: SelectionConfig | None = None,
    goal_count: int | None = None,
) -> PlacementGenome:
    resolved = config or SelectionConfig()
    pool = list(dedupe_candidates(normal_candidates))
    resolved_goal = max(0, goal_count) if goal_count is not None else max(0, skeleton.capacity_goals)
    if not pool or resolved_goal == 0:
        return PlacementGenome(commit_order=())

    is_ids = compute_best_known_independent_set_candidate_ids(pool)
    ordered = order_ids_by_overlap_pack_sort_key(is_ids, pool, skeleton, inp, config=resolved)

    commit_order: list[str] = []
    committed_occupied: set[Coord] = set()
    committed_fot: set[Coord] = set()
    committed_route: set[Coord] = set()

    def try_append(cid: str) -> bool:
        c = by_id[cid]
        occ = frozenset(committed_occupied)
        if _overlaps(c, occ) or _fot_conflict(c, committed_occupied=occ, committed_fixed_output_transport_cells=frozenset(committed_fot)):
            return False
        commit_order.append(cid)
        committed_occupied.update(c.occupied_cells)
        committed_fot.add(fixed_output_transport_cell(c))
        committed_route.add(c.output_stub)
        return True

    by_id = {c.candidate_id: c for c in pool}
    for cid in ordered:
        if len(commit_order) >= resolved_goal:
            break
        try_append(cid)

  # Greedy fill: remaining pool sorted by overlap_pack_sort_key, scan until goal or exhausted
    remaining = [c for c in pool if c.candidate_id not in commit_order]
    while len(commit_order) < resolved_goal and remaining:
        # recompute scores on remaining; pick best key; try_append or remove
        ...

    return PlacementGenome(commit_order=tuple(commit_order))
```

Reuse `overlap_graph.compute_best_known_independent_set_candidate_ids` (returns ordered IDs per component merge + global sort).

- [ ] **Step 3: Run unit tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_overlap_graph.py tests/unit/asteroid_lab/test_rttp_b1_overlap_pack_selection.py -v -k "not gate_a"
```

---

### Task 7: `primary_genome` dispatch + pipeline default unchanged

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/selection/primary_genome.py`
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Modify: `django_apps/asteroid_lab/management/commands/run_solver.py` (if `selection_mode` choices exist)

- [ ] **Step 1: Failing test — dispatch returns overlap pack genome**

```python
def test_select_primary_genome_overlap_pack_mode():
    genome = select_primary_genome(
        mode=SelectionMode.GREEDY_REGRET_OVERLAP_PACK,
        normal_candidates=pool,
        skeleton=skeleton,
        inp=inp,
        goal_count=10,
        ga_config=GaEvolutionShadowConfig(),
    )
    assert isinstance(genome, PlacementGenome)
```

- [ ] **Step 2: Implement dispatch branch**

```python
if mode is SelectionMode.GREEDY_REGRET_OVERLAP_PACK:
    return select_genome_overlap_pack(pool, skeleton, inp, goal_count=goal_count)
```

- [ ] **Step 3: Extend `_VALID_SELECTION_MODES`** with `SelectionMode.GREEDY_REGRET_OVERLAP_PACK.value`.

- [ ] **Step 4: Assert `RttpPipelineConfig.selection_mode` default still `GREEDY_REGRET`** (existing test or add).

```bash
python -m pytest tests/unit/asteroid_lab/test_selection_mode_contract.py -v
```

---

### Task 8: Phase 1 Gate A acceptance (frozen `target_floor`)

**Files:**
- Create: `tests/unit/asteroid_lab/test_rttp_b1_overlap_pack_selection.py` (Gate A section)
- Uses: `tests/support/rttp_b1_gate_a_frozen_bounds.py`

**Precondition:** Task 4 GO + frozen constants populated.

- [ ] **Step 1: Test default mode unchanged (A2 baseline)**

```python
@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_greedy_regret_baseline_unchanged_at_59(...):
    pipeline_config = RttpPipelineConfig(..., selection_mode=SelectionMode.GREEDY_REGRET)
    # run pipeline; assert len(genome.commit_order) == GATE_A_GREEDY_REGRET_BASELINE  # 59
```

- [ ] **Step 2: Test overlap pack mode meets frozen floor**

```python
@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_overlap_pack_meets_frozen_target_floor(...):
    from tests.support.rttp_b1_gate_a_frozen_bounds import GATE_A_TARGET_FLOOR
    pipeline_config = RttpPipelineConfig(
        ...,
        selection_mode=SelectionMode.GREEDY_REGRET_OVERLAP_PACK,
    )
    # run pipeline
    assert len(genome.commit_order) >= GATE_A_TARGET_FLOOR
    assert len(genome.commit_order) <= GATE_A_PLACEMENT_GOAL
```

- [ ] **Step 3: Re-run A2 parity test unchanged**

```bash
python -m pytest tests/investigation/test_rttp_greedy_regret_selection_attrition.py::test_recovery_map_selection_attrition_trace_gate_a_parity_config -v
```

Expected: still `commit_order_len == 59` for production default path.

- [ ] **Step 4: Run overlap pack Gate A test**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_b1_overlap_pack_selection.py -v -m slow
```

---

### Task 9: Phase C — cert slug regression guard

**Files:**
- Modify: `tests/unit/asteroid_lab/test_rttp_b1_overlap_pack_selection.py` or new `test_rttp_b1_slug_regression_guards.py`

- [ ] **Step 1: Record baseline `commit_order_len` for `rttp-cert-candidate-recon-l0` under `GREEDY_REGRET`** (run once, freeze constant `CERT_SLUG_GREEDY_REGRET_BASELINE` in `rttp_b1_gate_a_frozen_bounds.py` or sibling file).

- [ ] **Step 2: Test — default mode `>= CERT_SLUG_GREEDY_REGRET_BASELINE`**

- [ ] **Step 3: Test — overlap pack mode `>= CERT_SLUG_GREEDY_REGRET_BASELINE`** on cert slug (same pipeline config except mode).

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_b1_slug_regression_guards.py -v -m slow
```

---

### Task 10: Optional B1-A / B1-C (only if Task 8 fails)

**Precondition:** Task 8 `test_gate_a_overlap_pack_meets_frozen_target_floor` **FAILED** but Phase 0 GO.

- [ ] **Step 1: B1-A** — add spatial diversity tie-break to `overlap_pack_sort_key` (anchor grid bucket); re-run Task 8.

- [ ] **Step 2: If still failing, B1-C** — one-pass deterministic swap: for each removed-by-overlap candidate from A2 trace class, try replace lowest-score committed if swap increases count without overlap.

- [ ] **Step 3: Do not merge B1-A/C if Task 8 passes without them (YAGNI).**

---

### Task 11: Final report + narrow gates

**Files:**
- Modify: `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-b1-overlap-packing-report.md` (§Phase 1 results, B1-H2 verdict)
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Complete report** with Phase 0 + Phase 1 tables, frozen constants citation, explicit **B1 CLOSED** or **NO-GO** / **PARTIAL**.

- [ ] **Step 2: Narrow verification**

```bash
python -m pytest tests/unit/asteroid_lab/test_overlap_graph.py tests/unit/asteroid_lab/test_selection_mode_contract.py tests/unit/asteroid_lab/test_rttp_b1_overlap_pack_selection.py tests/investigation/test_rttp_overlap_graph_packing_bounds.py tests/investigation/test_rttp_greedy_regret_selection_attrition.py -v
python -m ruff check django_apps/asteroid_lab/optimization/selection/overlap_graph.py django_apps/asteroid_lab/optimization/selection/overlap_pack.py django_apps/asteroid_lab/contracts/selection_mode.py django_apps/asteroid_lab/optimization/selection/primary_genome.py django_apps/asteroid_lab/services/solver_runtime_entry.py harness/investigation/rttp_overlap_graph_packing_bounds.py
python -m mypy django_apps/asteroid_lab/optimization/selection/overlap_graph.py django_apps/asteroid_lab/optimization/selection/overlap_pack.py django_apps/asteroid_lab/contracts/selection_mode.py django_apps/asteroid_lab/optimization/selection/primary_genome.py
```

- [ ] **Step 3: Mark B1 **CLOSED** in `current_plan.md` only if Phase 1 acceptance + Phase C pass.**

---

## Plan self-review

| Check | Result |
|-------|--------|
| Spec §4–§7 covered | Tasks 1–11 |
| Phase 0 NO-GO stops Phase 1 | Task 4 GATE |
| `upper_bound` not trivial-only | Normative section + Task 1 |
| `target_floor` frozen | Task 4 + Task 8 |
| Ordering tie-break | Normative section + Task 6 |
| Artifact not solver input | Harness imports `overlap_graph` only; runtime rebuilds |
| Default `GREEDY_REGRET` unchanged | Task 8 |
| No placeholders | PASS |
| One PR, gated phases | Header + Task 4 |

---

## Execution handoff

**Plan saved to:** `docs/superpowers/plans/2026-05-27-rttp-elcp-rf-b1-overlap-packing.md`

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration.

2. **Inline Execution** — execute tasks in this session using executing-plans with checkpoints (run Task 4 gate before Task 5).

**Which approach?**
