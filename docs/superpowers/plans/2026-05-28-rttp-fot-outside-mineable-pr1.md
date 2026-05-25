# RTTP FOT Outside-Mineable — PR-1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject catalog-native RTTP candidates whose fixed output transport (FOT) falls on `mineable_cells`, and enforce the same invariant at commit-time and read-only validation so Lab replay and committed layouts show zero field FOT cells.

**Architecture:** Add `FixedOutputTransportPolicy` (PR-1 default `OUTSIDE_MINEABLE`) and extend `_validate_geometry` in `candidate_generator.py` to reject before `probe_route`. Defense in depth: `attempt_commit_candidate` + `validate_final_layout` use `fixed_output_transport_cell()` (not `output_stub`). Replay rejected overlay carries `rejection_reason` enum value. PR-2 outward filter is **out of scope**.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy (`django_apps config src`)

**Spec:** [`docs/superpowers/specs/2026-05-28-rttp-fixed-output-transport-outside-mineable-design.md`](../specs/2026-05-28-rttp-fixed-output-transport-outside-mineable-design.md)

**Branch:** `feat/rttp-fot-outside-mineable-pr1`

**Work classification:** contract change · implementation change

**Must NOT modify:** `incremental_commit.py` route probe algorithm core, selection/regret scoring, `game_data` importers, PR-2 `outward_dirs` module.

**Coordinate reminder:** FOT = `anchor + fixed_output_transport_offset` (1 step). Route probe start = `output_stub` (2 steps). Do not conflate.

---

## File map

| Action | Path |
|--------|------|
| Modify | `django_apps/asteroid_lab/optimization/candidates/candidate_dtos.py` |
| Modify | `django_apps/asteroid_lab/optimization/candidates/candidate_generator.py` |
| Modify | `django_apps/asteroid_lab/optimization/candidates/__init__.py` |
| Modify | `django_apps/asteroid_lab/optimization/commit/incremental_commit.py` |
| Modify | `django_apps/asteroid_lab/optimization/validation/final_validation.py` |
| Modify | `django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py` |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_entry.py` |
| Create | `tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py` |
| Modify | `tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py` |
| Modify | `tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py` |
| Modify | `tests/unit/asteroid_lab/test_placement_overlay_projection.py` |
| Modify | `documents/ai/current_plan.md` (queue row only) |

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Create branch**

```powershell
Set-Location F:\Python_Projects\shapez2Factory
git checkout master
git pull
git checkout -b feat/rttp-fot-outside-mineable-pr1
```

- [ ] **Step 2: Baseline narrow gate (pre-edit)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_candidate_generator.py tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py tests/unit/asteroid_lab/test_rttp_commit.py tests/unit/asteroid_lab/test_placement_overlay_projection.py -v --tb=short
```

Expected: PASS (records pre-change behavior).

---

