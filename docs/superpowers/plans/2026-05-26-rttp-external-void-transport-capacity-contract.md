# RTTP External Void Transport Capacity Contract (EVTC) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce throughput-based exterior connector planning, void transport-installable route domain, commit-time shortest-path evidence, and read-only validation — without conflating product placement shortfall with validation failure.

**Architecture:** **Shapez 2 1.0** (release **2026-04-23**). Unified denominator: `space_transport_max = port_rate × space_full_unit_count` from DB. Tier-1 wiki sanity: shape **2880** (`15×4×48`), fluid **345600** (`1200×288`). Both **APPROVED** for EVTC-1a/1b; solver never hardcodes wiki literals. Then `required_external_connectors` (ceildiv).

**Tech Stack:** Python 3.12+, Django 5.2, `Decimal`, existing RTTP pipeline (`optimization_input_from_reconstruction`, `RttpSkeletonBuilder`, `probe_route`, `incremental_commit`, `validate_layout_connectivity_issues`), pytest, ruff, mypy (`django_apps/asteroid_lab/contracts` paths).

**Canonical spec:** [`docs/superpowers/specs/2026-05-26-rttp-external-void-transport-capacity-contract.md`](../specs/2026-05-26-rttp-external-void-transport-capacity-contract.md)

---

## File map (create / modify)

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/contracts/rttp_exterior_transport_keys.py` | Structural constants (shape 4/48; fluid 288); logical keys — not solver SoT |
| `django_apps/asteroid_lab/contracts/rttp_exterior_throughput_tier.py` | `ExteriorThroughputTier.TIER_1` enum |
| `django_apps/asteroid_lab/contracts/rttp_exterior_connector_policy.py` | `ConnectorCountPolicy` enum |
| `django_apps/game_data/models/exterior_transport_capacity.py` | **CANON DB** shape + fluid tier rows (`EVTC_CANON` seed) |
| `django_apps/game_data/services/exterior_transport_capacity.py` | `get_active_*` + `space_*_max_per_min_from_row` (game_data SoT) |
| `django_apps/game_data/migrations/0027_exterior_transport_capacity_tier1.py` | Tier-1 formal registration (15/4/48, 1200/288) |
| `django_apps/asteroid_lab/services/rttp_exterior_transport_resolver.py` | `space_belt_max` / `space_pipe_max` @ tier |
| `django_apps/asteroid_lab/services/required_external_connectors.py` | ceildiv + kind → count |
| `django_apps/asteroid_lab/optimization/routing/exterior_connector_planner.py` | Select `required_count` void goals |
| `django_apps/asteroid_lab/optimization/routing/exterior_connector_plan.py` | `ExteriorConnectorPlan` dataclass |
| `django_apps/asteroid_lab/optimization/reconstruction_adapter.py` | Wire planner into `route_goals` |
| `django_apps/asteroid_lab/optimization/skeleton/skeleton_builder.py` | `capacity_goals` from required connectors |
| `django_apps/asteroid_lab/optimization/routing/lift_lane_domain.py` | Void traversable (EVTC-4) |
| `django_apps/asteroid_lab/optimization/routing/route_probe.py` | Priority tie-break (EVTC-v0); weights (EVTC-7) |
| `django_apps/asteroid_lab/optimization/commit/route_path_evidence.py` | Hash + DTO for commit metrics |
| `django_apps/asteroid_lab/optimization/commit/incremental_commit.py` | Emit evidence per commit |
| `django_apps/asteroid_lab/contracts/rttp_layout_issue_codes.py` | New issue codes |
| `django_apps/asteroid_lab/optimization/validation/layout_connectivity_validation.py` | Connector count + path checks |
| `documents/Algorithm/asteroid_lab_01_optimization_input.md` | Invariant text |
| `documents/ai/current_plan.md` | ACTIVE EVTC row |

---

### Task 0: EVTC-0 — Spec queue + plan linkage (docs only)

**Files:**
- Create: `docs/superpowers/specs/2026-05-26-rttp-external-void-transport-capacity-contract.md` (done)
- Create: this plan file (done)
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/specs/2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md` (§14 EVTC pointer)

- [ ] **Step 1: Add ACTIVE row to `current_plan.md`**

