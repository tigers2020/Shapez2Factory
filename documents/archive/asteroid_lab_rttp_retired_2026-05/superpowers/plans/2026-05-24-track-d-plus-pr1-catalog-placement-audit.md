# Track D+ PR-1 — Catalog Placement Audit (Observe-Only) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add observe-only catalog placement audit after RTTP commit validation, expose metrics on `rttp.catalog_placement_validation`, and prove mismatch taxonomy in pytest without changing `validation_passed` or solver behavior.

**Architecture:** Frozen contracts in `catalog_placement.py`; public footprint transform in `catalog_geometry_transform.py` (no private `pattern_library` imports); pure audit in `catalog_placement_audit.py`; pipeline records an algorithm step; `solver_runtime_entry` passes the step into `build_rttp_solver_summary`. Optional `catalog_placement_ref` on `BundleCandidate` defaults to `None` — generator unchanged.

**Tech Stack:** Python 3.12, Django 5, frozen dataclasses, StrEnum, pytest, ruff.

**Approved spec:** [`2026-05-24-track-d-plus-catalog-placement-validation-design.md`](../specs/2026-05-24-track-d-plus-catalog-placement-validation-design.md)

**Recommended worktree:** `f:\Python_Projects\shapez2Factory\.worktrees\track-d-plus-pr1` on branch `feature/track-d-plus-pr1-catalog-audit`

---

## Out of scope (PR gate)

| Area | Reason |
|------|--------|
| `validation_passed` / `run_success` changes | PR-1 observe-only |
| `optimization/selection/**`, fitness, regret | Forbidden |
| `optimization/macros/**` beyond audit step wiring | Macro PAUSE |
| Connector mismatch computation | PR-2+ |
| `ValidationResult` / fail-closed | PR-2 |
| `candidate_generator` changes | PR-3 |
| Replay frames → algorithm input | Forbidden |

**Regression gates (stay green):**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v
python -m pytest tests/unit/architecture/test_catalog_consumption_boundaries.py -v
powershell -File scripts/test_reconstruction_narrow.ps1
python -m ruff check django_apps/asteroid_lab/contracts django_apps/asteroid_lab/adapters django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/optimization/rttp_solver_summary.py
```

---

## File map

| File | Change |
|------|--------|
| `django_apps/asteroid_lab/contracts/catalog_placement.py` | **Create** DTOs + enums |
| `django_apps/asteroid_lab/adapters/catalog_geometry_transform.py` | **Create** public transform |
| `django_apps/asteroid_lab/adapters/catalog_placement_audit.py` | **Create** audit logic |
| `django_apps/asteroid_lab/optimization/candidates/candidate_dtos.py` | Add optional `catalog_placement_ref` |
| `django_apps/asteroid_lab/optimization/pipeline.py` | Audit after `validate_final_layout`; record step |
| `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | New step id + builder |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Pass audit step from pipeline result |
| `tests/unit/asteroid_lab/test_catalog_geometry_transform.py` | **Create** |
| `tests/unit/asteroid_lab/test_catalog_placement_audit.py` | **Create** taxonomy fixtures |
| `tests/unit/asteroid_lab/test_rttp_pipeline_catalog_audit.py` | **Create** validation_passed unchanged |
| `tests/unit/asteroid_lab/test_rttp_solver_summary.py` | Expect new step id in ordering |
| `docs/adr/ADR-004-game-data-snapshot-boundary.md` | D+ PR-1 subsection |
| `documents/index/document_inventory.md` | Track D+ row |
| `docs/domain/asteroid_game_data_snapshot.md` | D+ PR-1 paragraph |
| `documents/ai/current_plan.md` | ACTIVE Track D+ PR-1 |

---

### Task 1 — Contracts (`catalog_placement.py`)

**Files:**
- Create: `django_apps/asteroid_lab/contracts/catalog_placement.py`
- Test: `tests/unit/asteroid_lab/test_catalog_placement_contracts.py`

- [ ] **Step 1: Write failing import test**

