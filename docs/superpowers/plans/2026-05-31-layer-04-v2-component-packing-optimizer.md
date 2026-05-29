# Layer 04 v2 — Component-Local Packing Optimizer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace L4 sequential greedy with component-local exact packing (|C|≤20) + greedy fallback, maximizing `set_score` per conflict component while preserving L3 estimate / L4 install boundary.

**Architecture:** Build overlap graph on `occupied_cells`, partition connected components, run branch-and-bound MWIS per small component, materialize winners with runtime budget checks, emit `PACKING_SET_LOSER` rejections and `Layer04PackingObservability` (greedy baseline on cloned budget only).

**Tech Stack:** Python 3.12+ · Django `django_apps/asteroid_lab` layers · pytest · ruff · mypy (`django_apps config src`)

**Spec:** [`2026-05-31-layer-04-v2-component-packing-optimizer-design.md`](../specs/2026-05-31-layer-04-v2-component-packing-optimizer-design.md) (**APPROVED**)

---

## Execution contract

```text
Commit: ONLY when the user explicitly requests git commit.
```

- [ ] **Checkpoint** — Record pytest/ruff/mypy paths; no commit unless user asks.

---

## Acceptance (must all pass)

```text
§0: L3 does not import overlay builder; L4 does not re-probe.
§5.2: Logical winner computed first; budget applies at materialization only.
§7.2: component_id == f"component_{ordinal:04d}" (no hash in contract).
§7.3: greedy_baseline_* uses cloned LayerBudgetContext; never mutates runtime ctx.
§7.4: EXACT_PACK losers have packing_rejection_kind=PACKING_SET_LOSER, reason=PHYSICAL_OVERLAP.
§9.1: Synthetic packing-density selects B..F (gain 20), not blocker A.
§9.2a/9.2b: selected_count and route_cost tie-breaks.
§9.3: |C|>20 uses GREEDY_FALLBACK on component subset only.
§9.5: corner W/S still selects S (gain 9) over W (gain 6).
```

---

## File map

| File | Responsibility |
|------|----------------|
| `layers/contracts/rim_placement.py` | `RimSelectionStrategy`, `RimPackingRejectionKind`, observability DTOs, extend `RimPlacementRejection`, `Layer04RimPlacementResult.packing_observability` |
| `layers/layer_04_rim_bundle_placement/set_score.py` | `set_score_tuple`, aggregates, compare |
| `layers/layer_04_rim_bundle_placement/conflict_graph.py` | `occupied_cells`, edges, components, `component_id` |
| `layers/layer_04_rim_bundle_placement/exact_pack.py` | Branch-and-bound MWIS for \|C\|≤20 |
| `layers/layer_04_rim_bundle_placement/select_v2.py` | Orchestration, materialization, rejections, observability |
| `layers/layer_04_rim_bundle_placement/select.py` | **Keep** v1 greedy (fallback subset + baseline) |
| `layers/layer_04_rim_bundle_placement/run.py` | Call `select_non_overlapping_candidates_v2` |
| `replay/layer04_segment.py` | Project `packing_observability` fields (optional keys) |
| `replay/event_types.py` | Register new metadata keys if emitted |
| `tests/unit/asteroid_lab/layers/fixtures/layer_04_packing_density.py` | §9.1 star graph |
| `tests/unit/asteroid_lab/layers/fixtures/layer_04_tiebreak_sets.py` | §9.2a / §9.2b |
| `tests/unit/asteroid_lab/layers/fixtures/layer_04_large_component.py` | §9.3 \|C\|>20 |
| `tests/unit/asteroid_lab/layers/test_layer_04_component_packing.py` | Core v2 tests |
| `tests/unit/asteroid_lab/layers/test_layer_04_packing_observability.py` | Baseline clone budget |
| `docs/superpowers/specs/2026-05-28-layer-04-rim-bundle-placement-design.md` | §3.4 pointer → v2 spec |

---

### Task 1: Contract enums and DTOs

**Files:**
- Modify: `django_apps/asteroid_lab/layers/contracts/rim_placement.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement_contracts.py` (create)

- [ ] **Step 1: Failing test — component_id format**