Insert after Task 6 CLOSED block:

```markdown
**ACTIVE — EVTC** — **NEXT: EVTC-1a** (shape + fluid DB tier-1 seed) + **EVTC-1b** (both resolvers). A6 CLOSED.
```

- [ ] **Step 2: Add §14 to recovery design spec**

Append to `2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`:

```markdown
## §14 — Post-A6: EVTC (separate track)

Task 6 (A6) closes validation false-positives only. Throughput-aligned exterior connector count, void transport-installable domain, and shortest-path evidence are defined in [`2026-05-26-rttp-external-void-transport-capacity-contract.md`](2026-05-26-rttp-external-void-transport-capacity-contract.md).
```

- [ ] **Step 3: Commit (when user requests)**

```bash
git add docs/superpowers/specs/2026-05-26-rttp-external-void-transport-capacity-contract.md docs/superpowers/plans/2026-05-26-rttp-external-void-transport-capacity-contract.md documents/ai/current_plan.md docs/superpowers/specs/2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md
git commit -m "docs(rttp): add EVTC canonical spec and implementation plan"
```

---

### Task 1a: EVTC-1a — CANON DB registration (shape + fluid tier 1) — **DONE**

**Work classification:** contract change (game_data)

**Files:**
- Create: `django_apps/game_data/models/exterior_transport_capacity.py`
- Create: `django_apps/game_data/services/exterior_transport_capacity.py`
- Create: `django_apps/game_data/migrations/0027_exterior_transport_capacity_tier1.py`
- Test: `tests/unit/game_data/test_exterior_transport_capacity.py`

- [x] **Step 1: Model + tier-1 seed**

```python
# ExteriorShapeTransportCapacity @ speed_tier=1
mini_unit_output_per_min = Decimal("15.0000")  # shapes/min
buildings_per_regular_belt = 4
space_belt_full_belt_count = 48
# → space_belt_max = 2880 (wiki sanity)
```

- [x] **Step 2: Test**

```python
def test_shape_tier1_space_belt_max_is_2880(db) -> None:
    row = get_active_exterior_shape_transport_capacity(speed_tier=1)
    regular = row.mini_unit_output_per_min * Decimal(row.buildings_per_regular_belt)
    assert regular == Decimal("60")
    assert regular * Decimal(row.space_belt_full_belt_count) == Decimal("2880")
```

- [x] **Step 3: Fluid tier-1 CANON** — same migration; `test_fluid_tier1_space_pipe_max_is_345600_from_db`

**Optional follow-up:** tiers 2–5 seed + dump parity (not EVTC-1 blocker).

---

### Task 1b: EVTC-1b — Shape + fluid resolvers + connector ceildiv — **DONE**

**Work classification:** implementation

**Depends on:** Task 1a (CANON DB) complete.

**Files:**
- Create: `django_apps/asteroid_lab/contracts/rttp_exterior_transport_keys.py`
- Create: `django_apps/asteroid_lab/contracts/rttp_exterior_throughput_tier.py`
- Create: `django_apps/asteroid_lab/contracts/rttp_exterior_connector_policy.py`
- Create: `django_apps/asteroid_lab/services/rttp_exterior_transport_resolver.py`
- Create: `django_apps/asteroid_lab/services/required_external_connectors.py`
- Test: `tests/unit/asteroid_lab/test_rttp_exterior_transport_resolver.py`
- Test: `tests/unit/asteroid_lab/test_required_external_connectors.py`

- [x] **Step 1: Write failing resolver tests (shape + fluid)**

```python
def test_tier1_shape_space_belt_max_is_2880(imported_game_data_batch_module) -> None:
    assert space_belt_max_per_min(ExteriorThroughputTier.TIER_1) == Decimal("2880.0000")


def test_tier1_fluid_space_pipe_max_is_345600(imported_game_data_batch_module) -> None:
    assert space_pipe_max_per_min(ExteriorThroughputTier.TIER_1) == Decimal("345600.0000")
```

- [x] **Step 2: Implement resolvers + ceildiv**

