# RTTP Mining Equipment Goal — MEG-C1/C2 Implementation Plan

> **DO NOT EXECUTE** — **SUSPENDED** by [`2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`](../specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md). Historical reference only. MEG-C2 forbidden until RTTP runtime is explicitly re-opened by a new approved spec.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement honest mining equipment goal accounting (measurement + validation split). **MEG-C1/C2 success does not mean reaching 467** — it means a recovery-map run with ~25 pass-qualified equipment cells reports `optimization_goal.passed=false`, `validation_passed=false`, `run_status=partial_success`, and `shortfall` visible outside `layout_connectivity_issue_codes`.

**Architecture:** New read-only module `services/mining_equipment_goal.py` owns target formula, `ExteriorPassEvidence` builder, predicate, and aggregator. `pipeline.py` computes `structural_validation_passed` from existing `validate_pipeline_layout`, then merges `optimization_goal` block into product `validation_passed`. `rttp_solver_summary.py` persists `optimization_goal` + `run_status` for Lab/replay consumers.

**Tech Stack:** Python 3.12+, Django `asteroid_lab`, pytest, ruff, mypy (`django_apps`).

**Status:** **SUSPENDED** — was APPROVED 2026-05-27; **DO NOT EXECUTE** (decontamination P0). Historical reference only.  
**Execution mode:** **Subagent-Driven** (frozen — do not run until RTTP re-opened)  
**Work classification:** contract change · implementation change  
**Spec:** [`docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md`](../specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md)  
**Scope:** **MEG-C1 + MEG-C2 only** (MEG-C3/C4 out of scope — do not start)  
**Commits:** Withheld unless user explicitly requests.

### Review amendments (locked before implementation)

| # | Amendment | Resolution |
|---|-----------|------------|
| 1 | Import cycle `placement_goal` ↔ `mining_equipment_goal` | **Formula canonical owner:** `mining_equipment_goal.compute_target_mining_equipment_cells`. `placement_goal.compute_placement_goal_count` = thin deprecated alias importing **only** from MEG. **Never** import MEG from `placement_goal` into MEG. |
| 2 | `CommitResult` field drift | Evidence builder uses **private adapters** (`_normalize_exterior_lane_assignments`, `_normalize_elcp_route_evidence_by_candidate`) — no scattered raw field reads in aggregator/predicate. |
| 3 | `SolverRun.RunStatus.PARTIAL` | **Verified present** (`models.py` `RunStatus.PARTIAL`, migration `0010_solverrun_status_partial`). Persist maps `run_status=partial_success` → `PARTIAL`. If enum missing in a fork: product truth stays in `solver_summary.run_status`; DB enum migration is out of C2 scope. |

**Phase-1 done signal (recovery map, ~25 pass-qualified cells):**

```text
structural_validation_passed = true   (may)
optimization_goal.passed = false
validation_passed = false
run_status = partial_success
optimization_goal.shortfall = 442     (example when confirmed_passed = 25, target = 467)
mining_equipment_goal_shortfall ∉ layout_connectivity_issue_codes
```

---

## File structure

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/contracts/rttp_optimization_goal.py` | **New** — `MINING_EQUIPMENT_GOAL_SHORTFALL_ISSUE_CODE`, `RttpRunStatus` |
| `django_apps/asteroid_lab/services/mining_equipment_goal.py` | **New** — **canonical** `compute_target_mining_equipment_cells`, DTOs, commit adapters, evidence builder, aggregator, `optimization_goal` JSON |
| `django_apps/asteroid_lab/services/placement_goal.py` | **Thin alias only** — `compute_placement_goal_count` imports from MEG; docstring for deprecated semantics. **No MEG import from placement_goal.** |
| `django_apps/asteroid_lab/optimization/pipeline.py` | Wire MEG after commit validation; extend `PipelineResult` |
| `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | Accept `optimization_goal`, `run_status`, `structural_validation_passed` |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Pass MEG into summary; map `run_status` → `SolverRun.status` on persist |
| `django_apps/asteroid_lab/services/solver_run_lab_summary.py` | Expose `optimization_goal` in Lab row (`throughput_goal` sibling) |
| `tests/unit/asteroid_lab/test_mining_equipment_goal.py` | **New** — T1–T7 unit tests |
| `tests/unit/asteroid_lab/test_rttp_core_recovery_gate_a.py` | Update Gate A shortfall test (T5) |
| `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` | Optional: `optimization_goal` in lab payload |
| `documents/ai/current_plan.md` | ACTIVE row for MEG-C1/C2 |

**Not modified (MEG-C3):** `greedy_regret.py`, `incremental_commit.py` selection tuning, `lift_lane_domain.py`, candidate pool expansion.

---

## Spec → plan coverage

| Spec § | Task |
|--------|------|
| §4 target ceil | Task 1 |
| §5.4 `ExteriorPassEvidence` | Task 2–3 |
| §6 DTOs / bundle vs cells | Task 1, 4 |
| §7.1 two-layer validation | Task 5 |
| §7.2 `run_status` | Task 6 |
| §7.3 `optimization_goal` block | Task 5–6 |
| §8 MEG-C1/C2 only | Entire plan |
| §10 T1–T7 | Tasks 1–7 |

---

