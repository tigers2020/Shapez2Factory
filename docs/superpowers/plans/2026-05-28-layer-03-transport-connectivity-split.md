# Layer 03 Transport Connectivity Split — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Amend the approved Virtual Exterior Transport Domain contract so `placeable_cells` (install/search space) is never confused with an already-connected belt/pipe network; route probe returns an explicit simple path only; forbid promoting a full exterior component into candidate transport cells.

**Architecture:** Rename/clarify `ExteriorTransportDomain.traversable_cells` → `placeable_cells` (exterior-reachable, non-field cells in bounded bbox — interior holes excluded). `immediate_route_probe` BFS walks `placeable_cells` but success means `RouteProbeResult.path_coords` is the proposed route; actual transport network for the candidate remains `transport_stub_cells ∪ path_coords` (path may overlap stubs). Expand validates stub ⊆ `placeable_cells`, not “stub ⊆ connected transport graph”. Add `reject_reason_counts` metrics + Lab highlight for 583-cell diagnosis.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy (`django_apps config src`), existing `ExteriorTransportDomain`, `immediate_route_probe`, `expand_rim_bundle_candidates`

**Parent spec (amend):** [`2026-05-28-layer-03-virtual-exterior-transport-domain-design.md`](../specs/2026-05-28-layer-03-virtual-exterior-transport-domain-design.md) (APPROVED — add §3.6 + §5.3)

**Depends on:** Virtual exterior v1 code landed (`exterior_domain.py`, `expand.py`, `route_probe.py`)

**Work classification:** contract change · implementation change

**Branch suggestion:** `feat/layer-03-transport-connectivity-split`

**pytest:** No `-q`, `--quiet`, or `--tb=no`.

---

## Problem (why this plan exists)

Current v1 implementation builds `traversable_cells` as the **4-neighbor component** from `route_probe_start` within `bbox \ field_cells`, then:

1. Requires `transport_stub_cells ⊆ domain.traversable_cells` (geometry gate).
2. Runs BFS to goals over the same set.

That is correct for **excluding interior holes**, but the name and gate read as “the whole component is connected transport.” On large exterior void regions, start and goal can lie in the same placeable component while **no explicit belt path** is part of the candidate — conflating **installability** with **transport connectivity**.

**583-cell symptom (1458/1458 geometry, 0 probe)** is still dominated by projection/domain gates (`TRANSPORT_COLLIDES_WITH_FIELD`, etc.). This plan fixes a **contract bug** and observability; pool recovery on production maps may need a follow-up plan (catalog/topology).

---

## File map

| Action | Path |
|--------|------|
| Modify | `docs/superpowers/specs/2026-05-28-layer-03-virtual-exterior-transport-domain-design.md` |
| Modify | `django_apps/asteroid_lab/layers/contracts/exterior_transport_domain.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/exterior_domain.py` |
| Modify | `django_apps/asteroid_lab/layers/contracts/candidates.py` |
| Modify | `django_apps/asteroid_lab/layers/shared/route_probe.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py` |
| Modify | `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` |
| Modify | `django_apps/asteroid_lab/services/solver_run_lab_summary.py` |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py` |
| Create | `tests/unit/asteroid_lab/layers/fixtures/layer_03_placeable_flood_trap.py` |
| Modify | `docs/superpowers/specs/2026-05-28-layer-03-rim-mining-bundles-design.md` (cross-link one paragraph) |

---

### Task 1: Spec amendment — “Traversable domain is not transport connectivity”

**Files:**
- Modify: `docs/superpowers/specs/2026-05-28-layer-03-virtual-exterior-transport-domain-design.md`

- [ ] **Step 1: Insert §3.6 after §3.5** (English normative + Korean reference)

```markdown
## §3.6 Traversable domain is not transport connectivity

### Installability domain (`placeable_cells`)

```text
placeable_cells = exterior-reachable non-field coordinates inside search_bbox
(interior holes excluded — §3.3)
```

