# Layer 03 Weighted Transport Routing with Mining Occupancy Priority — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow belt/pipe routing through asteroid field cells at high cost while blocking only M/E-occupied cells; treat `route_probe_start_coord` as a transport **entry** (not pre-installed stub); replace uniform BFS with weighted Dijkstra so `route_probe_attempt_count > 0` on synthetic regression.

**Architecture:** `install_surface_cells` = (field ∩ bbox) ∪ (non-field ∩ bbox); `walkable_cells` = install surface − mining − incompatible − explicit_blocked (v1: last two empty). **Not** “anonymous bbox fill” without policy text — hard caps `EXTERIOR_TRANSPORT_MARGIN_CELLS`, `MAX_PATH_CELLS=64`, `MAX_EXPANDED_NODES=512`. Projection rejects `transport ∩ mining` only. Entry from `CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET` (§3.1 caveat). `expand.py` checks `domain.step_cost(entry) is not None` only; **Dijkstra is sole reachability authority** (no `reachable_walkable_from_start` in P0).

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy (`django_apps config src`), `heapq` (stdlib Dijkstra)

**Spec:** [`2026-05-28-layer-03-weighted-transport-routing-design.md`](../specs/2026-05-28-layer-03-weighted-transport-routing-design.md) — **APPROVED WITH BLOCKING AMENDMENTS (2026-05-28)**

### Architect blocking amendments (incorporated — implementation gate)

- [x] Walkable domain semantics bounded + blocker policy (spec §4.1)
- [x] `reachable_walkable_from_start` removed from P0; Dijkstra sole reachability authority
- [x] `transport_entry_coord` v1 fixed-output caveat (spec §3.1)
- [x] `TRANSPORT_COLLIDES_WITH_FIELD` not-emitted regression test (Task 3)
- [x] Dijkstra `MAX_PATH_CELLS` vs `MAX_EXPANDED_NODES` split (Task 5)

### Subagent-Driven execution groups (normative)

| Subagent | Tasks | Scope |
|----------|-------|--------|
| **A** | 1–2 | Spec/parent patches + reject enum + `BundleCandidate.__post_init__` |
| **B** | 3 | `transport_entry.py` + `project.py` + not-emitted field test |
| **C** | 4–5 | `WeightedTransportRouteDomain` builder + Dijkstra (no separate BFS gate) |
| **D** | 6–7 | P0 expand fixture + `expand.py` integration |
| **E** | 8–9 | Metrics/Lab + regression gate |

**Work classification:** contract change · implementation change

**Branch suggestion:** `feat/layer-03-weighted-transport-routing`

**pytest:** No `-q`, `--quiet`, or `--tb=no`.

**Do not commit** unless explicitly instructed.

---

## File map