### Task 0: Queue + cross-links

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md` (header: link plan)

- [ ] **Step 1:** Add ACTIVE row after current ELCP/F1.2a block:

```markdown
**ACTIVE (2026-05-27):** **MEG-C1/C2** — mining equipment goal measurement + validation split (no 467 optimization). Spec: [`2026-05-27-rttp-mining-equipment-goal-contract-design.md`](../docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md) · plan: [`2026-05-27-rttp-mining-equipment-goal.md`](../docs/superpowers/plans/2026-05-27-rttp-mining-equipment-goal.md). Phase-1 done = 25/467 → `partial_success`, not product pass.
```

- [ ] **Step 2:** In spec header, add: `**Implementation plan:** [`2026-05-27-rttp-mining-equipment-goal.md`](../plans/2026-05-27-rttp-mining-equipment-goal.md)`

---

### Task 1: Issue codes + target formula + `mining_equipment_cells`

**Files:**
- Create: `django_apps/asteroid_lab/contracts/rttp_optimization_goal.py`
- Create: `django_apps/asteroid_lab/services/mining_equipment_goal.py` (partial — grow in later tasks)
- Create: `tests/unit/asteroid_lab/test_mining_equipment_goal.py`
- Modify: `django_apps/asteroid_lab/services/placement_goal.py` (thin alias — Task 1 Step 3b)

- [ ] **Step 1: Write failing tests (T1, T7 cell math)**

Create `tests/unit/asteroid_lab/test_mining_equipment_goal.py`:

```python
"""MEG-C1/C2 unit tests (spec §10 T1–T7)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.catalog_placement import CatalogPlacementRef
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.mining_equipment_goal import (
    compute_target_mining_equipment_cells,
    mining_equipment_cells,
)


def test_target_mining_equipment_cells_583_at_80_percent_is_467() -> None:
    assert compute_target_mining_equipment_cells(
        mineable_cell_count=583,
        placement_target_percent=80,
    ) == 467


def _bundle_candidate(
    *,
    anchor: Coord,
    extension_offsets: tuple[Coord, ...],
) -> BundleCandidate:
    extractor = (0, 0)
    occupied = frozenset({extractor, *extension_offsets})
    pattern = BundlePattern(
        pattern_id="test_lin",
        extension_count=len(extension_offsets),
        occupied_offsets=occupied,
        extractor_offset=extractor,
        extension_offsets=extension_offsets,
        output_dir="east",
        fixed_output_transport_offset=(1, 0),
        output_stub_offset=(1, 0),
        throughput_factor=1,
        topology_kind="linear",
    )
    stub = (anchor[0] + 1, anchor[1])
    return BundleCandidate(
        candidate_id=f"{anchor[0]},{anchor[1]}:test_lin:shape_belt",
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=frozenset(
            (anchor[0] + c[0], anchor[1] + c[1]) for c in occupied
        ),
        output_stub=stub,
        output_dir="east",
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=1,
        route_probe_cost=1,
        reachable=True,
        catalog_placement_ref=None,
    )


def test_mining_equipment_cells_one_extractor_three_extensions() -> None:
    anchor = (10, 20)
    extensions = ((1, 0), (2, 0), (3, 0))
    candidate = _bundle_candidate(anchor=anchor, extension_offsets=extensions)
    mineable = frozenset(
        {
            anchor,
            (anchor[0] + 1, anchor[1]),
            (anchor[0] + 2, anchor[1]),
            (anchor[0] + 3, anchor[1]),
        }
    )
    cells = mining_equipment_cells(candidate, mineable_cells=mineable)
    assert len(cells) == 4
    assert anchor in cells
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_mining_equipment_goal.py -v`  
Expected: `ModuleNotFoundError` or import errors for `mining_equipment_goal`.

- [ ] **Step 3: Implement constants + formula + cell helper**

`django_apps/asteroid_lab/contracts/rttp_optimization_goal.py`:

```python
"""RTTP optimization goal issue codes and run status (output-only)."""

from __future__ import annotations

from enum import StrEnum

MINING_EQUIPMENT_GOAL_SHORTFALL_ISSUE_CODE = "mining_equipment_goal_shortfall"


class RttpRunStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAIL = "fail"


__all__ = [
    "MINING_EQUIPMENT_GOAL_SHORTFALL_ISSUE_CODE",
    "RttpRunStatus",
]
```

`django_apps/asteroid_lab/services/mining_equipment_goal.py` (initial):

```python
"""Mining equipment goal — read-only measurement (MEG-C1/C2). Not imported by selection."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def compute_target_mining_equipment_cells(
    *,
    mineable_cell_count: int,
    placement_target_percent: int,
) -> int:
    """Canonical MEG target (ceil). Spec §4."""
    if mineable_cell_count <= 0 or placement_target_percent <= 0:
        return 0
    product = (
        Decimal(mineable_cell_count) * Decimal(placement_target_percent) / Decimal(100)
    )
    return int(product.to_integral_value(rounding=ROUND_CEILING))


def _translate_offset(anchor: Coord, offset: Coord) -> Coord:
    return (anchor[0] + offset[0], anchor[1] + offset[1])


