# B2-T3 Transport-Aware Route Domain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** RTTP excludes wrong-kind existing transport from trunk/seed, strips incompatible coords from trunk even when they overlap ring cells (INV-B2T3-08), hard-blocks them in `RouteCellDomain`, and emits mismatch metrics on `RTTP_ROUTE_DOMAIN`.

**Architecture:** Adapter partitions transport → `blocked_incompatible_transport_cells` on `OptimizationInput`. Skeleton and route-domain builders subtract incompatible from `trunk_mask` before blocked/traversable are finalized, then union incompatible into `blocked_cells`. Pipeline metrics are output-only.

**Tech Stack:** Python 3.12, frozen dataclasses, `StrEnum`, pytest, ruff.

**Approved spec:** [`2026-05-24-b2-t3-transport-aware-route-domain-design.md`](../specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md) (rev 2 — INV-B2T3-08)

**Prerequisite:** B2-T2 on `master` (PR #60 merged). Branch: `feature/b2-t3-transport-aware-route-domain`

**Recommended worktree:** `f:\Python_Projects\shapez2Factory\.worktrees\b2-t3-transport-aware-route-domain`

---

## Out of scope

`RouteDomainSnapshotBuilder` module, macro/selection/validation changes, replay-as-input, Track D geometry.

---

## File map

| File | Change |
|------|--------|
| `optimization/input_contracts.py` | `blocked_incompatible_transport_cells` |
| `optimization/reconstruction_adapter.py` | `partition_existing_transport`, adapter wire, metrics helper |
| `optimization/skeleton/skeleton_builder.py` | trunk_mask subtract incompatible |
| `optimization/routing/lift_lane_domain.py` | trunk subtract + blocked union |
| `optimization/pipeline.py` | `mismatched_existing_transport_*` on route-domain step |
| `tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py` | **Create** |
| `tests/unit/asteroid_lab/test_optimization_input_adapter.py` | mixed transport |
| `tests/unit/asteroid_lab/test_rttp_existing_trunk.py` | regression |
| `docs/domain/asteroid_game_data_snapshot.md` | B2-T3 blurb |
| `documents/ai/current_plan.md` | ACTIVE next = B2-T3 |

---

### Task 1 — `OptimizationInput` field + adapter partition

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/input_contracts.py`
- Modify: `django_apps/asteroid_lab/optimization/reconstruction_adapter.py`
- Create: `tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py` (partition tests only)

- [ ] **Step 1: Failing partition test**

```python
"""B2-T3 — transport-kind aware route domain (Policy B)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.input_contracts import (
    ExistingTransportCell,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    partition_existing_transport,
)


def test_partition_existing_transport_shape_active() -> None:
    belt = ExistingTransportCell(coord=(4, 5), transport_kind=TransportKind.SHAPE_BELT)
    pipe = ExistingTransportCell(coord=(4, 6), transport_kind=TransportKind.FLUID_PIPE)
    existing = frozenset({belt, pipe})
    trunk, blocked, by_kind = partition_existing_transport(
        existing, TransportKind.SHAPE_BELT
    )
    assert trunk == frozenset({(4, 5)})
    assert blocked == frozenset({(4, 6)})
    assert by_kind == {"fluid_pipe": 1}
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py::test_partition_existing_transport_shape_active -v
```

- [ ] **Step 3: Implement field + partition + adapter wire**

`input_contracts.py`:

```python
blocked_incompatible_transport_cells: frozenset[Coord] = frozenset()
```

`reconstruction_adapter.py`:

```python
def partition_existing_transport(
    existing_transport: frozenset[ExistingTransportCell],
    active_kind: TransportKind,
) -> tuple[frozenset[Coord], frozenset[Coord], dict[str, int]]:
    trunk: set[Coord] = set()
    blocked: set[Coord] = set()
    by_kind: dict[str, int] = {}
    for cell in existing_transport:
        if cell.transport_kind == active_kind:
            trunk.add(cell.coord)
        else:
            blocked.add(cell.coord)
            key = cell.transport_kind.value
            by_kind[key] = by_kind.get(key, 0) + 1
    return frozenset(trunk), frozenset(blocked), by_kind
```

In `optimization_input_from_reconstruction`, replace `_existing_trunk_cells` usage:

```python
    existing_trunk, blocked_incompatible, _by_kind = partition_existing_transport(
        existing_transport, transport_kind
    )
    ...
        existing_trunk_cells=existing_trunk,
        blocked_incompatible_transport_cells=blocked_incompatible,
```

Delete `_existing_trunk_cells` to avoid dual paths.

- [ ] **Step 4: Failing adapter mixed-transport test** — append to `test_optimization_input_adapter.py`:

```python
def _pipe_cell(x: int, y: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x, y=y, layer=None, rotation=0,
        tile_type="SpacePipe_Forward", cell_kind="space_pipe",
        transport_kind="fluid_pipe",
        has_nested_blueprint=False, nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": x, "Y": y, "T": "SpacePipe_Forward"},
    )


def test_mixed_existing_transport_partitions_for_shape_run() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    cells = cells + (_belt_cell(4, 5), _pipe_cell(4, 6))
    inp = optimization_input_from_reconstruction(ReconstructionResult(cells=cells))
    assert inp.transport_kind is TransportKind.SHAPE_BELT
    assert len(inp.existing_transport_cells) == 2
    assert inp.existing_trunk_cells == frozenset({(4, 5)})
    assert inp.blocked_incompatible_transport_cells == frozenset({(4, 6)})
```

- [ ] **Step 5: Run adapter + partition tests — expect PASS**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py tests/unit/asteroid_lab/test_optimization_input_adapter.py -v
```

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/optimization/input_contracts.py django_apps/asteroid_lab/optimization/reconstruction_adapter.py tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py tests/unit/asteroid_lab/test_optimization_input_adapter.py
git commit -m "feat(rttp): partition existing transport by active kind"
```

---

### Task 2 — Skeleton + route-domain blocked-incompatible enforcement (INV-B2T3-08)

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/skeleton/skeleton_builder.py`
- Modify: `django_apps/asteroid_lab/optimization/routing/lift_lane_domain.py`

- [ ] **Step 1: Failing skeleton/domain tests** — append to `test_rttp_transport_kind_route_domain.py`:

```python
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.routing.route_probe import probe_route
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import (
    RttpSkeletonBuilder,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from tests.unit.asteroid_lab.test_optimization_input_adapter import (
    _belt_cell,
    _field_cell,
    _pipe_cell,
)


def _mixed_reconstruction() -> ReconstructionResult:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    return ReconstructionResult(cells=cells + (_belt_cell(4, 5), _pipe_cell(4, 6)))


def test_shape_route_does_not_use_fluid_pipe_trunk_seed() -> None:
    inp = optimization_input_from_reconstruction(_mixed_reconstruction())
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = build_route_domain_from_skeleton(skeleton, inp)
    assert (4, 6) not in skeleton.trunk_mask_cells
    assert (4, 6) in domain.blocked_cells
    assert (4, 6) not in domain.trunk_mask_cells
    assert (4, 6) not in domain.traversable_cells


def test_fluid_route_does_not_use_shape_belt_trunk_seed() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    cells = cells + (_pipe_cell(4, 5), _pipe_cell(4, 6), _belt_cell(3, 5))
    inp = optimization_input_from_reconstruction(ReconstructionResult(cells=cells))
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = build_route_domain_from_skeleton(skeleton, inp)
    assert (3, 5) not in skeleton.trunk_mask_cells
    assert (3, 5) in domain.blocked_cells


def test_incompatible_on_ring_excluded_from_trunk_not_traversable() -> None:
    """INV-B2T3-08: wrong-kind on a ring coord must not be trunk or traversable."""
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    # Rim corner — ring builder includes (5,5); wrong-kind pipe must not become trunk
    rim_pipe = _pipe_cell(5, 5)
    inp = optimization_input_from_reconstruction(ReconstructionResult(cells=cells + (rim_pipe,)))
    assert inp.transport_kind is TransportKind.SHAPE_BELT
    assert (5, 5) in inp.blocked_incompatible_transport_cells
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = build_route_domain_from_skeleton(skeleton, inp)
    assert (5, 5) not in skeleton.trunk_mask_cells
    assert (5, 5) not in domain.trunk_mask_cells
    assert (5, 5) not in domain.traversable_cells
    assert (5, 5) in domain.blocked_cells


def test_route_probe_path_does_not_cross_incompatible_transport() -> None:
    inp = optimization_input_from_reconstruction(_mixed_reconstruction())
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = build_route_domain_from_skeleton(skeleton, inp)
    goals = probe_goal_coords(inp, skeleton)
    start = skeleton.lift_columns[0].platform_coord
    result = probe_route(domain, start, goals)
    if result.reachable and result.path:
        assert not (set(result.path) & inp.blocked_incompatible_transport_cells)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py -k "shape_route or fluid_route or incompatible_on_ring or route_probe" -v
```

- [ ] **Step 3: Skeleton trunk subtract**

In `skeleton_builder.py` `_score_option`:

```python
    incompatible = inp.blocked_incompatible_transport_cells
    trunk_mask_cells = frozenset(
        (option.ring_cells | inp.existing_trunk_cells) - incompatible
    )
```

- [ ] **Step 4: Route domain trunk subtract + blocked union**

In `build_route_domain_from_skeleton`:

```python
    incompatible = inp.blocked_incompatible_transport_cells
    trunk_mask = frozenset(skeleton.trunk_mask_cells - incompatible)
    ...
    blocked = frozenset(
        (inp.mineable_cells | inp.external_void_cells)
        - platform_cells
        - trunk_mask
        - lift_coords
        - goal_coords
    )
    blocked = frozenset(blocked | incompatible)
    traversable = trunk_mask | lift_coords | goal_coords

    return RouteCellDomain(
        blocked_cells=blocked,
        trunk_mask_cells=trunk_mask,
        ...
        traversable_cells=traversable,
    )
```

- [ ] **Step 5: Run domain tests — expect PASS**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py -v
```

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/optimization/skeleton/skeleton_builder.py django_apps/asteroid_lab/optimization/routing/lift_lane_domain.py tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py
git commit -m "feat(rttp): strip incompatible transport from trunk and block route domain"
```

---

### Task 3 — `RTTP_ROUTE_DOMAIN` diagnostics

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/reconstruction_adapter.py`
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`

- [ ] **Step 1: Metrics helper + test**

Add to `reconstruction_adapter.py`:

```python
def mismatched_existing_transport_metrics(
    blocked_incompatible: frozenset[Coord],
    *,
    by_kind: dict[str, int],
) -> dict[str, int | dict[str, int]]:
    return {
        "mismatched_existing_transport_count": len(blocked_incompatible),
        "mismatched_existing_transport_by_kind": dict(by_kind),
    }
```

Append test:

```python
def test_transport_kind_mismatch_diagnostics_from_partition() -> None:
    belt = ExistingTransportCell(coord=(1, 1), transport_kind=TransportKind.SHAPE_BELT)
    pipe_a = ExistingTransportCell(coord=(2, 2), transport_kind=TransportKind.FLUID_PIPE)
    pipe_b = ExistingTransportCell(coord=(3, 3), transport_kind=TransportKind.FLUID_PIPE)
    _trunk, blocked, by_kind = partition_existing_transport(
        frozenset({belt, pipe_a, pipe_b}), TransportKind.SHAPE_BELT
    )
    metrics = mismatched_existing_transport_metrics(blocked, by_kind=by_kind)
    assert metrics["mismatched_existing_transport_count"] == 2
    assert metrics["mismatched_existing_transport_by_kind"] == {"fluid_pipe": 2}
```

- [ ] **Step 2: Run test — expect PASS after helper**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py::test_transport_kind_mismatch_diagnostics_from_partition -v
```

- [ ] **Step 3: Pipeline — both v0.1 and macro route-domain steps**

After `skeleton = RttpSkeletonBuilder.build(...)` in `_run_v01_rttp_pipeline` and macro equivalent:

```python
    _trunk, _blocked, by_kind = partition_existing_transport(
        inp.existing_transport_cells, inp.transport_kind
    )
    transport_mismatch_metrics = mismatched_existing_transport_metrics(
        inp.blocked_incompatible_transport_cells, by_kind=by_kind
    )
```

Merge into `RTTP_ROUTE_DOMAIN` `_record_pipeline_step` `metrics_json`:

```python
        metrics_json={"skeleton_id": skeleton.skeleton_id, **transport_mismatch_metrics},
```

- [ ] **Step 4: Run smoke tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_existing_trunk.py tests/unit/asteroid_lab/test_rttp_lift_lane_domain.py -v
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/optimization/reconstruction_adapter.py django_apps/asteroid_lab/optimization/pipeline.py tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py
git commit -m "feat(rttp): emit mismatched existing transport route-domain metrics"
```

---

### Task 4 — Tests (regression + acceptance gate)

**Files:**
- Modify: `tests/unit/asteroid_lab/test_rttp_existing_trunk.py`

- [ ] **Step 1: Existing trunk regression**

In `test_skeleton_includes_existing_trunk_cells`:

```python
    assert inp.blocked_incompatible_transport_cells == frozenset()
    assert inp.existing_trunk_cells <= skeleton.trunk_mask_cells
```

- [ ] **Step 2: Run full B2-T3 test module + adapter**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py tests/unit/asteroid_lab/test_optimization_input_adapter.py tests/unit/asteroid_lab/test_rttp_existing_trunk.py -v
```

Expected: all PASS; module covers:

- `test_route_probe_ignores_mismatched_existing_transport_kind` → `test_route_probe_path_does_not_cross_incompatible_transport`
- `test_shape_route_does_not_use_fluid_pipe_trunk_seed`
- `test_fluid_route_does_not_use_shape_belt_trunk_seed`
- `test_transport_kind_mismatch_diagnostics_from_partition`
- `test_incompatible_on_ring_excluded_from_trunk_not_traversable`

- [ ] **Step 3: Commit**

```bash
git add tests/unit/asteroid_lab/test_rttp_existing_trunk.py
git commit -m "test(rttp): regression for transport-aware trunk and diagnostics"
```

---

### Task 5 — Docs, `current_plan`, narrow gate

**Files:**
- Modify: `docs/domain/asteroid_game_data_snapshot.md`
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Domain doc B2-T3 paragraph**

```markdown
**B2-T3 (RTTP):** Wrong-kind existing transport is excluded from trunk seeding (including ring overlap) and unioned into route-domain `blocked_cells` (INV-B2T3-08). Metrics: `mismatched_existing_transport_count`, `mismatched_existing_transport_by_kind` on `rttp.route_domain`. Spec: `docs/superpowers/specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md`.
```

- [ ] **Step 2: Update `current_plan.md` next focus**

Replace B2-T2 ACTIVE line with:

```markdown
**우선순위:** **B2-T3** transport-aware route domain — `feature/b2-t3-transport-aware-route-domain`. Plan: [`2026-05-24-b2-t3-transport-aware-route-domain.md`](../../docs/superpowers/plans/2026-05-24-b2-t3-transport-aware-route-domain.md). **CLOSED:** B2-T2 per-cell transport (PR #60).
```

- [ ] **Step 3: Narrow gate**

```powershell
python -m pytest tests/unit/asteroid_lab -k "transport_kind or route_probe or rttp" -v
powershell -File scripts/test_reconstruction_narrow.ps1
python -m ruff check django_apps/asteroid_lab/optimization django_apps/asteroid_lab/adapters tests/unit/asteroid_lab
```

- [ ] **Step 4: Commit**

```bash
git add docs/domain/asteroid_game_data_snapshot.md documents/ai/current_plan.md
git commit -m "docs: B2-T3 transport-aware route domain and current plan"
```

---

## Plan self-review (rev 2)

| Spec requirement | Task |
|------------------|------|
| INV-B2T3-01–07 | 1–3 |
| INV-B2T3-08 ring overlap | 2 (`skeleton_builder` + `lift_lane_domain` + ring test) |
| Policy B blocked union order | 2 step 4 |
| Metrics naming | 3 |
| Four named tests + ring test | 2, 4 |
| No RouteDomainSnapshotBuilder | Out of scope |

No TBD placeholders.

---

## Execution handoff

**Plan:** `docs/superpowers/plans/2026-05-24-b2-t3-transport-aware-route-domain.md`  
**Spec (rev 2):** `docs/superpowers/specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md`

1. **Subagent-Driven (recommended)** — fresh subagent per task  
2. **Inline Execution** — executing-plans with checkpoint after Task 2

Which approach?
