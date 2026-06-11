# Layer 04 Transport Routing Implementation Plan

> **Renumber (2026-05-31):** Canonical stack slug for transport is **`layer_05_transport_routing` (L5)**; inner fill is **L4**. Implement renumber PR-1 from [`2026-05-31-layer-stack-l4-l5-renumber`](../2026-05-31-layer-stack-l4-l5-renumber/README.md) before adding new transport features on old L4 naming. Physical package `layer_04_transport_routing/` remains until PR-2.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement merge-aware weighted transport routing from L3 `m_output_stub` to L2 connectors, with catalog-backed `SpaceBelt_*` / `SpacePipe_*` tile projection, as the sole authoritative transport layer for replay.

**Architecture:** V1 slug `layer_04_transport_routing`; R1 sequential A* with trunk-as-goal attach; C1 JSON catalog port at Django boundary; L3 `route_probe_path` witness-only (W5). L4 source adapter maps `throughput_factor` → `source_load_m`. Search uses L4 weights; commit uses separate whitelist validator.

**Tech Stack:** Python 3.12, `src/shapez2_factory/` (core), `django_apps/asteroid_lab/` (adapters/replay), pytest, ruff, mypy, black.

**Spec:** [`docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md`](../../specs/2026-05-31-layer-04-transport-routing-design.md) (APPROVED §1).

**Approval gate:** Implement PR-L4-0 before algorithm code.

**Verification (narrow):** `python -m pytest <path> -v`  
**Verification (PR):** `powershell -File scripts/test_fast.ps1` → `ruff check .` → `mypy django_apps config src` → `black --check .`

---

## File structure

**Create (core):**

| Path | Responsibility |
|------|----------------|
| `src/.../layers/contracts/layer04_route.py` | `Layer04RoutePlan`, `Layer04SourceView`, failures, tiles |
| `src/.../layers/layer_04_transport_routing/run.py` | Orchestrator |
| `src/.../layers/layer_04_transport_routing/source_adapter.py` | `rim_result` → `Layer04SourceView` |
| `src/.../layers/layer_04_transport_routing/route_domain.py` | `L4RouteSearchDomain` + terrain weights |
| `src/.../layers/layer_04_transport_routing/astar.py` | A* with deterministic tie-break |
| `src/.../layers/layer_04_transport_routing/sequential_router.py` | R1 main loop |
| `src/.../layers/layer_04_transport_routing/merge_groups.py` | Union-find groups + capacity |
| `src/.../layers/layer_04_transport_routing/commit_validator.py` | e/m whitelist |
| `src/.../layers/layer_04_transport_routing/sprite_projector.py` | Path → ESWN → catalog tile |
| `src/.../application/asteroid_lab/ports/space_transport_catalog.py` | Protocol |
| `src/.../adapters/asteroid_lab/space_transport_catalog_snapshot.py` | Pure snapshot DTO |

**Create (Django):**

| Path | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/services/space_transport_catalog_import.py` | JSON → snapshot |
| `django_apps/asteroid_lab/replay/layer04_transport_segment.py` | Replay from `transport_tiles` |

**Modify:**

| Path | Change |
|------|--------|
| `layers/contracts/layer_slugs.py` | Add `LAYER_04_TRANSPORT_ROUTING`; deprecate rim slug |
| `layers/contracts/rim_greedy.py` | Add `throughput_factor` to `CommittedRimSeedPlacement` |
| `layer_03_rim_greedy_placement/commit_finalize.py` | Populate `throughput_factor` from candidate |
| `stack_runner.py` | Run L4 between L3 and L5; pass `Layer04RoutePlan` to L5 |
| `docs/.../layer-03-rim-placement-v2-design.md` | L3 amendment (witness / L4 authority) |
| `test_layer_04_disabled_shim.py` | Replace with transport routing smoke / migration |

**Deprecate (migration period):**

| Path | Change |
|------|--------|
| `layer_04_rim_bundle_placement/run.py` | Re-export `run_layer_04_transport_routing` + `DeprecationWarning` |

---

## Phase L4-0 — Contract + L3 amendment

### Task 0.1: L3 spec amendment (docs only)

**Files:**
- Modify: `docs/superpowers/specs/2026-05-31-layer-03-rim-placement-v2-design.md:53-58` and new § “Transport authority”

- [ ] **Step 1:** Replace non-goal “Rim bundle packing role of L4 (remains disabled)” with “Final transport routing is Layer 04; L3 does not emit committed SpaceBelt/SpacePipe tiles.”
- [ ] **Step 2:** Add witness-only paragraph (W1–W4) and L4 sole authority paragraph from spec § “Required L3 spec amendment”.
- [ ] **Step 3:** Commit docs only when user requests commit.

---

### Task 0.2: Layer04 failure enum + route plan DTOs

**Files:**
- Create: `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer04_route.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer04_route_contracts.py`

- [ ] **Step 1: Write failing test**

```python
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04FailureReason,
    Layer04RoutePlan,
    Layer04SourceView,
    ProjectedTransportTile,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord


