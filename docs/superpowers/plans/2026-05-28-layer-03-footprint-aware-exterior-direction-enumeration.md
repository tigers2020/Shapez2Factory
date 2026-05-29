# Layer 03 Footprint-Aware Exterior Direction Enumeration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace R1 single `output_dir` per rim anchor with R2-lite enumeration (≤4 exterior cardinal directions), so feasible seed rotations are tried before rejection; restore `route_probe_attempt_count > 0` on synthetic fixtures without changing the M-anchor projection formula.

**Architecture:** Add `exterior_output_dir_candidates()` in `rim_anchors.py` (first step ∉ `field_cells`; sorted by L2 goal distance, **all** dirs enumerated). `expand.py` nests `for output_dir in candidates: for seed in catalog`. Optional `preview_mining_footprint_at_anchor()` avoids full projection on obvious off-field cases. Metrics split `direction_seed_attempt_count` (enumeration total) vs `seed_projection_attempt_count` (actual `project_miner_seed_at_anchor` calls). Virtual exterior / `placeable_cells` probe path unchanged.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy (`django_apps config src`), `Direction`, `rotate_offset`, `ReconstructionCompleteMap`

**Spec:** [`2026-05-28-layer-03-footprint-aware-exterior-direction-enumeration-design.md`](../specs/2026-05-28-layer-03-footprint-aware-exterior-direction-enumeration-design.md) (APPROVED 2026-05-28)

**Work classification:** contract change · implementation change

**Branch suggestion:** `feat/layer-03-footprint-direction-enumeration`

**pytest:** No `-q`, `--quiet`, or `--tb=no`.

### Lab UI metric migration (normative)

| Metric | Before (R1) | After (R2-lite) |
|--------|-------------|-----------------|
| `Seed projection attempts` (Lab) | Often read as `81 × 18` | Maps to `seed_projection_attempt_count` = **actual** `project_miner_seed_at_anchor` calls |
| *(new)* | — | `direction_seed_attempt_count` = Σ (direction candidates × seeds) per anchor |
| `exterior_direction_candidate_count` | — | Σ direction candidates over anchors |

`direction_seed_attempt_count` is the new total enumeration counter; it will exceed legacy `81×18` when anchors have multiple exterior dirs.

### Direction candidate vs exterior reachability

A direction is included when `step(anchor, d) ∉ field_cells`. That is a **search candidate only**, not proof of exterior reachability. Interior holes or disconnected first steps are rejected later by `build_exterior_transport_domain` / `placeable_cells` (virtual exterior spec).

---

## File map

| Action | Path |
|--------|------|
| Modify | `docs/superpowers/specs/2026-05-28-layer-03-footprint-aware-exterior-direction-enumeration-design.md` (status APPROVED) |
| Modify | `docs/superpowers/specs/2026-05-28-layer-03-rim-mining-bundles-design.md` §1.4 |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/rim_anchors.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py` |
| Create | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/mining_footprint.py` |
| Modify | `django_apps/asteroid_lab/layers/contracts/candidates.py` |
| Modify | `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_rim_stack.py` |
| Modify | `django_apps/asteroid_lab/services/solver_run_lab_summary.py` |
| Create | `tests/unit/asteroid_lab/layers/fixtures/layer_03_eeemb_projection.py` |
| Create | `tests/unit/asteroid_lab/layers/fixtures/layer_03_r1_fail_r2_success.py` |
| Create | `tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py` |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py` |

**Do not modify** `project.py` projection formula unless EEEMB regression fails (then stop and file bug — spec says formula is correct).

---

### Task 1: Finalize spec + parent §1.4

**Files:**
- Modify: `docs/superpowers/specs/2026-05-28-layer-03-footprint-aware-exterior-direction-enumeration-design.md`
- Modify: `docs/superpowers/specs/2026-05-28-layer-03-rim-mining-bundles-design.md`

- [ ] **Step 1: Set spec status APPROVED** in §10 and add Architect decision block (R2-lite, M-anchor unchanged).

- [ ] **Step 2: Add §2.3 note** (direction candidate ≠ exterior proof):

```markdown
A non-field first step is only a direction candidate, not proof of exterior reachability.
Interior-hole or disconnected candidates are rejected later by the virtual exterior domain.
```

- [ ] **Step 3: Harden §7.2 P0 gate** to `route_probe_attempt_count > 0` only (remove OR normal_candidate_count).

- [ ] **Step 4: Replace parent §1.4** with R2-lite cross-link text from spec §8.

---

### Task 2: `exterior_output_dir_candidates` API

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/rim_anchors.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py`

