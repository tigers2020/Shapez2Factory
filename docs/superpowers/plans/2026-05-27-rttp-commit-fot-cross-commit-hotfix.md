# RTTP Commit FOT Cross-Commit Hotfix (PR1.5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reserve each confirmed extractor's `fixed_output_transport` cell across incremental commit so a later extractor cannot anchor on that cell (Lab regression: N@`(-1,-9)` FOT `(-1,-10)` blocked by W@`(-1,-10)`).

**Architecture:** `extractor occupied cell != fixed_output_transport cell`. Per-candidate Phase 1 `INV-R-*` is insufficient; add `CommitDomainState.committed_fixed_output_transport_cells`, bidirectional checks in `incremental_commit`, read-only detection in `validate_final_layout`, and optional selection pre-filter in greedy regret. Do **not** merge FOT into `reserved_route_cells`. Authority: [`docs/superpowers/specs/2026-05-27-rttp-commit-fot-cross-commit-hotfix.md`](../specs/2026-05-27-rttp-commit-fot-cross-commit-hotfix.md).

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy (`django_apps config src`)

**Branch:** `feat/rttp-miner-output-transport-topology-pr1` or `feat/rttp-commit-fot-cross-commit-pr15`

**Work classification:** contract change · regression fix (Commit Path B)

**Must NOT modify:** route probe core, `game_data` importers, `exhaustive_generator.py` production imports, Phase 1 `miner_placement_topology` rules (unless fixing unrelated bugs).

**Implementation status (2026-05-27):** Core commit/validation/selection/deferred/macro paths and `test_rttp_commit_fot_conflict.py` may already be landed locally. Use this plan as **verification + gap closure** (selection tests, runtime doc footnote, Lab acceptance). Do not skip failing steps if files differ from spec.

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `django_apps/asteroid_lab/optimization/candidates/placement_cells.py` | `fixed_output_transport_cell` — projected pattern only |
| Modify | `django_apps/asteroid_lab/optimization/commit/incremental_commit.py` | FOT state + `FIXED_OUTPUT_TRANSPORT_CONFLICT` |
| Modify | `django_apps/asteroid_lab/optimization/validation/final_validation.py` | INV-VALIDATION-FOT-01 |
| Modify | `django_apps/asteroid_lab/optimization/commit/deferred_retry_execute.py` | Rebuild FOT set after primary |
| Modify | `django_apps/asteroid_lab/optimization/commit/incremental_macro_commit.py` | Propagate FOT on macro child commits |
| Modify | `django_apps/asteroid_lab/optimization/selection/greedy_regret.py` | `_fot_conflict` pool filter |
| Modify | `django_apps/asteroid_lab/optimization/selection/macro_greedy_regret.py` | Per-child FOT filter |
| Create | `tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py` | N→W / W→N commit + validation |
| Create | `tests/unit/asteroid_lab/test_rttp_selection_fot_prefilter.py` | Selection omits FOT-conflicting pair |
| Modify | `tests/unit/asteroid_lab/test_rttp_commit.py` | `_pick_committable_candidates` tracks FOT |
| Modify | `documents/Algorithm/asteroid_lab_07_incremental_commit.md` | `CommitConflictReason` + domain field footnote |
| Spec (done) | `docs/superpowers/specs/2026-05-27-rttp-commit-fot-cross-commit-hotfix.md` | Contract authority |

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Checkout branch**

```powershell
Set-Location F:\Python_Projects\shapez2Factory
git checkout feat/rttp-miner-output-transport-topology-pr1
# or: git checkout -b feat/rttp-commit-fot-cross-commit-pr15
```

- [ ] **Step 2: Confirm regression exists on base (optional)**

