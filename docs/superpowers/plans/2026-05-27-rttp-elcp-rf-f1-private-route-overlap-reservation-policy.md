# P1-ELCP-RF-F1 — Private Route Overlap Reservation Policy — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement F0 §3–§4 reservation policy in production commit: legal shared trunk reuse allowed, illegal private approach overlap still rejected; measure ≥50% reduction in E0 `private_route_overlap` mechanism rows (23 baseline) on Gate A overlap-pack stale universe.

**Architecture:** Extract pure policy builders (`shareable_at_commit`, `ReservationCandidateCells`) in `reservation_overlap_policy.py`; wire ELCP loop in `incremental_commit.py` (F1a overlap input + shareable union, F1b committed delta). Update E0 harness replay for G1 (F1c). TDD: Tier C unit tests first, then production, then Tier S/G investigation.

**Tech Stack:** Python 3.12+, Django/pytest, `GREEDY_REGRET_OVERLAP_PACK`, `incremental_commit`, `exterior_lane_trunk`, E0 harness replay.

**Design spec:** [`docs/superpowers/specs/2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md`](../specs/2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md)

**F1a transitional (explicit):** F1a may commit `outcome.route_cells` (full merged) while overlap uses `ReservationCandidateCells` only. F1b MUST set `committed_route_cells |= reservation_candidate_cells` on ELCP success.

---

## File structure

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/optimization/commit/exterior_lane_trunk.py` | `shareable_trunk_cells_for_transport` (transport_kind filter + prospective new_trunk) |
| `django_apps/asteroid_lab/optimization/commit/reservation_overlap_policy.py` | **NEW** — pure F0 pipeline steps 2–5 helpers |
| `django_apps/asteroid_lab/optimization/commit/incremental_commit.py` | Wire ELCP + `_attempt_commit_one` overlap/committed params |
| `tests/unit/asteroid_lab/test_reservation_overlap_policy.py` | **NEW** — Tier C1–C5 (no DB) |
| `tests/unit/asteroid_lab/test_exterior_lane_trunk.py` | Extend shareable union tests |
| `tests/unit/asteroid_lab/test_rttp_route_spine_trunk_sharing.py` | Tier S regression after F1a |
| `tests/support/rttp_f1_gate_a_g1_bounds.py` | **NEW** — G1 frozen constants (investigation only) |
| `harness/investigation/rttp_elcp_e0_reservation_mechanism.py` | F1c replay uses F0 pipeline helpers |
| `tests/investigation/test_rttp_elcp_rf_f1_reservation_policy_gate_a.py` | **NEW** — G1 assertion on replay histogram |
| `tests/investigation/test_rttp_elcp_rf_e0_reservation_mechanism.py` | Keep green (E0 contract); may relax only if spec-amended |
| `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy-report.md` | **NEW** — G1 counts, SHA, before/after histogram |
| `documents/ai/current_plan.md` | ACTIVE F1 → CLOSED when report + gates green |

**Not modified:** selection modes default, validation repair, `lane_capacity_shortfall` policy, inlet guards (unless FL-06 stub path shared).

---

## Spec → plan coverage

| Spec § | Task |
|--------|------|
| §3.1 ShareableTrunkCells + prospective trunk | Task 1, 4 |
| §3.2 ReservationCandidateCells + FL-06 bounds + no full path | Task 2, 3 |
| §3.3 PrivateRouteOverlap | Task 3, 4 |
| §4.1 Pipeline order | Task 2–4 |
| §4.2 SPINE-G* | Task 2, 3 |
| §5 INV-S1..S6 | Task 3, 5, 7 |
| §6 F1a/b/c | Tasks 3–4 (a), 5 (b), 6–7 (c) |
| §7 Tier S/C/G | Tasks 3, 5, 7 |
| §9 no new conflict enum | All tasks |

---

### Task 0: Queue + spec linkage

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/specs/2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md` (add plan link in header)

- [ ] **Step 1: Add ACTIVE row** after E0 CLOSED line in `documents/ai/current_plan.md`:

```markdown
**ACTIVE (2026-05-27):** **P1-ELCP-RF-F1** — private route overlap / shareable trunk reservation policy (F0 contract → production F1a/F1b/F1c). Spec: [`2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md`](../../docs/superpowers/specs/2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md) · plan: [`2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy.md`](../../docs/superpowers/plans/2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy.md).
```

- [ ] **Step 2: Link plan in F0 spec header** — replace `Implementation plan: *Not in F0*` with plan path above.

- [ ] **Step 3: Commit** (only when user explicitly requests a commit)

```bash
git add documents/ai/current_plan.md docs/superpowers/specs/2026-05-27-rttp-elcp-rf-f0-private-route-overlap-reservation-policy-design.md docs/superpowers/plans/2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy.md
git commit -m "docs: add P1-ELCP-RF-F1 reservation policy implementation plan"
```

---

## Phase F1a — Shareable union + ReservationCandidateCells overlap input + spine guard

### Task 1: Shareable trunk helper (transport_kind + prospective trunk)

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/exterior_lane_trunk.py`
- Modify: `tests/unit/asteroid_lab/test_exterior_lane_trunk.py`

- [ ] **Step 1: Write failing test C1**

Add to `tests/unit/asteroid_lab/test_exterior_lane_trunk.py`:

```python
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import TransportKind
from django_apps.asteroid_lab.optimization.commit.exterior_lane_trunk import (
    shareable_trunk_cells_for_transport,
)


def test_shareable_trunk_cells_for_transport_filters_kind_and_adds_prospective() -> None:
    s_shape = _state(frozenset({(1, 0)}))
    s_fluid = ExteriorLaneTrunkState(
        lane_id="exterior_lane:fluid_pipe:0",
        transport_kind=TransportKind.FLUID_PIPE,
        active=True,
        assigned_load_per_min=Decimal("0"),
        trunk_cells=frozenset({(9, 9)}),
        connector_coord=(10, 9),
    )
    shareable = shareable_trunk_cells_for_transport(
        (s_shape, s_fluid),
        transport_kind=TransportKind.SHAPE_BELT,
        prospective_new_trunk=frozenset({(2, 0)}),
    )
    assert shareable == frozenset({(1, 0), (2, 0)})
    assert (9, 9) not in shareable
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_trunk.py::test_shareable_trunk_cells_for_transport_filters_kind_and_adds_prospective -v`  
Expected: FAIL — `ImportError: cannot import name 'shareable_trunk_cells_for_transport'`

- [ ] **Step 3: Implement helper**

Add to `exterior_lane_trunk.py` (after `shareable_trunk_cells_from_states`):

```python
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import TransportKind


def shareable_trunk_cells_for_transport(
    states: tuple[ExteriorLaneTrunkState, ...],
    *,
    transport_kind: TransportKind,
    prospective_new_trunk: frozenset[Coord] = frozenset(),
) -> frozenset[Coord]:
    """F0 §3.1: active lane trunk union for one transport_kind plus partition-classified new trunk."""

    merged: set[Coord] = set(prospective_new_trunk)
    for state in states:
        if state.active and state.transport_kind is transport_kind:
            merged.update(state.trunk_cells)
    return frozenset(merged)
```

Add to `__all__`: `"shareable_trunk_cells_for_transport"`.

Keep `shareable_trunk_cells_from_states` delegating to all active lanes (existing tests unchanged) OR document it as legacy; do not break `test_shareable_trunk_union`.

- [ ] **Step 4: Run test — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_trunk.py::test_shareable_trunk_cells_for_transport_filters_kind_and_adds_prospective -v`  
Expected: PASS