def test_layer04_failure_reason_route_not_found():
    assert Layer04FailureReason.ROUTE_NOT_FOUND.value == "route_not_found"


def test_layer04_source_view_frozen():
    v = Layer04SourceView(
        placement_id="p1",
        m_output_stub=Coord(1, 0),
        source_load_m=12,
        throughput_factor=12,
        equipment_cells=frozenset(),
        route_probe_path=(),
    )
    assert v.source_load_m == 12


def test_layer04_route_plan_empty():
    plan = Layer04RoutePlan.empty(resource_kind="shape", transport_kind="space_belt")
    assert plan.transport_tiles == ()
    assert plan.failures == ()
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer04_route_contracts.py -v`  
Expected: `ModuleNotFoundError: layer04_route`

- [ ] **Step 3: Implement DTOs**

```python
# layer04_route.py (minimal skeleton)
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

class Layer04FailureReason(StrEnum):
    MISSING_L2_EXTERIOR_PLAN = "missing_l2_exterior_plan"
    EMPTY_L3_PACKAGE = "empty_l3_package"
    RESOURCE_KIND_MISMATCH = "resource_kind_mismatch"
    MIX_UNSUPPORTED = "mix_unsupported"
    NO_CONNECTOR_WITH_CAPACITY = "no_connector_with_capacity"
    ROUTE_NOT_FOUND = "route_not_found"
    CAPACITY_OVERFLOW = "capacity_overflow"
    COMMIT_OVERLAP_BLOCKED = "commit_overlap_blocked"
    CATALOG_MISSING_TILE = "catalog_missing_tile"
    UNSUPPORTED_IO_SIGNATURE = "unsupported_io_signature"

@dataclass(frozen=True, slots=True)
class Layer04SourceView:
    placement_id: str
    m_output_stub: Coord
    source_load_m: int
    throughput_factor: int
    equipment_cells: frozenset[Coord]
    route_probe_path: tuple[Coord, ...]

# ... CommittedRoute, RouteGroupSummary, ProjectedTransportTile,
# Layer04Failure, Layer04Metrics, Layer04RoutePlan with .empty()
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Step 5: Export from contracts `__init__` if project pattern requires**

---

### Task 0.3: Add `throughput_factor` to `CommittedRimSeedPlacement`

**Files:**
- Modify: `src/.../layers/contracts/rim_greedy.py:67-77`
- Modify: `src/.../layer_03_rim_greedy_placement/commit_finalize.py:164-174`
- Test: `tests/unit/asteroid_lab/layers/test_layer04_source_adapter.py`

- [ ] **Step 1: Failing test**

```python
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.source_adapter import (
    build_layer04_sources,
)


def test_source_load_m_equals_throughput_factor(minimal_rim_result):
    views = build_layer04_sources(minimal_rim_result)
    assert views[0].source_load_m == views[0].throughput_factor == 16
```

- [ ] **Step 2: Run — FAIL** (field / adapter missing)

- [ ] **Step 3: Add field + wire commit_finalize**

```python
return CommittedRimSeedPlacement(
  ...
  throughput_factor=cand.throughput_factor,
  route_probe_path=path,
)
```

- [ ] **Step 4: Implement `source_adapter.py`**

```python
def build_layer04_sources(rim: IntegratedRimGreedyResult) -> tuple[Layer04SourceView, ...]:
    views = []
    for p in rim.committed_placements:
        views.append(
            Layer04SourceView(
                placement_id=p.placement_id,
                m_output_stub=p.m_output_stub,
                source_load_m=p.throughput_factor,
                throughput_factor=p.throughput_factor,
                equipment_cells=p.miner_cells | p.extension_cells,
                route_probe_path=p.route_probe_path,
            )
        )
    return tuple(sorted(views, key=lambda v: v.placement_id))
```

