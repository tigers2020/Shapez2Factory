# Reconstruction Field Cell Capacity Contract — Implementation Plan

> **STALE (2026-05-26):** Superseded by [`2026-05-26-reconstruction-complete-map-dto.md`](2026-05-26-reconstruction-complete-map-dto.md). Do not implement overlay `recon.cells` SoT steps below.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Invariant (do not drift)

**Use `asteroid_field_cells` as the only solver/Lab terrain upper-bound numerator. Do not change RTTP commit semantics, replay-as-input, or CANON ×16 reference rates.**

Do not change: `actual_committed_output_per_min` formula (PR-2b), route validation rules, incremental commit order, gene throughput_factor semantics.

**Goal:** `mineable_cells`, capacity platform count, and theoretical max throughput all use the same **asteroid field cell** set (`asteroid_shape_field` / `asteroid_fluid_field` on `recon.cells`), not mask-shrunk `confirmed_cells` and not `mineable_field_kind` miner inference.

**Architecture:** New `reconstruction/field_cells.py` SoT → wire `acceptance_topology`, `confidence`, `reconstruction_capacity_summary`, `optimization_input` → Lab DTO/JS footprint copy. Mask metrics remain diagnostic-only.

**Tech Stack:** Python 3.12+, Django 5.x, pytest-django, ruff, black, mypy `django_apps config src`, Django gettext + `scripts/build_locale_ko.py`

**Spec:** [`docs/superpowers/specs/2026-05-25-reconstruction-field-cell-capacity-contract-design.md`](../specs/2026-05-25-reconstruction-field-cell-capacity-contract-design.md)

**Branch:** `feat/reconstruction-field-cell-capacity-contract` (worktree recommended)

**Naming (reviewer Option A — this PR):** Keep JSON keys `confirmed_cell_count`, `capacity_upper_bound_platform_count`. **Document in code/docstrings:** both mean **asteroid field cell count** for solver paths. No `capacity_upper_bound_field_cell_count` rename in this PR (follow-up contract PR optional).

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `django_apps/asteroid_lab/reconstruction/field_cells.py` | SoT: `asteroid_field_cells_from_reconstruction`, `count_asteroid_field_cells_by_resource` |
| Create | `tests/unit/asteroid_lab/test_field_cells.py` | Transport/miner/fill exclusion & inclusion contract |
| Modify | `django_apps/asteroid_lab/reconstruction/acceptance_topology.py` | `mineable_cells` from field_cells SoT |
| Modify | `django_apps/asteroid_lab/reconstruction/confidence.py` | `confirmed_cells := field_cells`; `ambiguous_cells := ∅` on result |
| Modify | `django_apps/asteroid_lab/services/reconstruction_capacity_summary.py` | Count field cells; observability uses field set |
| Modify | `django_apps/asteroid_lab/optimization/reconstruction_adapter.py` | Assert/wire mineable via topo (field cells) |
| Modify | `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | Observability counts from field cells if needed |
| Modify | `tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py` | Field-count cap; remove confirmed-only fixtures |
| Modify | `tests/unit/asteroid_lab/test_reconstruction_topology.py` | External void not in field set |
| Modify | `tests/unit/asteroid_lab/test_optimization_input_adapter.py` | `mineable_cells == asteroid_field_cells` |
| Modify | `tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py` | Overlap vs field cells not mask-confirmed |
| Modify | `tests/unit/asteroid_lab/test_throughput_target.py` | PR-2c target scales with new recon max (intentional) |
| Modify | `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` | Fixture throughput from field counts |
| Modify | `django_apps/web/templates/web/partials/lab_stat_cards.html` | Footprint subtitle msgid |
| Modify | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Footprint numerator = field count |
| Modify | `scripts/build_locale_ko.py` | New disclaimer/footprint msgids |
| Modify | `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` | Template msgid regression |
| Modify | `documents/ai/current_plan.md` | Queue line when PR opens |

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Create branch**

```powershell
Set-Location F:\Python_Projects\shapez2Factory
git checkout master
git pull
git checkout -b feat/reconstruction-field-cell-capacity-contract
```

- [ ] **Step 2: Baseline narrow gate (pre-edit)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py tests/unit/asteroid_lab/test_throughput_target.py tests/unit/asteroid_lab/test_optimization_input_adapter.py -v --tb=short
```

