# Layer 03 Virtual Exterior Transport Domain — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace L3 transport installability SoT (`transport ⊆ external_void_cells`) with a bounded **virtual exterior transport domain** so belt/pipe may use map-absolute coordinates outside finite `external_void_cells` while M/E stay on `field_cells`, restoring `route_probe_attempt_count > 0` on a synthetic fixture.

**Architecture:** `project_miner_seed_at_anchor` keeps projection + local checks only (no domain, no route_goals). `build_exterior_transport_domain` runs in `expand.py` after a successful projection; `immediate_route_probe` uses `domain.traversable_cells`. Rename `select_fieldward_output_dir` → `select_exterior_output_dir`. `TRANSPORT_STUB_NOT_IN_VOID` never emitted on new paths.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy, `ReconstructionCompleteMap`, `BBox`/`cells_in_bbox` from `snapshots/grid_contract.py`

**Spec:** [`2026-05-28-layer-03-virtual-exterior-transport-domain-design.md`](../specs/2026-05-28-layer-03-virtual-exterior-transport-domain-design.md) (APPROVED)

**Work classification:** contract change · implementation change

**Blocked plan:** [`2026-05-28-layer-03-rim-void-depth-projection.md`](2026-05-28-layer-03-rim-void-depth-projection.md) — do not implement for pool recovery

**Branch suggestion:** `feat/layer-03-virtual-exterior-transport`

**pytest:** No `-q`, `--quiet`, or `--tb=no`.

---

## File map

| Action | Path |
|--------|------|
| Create | `django_apps/asteroid_lab/layers/contracts/exterior_transport_domain.py` |
| Create | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/exterior_domain.py` |
| Modify | `django_apps/asteroid_lab/layers/contracts/candidates.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/project.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/rim_anchors.py` |
| Modify | `django_apps/asteroid_lab/layers/shared/route_probe.py` |
| Modify | `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` (optional wire) |
| Modify | `docs/superpowers/specs/2026-05-28-layer-03-rim-mining-bundles-design.md` §1.2 |
| Create | `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py` |
| Create | `tests/unit/asteroid_lab/layers/fixtures/layer_03_virtual_exterior_map.py` |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py` |

---

### Task 1: New `CandidateRejectReason` values

**Files:**
- Modify: `django_apps/asteroid_lab/layers/contracts/candidates.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py`

- [ ] **Step 1: Write failing test**

```python
def test_new_exterior_transport_reject_reasons_exist() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import CandidateRejectReason

    assert CandidateRejectReason.TRANSPORT_COLLIDES_WITH_FIELD.value == (
        "transport_collides_with_field"
    )
    assert CandidateRejectReason.EXTERIOR_ENTRY_NOT_REACHABLE.value == (
        "exterior_entry_not_reachable"
    )
    assert CandidateRejectReason.EXTERIOR_CONNECTOR_UNREACHABLE.value == (
        "exterior_connector_unreachable"
    )
```

- [ ] **Step 2: Run — FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py::test_new_exterior_transport_reject_reasons_exist`

- [ ] **Step 3: Add enum members** (keep `TRANSPORT_STUB_NOT_IN_VOID` unchanged for wire compat)

```python
TRANSPORT_COLLIDES_WITH_FIELD = "transport_collides_with_field"
EXTERIOR_ENTRY_NOT_REACHABLE = "exterior_entry_not_reachable"
EXTERIOR_CONNECTOR_UNREACHABLE = "exterior_connector_unreachable"
```

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit (if user requested)**

---

### Task 2: `ExteriorTransportDomain` contract DTO

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/exterior_transport_domain.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py`

- [ ] **Step 1: Write failing test**

```python
def test_exterior_transport_domain_frozen() -> None:
    from django_apps.asteroid_lab.layers.contracts.exterior_transport_domain import (
        ExteriorTransportDomain,
    )
    from django_apps.asteroid_lab.snapshots.grid_contract import BBox

    domain = ExteriorTransportDomain(
        search_bbox=BBox(0, 10, 0, 10),
        blocked_field_cells=frozenset({(5, 5)}),
        traversable_cells=frozenset({(4, 5), (3, 5)}),
    )
    assert (4, 5) in domain.traversable_cells
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement**

```python
@dataclass(frozen=True, slots=True)
class ExteriorTransportDomain:
    search_bbox: BBox
    blocked_field_cells: frozenset[Coord]
    traversable_cells: frozenset[Coord]