def mining_equipment_cells(
    candidate: BundleCandidate,
    *,
    mineable_cells: frozenset[Coord],
) -> frozenset[Coord]:
    anchor = candidate.anchor_coord
    equipment: set[Coord] = {_translate_offset(anchor, candidate.pattern.extractor_offset)}
    for off in candidate.pattern.extension_offsets:
        equipment.add(_translate_offset(anchor, off))
    return frozenset(c for c in equipment if c in mineable_cells)


@dataclass(frozen=True, slots=True)
class MiningEquipmentGoalPlan:
    mineable_cell_count: int
    placement_target_percent: int
    target_mining_equipment_cells: int

    @property
    def placement_goal_count(self) -> int:
        return self.target_mining_equipment_cells
```

- [ ] **Step 3b: Thin alias in `placement_goal.py` (break cycle)**

Replace body of `compute_placement_goal_count` with re-export (keep function name for callers):

```python
from django_apps.asteroid_lab.services.mining_equipment_goal import (
    compute_target_mining_equipment_cells,
)


def compute_placement_goal_count(
    *,
    asteroid_field_cell_count: int,
    placement_target_percent: int,
) -> int:
    """Deprecated alias — target mining equipment cells (extractor+extension), not bundle count."""
    return compute_target_mining_equipment_cells(
        mineable_cell_count=asteroid_field_cell_count,
        placement_target_percent=placement_target_percent,
    )
```

**Invariant:** `placement_goal.py` must **not** import anything from MEG except the alias above; `mining_equipment_goal.py` must **not** import `placement_goal`.

- [ ] **Step 4: Run tests — expect PASS for T1 + cell helper**

Also run one existing placement_goal test if present:

Run: `python -m pytest tests/unit/asteroid_lab/test_placement_goal.py -v`  
(If file missing, skip; Gate A uses `compute_placement_goal_count` in Task 7.)

Run: `python -m pytest tests/unit/asteroid_lab/test_mining_equipment_goal.py::test_target_mining_equipment_cells_583_at_80_percent_is_467 tests/unit/asteroid_lab/test_mining_equipment_goal.py::test_mining_equipment_cells_one_extractor_three_extensions -v`

- [ ] **Step 5: ruff**

Run: `python -m ruff check django_apps/asteroid_lab/contracts/rttp_optimization_goal.py django_apps/asteroid_lab/services/mining_equipment_goal.py tests/unit/asteroid_lab/test_mining_equipment_goal.py`

---

### Task 2: `ExteriorPassEvidence` + `has_confirmed_exterior_pass`

**Files:**
- Modify: `django_apps/asteroid_lab/services/mining_equipment_goal.py`
- Modify: `tests/unit/asteroid_lab/test_mining_equipment_goal.py`

- [ ] **Step 1: Write failing predicate tests**

Append to `test_mining_equipment_goal.py`:

```python
from django_apps.asteroid_lab.services.mining_equipment_goal import (
    ExteriorPassEvidence,
    has_confirmed_exterior_pass,
)


def _evidence(**kwargs: object) -> ExteriorPassEvidence:
    base = dict(
        candidate_id="c1",
        transport_kind=TransportKind.SHAPE_BELT,
        output_stub_reserved=True,
        reached_elcp_lane_id=None,
        reached_external_margin=False,
        shareable_trunk_overlap_only=True,
        lane_capacity_ok=True,
    )
    base.update(kwargs)
    return ExteriorPassEvidence(**base)  # type: ignore[arg-type]


def test_has_confirmed_exterior_pass_elcp_active_requires_lane() -> None:
    assert has_confirmed_exterior_pass(
        _evidence(reached_elcp_lane_id="lane-a", lane_capacity_ok=True),
        elcp_plan_active=True,
    )
    assert not has_confirmed_exterior_pass(
        _evidence(reached_external_margin=True, reached_elcp_lane_id=None),
        elcp_plan_active=True,
    )


def test_has_confirmed_exterior_pass_legacy_margin_when_elcp_inactive() -> None:
    assert has_confirmed_exterior_pass(
        _evidence(reached_external_margin=True),
        elcp_plan_active=False,
    )


def test_has_confirmed_exterior_pass_rejects_missing_stub_or_private_overlap() -> None:
    assert not has_confirmed_exterior_pass(
        _evidence(output_stub_reserved=False),
        elcp_plan_active=False,
    )
    assert not has_confirmed_exterior_pass(
        _evidence(shareable_trunk_overlap_only=False),
        elcp_plan_active=False,
    )
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_mining_equipment_goal.py -k has_confirmed_exterior_pass -v`

- [ ] **Step 3: Implement DTO + predicate**

Add to `mining_equipment_goal.py`:

```python
@dataclass(frozen=True, slots=True)
class ExteriorPassEvidence:
    candidate_id: str
    transport_kind: TransportKind
    output_stub_reserved: bool
    reached_elcp_lane_id: str | None
    reached_external_margin: bool
    shareable_trunk_overlap_only: bool
    lane_capacity_ok: bool


def has_confirmed_exterior_pass(
    evidence: ExteriorPassEvidence,
    *,
    elcp_plan_active: bool,
) -> bool:
    if not evidence.output_stub_reserved:
        return False
    if not evidence.shareable_trunk_overlap_only:
        return False
    if elcp_plan_active:
        return evidence.reached_elcp_lane_id is not None and evidence.lane_capacity_ok
    return evidence.reached_external_margin