```python
def space_belt_max_per_min(tier: ExteriorThroughputTier) -> Decimal:
    row = get_active_exterior_shape_transport_capacity(speed_tier=int(tier))
    regular = row.mini_unit_output_per_min * Decimal(row.buildings_per_regular_belt)
    return regular * Decimal(row.space_belt_full_belt_count)


def space_pipe_max_per_min(tier: ExteriorThroughputTier) -> Decimal:
    row = get_active_exterior_fluid_transport_capacity(speed_tier=int(tier))
    return (
        row.fluid_launcher_output_per_min
        * Decimal(row.space_pipe_full_fluid_launcher_count)
    )
```

- [x] **Step 3: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_rttp_exterior_transport_resolver.py tests/unit/asteroid_lab/test_required_external_connectors.py tests/unit/game_data/test_exterior_shape_transport_capacity.py tests/unit/game_data/test_exterior_fluid_transport_capacity.py -v --tb=short`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(rttp): tier-1 exterior transport resolvers and connector ceildiv"
```

---

### Task 2: EVTC-2 — Exterior connector planner

**Files:**
- Create: `django_apps/asteroid_lab/optimization/routing/exterior_connector_plan.py`
- Create: `django_apps/asteroid_lab/optimization/routing/exterior_connector_planner.py`
- Modify: `django_apps/asteroid_lab/optimization/reconstruction_adapter.py`
- Test: `tests/unit/asteroid_lab/test_exterior_connector_planner.py`

- [ ] **Step 1: Write failing test — goal count matches required**

```python
def test_planner_emits_exactly_required_goals(greenfield_optimization_input) -> None:
    from django_apps.asteroid_lab.optimization.routing.exterior_connector_planner import (
        plan_exterior_connectors,
    )
    from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import (
        RttpSkeletonBuilder,
    )
    from django_apps.asteroid_lab.optimization.input_contracts import RttpSkeletonConfig

    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    plan = plan_exterior_connectors(
        inp,
        skeleton=skeleton,
        required_count=3,
        transport_kind=inp.transport_kind,
    )
    assert len(plan.selected_goals) == 3
    for goal in plan.selected_goals:
        assert goal.coord in inp.external_void_cells
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_connector_planner.py::test_planner_emits_exactly_required_goals -v --tb=short`

- [ ] **Step 3: Implement planner + plan dataclass**

Implement `plan_exterior_connectors` using void candidates with BFS distance 3–5 from mineable (reuse logic pattern from archived Phase C — port minimal functions into planner module, no I/O).

- [ ] **Step 4: Wire `optimization_input_from_reconstruction`**

Replace:

```python
route_goals = _external_margin_route_goals(rim, external_void, transport_kind)
```

With:

```python
from django_apps.asteroid_lab.services.required_external_connectors import (
    required_external_connectors,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
)
# ... compute max from envelope primary resource, then:
required = required_external_connectors(
    max_asteroid_throughput_per_min=Decimal(primary_max_str),
    transport_kind=transport_kind,
)
plan = plan_exterior_connectors(inp_partial, skeleton=None, required_count=required, ...)
route_goals = plan.selected_goals
```

**Note:** Adapter may need two-pass build (complete_map → max throughput → goals) or accept `required_count` passed from `solver_runtime_entry` — prefer computing in adapter from `complete_map` already available at call sites.

- [ ] **Step 5: Run planner tests + `test_rttp_route_goals.py`**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_connector_planner.py tests/unit/asteroid_lab/test_rttp_route_goals.py -v --tb=short`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(rttp): add exterior connector planner and adapter wire"
```

---

### Task 3: EVTC-3 — `capacity_goals` + probe goal set alignment

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/skeleton/skeleton_builder.py`
- Modify: `django_apps/asteroid_lab/optimization/routing/route_goals.py`
- Test: `tests/unit/asteroid_lab/test_skeleton_capacity_goals_evtc.py`

- [ ] **Step 1: Failing test — `skeleton.capacity_goals == required_external_connectors`**

```python
@pytest.mark.django_db
def test_skeleton_capacity_goals_matches_required_connectors(imported_game_data_batch_module) -> None:
    # import_core_recovery_test_map + reconstruction + optimization_input_from_reconstruction
    # assert skeleton.capacity_goals == required_external_connectors(...)