A coordinate ∈ placeable_cells means belt/pipe **may be considered for placement** during route search.
It does NOT mean adjacent placeable cells are already connected transport.

### Transport network (candidate stage)

```text
proposed_transport_cells = transport_stub_cells ∪ route_probe_result.path_coords
```

- `transport_stub_cells` — seed-projected belt/pipe stubs (map absolute).
- `path_coords` — simple path returned by immediate_route_probe (bounded by LAYER03_ROUTE_PROBE_MAX_STEPS).
- Overlap between stubs and path is allowed (intentional merge/share).

**Forbidden:**

```text
candidate.transport_stub_cells = domain.placeable_cells
candidate.transport_stub_cells |= full_placeable_component
Using 4-neighbor adjacency of placeable cells alone as proof of transport connectivity
Treating a 2×2 (or larger) void block as an already-connected belt network without path_coords
```

**Normative (English):**

```text
ExteriorTransportDomain.placeable_cells defines where belt/pipe may be placed or searched.
It does not imply that all adjacent placeable cells are already transport-connected.

Transport connectivity is established only by:
1. the explicit route path selected by immediate_route_probe (path_coords),
2. existing committed transport cells of the same compatible transport kind (L5+ — out of scope for L3 v1),
3. intentional overlap/merge points admitted by route/commit policy.

Adjacency of virtual exterior cells alone MUST NOT create transport connectivity.
```

**Korean reference:**

```text
placeable_cells는 벨트/파이프를 설치·탐색할 수 있는 후보 공간일 뿐이다.
인접한 placeable cell이 자동으로 transport network로 연결된 것으로 보면 안 된다.

belt/pipe 연결은 immediate_route_probe가 선택한 path_coords,
(향후) committed transport, 명시적 merge/overlap에서만 인정한다.
```

### Belt/pipe overlap

| Situation | Allowed |
|-----------|---------|
| Same transport kind: route path shares a cell with seed stub | Yes — merge/share |
| Same kind: route path shares cell with another candidate stub | Dedupe/policy (L4+) |
| Shape belt vs fluid pipe same cell | No — kind conflict (unchanged) |
| Placeable cells merely 4-adjacent | No — not connectivity |
| Full placeable component promoted to transport_stub_cells | **Forbidden** |
```

- [ ] **Step 2: Add §5.3 under Route probe**

```markdown
### 5.3 Probe path semantics

```text
BFS walks placeable_cells (search space only).
On success, RouteProbeResult.path_coords is a simple shortest-path (priority, steps tie-break unchanged).
path_coords MUST NOT be replaced by the full placeable component.
path_coords steps MUST be ≤ LAYER03_ROUTE_PROBE_MAX_STEPS.
```

Add to `RouteProbeResult` (contract):

```python
def proposed_transport_cells(self, *, stub_cells: frozenset[Coord]) -> frozenset[Coord]:
    return stub_cells | frozenset(self.path_coords)
```
```

- [x] **Step 3: Update §3.1 DTO field name** `traversable_cells` → `placeable_cells`. Python DTO: `placeable_cells` only; wire/logs MAY alias `traversable_cells` one release; solver MUST NOT read `traversable_cells` from runtime objects.

- [ ] **Step 4: Update approval record** with amendment date and “connectivity split” bullet.

---

### Task 2: Rename DTO field `traversable_cells` → `placeable_cells`

**Files:**
- Modify: `django_apps/asteroid_lab/layers/contracts/exterior_transport_domain.py`
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/exterior_domain.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py`

- [ ] **Step 1: Write failing test**

```python
def test_exterior_transport_domain_exposes_placeable_cells() -> None:
    from django_apps.asteroid_lab.layers.contracts.exterior_transport_domain import (
        ExteriorTransportDomain,
    )
    from django_apps.asteroid_lab.snapshots.grid_contract import BBox

    domain = ExteriorTransportDomain(
        search_bbox=BBox(0, 10, 0, 10),
        blocked_field_cells=frozenset({(5, 5)}),
        placeable_cells=frozenset({(4, 5), (3, 5)}),
    )
    assert (4, 5) in domain.placeable_cells
    assert not hasattr(domain, "traversable_cells")  # removed, not alias
```

