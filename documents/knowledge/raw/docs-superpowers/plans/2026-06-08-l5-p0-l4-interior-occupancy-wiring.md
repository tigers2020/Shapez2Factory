# PR-L5-P0 — L4 Interior Occupancy → L5 Route Domain Wiring

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `interior_occupied_cells` from L4 inner fill into L5 transport routing so occupied interior cells are **hard blocked** in A* search and commit validation, preserving stub/connector/trunk attach whitelists.

**Architecture:** Extend existing R1 sequential router (`layer_04_transport_routing/` package, canonical `run_layer_05_transport_routing`). `build_l4_route_search_domain()` subtracts L4 occupied cells from walkable set. `L4CommitValidator` rejects paths through those cells with `INTERIOR_OCCUPIED_BLOCKED`. `stack_runner` already passes `last_inner_fill.interior_occupied_cells` — stop ignoring it in `run.py`. No trunk-traverse v2, no 3D Z routing, no L3 changes.

**Tech Stack:** Python 3.12+, `src/shapez2_factory/`, pytest, ruff, mypy, black. Validation per `AGENTS.md`.

**Spec:** [`docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md`](../specs/2026-05-31-layer-04-transport-routing-design.md) § “L4 interior occupancy (normative, PR-L5-P0)”.

**Non-goals (this PR):**

- Trunk traverse v2 / global min-cost routing
- Mixed-kind dual L5 runs
- L3 `PenaltyMode` changes
- Sprite oracle / Turn-Merger expansion
- Multilayer blueprint `Z` → solver 3D domain
- Stack strict mode requiring `transport_catalog` (defer → follow-up note only)

**Status note (2026-06-08):** Core implementation + tests may already exist locally uncommitted. Tasks below are verify-or-implement; run tests first.

**Verification (PR gate):**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer05_l4_interior_occupancy.py -v
python -m pytest tests/unit/asteroid_lab/layers/test_layer04_route_domain.py tests/unit/asteroid_lab/layers/test_layer04_commit_validator.py tests/unit/asteroid_lab/layers/test_layer04_sequential_router.py -v
powershell -File scripts/test_fast.ps1
ruff check .
mypy django_apps config src
black --check .
```

---

## File structure

| Path | Responsibility |
|------|----------------|
| `src/.../contracts/layer05_route.py` | Add `INTERIOR_OCCUPIED_BLOCKED` to `Layer05FailureReason` |
| `src/.../layer_04_transport_routing/route_domain.py` | `interior_occupied_cells` hard block in walkable |
| `src/.../layer_04_transport_routing/commit_validator.py` | Interior overlap + trunk attach whitelist |
| `src/.../layer_04_transport_routing/sequential_router.py` | Thread interior into domain/validator; `ROUTE_NOT_FOUND` detail |
| `src/.../layer_04_transport_routing/run.py` | Pass `interior_occupied_cells` (remove `_ =` discard) |
| `tests/.../fixtures/l5_l4_occupancy_barrier.py` | Named choke / detour fixture maps |
| `tests/.../test_layer05_l4_interior_occupancy.py` | PR acceptance pack (4+ tests) |
| `docs/.../layer-04-transport-routing-design.md` | Normative § already added — verify wording |

**Unchanged (must stay green):**

- `stack_runner.py` — already passes `interior_occupied_cells=last_inner_fill.interior_occupied_cells`
- L3 route probe — witness only; no coupling

---

## Task 1: Failure reason contract

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_route.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer04_route_contracts.py`

- [ ] **Step 1: Write the failing test**

```python
def test_layer05_failure_reason_interior_occupied_blocked() -> None:
    from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
        Layer05FailureReason,
    )

    assert Layer05FailureReason.INTERIOR_OCCUPIED_BLOCKED.value == "interior_occupied_blocked"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer04_route_contracts.py::test_layer05_failure_reason_interior_occupied_blocked -v`

Expected: FAIL if enum member missing.

- [ ] **Step 3: Add enum member**

In `layer05_route.py` inside `class Layer05FailureReason(StrEnum)` after `COMMIT_OVERLAP_BLOCKED`:

```python
INTERIOR_OCCUPIED_BLOCKED = "interior_occupied_blocked"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer04_route_contracts.py -v`

Expected: PASS

---

## Task 2: Route domain hard block

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/route_domain.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer05_l4_interior_occupancy.py`

- [ ] **Step 1: Write the failing test**

```python
def test_l5_interior_block_excluded_from_walkable_domain() -> None:
    from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing import (
        route_domain,
    )
    from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
        build_rect_field_with_void_shell,
    )

    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    interior = frozenset({(1, 1)})
    domain = route_domain.build_l4_route_search_domain(
        complete_map=cm,
        miner_cells=frozenset(),
        extension_cells=frozenset(),
        interior_occupied_cells=interior,
    )
    assert (1, 1) not in domain.walkable_cells