```

- [ ] **Step 4: Run — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_mining_equipment_goal.py -k has_confirmed_exterior_pass -v`

---

### Task 3: Post-commit `ExteriorPassEvidence` builder

**Files:**
- Modify: `django_apps/asteroid_lab/services/mining_equipment_goal.py`
- Modify: `tests/unit/asteroid_lab/test_mining_equipment_goal.py`

**Rules:**

1. Only `build_exterior_pass_evidence_for_committed_bundles` touches `CommitResult` (via adapters below).
2. Aggregator / predicate consume `tuple[ExteriorPassEvidence, ...]` only — **no** `commit_result` field access.
3. **Adapters (private, module-local):** normalize raw commit payloads; if `incremental_commit` renames a field, fix adapters only.

```python
@dataclass(frozen=True, slots=True)
class _NormalizedLaneAssignment:
    candidate_id: str
    exterior_lane_id: str | None
    legacy_elcp_fallback: bool
    reached_goal: tuple[int, int] | None


def _normalize_exterior_lane_assignments(
    commit_result: CommitResult,
) -> dict[str, _NormalizedLaneAssignment]:
    out: dict[str, _NormalizedLaneAssignment] = {}
    for raw in commit_result.exterior_lane_assignments:
        if not isinstance(raw, dict):
            continue
        cid = raw.get("candidate_id")
        if not isinstance(cid, str):
            continue
        reached: tuple[int, int] | None = None
        rg = raw.get("reached_goal")
        if isinstance(rg, list) and len(rg) >= 2:
            reached = (int(rg[0]), int(rg[1]))
        lane_raw = raw.get("exterior_lane_id")
        out[cid] = _NormalizedLaneAssignment(
            candidate_id=cid,
            exterior_lane_id=str(lane_raw) if lane_raw else None,
            legacy_elcp_fallback=bool(raw.get("legacy_elcp_fallback")),
            reached_goal=reached,
        )
    return out


def _normalize_elcp_route_evidence_by_candidate(
    commit_result: CommitResult,
) -> frozenset[str]:
    """Candidate ids with ELCP route evidence rows (current CommitResult field)."""
    return frozenset(ev.candidate_id for ev in commit_result.exterior_lane_route_evidence)
```

- [ ] **Step 1: Write failing builder test**

```python
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.services.mining_equipment_goal import (
    build_exterior_pass_evidence_for_committed_bundles,
)


def test_builder_marks_legacy_elcp_fallback_ineligible_for_elcp_pass() -> None:
    candidate = _bundle_candidate(anchor=(0, 0), extension_offsets=())
    by_id = {candidate.candidate_id: candidate}
    commit = CommitResult(
        committed_ids=(candidate.candidate_id,),
        reserved_route_cells=frozenset({candidate.output_stub}),
        domain_version=1,
        conflicts=(),
        exterior_lane_assignments=(
            {
                "candidate_id": candidate.candidate_id,
                "exterior_lane_id": "lane-1",
                "legacy_elcp_fallback": True,
                "reached_goal": [],
            },
        ),
    )
    rows = build_exterior_pass_evidence_for_committed_bundles(
        commit_result=commit,
        candidates_by_id=by_id,
        inp_transport_kind=TransportKind.SHAPE_BELT,
        elcp_plan_active=True,
        exterior_lane_plan_present=True,
    )
    assert len(rows) == 1
    assert rows[0].reached_elcp_lane_id is None
    assert rows[0].output_stub_reserved is True
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement adapters + builder**

```python
def build_exterior_pass_evidence_for_committed_bundles(
    *,
    commit_result: CommitResult,
    candidates_by_id: dict[str, BundleCandidate],
    inp_transport_kind: TransportKind,
    elcp_plan_active: bool,
    exterior_lane_plan_present: bool,
) -> tuple[ExteriorPassEvidence, ...]:
    assignment_by_id = _normalize_exterior_lane_assignments(commit_result)
    elcp_route_ids = _normalize_elcp_route_evidence_by_candidate(commit_result)
    reserved = commit_result.reserved_route_cells
    out: list[ExteriorPassEvidence] = []
    for cid in commit_result.committed_ids:
        candidate = candidates_by_id.get(cid)
        if candidate is None:
            continue
        row = assignment_by_id.get(cid)
        legacy_fallback = bool(row and row.legacy_elcp_fallback)
        has_reached_goal = row is not None and row.reached_goal is not None
        lane_id: str | None = None
        if (
            elcp_plan_active
            and exterior_lane_plan_present
            and row is not None
            and not legacy_fallback
            and has_reached_goal
        ):
            lane_id = row.exterior_lane_id
        reached_margin = cid in elcp_route_ids or has_reached_goal
        if not elcp_plan_active:
            reached_margin = candidate.output_stub in reserved
        out.append(
            ExteriorPassEvidence(
                candidate_id=cid,
                transport_kind=inp_transport_kind,
                output_stub_reserved=candidate.output_stub in reserved,
                reached_elcp_lane_id=lane_id,
                reached_external_margin=reached_margin,
                shareable_trunk_overlap_only=True,
                lane_capacity_ok=lane_id is not None or not elcp_plan_active,
            )
        )
    return tuple(out)