Expected: PASS (establishes red-green baseline).

---

### Task 1: `field_cells` SoT module (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/reconstruction/field_cells.py`
- Create: `tests/unit/asteroid_lab/test_field_cells.py`

- [ ] **Step 1: Write failing tests (reviewer-required cases)**

Create `tests/unit/asteroid_lab/test_field_cells.py`:

```python
"""Asteroid field cell SoT — mineable/cap/placement numerator (transport excluded)."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cells_from_reconstruction,
    count_asteroid_field_cells_by_resource,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO


def _cell(x: int, y: int, *, cell_kind: str, transport_kind: str = "none") -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind=cell_kind,
        transport_kind=transport_kind,
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )


def _recon(*cells: DecodedCellDTO) -> ReconstructionResult:
    return ReconstructionResult(
        cells=cells,
        confirmed_cells=frozenset(),
        ambiguous_cells=frozenset(),
        external_void_cells=frozenset(),
        confidence_score=1.0,
        quality_tier="CONFIDENT_RECONSTRUCTION",
    )


def test_transport_cell_excluded_even_when_on_recon_cells() -> None:
    recon = _recon(
        _cell(0, 0, cell_kind="asteroid_shape_field"),
        _cell(1, 0, cell_kind="shape_belt", transport_kind="shape_belt"),
    )
    fields = asteroid_field_cells_from_reconstruction(recon)
    assert fields == frozenset({(0, 0)})
    assert count_asteroid_field_cells_by_resource(recon) == {"shape": 1, "fluid": 0}


def test_miner_extension_excluded_unless_converted_to_asteroid_field() -> None:
    recon = _recon(
        _cell(0, 0, cell_kind="shape_miner"),
        _cell(1, 0, cell_kind="shape_miner_extension"),
        _cell(2, 0, cell_kind="asteroid_shape_field"),
    )
    fields = asteroid_field_cells_from_reconstruction(recon)
    assert fields == frozenset({(2, 0)})


def test_inferred_fill_synthetic_asteroid_field_included() -> None:
    recon = _recon(
        DecodedCellDTO(
            x=3,
            y=3,
            layer=None,
            rotation=0,
            tile_type="",
            cell_kind="asteroid_shape_field",
            transport_kind="none",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={"_replay_synthetic": True},
        ),
    )
    assert asteroid_field_cells_from_reconstruction(recon) == frozenset({(3, 3)})


def test_fluid_field_counted_separately() -> None:
    recon = _recon(
        _cell(0, 0, cell_kind="asteroid_shape_field"),
        _cell(1, 0, cell_kind="asteroid_fluid_field"),
    )
    assert count_asteroid_field_cells_by_resource(recon) == {"shape": 1, "fluid": 1}
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_field_cells.py -v --tb=short
```

Expected: FAIL (`ModuleNotFoundError` or import error).

- [ ] **Step 3: Implement `field_cells.py`**

Create `django_apps/asteroid_lab/reconstruction/field_cells.py`:

```python
"""Single source of truth for reconstructed asteroid resource field cells."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.acceptance_topology import topology_coord_for_cell
from django_apps.asteroid_lab.reconstruction.evidence import ASTEROID_FIELD_KINDS
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_SHAPE_FIELD = "asteroid_shape_field"
_FLUID_FIELD = "asteroid_fluid_field"


def asteroid_field_cells_from_reconstruction(
    recon: ReconstructionResult,
    *,
    coord_frame: CoordFrame | None = None,
) -> frozenset[Coord]:
    frame = coord_frame if coord_frame is not None else recon.coord_frame
    out: set[Coord] = set()
    for cell in recon.cells:
        if cell.cell_kind not in ASTEROID_FIELD_KINDS:
            continue
        out.add(topology_coord_for_cell(cell, coord_frame=frame))
    return frozenset(out)


def count_asteroid_field_cells_by_resource(
    recon: ReconstructionResult,
    *,
    coord_frame: CoordFrame | None = None,
) -> dict[str, int]:
    frame = coord_frame if coord_frame is not None else recon.coord_frame
    counts = {"shape": 0, "fluid": 0}
    for cell in recon.cells:
        if cell.cell_kind == _SHAPE_FIELD:
            counts["shape"] += 1
        elif cell.cell_kind == _FLUID_FIELD:
            counts["fluid"] += 1
    return counts


__all__ = [
    "asteroid_field_cells_from_reconstruction",
    "count_asteroid_field_cells_by_resource",
]
```

