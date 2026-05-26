# FL-06 Output Stub / Route Reservation Alignment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix T1b FL-06 on diagnostic canon by aligning commit-time route reservation with `validate_final_layout` — either include `output_stub` in `reserved_route_cells` or reject commit when stub cannot be legally reserved — without validation relaxation.

**Architecture:** Investigation-first: capture `probe_start`, `probe.path`, and `route_cells` at commit time (H1a/H1b). Implement minimal contract-correct change in `incremental_commit._attempt_commit_one` (or adjacent helper) after Q1–Q4 are answered. Verify with unit fixture + canon CLI probe.

**Tech Stack:** Python 3.12+, Django 5.2, pytest, ruff, mypy paths per AGENTS.md.

**Design spec:** [`docs/superpowers/specs/2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md`](../specs/2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md)

**E-track baseline:** [`90fba2ed`](https://github.com/tigers2020/Shapez2Factory/commit/90fba2ed) — primary FL-06, SolverRun 108.

---

## File structure

| File | Responsibility |
|------|----------------|
| `harness/investigation/commit_route_reservation_diagnostic.py` | Capture probe_start / path / route_cells vs output_stub |
| `tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py` | Reproduction + regression tests |
| `django_apps/asteroid_lab/optimization/commit/incremental_commit.py` | Minimal fix (Task 4 only, after investigation) |
| `docs/superpowers/reports/2026-05-30-rttp-fl06-route-reservation-investigation-notes.md` | Q1–Q6 answers (Task 3) |
| `documents/ai/current_plan.md` | FL-06 track close metadata (Task 6) |

**Not modified until Task 4:** `final_validation.py` (no relaxation).

---

## Spec → plan coverage

| Spec § | Task |
|--------|------|
| §6 Q1–Q4 | Task 1–3 |
| §7 Option B | Task 4 decision gate |
| §9 acceptance | Task 2, 4, 5, 6 |

---

### Task 1: Commit route reservation diagnostic harness

**Files:**
- Create: `harness/investigation/commit_route_reservation_diagnostic.py`
- Test: `tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py`

- [ ] **Step 1: Write failing diagnostic test**

Create `tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py`:

```python
"""FL-06 — output_stub vs commit-time route reservation alignment."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    _attempt_commit_one,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import (
    RttpSkeletonBuilder,
)
from django_apps.asteroid_lab.optimization.input_contracts import RttpSkeletonConfig
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from harness.investigation.commit_route_reservation_diagnostic import (
    CommitRouteReservationSnapshot,
    snapshot_commit_reservation,
)
from tests.support.rttp_narrow_corridor_fixture import (
    NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
    candidate_by_id,
)


@pytest.fixture
def narrow_corridor_optimization_input() -> OptimizationInput:
    from tests.support.rttp_narrow_corridor_fixture import (
        build_narrow_corridor_optimization_input,
    )

    return build_narrow_corridor_optimization_input()


@pytest.fixture
def narrow_skeleton(narrow_corridor_optimization_input: OptimizationInput):
    return RttpSkeletonBuilder.build(
        narrow_corridor_optimization_input,
        config=RttpSkeletonConfig(),
    )


def test_snapshot_commit_reservation_exports_probe_start_and_stub_membership(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    inp = narrow_corridor_optimization_input
    generation = generate_candidates(
        inp,
        narrow_skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    cand = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    domain = initial_commit_domain(narrow_skeleton, inp)
    goals = frozenset(probe_goal_coords(inp))
    snap = snapshot_commit_reservation(
        cand,
        skeleton=narrow_skeleton,
        inp=inp,
        goals=goals,
        committed_occupied=frozenset(),
        committed_route_cells=frozenset(),
        committed_fixed_output_transport_cells=frozenset(),
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert isinstance(snap, CommitRouteReservationSnapshot)
    assert snap.output_stub == cand.output_stub
    assert snap.probe_start is not None
    assert isinstance(snap.stub_in_path, bool)
    assert isinstance(snap.stub_in_route_cells, bool)
```

- [ ] **Step 2: Run test — expect FAIL (module missing)**

Run:

```bash
python -m pytest tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py::test_snapshot_commit_reservation_exports_probe_start_and_stub_membership -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement diagnostic module**

Create `harness/investigation/commit_route_reservation_diagnostic.py`:

```python
"""Commit-time route reservation diagnostic (FL-06 investigation)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    _attempt_commit_one,
    _route_cells_from_path,
    _rebuild_domain,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.route_probe import probe_route
from django_apps.asteroid_lab.optimization.routing.route_probe_start import (
    resolve_route_probe_start,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


@dataclass(frozen=True, slots=True)
class CommitRouteReservationSnapshot:
    candidate_id: str
    output_stub: Coord
    probe_start: Coord | None
    probe_start_is_output_stub: bool
    path: tuple[Coord, ...]
    route_cells: frozenset[Coord]
    stub_in_path: bool
    stub_in_route_cells: bool
    attempt_committed: bool


def snapshot_commit_reservation(
    candidate: BundleCandidate,
    *,
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goals: frozenset[Coord],
    committed_occupied: frozenset[Coord],
    committed_route_cells: frozenset[Coord],
    committed_fixed_output_transport_cells: frozenset[Coord],
    route_probe_start_policy: RouteProbeStartPolicy,
) -> CommitRouteReservationSnapshot:
    current_domain = _rebuild_domain(
        skeleton,
        inp,
        committed_occupied=committed_occupied,
        committed_route_cells=committed_route_cells,
    )
    probe_start = resolve_route_probe_start(
        anchor_coord=candidate.anchor_coord,
        output_stub=candidate.output_stub,
        domain=current_domain,
        policy=route_probe_start_policy,
    )
    path: tuple[Coord, ...] = ()
    route_cells: frozenset[Coord] = frozenset()
    if probe_start is not None:
        probe = probe_route(current_domain, probe_start, goals)
        path = probe.path
        route_cells = _route_cells_from_path(path, candidate.occupied_cells)
    outcome = _attempt_commit_one(
        candidate,
        skeleton=skeleton,
        inp=inp,
        goals=goals,
        committed_occupied=committed_occupied,
        committed_route_cells=committed_route_cells,
        committed_fixed_output_transport_cells=committed_fixed_output_transport_cells,
        route_probe_start_policy=route_probe_start_policy,
    )
    stub = candidate.output_stub
    return CommitRouteReservationSnapshot(
        candidate_id=candidate.candidate_id,
        output_stub=stub,
        probe_start=probe_start,
        probe_start_is_output_stub=probe_start == stub,
        path=path,
        route_cells=route_cells,
        stub_in_path=stub in path,
        stub_in_route_cells=stub in route_cells,
        attempt_committed=outcome.committed,
    )


__all__ = ["CommitRouteReservationSnapshot", "snapshot_commit_reservation"]
```

Note: imports `_rebuild_domain`, `_route_cells_from_path` from commit module — investigation harness only; do not use as solver input.

- [ ] **Step 4: Run test — expect PASS**

Run:

```bash
python -m pytest tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py::test_snapshot_commit_reservation_exports_probe_start_and_stub_membership -v
```

- [ ] **Step 5: Ruff**

```bash
python -m ruff check harness/investigation/commit_route_reservation_diagnostic.py tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py
```

---

### Task 2: FL-06 reproduction regression test

**Files:**
- Modify: `tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py`

- [ ] **Step 1: Add failing regression — stub omission fails final validation**

Append to `test_fl06_route_reservation_alignment.py`:

```python
from django_apps.asteroid_lab.optimization.commit.incremental_commit import incremental_commit
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)
from harness.investigation.rttp_final_layout_assert_probe import (
    FinalLayoutAssertCode,
    diagnose_final_layout,
)


def test_incremental_commit_reserved_routes_must_include_output_stub(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    """When reserved routes exist, output_stub must be reserved (FL-06 contract)."""
    inp = narrow_corridor_optimization_input
    generation = generate_candidates(
        inp,
        narrow_skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    cand = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    domain = initial_commit_domain(narrow_skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=(cand.candidate_id,)),
        {cand.candidate_id: cand},
        inp,
        narrow_skeleton,
        domain=domain,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    by_id = {cand.candidate_id: cand}
    layout_ok = validate_final_layout(
        result.committed_ids,
        result.reserved_route_cells,
        by_id,
        inp,
    )
    code, detail = diagnose_final_layout(
        result.committed_ids,
        result.reserved_route_cells,
        by_id,
        inp,
    )
    if result.reserved_route_cells:
        assert layout_ok, (code, detail)
        assert code is FinalLayoutAssertCode.FL_OK, detail
    else:
        pytest.skip("no reserved routes — FL-06 not applicable")
```

- [ ] **Step 2: Run — document PASS or FAIL**

Run:

```bash
python -m pytest tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py -v
```

If **FAIL** with FL-06 on narrow corridor → reproduction confirmed (expected pre-fix).  
If **PASS** → extend fixture toward multi-commit stress or canon-derived coords in Task 3.

---

### Task 3: Canon FL-06 candidate diagnostic (Q1–Q6)

**Files:**
- Create: `docs/superpowers/reports/2026-05-30-rttp-fl06-route-reservation-investigation-notes.md`
- Modify: `harness/investigation/run_canon_slug_probe.py` (optional: emit reservation snapshot for first FL-06 candidate)

- [ ] **Step 1: Extend canon probe to capture reservation snapshot for failing candidate**

Add optional diagnostic in `run_canon_probe` after `diagnose_final_layout`: for the failing `candidate_id` in detail, call `snapshot_commit_reservation` with replayed commit domain state **or** document manual capture steps in investigation notes if full replay is too heavy for v1.

Minimum investigation notes template:

```markdown
# FL-06 Route Reservation Investigation Notes

## Failing candidate (Run 108)
- candidate_id: ...
- output_stub: (-1, -16)

## Q1 probe_start: ...
## Q2 probe_start == output_stub: ...
## Q3 stub in path: ...
## Q4 stub in route_cells: ...
## Q5 policy: PLATFORM_FALLBACK_WHEN_STUB_BLOCKED (default OUTWARD_FROM_RIM)
## Q6 N-direction geometry: ...

## Root cause classification: H1a | H1b | H3 | H4
## Chosen fix option: A (with proof) | B | C
```

- [ ] **Step 2: Run canon probe and fill notes**

```bash
python -m harness.investigation.run_canon_slug_probe
```

Record output in investigation notes; classify H1a/H1b/H3/H4.

---

### Task 4: Minimal contract-correct fix

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_commit.py` (inside `_attempt_commit_one`, after `route_cells` computed)
- Test: `tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py`

**Decision gate (from Task 3 notes):**

- If stub legal but omitted → guarded union (Option A with proof):

```python
if (
    candidate.output_stub not in route_cells
    and candidate.output_stub not in candidate.occupied_cells
    and candidate.output_stub not in current_domain.blocked_cells
):
    route_cells = frozenset({candidate.output_stub}) | route_cells
```

- If stub blocked and fallback used → Option B: extend path/reservation to include attachment segment **or** return `REPROBE_FAILED` / new conflict when stub cannot be reserved (do **not** weaken validation).

- [ ] **Step 1: Implement chosen fix per investigation notes**
- [ ] **Step 2: Run Task 2 regression — expect PASS**
- [ ] **Step 3: Run existing commit tests — no regression**

```bash
python -m pytest tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py tests/unit/asteroid_lab/test_rttp_commit.py tests/unit/asteroid_lab/test_fot_pr2_outward_rim_void_probe.py -v
```

---

### Task 5: Canon slug verification

- [ ] **Step 1: Run canon probe**

```bash
python -m harness.investigation.run_canon_slug_probe
```

Expected: `primary_fl_xx` = **FL-OK** (or not FL-06); `forensics.catalog_passed` = true.

- [ ] **Step 2: Run investigation integration test if canon slug seeded in test DB**

```bash
python -m pytest tests/investigation/test_rttp_t1b_canon_slug_layout_probe.py -v
```

---

### Task 6: Governance close

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`
- Modify: `docs/superpowers/specs/2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md` (Status → CLOSED after merge)

- [ ] **Step 1: Update current_plan** — FL-06 fix CLOSED with merge SHA; T1b canon T1b PASS note
- [ ] **Step 2: Full gate (product fix scope)**

```bash
python -m pytest tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py tests/investigation/ -v
python -m ruff check django_apps/asteroid_lab/optimization/commit/incremental_commit.py harness/investigation tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py
python -m ruff check .
python -m mypy django_apps config src
```

---

## Self-review

| Check | Status |
|-------|--------|
| Spec §6 questions → Task 1–3 | OK |
| No validation relaxation in plan | OK |
| Option A gated on legality proof | OK |
| Placeholder scan | No TBD in task code blocks |

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-30-rttp-fl06-output-stub-route-reservation-alignment.md`.

**Two execution options:**

1. **Subagent-driven** — task-per-subagent with review between tasks  
2. **Inline** — execute Tasks 1→6 in session with checkpoints

**Which approach?**