```

- [ ] **Step 2: Run test — expect FAIL** if param ignored.

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer05_l4_interior_occupancy.py::test_l5_interior_block_excluded_from_walkable_domain -v`

- [ ] **Step 3: Implement domain subtraction**

In `build_l4_route_search_domain`, add parameter and subtract interior (minus L3 equipment):

```python
def build_l4_route_search_domain(
    *,
    complete_map: ReconstructionCompleteMap,
    miner_cells: frozenset[Coord],
    extension_cells: frozenset[Coord],
    interior_occupied_cells: frozenset[Coord] = frozenset(),
) -> L4RouteSearchDomain:
    field_cells = complete_map.field_cells
    void_cells = complete_map.external_void_cells - field_cells
    equipment = miner_cells | extension_cells
    interior_block = interior_occupied_cells - equipment
    walkable = (void_cells | field_cells | equipment) - interior_block
    ...
```

- [ ] **Step 4: Run test — expect PASS**

---

## Task 3: Commit validator interior + trunk whitelist

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/commit_validator.py`

- [ ] **Step 1: Write failing validator tests**

```python
def test_l5_blocks_l4_interior_occupied_cell() -> None:
    from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
        Layer04FailureReason,
    )
    from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing import (
        commit_validator,
    )

    v = commit_validator.L4CommitValidator(
        equipment_cells=frozenset({(2, 2)}),
        connector_cells=frozenset({(5, 2)}),
        stub_cells=frozenset({(3, 2)}),
        interior_occupied_cells=frozenset({(4, 2)}),
    )
    assert v.validate_route_cell((4, 2)) is Layer04FailureReason.INTERIOR_OCCUPIED_BLOCKED


def test_l5_allows_source_stub_and_connector_whitelist() -> None:
    from tests.unit.asteroid_lab.layers.fixtures.l5_l4_occupancy_barrier import (
        L5_L4_CHOKE_VOID,
        L5_L4_CONNECTOR,
        L5_L4_MINER,
        L5_L4_STUB,
    )
    from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing import (
        commit_validator,
    )

    v = commit_validator.L4CommitValidator(
        equipment_cells=frozenset({L5_L4_MINER}),
        connector_cells=frozenset({L5_L4_CONNECTOR}),
        stub_cells=frozenset({L5_L4_STUB}),
        interior_occupied_cells=frozenset({L5_L4_CHOKE_VOID}),
    )
    assert v.validate_route_cell(L5_L4_STUB) is None
    assert v.validate_route_cell(L5_L4_CONNECTOR) is None
```

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Extend `L4CommitValidator`**

```python
@dataclass(frozen=True, slots=True)
class L4CommitValidator:
    equipment_cells: frozenset[Coord]
    connector_cells: frozenset[Coord]
    stub_cells: frozenset[Coord]
    interior_occupied_cells: frozenset[Coord] = frozenset()
    trunk_attach_cells: frozenset[Coord] = frozenset()

    def validate_route_cell(self, coord: Coord) -> Layer04FailureReason | None:
        if coord in self.connector_cells or coord in self.stub_cells:
            return None
        if coord in self.trunk_attach_cells:
            return None
        if coord in self.interior_occupied_cells:
            return Layer04FailureReason.INTERIOR_OCCUPIED_BLOCKED
        if coord in self.equipment_cells:
            return Layer04FailureReason.COMMIT_OVERLAP_BLOCKED
        return None
```

- [ ] **Step 4: Run tests — expect PASS**

---

## Task 4: Sequential router + run orchestrator wiring

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py`
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py`

- [ ] **Step 1: Write named fixture**

Create `tests/unit/asteroid_lab/layers/fixtures/l5_l4_occupancy_barrier.py` with:

- `l5_l4_occupancy_barrier_no_detour_map()` — single west void choke, no south detour
- `l5_l4_occupancy_barrier_basic_map()` — same choke + south detour void row
- `l5_l4_occupancy_barrier_rim_result()` — one miner at `(3,0)`, stub at `(2,0)`, connector at `(-1,0)`
- `l5_l4_occupancy_barrier_exterior_plan()` — west `ExteriorConnector`

- [ ] **Step 2: Write integration tests**

```python
def test_l5_reroutes_around_l4_interior_occupied_cell() -> None:
    # baseline: no_detour map, no interior → path uses choke (1,0)
    # blocked: basic map + interior {(1,0)} → path avoids choke, uses south detour
    ...
    assert L5_L4_CHOKE_VOID in baseline.routes[0].path_coords
    assert L5_L4_CHOKE_VOID not in blocked.routes[0].path_coords