- [ ] **Step 5: Fix any tests constructing `CommittedRimSeedPlacement` without new field**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer04_source_adapter.py tests/unit/asteroid_lab/layers/test_commit_finalize.py -v`

---

### Task 0.4: Layer slug + disabled shim migration

**Files:**
- Modify: `src/.../layers/contracts/layer_slugs.py`
- Create: `src/.../layers/layer_04_transport_routing/run.py` (stub returns empty plan)
- Modify: `src/.../layer_04_rim_bundle_placement/run.py` (delegate + warn)
- Test: `tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py`

- [ ] **Step 1: Test stub run**

```python
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.run import (
    run_layer_04_transport_routing,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import Layer04RoutePlan


def test_layer04_stub_returns_empty_plan(empty_layer04_input):
    plan = run_layer_04_transport_routing(**empty_layer04_input)
    assert isinstance(plan, Layer04RoutePlan)
```

- [ ] **Step 2–4:** Implement stub + slug constant `LAYER_04_TRANSPORT_ROUTING = "layer_04_transport_routing"`

- [ ] **Step 5:** Update `test_layer_04_disabled_shim.py` → expect deprecation on old entrypoint OR remove if shim deleted

---

## Phase L4-1 — Transport catalog

### Task 1.1: Catalog port + snapshot DTO

**Files:**
- Create: `src/.../ports/space_transport_catalog.py`
- Create: `src/.../adapters/asteroid_lab/space_transport_catalog_snapshot.py`
- Test: `tests/unit/asteroid_lab/test_space_transport_catalog_snapshot.py`

- [x] **Step 1: Test parses Forward entry with ESWN signature**

```python
def test_catalog_lookup_forward_west_to_east(sample_catalog_snapshot):
    # Through-tile signature (not source-only): input W, output E at R0_E_CW.
    entry = sample_catalog_snapshot.lookup_io(
        transport_kind="space_belt",
        input_mask=(False, False, True, False),
        output_mask=(True, False, False, False),
    )
    assert entry.tile_id == "SpaceBelt_Forward"
    assert entry.canonical_rotation == 0
```

- [ ] **Step 2–4:** Implement `TransportIoSignature`, `SpaceTransportTileCatalogEntry`, `SpaceTransportTileCatalog.from_payload`

Use fixture: `tests/fixtures/asteroid_lab/space_transport_catalog_min.json` (hand-trimmed 2–3 tiles from `documents/game_data/research_unlocks.json`).

---

### Task 1.2: Django JSON importer

**Files:**
- Create: `django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- Test: `tests/unit/asteroid_lab/test_space_transport_catalog_import.py`

- [ ] **Step 1: Test imports `SpaceBelt_Forward` from research_unlocks path**

Run against `documents/game_data/research_unlocks.json` (skip if file missing in CI with `@pytest.mark.skipif`).

- [ ] **Step 2–3:** Walk `DefinitionsById.SpaceBelt_*` / `SpacePipe_*`; map `SpecializedIslandTenantSystemsByType` from `simulation_systems.json`

- [ ] **Step 4:** Wire CLI `--space-transport-catalog` mirroring gene-catalog pattern (if CLI stack needs it in L4-5)

---

## Phase L4-2 — A* MVP (one source, one connector, no merge)

### Task 2.1: L4 route domain + weights

**Files:**
- Create: `src/.../layer_04_transport_routing/route_domain.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer04_route_domain.py`

```python
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.route_domain import (
    L4_CELL_WEIGHT,
    L4RouteSearchDomain,
)

def test_void_cost_is_one(small_domain):
    assert small_domain.step_cost(Coord(0, 0)) == L4_CELL_WEIGHT["void"]
```

---

### Task 2.2: A* with tie-break

**Files:**
- Create: `src/.../layer_04_transport_routing/astar.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer04_astar.py`

```python
def test_astar_prefers_void_over_field(fixed_map):
    path = astar_to_goal(domain=fixed_map, start=Coord(0, 0), goal=Coord(3, 0))
    assert fixed_map.field_cells.isdisjoint(set(path[1:-1]))
```

Reuse heap/tie-break **pattern** from `layers/shared/route_probe.py` but **do not** import L3 `WeightedTransportRouteDomain`.

---

### Task 2.3: Commit validator (equipment whitelist)

**Files:**
- Create: `src/.../layer_04_transport_routing/commit_validator.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer04_commit_validator.py`

```python
def test_rejects_belt_on_miner_cell(validator_ctx):
    err = validator_ctx.validate_tile(coord=miner_coord, tile_kind="route")
    assert err is Layer04FailureReason.COMMIT_OVERLAP_BLOCKED
```

---

### Task 2.4: MVP router + W5 witness test

**Files:**
- Modify: `src/.../layer_04_transport_routing/sequential_router.py` (MVP: single source, single goal)
- Test: `tests/unit/asteroid_lab/layers/test_layer04_witness_path_ignored.py`

```python
def test_routing_unchanged_when_probe_paths_cleared(same_map_two_runs):
  plan_a = run_layer_04(..., rim_result=with_paths)
  plan_b = run_layer_04(..., rim_result=with_paths_cleared)
  assert plan_a.transport_tiles == plan_b.transport_tiles
```

---

## Phase L4-3 — Merge-aware groups

### Task 3.1: Union-find + capacity

**Files:**
- Create: `src/.../layer_04_transport_routing/merge_groups.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer04_merge_groups.py`

```python
def test_two_sources_same_connector_group_capacity_24_shape():
    # 2 connectors in group → capacity 24 for shape (12 each)
    ...
```

Rules:
- `capacity_m = connector_count * unit_capacity_m`
- Reject attach when `used_m + source_load_m > capacity_m`
- Second source may use **trunk attach cell** as goal (stop on attach; no through-trunk)

---

### Task 3.2: Full sequential router

**Files:**
- Modify: `sequential_router.py`, `run.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer04_sequential_router.py`

---

## Phase L4-4 — Sprite projection

### Task 4.1: ESWN signature from committed path graph

**Files:**
- Create: `src/.../layer_04_transport_routing/sprite_projector.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py`

```python
def test_straight_east_resolves_forward(catalog):
    tile = project_cell(
        coord=Coord(1, 0),
        neighbors=path_graph,
        transport_kind="space_belt",
        catalog=catalog,
    )
    assert tile.tile_id == "SpaceBelt_Forward"
```

Fail closed: `UNSUPPORTED_IO_SIGNATURE` when degree/signature not in catalog.

**Gate:** LeftTurn/RightTurn golden tests blocked until visual oracle documents left/right mapping (see `space_transport_identifiers.md`).

---

## Phase L4-5 — Stack, replay, metrics

### Task 5.1: stack_runner wire L3 → L4 → L5

**Files:**
- Modify: `src/.../stack_runner.py:148-175`
- Modify: `django_apps/asteroid_lab/layers/stack_runner.py`
- Test: `tests/unit/asteroid_lab/layers/test_stack_runner_layer04.py`

Pass `Layer04RoutePlan` into L5 instead of `empty_layer04_rim_placement_result()`.

---

### Task 5.2: Replay segment for `transport_tiles`

**Files:**
- Create: `django_apps/asteroid_lab/replay/layer04_transport_segment.py`
- Deprecate route overlay kinds in old `layer04_segment.py` for final transport
- Test: `tests/unit/asteroid_lab/replay/test_layer04_transport_segment.py`

```python
def test_replay_uses_transport_tiles_not_probe_path(plan_with_tiles):
    frames = build_layer04_transport_frames(plan_with_tiles)
    kinds = {c.kind for f in frames for c in f.overlay_cells}
    assert "route_probe_path" not in kinds
    assert any(k.startswith("space_") for k in kinds)
```

---

### Task 5.3: Post-summary metrics + JSONL log slug rename

**Files:**
- Create: `src/.../layers/observability/layer04_post_summary_metrics.py`
- Modify: `django_apps/asteroid_lab/services/solver_layer_stack_log.py`
- Modify: `documents/ai/manuals/environment.md` log filenames

---

## Spec self-review (plan author)

| Spec section | Task |
|--------------|------|
| Witness W1–W5 | 2.4, 5.2 |
| `source_load_m` adapter | 0.3 |
| L4 weights + commit split | 2.1, 2.3 |
| Merge trunk attach v1 | 3.1–3.2 |
| Catalog C1 | 1.1–1.2 |
| Sprite projection | 4.1 |
| MIX_UNSUPPORTED | 3.2 + test |
| PR-L4-0..5 | Phases above |

No TBD placeholders in task code blocks.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-31-layer-04-transport-routing/README.md`.

**Options:**

1. **Subagent-Driven (recommended)** — one task per subagent, review between tasks  
2. **Inline Execution** — same session with executing-plans checkpoints  

Which approach?
