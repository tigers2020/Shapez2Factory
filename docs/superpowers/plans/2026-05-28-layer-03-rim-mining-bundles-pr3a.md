# Layer 03 Rim Mining Bundles — PR-3a Implementation Plan (Contracts + Route Probe)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land typed L3 candidate / route-goal / route-probe contracts and pool invariants so PR-3b can implement rim expansion without enum or DTO drift.

**Architecture:** Add `layers/contracts/candidates.py` and `route_goal.py` per approved spec; add `layers/shared/route_probe.py` as a **bounded BFS feasibility stub** (no L3 generator yet). Enforce `normal_candidates` ⊆ `SUCCEEDED` via factory + tests. **No** `layer_03/expand.py` or projection in this PR.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy `django_apps config src`, `StrEnum`, frozen dataclasses

**Spec:** [`2026-05-28-layer-03-rim-mining-bundles-design.md`](../specs/2026-05-28-layer-03-rim-mining-bundles-design.md)  
**Parent:** [`2026-05-27-asteroid-lab-algorithm-layer-stack.md`](2026-05-27-asteroid-lab-algorithm-layer-stack.md) (Task 5a)

**Work classification:** contract change

**Branch:** `feat/layer-03-rim-candidates-pr3a` (worktree recommended)

---

## Out of scope (PR-3a)

```text
- layer_03_rim_mining_bundles/expand.py, project.py, seed_catalog DB loader
- stack_runner L2→L3 plan pass
- Layer 04 inner fill
- Full route_domain / RouteDomainSnapshotBuilder integration
```

**Commit boundary:** contracts + shared route_probe + tests green; `run_layer_03` remains stub.

---

## Execution order (Subagent-Driven)

```text
1. Apply spec/plan P0 patches (done in repo docs)
2. Task 1–3: enums / DTO / equivalence_key
3. Checkpoint A — DTO + pool invariant review (after Task 2)
4. Task 4–5: RouteGoal / route_probe
5. Checkpoint B — route_probe contract review (after Task 5)
6. Task 6: PR-3a gate (pytest + ruff + mypy)
7. PR-3b plan (separate branch/stacked PR)
```

**Commit:** only when the user explicitly requests git commit.

---

## File map

| Action | Path |
|--------|------|
| Create | `django_apps/asteroid_lab/layers/contracts/transport_kind.py` |
| Create | `django_apps/asteroid_lab/layers/contracts/candidates.py` |
| Create | `django_apps/asteroid_lab/layers/contracts/route_goal.py` |
| Create | `django_apps/asteroid_lab/layers/shared/route_probe.py` |
| Create | `django_apps/asteroid_lab/layers/shared/equivalence_key.py` |
| Modify | `django_apps/asteroid_lab/layers/contracts/__init__.py` |
| Modify | `django_apps/asteroid_lab/layers/shared/__init__.py` |
| Create | `tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py` |
| Create | `tests/unit/asteroid_lab/layers/test_layer_03_route_goal_builder.py` |

---

### Task 1: Transport and reject enums

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/transport_kind.py`

- [ ] **Step 1: Write failing import test**

```python
# tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py
from django_apps.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
    map_resource_kind_to_transport_kind,
)


def test_map_resource_kind_to_transport_kind() -> None:
    assert map_resource_kind_to_transport_kind(ResourceKind.SHAPE) == TransportKind.SHAPE_BELT
    assert map_resource_kind_to_transport_kind(ResourceKind.FLUID) == TransportKind.FLUID_PIPE
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py::test_map_resource_kind_to_transport_kind -v`  
Expected: FAIL (module missing)

- [ ] **Step 3: Implement**

```python
# django_apps/asteroid_lab/layers/contracts/transport_kind.py
from __future__ import annotations

from enum import StrEnum


class ResourceKind(StrEnum):
    SHAPE = "shape"
    FLUID = "fluid"


class TransportKind(StrEnum):
    SHAPE_BELT = "shape_belt"
    FLUID_PIPE = "fluid_pipe"


def map_resource_kind_to_transport_kind(resource_kind: ResourceKind) -> TransportKind:
    if resource_kind == ResourceKind.SHAPE:
        return TransportKind.SHAPE_BELT
    if resource_kind == ResourceKind.FLUID:
        return TransportKind.FLUID_PIPE
    msg = f"unknown resource_kind: {resource_kind!r}"
    raise ValueError(msg)


def resource_kind_from_plan_string(value: str) -> ResourceKind:
    normalized = value.strip().lower()
    if normalized == ResourceKind.SHAPE.value:
        return ResourceKind.SHAPE
    if normalized == ResourceKind.FLUID.value:
        return ResourceKind.FLUID
    msg = f"unknown plan transport_kind string: {value!r}"
    raise ValueError(msg)