```

- [ ] **Step 2: Change `_capacity_goals` to call `required_external_connectors`**

Pass `max_asteroid_throughput_per_min` via new optional field on `OptimizationInput` **or** compute from envelope in builder if `complete_map` reference is added — **prefer** `OptimizationInput.required_external_connector_count: int | None` set in adapter (explicit, testable).

Add to `OptimizationInput`:

```python
required_external_connector_count: int | None = None
```

In `_capacity_goals`:

```python
if inp.required_external_connector_count is not None:
    return max(0, inp.required_external_connector_count)
# legacy fallback until all callers set field — remove in EVTC-3 follow-up
```

- [ ] **Step 3: Restrict `probe_goal_coords` to `inp.route_goals` only (drop ring_ports from probe targets if spec requires)**

**Decision locked in spec:** probe targets = selected connectors. Update `probe_goal_coords`:

```python
def probe_goal_coords(inp: OptimizationInput, skeleton: RttpSkeleton) -> frozenset[Coord]:
    del skeleton  # ring ports used for planner input only, not extra probe goals
    return frozenset(
        goal.coord
        for goal in inp.route_goals
        if goal.transport_kind is None or goal.transport_kind is inp.transport_kind
    )
```

Update `test_rttp_route_goals.py` — ring ports no longer auto-included in probe set.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_skeleton_capacity_goals_evtc.py tests/unit/asteroid_lab/test_rttp_route_goals.py -v --tb=short`

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(rttp): align capacity_goals and probe goals with EVTC connectors"
```

---

### Task 4: EVTC-4 — Void traversable route domain

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/routing/lift_lane_domain.py`
- Test: `tests/unit/asteroid_lab/test_route_domain_void_traversable.py`

- [ ] **Step 1: Failing test — path may traverse void between platform and connector**

```python
def test_void_cells_traversable_when_in_external_void(domain_builder_fixtures) -> None:
    domain = build_route_domain_from_skeleton(skeleton, inp)
    void_coord = next(iter(inp.external_void_cells))
    assert void_coord in domain.traversable_cells
    assert void_coord not in domain.blocked_cells
```

- [ ] **Step 2: Adjust blocked/traversable sets per spec §6**

Remove blanket `external_void_cells` from blocked; add selected void walk cells to traversable; keep mineable blocked except platform/lift exceptions.

- [ ] **Step 3: Run route + commit tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_route_domain_void_traversable.py tests/unit/asteroid_lab/test_rttp_a5_output_stub_reservation.py tests/unit/asteroid_lab/test_rttp_core_recovery_gate_a.py -v --tb=short`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(rttp): treat external void as transport-traversable in route domain"
```

---

### Task 5: EVTC-5 — Commit-time route evidence

**Files:**
- Create: `django_apps/asteroid_lab/optimization/commit/route_path_evidence.py`
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_commit.py`
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py` (metrics_json merge)
- Test: `tests/unit/asteroid_lab/test_commit_route_path_evidence.py`

- [ ] **Step 1: Failing test — commit metrics include path_hash**

```python
def test_incremental_commit_records_route_evidence_for_successful_commit() -> None:
    # small fixture commit -> result.metrics or pipeline step lists evidence
    assert evidence["path_length"] == len(probe.path)
```

- [ ] **Step 2: Implement `build_route_path_evidence(probe, candidate_id)` returning dict**

Use `hashlib.sha256(repr(path).encode()).hexdigest()[:16]` for stable `path_hash`.

- [ ] **Step 3: Append to commit batch metrics in pipeline `_record_pipeline_step`**

Keys: `required_external_connectors`, `planned_external_connectors`, `commit_route_evidence` (list).

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_commit_route_path_evidence.py -v --tb=short`

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(rttp): persist commit-time route path evidence"
```

---

### Task 6: EVTC-6 — Validation issue codes + Gate EVTC-A

**Files:**
- Modify: `django_apps/asteroid_lab/contracts/rttp_layout_issue_codes.py`
- Modify: `django_apps/asteroid_lab/optimization/validation/layout_connectivity_validation.py`
- Modify: `django_apps/asteroid_lab/services/rttp_recovery_evidence.py` (row fields)
- Test: `tests/unit/asteroid_lab/test_rttp_layout_connectivity_validation.py`
- Test: `tests/unit/asteroid_lab/test_rttp_evtc_gate.py`