Export from `django_apps/asteroid_lab/reconstruction/__init__.py` if package re-exports public API.

- [ ] **Step 4: Run tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_field_cells.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/reconstruction/field_cells.py tests/unit/asteroid_lab/test_field_cells.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add django_apps/asteroid_lab/reconstruction/field_cells.py django_apps/asteroid_lab/reconstruction/__init__.py tests/unit/asteroid_lab/test_field_cells.py
git commit -m "feat(asteroid_lab): add asteroid_field_cells reconstruction SoT"
```

---

### Task 2: Wire acceptance topology (remove `mineable_field_kind` path for mineable set)

**Files:**
- Modify: `django_apps/asteroid_lab/reconstruction/acceptance_topology.py`
- Test: `tests/unit/asteroid_lab/test_field_cells.py` (add integration test)

- [ ] **Step 1: Add failing test — topo mineable equals field_cells**

Append to `tests/unit/asteroid_lab/test_field_cells.py`:

```python
from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_reconstruction,
)


def test_acceptance_topology_mineable_equals_field_cells() -> None:
    recon = _recon(
        _cell(0, 0, cell_kind="asteroid_shape_field"),
        _cell(1, 0, cell_kind="shape_miner"),
    )
    topo = acceptance_topology_from_reconstruction(recon)
    assert topo.mineable_cells == asteroid_field_cells_from_reconstruction(recon)
```

- [ ] **Step 2: Run test — expect FAIL** (miner coord still in mineable via `mineable_field_kind`)

```powershell
python -m pytest tests/unit/asteroid_lab/test_field_cells.py::test_acceptance_topology_mineable_equals_field_cells -v --tb=short
```

- [ ] **Step 3: Patch `acceptance_topology_from_reconstruction`**

In `acceptance_topology.py`, replace mineable set build:

```python
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cells_from_reconstruction,
)

# inside acceptance_topology_from_reconstruction, after by_coord built:
mineable_f = asteroid_field_cells_from_reconstruction(result, coord_frame=frame)
```

Remove or keep `mineable_field_kind` only for other callers (do not use for `mineable_cells` set).

- [ ] **Step 4: Run field_cells + topology tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_field_cells.py tests/unit/asteroid_lab/test_reconstruction_topology.py -v --tb=short
```

Expected: PASS; `test_reconstruction_does_not_mark_external_void_as_mineable` still PASS.

- [ ] **Step 5: Commit**

```powershell
git add django_apps/asteroid_lab/reconstruction/acceptance_topology.py tests/unit/asteroid_lab/test_field_cells.py
git commit -m "fix(asteroid_lab): acceptance mineable uses asteroid field cells only"
```

---

### Task 3: Confidence — solver `confirmed_cells` = field cells (Option A)

**Files:**
- Modify: `django_apps/asteroid_lab/reconstruction/confidence.py`
- Create/Modify: `tests/unit/asteroid_lab/test_reconstruction_confidence_field_cells.py` (or extend existing confidence tests)

- [ ] **Step 1: Write failing test**

