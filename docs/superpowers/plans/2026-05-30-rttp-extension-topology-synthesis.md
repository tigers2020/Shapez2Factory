# RTTP Extension Topology Synthesis (S2b-1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Emit production-safe opposite-arm extension topologies (ext 0..3) on the catalog-native RTTP path so committed layouts can materialize `Layout_*MinerExtension` cells with correct `throughput_factor`.

**Architecture:** New `catalog/extension_topology_synthesis.py` builds deterministic linear chains on the **opposite** arm of `output_dir`. `asteroid_equipment_projection` multiplies each base rotation into four `ProjectedEquipmentSpec` rows. Phase 1 `normalize_miner_placement_topology` stays empty-extension. No `pattern_library` import in production.

**Tech stack:** Python 3.12+, Django `asteroid_lab`, pytest, ruff, existing INV-R tests.

**Design spec:** [`../specs/2026-05-30-rttp-extension-topology-synthesis-design.md`](../specs/2026-05-30-rttp-extension-topology-synthesis-design.md)

---

## File map

| Action | Path |
|--------|------|
| Create | `django_apps/asteroid_lab/catalog/extension_topology_synthesis.py` |
| Modify | `django_apps/asteroid_lab/catalog/asteroid_equipment_projection.py` |
| Modify | `django_apps/asteroid_lab/contracts/catalog_candidate.py` |
| Modify | `django_apps/asteroid_lab/catalog/projection_source.py` — add `topology_kind` to `ProjectedEquipmentSpec` |
| Modify | `django_apps/asteroid_lab/adapters/catalog_candidate_placements.py` — pass `topology_kind` through |
| Create | `tests/unit/asteroid_lab/test_extension_topology_synthesis.py` |
| Modify | `tests/unit/asteroid_lab/test_catalog_candidate_contracts.py` (pattern_id ext dimension) |
| Modify | `tests/unit/asteroid_lab/test_miner_placement_topology_extensions.py` (cross-ref S2b-1) |
| Verify | `tests/unit/asteroid_lab/test_rttp_core_recovery_gate_a.py` |
| Docs | Recovery spec §13 link (optional one-liner) |

---

### Task 1: `ExtensionTopologyKind` + opposite-arm synthesis (unit)

**Files:**
- Create: `django_apps/asteroid_lab/catalog/extension_topology_synthesis.py`
- Create: `tests/unit/asteroid_lab/test_extension_topology_synthesis.py`

- [x] **Step 1: Write failing tests for E-output opposite (W) arm**

```python
# tests/unit/asteroid_lab/test_extension_topology_synthesis.py
from django_apps.asteroid_lab.catalog.extension_topology_synthesis import (
    ExtensionTopologyKind,
    synthesize_opposite_arm_linear_topologies,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection


def test_e_output_opposite_arm_linear_offsets() -> None:
    topologies = synthesize_opposite_arm_linear_topologies(
        output_dir=CardinalDirection.E,
        max_extension_count=3,
    )
    assert len(topologies) == 4
    assert topologies[0].extension_count == 0
    assert topologies[0].topology_kind == ExtensionTopologyKind.NONE
    assert topologies[1].extension_offsets == ((-1, 0),)
    assert topologies[3].extension_offsets == ((-1, 0), (-2, 0), (-3, 0))


def test_e_output_extension_not_on_output_axis() -> None:
    unit_e = (1, 0)
    for topo in synthesize_opposite_arm_linear_topologies(output_dir=CardinalDirection.E):
        assert unit_e not in topo.extension_offsets
```