- [ ] **Step 1: Write failing tests**

```python
def test_exterior_output_dir_candidates_includes_all_non_field_cardinals() -> None:
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.rim_anchors import (
        exterior_output_dir_candidates,
    )
    anchor = (5, 5)
    complete_map = _minimal_complete_map(
        field_cells=frozenset({anchor}),
        external_void_cells=frozenset({(5, 4), (6, 5), (99, 99)}),
    )
    dirs = exterior_output_dir_candidates(
        anchor,
        complete_map=complete_map,
        route_goals=(),
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert set(dirs) == {Direction.N, Direction.E, Direction.S, Direction.W}


def test_exterior_output_dir_candidates_sorted_by_goal_not_truncated() -> None:
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.rim_anchors import (
        exterior_output_dir_candidates,
        select_exterior_output_dir,
    )
    anchor = (5, 5)
    complete_map = _minimal_complete_map(
        field_cells=frozenset({anchor}),
        external_void_cells=frozenset({(5, 4), (6, 5)}),
    )
    goals = (
        RouteGoal(
            goal_id="north",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=(5, 4),
            transport_kind=TransportKind.SHAPE_BELT,
            priority=0,
            connector_role=ExteriorConnectorRole.REQUIRED,
        ),
        RouteGoal(
            goal_id="east",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=(6, 5),
            transport_kind=TransportKind.SHAPE_BELT,
            priority=0,
            connector_role=ExteriorConnectorRole.REQUIRED,
        ),
    )
    dirs = exterior_output_dir_candidates(
        anchor,
        complete_map=complete_map,
        route_goals=goals,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert len(dirs) == 2
    assert dirs[0] == select_exterior_output_dir(
        anchor,
        complete_map=complete_map,
        route_goals=goals,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert set(dirs) == {Direction.N, Direction.E}
```

- [ ] **Step 2: Run — FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py::test_exterior_output_dir_candidates_includes_all_non_field_cardinals tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py::test_exterior_output_dir_candidates_sorted_by_goal_not_truncated`

- [ ] **Step 3: Implement in `rim_anchors.py`**

```python
def _exterior_cardinal_dirs(anchor: Coord, *, field_cells: frozenset[Coord]) -> list[tuple[Direction, Coord]]:
    out: list[tuple[Direction, Coord]] = []
    for direction, (dx, dy) in _OFFSET_BY_DIRECTION:
        neighbor = (anchor[0] + dx, anchor[1] + dy)
        if neighbor not in field_cells:
            out.append((direction, neighbor))
    return out


def exterior_output_dir_candidates(
    anchor: Coord,
    *,
    complete_map: ReconstructionCompleteMap,
    route_goals: tuple[RouteGoal, ...],
    transport_kind: TransportKind,
) -> tuple[Direction, ...]:
    pairs = _exterior_cardinal_dirs(anchor, field_cells=complete_map.field_cells)
    if not pairs:
        return ()
    matching = [g for g in route_goals if g.transport_kind == transport_kind]
    tie_order = {Direction.N: 0, Direction.E: 1, Direction.S: 2, Direction.W: 3}

    def score(item: tuple[Direction, Coord]) -> tuple[int, int, int]:
        direction, void_coord = item
        if not matching:
            return (0, tie_order[direction], 0)
        min_goal_dist = min(_manhattan(void_coord, g.coord) for g in matching)
        return (min_goal_dist, tie_order[direction], 0)

    ordered = sorted(pairs, key=score)
    return tuple(d for d, _ in ordered)
```

Refactor `select_exterior_output_dir` to call `exterior_output_dir_candidates` and return `candidates[0]` if any, else `None` (preserves existing rim_generation tests).

- [ ] **Step 4: Export in `__all__`**

- [ ] **Step 5: Run — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py`