```python
"""Confidence result coords align with field cells (mask does not shrink solver set)."""

from django_apps.asteroid_lab.reconstruction.confidence import apply_confidence_to_result
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cells_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame


def _cell(x: int, y: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x, y=y, layer=None, rotation=0, tile_type="",
        cell_kind="asteroid_shape_field", transport_kind="none",
        has_nested_blueprint=False, nested_entry_count=0,
        nested_type_counts_json={}, raw_entry_json={},
    )


def test_apply_confidence_confirmed_equals_all_field_cells() -> None:
    base = ReconstructionResult(
        cells=(_cell(0, 0), _cell(1, 0), _cell(2, 0)),
        summary_json={},
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    out = apply_confidence_to_result(base, wall_coords=set(), interior_patch_coords=frozenset())
    expected = asteroid_field_cells_from_reconstruction(out)
    assert out.confirmed_cells == expected
    assert out.ambiguous_cells == frozenset()
```

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_confidence_field_cells.py -v --tb=short
```

- [ ] **Step 3: Implement in `apply_confidence_to_result`**

At end of function (after metrics), set:

```python
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cells_from_reconstruction,
)

field_cells = asteroid_field_cells_from_reconstruction(provisional)
# ... build final ReconstructionResult with:
confirmed_cells=field_cells,
ambiguous_cells=frozenset(),
```

Keep `merge_mask_agreement` for `summary_json` metrics (`ambiguous_ratio`, `confidence_score`) only — do not assign mask `confirmed` to `ReconstructionResult.confirmed_cells`.

Add module docstring note (Option A):

```text
confirmed_cells on ReconstructionResult == all asteroid field cells (solver SoT).
Mask-derived subsets are diagnostic-only in summary_json.
```

- [ ] **Step 4: Run confidence + pipeline tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_confidence_field_cells.py tests/unit/asteroid_lab/test_reconstruction_topology.py -v --tb=short
```

- [ ] **Step 5: Commit**

```powershell
git add django_apps/asteroid_lab/reconstruction/confidence.py tests/unit/asteroid_lab/test_reconstruction_confidence_field_cells.py
git commit -m "fix(asteroid_lab): confirmed_cells equals asteroid field cells for solver"
```

---

### Task 4: Capacity summary uses field counts (not `recon.confirmed_cells` mask)

**Files:**
- Modify: `django_apps/asteroid_lab/services/reconstruction_capacity_summary.py`
- Modify: `tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py`

- [ ] **Step 1: Add failing test — cap uses all fields not partial confirmed**

```python
def test_shape_capacity_uses_all_asteroid_field_cells_not_mask_confirmed() -> None:
    """Three shape fields; only one in confirmed_cells — cap must still be 3 × 120."""
    cells = tuple(
        DecodedCellDTO(
            x=i, y=0, layer=None, rotation=0, tile_type="",
            cell_kind="asteroid_shape_field", transport_kind="none",
            has_nested_blueprint=False, nested_entry_count=0,
            nested_type_counts_json={}, raw_entry_json={},
        )
        for i in range(3)
    )
    recon = ReconstructionResult(
        cells=cells,
        confirmed_cells=frozenset({(0, 0)}),  # stale mask-sized set
        ambiguous_cells=frozenset({(1, 0), (2, 0)}),
        external_void_cells=frozenset(),
        confidence_score=0.5,
        quality_tier="PARTIAL",
    )
    row = build_reconstruction_capacity_summary(recon=recon, resource_kind="shape")
    assert row["capacity_upper_bound_platform_count"] == 3
    assert row["max_throughput_per_min"] == "360.0000"
```

- [ ] **Step 2: Run — expect FAIL** (still reads `confirmed_cells`)

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py::test_shape_capacity_uses_all_asteroid_field_cells_not_mask_confirmed -v --tb=short
```

- [ ] **Step 3: Replace `count_confirmed_platforms_by_resource`**

Rename to `count_asteroid_field_cells_by_resource` delegating to `field_cells.count_asteroid_field_cells_by_resource` (or thin wrapper). Remove loop over `recon.confirmed_cells`.

Update `build_reconstruction_observability`:

```python
field_cells = asteroid_field_cells_from_reconstruction(recon)
by_resource = count_asteroid_field_cells_by_resource(recon)
obs = {
    ...
    "mineable_cell_count": len(field_cells),
    "confirmed_cell_count": len(field_cells),  # Option A: same value, documented
    "shape_confirmed_cell_count": by_resource["shape"],
    "fluid_confirmed_cell_count": by_resource["fluid"],
    ...
}
```

Docstring on `capacity_upper_bound_platform_count`: **field cell count**.

- [ ] **Step 4: Run capacity tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py -v --tb=short
```