- [x] **Step 2: Run test — expect FAIL (module missing)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_extension_topology_synthesis.py -v --tb=short
```

- [x] **Step 3: Implement minimal synthesis module**

Implement `ExtensionTopologyKind`, `ExtensionTopology`, `synthesize_opposite_arm_linear_topologies`. Use `cardinal_unit_vector` from `adapters.catalog_geometry_transform` for arm steps. **Do not** import `pattern_library`.

```python
# Keep extension arm math in catalog production code only.
# Do not import optimization.candidates.pattern_library here:
# pattern_library contains test/legacy candidate patterns whose linear E variants
# place extensions on the output axis and are forbidden for S2b production synthesis.
```

Opposite arm mapping:

```python
_OPPOSITE: dict[CardinalDirection, CardinalDirection] = {
    CardinalDirection.E: CardinalDirection.W,
    CardinalDirection.W: CardinalDirection.E,
    CardinalDirection.N: CardinalDirection.S,
    CardinalDirection.S: CardinalDirection.N,
}
```

Build offsets with `unit = cardinal_unit_vector(opposite_arm)` → `(i+1)*unit` for `i in range(extension_count)`.

- [x] **Step 4: Run tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_extension_topology_synthesis.py -v --tb=short
```

- [x] **Step 5: Add N/E/S/W invariant matrix test**

One parametrized test: for each `output_dir`, ext 0..3, assert INV-R-03, FOT/stub not in `{extractor} ∪ extensions`, throughput 4/8/12/16 via `throughput_factor_for_extension_count`.

---

### Task 2: `catalog_pattern_id` extension dimension

**Files:**
- Modify: `django_apps/asteroid_lab/contracts/catalog_candidate.py`
- Modify: `tests/unit/asteroid_lab/test_catalog_candidate_contracts.py`

- [x] **Step 1: Failing test for `_ext{n}` suffix (including `_ext0`)**

```python
def test_catalog_pattern_id_always_includes_extension_count() -> None:
    from django_apps.asteroid_lab.contracts.catalog_candidate import catalog_pattern_id
    from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection

    assert catalog_pattern_id("shape_miner", CardinalDirection.E, extension_count=0) == (
        "cat_shape_miner_E_ext0"
    )
    assert catalog_pattern_id("shape_miner", CardinalDirection.E, extension_count=2).endswith(
        "_ext2"
    )
```

- [x] **Step 2: Run test — FAIL**

- [x] **Step 3: Extend signature (always `_ext{n}`)**

```python
def catalog_pattern_id(
    canonical_id: str,
    rotation: CardinalDirection,
    *,
    extension_count: int = 0,
) -> str:
    safe_id = canonical_id.replace(":", "_")
    return f"cat_{safe_id}_{rotation.value}_ext{extension_count}"
```

Update all call sites in `asteroid_equipment_projection` (Task 3). Grep `catalog_pattern_id` and fix tests expecting legacy IDs without `_ext0`.

- [x] **Step 4: Run catalog contract tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_candidate_contracts.py -v --tb=short
```

---

### Task 3: Wire projection — 4 specs per rotation

**Files:**
- Modify: `django_apps/asteroid_lab/catalog/asteroid_equipment_projection.py`
- Modify: `django_apps/asteroid_lab/catalog/projection_source.py` — `ProjectedEquipmentSpec.topology_kind: str`
- Modify: `django_apps/asteroid_lab/adapters/catalog_candidate_placements.py` — map `topology_kind` → `CatalogPlacementSpec`

**`topology_kind` propagation (normative):**

```text
ExtensionTopology.topology_kind
  → ProjectedEquipmentSpec.topology_kind
  → CatalogPlacementSpec.topology_kind
  → BundlePattern.topology_kind