def test_l5_route_not_found_when_l4_blocks_all_paths() -> None:
    # no_detour map + interior blocks choke + west void cells → ROUTE_NOT_FOUND
    ...
    assert failure.reason is Layer04FailureReason.ROUTE_NOT_FOUND
    assert "blocked_by_l4_interior_count=" in failure.detail


def test_run_layer_05_wires_interior_occupied_cells() -> None:
    plan = run.run_layer_05_transport_routing(
        ...,
        interior_occupied_cells=frozenset({L5_L4_CHOKE_VOID}),
    )
    assert L5_L4_CHOKE_VOID not in plan.routes[0].path_coords
```

- [ ] **Step 3: Thread `interior_occupied_cells` in `route_layer04_sequential`**

Add parameter `interior_occupied_cells: frozenset[tuple[int, int]] = frozenset()`.

Pass to `build_l4_route_search_domain(..., interior_occupied_cells=interior_block)`.

On `ROUTE_NOT_FOUND`, set `detail`:

```python
detail=(
    f"source_id={source.placement_id};"
    f"blocked_by_l4_interior_count={len(interior_block)};"
    f"blocked_by_equipment_count={len(equipment_cells)}"
)
```

Per-source commit validation: build fresh `L4CommitValidator` with `trunk_attach_cells=frozenset(g.coord for g in registry.trunk_goals())`.

- [ ] **Step 4: Fix `run_layer_05_transport_routing`**

Remove `_ = interior_occupied_cells`. Normalize and forward:

```python
interior = (
    frozenset(interior_occupied_cells)
    if interior_occupied_cells is not None
    else frozenset()
)
return route_layer04_sequential(..., interior_occupied_cells=interior)
```

- [ ] **Step 5: Run full PR test file**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer05_l4_interior_occupancy.py -v`

Expected: 6 passed

---

## Task 5: Regression gate + docs

**Files:**
- Verify: `docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md` § L4 interior occupancy

- [ ] **Step 1: Run L4 regression slice**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer04_route_domain.py tests/unit/asteroid_lab/layers/test_layer04_commit_validator.py tests/unit/asteroid_lab/layers/test_layer04_sequential_router.py -v
```

Expected: all PASS (no behavior change when `interior_occupied_cells` empty).

- [ ] **Step 2: Run full fast gate**

```bash
powershell -File scripts/test_fast.ps1
ruff check .
mypy django_apps config src
black --check .
```

- [ ] **Step 3: Commit (only when user requests)**

```bash
git add src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_route.py \
  src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/ \
  tests/unit/asteroid_lab/layers/fixtures/l5_l4_occupancy_barrier.py \
  tests/unit/asteroid_lab/layers/test_layer05_l4_interior_occupancy.py \
  tests/unit/asteroid_lab/layers/test_layer04_route_contracts.py \
  docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md
git commit -m "$(cat <<'EOF'
fix(l5): wire L4 interior occupancy into route domain

Hard-block interior_occupied_cells in L5 A* and commit validator so
transport routing respects L4 fill before commit.
EOF
)"
```

---

## Self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| `interior_occupied_cells` hard block in search domain | Task 2 |
| `INTERIOR_OCCUPIED_BLOCKED` on commit | Task 1, 3 |
| Stub / connector / trunk attach whitelist | Task 3, 4 |
| `run_layer_05` stops ignoring input | Task 4 |
| `ROUTE_NOT_FOUND` observability detail | Task 4 |
| Named fixture reroute + fail | Task 4 |
| No trunk traverse / no L3 changes | Non-goals |
| Stack strict `transport_catalog` | Deferred (text) |

**Placeholder scan:** None.

---

## Deferred (text only — not this PR)

1. **L3↔L5 drift fixture** — L3 commit set + L5 run on named map; assert probe-feasible ≠ L5 failure taxonomy.
2. **Large fluid L5 capacity regression** — extend PR-1 large map fixture to L5 layer.
3. **Blueprint `Z` → `DecodedCellDTO.layer`** — copy JSON multilayer transport (user 3-floor belt paste).
4. **Stack strict mode** — fail closed when `transport_catalog is None` on full stack runs.
5. **Trunk traverse v2** — separate spec amendment.

---

## Execution Handoff

Plan saved to `docs/superpowers/plans/2026-06-08-l5-p0-l4-interior-occupancy-wiring.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks
2. **Inline Execution** — run tasks in this session (`executing-plans`), checkpoint after Task 4

**Note:** Local workspace may already satisfy Tasks 1–4. Start with Task 4 Step 5 verification; only implement deltas if red.