- [ ] **Step 5: Commit**

```powershell
git add django_apps/asteroid_lab/services/reconstruction_capacity_summary.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py
git commit -m "fix(asteroid_lab): capacity upper bound uses asteroid field cell count"
```

---

### Task 5: PR-2c throughput target regression (intentional max increase)

**Files:**
- Modify: `tests/unit/asteroid_lab/test_throughput_target.py`
- Modify: `docs/superpowers/specs/2026-05-25-reconstruction-field-cell-capacity-contract-design.md` (already has migration note — add one line to plan gate if needed)

- [ ] **Step 1: Add test documenting target formula**

Append to `tests/unit/asteroid_lab/test_throughput_target.py`:

```python
def test_target_scales_with_reconstruction_max_field_based_cap() -> None:
    """PR-2c: target = reconstruction_max × percent/100 (intentional when field cap rises)."""
    recon_max = Decimal("75360")  # e.g. 628 shape fields × 120
    target = compute_target_throughput_per_min(
        reconstruction_max=recon_max,
        percent=10,
    )
    assert target == Decimal("7536")
```

- [ ] **Step 2: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_throughput_target.py -v --tb=short
```

Expected: PASS (pure math; documents contract for reviewers).

- [ ] **Step 3: Commit**

```powershell
git add tests/unit/asteroid_lab/test_throughput_target.py
git commit -m "test(asteroid_lab): document PR-2c target scales with field-based recon max"
```

---

### Task 6: Downstream adapters and fixture contract

**Files:**
- Modify: `tests/unit/asteroid_lab/test_optimization_input_adapter.py`
- Modify: `tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py`
- Modify: `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`

- [ ] **Step 1: Optimization input test**

Assert for a small recon fixture:

```python
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cells_from_reconstruction,
)

def test_optimization_input_mineable_equals_field_cells(sample_recon):
    inp = optimization_input_from_reconstruction(sample_recon)
    assert inp.mineable_cells == asteroid_field_cells_from_reconstruction(sample_recon)
```

- [ ] **Step 2: Update fixture contract**

In `test_reconstruction_fixture_contract.py`, replace `recon.confirmed_cells` overlap assertions with `asteroid_field_cells_from_reconstruction(recon)` vs `expected.mineable_cells` (≥95% overlap).

- [ ] **Step 3: Update lab summary fixture**

Adjust `test_lab_run_summary_nested_capacity_from_solver_summary` embedded `max_throughput_per_min` if platform count in fixture changes (8 fields → `960.0000` already; verify after Task 4).

- [ ] **Step 4: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_optimization_input_adapter.py tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v --tb=short
```

- [ ] **Step 5: Commit**

```powershell
git add tests/unit/asteroid_lab/test_optimization_input_adapter.py tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py
git commit -m "test(asteroid_lab): align adapters and fixtures with field cell mineable SoT"
```

---

### Task 7: Lab UI — footprint and disclaimer copy

**Files:**
- Modify: `django_apps/web/templates/web/partials/lab_stat_cards.html`
- Modify: `django_apps/web/templates/web/asteroid_miner_layout_solver.html` (disclaimer block if separate)
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- Modify: `scripts/build_locale_ko.py`
- Modify: `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py`

- [ ] **Step 1: Template msgids**

`lab_stat_cards.html` footprint subtitle:

```django
{% trans "field cells / map cells" %}
```

Disclaimer (compact, near cards) — add msgid:

```django
{% trans "Theoretical field capacity: all reconstructed asteroid field cells × base extractor unit (×4)" %}
```

- [ ] **Step 2: JS footprint numerator**

In `updateLabStatCards`, use field-aligned counts from `rec`:

```javascript
const fieldCount =
  rec.shape_confirmed_cell_count != null && rec.fluid_confirmed_cell_count != null
    ? Number(rec.shape_confirmed_cell_count) + Number(rec.fluid_confirmed_cell_count)
    : rec.confirmed_cell_count;
set(
  "lab-card-footprint-value",
  fieldCount !== dash && displayCells !== dash
    ? String(fieldCount) + " / " + String(displayCells)
    : dash,
);
```

(After backend Task 4, `confirmed_cell_count` equals total field cells; shape+fluid sum is equivalent.)

- [ ] **Step 3: UI string regression test**

```python
def test_lab_footprint_subtitle_documents_field_cells() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    assert "field cells / map cells" in text
```

- [ ] **Step 4: Regenerate KO locale**

```powershell
python scripts/build_locale_ko.py
```

- [ ] **Step 5: Commit**

```powershell
git add django_apps/web/templates/web/partials/lab_stat_cards.html django_apps/web/static/web/js/asteroid_miner_layout_lab.js scripts/build_locale_ko.py locale/ko/LC_MESSAGES/django.po locale/ko/LC_MESSAGES/djangojs.po tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py
git commit -m "feat(web): Lab footprint and disclaimer for field-cell capacity"
```

---

### Task 8: Full gate and manual slug check

**Files:** none

- [ ] **Step 1: Narrow asteroid_lab suite**

```powershell
python -m pytest tests/unit/asteroid_lab/test_field_cells.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py tests/unit/asteroid_lab/test_reconstruction_confidence_field_cells.py tests/unit/asteroid_lab/test_throughput_target.py tests/unit/asteroid_lab/test_optimization_input_adapter.py -v --tb=short
```

- [ ] **Step 2: Ruff + mypy**

```powershell
python -m ruff check django_apps/asteroid_lab/reconstruction/field_cells.py django_apps/asteroid_lab/reconstruction/acceptance_topology.py django_apps/asteroid_lab/reconstruction/confidence.py django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
python -m mypy django_apps/asteroid_lab/reconstruction/field_cells.py django_apps/asteroid_lab/reconstruction/acceptance_topology.py django_apps/asteroid_lab/reconstruction/confidence.py django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
```

- [ ] **Step 3: Manual Lab (reference slug)**

```powershell
python manage.py run_solver --slug <project-slug>
```

Verify:
- Resource Capacity `(N)` ≈ shape field tile count (not 32 mask subset).
- Theoretical Max ≈ N × 120 shapes/min (shape-primary).
- Footprint shows `field / map` with field numerator = N.
- Throughput target % rises vs old runs (intentional).

- [ ] **Step 4: Update `documents/ai/current_plan.md`** (one line: PR opened / in progress)

---

## Plan gate (pre-merge)

- [ ] `asteroid_field_cells_from_reconstruction` is sole mineable/cap numerator
- [ ] Transport excluded; miner/extension excluded unless `asteroid_*_field` on `recon.cells`
- [ ] Synthetic fill `asteroid_*_field` included
- [ ] Option A: JSON keys unchanged; docstrings state field-cell semantics
- [ ] PR-2c test documents `target = recon_max × percent/100` with higher field-based max
- [ ] No replay / prior summary as capacity input
- [ ] Full narrow pytest + ruff + mypy green

---

## Spec coverage self-review

| Spec requirement | Task |
|------------------|------|
| `field_cells.py` SoT | Task 1 |
| acceptance_topology | Task 2 |
| confidence confirmed = field cells | Task 3 |
| capacity summary | Task 4 |
| observability counts | Task 4 |
| OptimizationInput mineable | Task 2 + Task 6 |
| UI footprint/disclaimer | Task 7 |
| PR-2c intentional target change | Task 5 |
| Option A naming | Plan header + Task 3 docstring + Task 4 |
| mineable_field_kind regression tests | Task 1 + Task 2 |

No TBD placeholders in task steps.

---

## Execution handoff

Plan saved to [`docs/superpowers/plans/2026-05-25-reconstruction-field-cell-capacity-contract.md`](2026-05-25-reconstruction-field-cell-capacity-contract.md).

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session with executing-plans checkpoints  

Which approach?