### Task 1: Policy + reject enums

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/candidates/candidate_dtos.py`
- Modify: `django_apps/asteroid_lab/optimization/candidates/__init__.py`
- Create: `tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py`

- [ ] **Step 1: Write failing enum tests**

Create `tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py`:

```python
"""PR-1: FOT must not lie on mineable_cells (INV-FOT-01)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    CandidateRejectReason,
    FixedOutputTransportPolicy,
)


def test_fixed_output_transport_policy_enum_values() -> None:
    assert FixedOutputTransportPolicy.ALLOW.value == "allow"
    assert FixedOutputTransportPolicy.OUTSIDE_MINEABLE.value == "outside_mineable"
    assert FixedOutputTransportPolicy.OUTWARD_FROM_RIM.value == "outward_from_rim"


def test_candidate_reject_reason_fot_inside_mineable_exists() -> None:
    assert (
        CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE.value
        == "fixed_output_transport_inside_mineable"
    )


def test_candidate_reject_reason_fot_kind_blocked_exists() -> None:
    assert (
        CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_KIND_BLOCKED.value
        == "fixed_output_transport_kind_blocked"
    )
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py::test_fixed_output_transport_policy_enum_values -v --tb=short
```

Expected: FAIL (`FixedOutputTransportPolicy` not defined).

- [ ] **Step 3: Implement enums**

In `candidate_dtos.py`, add after `ExtractorPlacementPolicy`:

```python
class FixedOutputTransportPolicy(StrEnum):
    ALLOW = "allow"
    PENALIZE_FIELD_USAGE = "penalize_field_usage"
    OUTSIDE_MINEABLE = "outside_mineable"
    OUTWARD_FROM_RIM = "outward_from_rim"
```

Extend `CandidateRejectReason`:

```python
    FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE = "fixed_output_transport_inside_mineable"
    FIXED_OUTPUT_TRANSPORT_KIND_BLOCKED = "fixed_output_transport_kind_blocked"
    # PR-2 only (add member now; generator ignores until PR-2):
    OUTPUT_DIR_NOT_OUTWARD_FROM_RIM = "output_dir_not_outward_from_rim"
    FIXED_OUTPUT_TRANSPORT_NOT_IN_ROUTE_DOMAIN = "fixed_output_transport_not_in_route_domain"
```

Export in `candidates/__init__.py` `__all__`.

- [ ] **Step 4: Run enum tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py -k "policy_enum or reject_reason" -v --tb=short
```

- [ ] **Step 5: Commit** (only if user requested commit)

```powershell
git add django_apps/asteroid_lab/optimization/candidates/candidate_dtos.py django_apps/asteroid_lab/optimization/candidates/__init__.py tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py
git commit -m "feat(asteroid_lab): add FOT policy and reject reason enums"
```

---

### Task 2: Candidate generator geometry reject

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/candidates/candidate_generator.py`
- Modify: `tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py`

- [ ] **Step 1: Write failing generator tests**

Append to `test_fot_outside_mineable_pr1.py`:

```python
from dataclasses import replace

from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from tests.unit.asteroid_lab.conftest import _external_margin_goals, _external_void_ring, _perimeter_cells


def _west_rim_greenfield() -> OptimizationInput:
    """4×4 mineable block; only west-rim anchor (5,5) for directional tests."""
    mineable = frozenset((x, y) for x in range(5, 9) for y in range(5, 9))
    rim = frozenset({(5, 5)})
    inner = mineable - rim
    external_void = _external_void_ring(mineable)
    from tests.support.catalog_test_fixtures import build_minimal_test_catalog_slice

    return OptimizationInput(
        mineable_cells=mineable,
        rim_cells=rim,
        inner_cells=inner,
        external_void_cells=external_void,
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        transport_kind=TransportKind.SHAPE_BELT,
        route_goals=_external_margin_goals(_perimeter_cells(mineable), external_void),
        existing_transport_cells=frozenset(),
        catalog_slice=build_minimal_test_catalog_slice(),
    )


def test_candidate_rejects_fixed_output_transport_inside_mineable() -> None:
    inp = _west_rim_greenfield()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(
        inp,
        skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    assert not any(
        fixed_output_transport_cell(c) in inp.mineable_cells for c in result.normal_candidates
    )
    assert any(
        r.rejection_reason
        is CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE
        for r in result.rejected_candidates
    )


def test_candidate_allow_policy_may_admit_mineable_fot_for_diagnostic() -> None:
    inp = _west_rim_greenfield()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    strict = generate_candidates(
        inp,
        skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    loose = generate_candidates(
        inp,
        skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.ALLOW,
    )
    assert len(loose.normal_candidates) >= len(strict.normal_candidates)
```

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py::test_candidate_rejects_fixed_output_transport_inside_mineable -v --tb=short
```

Expected: FAIL (no `fixed_output_transport_policy` kwarg or no rejects).

- [ ] **Step 3: Implement generator changes**

In `candidate_generator.py`:

1. Import `FixedOutputTransportPolicy` and new reject reasons.

2. Add helper:

```python
def _policy_requires_outside_mineable(policy: FixedOutputTransportPolicy) -> bool:
    return policy in (
        FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
        FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
    )
```

3. Extend `_validate_geometry` signature with `fot_abs: Coord` and `policy: FixedOutputTransportPolicy`:

```python
    if fot_abs in inp.blocked_incompatible_transport_cells:
        return CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_KIND_BLOCKED
    if _policy_requires_outside_mineable(policy) and fot_abs in inp.mineable_cells:
        return CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE
```

Keep existing `fot_abs in occupied` → `FIXED_OUTPUT_TRANSPORT_IN_OCCUPIED` (compute `fot_abs` before call).

4. `generate_candidates(..., fixed_output_transport_policy: FixedOutputTransportPolicy = FixedOutputTransportPolicy.OUTSIDE_MINEABLE)`:

```python
            fot_abs = _translate_offset(anchor, spec.fixed_output_transport_offset)
            geometry_reason = _validate_geometry(
                inp, spec, anchor, occupied, output_stub, fot_abs=fot_abs, policy=policy
            )
```

- [ ] **Step 4: Run generator tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py -v --tb=short
```

- [ ] **Step 5: Strengthen catalog-native test**

In `test_catalog_native_candidate_generator.py`, add to `test_normal_candidate_has_empty_extensions_and_fot_not_occupied`:

```python
    assert fot not in inp.mineable_cells
```

(loop all normal candidates or use first + parametrize if needed).

- [ ] **Step 6: Run catalog + candidate tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py -v --tb=short
```

- [ ] **Step 7: ruff**

```powershell
python -m ruff check django_apps/asteroid_lab/optimization/candidates/
```

---

### Task 3: Commit-time defense (INV-FOT-01)

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_commit.py`
- Modify: `tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py`

- [ ] **Step 1: Write failing commit test**

Append:

```python
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome


def test_incremental_commit_never_confirms_candidate_with_mineable_fot(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.ALLOW,
    )
    bad = next(
        c
        for c in generation.normal_candidates
        if fixed_output_transport_cell(c) in inp.mineable_cells
    )
    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=(bad.candidate_id,)),
        {bad.candidate_id: bad},
        inp,
        skeleton,
        domain=domain,
    )
    assert bad.candidate_id not in result.committed_ids
    assert any(
        c.reason is CommitConflictReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE
        for c in result.conflicts
    )
```

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py::test_incremental_commit_never_confirms_candidate_with_mineable_fot -v --tb=short
```

- [ ] **Step 3: Add `CommitConflictReason` + early return**

In `incremental_commit.py`:

```python
class CommitConflictReason(StrEnum):
    ...
    FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE = "fixed_output_transport_inside_mineable"
```

In `attempt_commit_candidate`, after FOT/occupied cross checks, before `probe_route`:

```python
    if fot_cell in inp.mineable_cells:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE,
            ),
        )
```

- [ ] **Step 4: Run commit test — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py::test_incremental_commit_never_confirms_candidate_with_mineable_fot -v --tb=short
```

---

### Task 4: Read-only validation

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/validation/final_validation.py`
- Modify: `tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py`

- [ ] **Step 1: Write failing validation test**

Use `greenfield_with_catalog` + `_pick_committable` pattern from `test_rttp_commit.py`, or build one committed candidate under `OUTSIDE_MINEABLE` and assert `validate_final_layout` True; then synthetic bad candidate dict with mineable FOT → False.

Minimal:

```python
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)


def test_validation_fails_confirmed_candidate_with_mineable_fot(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(inp, skeleton)
    assert generation.normal_candidates
    cand = generation.normal_candidates[0]
    assert fixed_output_transport_cell(cand) not in inp.mineable_cells
    by_id = {cand.candidate_id: cand}
    assert validate_final_layout((cand.candidate_id,), frozenset(), by_id, inp)

    bad_fot = next(iter(inp.mineable_cells - cand.occupied_cells))
    # Mutate: replace pattern offsets so FOT lands on mineable (test-only factory)
    # Prefer tests.support factory if added; else skip with documented BundleCandidate clone.
```

**Implementation note:** If mutating `BundleCandidate` is awkward, add `tests/support/fot_test_fixtures.py` with `bundle_candidate_with_fot_at(coord)` using `build_pattern_library` lin pattern — keep test file under 40 lines.

- [ ] **Step 2: Extend `validate_final_layout` loop**

```python
        fot_cell = fixed_output_transport_cell(candidate)
        if fot_cell in inp.mineable_cells:
            return False
```

- [ ] **Step 3: Run validation test — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py -k validation -v --tb=short
```

---

### Task 5: Replay reject reason + overlay acceptance

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py`
- Modify: `tests/unit/asteroid_lab/test_placement_overlay_projection.py`

- [ ] **Step 1: Write failing replay test**

In `test_rttp_replay_diagnostics.py`:

```python
def test_replay_marks_rejected_candidate_fot_inside_mineable() -> None:
    rejected = (
        RejectedBundleCandidate(
            candidate_id="5,5:cat_x:shape_belt",
            anchor_coord=(5, 5),
            pattern_id="cat_test",
            rejection_reason=CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE,
            route_probe_cost=None,
        ),
    )
    payload = build_candidates_replay_payload(
        CandidateGenerationResult(normal_candidates=(), rejected_candidates=rejected),
    )
    cell = next(c for c in payload.cell_overlay_json["cells"] if c.get("x") == 5)
    assert cell.get("rejection_reason") == "fixed_output_transport_inside_mineable"
```

- [ ] **Step 2: Implement replay field**

In `build_candidates_replay_payload`, rejected cell dict:

```python
                "rejection_reason": rej.rejection_reason.value,
```

- [ ] **Step 3: Overlay test — zero confirmed mineable FOT**

In `test_placement_overlay_projection.py`, after `build_confirmed_placement_overlay_rows` on normal candidates from greenfield:

```python
    for row in merged:
        if "fixed_output_transport" not in str(row.get("overlay_semantic_kind", "")):
            continue
        coord = (int(row["x"]), int(row["y"]))
        assert coord not in inp.mineable_cells
```

- [ ] **Step 4: Run replay + overlay tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py tests/unit/asteroid_lab/test_placement_overlay_projection.py -v --tb=short
```

---

### Task 6: Solver runtime default policy

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`

- [ ] **Step 1: Thread policy into `generate_candidates` call sites**

Import `FixedOutputTransportPolicy`. Where `generate_candidates` is invoked for production RTTP (same path as `ExtractorPlacementPolicy.INTERIOR_AND_RIM`), add:

```python
fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
```

Do not change `ExtractorPlacementPolicy` default in PR-1 (PR-2 may revisit).

- [ ] **Step 2: Smoke**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py tests/unit/asteroid_lab/test_rttp_reconstruction_fixture_e2e.py -v --tb=short
```

---

### Task 7: Gate + docs queue

**Files:**
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Narrow gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py tests/unit/asteroid_lab/test_rttp_candidate_generator.py tests/unit/asteroid_lab/test_rttp_commit.py tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py tests/unit/asteroid_lab/test_placement_overlay_projection.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/optimization/candidates django_apps/asteroid_lab/optimization/commit/incremental_commit.py django_apps/asteroid_lab/optimization/validation/final_validation.py django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py django_apps/asteroid_lab/services/solver_runtime_entry.py
python -m mypy django_apps/asteroid_lab/optimization/candidates django_apps/asteroid_lab/optimization/commit django_apps/asteroid_lab/optimization/validation
```

Expected: PASS.

- [ ] **Step 2: Add ACTIVE queue row** in `current_plan.md` (one bullet: PR-1 FOT outside mineable, link spec+plan).

- [ ] **Step 3: User-requested commit only**

---

## Subagent-Driven execution map

| Subagent | Tasks | Gate after |
|----------|-------|------------|
| Contract | Task 1 | enum tests green |
| Generator | Task 2 | `test_fot_outside_mineable_pr1` generator tests green |
| Commit/validation | Task 3–4 | commit + validation tests green |
| Replay/runtime | Task 5–6 | replay/overlay/pipeline smoke green |
| Close | Task 7 | narrow pytest + ruff + mypy |

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| INV-FOT-01 normal pool | Task 2 |
| `FIXED_OUTPUT_TRANSPORT_KIND_BLOCKED` | Task 2 |
| Commit defense | Task 3 |
| Validation read-only fail | Task 4 |
| Replay reject reason | Task 5 |
| Overlay zero mineable FOT | Task 5 |
| Default `OUTSIDE_MINEABLE` runtime | Task 6 |
| PR-2 outward / PR-3 ring | **Excluded** |
| `output_stub` probe unchanged | Task 2 (no probe start edit) |

Placeholder scan: none.

---

## PR-2 / PR-3 follow-up plans (not this file)

- `2026-05-28-rttp-fot-outward-from-rim-pr2.md` (to be written after PR-1 merge)
- `2026-05-28-rttp-fot-ring-alignment-pr3.md` (scoring only)