```python
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    RimComponentSelectionRecord,
    RimSelectionStrategy,
)


def test_component_id_is_ordinal_string_only() -> None:
    rec = RimComponentSelectionRecord(
        component_id="component_0003",
        component_sort_key=(11, -6, "layer_03:miner:a"),
        node_count=5,
        selection_strategy=RimSelectionStrategy.EXACT_PACK,
        selected_candidate_ids=("a",),
        materialized_candidate_ids=("a",),
        total_effective_mining_gain=4,
        selected_count=1,
    )
    assert rec.component_id == "component_0003"
```

- [ ] **Step 2: Run — FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_rim_placement_contracts.py::test_component_id_is_ordinal_string_only -v
```

- [ ] **Step 3: Add enums and dataclasses**

```python
class RimSelectionStrategy(StrEnum):
    EXACT_PACK = "EXACT_PACK"
    GREEDY_FALLBACK = "GREEDY_FALLBACK"


class RimPackingRejectionKind(StrEnum):
    PACKING_SET_LOSER = "PACKING_SET_LOSER"
    BUDGET_INTERRUPTED = "BUDGET_INTERRUPTED"
    NON_SUCCEEDED_PROBE = "NON_SUCCEEDED_PROBE"
```

Extend `RimPlacementRejection` with optional `packing_component_id`, `packing_rejection_kind`, `winner_selected_due_to_higher_set_score`.

Add `RimComponentSelectionRecord`, `Layer04PackingObservability` per spec §7.

Extend `Layer04RimPlacementResult` with `packing_observability: Layer04PackingObservability | None = None`.

Update `build_layer04_rim_placement_result(..., packing_observability=None)` — default `None` for empty result.

- [ ] **Step 4: Run — PASS**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_rim_placement_contracts.py -v
```

- [ ] **Step 5: ruff**

```bash
python -m ruff check django_apps/asteroid_lab/layers/contracts/rim_placement.py tests/unit/asteroid_lab/layers/test_layer_04_rim_placement_contracts.py
```

---