If FOT fix not yet applied, `test_n_miner_fot_blocked_by_later_w_extractor_at_same_cell` should FAIL. After full plan, it must PASS.

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py::test_n_miner_fot_blocked_by_later_w_extractor_at_same_cell -v
```

Expected after fix: PASS

---

### Task 1: FOT coordinate helper

**Files:**
- Create: `django_apps/asteroid_lab/optimization/candidates/placement_cells.py`
- Test: `tests/unit/asteroid_lab/test_placement_cells.py` (inline in Task 2 module or separate)

- [ ] **Step 1: Write helper module**

```python
"""Absolute placement cells derived from bundle pattern + anchor."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord


def fixed_output_transport_cell(candidate: BundleCandidate) -> Coord:
    """Absolute FOT from projected ``BundlePattern`` only (PR1.5).

    No rotation re-derivation or catalog fallback in commit/validation paths.
    """
    offset = candidate.pattern.fixed_output_transport_offset
    anchor = candidate.anchor_coord
    return (anchor[0] + offset[0], anchor[1] + offset[1])


__all__ = ["fixed_output_transport_cell"]
```

- [ ] **Step 2: Run import smoke**

```powershell
python -c "from django_apps.asteroid_lab.optimization.candidates.placement_cells import fixed_output_transport_cell; print(fixed_output_transport_cell)"
```

Expected: no ImportError

- [ ] **Step 3: Commit** (when user requests commit)

```bash
git add django_apps/asteroid_lab/optimization/candidates/placement_cells.py
git commit -m "feat(asteroid_lab): add fixed_output_transport_cell helper"
```

---

### Task 2: Commit domain state and bidirectional gate

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_commit.py`
- Create: `tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py`

- [ ] **Step 1: Write failing tests (N→W and W→N)**

Create `tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py` with shared factories:

```python
"""Cross-commit: extractor must not occupy a prior commit's fixed_output_transport cell."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.catalog_placement import CatalogPlacementRef
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput, TransportKind
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import (
    RttpSkeletonBuilder,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)


def _pattern(
    *,
    pattern_id: str,
    output_dir: str,
    fot: Coord,
    stub: Coord,
) -> BundlePattern:
    return BundlePattern(
        pattern_id=pattern_id,
        extension_count=0,
        occupied_offsets=frozenset({(0, 0)}),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_dir=output_dir,
        fixed_output_transport_offset=fot,
        output_stub_offset=stub,
        throughput_factor=4,
        topology_kind="test",
    )


def _candidate(candidate_id: str, anchor: Coord, pattern: BundlePattern) -> BundleCandidate:
    occupied = frozenset({anchor})
    stub = (
        anchor[0] + pattern.output_stub_offset[0],
        anchor[1] + pattern.output_stub_offset[1],
    )
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=4,
        route_probe_cost=1,
        reachable=True,
        catalog_placement_ref=CatalogPlacementRef("test", anchor, pattern.output_dir),
    )


