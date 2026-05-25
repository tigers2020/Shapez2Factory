# RTTP FOT PR-2 — Outward Rim, Void Attach, Probe Start — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Admit rim-outward candidates whose FOT sits on `external_void ∪ ring_cells`, and route-probe from rim `platform_coord` when `output_stub` is void-blocked — without a `transport_installable_in_void` flag and without §0.2 void pre-install.

**Architecture:** New `transport_attach_surface.py` + `route_probe_start.py` (shared resolver). Extend `_validate_geometry` for `OUTWARD_FROM_RIM`. Replace hard-coded `probe_route(domain, output_stub, …)` with `resolve_route_probe_start` in generator and `incremental_commit`. Pipeline switches to `OUTWARD_FROM_RIM` + `PLATFORM_FALLBACK_WHEN_STUB_BLOCKED`.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy (`django_apps config src`)

**Spec:** [`docs/superpowers/specs/2026-05-28-rttp-fot-pr2-outward-rim-void-probe-design.md`](../specs/2026-05-28-rttp-fot-pr2-outward-rim-void-probe-design.md)

**Branch:** `feat/rttp-fot-pr2-outward-rim-void-probe`

**Work classification:** contract change · implementation change

**Prerequisite:** PR-1 merged or present on branch (`OUTSIDE_MINEABLE`, FOT mineable reject, commit defense).

**Must NOT:** Global void traversable; validation repair; replay as solver input; move extractor off mineable.

**Coordinate reminder:** FOT = anchor + 1×unit(output_dir). `output_stub` = anchor + 2×unit. Probe start may equal `anchor_coord` (platform), not stub.

---

## File map

| Action | Path |
|--------|------|
| Create | `django_apps/asteroid_lab/optimization/candidates/transport_attach_surface.py` |
| Create | `django_apps/asteroid_lab/optimization/routing/route_probe_start.py` |
| Modify | `django_apps/asteroid_lab/optimization/candidates/candidate_dtos.py` |
| Modify | `django_apps/asteroid_lab/optimization/candidates/candidate_generator.py` |
| Modify | `django_apps/asteroid_lab/optimization/candidates/__init__.py` |
| Modify | `django_apps/asteroid_lab/optimization/routing/route_probe.py` (export `_initial_phase` or duplicate in resolver) |
| Modify | `django_apps/asteroid_lab/optimization/commit/incremental_commit.py` |
| Modify | `django_apps/asteroid_lab/optimization/pipeline.py` |
| Modify | `django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py` (optional `route_probe_start` on metrics) |
| Create | `tests/unit/asteroid_lab/test_fot_pr2_outward_rim_void_probe.py` |
| Modify | `tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py` (keep PR-1 tests on `OUTSIDE_MINEABLE`) |
| Modify | `tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py` |
| Modify | `tests/unit/asteroid_lab/test_rttp_commit.py` |
| Modify | `documents/ai/current_plan.md` (plan link → ACTIVE) |

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Create branch**

```powershell
Set-Location F:\Python_Projects\shapez2Factory
git checkout master
git pull
git checkout -b feat/rttp-fot-pr2-outward-rim-void-probe
```

- [ ] **Step 2: Baseline PR-1 narrow gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py tests/unit/asteroid_lab/test_rttp_commit.py -v --tb=short
```

Expected: PASS.

---

### Task 1: Enums + attach surface module

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/candidates/candidate_dtos.py`
- Create: `django_apps/asteroid_lab/optimization/candidates/transport_attach_surface.py`
- Create: `tests/unit/asteroid_lab/test_fot_pr2_outward_rim_void_probe.py`

- [ ] **Step 1: Write failing tests**

Add to `test_fot_pr2_outward_rim_void_probe.py`:

```python
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    CandidateRejectReason,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.transport_attach_surface import (
    outward_dirs,
    transport_attach_surface_cells,
)


def test_route_probe_start_policy_enum() -> None:
    assert (
        RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED.value
        == "platform_fallback_when_stub_blocked"
    )


def test_reject_reason_attach_surface_exists() -> None:
    assert (
        CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_NOT_ON_ATTACH_SURFACE.value
        == "fixed_output_transport_not_on_attach_surface"
    )


def test_reject_reason_probe_start_blocked_exists() -> None:
    assert (
        CandidateRejectReason.ROUTE_PROBE_START_BLOCKED.value
        == "route_probe_start_blocked"
    )
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_pr2_outward_rim_void_probe.py -v --tb=short
```

- [ ] **Step 3: Implement enums in `candidate_dtos.py`**

```python
class RouteProbeStartPolicy(StrEnum):
    OUTPUT_STUB_ONLY = "output_stub_only"
    PLATFORM_FALLBACK_WHEN_STUB_BLOCKED = "platform_fallback_when_stub_blocked"
```