```python
# tests/unit/asteroid_lab/test_catalog_placement_contracts.py
from django_apps.asteroid_lab.contracts.catalog_placement import (
    CardinalDirection,
    CatalogPlacementAudit,
    CatalogPlacementIssueCode,
    CatalogPlacementRef,
)


def test_cardinal_direction_values() -> None:
    assert CardinalDirection.E.value == "E"
    assert CardinalDirection.N.value == "N"


def test_catalog_placement_issue_code_is_str_enum() -> None:
    assert CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH.value == (
        "catalog_footprint_mismatch"
    )
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_catalog_placement_contracts.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement contracts**

```python
# django_apps/asteroid_lab/contracts/catalog_placement.py
"""Catalog placement audit contracts (Track D+)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from django_apps.asteroid_lab.optimization.coords import Coord


class CardinalDirection(StrEnum):
    N = "N"
    E = "E"
    S = "S"
    W = "W"


class CatalogPlacementIssueCode(StrEnum):
    CATALOG_VARIANT_MAPPING_MISSING = "catalog_variant_mapping_missing"
    CATALOG_VARIANT_NOT_IN_SLICE = "catalog_variant_not_in_slice"
    CATALOG_FOOTPRINT_MISMATCH = "catalog_footprint_mismatch"
    CATALOG_CONNECTOR_MISMATCH = "catalog_connector_mismatch"
    CATALOG_ANCHOR_TRANSFORM_ERROR = "catalog_anchor_transform_error"
    CATALOG_ROTATION_UNSUPPORTED = "catalog_rotation_unsupported"


@dataclass(frozen=True, slots=True)
class CatalogPlacementRef:
    canonical_id: str
    anchor_coord: Coord
    rotation: CardinalDirection


@dataclass(frozen=True, slots=True)
class CatalogPlacementAudit:
    catalog_validation_mode: Literal["observe_only"]
    checked_candidate_count: int
    matched_candidate_count: int
    mismatch_candidate_count: int
    unmapped_candidate_count: int
    not_in_slice_count: int
    transform_error_count: int
    issue_codes: tuple[str, ...]


__all__ = [
    "CardinalDirection",
    "CatalogPlacementAudit",
    "CatalogPlacementIssueCode",
    "CatalogPlacementRef",
]
```

- [ ] **Step 4: Run test — expect PASS**

```bash
python -m pytest tests/unit/asteroid_lab/test_catalog_placement_contracts.py -v
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/contracts/catalog_placement.py tests/unit/asteroid_lab/test_catalog_placement_contracts.py
git commit -m "feat(asteroid-lab): add catalog placement audit contracts"
```

---

### Task 2 — Public geometry transform

**Files:**
- Create: `django_apps/asteroid_lab/adapters/catalog_geometry_transform.py`
- Test: `tests/unit/asteroid_lab/test_catalog_geometry_transform.py`

- [ ] **Step 1: Write failing parity + transform tests**

```python
# tests/unit/asteroid_lab/test_catalog_geometry_transform.py
from __future__ import annotations

import pytest

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    CatalogTransformError,
    expected_footprint_coords,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import BuildingFootprintCell
from django_apps.asteroid_lab.optimization.candidates.pattern_library import (
    build_pattern_library,
)


def test_expected_footprint_east_identity_at_anchor() -> None:
    cells = (BuildingFootprintCell(0, 0, 0), BuildingFootprintCell(1, 0, 1))
    got = expected_footprint_coords(
        cells,
        anchor_coord=(5, 7),
        rotation=CardinalDirection.E,
    )
    assert got == frozenset({(5, 7), (6, 7)})


def test_catalog_geometry_transform_matches_pattern_library_east_rotation() -> None:
  patterns = build_pattern_library()
  pat = next(p for p in patterns if p.pattern_id == "lin_e_len2")
  cells = tuple(
      BuildingFootprintCell(x, y, i)
      for i, (x, y) in enumerate(sorted(pat.occupied_offsets))
  )
  expected = expected_footprint_coords(
      cells,
      anchor_coord=(0, 0),
      rotation=CardinalDirection.E,
  )
  assert expected == pat.occupied_offsets


def test_empty_footprint_raises_catalog_transform_error() -> None:
    with pytest.raises(CatalogTransformError, match="empty footprint_cells"):
        expected_footprint_coords(
            (),
            anchor_coord=(0, 0),
            rotation=CardinalDirection.E,
        )
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_catalog_geometry_transform.py -v
```

- [ ] **Step 3: Implement transform (no pattern_library import)**

```python
# django_apps/asteroid_lab/adapters/catalog_geometry_transform.py
"""Public catalog footprint rotation/translate (Track D+)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import BuildingFootprintCell
from django_apps.asteroid_lab.optimization.coords import Coord


class CatalogTransformError(ValueError):
    """Footprint could not be transformed."""


def _rotation_matrix(direction: CardinalDirection) -> tuple[tuple[int, int], tuple[int, int]]:
    if direction == CardinalDirection.E:
        return ((1, 0), (0, 1))
    if direction == CardinalDirection.N:
        return ((0, 1), (-1, 0))
    if direction == CardinalDirection.S:
        return ((0, -1), (1, 0))
    if direction == CardinalDirection.W:
        return ((-1, 0), (0, -1))
    raise CatalogTransformError(f"unsupported rotation {direction!r}")


def _rotate_point(direction: CardinalDirection, point: Coord) -> Coord:
    (a11, a12), (a21, a22) = _rotation_matrix(direction)
    return (a11 * point[0] + a12 * point[1], a21 * point[0] + a22 * point[1])


