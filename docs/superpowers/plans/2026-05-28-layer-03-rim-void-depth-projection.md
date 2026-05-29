# Layer 03 Rim Void-Depth Pre-Gate (Observability) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** **BLOCKED** — superseded by [`2026-05-28-layer-03-virtual-exterior-transport-domain-design.md`](../specs/2026-05-28-layer-03-virtual-exterior-transport-domain-design.md). Do not implement for pool recovery. Optional observability-only subset may be extracted later.

**Goal (historical):** Classify L3 geometry failures with a void-depth **necessary-condition** pre-gate, new metrics (`reject_reason_counts`, `projection_call_count`, `void_depth_pregate_rejected_count`), and Lab/JSONL output — **without** requiring `route_probe_attempt_count > 0` on production maps.

**Architecture:** Add `void_depth.py` + `seed_extent.py` under `layer_03_rim_mining_bundles/`. Extend contracts (`INSUFFICIENT_VOID_DEPTH`, `Layer03ExpansionMetrics`). Wire pre-gate in `expand.py` before `project_miner_seed_at_anchor`. Propagate metrics through post-summary, rim-stack merge, and Lab highlights. Golden 5×5 stays green; thick-rim fixture proves P0 histogram.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy, existing L3 expand/catalog/project modules

**Spec:** [`2026-05-28-layer-03-rim-void-depth-projection-design.md`](../specs/2026-05-28-layer-03-rim-void-depth-projection-design.md) (APPROVED)

**Work classification:** contract change · implementation change

**Depends on:** PR-3a contracts, PR-3b expand (merged in workspace)

**Out of scope (normative):** pool recovery, transport truncation, `route_probe_attempt_count > 0` as P0 gate, L4/L5/L6 behavior changes

**Execution:** Subagent-Driven or Inline per user choice. **Commit:** only when user explicitly requests (repo policy).

**pytest:** Never use `-q`, `--quiet`, or `--tb=no`.

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `django_apps/asteroid_lab/layers/contracts/candidates.py` | Enum + metrics fields + factory validation |
| Create | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/void_depth.py` | `void_depth_along_dir` |
| Create | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/seed_extent.py` | `transport_required_void_extent_from_decoded_json` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/seed_catalog.py` | `MinerSeedEntry.required_void_extent` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py` | Pre-gate + histogram + new counters |
| Modify | `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` | L3 wire fields |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_rim_stack.py` | Merge new metrics into `solver_summary` |
| Modify | `django_apps/asteroid_lab/services/solver_run_lab_summary.py` | L3 highlights (output-only) |
| Create | `tests/unit/asteroid_lab/layers/test_layer_03_void_depth.py` | P0 unit + thick-rim expansion |
| Create | `tests/unit/asteroid_lab/layers/fixtures/layer_03_thick_rim_map.py` | Shallow void rim topology |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py` | Catalog extent assertion |
| Modify | `tests/unit/asteroid_lab/test_solver_runtime_rim_stack.py` | New metric fields on manual `Layer03ExpansionMetrics` |
| Modify | `docs/superpowers/specs/2026-05-28-layer-03-rim-mining-bundles-design.md` | §2.7 cross-ref `INSUFFICIENT_VOID_DEPTH` (one line) |

---

### Task 1: `INSUFFICIENT_VOID_DEPTH` enum

**Files:**
- Modify: `django_apps/asteroid_lab/layers/contracts/candidates.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_void_depth.py`

- [ ] **Step 1: Write failing test**

```python
def test_candidate_reject_reason_includes_insufficient_void_depth() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import CandidateRejectReason

    assert (
        CandidateRejectReason.INSUFFICIENT_VOID_DEPTH.value == "insufficient_void_depth"
    )
```