def test_n_miner_fot_blocked_by_later_w_extractor_at_same_cell(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    """Lab (-1,-9)/(-1,-10) geometry on greenfield mineable (6,7)/(6,6)."""
    n_pattern = _pattern(pattern_id="n", output_dir="N", fot=(0, -1), stub=(0, -2))
    w_pattern = _pattern(pattern_id="w", output_dir="W", fot=(-1, 0), stub=(-2, 0))
    n_anchor: Coord = (6, 7)
    w_anchor: Coord = (6, 6)
    n_cand = _candidate("n:6,7", n_anchor, n_pattern)
    w_cand = _candidate("w:6,6", w_anchor, w_pattern)
    assert fixed_output_transport_cell(n_cand) == w_anchor

    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = incremental_commit(
        PlacementGenome(commit_order=(n_cand.candidate_id, w_cand.candidate_id)),
        {n_cand.candidate_id: n_cand, w_cand.candidate_id: w_cand},
        inp,
        skeleton,
        domain=initial_commit_domain(skeleton, inp),
    )
    assert n_cand.candidate_id in result.committed_ids
    assert w_cand.candidate_id not in result.committed_ids
    assert any(
        c.candidate_id == w_cand.candidate_id
        and c.reason is CommitConflictReason.FIXED_OUTPUT_TRANSPORT_CONFLICT
        for c in result.conflicts
    )


def test_w_miner_first_blocks_n_fot_on_same_cell(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    n_pattern = _pattern(pattern_id="n", output_dir="N", fot=(0, -1), stub=(0, -2))
    w_pattern = _pattern(pattern_id="w", output_dir="W", fot=(-1, 0), stub=(-2, 0))
    n_cand = _candidate("n:6,7", (6, 7), n_pattern)
    w_cand = _candidate("w:6,6", (6, 6), w_pattern)
    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = incremental_commit(
        PlacementGenome(commit_order=(w_cand.candidate_id, n_cand.candidate_id)),
        {n_cand.candidate_id: n_cand, w_cand.candidate_id: w_cand},
        inp,
        skeleton,
        domain=initial_commit_domain(skeleton, inp),
    )
    assert w_cand.candidate_id in result.committed_ids
    assert n_cand.candidate_id not in result.committed_ids
    assert any(
        c.candidate_id == n_cand.candidate_id
        and c.reason is CommitConflictReason.FIXED_OUTPUT_TRANSPORT_CONFLICT
        for c in result.conflicts
    )
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py -v
```

Expected: FAIL (`FIXED_OUTPUT_TRANSPORT_CONFLICT` missing or W commits)

- [ ] **Step 3: Implement `incremental_commit.py` changes**

1. Add enum member (comment: cross-commit, not `CandidateRejectReason`):

```python
FIXED_OUTPUT_TRANSPORT_CONFLICT = "fixed_output_transport_conflict"
```

2. Append to `CommitDomainState` (**append-only** — do not reorder existing fields):

```python
committed_fixed_output_transport_cells: frozenset[Coord]
```

3. `initial_commit_domain`: `committed_fixed_output_transport_cells=frozenset()`

4. Import `fixed_output_transport_cell` from `placement_cells`.

5. In `_attempt_commit_one`, after `OVERLAP` check and **before** FOT checks, keep existing order:

```python
if candidate.output_stub in committed_route_cells:
    return ... INLET_ON_SHARED_TRANSPORT
fot_cell = fixed_output_transport_cell(candidate)
if candidate.occupied_cells & committed_fixed_output_transport_cells:
    return ... FIXED_OUTPUT_TRANSPORT_CONFLICT
if fot_cell in committed_occupied:
    return ... FIXED_OUTPUT_TRANSPORT_CONFLICT
```

6. In `incremental_commit` loop after successful commit:

```python
committed_fixed_output_transport_cells = frozenset(
    committed_fixed_output_transport_cells | {fixed_output_transport_cell(candidate)}
)
```

Pass `committed_fixed_output_transport_cells` into every `_attempt_commit_one` call.

- [ ] **Step 4: Run tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py -v
```

Expected: 2+ passed

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/optimization/commit/incremental_commit.py tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py
git commit -m "fix(asteroid_lab): reserve FOT cells across incremental commit"
```

---

### Task 3: Final validation (read-only)

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/validation/final_validation.py`
- Test: extend `tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py`

- [ ] **Step 1: Add validation test**

```python
def test_validate_final_layout_rejects_extractor_on_peer_fot(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    n_pattern = _pattern(pattern_id="n", output_dir="N", fot=(0, -1), stub=(0, -2))
    w_pattern = _pattern(pattern_id="w", output_dir="W", fot=(-1, 0), stub=(-2, 0))
    n_cand = _candidate("n", (6, 7), n_pattern)
    w_cand = _candidate("w", (6, 6), w_pattern)
    by_id = {n_cand.candidate_id: n_cand, w_cand.candidate_id: w_cand}
    assert (
        validate_final_layout(
            (n_cand.candidate_id, w_cand.candidate_id),
            frozenset(),
            by_id,
            greenfield_optimization_input,
        )
        is False
    )
```

- [ ] **Step 2: Implement loop in `validate_final_layout`**

```python
occupied_seen: set[tuple[int, int]] = set()
fot_seen: set[tuple[int, int]] = set()
for candidate_id in committed_ids:
    ...
    fot_cell = fixed_output_transport_cell(candidate)
    if fot_cell in occupied_seen or candidate.occupied_cells & frozenset(fot_seen):
        return False
    occupied_seen.update(candidate.occupied_cells)
    fot_seen.add(fot_cell)
```

Docstring: `Assert-only checks (no repair): ... INV-VALIDATION-FOT-01.`

**Do not** add FOT to `reserved_route_cells`. **Do not** implement `ValidationIssueCode` enum in this PR (spec hook `fixed_output_transport_occupied` is documentation-only until structured validation exists).

- [ ] **Step 3: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py tests/unit/asteroid_lab/test_final_validation_route_disjoint.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/optimization/validation/final_validation.py tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py
git commit -m "fix(asteroid_lab): assert FOT not occupied in final validation"
```

---

### Task 4: Deferred retry and macro commit propagation

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/deferred_retry_execute.py`
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_macro_commit.py`

- [ ] **Step 1: `deferred_retry_execute._state_after_primary`**

Rebuild FOT from primary committed candidates in commit order:

```python
fot.add(fixed_output_transport_cell(candidate))
return (frozenset(occupied), frozenset(fot), primary_commit_result.reserved_route_cells, ...)
```

Pass `committed_fixed_output_transport_cells` into `_attempt_commit_one` and `_apply_confirmed` (extend return tuple to include FOT set).

- [ ] **Step 2: `incremental_macro_commit._domain_after_single_commit`**

```python
committed_fixed_output_transport_cells = frozenset(
    domain.committed_fixed_output_transport_cells
    | {fixed_output_transport_cell(candidate)}
)
```

Include field in returned `CommitDomainState`.

- [ ] **Step 3: Run macro + deferred tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py tests/unit/asteroid_lab/test_rttp_macro_bundle_t3.py -v
```

Expected: PASS (or document known macro failures unrelated to FOT)

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/optimization/commit/deferred_retry_execute.py django_apps/asteroid_lab/optimization/commit/incremental_macro_commit.py
git commit -m "fix(asteroid_lab): propagate FOT state in deferred retry and macro commit"
```

---

### Task 5: Greedy regret selection pre-filter

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/selection/greedy_regret.py`
- Create: `tests/unit/asteroid_lab/test_rttp_selection_fot_prefilter.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_commit.py` (helper FOT tracking)

- [ ] **Step 1: Write failing selection test**

```python
"""Selection must not schedule two miners whose occupied/FOT cells cross."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.selection.greedy_regret import select_genome
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def _cand(cid: str, anchor: tuple[int, int], fot: tuple[int, int], stub: tuple[int, int]) -> BundleCandidate:
    pattern = BundlePattern(
        pattern_id="n" if fot == (0, -1) else "w",
        extension_count=0,
        occupied_offsets=frozenset({(0, 0)}),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_dir="N" if fot == (0, -1) else "W",
        fixed_output_transport_offset=fot,
        output_stub_offset=stub,
        throughput_factor=4,
        topology_kind="test",
    )
    return BundleCandidate(
        candidate_id=cid,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=frozenset({anchor}),
        output_stub=(anchor[0] + stub[0], anchor[1] + stub[1]),
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=4,
        route_probe_cost=1,
        reachable=True,
    )


def test_select_genome_excludes_fot_conflicting_second_miner(
    greenfield_optimization_input,
) -> None:
    from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import (
        RttpSkeletonBuilder,
        RttpSkeletonConfig,
    )

    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    n = _cand("n", (6, 7), (0, -1), (0, -2))
    w = _cand("w", (6, 6), (-1, 0), (-2, 0))
    assert fixed_output_transport_cell(n) == (6, 6)
    genome = select_genome((n, w), skeleton, inp, goal_count=2)
    assert genome.commit_order == (n.candidate_id,)
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_selection_fot_prefilter.py -v
```

- [ ] **Step 3: Implement `_fot_conflict` and pool filter in `greedy_regret.py`**

```python
def _fot_conflict(
    candidate: BundleCandidate,
    *,
    committed_occupied: frozenset[Coord],
    committed_fixed_output_transport_cells: frozenset[Coord],
) -> bool:
    fot_cell = fixed_output_transport_cell(candidate)
    if candidate.occupied_cells & committed_fixed_output_transport_cells:
        return True
    return fot_cell in committed_occupied
```

After each pick, `committed_fixed_output_transport_cells.add(fixed_output_transport_cell(best))` and filter pool with `_fot_conflict`.

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_selection_fot_prefilter.py tests/unit/asteroid_lab/test_rttp_greedy_regret.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/optimization/selection/greedy_regret.py tests/unit/asteroid_lab/test_rttp_selection_fot_prefilter.py
git commit -m "fix(asteroid_lab): pre-filter FOT conflicts in greedy regret selection"
```

---

### Task 6: Macro greedy regret pre-filter

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/selection/macro_greedy_regret.py`

- [ ] **Step 1: Add `_macro_fot_conflict` using `_fot_conflict` per child**

- [ ] **Step 2: Track FOT per committed child stub loop (same as occupied update)**

- [ ] **Step 3: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_macro_bundle_t3.py -v
```

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/optimization/selection/macro_greedy_regret.py
git commit -m "fix(asteroid_lab): pre-filter FOT conflicts in macro greedy selection"
```

---

### Task 7: Runtime doc footnote

**Files:**
- Modify: `documents/Algorithm/asteroid_lab_07_incremental_commit.md`

- [ ] **Step 1: Add under Conflict / Invariant sections**

```markdown
- **PR1.5:** `CommitConflictReason.FIXED_OUTPUT_TRANSPORT_CONFLICT` — cross-commit FOT reservation (`INV-COMMIT-FOT-01/02`). Distinct from candidate-generation `FIXED_OUTPUT_TRANSPORT_IN_OCCUPIED`.
- **PR1.5:** `CommitDomainState.committed_fixed_output_transport_cells` — append-only field; not merged into `committed_route_cells`.
```

- [ ] **Step 2: Commit**

```bash
git add documents/Algorithm/asteroid_lab_07_incremental_commit.md
git commit -m "docs: PR1.5 FOT cross-commit commit contract"
```

---

### Task 8: PR1.5 narrow gate and Lab acceptance

**Files:** none (verification)

- [ ] **Step 1: Narrow pytest gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py
python -m pytest tests/unit/asteroid_lab/test_rttp_commit.py tests/unit/asteroid_lab/test_final_validation_route_disjoint.py
python -m pytest tests/unit/asteroid_lab/test_rttp_greedy_regret.py tests/unit/asteroid_lab/test_rttp_selection_fot_prefilter.py
python -m ruff check django_apps/asteroid_lab/optimization/commit django_apps/asteroid_lab/optimization/validation django_apps/asteroid_lab/optimization/candidates/placement_cells.py django_apps/asteroid_lab/optimization/selection/greedy_regret.py django_apps/asteroid_lab/optimization/selection/macro_greedy_regret.py tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py tests/unit/asteroid_lab/test_rttp_selection_fot_prefilter.py
```

Expected: all PASS

- [ ] **Step 2: Broader RTTP (informational; may fail on Phase 1 catalog)**

```powershell
python -m pytest tests/unit/asteroid_lab -k "rttp and not macro_real_map"
```

Record pass/fail count; triage `validation_passed` / `catalog_footprint_mismatch` separately from PR1.5.

- [ ] **Step 3: Lab manual acceptance**

```powershell
python manage.py run_solver --slug <island-slug>
```

Hover `(-1,-10)` on **new** run:

| Expect | Must NOT see |
|--------|----------------|
| `placement.confirmed_fixed_output_transport` | `placement.confirmed_extractor` on same cell |

Old replay `frame_index: 22` may still show pre-fix layout until re-run.

- [ ] **Step 4: Mark spec/plan CLOSED in session notes** (user or agent when Lab green)

---

## Self-review (plan vs spec)

| Spec requirement | Task |
|------------------|------|
| INV-COMMIT-FOT-01/02 bidirectional | Task 2 |
| `committed_fixed_output_transport_cells` append-only | Task 2, 4 |
| FOT ∉ `reserved_route_cells` | Task 2 doc / no code path adds FOT to routes |
| `fixed_output_transport_cell` no re-derivation | Task 1 |
| INV-VALIDATION-FOT-01 read-only | Task 3 |
| Validation issue code hook (bool v0) | Task 3 note — no enum task |
| Selection pre-filter, commit authoritative | Task 5, 6 |
| INLET before FOT precedence | Task 2 step 3 order |
| Replay output-only | Task 8 step 3 |
| `test_rttp_commit_fot_conflict` | Task 2 |
| `test_rttp_greedy_regret` + selection FOT | Task 5 |

**Placeholder scan:** none.

**Out of scope (explicit):** Phase 1 topology rollback; `ValidationIssueCode` StrEnum implementation; broad pipeline `validation_passed` catalog triage (separate plan).

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-27-rttp-commit-fot-cross-commit-hotfix.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute in this session with executing-plans checkpoints  

**Which approach?**

If **Subagent-Driven:** use superpowers:subagent-driven-development.  
If **Inline:** use superpowers:executing-plans; start with Task 8 verification if code already landed, else Task 0.