```

- [ ] **Step 4: Run test — PASS**

- [ ] **Step 5: Commit** (when user requests git commit)

```bash
git add django_apps/asteroid_lab/layers/contracts/transport_kind.py tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py
git commit -m "feat(asteroid_lab): add L3 ResourceKind and TransportKind enums"
```

---

### Task 2: Candidate DTOs + pool factory

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/candidates.py`

- [ ] **Step 1: Write failing pool invariant tests**

```python
import pytest

from django_apps.asteroid_lab.layers.contracts.candidates import (
    BundleCandidate,
    BundleCellRole,
    BundlePlacement,
    CandidateRejectReason,
    Layer03ExpansionMetrics,
    Layer03SkipReason,
    RimBundleCandidateSet,
    RouteProbeStatus,
    RouteProbedBundleCandidate,
    build_rim_bundle_candidate_set,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
)


def _minimal_candidate(*, gene_key: str = "miner_seed_m3e_01") -> BundleCandidate:
    anchor = (3, 4)
  # ... use helper in candidates.py: make_bundle_candidate_for_test(...)
    raise NotImplementedError


def test_normal_candidates_type_requires_succeeded_status() -> None:
    with pytest.raises(ValueError, match="normal_candidates"):
        build_rim_bundle_candidate_set(
            normal_candidates=(
                RouteProbedBundleCandidate(
                    candidate=_minimal_candidate(),
                    route_probe_status=RouteProbeStatus.FAILED,
                    route_probe_result=None,
                    route_goal_id=None,
                    reject_reason=CandidateRejectReason.ROUTE_PROBE_FAILED,
                ),
            ),
            diagnostic_rejected_candidates=(),
            metrics=Layer03ExpansionMetrics.empty(),
        )


def test_unprobed_never_in_normal_pool() -> None:
    with pytest.raises(ValueError, match="SKIPPED_GEOMETRY"):
        build_rim_bundle_candidate_set(
            normal_candidates=(
                RouteProbedBundleCandidate(
                    candidate=_minimal_candidate(),
                    route_probe_status=RouteProbeStatus.SKIPPED_GEOMETRY,
                    route_probe_result=None,
                    route_goal_id=None,
                    reject_reason=CandidateRejectReason.LOCAL_GEOMETRY_INVALID,
                ),
            ),
            diagnostic_rejected_candidates=(),
            metrics=Layer03ExpansionMetrics.empty(),
        )
```

- [ ] **Step 2: Run tests — FAIL**

- [ ] **Step 3: Implement `candidates.py`**

Implement frozen dataclasses per spec §2.3–§2.9 including:

- `RouteProbeStatus` with `SUCCEEDED`, `FAILED`, `SKIPPED_BUDGET`, `SKIPPED_GEOMETRY`, `SKIPPED_NO_GOAL`
- `CandidateRejectReason` full set from spec
- `RouteProbeResult` stores path shape only (no `route_probe_status` on this type)
- `RouteProbedBundleCandidate.__post_init__` validates when `route_probe_status == SUCCEEDED`:
  - `route_probe_result is not None`
  - `route_goal_id is not None`
  - `route_probe_result.path_coords[0] == candidate.route_probe_start_coord`
  - `route_probe_result.path_coords[-1] == route_probe_result.goal_coord`
- `build_rim_bundle_candidate_set(...)` factory repeats pool rules:
  - `normal_candidates` only `SUCCEEDED`
  - `route_goal_id is not None` iff `SUCCEEDED`
  - `route_probe_result is not None` iff `SUCCEEDED`
- `Layer03ExpansionMetrics.empty()` factory with `layer_skip_reason=Layer03SkipReason.NONE`

- [ ] **Step 4: Add `make_bundle_candidate_for_test` helper in test module or `tests/helpers/layer_03_factories.py`**

- [ ] **Step 5: Run pool tests — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py -v`

- [ ] **Step 6: Checkpoint A — DTO / pool invariant review**

Review against spec §2.3–§2.9: `TransportKind` vs `ResourceKind`, `route_goal_id` nullability, wrapper validation location.

- [ ] **Step 7: Commit** (when user requests git commit)

---

### Task 3: Equivalence key (gene_key excluded)

**Files:**
- Create: `django_apps/asteroid_lab/layers/shared/equivalence_key.py`

- [ ] **Step 1: Write failing test**

`build_equivalence_key` accepts **only** semantic fields from spec §2.6 — **no `gene_key` parameter**.

```python
from django_apps.asteroid_lab.genetic_sample.enums import Direction


def test_equivalence_key_ignores_gene_key_on_candidates() -> None:
    from django_apps.asteroid_lab.layers.shared.equivalence_key import (
        build_equivalence_key_from_candidate,
    )

    shared = dict(
        transport_kind=TransportKind.SHAPE_BELT,
        resource_kind=ResourceKind.SHAPE,
        output_dir=Direction.E,
        throughput_factor=16,
        route_probe_start_coord=(5, 4),
        mining_occupied_cells=frozenset({(3, 4), (4, 4)}),
        transport_stub_cells=frozenset({(5, 4)}),
        topology_signature="topo_a",
    )
    cand_a = make_bundle_candidate_for_test(gene_key="miner_seed_m3e_01", **shared)
    cand_b = make_bundle_candidate_for_test(gene_key="miner_seed_m1e_01", **shared)
    assert cand_a.candidate_id != cand_b.candidate_id
    assert build_equivalence_key_from_candidate(cand_a) == build_equivalence_key_from_candidate(
        cand_b
    )