---

### Task 3: EEEMB M-anchor regression fixture + test

**Files:**
- Create: `tests/unit/asteroid_lab/layers/fixtures/layer_03_eeemb_projection.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py`

- [ ] **Step 1: Fixture**

```python
"""Colinear E E E M B seed; M local (4,0); anchor (7,3)."""

def eeemb_decoded_json() -> dict[str, object]:
    return {
        "BP": {
            "Entries": [
                {"T": "Layout_ShapeMinerExtension", "X": 1, "Y": 0, "R": 0},
                {"T": "Layout_ShapeMinerExtension", "X": 2, "Y": 0, "R": 0},
                {"T": "Layout_ShapeMinerExtension", "X": 3, "Y": 0, "R": 0},
                {"T": "Layout_ShapeMiner", "X": 4, "Y": 0, "R": 0},
                {"T": "SpaceBelt_Forward", "X": 5, "Y": 0, "R": 0},
            ],
        },
    }

def eeemb_seed_entry() -> MinerSeedEntry:
    return MinerSeedEntry(
        gene_key="test_eeemb",
        pattern_id="eeemb_test",
        intrinsic_priority_rank=1,
        throughput_factor=16,
        topology_signature="topo_eeemb",
        decoded_json=eeemb_decoded_json(),
    )

def eeemb_complete_map() -> ReconstructionCompleteMap:
    field = frozenset({(4, 3), (5, 3), (6, 3), (7, 3)})
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=frozenset({(8, 3)}),
        coord_frame=CoordFrame.ISLAND_RAW,
    )
```

- [ ] **Step 2: Failing test**

```python
def test_eeemb_projection_m_anchor_output_dir_e() -> None:
    from django_apps.asteroid_lab.genetic_sample.enums import Direction
    result = project_miner_seed_at_anchor(
        seed=eeemb_seed_entry(),
        anchor_coord=(7, 3),
        output_dir=Direction.E,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=eeemb_complete_map(),
    )
    assert result.candidate is not None
    assert result.reject_reason is None
    c = result.candidate
    assert c.anchor_coord == (7, 3)
    assert c.mining_occupied_cells <= eeemb_complete_map().field_cells
    assert c.transport_stub_cells & eeemb_complete_map().field_cells == frozenset()
    assert (4, 3) in c.mining_occupied_cells
    assert (8, 3) in c.transport_stub_cells
```

- [ ] **Step 3: Run — expect PASS** (formula already correct). If FAIL, stop — do not change formula without spec amendment.

---

### Task 4: R1-fail / R2-lite-success fixture + test (P0 hard gate)

**Files:**
- Create: `tests/unit/asteroid_lab/layers/fixtures/layer_03_r1_fail_r2_success.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py`

- [ ] **Step 1: Fixture design**

```text
anchor = (7, 3) on field strip (4,3)..(7,3)
exterior dirs: N → (7,2), E → (8,3)
L2 goal at (7, 2) so R1 select_exterior_output_dir picks N first
EEEMB seed succeeds only with output_dir=E (belt to (8,3))
expand_rim_bundle_candidates with single seed → route_probe_attempt_count > 0
```

Implement `r1_fail_r2_success_complete_map()`, `r1_fail_r2_success_l2_plan()` with goal `(7,2)`, catalog with only `eeemb_seed_entry()`.

- [ ] **Step 2: Failing test**

```python
def test_r2_lite_finds_e_direction_when_r1_would_pick_n_only() -> None:
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.rim_anchors import (
        exterior_output_dir_candidates,
        select_exterior_output_dir,
    )
    anchor = (7, 3)
    complete_map = r1_fail_r2_success_complete_map()
    plan = r1_fail_r2_success_l2_plan()
    goals = build_layer03_route_goals(plan, transport_kind=TransportKind.SHAPE_BELT)
    assert select_exterior_output_dir(
        anchor, complete_map=complete_map, route_goals=goals, transport_kind=TransportKind.SHAPE_BELT
    ) == Direction.N
    dirs = exterior_output_dir_candidates(
        anchor, complete_map=complete_map, route_goals=goals, transport_kind=TransportKind.SHAPE_BELT
    )
    assert Direction.N in dirs and Direction.E in dirs

    result = expand_rim_bundle_candidates(
        complete_map=complete_map,
        exterior_plan=plan,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=MinerSeedCatalog.from_entries(eeemb_seed_entry()),
    )
    assert result.metrics.route_probe_attempt_count > 0
```

