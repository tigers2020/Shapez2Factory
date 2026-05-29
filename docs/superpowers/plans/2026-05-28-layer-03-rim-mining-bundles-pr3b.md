# Layer 03 Rim Mining Bundles — PR-3b Implementation Plan (Generator + Stack Wire)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `layer_03_rim_mining_bundles` dense candidate expansion (A′′ + R1-hardening) and pass `ExteriorConnectionPlan` from L2 through `stack_runner`, producing a typed `RimBundleCandidateSet` with metrics.

**Architecture:** PR-3a contracts/probe must be merged first. Add `rim_anchors`, `seed_catalog`, `project`, `route_goals`, `expand` under `layer_03/`; replace stub `run.py`. Patch `stack_runner` to capture L2 plan and pass into L3. **Layer 04 remains stub** in this PR (separate future plan).

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy, `GeneticSample` ORM for catalog loader, `field_rim_cells`, `ReconstructionCompleteMap`

**Spec:** [`2026-05-28-layer-03-rim-mining-bundles-design.md`](../specs/2026-05-28-layer-03-rim-mining-bundles-design.md)  
**Depends on:** [`2026-05-28-layer-03-rim-mining-bundles-pr3a.md`](2026-05-28-layer-03-rim-mining-bundles-pr3a.md)

**Work classification:** contract change · implementation change

**Branch:** `feat/layer-03-rim-expansion-pr3b` (after PR-3a merge)

**Execution:** Subagent-Driven after PR-3a merges. **Commit:** user request only.

**Spec hold order (normative):** compute `rim_anchor_count` first; if `exterior_plan is None`, return before `derive_layer03_resource_kind` / `build_layer03_route_goals` (see spec §3.1).

---

## Out of scope (PR-3b)

```text
- layer_04_inner_pattern_fill generator
- L5 commit / validation
- GA / evolutionary search
- maximal_non_overlap_preview as algorithm input
- R2 multi-void-edge / R3 cardinal-4
- shared/pattern_project.py (stay in layer_03/project.py)
```

---

## File map

| Action | Path |
|--------|------|
| Create | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/rim_anchors.py` |
| Create | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/seed_catalog.py` |
| Create | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/project.py` |
| Create | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/route_goals.py` |
| Create | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/run.py` |
| Modify | `django_apps/asteroid_lab/layers/stack_runner.py` |
| Modify | `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` (L3 metrics wire) |
| Create | `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py` |
| Create | `tests/unit/asteroid_lab/layers/fixtures/layer_03_golden_map.py` |
| Modify | `tests/unit/asteroid_lab/layers/test_stack_runner_budget_interruption.py` (or create) |

---

### Task 1: Rim anchors + fieldward selection

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/rim_anchors.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py`

- [ ] **Step 1: Write failing tests**

```python
def test_select_fieldward_prefers_closer_route_goal() -> None:
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.rim_anchors import (
        select_fieldward_output_dir,
    )
    # anchor with void to north (closer goal) and east (farther goal)
    direction = select_fieldward_output_dir(
        anchor=(5, 5),
        complete_map=map_with_field_and_void,
        route_goals=(goal_north, goal_east),
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert direction == Direction.N


def test_select_fieldward_tiebreak_nesw() -> None:
    # equal distance to N and E → N wins
    ...


def test_no_void_neighbor_returns_none() -> None:
    ...
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement using `field_rim_cells` + `neighbors4` + goal distance**

Import `Direction` from `django_apps.asteroid_lab.genetic_sample.enums` (canonical in repo; used by `gene_template` / `coord_transform`). **Do not** add a duplicate `Direction` under `layers/contracts/` unless a future ADR moves it.

- [ ] **Step 4: Run — PASS**

---

### Task 2: Seed catalog loader

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/seed_catalog.py`

- [ ] **Step 1: Write failing test (pytest-django)**

```python
@pytest.mark.django_db
def test_load_miner_seed_catalog_sorted_by_intrinsic_priority(
    seed_miner_patterns_loaded,
) -> None:
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import (
        load_miner_seed_catalog,
    )
    catalog = load_miner_seed_catalog()
    ranks = [s.intrinsic_priority_rank for s in catalog.seeds]
    assert ranks == sorted(ranks)
    assert catalog.seeds[0].pattern_id == "m3e_01"
```

Use existing `seed_miner_patterns` test fixtures or management command in test setup.

- [ ] **Step 2: Implement ORM loader**