```

- [ ] **Step 2: Implement stable hash** (e.g. SHA256 of canonical JSON tuple; **no `gene_key` argument**)

- [ ] **Step 3: Run test — PASS**

---

### Task 4: RouteGoal builder from ExteriorConnectionPlan

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/route_goal.py`
- Create: `tests/unit/asteroid_lab/layers/test_layer_03_route_goal_builder.py`

- [ ] **Step 1: Write failing test with minimal `ExteriorConnectionPlan` fixture**

```python
def test_build_layer03_route_goals_required_before_spare() -> None:
    from decimal import Decimal
    from django_apps.asteroid_lab.layers.contracts.route_goal import (
        ROUTE_GOAL_PRIORITY_REQUIRED,
        ROUTE_GOAL_PRIORITY_SPARE,
        build_layer03_route_goals,
    )
    # build plan with one required + one spare connector (reuse layer_02 factories)
    goals = build_layer03_route_goals(plan, transport_kind=TransportKind.SHAPE_BELT)
    assert goals[0].priority == ROUTE_GOAL_PRIORITY_REQUIRED
    assert goals[1].priority == ROUTE_GOAL_PRIORITY_SPARE
```

- [ ] **Step 2: Implement `build_layer03_route_goals`**

Filter `planned_connectors` by mapped `TransportKind`; map `ExteriorConnectorRole` → priority 0 / 10; sort `(priority, goal_id)`.

- [ ] **Step 3: Run tests — PASS**

---

### Task 5: Route probe stub

**Files:**
- Create: `django_apps/asteroid_lab/layers/shared/route_probe.py`

- [ ] **Step 1: Write failing probe test on 5×5 grid**

```python
def test_immediate_route_probe_reaches_nearest_goal() -> None:
    from django_apps.asteroid_lab.layers.shared.route_probe import immediate_route_probe
    # void grid + start + goal within LAYER03_ROUTE_PROBE_MAX_STEPS
    probed = immediate_route_probe(candidate=..., route_goals=..., traversable_void=...)
    assert probed.route_probe_status == RouteProbeStatus.SUCCEEDED
    assert probed.route_probe_result is not None
    assert probed.route_probe_result.path_coords[0] == candidate.route_probe_start_coord
    assert probed.route_probe_result.path_coords[-1] == probed.route_probe_result.goal_coord
```

- [ ] **Step 2: Implement bounded BFS over `external_void_cells`**

- Respect `transport_kind` filter on goals
- Pick lowest `(goal.priority, manhattan_distance)` on success
- Return `RouteProbeStatus.FAILED` when no path within step cap

- [ ] **Step 3: Run tests — PASS**

---

### Task 6: PR-3a gate

- [ ] **Step 1: Run narrow pytest**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py tests/unit/asteroid_lab/layers/test_layer_03_route_goal_builder.py -v
```

- [ ] **Step 2: ruff + mypy on touched paths**

```powershell
python -m ruff check django_apps/asteroid_lab/layers/contracts/transport_kind.py django_apps/asteroid_lab/layers/contracts/candidates.py django_apps/asteroid_lab/layers/contracts/route_goal.py django_apps/asteroid_lab/layers/shared/equivalence_key.py django_apps/asteroid_lab/layers/shared/route_probe.py
python -m mypy django_apps/asteroid_lab/layers/contracts/transport_kind.py django_apps/asteroid_lab/layers/contracts/candidates.py django_apps/asteroid_lab/layers/contracts/route_goal.py django_apps/asteroid_lab/layers/shared/equivalence_key.py django_apps/asteroid_lab/layers/shared/route_probe.py
```

Expected: PASS

- [ ] **Step 3: Checkpoint B — route_probe contract review**

Review `immediate_route_probe` path endpoints, goal priority ordering, and `RouteProbedBundleCandidate` SUCCEEDED validation against spec §2.5 and §3.2.

---

## Plan self-review (2026-05-28)

| Spec section | Task |
|--------------|------|
| §2.2 TransportKind | Task 1 |
| §2.3–§2.9 DTOs + pool invariant | Task 2 |
| §2.6 equivalence_key | Task 3 |
| §2.8 RouteGoal | Task 4 |
| §2.5 RouteProbeResult path endpoints | Task 5 |
| §3 generator | **PR-3b** |

No TBD placeholders in task steps above.

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-28-layer-03-rim-mining-bundles-pr3a.md`.

**Next:** PR-3b plan, then implement PR-3a before PR-3b.

**Execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — `executing-plans` with checkpoints in this session

Which approach do you want for implementation?