```

- [x] **Step 1: Failing test — projected spec count**

Reuse slice builder from `tests/unit/asteroid_lab/test_asteroid_equipment_projection.py`:

```python
# tests/unit/asteroid_lab/test_extension_topology_synthesis.py
from django_apps.asteroid_lab.catalog.asteroid_equipment_projection import (
    list_equipment_placement_specs,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def test_manual_shape_miner_emits_four_specs_per_rotation(
    catalog_slice_with_shape_miner: object,
) -> None:
    sl = catalog_slice_with_shape_miner  # same fixture as test_asteroid_equipment_projection
    specs = list_equipment_placement_specs(sl, transport_kind=TransportKind.SHAPE_BELT)
    e_specs = [s for s in specs if s.rotation is CardinalDirection.E]
    assert len(e_specs) == 4
    assert {s.throughput_factor for s in e_specs} == {4, 8, 12, 16}
    assert all(s.pattern_id.endswith(f"_ext{n}") for n, s in zip(range(4), sorted(e_specs, key=lambda r: r.throughput_factor)))
```

Add `catalog_slice_with_shape_miner` fixture to this test module (copy minimal `BuildingCatalogSlice` from `test_asteroid_equipment_projection.py`) if not importing conftest.

- [x] **Step 2: Refactor `_specs_from_geometry`**

After `normalize_miner_placement_topology` succeeds:

```python
for ext_topo in synthesize_opposite_arm_linear_topologies(
    output_dir=rotation,
    max_extension_count=3,
):
    occupied = frozenset({topo.extractor_offset, *ext_topo.extension_offsets})
    # re-validate INV-R with merged offsets; skip if fail-closed
    specs.append(ProjectedEquipmentSpec(...))
```

Set `throughput_factor=throughput_factor_for_extension_count(ext_topo.extension_count)`, `pattern_id=catalog_pattern_id(..., extension_count=ext_topo.extension_count)`, `topology_kind=ext_topo.topology_kind.value`.

- [x] **Step 3: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_extension_topology_synthesis.py tests/unit/asteroid_lab/test_catalog_candidate_contracts.py -v --tb=short
```

---

### Task 4: Candidate generator + overlay smoke

**Files:**
- Modify: `tests/unit/asteroid_lab/test_rttp_catalog_native_generator.py` (or nearest existing PR-3 test)
- Verify: `tests/unit/asteroid_lab/test_placement_overlay_projection.py`

- [x] **Step 1: Assert normal pool includes ext≥1 throughput factors**

After `generate_candidates`, at least one admitted candidate has `throughput_factor > 4` on a fixture with catalog slice.

- [x] **Step 2: Overlay test — extension cell kind**

Existing `test_placement_overlay_projection` pattern: committed bundle with `extension_offsets=((-1,0),)` projects `Layout_ShapeMinerExtension` (not FOT cell).

- [x] **Step 3: Narrow RTTP pytest**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "extension_topology or catalog_candidate or placement_overlay" -v --tb=short
```

---

### Task 5: Import boundary + Gate A regression

**Files:**
- Create or extend: `tests/unit/architecture/test_optimization_contamination_gates.py` (optional token)

- [x] **Step 1: Grep guard (optional architecture test)**

Assert `candidate_generator.py` source does not contain `pattern_library` or `exhaustive_generator`.

- [x] **Step 2: Gate A**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_core_recovery_gate_a.py -v --tb=short
```

- [x] **Step 3: Broader RTTP slice**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k rttp -v --tb=short
python -m ruff check django_apps/asteroid_lab/catalog django_apps/asteroid_lab/contracts/catalog_candidate.py django_apps/asteroid_lab/optimization/candidates/candidate_generator.py
```

---

### Task 6: Evidence recapture (manual / ops)

**Files:**
- Run: `python manage.py capture_rttp_recovery_evidence` (existing command)
- Output: `docs/superpowers/reports/2026-05-30-rttp-core-recovery-evidence-after-s2b1.json`

- [x] **Step 1: Import recovery test map if needed**

- [x] **Step 2: Capture both Gate A primary slugs**

- [x] **Step 3: Record in report**

Document `visible_extension_cell_count`, route-feasible ext≥1 count, and whether conditional extension criterion met.

**Do not** mark Gate B closed from this task.

---

### Task 7: Doc sync

- [x] Update [`2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`](../specs/2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md) §13 — link S2b-1 spec/plan; note A2 track gate partial until conditional extension evidence
- [x] Update [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md) — S2b-1 **CLOSED 2026-05-30** with plan link + after-s2b1 evidence

---

## Verification summary

| Gate | Command |
|------|---------|
| Iteration | `python -m pytest tests/unit/asteroid_lab/test_extension_topology_synthesis.py tests/unit/asteroid_lab/test_rttp_core_recovery_gate_a.py -v --tb=short` |
| RTTP narrow | `python -m pytest tests/unit/asteroid_lab/ -k rttp -v --tb=short` |
| Contamination | `powershell -File scripts/test_optimization_contamination.ps1` |

## Out of plan (S2b-2)

- N/S perpendicular arm families
- game_data footprint extension derivation
- Gate B selection / A4-2
- EVTC-6b validation wiring