- [ ] **Step 3: Run — FAIL** (expand still R1)

- [ ] **Step 4: Implement Task 5 first if not done, then re-run — PASS**

---

### Task 5: `expand.py` R2-lite loop

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py`
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/mining_footprint.py`
- Test: Task 4 test + `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py` (virtual exterior P0 still green)

- [ ] **Step 1: Add optional prefilter helper**

`mining_footprint.py`:

```python
def projected_mining_cells_at_anchor(
    *,
    seed: MinerSeedEntry,
    anchor_coord: Coord,
    output_dir: Direction,
    complete_map: ReconstructionCompleteMap,
) -> frozenset[Coord] | None:
    """Return mining cell coords if computable; None if seed has no extractor."""
    # Reuse same loop as project.py for mining cells only (no transport, no BundleCandidate)
```

```python
def mining_footprint_off_field(
    *,
    seed: MinerSeedEntry,
    anchor_coord: Coord,
    output_dir: Direction,
    complete_map: ReconstructionCompleteMap,
) -> bool:
    cells = projected_mining_cells_at_anchor(...)
    if cells is None:
        return False
    return bool(cells - complete_map.field_cells)
```

- [ ] **Step 2: Replace expand anchor loop**

```python
    exterior_direction_candidate_count = 0
    direction_seed_attempt_count = 0
    mining_footprint_prefilter_rejected_count = 0

    for anchor in outer_rim:
        ...
        output_dirs = exterior_output_dir_candidates(
            anchor,
            complete_map=complete_map,
            route_goals=route_goals,
            transport_kind=transport_kind,
        )
        if not output_dirs:
            diagnostics.append(_geometry_diagnostic(..., NO_EXTERIOR_VOID_NEIGHBOR))
            continue

        exterior_direction_candidate_count += len(output_dirs)

        for output_dir in output_dirs:
            for seed in catalog.by_intrinsic_priority_rank():
                direction_seed_attempt_count += 1
                if mining_footprint_off_field(...):
                    mining_footprint_prefilter_rejected_count += 1
                    local_geometry_rejected_count += 1
                    diagnostics.append(... MINING_CELL_OFF_FIELD ...)
                    continue

                seed_projection_attempt_count += 1
                projection = project_miner_seed_at_anchor(...)
                ...
```

Remove sole `select_exterior_output_dir` call from expand (keep function for tests).

- [ ] **Step 3: Run P0 tests**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py`

Expected: PASS including `route_probe_attempt_count > 0`

---

### Task 6: Direction metrics on `Layer03ExpansionMetrics`

**Files:**
- Modify: `django_apps/asteroid_lab/layers/contracts/candidates.py`
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py`
- Modify: `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py`
- Modify: `django_apps/asteroid_lab/services/solver_runtime_rim_stack.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py`

- [ ] **Step 1: Extend dataclass**

```python
@dataclass(frozen=True, slots=True)
class Layer03ExpansionMetrics:
    ...
    exterior_direction_candidate_count: int = 0
    direction_seed_attempt_count: int = 0
    mining_footprint_prefilter_rejected_count: int = 0
```

Update `empty()`, `_hold_metrics()`, and all explicit constructors in tests (`test_solver_runtime_rim_stack.py`, `test_layer_04_rim_placement.py`).

- [ ] **Step 2: Populate in expand metrics builder**

- [ ] **Step 3: Wire `merge_rim_stack_into_solver_summary`**

```python
solver_summary["exterior_direction_candidate_count"] = metrics.exterior_direction_candidate_count
solver_summary["direction_seed_attempt_count"] = metrics.direction_seed_attempt_count
solver_summary["mining_footprint_prefilter_rejected_count"] = metrics.mining_footprint_prefilter_rejected_count
```

- [ ] **Step 4: Test**