- [ ] **Step 2: Run — FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py::test_exterior_transport_domain_exposes_placeable_cells`

- [ ] **Step 3: Implement contract + builder return**

`exterior_transport_domain.py`:

```python
@dataclass(frozen=True, slots=True)
class ExteriorTransportDomain:
    """Bounded exterior install/search space for one L3 probe (not a transport network)."""

    search_bbox: BBox
    blocked_field_cells: frozenset[Coord]
    placeable_cells: frozenset[Coord]
```

`exterior_domain.py` — rename local variable and return field; docstring references §3.6.

- [ ] **Step 4: Grep-replace call sites**

```bash
rg "traversable_cells" django_apps/asteroid_lab tests/unit/asteroid_lab
```

Update: `expand.py`, `route_probe` call argument name `traversable_void=` → `placeable_cells=` (parameter rename in `immediate_route_probe`).

- [ ] **Step 5: Run exterior tests — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py`

---

### Task 3: `RouteProbeResult.proposed_transport_cells` helper

**Files:**
- Modify: `django_apps/asteroid_lab/layers/contracts/candidates.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py`

- [ ] **Step 1: Write failing test**

```python
def test_route_probe_result_proposed_transport_cells_unions_stub_and_path() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbeResult
    from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind

    stubs = frozenset({(5, 5), (6, 5)})
    result = RouteProbeResult(
        reached_goal=True,
        goal_coord=(8, 5),
        path_coords=((5, 5), (6, 5), (7, 5), (8, 5)),
        steps_expanded=3,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    proposed = result.proposed_transport_cells(stub_cells=stubs)
    assert proposed == frozenset({(5, 5), (6, 5), (7, 5), (8, 5)})
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Add method on `RouteProbeResult`**

```python
def proposed_transport_cells(self, *, stub_cells: frozenset[Coord]) -> frozenset[Coord]:
    return stub_cells | frozenset(self.path_coords)
```

- [ ] **Step 4: Run — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py::test_route_probe_result_proposed_transport_cells_unions_stub_and_path`

---

### Task 4: `immediate_route_probe` — parameter rename + path-only contract

**Files:**
- Modify: `django_apps/asteroid_lab/layers/shared/route_probe.py`
- Modify: `tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py`

- [ ] **Step 1: Write failing test** (path is strict subset of placeable in flood-trap fixture — Task 5)

- [ ] **Step 2: Rename keyword-only parameter**

```python
def immediate_route_probe(
    *,
    candidate: BundleCandidate,
    route_goals: tuple[RouteGoal, ...],
    placeable_cells: frozenset[Coord],
) -> RouteProbedBundleCandidate:
```

Replace every `traversable_void` reference inside with `placeable_cells`.

- [ ] **Step 3: Assert simple path invariant before return (success branch)**

```python
if len(path) < 2:
    # single-cell path only when start == goal; still simple
    pass
if len(path) != len(frozenset(path)):
    msg = "path_coords must be a simple path (no repeated cells)"
    raise ValueError(msg)
```

- [ ] **Step 4: Update all callers** (`expand.py`, tests).