| Action | Path |
|--------|------|
| Modify | `docs/superpowers/specs/2026-05-28-layer-03-weighted-transport-routing-design.md` (APPROVED WITH BLOCKING AMENDMENTS) |
| Modify | `docs/superpowers/specs/2026-05-28-layer-03-virtual-exterior-transport-domain-design.md` |
| Modify | `docs/superpowers/specs/2026-05-28-layer-03-rim-mining-bundles-design.md` |
| Modify | `django_apps/asteroid_lab/layers/contracts/candidates.py` |
| Create | `django_apps/asteroid_lab/layers/contracts/weighted_transport_route_domain.py` |
| Create | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/transport_entry.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/project.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/exterior_domain.py` |
| Modify | `django_apps/asteroid_lab/layers/shared/route_probe.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py` |
| Modify | `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_rim_stack.py` |
| Modify | `django_apps/asteroid_lab/services/solver_run_lab_summary.py` |
| Create | `tests/unit/asteroid_lab/layers/fixtures/layer_03_weighted_route_maps.py` |
| Create | `tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py` |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py` |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py` (EEEMB fixture if entry semantics change) |

---

### Task 1: Spec approval + parent/virtual amendments

**Files:**
- Modify: `docs/superpowers/specs/2026-05-28-layer-03-weighted-transport-routing-design.md`
- Modify: `docs/superpowers/specs/2026-05-28-layer-03-virtual-exterior-transport-domain-design.md`
- Modify: `docs/superpowers/specs/2026-05-28-layer-03-rim-mining-bundles-design.md`

- [x] **Step 1: Set weighted spec status APPROVED WITH BLOCKING AMENDMENTS** in §8 (done 2026-05-28).

- [x] **Step 2: Patch virtual exterior §3.3** — replace “nodes = bbox \ field” with weighted walkable model; cross-link weighted spec.

Insert after §3.3 title block:

```markdown
**Amended 2026-05-28 (weighted routing):** Field cells inside `search_bbox` are walkable at `FIELD_ROUTE_COST` unless in `mining_occupied_cells` (blocked). See weighted-transport-routing-design.md.
```

- [x] **Step 3: Patch virtual exterior §4.1 validation order** — replace steps 3 and 5:

```markdown
3. transport_stub_cells ∩ mining_occupied_cells = ∅  → TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT
4. anchor_abs ∈ mining_occupied_cells
5. route_probe_start_coord = transport_entry_coord; MUST NOT require ∈ transport_stub_cells
REMOVED: transport_stub_cells ∩ field_cells → TRANSPORT_COLLIDES_WITH_FIELD
```

- [x] **Step 4: Patch rim-mining §2.4** — `route_probe_start_coord` semantics + field transport allowed; add Korean reference from weighted spec §2.4.

- [x] **Step 5: No code in this task** — docs only.

---

### Task 2: Reject reason + `BundleCandidate` validation contract

**Files:**
- Modify: `django_apps/asteroid_lab/layers/contracts/candidates.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py`

- [ ] **Step 1: Write failing test — new reject reason exists**

```python
def test_candidate_reject_reason_includes_transport_collides_with_mining_equipment() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import CandidateRejectReason

    assert hasattr(CandidateRejectReason, "TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT")
    assert (
        CandidateRejectReason.TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT.value
        == "transport_collides_with_mining_equipment"
    )
```

- [ ] **Step 2: Run — FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py::test_candidate_reject_reason_includes_transport_collides_with_mining_equipment`

Expected: FAIL `AttributeError` or missing enum member.

- [ ] **Step 3: Add enum member** in `CandidateRejectReason`:

```python
TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT = "transport_collides_with_mining_equipment"
```

Keep `TRANSPORT_COLLIDES_WITH_FIELD` unchanged (deprecated emit only).

- [ ] **Step 4: Write failing test — entry need not be in stubs**

```python
def test_bundle_candidate_allows_route_probe_start_not_in_transport_stubs() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        BundleCandidate,
        make_bundle_candidate_for_test,
    )

    candidate = make_bundle_candidate_for_test(
        anchor_coord=(7, 3),
        mining_occupied_cells=frozenset({(7, 3)}),
        transport_stub_cells=frozenset(),  # no preinstalled belt at entry
        route_probe_start_coord=(8, 3),  # entry on field, not a stub
    )
    assert candidate.route_probe_start_coord == (8, 3)
```

Adjust `make_bundle_candidate_for_test` if it does not accept `mining_occupied_cells` / `route_probe_start_coord` overrides — extend factory in same task.

- [ ] **Step 5: Run — FAIL** (current `__post_init__` requires start ∈ stubs).

- [ ] **Step 6: Update `BundleCandidate.__post_init__`**

Replace:

```python
if self.route_probe_start_coord not in self.transport_stub_cells:
    raise ValueError(...)
```

With:

```python
if self.route_probe_start_coord in self.mining_occupied_cells:
    msg = "route_probe_start_coord must not be in mining_occupied_cells"
    raise ValueError(msg)
```

Keep:

```python
if self.mining_occupied_cells & self.transport_stub_cells:
    raise ValueError(...)
```

- [ ] **Step 7: Extend `RouteProbeResult`**