- [ ] **Step 2: Run test — FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_void_depth.py::test_candidate_reject_reason_includes_insufficient_void_depth`

Expected: `AttributeError` or enum member missing

- [ ] **Step 3: Add enum member**

In `CandidateRejectReason` (after `TRANSPORT_STUB_NOT_IN_VOID`):

```python
INSUFFICIENT_VOID_DEPTH = "insufficient_void_depth"
```

- [ ] **Step 4: Run test — PASS**

- [ ] **Step 5: Commit (if user requested)**

```bash
git add django_apps/asteroid_lab/layers/contracts/candidates.py tests/unit/asteroid_lab/layers/test_layer_03_void_depth.py
git commit -m "feat(l3): add INSUFFICIENT_VOID_DEPTH reject reason"
```

---

### Task 2: `Layer03ExpansionMetrics` contract extension

**Files:**
- Modify: `django_apps/asteroid_lab/layers/contracts/candidates.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_void_depth.py`

**Design:** Store `reject_reason_counts` as `tuple[tuple[str, int], ...]` (sorted by key) so the frozen dataclass stays hashable/deterministic. Add `reject_reason_counts_dict()` helper in `candidates.py` for Lab wire.

- [ ] **Step 1: Write failing tests**

```python
def test_layer03_expansion_metrics_reject_histogram_invariant() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        Layer03ExpansionMetrics,
        build_rim_bundle_candidate_set,
    )

    counts = (("insufficient_void_depth", 3), ("transport_stub_not_in_void", 1))
    metrics = Layer03ExpansionMetrics(
        rim_anchor_count=2,
        seed_projection_attempt_count=4,
        projection_call_count=1,
        void_depth_pregate_rejected_count=3,
        local_geometry_rejected_count=4,
        route_probe_attempt_count=0,
        route_probe_succeeded_count=0,
        route_probe_failed_count=0,
        dedupe_duplicate_count=0,
        normal_candidate_count=0,
        diagnostic_rejected_count=4,
        budget_skipped_count=0,
        layer_skip_reason=Layer03SkipReason.NONE,
        reject_reason_counts=counts,
    )
    build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(_fake_diagnostic(),) * 4,
        metrics=metrics,
    )


def test_layer03_metrics_rejects_histogram_sum_mismatch() -> None:
    # metrics with sum(counts) != local_geometry_rejected_count → ValueError
    ...
```

Use minimal `RouteProbedBundleCandidate` stubs with `SKIPPED_GEOMETRY` (copy pattern from `test_layer_03_04_probe_before_pool.py`).

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement fields + `empty()` + validation in `build_rim_bundle_candidate_set`**

```python
@dataclass(frozen=True, slots=True)
class Layer03ExpansionMetrics:
    rim_anchor_count: int
    seed_projection_attempt_count: int
    projection_call_count: int
    void_depth_pregate_rejected_count: int
    local_geometry_rejected_count: int
    ...
    reject_reason_counts: tuple[tuple[str, int], ...]

    @classmethod
    def empty(cls) -> Layer03ExpansionMetrics:
        return cls(
            ...
            projection_call_count=0,
            void_depth_pregate_rejected_count=0,
            reject_reason_counts=(),
        )


def reject_reason_counts_dict(
    metrics: Layer03ExpansionMetrics,
) -> dict[str, int]:
    return dict(metrics.reject_reason_counts)


def _validate_reject_reason_counts(metrics: Layer03ExpansionMetrics) -> None:
    total = sum(n for _, n in metrics.reject_reason_counts)
    if total != metrics.local_geometry_rejected_count:
        msg = "sum(reject_reason_counts) must equal local_geometry_rejected_count"
        raise ValueError(msg)
    pregate = dict(metrics.reject_reason_counts).get(
        CandidateRejectReason.INSUFFICIENT_VOID_DEPTH.value, 0
    )
    if pregate != metrics.void_depth_pregate_rejected_count:
        msg = "void_depth_pregate_rejected_count must match insufficient_void_depth count"
        raise ValueError(msg)
    if metrics.projection_call_count > metrics.seed_projection_attempt_count:
        msg = "projection_call_count must be <= seed_projection_attempt_count"
        raise ValueError(msg)
```

Call `_validate_reject_reason_counts(metrics)` inside `build_rim_bundle_candidate_set`.

- [ ] **Step 4: Fix all `Layer03ExpansionMetrics(...)` call sites** (grep) — add `projection_call_count=0`, `void_depth_pregate_rejected_count=0`, `reject_reason_counts=()`.

- [ ] **Step 5: Run**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_void_depth.py tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py tests/unit/asteroid_lab/test_solver_runtime_rim_stack.py`

- [ ] **Step 6: Commit (if user requested)**

---

### Task 3: Seed `required_void_extent` helper + catalog

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/seed_extent.py`
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/seed_catalog.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_void_depth.py`
- Modify: `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py`

- [ ] **Step 1: Write failing tests**