- [ ] **Step 5: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/optimization/commit/exterior_lane_trunk.py tests/unit/asteroid_lab/test_exterior_lane_trunk.py`

---

### Task 2: Pure reservation pipeline module (F0 §4 steps 2–5)

**Files:**
- Create: `django_apps/asteroid_lab/optimization/commit/reservation_overlap_policy.py`
- Create: `tests/unit/asteroid_lab/test_reservation_overlap_policy.py`

- [ ] **Step 1: Write failing tests C2–C5 (minimal fixtures)**

Create `tests/unit/asteroid_lab/test_reservation_overlap_policy.py`:

```python
"""F0 Tier C — reservation overlap policy (no DB)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.commit.reservation_overlap_policy import (
    build_elcp_base_cells,
    build_reservation_candidate_cells,
    spine_delta_allowed_in_reservation,
)
from django_apps.asteroid_lab.optimization.coords import Coord


def test_build_elcp_base_cells_excludes_reused_trunk() -> None:
    base = build_elcp_base_cells(
        branch_cells=((0, 1), (0, 0)),
        new_trunk_cells=((1, 0),),
        reused_trunk_cells=((1, 0), (2, 0)),
    )
    assert base == frozenset({(0, 1), (0, 0), (1, 0)})
    assert (2, 0) not in base


def test_spine_delta_allowed_excludes_cells_not_in_shareable_or_fl06() -> None:
    spine_delta = frozenset({(5, 5), (1, 0)})
    shareable = frozenset({(1, 0)})
    fl06_required = frozenset()
    allowed = spine_delta_allowed_in_reservation(
        spine_delta,
        shareable_trunk_cells=shareable,
        fl06_required_cells=fl06_required,
    )
    assert allowed == frozenset({(1, 0)})


def test_build_reservation_candidate_cells_never_includes_full_probe_path() -> None:
    """C5 + INV-S6: probe path (4,4)(5,4) must not appear if not in branch/trunk/stub/spine allowance."""
    base = frozenset({(0, 0)})
    stub_aligned = frozenset({(0, 0), (-1, 0)})  # stub required
    spine_delta = frozenset({(5, 4), (4, 4)})  # parallel highway attempt
    shareable = frozenset()
    result = build_reservation_candidate_cells(
        stub_aligned_cells=stub_aligned,
        spine_delta_cells=spine_delta,
        shareable_trunk_cells=shareable,
        fl06_required_cells=stub_aligned,
    )
    assert (4, 4) not in result
    assert (5, 4) not in result
    assert (-1, 0) in result
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_reservation_overlap_policy.py -v`  
Expected: FAIL — module not found

- [ ] **Step 3: Implement `reservation_overlap_policy.py`**

```python
"""F0 §3–§4: shareable trunk and reservation candidate cell policy (pure helpers)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.coords import Coord


def build_elcp_base_cells(
    *,
    branch_cells: tuple[Coord, ...],
    new_trunk_cells: tuple[Coord, ...],
    reused_trunk_cells: tuple[Coord, ...],
) -> frozenset[Coord]:
  _ = reused_trunk_cells  # evidence only; MUST NOT enter base (F0 §3.2)
  return frozenset(branch_cells) | frozenset(new_trunk_cells)


def spine_delta_allowed_in_reservation(
    spine_delta_cells: frozenset[Coord],
    *,
    shareable_trunk_cells: frozenset[Coord],
    fl06_required_cells: frozenset[Coord],
) -> frozenset[Coord]:
  """SPINE-G3/G4: spine cells only when trunk-touch or FL-06 required."""

  return frozenset(
      c
      for c in spine_delta_cells
      if c in shareable_trunk_cells or c in fl06_required_cells
  )


def build_reservation_candidate_cells(
    *,
    stub_aligned_cells: frozenset[Coord],
    spine_delta_cells: frozenset[Coord],
    shareable_trunk_cells: frozenset[Coord],
    fl06_required_cells: frozenset[Coord],
) -> frozenset[Coord]:
  allowed_spine = spine_delta_allowed_in_reservation(
      spine_delta_cells,
      shareable_trunk_cells=shareable_trunk_cells,
      fl06_required_cells=fl06_required_cells,
  )
  return stub_aligned_cells | allowed_spine