```

Export from `layers/contracts/__init__.py` if that module re-exports contracts (match sibling pattern).

- [ ] **Step 4: Run — PASS**

---

### Task 3: `build_exterior_transport_domain` + BFS

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/exterior_domain.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py`

- [ ] **Step 1: Write failing tests**

```python
EXTERIOR_TRANSPORT_MARGIN_CELLS = 8  # must match module const


def test_traversable_includes_virtual_cell_outside_external_void() -> None:
    """Transport coord not in external_void_cells but in domain component."""
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.exterior_domain import (
        build_exterior_transport_domain,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_virtual_exterior_map import (
        virtual_exterior_complete_map,
        virtual_exterior_route_goals,
    )

    complete = virtual_exterior_complete_map()
    anchor = (5, 5)
    stub_cells = frozenset({(4, 5), (3, 5), (2, 5)})  # (2,5) outside finite void in fixture
    start = (2, 5)
    goals = virtual_exterior_route_goals()
    domain = build_exterior_transport_domain(
        complete_map=complete,
        anchor_abs=anchor,
        transport_stub_cells=stub_cells,
        route_goals=goals,
        route_probe_start=start,
    )
    assert (2, 5) not in complete.external_void_cells
    assert (2, 5) in domain.traversable_cells


def test_interior_hole_not_traversable() -> None:
    """Non-field cell inside asteroid hole is not in start component."""
    ...
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement `exterior_domain.py`**

```python
EXTERIOR_TRANSPORT_MARGIN_CELLS = 8

def build_exterior_transport_domain(
    *,
    complete_map: ReconstructionCompleteMap,
    anchor_abs: Coord,
    transport_stub_cells: frozenset[Coord],
    route_goals: tuple[RouteGoal, ...],
    route_probe_start: Coord,
) -> ExteriorTransportDomain:
    envelope = frozenset(
        {anchor_abs, route_probe_start, *transport_stub_cells, *(g.coord for g in route_goals)}
    )
    bb = expand_bbox(bbox_from_coords(envelope), EXTERIOR_TRANSPORT_MARGIN_CELLS)
    bbox_cells = cells_in_bbox(bb)
    field_in_bbox = complete_map.field_cells & bbox_cells
    nodes = bbox_cells - field_in_bbox
    traversable = _connected_component_from_start(route_probe_start, nodes=nodes)
    return ExteriorTransportDomain(
        search_bbox=bb,
        blocked_field_cells=field_in_bbox,
        traversable_cells=traversable,
    )


def _connected_component_from_start(start: Coord, *, nodes: frozenset[Coord]) -> frozenset[Coord]:
    if start not in nodes:
        return frozenset()
    seen: set[Coord] = {start}
    queue: deque[Coord] = deque([start])
    while queue:
        cur = queue.popleft()
        for nb in neighbors4(cur):
            if nb in seen or nb not in nodes:
                continue
            seen.add(nb)
            queue.append(nb)
    return frozenset(seen)
```

- [ ] **Step 4: Run unit tests — PASS**

---

### Task 4: Rename `select_exterior_output_dir`

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/rim_anchors.py`
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py`
- Modify: `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py`

- [ ] **Step 1: Rename function** (keep thin alias one release if tests import old name — prefer full rename per spec)

```python
def select_exterior_output_dir(
    anchor: Coord,
    *,
    complete_map: ReconstructionCompleteMap,
    route_goals: tuple[RouteGoal, ...],
    transport_kind: TransportKind,
) -> Direction | None:
    ...

# Deprecated alias — remove in follow-up if desired:
select_fieldward_output_dir = select_exterior_output_dir
```

Update `__all__` to export `select_exterior_output_dir` first.

- [ ] **Step 2: Update expand + tests** to call `select_exterior_output_dir`

- [ ] **Step 3: Run**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py`

Expected: PASS

---