```python
def test_transport_required_void_extent_m0e01() -> None:
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        _minimal_m0e_decoded_json,
    )
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_extent import (
        transport_required_void_extent_from_decoded_json,
    )

    assert transport_required_void_extent_from_decoded_json(_minimal_m0e_decoded_json()) == 2


def test_miner_seed_entry_has_required_void_extent(two_seed_catalog) -> None:
    for seed in two_seed_catalog().seeds:
        assert seed.required_void_extent >= 1
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement `seed_extent.py`**

Mirror `project.py` transport cell discovery:

```python
def transport_required_void_extent_from_decoded_json(decoded_json: dict[str, Any]) -> int:
    snap = build_decoded_blueprint_snapshot(decoded_json)
    extractor_local: Coord | None = None
    for cell in snap.cells:
        if cell.cell_kind in ("shape_miner", "fluid_miner"):
            extractor_local = (cell.x, cell.y)
            break
    if extractor_local is None:
        return 0
    max_x = 0
    for cell in snap.cells:
        if cell.cell_kind not in ("space_belt", "space_pipe"):
            continue
        ox = cell.x - extractor_local[0]
        oy = cell.y - extractor_local[1]
        if oy != 0:
            continue  # v0 colinear only
        if ox > 0:
            max_x = max(max_x, ox)
    return max_x
```

Add `required_void_extent: int` to `MinerSeedEntry`; set in `_entry_from_genetic_sample`.

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit (if user requested)**

---

### Task 4: `void_depth_along_dir`

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/void_depth.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_void_depth.py`

- [ ] **Step 1: Write failing tests**

```python
def test_void_depth_along_dir_counts_contiguous_void() -> None:
    from django_apps.asteroid_lab.genetic_sample.enums import Direction
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.void_depth import (
        void_depth_along_dir,
    )

    field = frozenset({(5, 5), (6, 5), (7, 5)})
    void = frozenset({(4, 5), (3, 5), (2, 5), (5, 4)})
    depth = void_depth_along_dir(
        (5, 5),
        Direction.W,
        external_void_cells=void,
    )
    assert depth == 3  # (4,5), (3,5), (2,5)


def test_void_depth_zero_when_first_step_not_void() -> None:
    depth = void_depth_along_dir((5, 5), Direction.N, external_void_cells=frozenset({(5, 6)}))
    assert depth == 0
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement**

```python
_OFFSET_BY_DIR: dict[Direction, Coord] = {
    Direction.N: (0, -1),
    Direction.E: (1, 0),
    Direction.S: (0, 1),
    Direction.W: (-1, 0),
}

def void_depth_along_dir(
    anchor_abs: Coord,
    output_dir: Direction,
    *,
    external_void_cells: frozenset[Coord],
) -> int:
    dx, dy = _OFFSET_BY_DIR[output_dir]
    x, y = anchor_abs
    depth = 0
    while True:
        x, y = x + dx, y + dy
        if (x, y) not in external_void_cells:
            break
        depth += 1
    return depth
```

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit (if user requested)**

---

### Task 5: Expand pre-gate + reject histogram

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_void_depth.py`

- [ ] **Step 1: Write failing thick-rim test**

Create `tests/unit/asteroid_lab/layers/fixtures/layer_03_thick_rim_map.py`:

```python
"""Field blob with only 1-cell void depth west of left rim — m0e needs extent 2."""

def thick_rim_complete_map() -> ReconstructionCompleteMap:
    # field: x in 5..7, y in 4..6  (3x3)
    # void west of x=5 only at (4,y), NOT at (3,y)
    ...


def thick_rim_l2_plan() -> ExteriorConnectionPlan:
    # single connector void at (4, 5) west of anchor (5,5)
    ...
```

```python
def test_thick_rim_expansion_insufficient_void_depth_histogram() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        CandidateRejectReason,
        reject_reason_counts_dict,
    )
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.expand import (
        expand_rim_bundle_candidates,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import two_seed_catalog
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_thick_rim_map import (
        thick_rim_complete_map,
        thick_rim_l2_plan,
    )

    result = expand_rim_bundle_candidates(
        complete_map=thick_rim_complete_map(),
        exterior_plan=thick_rim_l2_plan(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=two_seed_catalog(),
    )
    m = result.metrics
    counts = reject_reason_counts_dict(m)
    assert counts[CandidateRejectReason.INSUFFICIENT_VOID_DEPTH.value] > 0
    assert m.projection_call_count == 0
    assert m.route_probe_attempt_count == 0
    assert sum(counts.values()) == m.local_geometry_rejected_count
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement expand changes**

At top of seed loop (after `seed_projection_attempt_count += 1`):

```python
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.void_depth import (
    void_depth_along_dir,
)

reject_counts: dict[str, int] = {}
# ... in loop per anchor, compute once:
void_depth = void_depth_along_dir(
    anchor,
    output_dir,
    external_void_cells=complete_map.external_void_cells,
)

def _bump(reason: CandidateRejectReason) -> None:
    reject_counts[reason.value] = reject_counts.get(reason.value, 0) + 1