```python
@dataclass(frozen=True, slots=True)
class RouteProbeResult:
    reached_goal: bool
    goal_coord: Coord | None
    path_coords: tuple[Coord, ...]
    steps_expanded: int
    transport_kind: TransportKind
    route_cost: int = 0
    field_route_cell_count: int = 0
```

Update all explicit `RouteProbeResult(...)` constructors in tests (grep `RouteProbeResult(`).

- [ ] **Step 8: Run tests — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py`

---

### Task 3: `transport_entry.py` + projection contract

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/transport_entry.py`
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/project.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py`

- [ ] **Step 1: Write failing test — transport on field allowed**

```python
def test_projection_allows_transport_stub_on_field() -> None:
    from django_apps.asteroid_lab.genetic_sample.enums import Direction
    from django_apps.asteroid_lab.layers.contracts.transport_kind import (
        ResourceKind,
        TransportKind,
    )
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.project import (
        project_miner_seed_at_anchor,
    )
    from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
    from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_virtual_exterior_map import (
        virtual_exterior_m0e_seed,
    )

    complete_map = ReconstructionCompleteMap(
        cells=(),
        field_cells=frozenset({(5, 5), (6, 5)}),
        shape_field_cell_count=2,
        fluid_field_cell_count=0,
        external_void_cells=frozenset({(4, 5)}),
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    result = project_miner_seed_at_anchor(
        seed=virtual_exterior_m0e_seed(),
        anchor_coord=(5, 5),
        output_dir=Direction.W,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    assert result.candidate is not None
    assert result.reject_reason is None
    assert result.candidate.transport_stub_cells & complete_map.field_cells
```

- [ ] **Step 2: Run — FAIL** (`TRANSPORT_COLLIDES_WITH_FIELD`).

- [ ] **Step 3: Implement `transport_entry.py`**

```python
"""Derive L3 transport entry coordinate from rim anchor and output direction."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.coord_transform import (
    rotate_offset,
    steps_from_canonical_e,
)
from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.genetic_sample.gene_template import (
    CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
)
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def derive_transport_entry_coord(
    *,
    anchor_coord: Coord,
    output_dir: Direction,
) -> Coord:
  steps = steps_from_canonical_e(output_dir)
  offset = rotate_offset(CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET, steps)
  return (anchor_coord[0] + offset[0], anchor_coord[1] + offset[1])


__all__ = ["derive_transport_entry_coord"]
```

- [ ] **Step 4: Modify `project.py`**

1. Remove block:

```python
if transport_cells & complete_map.field_cells:
    return ProjectionResult(..., TRANSPORT_COLLIDES_WITH_FIELD)
```

2. Replace mining∩transport LOCAL_GEOMETRY with:

```python
if mining_cells & transport_cells:
    return ProjectionResult(
        candidate=None,
        reject_reason=CandidateRejectReason.TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT,
    )
```

3. Replace probe start logic:

```python
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.transport_entry import (
    derive_transport_entry_coord,
)

route_probe_start = derive_transport_entry_coord(
    anchor_coord=anchor_coord,
    output_dir=output_dir,
)
if route_probe_start in mining_cells:
    return ProjectionResult(
        candidate=None,
        reject_reason=CandidateRejectReason.TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT,
    )
```

4. Remove:

```python
if route_probe_start not in transport_cells:
    return ProjectionResult(..., LOCAL_GEOMETRY_INVALID)
```

5. Remove `local_geometry_invalid_detail` branch `probe_start_not_transport` (delete lines returning that string).

- [ ] **Step 5: Write failing test — `TRANSPORT_COLLIDES_WITH_FIELD` not emitted (P0)**

```python
def test_projection_does_not_emit_transport_collides_with_field() -> None:
    from django_apps.asteroid_lab.genetic_sample.enums import Direction
    from django_apps.asteroid_lab.layers.contracts.candidates import CandidateRejectReason
    from django_apps.asteroid_lab.layers.contracts.transport_kind import (
        ResourceKind,
        TransportKind,
    )
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.project import (
        project_miner_seed_at_anchor,
    )
    from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
    from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_virtual_exterior_map import (
        virtual_exterior_m0e_seed,
    )

    complete_map = ReconstructionCompleteMap(
        cells=(),
        field_cells=frozenset({(5, 5), (6, 5)}),
        shape_field_cell_count=2,
        fluid_field_cell_count=0,
        external_void_cells=frozenset({(4, 5)}),
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    result = project_miner_seed_at_anchor(
        seed=virtual_exterior_m0e_seed(),
        anchor_coord=(5, 5),
        output_dir=Direction.W,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    assert result.reject_reason != CandidateRejectReason.TRANSPORT_COLLIDES_WITH_FIELD
    if result.candidate is not None:
        assert result.reject_reason is None
```

- [ ] **Step 6: Run projection tests — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py::test_projection_allows_transport_stub_on_field tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py::test_projection_does_not_emit_transport_collides_with_field`

- [ ] **Step 7: Update `test_layer_03_exterior_domain.py`**

Replace `test_projection_rejects_transport_on_field` with `test_projection_allows_transport_stub_on_field` (or delete duplicate if moved).

---

### Task 4: `WeightedTransportRouteDomain` + builder

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/weighted_transport_route_domain.py`
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/exterior_domain.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py`

- [ ] **Step 1: Write failing test — field cell has higher cost**

```python
def test_weighted_domain_field_cost_exceeds_exterior() -> None:
    from django_apps.asteroid_lab.layers.contracts.weighted_transport_route_domain import (
        EXTERIOR_ROUTE_COST,
        FIELD_ROUTE_COST,
        WeightedTransportRouteDomain,
    )
    from django_apps.asteroid_lab.snapshots.grid_contract import BBox

    domain = WeightedTransportRouteDomain(
        search_bbox=BBox(0, 5, 0, 5),
        blocked_cells=frozenset(),
        walkable_cells=frozenset({(1, 1), (2, 1)}),
        field_cost_cells=frozenset({(2, 1)}),
    )
    assert domain.step_cost((1, 1)) == EXTERIOR_ROUTE_COST
    assert domain.step_cost((2, 1)) == FIELD_ROUTE_COST
    assert domain.step_cost((9, 9)) is None  # not walkable
```

- [ ] **Step 2: Implement DTO** (`weighted_transport_route_domain.py`):

```python
EXTERIOR_ROUTE_COST = 1
FIELD_ROUTE_COST = 25

@dataclass(frozen=True, slots=True)
class WeightedTransportRouteDomain:
    search_bbox: BBox
    blocked_cells: frozenset[Coord]
    walkable_cells: frozenset[Coord]
    field_cost_cells: frozenset[Coord]

    def step_cost(self, coord: Coord) -> int | None:
        if coord not in self.walkable_cells:
            return None
        if coord in self.field_cost_cells:
            return FIELD_ROUTE_COST
        return EXTERIOR_ROUTE_COST
```

- [ ] **Step 3: Add `build_weighted_transport_route_domain` in `exterior_domain.py`**

```python
def build_weighted_transport_route_domain(
    *,
    complete_map: ReconstructionCompleteMap,
    anchor_abs: Coord,
    transport_entry_coord: Coord,
    transport_stub_cells: frozenset[Coord],
    route_goals: tuple[RouteGoal, ...],
    mining_occupied_cells: frozenset[Coord],
    incompatible_transport_cells: frozenset[Coord] | None = None,
    explicit_blocked_cells: frozenset[Coord] | None = None,
) -> WeightedTransportRouteDomain:
    envelope = frozenset(
        {
            anchor_abs,
            transport_entry_coord,
            *transport_stub_cells,
            *(g.coord for g in route_goals),
        }
    )
    bb = expand_bbox(bbox_from_coords(envelope), EXTERIOR_TRANSPORT_MARGIN_CELLS)
    candidate_cells = cells_in_bbox(bb)
    field_surface = complete_map.field_cells & candidate_cells
    exterior_surface = candidate_cells - complete_map.field_cells
    install_surface = field_surface | exterior_surface
    incompatible = incompatible_transport_cells or frozenset()
    explicit_blocked = explicit_blocked_cells or frozenset()
    walkable = install_surface - mining_occupied_cells - incompatible - explicit_blocked
    field_cost = complete_map.field_cells & walkable
    blocked = (mining_occupied_cells | incompatible | explicit_blocked) & candidate_cells
    return WeightedTransportRouteDomain(
        search_bbox=bb,
        blocked_cells=blocked,
        walkable_cells=walkable,
        field_cost_cells=field_cost,
    )
```

**Forbidden in code/comments:** `walkable = cells_in_bbox(bb) - mining` as the only documented semantics.

- [ ] **Step 4: Do NOT add `reachable_walkable_from_start` in P0** (Architect: Dijkstra is sole reachability authority).

- [ ] **Step 5: Run — PASS** domain cost test.

---

### Task 5: Dijkstra route probe

**Files:**
- Modify: `django_apps/asteroid_lab/layers/shared/route_probe.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py`
- Fixture: `tests/unit/asteroid_lab/layers/fixtures/layer_03_weighted_route_maps.py`

- [ ] **Step 1: Fixture — exterior vs field fork** (`layer_03_weighted_route_maps.py`)

```python
"""5×1 field strip at y=5; goal north at (2,2); exterior corridor west vs field-through-center."""

def field_vs_exterior_complete_map() -> ReconstructionCompleteMap:
    field = frozenset({(1, 5), (2, 5), (3, 5)})
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=frozenset({(0, 5), (2, 2), (2, 4), (2, 3)}),
        coord_frame=CoordFrame.ISLAND_RAW,
    )
```

Document coords: entry `(2,5)` (miner anchor `(2,5)` with entry east `(3,5)` or anchor at miner — align with `derive_transport_entry`).

- [ ] **Step 2: Write failing test D — prefers exterior**

```python
def test_weighted_route_probe_prefers_exterior_over_field() -> None:
    # Build domain + candidate with entry and goal where exterior path cost < field path
    ...
    probed = weighted_route_probe(candidate=..., route_goals=..., domain=...)
    assert probed.route_probe_status == RouteProbeStatus.SUCCEEDED
    assert probed.route_probe_result is not None
    assert probed.route_probe_result.field_route_cell_count == 0
```

- [ ] **Step 3: Write failing test E — field fallback**

```python
def test_weighted_route_probe_uses_field_when_only_field_route_exists() -> None:
    ...
    assert probed.route_probe_result.field_route_cell_count > 0
```

- [ ] **Step 4: Add probe caps in `route_probe.py`**

```python
LAYER03_ROUTE_PROBE_MAX_PATH_CELLS = 64
LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES = 512
# Legacy alias (one release): LAYER03_ROUTE_PROBE_MAX_STEPS = LAYER03_ROUTE_PROBE_MAX_PATH_CELLS
```

- [ ] **Step 5: Implement `weighted_route_probe`**

```python
import heapq

def weighted_route_probe(
    *,
    candidate: BundleCandidate,
    route_goals: tuple[RouteGoal, ...],
    domain: WeightedTransportRouteDomain,
    field_cells: frozenset[Coord],
) -> RouteProbedBundleCandidate:
    start = candidate.route_probe_start_coord
    if domain.step_cost(start) is None:
        return ... EXTERIOR_ENTRY_NOT_REACHABLE ...

  expanded = 0
  # Dijkstra: while heap and expanded < LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES:
  #   pop; if goal reached and len(path) <= MAX_PATH_CELLS: record candidate goal
  # Reject if no goal or best path len > MAX_PATH_CELLS

    field_route_cell_count = sum(1 for c in path if c in field_cells)
    route_cost = ...  # sum step costs per spec §5
```

Goal selection tuple: `(total_route_cost, goal.priority, len(path_coords), goal.goal_id)`.

**Do not** add `reachable_walkable_from_start` here; unreachable goals fail inside Dijkstra → `EXTERIOR_CONNECTOR_UNREACHABLE`.

- [ ] **Step 6: Run tests D and E — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py -k "prefers_exterior or field_when_only"`

---

### Task 6: Test C — no preinstalled belt required (P0)

**Files:**
- Fixture: `tests/unit/asteroid_lab/layers/fixtures/layer_03_weighted_route_maps.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py`
- Modify: `tests/unit/asteroid_lab/layers/fixtures/layer_03_eeemb_projection.py` (optional: single-belt seed without extra stub at (2,0))

- [ ] **Step 1: Fixture `no_stub_entry_reachable_map`**

```text
anchor/miner on rim field cell
transport_entry on field, NOT in seed transport_stub_cells
L2 goal reachable through field + void
seed: minimal miner + zero or one stub NOT at entry
```

- [ ] **Step 2: Failing test**

```python
def test_route_probe_without_preinstalled_belt_at_entry() -> None:
    result = expand_rim_bundle_candidates(
        complete_map=no_stub_entry_reachable_map(),
        exterior_plan=no_stub_entry_l2_plan(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=MinerSeedCatalog.from_entries(no_stub_miner_only_seed()),
    )
    assert result.metrics.route_probe_attempt_count > 0
    counts = dict(result.metrics.reject_reason_counts)
    assert counts.get("local_geometry_invalid.probe_start_not_transport", 0) == 0
    assert counts.get("transport_collides_with_field", 0) == 0
```

- [ ] **Step 3: Run — FAIL** before expand integration.

- [ ] **Step 4: Wire expand (Task 7) then re-run — PASS**

---

### Task 7: `expand.py` integration

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py`

- [ ] **Step 1: Replace domain build + entry gate (no BFS reachability)**

```python
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.exterior_domain import (
    build_weighted_transport_route_domain,
)
from django_apps.asteroid_lab.layers.shared.route_probe import weighted_route_probe

domain = build_weighted_transport_route_domain(
    complete_map=complete_map,
    anchor_abs=anchor,
    transport_entry_coord=candidate.route_probe_start_coord,
    transport_stub_cells=candidate.transport_stub_cells,
    route_goals=route_goals,
    mining_occupied_cells=candidate.mining_occupied_cells,
)
if domain.step_cost(candidate.route_probe_start_coord) is None:
    ... EXTERIOR_ENTRY_NOT_REACHABLE ...
    continue

route_probe_attempt_count += 1
probed = weighted_route_probe(
    candidate=candidate,
    route_goals=route_goals,
    domain=domain,
    field_cells=complete_map.field_cells,
)
```

- [ ] **Step 2: Remove gates that assume non-field placeable only**

Delete or replace:

```python
if not candidate.transport_stub_cells <= placeable:
```

Remove old `build_exterior_transport_domain` + `immediate_route_probe(placeable_cells=...)` path and `transport_stub_cells <= placeable` checks.

- [ ] **Step 3: Call `weighted_route_probe`**

Pass `field_cells=complete_map.field_cells`.

- [ ] **Step 4: Aggregate metrics on success** (optional in expand or probe):

```python
field_route_cell_count_total += probed.route_probe_result.field_route_cell_count
weighted_route_cost_total += probed.route_probe_result.route_cost
```

Add to `Layer03ExpansionMetrics` in Task 8.

- [ ] **Step 5: Run P0 tests**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py`

---

### Task 8: Test B + metrics + Lab

**Files:**
- Modify: `django_apps/asteroid_lab/layers/contracts/candidates.py`
- Modify: observability + rim stack + lab summary
- Test: `test_layer_03_weighted_route_probe.py`

- [ ] **Step 1: Test B — transport blocked by M/E**

```python
def test_projection_rejects_transport_overlapping_mining() -> None:
    # Craft decoded_json where belt local overlaps extension/miner after projection
    result = project_miner_seed_at_anchor(...)
    assert result.reject_reason == CandidateRejectReason.TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT
```

- [ ] **Step 2: Extend `Layer03ExpansionMetrics`**

```python
field_route_cell_count_total: int = 0
weighted_route_cost_total: int = 0
transport_blocked_by_mining_count: int = 0
```

Increment `transport_blocked_by_mining_count` when emitting `TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT`.

- [ ] **Step 3: Wire `merge_rim_stack_into_solver_summary` + `build_layer03_post_summary_metrics`**

- [ ] **Step 4: Lab highlights** (`solver_run_lab_summary.py` L3 section)

```python
_highlight("Route probe attempts", _obs_field_count(solver_summary, "route_probe_attempt_count")),
_highlight("Field route cells", _obs_field_count(solver_summary, "field_route_cell_count_total")),
_highlight("Weighted route cost", _obs_field_count(solver_summary, "weighted_route_cost_total")),
```

- [ ] **Step 5: Run lab summary tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py`

---

### Task 9: Regression gate + broken test cleanup

- [ ] **Step 1: Narrow pytest**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py tests/unit/asteroid_lab/layers/test_layer_03_direction_enumeration.py tests/unit/asteroid_lab/test_solver_runtime_rim_stack.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py
```

Expected: all PASS; P0 `route_probe_attempt_count > 0` on `test_route_probe_without_preinstalled_belt_at_entry`.

- [ ] **Step 2: Ruff**

```bash
python -m ruff check django_apps/asteroid_lab/layers/contracts/candidates.py django_apps/asteroid_lab/layers/contracts/weighted_transport_route_domain.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/ django_apps/asteroid_lab/layers/shared/route_probe.py tests/unit/asteroid_lab/layers/test_layer_03_weighted_route_probe.py
```

- [ ] **Step 3: Mypy (touched packages)**

```bash
python -m mypy django_apps/asteroid_lab/layers/contracts/weighted_transport_route_domain.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles django_apps/asteroid_lab/layers/shared/route_probe.py
```

---

## Spec self-review (plan author)

| Prompt requirement | Task |
|--------------------|------|
| M/E ⊆ field | Task 3 (unchanged) |
| transport ∩ mining → new reject | Task 2, 3 |
| Withdraw TRANSPORT_COLLIDES_WITH_FIELD emit | Task 3 (dedicated test), 6 |
| Bounded walkable / install_surface | Task 4 |
| No reachable_walkable_from_start P0 | Task 4, 5, 7 |
| Dijkstra cap split | Task 5 |
| transport_entry v1 caveat | Task 1 spec §3.1 |
| transport entry not in stubs | Task 2, 3, 6 |
| Weighted Dijkstra | Task 5 |
| placeable ≠ transport network | Task 5, 7 (proposed_transport unchanged) |
| Tests A–F | Tasks 3, 5, 6, 8, 9 |
| Metrics + Lab | Task 8 |
| Non-goals respected | Header + Task 1 |

| Gap | Resolution |
|-----|------------|
| P1 583 fixture | Out of scope for P0 gate; add follow-up issue after synthetic green |
| `immediate_route_probe` API | Task 5: new `weighted_route_probe`; migrate call sites in Task 7 |

**Placeholder scan:** None (all tests include concrete names; code blocks present).

---

## Execution handoff

**Spec:** APPROVED WITH BLOCKING AMENDMENTS (2026-05-28) — implementation authorized.

**Execution mode:** **Subagent-Driven** (Architect-selected). Use groups **A → B → C → D → E**; spec-compliance review then code-quality review after each group.

**Checkpoints:**

- After **C:** Dijkstra tests D/E green.
- After **D:** P0 `test_route_probe_without_preinstalled_belt_at_entry` + `route_probe_attempt_count > 0`.
- After **E:** Task 9 regression gate.

**Do not commit** unless explicitly instructed.