```

Import `CommitResult` from `incremental_commit`. Optional later: tighten `lane_capacity_ok` from `exterior_lane_assignment_state` (read-only); not required for C2 acceptance.

- [ ] **Step 4: Run builder test — PASS**

---

### Task 4: Aggregator + `MiningEquipmentGoalResult` (T2–T4, T7)

**Files:**
- Modify: `django_apps/asteroid_lab/services/mining_equipment_goal.py`
- Modify: `tests/unit/asteroid_lab/test_mining_equipment_goal.py`

- [ ] **Step 1: Write failing aggregator tests**

```python
from django_apps.asteroid_lab.services.mining_equipment_goal import (
    aggregate_mining_equipment_goal_result,
)


def test_aggregate_counts_pass_qualified_cells_not_route_cells() -> None:
    ext = ((1, 0), (2, 0))
    candidate = _bundle_candidate(anchor=(5, 5), extension_offsets=ext)
    mineable = frozenset(candidate.occupied_cells)
    evidence = ExteriorPassEvidence(
        candidate_id=candidate.candidate_id,
        transport_kind=TransportKind.SHAPE_BELT,
        output_stub_reserved=True,
        reached_elcp_lane_id="lane-1",
        reached_external_margin=True,
        shareable_trunk_overlap_only=True,
        lane_capacity_ok=True,
    )
    result = aggregate_mining_equipment_goal_result(
        evidence_rows=(evidence,),
        candidates_by_id={candidate.candidate_id: candidate},
        mineable_cells=mineable,
        target_mining_equipment_cells=467,
        elcp_plan_active=True,
        committed_ids=(candidate.candidate_id,),
    )
    assert result.confirmed_passed_mining_equipment_cells == 3
    assert result.confirmed_committed_bundle_count == 1
    assert result.shortfall == 464


def test_aggregate_bundle_count_vs_equipment_cells_t7() -> None:
    candidate = _bundle_candidate(
        anchor=(0, 0),
        extension_offsets=((1, 0), (2, 0), (3, 0)),
    )
    mineable = frozenset(candidate.occupied_cells)
    evidence = ExteriorPassEvidence(
        candidate_id=candidate.candidate_id,
        transport_kind=TransportKind.SHAPE_BELT,
        output_stub_reserved=True,
        reached_elcp_lane_id="lane-1",
        reached_external_margin=True,
        shareable_trunk_overlap_only=True,
        lane_capacity_ok=True,
    )
    result = aggregate_mining_equipment_goal_result(
        evidence_rows=(evidence,),
        candidates_by_id={candidate.candidate_id: candidate},
        mineable_cells=mineable,
        target_mining_equipment_cells=10,
        elcp_plan_active=True,
        committed_ids=(candidate.candidate_id,),
    )
    assert result.confirmed_committed_bundle_count == 1
    assert result.confirmed_passed_mining_equipment_cells == 4
```

Add test for failing P4 (`shareable_trunk_overlap_only=False`) → 0 passed cells.

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement `MiningEquipmentGoalResult` + aggregator**

```python
@dataclass(frozen=True, slots=True)
class MiningEquipmentGoalResult:
    target_mining_equipment_cells: int
    confirmed_passed_mining_equipment_cells: int
    confirmed_committed_bundle_count: int
    shortfall: int
    confirmed_transport_route_cell_count: int = 0
    confirmed_trunk_cell_count: int = 0
    confirmed_external_link_touch_count: int = 0


def aggregate_mining_equipment_goal_result(
    *,
    evidence_rows: tuple[ExteriorPassEvidence, ...],
    candidates_by_id: dict[str, BundleCandidate],
    mineable_cells: frozenset[Coord],
    target_mining_equipment_cells: int,
    elcp_plan_active: bool,
    committed_ids: tuple[str, ...],
    reserved_route_cells: frozenset[Coord] | None = None,
) -> MiningEquipmentGoalResult:
    passed_cells = 0
    for ev in evidence_rows:
        if not has_confirmed_exterior_pass(ev, elcp_plan_active=elcp_plan_active):
            continue
        cand = candidates_by_id.get(ev.candidate_id)
        if cand is None:
            continue
        passed_cells += len(mining_equipment_cells(cand, mineable_cells=mineable_cells))
    shortfall = max(0, target_mining_equipment_cells - passed_cells)
    route_count = len(reserved_route_cells or frozenset())
    return MiningEquipmentGoalResult(
        target_mining_equipment_cells=target_mining_equipment_cells,
        confirmed_passed_mining_equipment_cells=passed_cells,
        confirmed_committed_bundle_count=len(committed_ids),
        shortfall=shortfall,
        confirmed_transport_route_cell_count=route_count,
    )
```

- [ ] **Step 4: Run full unit file — PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_mining_equipment_goal.py -v`

---

### Task 5: `optimization_goal` block + pipeline validation split

**Files:**
- Modify: `django_apps/asteroid_lab/services/mining_equipment_goal.py`
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`
- Modify: `tests/unit/asteroid_lab/test_mining_equipment_goal.py` (optional `optimization_goal_to_json` unit test)

- [ ] **Step 1: Add JSON builder**

```python
from django_apps.asteroid_lab.contracts.rttp_optimization_goal import (
    MINING_EQUIPMENT_GOAL_SHORTFALL_ISSUE_CODE,
)