# inside for seed:
seed_projection_attempt_count += 1
if seed.required_void_extent > void_depth:
    void_depth_pregate_rejected_count += 1
    local_geometry_rejected_count += 1
    _bump(CandidateRejectReason.INSUFFICIENT_VOID_DEPTH)
    diagnostics.append(...)  # existing SKIPPED_GEOMETRY pattern
    continue

projection_call_count += 1
projection = project_miner_seed_at_anchor(...)
if projection.candidate is None:
    local_geometry_rejected_count += 1
    if projection.reject_reason is not None:
        _bump(projection.reject_reason)
    ...
```

Build final metrics:

```python
reject_reason_counts=tuple(sorted(reject_counts.items())),
```

Update `_hold_metrics` with zero new fields.

- [ ] **Step 4: Run**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_void_depth.py tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py`

Golden 5×5 expand test must still pass (`route_probe` may still succeed).

- [ ] **Step 5: Commit (if user requested)**

---

### Task 6: Observability + Lab wire (output-only)

**Files:**
- Modify: `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py`
- Modify: `django_apps/asteroid_lab/services/solver_runtime_rim_stack.py`
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- Test: `tests/unit/asteroid_lab/test_solver_runtime_rim_stack.py`
- Test: `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`

- [ ] **Step 1: Write failing Lab test**

```python
def test_lab_layer3_shows_void_depth_pregate_and_projection_call_counts() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=1,
        status="partial",
        solver_summary={
            "rim_anchor_count": 81,
            "void_depth_pregate_rejected_count": 1400,
            "projection_call_count": 58,
            "seed_projection_attempt_count": 1458,
            "reject_reason_counts": {
                "insufficient_void_depth": 1400,
                "transport_stub_not_in_void": 58,
            },
            "local_geometry_rejected_count": 1458,
            ...
        },
    )
    l3 = {h["label"]: h["value"] for h in row["layer_summaries"][2]["highlights"]}
    assert l3["Void-depth pregate rejected"] == "1400"
    assert l3["Projection calls"] == "58"
    assert "insufficient_void_depth" in l3["Top reject reasons"]
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Wire metrics**

`build_layer03_post_summary_metrics`:

```python
"projection_call_count": metrics.projection_call_count,
"void_depth_pregate_rejected_count": metrics.void_depth_pregate_rejected_count,
"reject_reason_counts": reject_reason_counts_dict(metrics),
```

`merge_rim_stack_into_solver_summary`: copy same keys from `layer03.metrics`.

Lab highlights (L3): add three highlights; format top-2 reject keys as `key: count, key: count`.

- [ ] **Step 4: Run tests — PASS**

- [ ] **Step 5: Commit (if user requested)**

---

### Task 7: Parent spec cross-reference

**Files:**
- Modify: `docs/superpowers/specs/2026-05-28-layer-03-rim-mining-bundles-design.md` (§2.7 enum list only)

- [ ] **Step 1: Add line** `INSUFFICIENT_VOID_DEPTH = "insufficient_void_depth"` with link to void-depth spec.

- [ ] **Step 2: Commit (if user requested)**

---

### Task 8: PR validation gate

- [ ] **Step 1: Narrow pytest**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_void_depth.py tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py tests/unit/asteroid_lab/test_solver_runtime_rim_stack.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py
```

Expected: all PASS. P0 does **not** require `route_probe_attempt_count > 0` on thick-rim test.

- [ ] **Step 2: Ruff**

```bash
python -m ruff check django_apps/asteroid_lab/layers/contracts/candidates.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/ django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py django_apps/asteroid_lab/services/solver_runtime_rim_stack.py django_apps/asteroid_lab/services/solver_run_lab_summary.py
```

- [ ] **Step 3: Mypy (PR scope)**

```bash
python -m mypy django_apps/asteroid_lab/layers/contracts/candidates.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles django_apps/asteroid_lab/services/solver_runtime_rim_stack.py
```

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| §1.1 observability not pool rescue | Header + Task 5 thick-rim (`projection_call_count==0` OK) |
| §3.1 `void_depth_along_dir` | Task 4 |
| §3.2 `required_void_extent` | Task 3 |
| §3.3 pre-gate + necessary-condition | Task 5 |
| §3.4 enum | Task 1 |
| §4.2 metrics semantics | Task 2, 6 |
| §4.3 Lab highlights | Task 6 |
| §6.1 P0 tests | Tasks 4–6, 8 |
| §6.2 P1 recovery | **Not in plan** (follow-up) |
| Coordinate model unchanged | No Lab coord imports in new modules |

**Placeholder scan:** None.

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-28-layer-03-rim-void-depth-projection.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session with `executing-plans`, batch checkpoints  

Which approach do you want?