__all__ = [
    "build_elcp_base_cells",
    "build_reservation_candidate_cells",
    "spine_delta_allowed_in_reservation",
]
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_reservation_overlap_policy.py -v`  
Expected: PASS

- [ ] **Step 5: Add C2 test (branch not shareable → private overlap via production predicate)**

```python
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    _private_route_cell_overlap,
)


def test_peer_branch_overlap_is_private_not_shareable() -> None:
    shareable = frozenset({(1, 0)})
    committed = frozenset({(1, 0), (0, 1)})
    reservation = frozenset({(0, 1)})
    private = _private_route_cell_overlap(
        reservation, committed, shareable_trunk_cells=shareable
    )
    assert private == frozenset({(0, 1)})
```

- [ ] **Step 6: Run C2 — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_reservation_overlap_policy.py::test_peer_branch_overlap_is_private_not_shareable -v`

- [ ] **Step 7: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/optimization/commit/reservation_overlap_policy.py tests/unit/asteroid_lab/test_reservation_overlap_policy.py`

---

### Task 3: ELCP reservation builder integrating FL-06 + spine (production helpers)

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/reservation_overlap_policy.py`
- Modify: `tests/unit/asteroid_lab/test_reservation_overlap_policy.py`

- [ ] **Step 1: Add failing integration-style unit test** (uses real stub merge import)

```python
from dataclasses import replace
from unittest.mock import MagicMock

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import TransportKind
from django_apps.asteroid_lab.optimization.commit.reservation_overlap_policy import (
    compute_elcp_reservation_candidate_cells,
)


@pytest.mark.django_db
def test_compute_elcp_reservation_uses_base_not_full_path(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    # Use narrow corridor fixture candidate + minimal branch/new_trunk;
    # assert (4,4) probe interior not in result — mirror Task 2 C5 pattern with real candidate.
    ...
```

**Implementer note:** Import `build_narrow_corridor_optimization_input` + one `BundleCandidate`; build `base_cells` from partition tuples; call `compute_elcp_reservation_candidate_cells` with a `probe.path` containing extra interior cells; assert interior ∉ result. Complete the `...` body before marking done.

- [ ] **Step 2: Implement `compute_elcp_reservation_candidate_cells`**

Add to `reservation_overlap_policy.py` (imports from `incremental_commit` for `_route_cells_with_required_output_stub`, `_augment_route_cells_with_output_spine`):

```python
def compute_elcp_reservation_candidate_cells(
    *,
    candidate: BundleCandidate,
    inp: OptimizationInput,
    domain: RouteCellDomain,
    branch_cells: tuple[Coord, ...],
    new_trunk_cells: tuple[Coord, ...],
    reused_trunk_cells: tuple[Coord, ...],
    shareable_at_commit: frozenset[Coord],
    committed_route_cells: frozenset[Coord],
) -> frozenset[Coord] | None:
    """F0 §4 steps 2–5. Returns None when FL-06 rejects stub alignment."""

    base = build_elcp_base_cells(
        branch_cells=branch_cells,
        new_trunk_cells=new_trunk_cells,
        reused_trunk_cells=reused_trunk_cells,
    )
    stub_aligned = _route_cells_with_required_output_stub(
        candidate, base, domain, inp
    )
    if stub_aligned is None:
        return None
    fl06_required = frozenset(stub_aligned - base)
    augmented = _augment_route_cells_with_output_spine(
        candidate,
        base,
        domain,
        committed_route_cells=committed_route_cells,
        shareable_trunk_cells=shareable_at_commit,
    )
    spine_delta = frozenset(augmented - base)
    return build_reservation_candidate_cells(
        stub_aligned_cells=stub_aligned,
        spine_delta_cells=spine_delta,
        shareable_trunk_cells=shareable_at_commit,
        fl06_required_cells=fl06_required | frozenset(stub_aligned),
    )
```

- [ ] **Step 3: Run unit tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_reservation_overlap_policy.py -v`  
Expected: PASS

---

### Task 4: Wire F1a into `_attempt_commit_one` + ELCP loop (overlap input only)

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_commit.py`

- [ ] **Step 1: Extend `_attempt_commit_one` signature**