- [ ] **Step 5: Run probe tests — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py`

---

### Task 5: Anti-flood regression fixture + tests

**Files:**
- Create: `tests/unit/asteroid_lab/layers/fixtures/layer_03_placeable_flood_trap.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py`

**Fixture design (docstring):**

```text
2×2 placeable void block {(0,0),(1,0),(0,1),(1,1)} plus corridor to goal.
Single stub at (0,0); goal at (1,1).
placeable_cells is the whole component (4 cells).
Correct behavior: probe may succeed with path_coords length 3 (e.g. (0,0)→(1,0)→(1,1)),
but proposed_transport_cells MUST equal stubs ∪ path, not all 4 placeable cells.
```

- [ ] **Step 1: Implement fixture** `placeable_flood_trap_complete_map()`, `placeable_flood_trap_goals()`, `minimal_stub_candidate()` using `make_bundle_candidate_for_test`.

- [ ] **Step 2: Write failing test**

```python
def test_probe_path_is_not_full_placeable_component() -> None:
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.exterior_domain import (
        build_exterior_transport_domain,
    )
    from django_apps.asteroid_lab.layers.shared.route_probe import immediate_route_probe
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_placeable_flood_trap import (
        flood_trap_candidate,
        flood_trap_complete_map,
        flood_trap_goals,
    )

    candidate = flood_trap_candidate()
    complete_map = flood_trap_complete_map()
    domain = build_exterior_transport_domain(
        complete_map=complete_map,
        anchor_abs=candidate.anchor_coord,
        transport_stub_cells=candidate.transport_stub_cells,
        route_goals=flood_trap_goals(),
        route_probe_start=candidate.route_probe_start_coord,
    )
    assert len(domain.placeable_cells) >= 4
    probed = immediate_route_probe(
        candidate=candidate,
        route_goals=flood_trap_goals(),
        placeable_cells=domain.placeable_cells,
    )
    assert probed.route_probe_status == RouteProbeStatus.SUCCEEDED
    assert probed.route_probe_result is not None
    path_set = frozenset(probed.route_probe_result.path_coords)
    assert path_set < domain.placeable_cells  # strict subset — not whole component
    proposed = probed.route_probe_result.proposed_transport_cells(
        stub_cells=candidate.transport_stub_cells,
    )
    assert proposed == candidate.transport_stub_cells | path_set
    assert proposed != domain.placeable_cells
```

- [ ] **Step 3: Run — FAIL or PASS** (document actual BFS path length in assertion if map geometry requires 3 steps)

- [ ] **Step 4: Fix builder/probe only if test exposes violation** (do not weaken assertion to `<= placeable`)

---

### Task 6: `expand.py` — placeable gate wording + forbid component promotion

**Files:**
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py`

- [ ] **Step 1: Write failing test** (extend `test_layer_03_exterior_domain.py`)

```python
def test_successful_candidate_transport_stub_cells_unchanged_after_probe() -> None:
    """Pool candidate keeps seed stubs only; path lives on RouteProbeResult."""
    result = expand_rim_bundle_candidates(...)  # virtual_exterior fixture
    assert result.metrics.normal_candidate_count >= 1
    probed = result.normal_candidates[0]
    assert probed.route_probe_result is not None
    # Bundled candidate must not gain every placeable cell as stub
    assert len(probed.candidate.transport_stub_cells) < 10
```

- [ ] **Step 2: Update expand loop**

```python
domain = build_exterior_transport_domain(...)
placeable = domain.placeable_cells
if candidate.route_probe_start_coord not in placeable:
    ... EXTERIOR_ENTRY_NOT_REACHABLE ...
if not candidate.transport_stub_cells <= placeable:
    ... EXTERIOR_ENTRY_NOT_REACHABLE ...

probed = immediate_route_probe(
    candidate=candidate,
    route_goals=route_goals,
    placeable_cells=placeable,
)
# Do NOT mutate candidate.transport_stub_cells with placeable or path_coords
```

Remove any comment saying “traversable = connected transport”.

- [ ] **Step 3: Run — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py`

---

### Task 7: `reject_reason_counts` metrics + Lab highlight

**Files:**
- Modify: `django_apps/asteroid_lab/layers/contracts/candidates.py`
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py`
- Modify: `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py`
- Modify: `django_apps/asteroid_lab/services/solver_runtime_rim_stack.py`
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py`

- [ ] **Step 1: Add optional field to `Layer03ExpansionMetrics`**

```python
reject_reason_counts: tuple[tuple[str, int], ...] = ()  # sorted by (-count, reason)
```

Factory helper in `expand.py`:

```python
def _build_reject_reason_counts(
    diagnostics: Sequence[RouteProbedBundleCandidate],
) -> tuple[tuple[str, int], ...]:
    tallies: Counter[str] = Counter()
    for d in diagnostics:
        if d.reject_reason is not None:
            tallies[d.reject_reason.value] += 1
    return tuple(sorted(tallies.items(), key=lambda kv: (-kv[1], kv[0])))