### Task 2: `set_score` module

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/set_score.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_04_set_score.py`

- [ ] **Step 1: Failing test — lexicographic compare**

```python
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.set_score import (
    compare_set_scores,
    set_score_tuple,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_set_score_prefers_higher_count_at_equal_gain() -> None:
    a = succeeded_probe_at((0, 0), equivalence_key="a", mining=frozenset({(0, 0), (1, 0)}))
    b = succeeded_probe_at((5, 0), equivalence_key="b", mining=frozenset({(5, 0)}))
    c = succeeded_probe_at((6, 0), equivalence_key="c", mining=frozenset({(6, 0)}))
  # Build two sets manually in test helper — see Task 8 for full fixture
    score_two = set_score_tuple(entries=(a, b))
    score_three = set_score_tuple(entries=(a, b, c))
    assert compare_set_scores(score_three, score_two) > 0
```

- [ ] **Step 2: Run — FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_set_score.py -v
```

- [ ] **Step 3: Implement**

```python
def set_score_tuple(
    *,
    entries: tuple[RouteProbedBundleCandidate, ...],
) -> tuple[int, int, float, float, tuple[str, ...]]:
    total_gain = sum(effective_mining_gain(e.candidate) for e in entries)
    count = len(entries)
    total_route = sum(route_cost_for_sort(e) for e in entries)
    total_conn = sum(connector_goal_distance(e) for e in entries)
    ids = tuple(sorted(e.candidate.candidate_id for e in entries))
    return (total_gain, count, -total_route, -total_conn, ids)


def compare_set_scores(a: tuple, b: tuple) -> int:
    return (a > b) - (a < b)  # lexicographic on stored tuple with negated costs
```

Use spec §4 ordering: negate costs in tuple so ascending tuple compare = maximize gain, count, minimize costs.

- [ ] **Step 4: Run — PASS**

---

### Task 3: Conflict graph

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/conflict_graph.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_04_conflict_graph.py`

- [ ] **Step 1: Failing test — edges on stub overlap**

```python
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.conflict_graph import (
    build_conflict_components,
    occupied_cells_for_entry,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_occupied_cells_includes_transport_stub() -> None:
    e = succeeded_probe_at((1, 1), mining=frozenset({(1, 1)}), transport=frozenset({(2, 1)}))
    assert (2, 1) in occupied_cells_for_entry(e)


def test_shared_stub_creates_edge() -> None:
    e1 = succeeded_probe_at((1, 1), equivalence_key="e1", transport=frozenset({(9, 9)}))
    e2 = succeeded_probe_at((5, 5), equivalence_key="e2", transport=frozenset({(9, 9)}))
    components = build_conflict_components((e1, e2))
    assert len(components) == 1
    assert components[0].node_count == 2
    assert components[0].component_id == "component_0000"
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement**

```python
@dataclass(frozen=True, slots=True)
class ConflictComponent:
    component_id: str
    component_sort_key: tuple[int, int, str]
    entries: tuple[RouteProbedBundleCandidate, ...]

    @property
    def node_count(self) -> int:
        return len(self.entries)
```

- Union-find or BFS for connected components.
- Sort components by `component_sort_key` per spec §3.3.
- Assign `component_id = f"component_{ordinal:04d}"`.

- [ ] **Step 4: Run — PASS**

---

### Task 4: Exact pack (branch-and-bound)

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/exact_pack.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_04_exact_pack.py`

**Constants:**

```python
MAX_EXACT_COMPONENT_SIZE = 20
MAX_BRANCH_NODES = 500_000  # guardrail; raise in test if too low for fixtures
```

- [ ] **Step 1: Failing test — independent set on 3-node line**

Build three entries where only non-adjacent pairs are compatible (use disjoint mining cells).

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement `select_max_set_score_independent_set`**

Algorithm sketch (normative for plan):

```python
def select_max_set_score_independent_set(
    entries: tuple[RouteProbedBundleCandidate, ...],
) -> tuple[RouteProbedBundleCandidate, ...]:
    n = len(entries)
    # conflict_masks[i] = bitmask of neighbors j (j < i) for pruning
    # DFS with branch: include i if compatible with current mask
    # Bound: optimistic_gain_upper_bound from remaining nodes
    ...
```

- MUST prune when `current_score` + `upper_bound < best_score`.
- MUST NOT iterate all `2^n` without pruning (assert branch count in tests for n=20 path uses pruning — smoke test with n≤12 full verify).

- [ ] **Step 4: Run — PASS**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_exact_pack.py -v
```

---

### Task 5: `select_v2` orchestration

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/select_v2.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_04_select_v2_budget.py`

- [ ] **Step 1: Failing test — budget does not mutate baseline ctx**

```python
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select_v2 import (
    OBSERVABILITY_BASELINE_BUDGET_MS,
    compute_greedy_baseline_observability,
)


def test_greedy_baseline_uses_fresh_budget_context() -> None:
    runtime = LayerBudgetContext.from_budget_ms(1)  # 1ms — will exhaust quickly
    entries = (...)  # minimal 2-entry non-overlap
    obs = compute_greedy_baseline_observability(
        normal_candidates=entries,
        observability_budget_ms=OBSERVABILITY_BASELINE_BUDGET_MS,
    )
    assert runtime.remaining_budget_ms() >= 0  # unchanged by baseline path
    assert obs.greedy_baseline_total_gain is not None or obs.greedy_baseline_skipped_reason
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement `select_non_overlapping_candidates_v2`**

Return type:

```python
@dataclass(frozen=True, slots=True)
class Layer04SelectionOutcome:
    selected_entries: tuple[RouteProbedBundleCandidate, ...]
    rejected: tuple[RimPlacementRejection, ...]
    packing_observability: Layer04PackingObservability
```

Flow:

1. Partition failed probes → `NON_SUCCEEDED_PROBE`.
2. `build_conflict_components(succeeded)`.
3. Per component: `EXACT_PACK` or `GREEDY_FALLBACK` → `logical_winner_entries`.
4. Materialize in global order; check `budget_ctx.remaining_budget_ms()` before each accept.
5. On budget stop: `BUDGET_INTERRUPTED` for queued materializations; set `budget_limited`, `budget_interrupted_component_id`.
6. Rejections for losers in fully computed components: `PACKING_SET_LOSER` + `PHYSICAL_OVERLAP`.
7. Call `compute_greedy_baseline_observability` with `LayerBudgetContext.from_budget_ms(OBSERVABILITY_BASELINE_BUDGET_MS)` only.

Materialization order: `sorted(logical_winner_entries, key=candidate_sort_key)`.

- [ ] **Step 4: Run — PASS**

---

### Task 6: Wire `run.py`

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/run.py`
- Modify: `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py`

- [ ] **Step 1: Switch import to v2**

```python
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.select_v2 import (
    select_non_overlapping_candidates_v2,
)

def run_layer_04_rim_bundle_placement(...):
    ...
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=candidate_set.normal_candidates,
        budget_ctx=budget_ctx,
    )
    placements = tuple(build_rim_bundle_placement(e) for e in outcome.selected_entries)
    ...
    return build_layer04_rim_placement_result(
        ...,
        packing_observability=outcome.packing_observability,
    )
```

- [ ] **Step 2: Run existing L4 tests — fix regressions**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py tests/unit/asteroid_lab/layers/test_layer_04_mining_first_selection.py -v
```

Expect corner W/S and overlap tests to pass via v2 exact pack on small components.

- [ ] **Step 3: ruff + mypy**

```bash
python -m ruff check django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/
python -m mypy django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/
```

---

### Task 7: §9.1 Packing-density fixture

**Files:**
- Create: `tests/unit/asteroid_lab/layers/fixtures/layer_04_packing_density.py`
- Modify: `tests/unit/asteroid_lab/layers/test_layer_04_component_packing.py`

- [ ] **Step 1: Build star graph entries**

```python
def packing_density_probes() -> tuple[RouteProbedBundleCandidate, ...]:
    blocker_a = succeeded_probe_at(
        (2, 2),
        equivalence_key="blocker_a",
        mining=frozenset({(0, 2), (1, 2), (2, 2), (3, 2)}),  # horizontal bar
        output_dir=Direction.E,
    )
    verticals = []
    for x in (0, 1, 3, 4, 5):
        verticals.append(
            succeeded_probe_at(
                (x, 0),
                equivalence_key=f"vert_{x}",
                mining=frozenset({(x, y) for y in range(5)}),
                output_dir=Direction.S,
            )
        )
    return (blocker_a, *verticals)
```

Adjust coordinates so: `blocker_a` overlaps every vertical; verticals pairwise disjoint; all in one component.

- [ ] **Step 2: Failing test**

```python
def test_packing_density_selects_vertical_bundle_not_blocker() -> None:
    entries = packing_density_probes()
    outcome = select_non_overlapping_candidates_v2(
        normal_candidates=entries,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
    )
    selected_ids = {e.candidate.candidate_id for e in outcome.selected_entries}
    assert "blocker_a" not in {e.candidate.equivalence_key for e in outcome.selected_entries}
    assert outcome.packing_observability.selected_total_gain == 20
```

- [ ] **Step 3: Tune footprints until overlap graph matches spec — PASS**

---

### Task 8: §9.2 Tie-break fixtures

**Files:**
- Create: `tests/unit/asteroid_lab/layers/fixtures/layer_04_tiebreak_sets.py`
- Modify: `tests/unit/asteroid_lab/layers/test_layer_04_component_packing.py`

- [ ] **Step 1: 9.2a — equal gain, different count** (two competing maximal sets in one component)

- [ ] **Step 2: 9.2b — equal gain and count, different route_cost**

```python
def test_set_score_prefers_lower_route_cost_at_equal_gain_and_count() -> None:
    # Set Q: two probes route_cost=1 each; Set P: route_cost=50 each
    # Only one maximal set fits in component — assert Q selected
```

- [ ] **Step 3: Run**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_component_packing.py -v
```

---

### Task 9: §9.3 Large-component fallback

**Files:**
- Create: `tests/unit/asteroid_lab/layers/fixtures/layer_04_large_component.py`
- Modify: `tests/unit/asteroid_lab/layers/test_layer_04_component_packing.py`

- [ ] **Step 1: Build 21 mutually non-overlapping entries in one component** (shared mega-stub — single clique of 21)

Use one shared `transport=frozenset({(0, 0)})` and distinct mining cells so all 21 share stub → one component with `node_count=21`.

- [ ] **Step 2: Assert `GREEDY_FALLBACK`**

```python
def test_large_component_uses_greedy_fallback() -> None:
    ...
    rec = outcome.packing_observability.component_records[0]
    assert rec.selection_strategy == RimSelectionStrategy.GREEDY_FALLBACK
```

---

### Task 10: §9.5 Corner W/S regression

**Files:**
- Modify: `tests/unit/asteroid_lab/layers/test_layer_04_mining_first_selection.py`

- [ ] **Step 1: Run unchanged assertions through `run_layer_04` or `select_v2`**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_mining_first_selection.py -v
```

- [ ] **Step 2: Add `packing_rejection_kind` assertion on W loser**

```python
assert rejected_w.packing_rejection_kind == RimPackingRejectionKind.PACKING_SET_LOSER
```

---

### Task 11: §9.4 Run #286 derived fixture (optional but recommended)

**Files:**
- Create: `tests/fixtures/layer04/run286_strip_component.json` (frozen candidate footprints from project 23)
- Create: `tests/unit/asteroid_lab/layers/test_layer_04_run286_strip_regression.py`

- [ ] **Step 1: Script once to export probe entries** (dev-only; commit JSON)

- [ ] **Step 2: Assert**

```python
def test_run286_strip_component_beats_greedy_baseline() -> None:
    entries = load_run286_strip_entries()
    outcome = select_non_overlapping_candidates_v2(...)
    assert outcome.packing_observability.selected_total_gain >= (
        outcome.packing_observability.greedy_baseline_total_gain or 0
    )
```

Do **not** assert three overlapping S seeds all selected.

---

### Task 12: Replay projection

**Files:**
- Modify: `django_apps/asteroid_lab/replay/layer04_segment.py`
- Modify: `django_apps/asteroid_lab/replay/event_types.py` (if new keys)
- Test: `tests/unit/asteroid_lab/replay/test_layer04_segment.py`

- [ ] **Step 1: Pass `packing_observability` into segment builder from assembler**

- [ ] **Step 2: Add optional metadata on `layer04_rim_placement_complete`**

```python
"budget_limited": obs.budget_limited,
"selected_total_gain": obs.selected_total_gain,
"greedy_baseline_total_gain": obs.greedy_baseline_total_gain,
```

- [ ] **Step 3: pytest replay segment**

```bash
python -m pytest tests/unit/asteroid_lab/replay/test_layer04_segment.py -v
```

---

### Task 13: Layer boundary + doc pointers

**Files:**
- Modify: `docs/superpowers/specs/2026-05-28-layer-04-rim-bundle-placement-design.md` (§3.4 superseded → v2 link)
- Modify: `docs/superpowers/specs/2026-05-30-outer-rim-direction-arbitration-design.md` (§8 promoted note)
- Create: `tests/unit/asteroid_lab/layers/test_layer_03_l4_boundary.py`

- [ ] **Step 1: Boundary test**

```python
def test_layer03_package_does_not_import_provisional_overlay_builder() -> None:
    import django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.run as l3_run
    src = inspect.getsource(l3_run)
    assert "build_provisional_overlay" not in src
```

---

### Task 14: Full narrow gate

- [ ] **Run**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_04_component_packing.py tests/unit/asteroid_lab/layers/test_layer_04_select_v2_budget.py tests/unit/asteroid_lab/layers/test_layer_04_conflict_graph.py tests/unit/asteroid_lab/layers/test_layer_04_exact_pack.py tests/unit/asteroid_lab/layers/test_layer_04_set_score.py tests/unit/asteroid_lab/layers/test_layer_04_mining_first_selection.py tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py -v
python -m ruff check django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/ django_apps/asteroid_lab/layers/contracts/rim_placement.py
python -m mypy django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/ django_apps/asteroid_lab/layers/contracts/rim_placement.py
```

---

## Plan self-review (spec coverage)

| Spec section | Task |
|--------------|------|
| §0 L3/L4 boundary | Task 13 |
| §3 conflict graph | Task 3 |
| §4 set_score | Task 2, 8 |
| §5.1–5.5 algorithm | Task 4, 5, 9 |
| §5.2 budget materialization | Task 5 |
| §7 DTOs | Task 1, 5 |
| §7.3 baseline budget | Task 5 |
| §7.4 PACKING_SET_LOSER | Task 1, 5, 10 |
| §8 replay | Task 12 |
| §9.1–9.6 tests | Tasks 7–11, 13 |
| §10 outer-rim §8 | Doc pointer Task 13 |

No `TBD` placeholders in task steps.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-31-layer-04-v2-component-packing-optimizer.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session, `executing-plans` checkpoints

Which approach do you want?