def optimization_goal_passed(result: MiningEquipmentGoalResult) -> bool:
    if result.target_mining_equipment_cells <= 0:
        return True
    return (
        result.confirmed_passed_mining_equipment_cells
        >= result.target_mining_equipment_cells
    )


def optimization_goal_to_json(result: MiningEquipmentGoalResult) -> dict[str, object]:
    passed = optimization_goal_passed(result)
    block: dict[str, object] = {
        "passed": passed,
        "issue_code": None if passed else MINING_EQUIPMENT_GOAL_SHORTFALL_ISSUE_CODE,
        "target_mining_equipment_cells": result.target_mining_equipment_cells,
        "confirmed_passed_mining_equipment_cells": result.confirmed_passed_mining_equipment_cells,
        "shortfall": result.shortfall,
        "confirmed_committed_bundle_count": result.confirmed_committed_bundle_count,
    }
    return block


def resolve_run_status(
    *,
    structural_validation_passed: bool,
    optimization_goal: Mapping[str, object],
) -> RttpRunStatus:
    from django_apps.asteroid_lab.contracts.rttp_optimization_goal import RttpRunStatus

    if not structural_validation_passed:
        return RttpRunStatus.FAIL
    if bool(optimization_goal.get("passed")):
        return RttpRunStatus.SUCCESS
    return RttpRunStatus.PARTIAL_SUCCESS
```

- [ ] **Step 2: Add pipeline helper `_apply_mining_equipment_goal`**

In `pipeline.py` (new function near bottom of module, before `run_rttp_pipeline`):

```python
def _apply_mining_equipment_goal(
    *,
    structural_validation_passed: bool,
    commit_result: CommitResult,
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
    placement_target_percent: int,
    placement_platform_cell_count: int,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None,
    reconstruction_max_active: bool,
) -> tuple[bool, dict[str, object], bool, str]:
    """Returns (validation_passed, optimization_goal_json, structural_passed, run_status_value)."""
    from django_apps.asteroid_lab.services.mining_equipment_goal import (
        aggregate_mining_equipment_goal_result,
        build_exterior_pass_evidence_for_committed_bundles,
        compute_target_mining_equipment_cells,
        optimization_goal_to_json,
        resolve_run_status,
    )

    target = compute_target_mining_equipment_cells(
        mineable_cell_count=placement_platform_cell_count,
        placement_target_percent=placement_target_percent,
    )
    elcp_active = reconstruction_max_active and exterior_lane_plan is not None
    evidence = build_exterior_pass_evidence_for_committed_bundles(
        commit_result=commit_result,
        candidates_by_id=candidates_by_id,
        inp_transport_kind=inp.transport_kind,
        elcp_plan_active=elcp_active,
        exterior_lane_plan_present=exterior_lane_plan is not None,
    )
    meg_result = aggregate_mining_equipment_goal_result(
        evidence_rows=evidence,
        candidates_by_id=candidates_by_id,
        mineable_cells=inp.mineable_cells,
        target_mining_equipment_cells=target,
        elcp_plan_active=elcp_active,
        committed_ids=commit_result.committed_ids,
        reserved_route_cells=commit_result.reserved_route_cells,
    )
    opt_goal = optimization_goal_to_json(meg_result)
    run_status = resolve_run_status(
        structural_validation_passed=structural_validation_passed,
        optimization_goal=opt_goal,
    )
    validation_passed = structural_validation_passed and bool(opt_goal["passed"])
    return validation_passed, opt_goal, structural_validation_passed, run_status.value
```

- [ ] **Step 3: Wire normal pipeline** (~line 714 after `validate_pipeline_layout`)

Replace direct use of `validation_passed` with:

```python
structural_validation_passed, catalog_result, layout_connectivity_issues = (
    validate_pipeline_layout(...)
)
validation_passed, optimization_goal, structural_passed, run_status = (
    _apply_mining_equipment_goal(
        structural_validation_passed=structural_validation_passed,
        commit_result=commit_result,
        candidates_by_id=candidates_by_id,
        inp=inp,
        placement_target_percent=config.placement_target_percent,
        placement_platform_cell_count=_placement_platform_cell_count(config, inp),
        exterior_lane_plan=exterior_lane_plan,
        reconstruction_max_active=config.reconstruction_max_throughput_per_min is not None,
    )
)
```

Add to commit step `metrics_json` (do **not** append shortfall to `layout_connectivity_issue_codes`):

```python
"structural_validation_passed": structural_passed,
"optimization_goal": optimization_goal,
"run_status": run_status,
"target_mining_equipment_cells": optimization_goal["target_mining_equipment_cells"],
"confirmed_passed_mining_equipment_cells": optimization_goal[
    "confirmed_passed_mining_equipment_cells"
],
```

Extend `PipelineResult`:

```python
@dataclass(frozen=True, slots=True)
class PipelineResult:
    ...
    structural_validation_passed: bool = False
    optimization_goal: dict[str, Any] | None = None
    run_status: str = "fail"