### Task 5: `project_miner_seed_at_anchor` — local geometry only

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/project.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py`

- [ ] **Step 1: Write failing test**

```python
def test_projection_rejects_transport_on_field_with_new_reason() -> None:
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.project import (
        project_miner_seed_at_anchor,
    )
    # Craft seed/decoded_json or complete_map so rotated belt lands on field cell
    ...
    assert result.reject_reason == CandidateRejectReason.TRANSPORT_COLLIDES_WITH_FIELD


def test_projection_does_not_emit_transport_stub_not_in_void() -> None:
    """Stub outside external_void_cells but not on field → projection succeeds."""
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_virtual_exterior_map import (
        virtual_exterior_complete_map,
        virtual_exterior_m0e_seed,
    )
    result = project_miner_seed_at_anchor(
        seed=virtual_exterior_m0e_seed(),
        anchor_coord=(5, 5),
        output_dir=Direction.W,
        ...
    )
    assert result.candidate is not None
    assert result.reject_reason is None
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Replace validation block**

Remove:

```python
if transport_cells - complete_map.external_void_cells:
    return ProjectionResult(
        candidate=None,
        reject_reason=CandidateRejectReason.TRANSPORT_STUB_NOT_IN_VOID,
    )
```

Add before mining/transport overlap check:

```python
if transport_cells & complete_map.field_cells:
    return ProjectionResult(
        candidate=None,
        reject_reason=CandidateRejectReason.TRANSPORT_COLLIDES_WITH_FIELD,
    )
```

Keep `MINING_CELL_OFF_FIELD`, anchor-on-miner, probe-start checks unchanged.

- [ ] **Step 4: Run — PASS**

---