Add to `CandidateRejectReason`:

```python
FIXED_OUTPUT_TRANSPORT_NOT_ON_ATTACH_SURFACE = "fixed_output_transport_not_on_attach_surface"
ROUTE_PROBE_START_BLOCKED = "route_probe_start_blocked"
```

Export in `candidates/__init__.py`.

- [ ] **Step 4: Implement `transport_attach_surface.py`**

```python
from django_apps.asteroid_lab.adapters.catalog_geometry_transform import cardinal_unit_vector
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import RouteCellDomain
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def transport_attach_surface_cells(
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
) -> frozenset[Coord]:
    return frozenset(inp.external_void_cells | skeleton.ring_cells)


def outward_dirs(
    anchor: Coord,
    output_dir: str,
    *,
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    domain: RouteCellDomain,
) -> frozenset[str]:
    attach = transport_attach_surface_cells(inp, skeleton)
    goals = probe_goal_coords(inp, skeleton)
    outward: set[str] = set()
    for direction in ("N", "E", "S", "W"):
        unit = cardinal_unit_vector(CardinalDirection(direction))
        neighbor = (anchor[0] + unit[0], anchor[1] + unit[1])
        if neighbor in inp.mineable_cells:
            continue
        if neighbor in inp.blocked_incompatible_transport_cells:
            continue
        if neighbor in attach or neighbor in goals:
            outward.add(direction)
    if output_dir in outward:
        return frozenset({output_dir})
    return frozenset(outward)
```

Adjust `outward_dirs` signature if catalog only needs “is this rotation outward” — normative check in generator: `spec.output_dir in outward_dirs(...)`.

- [ ] **Step 5: Re-run enum tests — PASS**

---

### Task 2: `resolve_route_probe_start`

**Files:**
- Create: `django_apps/asteroid_lab/optimization/routing/route_probe_start.py`
- Modify: `django_apps/asteroid_lab/optimization/routing/route_probe.py`

- [ ] **Step 1: Write failing resolver test**

```python
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.routing.route_probe_start import (
    RouteProbeStartPolicy,
    resolve_route_probe_start,
)
from tests.support.rttp_narrow_corridor_fixture import build_narrow_corridor_optimization_input


def test_platform_fallback_when_stub_in_void(narrow_skeleton) -> None:
    inp = build_narrow_corridor_optimization_input()
    domain = build_route_domain_from_skeleton(narrow_skeleton, inp)
    anchor = (7, 5)  # west rim in fixture
    stub = (5, 5)  # two steps W into void — adjust to match catalog offset for cat_bv_1_S
    start = resolve_route_probe_start(
        anchor_coord=anchor,
        output_stub=stub,
        domain=domain,
        policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert start == anchor
    assert start not in domain.blocked_cells
```

Tune `anchor`/`stub` from `build_catalog_placement_specs` projection for `cat_bv_1_S` at `(7,5)`.

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement resolver**

Move or re-export `initial_phase` from `route_probe.py`:

```python
def resolve_route_probe_start(
    *,
    anchor_coord: Coord,
    output_stub: Coord,
    domain: RouteCellDomain,
    policy: RouteProbeStartPolicy,
) -> Coord | None:
    from django_apps.asteroid_lab.optimization.routing.route_probe import initial_phase

    if output_stub not in domain.blocked_cells and initial_phase(domain, output_stub) is not None:
        return output_stub
    if policy is RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED:
        if initial_phase(domain, anchor_coord) == "platform":
            return anchor_coord
    return None
```

Rename `_initial_phase` → `initial_phase` (public) in `route_probe.py`; keep `probe_route` using it.

- [ ] **Step 4: Run resolver test — PASS**

---