Add optional keyword-only parameters:

```python
overlap_reservation_cells: frozenset[Coord] | None = None,
```

After `route_cells = merged_route_cells` (FL-06), before private overlap:

```python
cells_for_overlap = (
    overlap_reservation_cells
    if overlap_reservation_cells is not None
    else route_cells
)
private_overlap = _private_route_cell_overlap(
    cells_for_overlap,
    committed_route_cells,
    shareable_trunk_cells=resolved_shareable,
)
```

Docstring note: F1a transitional — `route_cells` return unchanged for committed growth until F1b.

- [ ] **Step 2: Wire ELCP block in `incremental_commit` (~L578–621)**

Replace:

```python
lane_shareable = frozenset(trunk_row_pre.trunk_cells) | frozenset(tm_new_trunk)
```

With:

```python
from django_apps.asteroid_lab.optimization.commit.exterior_lane_trunk import (
    shareable_trunk_cells_for_transport,
)
from django_apps.asteroid_lab.optimization.commit.reservation_overlap_policy import (
    compute_elcp_reservation_candidate_cells,
)

shareable_at_commit = shareable_trunk_cells_for_transport(
    trunk_states_elcp,
    transport_kind=candidate.transport_kind,
    prospective_new_trunk=frozenset(tm_new_trunk),
)
current_domain_pre = _rebuild_domain(
    skeleton, inp,
    committed_occupied=committed_occupied,
    committed_route_cells=committed_route_cells,
)
reservation_candidate_cells = compute_elcp_reservation_candidate_cells(
    candidate=candidate,
    inp=inp,
    domain=current_domain_pre,
    branch_cells=tm_branch,
    new_trunk_cells=tm_new_trunk,
    reused_trunk_cells=tm_reused,
    shareable_at_commit=shareable_at_commit,
    committed_route_cells=committed_route_cells,
)
if reservation_candidate_cells is None:
    conflicts.append(CommitConflict(..., OUTPUT_STUB_NOT_RESERVED))
    continue
```

Pass into `_attempt_commit_one`:

```python
shareable_trunk_cells=shareable_at_commit,
overlap_reservation_cells=reservation_candidate_cells,
```

Remove assignment to `lane_shareable` or alias `lane_shareable = shareable_at_commit` for spine augment inside `_attempt_commit_one` path (precomputed branch still uses `route_delta` for probe cells).

- [ ] **Step 3: Run Tier S safety suite**

Run: `python -m pytest tests/unit/asteroid_lab/test_rttp_route_spine_trunk_sharing.py -v`  
Expected: PASS (all four tests)

- [ ] **Step 4: Run narrow overlap unit**

Run: `python -m pytest tests/unit/asteroid_lab/test_reservation_overlap_policy.py tests/unit/asteroid_lab/test_exterior_lane_trunk.py -v`

- [ ] **Step 5: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/optimization/commit/incremental_commit.py django_apps/asteroid_lab/optimization/commit/reservation_overlap_policy.py`

- [ ] **Step 6: Commit F1a** (only when user requests)

```bash
git add django_apps/asteroid_lab/optimization/commit/ tests/unit/asteroid_lab/
git commit -m "feat(commit): F1a ELCP shareable union and reservation overlap input"
```

---

## Phase F1b — Committed route delta alignment

### Task 5: `committed_route_cells |= ReservationCandidateCells` on ELCP success

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_commit.py`
- Modify: `tests/unit/asteroid_lab/test_reservation_overlap_policy.py` (or new integration test)

- [ ] **Step 1: Return reservation delta from `_attempt_commit_one`**

Extend `CommitAttemptOutcome`:

```python
@dataclass(frozen=True, slots=True)
class CommitAttemptOutcome:
    committed: bool
    route_cells: frozenset[Coord] = frozenset()
    route_probe: RouteProbeResult | None = None
    conflict: CommitConflict | None = None
    committed_route_delta: frozenset[Coord] = frozenset()  # F1b: ELCP reservation cells committed
```

On success when `overlap_reservation_cells is not None`:

```python
return CommitAttemptOutcome(
    committed=True,
    route_cells=route_cells,
    route_probe=probe,
    committed_route_delta=overlap_reservation_cells,
)
```

Non-ELCP success: `committed_route_delta=route_cells` (preserve legacy growth).

- [ ] **Step 2: Update success path in `incremental_commit`**

Replace:

```python
committed_route_cells = frozenset(committed_route_cells | route_cells)
```

With:

```python
delta = (
    outcome.committed_route_delta
    if outcome.committed_route_delta
    else route_cells
)
committed_route_cells = frozenset(committed_route_cells | delta)
```

- [ ] **Step 3: Add unit test C3 reused trunk**

```python
def test_reused_trunk_overlap_empty_when_not_in_reservation_candidate() -> None:
    shareable = frozenset({(1, 0), (2, 0)})
    committed = frozenset({(1, 0), (2, 0)})
    reservation = frozenset({(0, 1)})  # branch only, no reused
    assert _private_route_cell_overlap(reservation, committed, shareable_trunk_cells=shareable) == frozenset()
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_reservation_overlap_policy.py tests/unit/asteroid_lab/test_rttp_route_spine_trunk_sharing.py -v`  
Expected: PASS

- [ ] **Step 5: Commit F1b** (only when user requests)

```bash
git commit -m "feat(commit): F1b ELCP committed_route_cells delta growth"
```

---

## Phase F1c — E0 harness replay + Gate A G1 measurement

### Task 6: G1 frozen bounds + harness replay under F0 contract

**Files:**
- Create: `tests/support/rttp_f1_gate_a_g1_bounds.py`
- Modify: `harness/investigation/rttp_elcp_e0_reservation_mechanism.py`

- [ ] **Step 1: Add G1 constants**

```python
"""Gate A G1 bounds for P1-ELCP-RF-F1 (investigation assertions only)."""

E0_PRIVATE_ROUTE_OVERLAP_MECHANISM_BASELINE = 23
F1_G1_MAX_PRIVATE_ROUTE_OVERLAP_ROWS = 11  # floor(23 * 0.5) — ≥50% reduction

__all__ = [
    "E0_PRIVATE_ROUTE_OVERLAP_MECHANISM_BASELINE",
    "F1_G1_MAX_PRIVATE_ROUTE_OVERLAP_ROWS",
]
```

- [ ] **Step 2: Update `_mechanism_signals_from_route_bundle` / replay**

Import and call `compute_elcp_reservation_candidate_cells` + `shareable_trunk_cells_for_transport` instead of ad-hoc `lane_shareable` + full merged route for `private_overlap_cells` classification.

Ensure `ElcpE0MechanismClass.private_route_overlap` uses:

```python
private_overlap = _private_route_cell_overlap(
    reservation_candidate_cells,
    committed_route_cells,
    shareable_trunk_cells=shareable_at_commit,
)
```

- [ ] **Step 3: Run E0 unit harness tests**

Run: `python -m pytest tests/unit/harness/test_rttp_elcp_e0_reservation_mechanism.py -v`  
Expected: PASS (update expectations if classifier ordering changes)

- [ ] **Step 4: Ruff harness**

Run: `python -m ruff check harness/investigation/rttp_elcp_e0_reservation_mechanism.py tests/support/rttp_f1_gate_a_g1_bounds.py`

---

### Task 7: Gate A G1 investigation test + F1 report

**Files:**
- Create: `tests/investigation/test_rttp_elcp_rf_f1_reservation_policy_gate_a.py`
- Create: `docs/superpowers/reports/2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy-report.md`

- [ ] **Step 1: Write investigation test**