### Task 6: `expand.py` — domain after projection

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py`
- Create: `tests/unit/asteroid_lab/layers/fixtures/layer_03_virtual_exterior_map.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py`

- [ ] **Step 1: Create fixture** `layer_03_virtual_exterior_map.py`

Design (document in fixture docstring):

```text
Field 3×3 at x=5..7, y=4..6.
external_void_cells from acceptance_topology includes only immediate bbox padding.
Explicit void at (4,5) west of anchor (5,5).
Connector goal at (2, 12) — outside pre-existing external_void at y=12 corridor.
Seed m0e belt west: stubs (4,5), (3,5), (2,5) — (2,5) virtual.
```

Include `virtual_exterior_complete_map()`, `virtual_exterior_l2_plan()`, `virtual_exterior_route_goals()` via `build_layer03_route_goals`, and `virtual_exterior_m0e_seed()` MinerSeedEntry.

- [ ] **Step 2: Write failing P0 expansion test**

```python
def test_virtual_exterior_expansion_route_probe_succeeds() -> None:
    result = expand_rim_bundle_candidates(
        complete_map=virtual_exterior_complete_map(),
        exterior_plan=virtual_exterior_l2_plan(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=MinerSeedCatalog.from_entries(virtual_exterior_m0e_seed()),
    )
    assert result.metrics.route_probe_attempt_count > 0
    assert result.metrics.normal_candidate_count > 0
```

- [ ] **Step 3: Run — FAIL**

- [ ] **Step 4: Wire expand loop**

After `projection.candidate is not None`:

```python
candidate = projection.candidate
domain = build_exterior_transport_domain(
    complete_map=complete_map,
    anchor_abs=anchor,
    transport_stub_cells=candidate.transport_stub_cells,
    route_goals=route_goals,
    route_probe_start=candidate.route_probe_start_coord,
)
if not candidate.transport_stub_cells <= domain.traversable_cells:
    local_geometry_rejected_count += 1
    diagnostics.append(
        RouteProbedBundleCandidate(
            candidate=candidate,
            route_probe_status=RouteProbeStatus.SKIPPED_GEOMETRY,
            route_probe_result=None,
            route_goal_id=None,
            reject_reason=CandidateRejectReason.EXTERIOR_ENTRY_NOT_REACHABLE,
        )
    )
    continue

route_probe_attempt_count += 1
probed = immediate_route_probe(
    candidate=candidate,
    route_goals=route_goals,
    traversable_void=domain.traversable_cells,
)
```

Replace `traversable_void=complete_map.external_void_cells` with domain everywhere in expand.

Use `select_exterior_output_dir` at anchor loop.

- [ ] **Step 5: Run**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py`

Expected: PASS including P0 gate

---

### Task 7: `immediate_route_probe` — `EXTERIOR_CONNECTOR_UNREACHABLE`

**Files:**
- Modify: `django_apps/asteroid_lab/layers/shared/route_probe.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py` (extend)

- [ ] **Step 1: Write failing test**

```python
def test_probe_start_not_in_traversable_returns_exterior_entry_not_reachable() -> None:
    probed = immediate_route_probe(
        candidate=...,
        route_goals=...,
        traversable_void=frozenset(),  # empty
    )
    assert probed.reject_reason == CandidateRejectReason.EXTERIOR_ENTRY_NOT_REACHABLE


def test_no_reachable_goal_returns_exterior_connector_unreachable() -> None:
    probed = immediate_route_probe(
        candidate=...,
        route_goals=(goal_far_unconnected,),
        traversable_void=frozenset({start_only}),
    )
    assert probed.reject_reason == CandidateRejectReason.EXTERIOR_CONNECTOR_UNREACHABLE
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Update `route_probe.py`**

```python
if start not in traversable_void:
    return RouteProbedBundleCandidate(
        ...
        reject_reason=CandidateRejectReason.EXTERIOR_ENTRY_NOT_REACHABLE,
    )
...
if not reachable_goals:
    return RouteProbedBundleCandidate(
        ...
        reject_reason=CandidateRejectReason.EXTERIOR_CONNECTOR_UNREACHABLE,
    )
```

Keep `ROUTE_PROBE_FAILED` only for `matching` goals empty if still needed.

- [ ] **Step 4: Run probe tests — PASS**

---

### Task 8: Parent L3 spec §1.2 patch

**Files:**
- Modify: `docs/superpowers/specs/2026-05-28-layer-03-rim-mining-bundles-design.md`

- [ ] **Step 1: Replace A′′ bullet** `transport_stub_cells ⊆ external_void_cells` with:

```text
transport_stub_cells ∩ field_cells = ∅
transport_stub_cells ⊆ exterior_transport_traversable (L3 virtual domain — see virtual-exterior-transport-domain spec)
mining_occupied_cells ⊆ field_cells
```

- [ ] **Step 2: Add cross-link** to virtual exterior spec in §4 Related documents.

---

### Task 9: Regression + full narrow gate

- [ ] **Step 1: Run L3/L4 stack tests**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py tests/unit/asteroid_lab/test_solver_runtime_entry_layer02.py
```

Expected: all PASS; P0: `test_virtual_exterior_expansion_route_probe_succeeds` shows `route_probe_attempt_count > 0`.

- [ ] **Step 2: Ruff + mypy**

```bash
python -m ruff check django_apps/asteroid_lab/layers/contracts/exterior_transport_domain.py django_apps/asteroid_lab/layers/contracts/candidates.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/exterior_domain.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/project.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/rim_anchors.py django_apps/asteroid_lab/layers/shared/route_probe.py
python -m mypy django_apps/asteroid_lab/layers/contracts/exterior_transport_domain.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/exterior_domain.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/project.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py
```

---

## Plan self-review (spec coverage)

| Spec § | Task |
|--------|------|
| §2 M/E on field | Task 5 |
| §2 transport not on field, virtual domain | Tasks 3, 5, 6 |
| §3 domain builder | Task 2–3 |
| §4 projection boundary (no domain in project) | Task 5 |
| §5 route probe SoT | Tasks 6–7 |
| §6 `select_exterior_output_dir` | Task 4 |
| §7 T1–T6 P0 | Tasks 1–7, 9 |
| §12 Decision A `TRANSPORT_STUB_NOT_IN_VOID` | Task 5 test |
| §9 parent patch | Task 8 |

**Placeholder scan:** None.

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-28-layer-03-virtual-exterior-transport-domain.md`.

**Spec updated to** `APPROVED (2026-05-28)` at [`2026-05-28-layer-03-virtual-exterior-transport-domain-design.md`](../specs/2026-05-28-layer-03-virtual-exterior-transport-domain-design.md).

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session with `executing-plans`, batch checkpoints  

Which approach do you want?