Filter `GeneticSample` `metadata_json__schema=miner_seed_v2`, `metadata_json__is_seed=True`; sort by `intrinsic_priority_rank`.

- [ ] **Step 3: Add `MinerSeedCatalog.from_entries` for golden tests without DB**

- [ ] **Step 4: Run — PASS**

---

### Task 3: Project decoded_json at anchor

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/project.py`

- [ ] **Step 1: Write failing geometry tests**

```python
def test_mining_cells_subset_of_field_cells() -> None:
    projection = project_miner_seed_at_anchor(...)
    assert projection.candidate is not None
    assert projection.reject_reason is None
    candidate = projection.candidate
    assert candidate.mining_occupied_cells <= complete_map.field_cells


def test_transport_stub_subset_of_void() -> None:
    candidate = projection.candidate
    assert candidate is not None
    assert candidate.transport_stub_cells <= complete_map.external_void_cells
    assert candidate.mining_occupied_cells.isdisjoint(candidate.transport_stub_cells)


def test_anchor_on_outer_rim() -> None:
    from django_apps.asteroid_lab.reconstruction.rim_topology import field_rim_cells
    rim = field_rim_cells(complete_map.field_cells)
    assert projection.candidate is not None
    assert projection.candidate.anchor_coord in rim


def test_projection_failure_returns_reject_reason() -> None:
    projection = project_miner_seed_at_anchor(...)  # invalid fixture
    assert projection.candidate is None
    assert projection.reject_reason == CandidateRejectReason.LOCAL_GEOMETRY_INVALID
```

- [ ] **Step 2: Implement projection + `ProjectionResult`**

```python
@dataclass(frozen=True, slots=True)
class ProjectionResult:
    candidate: BundleCandidate | None
    reject_reason: CandidateRejectReason | None
```

- Parse buildings from `decoded_json` (reuse decode/normalize cell list patterns from genetic sample pipeline)
- Translate so `CANONICAL_EXTRACTOR_OFFSET` lands on `anchor_coord`
- Rotate from canonical E to `output_dir` (fieldward)
- Apply `resource_kind` → layout `T` swap (`MINER_LAYOUT_TYPES_SHAPE` / fluid mapping from `miner_seed_constants`)
- Emit `BundlePlacement` at map-absolute coords
- On invalid geometry: `ProjectionResult(candidate=None, reject_reason=<enum>)`
- On success: `ProjectionResult(candidate=..., reject_reason=None)`

- [ ] **Step 3: Run geometry tests — PASS**

---

### Task 4: Expand loop + dedupe

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py`

- [ ] **Step 1: Write failing golden test**

```python
def test_expand_rim_candidates_deterministic_count(golden_5x5_map, minimal_l2_plan, two_seed_catalog) -> None:
    result = expand_rim_bundle_candidates(
        complete_map=golden_5x5_map,
        exterior_plan=minimal_l2_plan,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000),
        seed_catalog=two_seed_catalog,
    )
    assert result.metrics.rim_anchor_count == expected_rim_count
    assert result.metrics.normal_candidate_count == expected_normal_count
    assert all(
        c.route_probe_status == RouteProbeStatus.SUCCEEDED for c in result.normal_candidates
    )
```

- [ ] **Step 2: Implement §3.1 pseudocode**

Order (must match spec §3.1):

```text
rim_anchor_count from outer_rim
IF exterior_plan is None: RETURN hold (before resource_kind / route_goals)
resource_kind → transport_kind → route_goals
IF route_goals empty: RETURN NO_ROUTE_GOALS
anchor loop with budget checks per spec §3.2
projection ← project_miner_seed_at_anchor → ProjectionResult
dedupe per §2.6 (increment dedupe_duplicate_count on every duplicate hit)
assign diagnostic_rejected_count = len(...) at end
```

- [ ] **Step 3: Write dedupe winner test**

```python
def test_duplicate_equivalence_keeps_lower_intrinsic_priority_rank() -> None:
    # two gene_keys, same geometry → one normal candidate, dedupe_duplicate_count == 1
```

- [ ] **Step 4: Run — PASS**

---

### Task 5: `run.py` + stack_runner

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/run.py`
- Modify: `django_apps/asteroid_lab/layers/stack_runner.py`

- [ ] **Step 1: Write failing stack integration test**

```python
def test_stack_runner_passes_exterior_plan_to_layer_03(monkeypatch) -> None:
    captured = {}
    def fake_l3(**kwargs):
        captured.update(kwargs)
    monkeypatch.setattr(..., "run_layer_03_rim_mining_bundles", fake_l3)
    # run_layers_02_to_05 with stub L2 returning plan
    assert "exterior_plan" in captured