```

Populate at end of `expand_rim_bundle_candidates`.

- [ ] **Step 2: Wire `merge_rim_stack_into_solver_summary`**

```python
solver_summary["layer03_reject_reason_counts"] = list(metrics.reject_reason_counts)
```

- [ ] **Step 3: Lab summary — top 3 reasons**

In L3 highlights after “Geometry rejected”, add:

```python
_highlight("Top reject reasons", _format_reject_reason_counts(solver_summary))
```

```python
def _format_reject_reason_counts(solver_summary: dict[str, Any]) -> str:
    raw = solver_summary.get("layer03_reject_reason_counts")
    if not raw:
        return _PLACEHOLDER
    parts = [f"{reason}: {count}" for reason, count in raw[:3]]
    return "; ".join(parts)
```

- [ ] **Step 4: Test histogram populated on all-geometry-fail expansion**

```python
def test_expand_populates_reject_reason_counts() -> None:
    # use projection-fail-heavy map or force failures
    result = expand_rim_bundle_candidates(...)
    counts = dict(result.metrics.reject_reason_counts)
    assert counts.get("transport_collides_with_field", 0) > 0 or len(counts) > 0
```

- [ ] **Step 5: Run tests + ruff**

---

### Task 8: Parent spec cross-link

**Files:**
- Modify: `docs/superpowers/specs/2026-05-28-layer-03-rim-mining-bundles-design.md`

- [ ] **Step 1:** In §4 Related documents table, add note: “Transport connectivity split — see virtual-exterior spec §3.6”.

---

### Task 9: Regression gate

- [ ] **Step 1: Narrow pytest**

```bash
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_exterior_domain.py tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py
```

Expected: all PASS; P0 virtual-exterior `route_probe_attempt_count > 0` still holds.

- [ ] **Step 2: Ruff**

```bash
python -m ruff check django_apps/asteroid_lab/layers/contracts/exterior_transport_domain.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/exterior_domain.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py django_apps/asteroid_lab/layers/shared/route_probe.py django_apps/asteroid_lab/layers/contracts/candidates.py django_apps/asteroid_lab/services/solver_run_lab_summary.py
```

- [ ] **Step 3: Mypy (touched modules)**

```bash
python -m mypy django_apps/asteroid_lab/layers/contracts/exterior_transport_domain.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/exterior_domain.py django_apps/asteroid_lab/layers/shared/route_probe.py django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py
```

---

## Spec self-review (plan author)

| Spec requirement | Task |
|------------------|------|
| §3.6 installability vs connectivity prose | Task 1 |
| `placeable_cells` rename | Task 2 |
| `path_coords` = proposed route only | Tasks 3–4 |
| No full component → transport_stub_cells | Tasks 5–6 |
| max steps / simple path | Task 4 |
| overlap/merge policy table | Task 1 |
| reject_reason_counts observability | Task 7 |
| Interior holes (§3.3) unchanged algorithm | Task 2 (rename only) |

**Out of scope (follow-up plan):** 583-cell `route_probe_attempt_count > 0` via catalog/topology/void-depth recovery; L5 committed-transport merge; mutating `BundleCandidate` to store `proposed_route_cells` on DTO (v1 keeps path on `RouteProbeResult` only).

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-28-layer-03-transport-connectivity-split.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, spec compliance review then code quality review between tasks (`superpowers:subagent-driven-development`).

2. **Inline Execution** — run tasks in this session with checkpoints (`superpowers:executing-plans`).

Which approach do you want?