def expected_footprint_coords(
    footprint_cells: tuple[BuildingFootprintCell, ...],
    *,
    anchor_coord: Coord,
    rotation: CardinalDirection,
) -> frozenset[Coord]:
    if not footprint_cells:
        raise CatalogTransformError("empty footprint_cells")
    out: set[Coord] = set()
    for cell in footprint_cells:
        local: Coord = (cell.x, cell.y)
        rotated = _rotate_point(rotation, local)
        out.add((anchor_coord[0] + rotated[0], anchor_coord[1] + rotated[1]))
    return frozenset(out)


__all__ = ["CatalogTransformError", "expected_footprint_coords"]
```

- [ ] **Step 4: Run test — expect PASS**

```bash
python -m pytest tests/unit/asteroid_lab/test_catalog_geometry_transform.py -v
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/adapters/catalog_geometry_transform.py tests/unit/asteroid_lab/test_catalog_geometry_transform.py
git commit -m "feat(asteroid-lab): add public catalog footprint transform"
```

---

### Task 3 — Audit engine

**Files:**
- Create: `django_apps/asteroid_lab/adapters/catalog_placement_audit.py`
- Test: `tests/unit/asteroid_lab/test_catalog_placement_audit.py`

- [ ] **Step 1: Write failing taxonomy tests**

Use `BuildingCatalogSlice` factory from `test_catalog_footprint_policy.py` patterns. Build minimal `BundleCandidate` instances with/without `catalog_placement_ref`.

Test cases:

1. `test_audit_unmapped_when_ref_missing` — committed id, ref None → `unmapped_candidate_count=1`
2. `test_audit_matched_when_footprint_aligns` — ref + slice geometry matching `occupied_cells`
3. `test_audit_mismatch_when_footprint_differs`
4. `test_audit_not_in_slice_when_canonical_id_unknown`
5. `test_audit_skips_when_catalog_slice_none` — `checked_candidate_count=0`

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_catalog_placement_audit.py -v
```

- [ ] **Step 3: Implement `audit_catalog_placements`**

Signature:

```python
def audit_catalog_placements(
    committed_ids: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
    catalog_slice: BuildingCatalogSlice | None,
    *,
    catalog_slice_hash: str | None = None,
    catalog_slice_version: str | None = None,
) -> CatalogPlacementAudit:
```

Logic per committed id:

- No ref → increment unmapped; append `CATALOG_VARIANT_MAPPING_MISSING` to issue_codes set (dedupe sorted)
- Ref + variant missing in slice → `not_in_slice`
- Transform error → `transform_error`
- `expected != occupied` → `mismatch`
- else → `matched`

Return `catalog_validation_mode="observe_only"` always.

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/unit/asteroid_lab/test_catalog_placement_audit.py -v
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/adapters/catalog_placement_audit.py tests/unit/asteroid_lab/test_catalog_placement_audit.py
git commit -m "feat(asteroid-lab): observe-only catalog placement audit"
```

---

### Task 4 — Optional ref on `BundleCandidate`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/candidates/candidate_dtos.py`

- [ ] **Step 1: Add field with default None**

```python
from django_apps.asteroid_lab.contracts.catalog_placement import CatalogPlacementRef

@dataclass(frozen=True, slots=True)
class BundleCandidate:
  ...
  catalog_placement_ref: CatalogPlacementRef | None = None
```

- [ ] **Step 2: Run existing candidate tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_candidate_generator.py tests/unit/asteroid_lab/test_rttp_narrow_corridor.py -v
```

Expected: PASS (default None preserves behavior)

- [ ] **Step 3: Commit**

```bash
git add django_apps/asteroid_lab/optimization/candidates/candidate_dtos.py
git commit -m "feat(asteroid-lab): optional catalog_placement_ref on BundleCandidate"
```

---

### Task 5 — Pipeline + solver summary wiring

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`
- Modify: `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py` `PipelineResult` dataclass if needed
- Test: `tests/unit/asteroid_lab/test_rttp_pipeline_catalog_audit.py`

- [ ] **Step 1: Write failing test — validation unchanged on mismatch**

Monkeypatch or construct minimal pipeline path: inject candidate with ref mismatch into `candidates_by_id`, run `_run_v01_rttp_pipeline` with tiny `OptimizationInput` fixture (copy from existing pipeline tests). Assert:

- `pipeline_result.validation_passed` same as without audit (True if layout valid)
- step `rttp.catalog_placement_validation` in `algorithm_steps` with `mismatch_candidate_count >= 1`

If full pipeline test is heavy, test helper `record_catalog_placement_audit_step` + integration on `_run_v01` tail only.

- [ ] **Step 2: Add `RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION`**