### Task 3: Generator geometry + probe wiring

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/candidates/candidate_generator.py`

- [ ] **Step 1: Write failing integration tests**

```python
def test_outward_rejects_inward_rim_rotation(west_rim_greenfield, skeleton) -> None:
    result = generate_candidates(
        west_rim_greenfield,
        skeleton,
        policy=ExtractorPlacementPolicy.RIM_ONLY,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    inward_ids = [r.candidate_id for r in result.rejected_candidates if "cat_bv_1_E" in r.candidate_id]
    assert inward_ids
    assert any(
        r.rejection_reason == CandidateRejectReason.OUTPUT_DIR_NOT_OUTWARD_FROM_RIM
        for r in result.rejected_candidates
    )


def test_narrow_corridor_has_normal_under_outward_policy(narrow_corridor_optimization_input, skeleton) -> None:
    result = generate_candidates(
        narrow_corridor_optimization_input,
        skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert len(result.normal_candidates) >= 1
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Extend `_validate_geometry`**

After PR-1 FOT checks, when `policy is OUTWARD_FROM_RIM` and `anchor in inp.rim_cells`:

```python
dirs = outward_dirs(anchor, spec.output_dir, inp=inp, skeleton=skeleton, domain=domain)
if spec.output_dir not in dirs:
    return CandidateRejectReason.OUTPUT_DIR_NOT_OUTWARD_FROM_RIM
attach = transport_attach_surface_cells(inp, skeleton)
if fot_abs not in attach:
    return CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_NOT_ON_ATTACH_SURFACE
```

Pass `skeleton` and `domain` into `_validate_geometry` (build domain once per `generate_candidates` call — already exists).

- [ ] **Step 4: Replace probe start**

```python
start = resolve_route_probe_start(
    anchor_coord=anchor,
    output_stub=output_stub,
    domain=domain,
    policy=route_probe_start_policy,
)
if start is None:
    rejected.append(..., rejection_reason=CandidateRejectReason.ROUTE_PROBE_START_BLOCKED, ...)
    continue
probe = probe_route(domain, start, goals, max_expansions=max_expansions)
```

Add kwarg `route_probe_start_policy: RouteProbeStartPolicy = RouteProbeStartPolicy.OUTPUT_STUB_ONLY` for backward compat in unit tests; production via pipeline uses `PLATFORM_FALLBACK_WHEN_STUB_BLOCKED`.

Optional: set `route_probe_start=start` on `BundleCandidate` (new field, default `output_stub` in dataclass for manual construction).

- [ ] **Step 5: Run integration tests — PASS**

---

### Task 4: Commit reprobe parity

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_commit.py`

- [ ] **Step 1: Write failing test in `test_rttp_commit.py`**

Assert `attempt_commit_candidate` succeeds for narrow corridor candidate when stub blocked but platform reachable — same candidate IDs as `NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID` under PR-2 policies.

- [ ] **Step 2: Wire commit**

```python
start = resolve_route_probe_start(
    anchor_coord=candidate.anchor_coord,
    output_stub=candidate.output_stub,
    domain=current_domain,
    policy=route_probe_start_policy,  # thread from pipeline config or default PR-2
)
if start is None:
    return CommitAttemptOutcome(..., reason=CommitConflictReason.REPROBE_FAILED)  # or new REPROBE_START_BLOCKED
probe = probe_route(current_domain, start, goals, ...)
```

Prefer reusing `REPROBE_FAILED` unless spec demands new `CommitConflictReason`.

- [ ] **Step 3: Run commit tests — PASS**

---

### Task 5: Pipeline defaults

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`

- [ ] **Step 1: Change `generate_candidates` calls**

```python
fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
```

Keep PR-1 tests using `OUTSIDE_MINEABLE` explicitly.

- [ ] **Step 2: Run pipeline-touching tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_pr2_outward_rim_void_probe.py tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py tests/unit/asteroid_lab/test_rttp_commit.py -v --tb=short
```

---

### Task 6: Overlay / replay (optional field)

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py`
- Modify: `tests/unit/asteroid_lab/test_placement_overlay_projection.py`

- [ ] **Step 1: Test FOT on void coord in overlay**

When normal candidate has `fot_abs in external_void_cells`, confirmed overlay row exists at FOT coord.

- [ ] **Step 2: Emit `route_probe_start` in replay metrics dict (output-only)**

No solver input wiring.

---

### Task 7: Ruff + plan doc

- [ ] **Step 1: Ruff**

```powershell
python -m ruff check django_apps/asteroid_lab/optimization/candidates/transport_attach_surface.py django_apps/asteroid_lab/optimization/routing/route_probe_start.py django_apps/asteroid_lab/optimization/candidates/candidate_generator.py django_apps/asteroid_lab/optimization/commit/incremental_commit.py
```

- [ ] **Step 2: Update `current_plan.md`**

Replace `Plan: TBD` with link to this file.

---

## Verification matrix

| Command | Expect |
|---------|--------|
| `python -m pytest tests/unit/asteroid_lab/test_fot_pr2_outward_rim_void_probe.py -v --tb=short` | PASS |
| `python -m pytest tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py -v --tb=short` | PASS (PR-1 policies unchanged) |
| `python -m ruff check <paths above>` | PASS |

Full gate before PR: `powershell -File scripts/test_full.ps1` → ruff → mypy → black → pytest (per AGENTS.md).

---

## Out of scope (PR-3)

- Regret scoring for ring alignment
- `PENALIZE_FIELD_USAGE` policy behavior