```

Macro pipeline (`_run_macro_rttp_pipeline`): set `optimization_goal={"passed": True, "issue_code": None, "macro_only_mode": True}` and `validation_passed = structural only` when `macro_only_mode` — document in code comment.

- [ ] **Step 4: Unit test for `optimization_goal_to_json` shortfall keys**

- [ ] **Step 5: Run pipeline-related tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_mining_equipment_goal.py tests/unit/asteroid_lab/test_rttp_core_recovery_gate_a.py -v`

---

### Task 6: Solver summary + runtime persist + Lab UI

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- Modify: `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` (if adding field assertions)

- [ ] **Step 1: Extend `build_rttp_solver_summary`**

Add parameters:

```python
def build_rttp_solver_summary(
    *,
    pipeline_ok: bool,
    ...
    optimization_goal: Mapping[str, Any] | None = None,
    run_status: str | None = None,
    structural_validation_passed: bool | None = None,
) -> dict[str, Any]:
```

Set:

```python
summary["optimization_goal"] = dict(optimization_goal or {"passed": True, "issue_code": None})
summary["run_status"] = run_status or ("success" if pipeline_ok else "fail")
if structural_validation_passed is not None:
    summary["structural_validation_passed"] = bool(structural_validation_passed)
summary["target_mining_equipment_cells"] = summary["optimization_goal"].get(
    "target_mining_equipment_cells"
)
```

Keep `validation_passed` / `run_success` = `pipeline_ok` (already combined product pass).

When goal shortfall and structural pass: add `mining_equipment_goal_shortfall` to **`issue_codes`** (top-level), **not** `layout_connectivity_issue_codes`.

- [ ] **Step 2: Wire `solver_runtime_entry.py`**

After pipeline, read from `pipeline_result`:

```python
optimization_goal = getattr(pipeline_result, "optimization_goal", None) or {}
run_status = getattr(pipeline_result, "run_status", "fail")
structural_passed = getattr(pipeline_result, "structural_validation_passed", False)
```

Pass into `build_rttp_solver_summary(..., pipeline_ok=pipeline_result.validation_passed, optimization_goal=optimization_goal, run_status=run_status, structural_validation_passed=structural_passed)`.

Extend `_persist_solver_run_outcome` with **PARTIAL guard**:

```python
def _solver_run_status_from_summary(solver_summary: Mapping[str, Any]) -> str:
    """Map product run_status to SolverRun.RunStatus value."""
    rs = str(solver_summary.get("run_status") or "")
    if rs == "partial_success":
        if hasattr(m.SolverRun.RunStatus, "PARTIAL"):
            return m.SolverRun.RunStatus.PARTIAL
        # Fork without PARTIAL enum: legacy DB storage; product truth in solver_summary.run_status
        return m.SolverRun.RunStatus.COMPLETED
    if rs == "fail" or not bool(solver_summary.get("validation_passed")):
        return m.SolverRun.RunStatus.FAILED
    return m.SolverRun.RunStatus.COMPLETED


def _persist_solver_run_outcome(run_id: int, *, solver_summary: dict[str, Any]) -> None:
    run = m.SolverRun.objects.get(pk=int(run_id))
    config = dict(run.config_json or {})
    config[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY] = dict(solver_summary)
    status = _solver_run_status_from_summary(solver_summary)
    m.SolverRun.objects.filter(pk=int(run_id)).update(config_json=config, status=status)
```

**Verified in repo:** `SolverRun.RunStatus.PARTIAL` exists (`django_apps/asteroid_lab/models.py`, migration `0010_solverrun_status_partial`). No migration in MEG-C2 unless enum missing in target branch.

Map `entry_result_to_json_dict` ui_status from `solver_summary["run_status"]`: `partial_success` → `"partial"`, `success` → `"completed"`, else `"failed"`.

- [ ] **Step 3: Lab summary**

In `lab_run_summary_from_solver_summary`, add:

```python
"optimization_goal": dict(solver_summary.get("optimization_goal") or {}),
"run_status": solver_summary.get("run_status"),
```

- [ ] **Step 4: Test**

Extend or add test asserting `optimization_goal` survives `lab_run_summary_from_solver_summary`.

---

### Task 7: Gate A regression — T5 + T6 + T7 integration

**Files:**
- Modify: `tests/unit/asteroid_lab/test_rttp_core_recovery_gate_a.py`

- [ ] **Step 1: Update `test_recovery_map_validation_passes_with_placement_goal_shortfall_only`**

Rename to `test_recovery_map_structural_pass_optimization_goal_shortfall`.

Change assertions:

```python
assert pipeline_result.structural_validation_passed is True
assert pipeline_result.optimization_goal is not None
assert pipeline_result.optimization_goal["passed"] is False
assert pipeline_result.optimization_goal["issue_code"] == "mining_equipment_goal_shortfall"
assert pipeline_result.validation_passed is False
assert pipeline_result.run_status == "partial_success"
assert committed_count < plan.placement_goal_count
assert plan.placement_goal_count == 467  # or expected_goal from fixture
```

Commit step metrics:

```python
assert "mining_equipment_goal_shortfall" not in layout_codes
opt = commit_step["metrics"].get("optimization_goal") or {}
assert opt.get("shortfall", 0) > 0
```

- [ ] **Step 2: Add T6-style assertion on algorithm_steps / run**