```python
"""P1-ELCP-RF-F1: Gate A measurable G1 on E0 stale universe (overlap-pack)."""

from __future__ import annotations

import pytest

from harness.investigation.rttp_elcp_e0_reservation_mechanism import (
    ElcpE0MechanismClass,
    run_gate_a_elcp_e0_reservation_forensics,
)
from tests.support.rttp_e0_gate_a_frozen_bounds import EXPECTED_OVERLAP_STALE_ROW_COUNT
from tests.support.rttp_f1_gate_a_g1_bounds import (
    E0_PRIVATE_ROUTE_OVERLAP_MECHANISM_BASELINE,
    F1_G1_MAX_PRIVATE_ROUTE_OVERLAP_ROWS,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_f1_private_route_overlap_mechanism_g1(
    imported_game_data_batch_module: object,
) -> None:
    result = run_gate_a_elcp_e0_reservation_forensics(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )
    assert len(result.rows) == EXPECTED_OVERLAP_STALE_ROW_COUNT
    private_count = sum(
        1
        for r in result.rows
        if r.elcp_e0_mechanism_class == ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP
    )
    print(f"F1_G1_PRIVATE_ROUTE_OVERLAP_COUNT={private_count}")
    print(f"F1_G1_BASELINE={E0_PRIVATE_ROUTE_OVERLAP_MECHANISM_BASELINE}")
    assert private_count <= F1_G1_MAX_PRIVATE_ROUTE_OVERLAP_ROWS
```

- [ ] **Step 2: Run G1 test (may FAIL until policy sufficient)**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_f1_reservation_policy_gate_a.py::test_gate_a_f1_private_route_overlap_mechanism_g1 -v`  
Expected after full F1: PASS with `private_count <= 11`. If FAIL after F1a only, complete F1b and re-run.

- [ ] **Step 3: Run D0 + E0 regression**

Run: `python -m pytest tests/investigation/test_rttp_elcp_rf_d0_stale_attribution.py::test_gate_a_elcp_d0_overlap_stale_attribution tests/investigation/test_rttp_elcp_rf_e0_reservation_mechanism.py::test_gate_a_elcp_e0_overlap_reservation_mechanism -v`  
Expected: PASS

- [ ] **Step 4: Publish F1 report** with §1 F0 carry-forward, §2 G1 before/after histogram, §3 Tier S confirmation, git SHA.

- [ ] **Step 5: Mark current_plan F1 CLOSED**; P1-ELCP-RF remains REOPENED (inlet subtrack / parent).

---

### Task 8: Full gate (PR-ready)

- [ ] **Step 1: Tier S full**

Run: `python -m pytest tests/unit/asteroid_lab/test_rttp_route_spine_trunk_sharing.py tests/unit/asteroid_lab/test_reservation_overlap_policy.py tests/unit/asteroid_lab/test_exterior_lane_trunk.py -v`

- [ ] **Step 2: Ruff + mypy (commit paths)**

Run: `python -m ruff check django_apps/asteroid_lab/optimization/commit/ harness/investigation/rttp_elcp_e0_reservation_mechanism.py tests/unit/asteroid_lab/test_reservation_overlap_policy.py`  
Run: `python -m mypy django_apps/asteroid_lab/optimization/commit/incremental_commit.py django_apps/asteroid_lab/optimization/commit/reservation_overlap_policy.py django_apps/asteroid_lab/optimization/commit/exterior_lane_trunk.py`

- [ ] **Step 3: Optional full pytest** per AGENTS PR checklist when user requests PR.

---

## Plan self-review

| Check | Result |
|-------|--------|
| §3.1 shareable + prospective | Task 1, 4 |
| §3.2 no full probe path | Tasks 2–3 |
| §3.3 overlap predicate | Tasks 3–4 |
| §4.1 pipeline order | Tasks 2–4 |
| §4.2 SPINE-G | Task 2 |
| §5 invariants | Tasks 4–5, 7 |
| §6 F1a/b/c | Tasks 4, 5, 6–7 |
| §7 Tier S/C/G | Tasks 4–7 |
| Placeholder scan | Task 3 Step 1 has implementer note to complete narrow-corridor body — **must be filled before Task 3 done** |
| F1a transitional documented | Plan header + Task 4 |

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-27-rttp-elcp-rf-f1-private-route-overlap-reservation-policy.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with checkpoints  

Which approach do you want?