```python
RTTP_CATALOG_PLACEMENT_VALIDATION = "rttp.catalog_placement_validation"
```

Add `catalog_placement_validation_step_from_audit(audit, *, catalog_slice_hash, catalog_slice_version)`.

Extend `build_rttp_solver_summary(..., catalog_placement_validation_step=None)` — insert after `catalog_slice_step`, before pipeline steps.

- [ ] **Step 3: Pipeline — after `validate_final_layout` in `_run_v01_rttp_pipeline` and macro path**

```python
from django_apps.asteroid_lab.adapters.catalog_placement_audit import audit_catalog_placements
from django_apps.asteroid_lab.contracts.building_catalog_slice_hash import catalog_slice_hash

audit = audit_catalog_placements(
    commit_result.committed_ids,
    candidates_by_id,
    inp.catalog_slice,
    catalog_slice_hash=catalog_slice_hash(inp.catalog_slice) if inp.catalog_slice else None,
    catalog_slice_version=inp.catalog_slice.slice_version if inp.catalog_slice else None,
)
# _record_pipeline_step(... step_id=RTTP_CATALOG_PLACEMENT_VALIDATION, passed=True always PR-1)
```

Store `catalog_placement_audit` on `PipelineResult` for entry to read, or embed only in `algorithm_steps`.

**Critical:** Do not AND audit into `validation_passed`.

- [ ] **Step 4: `solver_runtime_entry` — pass step from pipeline**

If audit step only in `algorithm_steps`, no entry change. If separate field on `PipelineResult`, thread into `build_rttp_solver_summary`.

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_rttp_pipeline_catalog_audit.py tests/unit/asteroid_lab/test_rttp_solver_summary.py -v
```

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/optimization/rttp_solver_summary.py django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/asteroid_lab/test_rttp_pipeline_catalog_audit.py tests/unit/asteroid_lab/test_rttp_solver_summary.py
git commit -m "feat(asteroid-lab): wire observe-only catalog placement audit step"
```

---

### Task 6 — Docs + inventory + current_plan

**Files:**
- Modify: `docs/adr/ADR-004-game-data-snapshot-boundary.md`
- Modify: `documents/index/document_inventory.md`
- Modify: `docs/domain/asteroid_game_data_snapshot.md`
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: ADR-004 — add subsection after Track D bullet**

```markdown
### Catalog placement audit (Track D+ PR-1, observe-only)

13. RTTP MAY run **read-only catalog placement audit** on committed candidates using `BuildingCatalogSlice` geometry and optional `CatalogPlacementRef`. PR-1 audit is **output-only** and MUST NOT change `validation_passed`, selection, fitness, macro, route probing, or replay semantics.
14. **Fail-closed catalog placement validation** for explicitly mapped candidates is deferred to Track D+ PR-2.
```

- [ ] **Step 2: `document_inventory.md` — new row**

| Track D+ catalog placement | `docs/superpowers/specs/2026-05-24-track-d-plus-catalog-placement-validation-design.md` | ACTIVE | PR-1 observe; PR-2 fail-closed |

- [ ] **Step 3: `current_plan.md` — Next focus bullet for PR-1 in progress**

- [ ] **Step 4: Commit**

```bash
git add docs/adr/ADR-004-game-data-snapshot-boundary.md documents/index/document_inventory.md docs/domain/asteroid_game_data_snapshot.md documents/ai/current_plan.md
git commit -m "docs: Track D+ PR-1 catalog placement audit contracts"
```

---

### Task 7 — Ops smoke E3 (manual checklist)

- [ ] **Step 1: Real slug E1**

```bash
python manage.py run_solver --slug copy-import-495e552c
```

Verify in persisted `solver_summary` JSON:

- `step_id` == `rttp.catalog_placement_validation`
- `metrics.catalog_validation_mode` == `observe_only`
- `metrics.catalog_slice_hash` present when catalog slice used

- [ ] **Step 2: Record in plan / current_plan when CLOSED**

---

## Plan self-review

| Spec requirement | Task |
|------------------|------|
| PR-1 observe-only mandatory text | Spec § Mandatory contract |
| No validation_passed change | Task 5 test |
| Public transform, no private import | Task 2 |
| CardinalDirection N/E/S/W | Task 1 |
| E3 pytest taxonomy | Task 3 |
| E3 real slug E1 | Task 7 |
| ADR + inventory | Task 6 |
| Connector mismatch not computed PR-1 | Task 3 (footprint only) |

No TBD placeholders in task steps.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-24-track-d-plus-pr1-catalog-placement-audit.md`.

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
**2. Inline Execution** — execute in this session with executing-plans checkpoints

**Follow-on:** PR-2 plan file `2026-05-24-track-d-plus-pr2-catalog-placement-validation.md` (not written until PR-1 merged).