```python
def test_expand_reports_direction_seed_attempt_count() -> None:
    result = expand_rim_bundle_candidates(...)  # r1_fail fixture
    assert result.metrics.direction_seed_attempt_count >= 2
    assert result.metrics.exterior_direction_candidate_count >= 2
```

---

### Task 7: `LOCAL_GEOMETRY_INVALID` subreason histogram

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/project.py`
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py`
- Modify: `django_apps/asteroid_lab/layers/contracts/candidates.py` (optional `reject_reason_detail: str | None` on diagnostic path only — YAGNI: use dotted histogram keys instead)

- [ ] **Step 1: Add helper in `project.py`**

```python
def local_geometry_invalid_detail(
    *,
    seed: MinerSeedEntry,
    anchor_coord: Coord,
    output_dir: Direction,
    complete_map: ReconstructionCompleteMap,
) -> str:
    """Return dotted subreason for histogram when projection would fail LOCAL_GEOMETRY_INVALID."""
```

Map each failure branch to:
`local_geometry_invalid.missing_extractor`, `.anchor_not_in_mining_cells`, `.mining_transport_overlap`, `.probe_start_not_transport`, `.unknown_layout`

- [ ] **Step 2: In expand, when `reject_reason == LOCAL_GEOMETRY_INVALID`, tally**

```python
detail = local_geometry_invalid_detail(...)
tally_key = detail  # use in _build_reject_reason_counts via diagnostic field
```

Simplest v1: add optional `reject_reason_histogram_key: str | None` on `RouteProbedBundleCandidate` **or** pass dotted string into diagnostics by using a parallel Counter in expand when appending diagnostics:

```python
histogram_key = (
    reject_reason.value
    if reject_reason != CandidateRejectReason.LOCAL_GEOMETRY_INVALID
    else local_geometry_invalid_detail(...)
)
```

Extend `_build_reject_reason_counts` to accept optional key override per diagnostic.

- [ ] **Step 3: Test**

```python
def test_local_geometry_invalid_subreason_in_histogram() -> None:
    # seed with no extractor → expand → reject_reason_counts contains
    # ("local_geometry_invalid.missing_extractor", 1)
```

---

### Task 8: Lab summary highlights

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`

- [ ] **Step 1: Add highlights after Rim anchor slots**

```python
_highlight("Direction seed attempts", _obs_field_count(solver_summary, "direction_seed_attempt_count")),
_highlight("Exterior dir candidates", _obs_field_count(solver_summary, "exterior_direction_candidate_count")),
```

Keep existing Top reject reasons line.

- [ ] **Step 2: Run** `python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py`

---

### Task 9: Regression gate

- [ ] **Step 1: Narrow pytest**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py tests/unit/asteroid_lab/test_solver_runtime_rim_stack.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py
```

Expected: all PASS; P0 `route_probe_attempt_count > 0` on R1-fail fixture.

- [ ] **Step 2: Ruff**

```bash
python -m ruff check django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/rim_anchors.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/mining_footprint.py django_apps/asteroid_lab/layers/contracts/candidates.py
```

- [ ] **Step 3: Mypy (touched modules)**

```bash
python -m mypy django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/rim_anchors.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/mining_footprint.py
```

---

## Spec self-review (plan author)

| Spec § | Task |
|--------|------|
| §2 R2-lite enumeration | 2, 5 |
| §2.3 ≤4 cardinals, field gate | 2 |
| §2.4 formula unchanged | 3 (regression only) |
| §3 flow | 5 |
| §5 subreasons | 7 |
| §6 metrics + migration note | 6, plan header |
| §7.1 EEEMB | 3 |
| §7.2 P0 probe > 0 | 4 |
| §7.3 583 optional | out of scope |
| §8 parent §1.4 | 1 |
| Direction ≠ exterior proof | Task 1 spec note, plan header |

No placeholders in task steps; all paths absolute.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-28-layer-03-footprint-aware-exterior-direction-enumeration.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task (groups: 1–2, 3–4, 5, 6–7, 8–9), spec then quality review between tasks.

2. **Inline Execution** — this session with checkpoints after Task 4 (P0) and Task 9 (gate).

Which approach?