If test runs full `run_solver_runtime_for_project`, assert `solver_summary["optimization_goal"]` keys — optional second test file marker `@pytest.mark.django_db` slow.

- [ ] **Step 3: Run Gate A + MEG unit**

Run: `python -m pytest tests/unit/asteroid_lab/test_mining_equipment_goal.py tests/unit/asteroid_lab/test_rttp_core_recovery_gate_a.py -v`

Expected: all selected tests PASS.

- [ ] **Step 4: ruff + mypy (narrow)**

Run: `python -m ruff check django_apps/asteroid_lab/services/mining_equipment_goal.py django_apps/asteroid_lab/contracts/rttp_optimization_goal.py django_apps/asteroid_lab/optimization/pipeline.py`  
Run: `python -m mypy django_apps/asteroid_lab/services/mining_equipment_goal.py django_apps/asteroid_lab/contracts/rttp_optimization_goal.py`

---

### Task 8: Close plan metadata

**Files:**
- Modify: `documents/ai/current_plan.md` — mark MEG-C1/C2 CLOSED after implementation (not in approval phase)
- Modify: spec status line → `Implementation plan approved` when user approves this plan

- [ ] **Step 1:** After green Task 7, update `current_plan.md` ACTIVE → CLOSED with date.

---

## Verification commands (MEG-C1/C2)

```bash
python -m pytest tests/unit/asteroid_lab/test_mining_equipment_goal.py -v
python -m pytest tests/unit/asteroid_lab/test_rttp_core_recovery_gate_a.py -v
python -m ruff check django_apps/asteroid_lab/services/mining_equipment_goal.py django_apps/asteroid_lab/contracts/rttp_optimization_goal.py django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/optimization/rttp_solver_summary.py django_apps/asteroid_lab/services/solver_runtime_entry.py
python -m mypy django_apps/asteroid_lab/services/mining_equipment_goal.py django_apps/asteroid_lab/contracts/rttp_optimization_goal.py
```

Full gate (`scripts/test_full.ps1`, entire pytest) — run before PR; not required for plan approval.

---

## Acceptance criteria (MEG-C1/C2)

| Criterion | Expected |
|-----------|----------|
| Target | `target_mining_equipment_cells(583, 80) == 467` |
| Recovery map run | `structural_validation_passed` may be true |
| Product pass | `validation_passed == false` when confirmed_passed ≪ 467 |
| Run status | `partial_success` when structural pass + goal fail |
| Shortfall visibility | `optimization_goal.shortfall > 0` (e.g. 442 when 25/467); issue code `mining_equipment_goal_shortfall` |
| Layout issues | Shortfall **not** in `layout_connectivity_issue_codes` |
| Bundle vs cells | T7: 1 bundle, 4 equipment cells when 1+3 extensions pass-qualified |
| Non-goals | No selection/commit tuning; no 467 achievement required |

---

## Plan self-review (2026-05-27)

| Check | Result |
|-------|--------|
| Spec coverage §4–§10 | Tasks 1–7 |
| Placeholders | None — code blocks are implementable starters |
| MEG-C3/C4 excluded | Stated in header + non-goals |
| Forbidden shortcuts | No replay as input; no layout repair; no layout issue for goal |
| Gate A test conflict | Task 7 renames/updates explicit regression test |
| Macro path | `optimization_goal` passthrough / macro_only note in Task 5 |
| Type consistency | `ExteriorPassEvidence` / `optimization_goal` keys match spec §7.3 |
| Review amendments 1–3 | Locked in header + Tasks 1, 3, 6 |
| Import cycle | Formula owner MEG; placement_goal alias only |

---

## Execution phases (Subagent-Driven)

**Chosen mode:** Subagent-Driven (Plan Review Lead). **REQUIRED SUB-SKILL:** superpowers:subagent-driven-development.

Do **not** implement Tasks 2–6 in one inline batch — boundaries mix easily (`validation_passed`, `run_status`, `optimization_goal`).

| Phase | Tasks | Owner | Deliverable |
|-------|-------|-------|-------------|
| **P0** | Task 0–1 | Main or inline | Constants, canonical formula, `mining_equipment_cells`, placement_goal alias |
| **P1** | Task 2–4 | Subagent A — pure MEG service | `ExteriorPassEvidence`, adapters, builder, aggregator; `test_mining_equipment_goal.py` green |
| **P2** | Task 5 | Subagent B — pipeline | `_apply_mining_equipment_goal`, `PipelineResult` fields, commit metrics block |
| **P3** | Task 6 | Subagent C — summary/runtime/Lab | `build_rttp_solver_summary`, `_persist_solver_run_outcome`, lab row |
| **P4** | Task 7–8 | Review lead (main) | Gate A test flip, ruff/mypy, `current_plan.md` CLOSED |

**Checkpoint after each phase:** narrow pytest per phase table + ruff on touched paths.

**Stop line:** MEG-C3/C4 out of scope until C1/C2 acceptance criteria green.

---

## Execution handoff

**Plan approved** — `docs/superpowers/plans/2026-05-27-rttp-mining-equipment-goal.md`.

**Next action:** Start **P0 (Task 0–1)** inline, then dispatch **Subagent A** for Tasks 2–4. Do not start MEG-C3.