- [ ] **Step 1: Add issue codes**

```python
ISSUE_CODE_INSUFFICIENT_EXTERIOR_CONNECTORS = "insufficient_exterior_connectors"
ISSUE_CODE_ROUTE_NOT_SHORTEST_FEASIBLE = "route_not_shortest_feasible"
```

- [ ] **Step 2: Failing tests for insufficient connectors**

Layout with 1 connector reserved but `required=3` → `validation_passed` false, code in tuple.

- [ ] **Step 3: Implement connector counting**

Count distinct `reached_goal` coords from `commit_route_evidence` or reserved route cells touching `inp.route_goals` coords.

- [ ] **Step 4: v0 shortest check**

Re-run `probe_route` in validation **read-only** from stored `probe_start` + domain snapshot hash — **if domain rebuild is too heavy**, defer `route_not_shortest_feasible` to EVTC-6b and only ship `insufficient_exterior_connectors` in EVTC-6.

- [ ] **Step 5: Recovery evidence capture**

Add `required_external_connectors`, `distinct_exterior_connector_count` to `build_recovery_evidence_row`.

Run: `python manage.py capture_rttp_recovery_evidence --import-test-map --output docs/superpowers/reports/2026-05-30-rttp-core-recovery-evidence-after-evtc.json`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(rttp): EVTC validation codes and evidence fields"
```

---

### Task 7: EVTC-7 — Priority tie-break + weighted shortest (v1)

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/routing/route_probe.py`
- Modify: `django_apps/asteroid_lab/optimization/routing/lift_lane_domain.py` (add `traversal_cost` map)
- Test: `tests/unit/asteroid_lab/test_route_probe_weighted.py`

- [ ] **Step 1: v0 — priority tie-break in unweighted BFS**

When multiple goals at same hop count, prefer higher `RouteGoal.priority` (pass `goal_meta: Mapping[Coord, RouteGoal]` into `probe_route`).

- [ ] **Step 2: Failing weighted test — void cheaper than mineable detour**

- [ ] **Step 3: Implement Dijkstra with `traversal_cost`**

- [ ] **Step 4: Full RTTP pytest slice**

Run: `python -m pytest tests/unit/asteroid_lab/ -k "rttp or route_probe or exterior_connector" -v --tb=short`

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(rttp): weighted route probe with void-favoring traversal costs"
```

---

## PR / merge gates (each EVTC PR)

```powershell
python -m pytest tests/unit/asteroid_lab/test_required_external_connectors.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/contracts/ django_apps/asteroid_lab/services/required_external_connectors.py
```

Before EVTC train merge to main:

```powershell
powershell -File scripts/test_fast.ps1
python -m ruff check .
python -m mypy django_apps config src
```

---

## Self-review (plan author)

| Check | Result |
|-------|--------|
| Spec §3 void installable | Task 4 |
| Spec §4 ceildiv + DB-derived saturated denominator | Task 1 |
| Spec §4.2a shape APPROVED | Task 1a-shape + 1b shape path |
| Spec §4.2 unified `port_rate × count` | Task 1a-shape + 1a-fluid + 1b |
| 5760 not tier-1 shape | Task 1b test 2880 |
| 345600 wiki tier-1 fluid sanity | Task 1a-fluid + 1b test from DB |
| Spec §5 planner | Task 2 |
| Spec §5 capacity_goals | Task 3 |
| Spec §7 v0 shortest | Task 7 step 1; Task 6 optional defer |
| Spec §8 commit evidence | Task 5 |
| Spec §9 validation codes | Task 6 |
| A6 boundary (shortfall not validation) | Preserved in spec §2; no task weakens |
| Placeholder scan | No TBD steps |
| `probe_goal_coords` ring port behavior change | Task 3 explicit test update |

**Gap note:** `optimization_input_from_reconstruction` may need `complete_map` + envelope in all call paths — verify `solver_runtime_entry` and tests pass `complete_map` before Task 2 Step 4.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-26-rttp-external-void-transport-capacity-contract.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per EVTC PR (0→7), review between PRs  
2. **Inline Execution** — implement EVTC-1 in this session with executing-plans checkpoints  

Which approach?