```

- [ ] **Step 2: Change `_Layer02To05Runner` to carry last L2 plan**

```python
# stack_runner.py — capture plan from L2 return value; pass to L3:
last_plan: ExteriorConnectionPlan | None = None
# after L2: last_plan = result if isinstance(result, ExteriorConnectionPlan) else last_plan
# L3: run(..., exterior_plan=last_plan, budget_ctx=budget_ctx)
```

Update `run_layer_03_rim_mining_bundles` signature per spec §2.10; return `RimBundleCandidateSet` (store on runner state or extend StackRunResult in follow-up if needed — v0: attach metrics to post-summary only).

- [ ] **Step 3: Wire post-summary metrics**

`build_layer03_post_summary_metrics(result: RimBundleCandidateSet) -> dict`

- [ ] **Step 4: Run stack test — PASS**

---

### Task 6: Budget exhaustion tests

**Files:**
- Modify/create: `tests/unit/asteroid_lab/layers/test_stack_runner_budget_interruption.py`

- [ ] **Step 1: Test anchor-boundary exhaustion**

```python
def test_budget_exhausted_at_anchor_boundary_sets_skip_reason_no_diagnostic() -> None:
    # now_fn advances so remaining_budget_ms hits 0 before first anchor processing
    result = expand_rim_bundle_candidates(...)
    assert result.metrics.layer_skip_reason == Layer03SkipReason.BUDGET_EXHAUSTED
    assert result.metrics.budget_skipped_count == 0
    assert result.diagnostic_rejected_candidates == ()
```

- [ ] **Step 2: Test mid-candidate SKIPPED_BUDGET diagnostic**

```python
def test_budget_exhausted_after_projection_appends_skipped_budget_diagnostic() -> None:
    ...
    assert result.metrics.budget_skipped_count == 1
    assert result.diagnostic_rejected_candidates[0].route_probe_status == RouteProbeStatus.SKIPPED_BUDGET
```

- [ ] **Step 3: Run — PASS**

---

### Task 7: L2 hold + intrinsic order tests

- [ ] **Step 1: `exterior_plan is None`**

```python
def test_missing_exterior_plan_hold() -> None:
    result = expand_rim_bundle_candidates(..., exterior_plan=None, ...)
    assert result.metrics.rim_anchor_count > 0
    assert result.metrics.seed_projection_attempt_count == 0
    assert result.metrics.layer_skip_reason == Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN
```

- [ ] **Step 2: `intrinsic_priority_rank` attempt order**

Spy `project_miner_seed_at_anchor` call order: `m3e_01` before `m1e_01` at same anchor.

- [ ] **Step 3: Run — PASS**

---

### Task 8: PR-3b gate

- [ ] **Step 1: Narrow pytest**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py tests/unit/asteroid_lab/layers/test_stack_runner_budget_interruption.py -v
```

- [ ] **Step 2: Regression PR-3a tests**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py tests/unit/asteroid_lab/layers/test_layer_03_route_goal_builder.py -v
```

- [ ] **Step 3: ruff + mypy**

```powershell
python -m ruff check django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles django_apps/asteroid_lab/layers/stack_runner.py
python -m mypy django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles django_apps/asteroid_lab/layers/stack_runner.py
```

---

## Plan self-review (2026-05-28)

| Spec §3 requirement | Task |
|---------------------|------|
| exterior_plan None before resource_kind | Task 4 |
| resource_kind before route_goals | Task 4 |
| ProjectionResult | Task 3 |
| wall-clock vs probe slot | Task 6 |
| dedupe_duplicate_count always on duplicate | Task 4 |
| SKIPPED_BUDGET diagnostic rules | Task 6 |
| early NO_ROUTE_GOALS | Task 4 |
| diagnostic_rejected_count at end | Task 4 |
| single transport_kind per run | Task 4 |
| L4 inner fill | Out of scope |

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-28-layer-03-rim-mining-bundles-pr3b.md`.

**Recommended order:** Merge PR-3a → implement PR-3b on same feature branch or stacked PRs.

**Execution options:**

1. **Subagent-Driven (recommended)**  
2. **Inline Execution** — `executing-plans` with checkpoints

Which approach should we use to start PR-3a?
