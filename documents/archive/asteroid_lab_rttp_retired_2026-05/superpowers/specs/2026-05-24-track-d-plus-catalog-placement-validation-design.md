# Track D+ — Catalog Placement Validation (C → A)

**Status:** Approved 2026-05-24  
**Parent:** [`2026-05-24-track-d-catalog-footprint-connector-design.md`](2026-05-24-track-d-catalog-footprint-connector-design.md)  
**Predecessor (CLOSED):** Track D PR #63 (`building_catalog_slice_v2`, output-only `rttp.catalog_slice` metrics)  
**PR-1 plan:** [`2026-05-24-track-d-plus-pr1-catalog-placement-audit.md`](../plans/2026-05-24-track-d-plus-pr1-catalog-placement-audit.md)

## Mandatory contract (all PRs)

```text
Track D+ PR-1 is observe-only.
It must not affect validation_passed, run_success, selection, fitness, macro behavior, route probing, or replay semantics.

Track D+ PR-2 may fail validation only for explicitly catalog-mapped committed candidates.
Unmapped synthetic candidates remain warning/metric-only until PR-3.
```

## 1. Problem

Track D made catalog footprint and connector geometry available on `BuildingCatalogSlice` v2 and added output-only counts on `rttp.catalog_slice`. RTTP still cannot distinguish:

```text
(1) committed placement genuinely mismatches catalog footprint
(2) candidate has no catalog mapping (synthetic lin_* patterns)
```

Collapsing (1) and (2) into immediate `validation_passed = false` would make D+ fail for mapping incompleteness, not catalog correctness.

**Bottleneck:** the contract chain is incomplete:

```text
committed RTTP candidate ↔ catalog variant ↔ anchor + rotation ↔ occupied_cells
```

## 2. Strategy: C → A

| Phase | PR | Behavior |
|-------|-----|----------|
| **C** | PR-1 | Observe-only audit → `rttp.catalog_placement_validation` metrics |
| **A (gated)** | PR-2 | Fail-closed only when `catalog_placement_ref` is declared on a committed candidate |
| **B (deferred)** | PR-3 | Catalog-native candidate generator; mandatory mapping; synthetic `lin_*` test-only |

**Out of scope for D+ v1:** reconstruction / `BuildingSnapshot` on-map audit (Track D — separate authority).

## 3. Success criteria

### PR-1

```text
After commit, pipeline runs catalog_placement_audit on committed_ids only.
solver_summary includes rttp.catalog_placement_validation with catalog_validation_mode=observe_only.
validation_passed, run_success, selection, fitness, macro, route probe unchanged.
optimization/* does not import BuildingSnapshot or game_data geometry types (INV-D-04).
Ops smoke E3: real slug step + provenance; taxonomy proved in pytest fixtures.
```

### PR-2

```text
Explicitly mapped committed candidates with footprint mismatch → validation_passed false.
Unmapped candidates → metric/warning only (not fail-closed).
ValidationResult DTO + ValidationIssueCode StrEnum; pipeline keeps bool via adapter.
```

### PR-3 (future spec/plan)

```text
Production candidates require catalog_placement_ref.
candidate_generator rejects patterns without valid catalog geometry.
```

## 4. Scope matrix

| In scope | Out of scope |
|----------|----------------|
| `CatalogPlacementRef`, audit DTOs, issue StrEnum | Macro / selection / fitness / regret changes |
| `adapters/catalog_placement_audit.py` | Replay / NDJSON / solver_summary as algorithm input |
| `adapters/catalog_geometry_transform.py` (public transform) | Private import of `pattern_library._rotation_matrix` |
| Optional `catalog_placement_ref` on `BundleCandidate` (default `None`) | Connector mismatch logic in PR-1 (enum reserved; count 0) |
| PR-1: pipeline audit step + summary wiring | PR-3: generator catalog-native rewrite |
| PR-2: `ValidationResult` + mapped fail-closed | Reconstruction building placement audit |
| ADR-004 subsection + `document_inventory` row | Validation repair / route creation / topology mutation |

## 5. Data contracts

### 5.1 `CardinalDirection` (`contracts/catalog_placement.py`)

StrEnum aligned with RTTP pattern library wire (`"N"`, `"E"`, `"S"`, `"W"`). **Do not** use `genetic_sample.enums.Direction` (`"n"`/`"e"` lowercase) on this path.

```python
class CardinalDirection(StrEnum):
    N = "N"
    E = "E"
    S = "S"
    W = "W"
```

### 5.2 `CatalogPlacementRef`

```python
@dataclass(frozen=True, slots=True)
class CatalogPlacementRef:
    canonical_id: str
    anchor_coord: Coord  # optimization.coords tuple
    rotation: CardinalDirection
```

- PR-1: optional field on `BundleCandidate`: `catalog_placement_ref: CatalogPlacementRef | None = None`
- Generator unchanged in PR-1; tests/fixtures inject refs for taxonomy proof

### 5.3 `CatalogPlacementAudit` (PR-1 output)

```python
@dataclass(frozen=True, slots=True)
class CatalogPlacementAudit:
    catalog_validation_mode: Literal["observe_only"]
    checked_candidate_count: int
    matched_candidate_count: int
    mismatch_candidate_count: int
    unmapped_candidate_count: int
    not_in_slice_count: int
    transform_error_count: int
    issue_codes: tuple[str, ...]  # CatalogPlacementIssueCode.value only
```

Per-candidate classification: `matched` | `mismatch` | `unmapped` | `not_in_slice` | `transform_error`.

### 5.4 `CatalogPlacementIssueCode` (StrEnum)

| Member | PR-1 | PR-2 severity (when ref declared) |
|--------|------|-----------------------------------|
| `catalog_variant_mapping_missing` | unmapped metric | warning |
| `catalog_variant_not_in_slice` | metric | error |
| `catalog_footprint_mismatch` | metric | error |
| `catalog_anchor_transform_error` | metric | error |
| `catalog_rotation_unsupported` | metric | error |
| `catalog_connector_mismatch` | **not computed** | error (optional PR-2+) |

## 6. Geometry transform (Section 3 correction)

**Forbidden:** `from ...pattern_library import _rotation_matrix` (or any private symbol).

**Required:** `django_apps/asteroid_lab/adapters/catalog_geometry_transform.py`:

```python
def expected_footprint_coords(
    footprint_cells: tuple[BuildingFootprintCell, ...],
    *,
    anchor_coord: Coord,
    rotation: CardinalDirection,
) -> frozenset[Coord]:
    """Variant-local footprint → island coords. Raises CatalogTransformError on invalid input."""
```

- Matrix math duplicated from `pattern_library` canonical EAST basis with a **parity unit test** (`test_catalog_geometry_transform_matches_pattern_library_east_rotation`).
- `catalog_footprint_policy` may call `expected_footprint_coords`; it must not import `pattern_library`.

**Compare rule (v1):**

```text
expected = expected_footprint_coords(variant.footprint_cells, anchor, rotation)
actual   = candidate.occupied_cells
mismatch if expected != actual
```

`output_stub` is not subtracted from `occupied_cells` (stub is outside occupied set in linear patterns).

## 7. Architecture

```text
OptimizationInput.catalog_slice (existing)
  → run_rttp_pipeline
       → incremental_commit
       → validate_final_layout (unchanged bool in PR-1)
       → audit_catalog_placements(committed_ids, candidates_by_id, catalog_slice)
       → record rttp.catalog_placement_validation step on pipeline steps
  → solver_runtime_entry
       → build_rttp_solver_summary(..., catalog_placement_validation_step=...)
```

| Module | Responsibility |
|--------|----------------|
| `contracts/catalog_placement.py` | DTOs + `CatalogPlacementIssueCode` + `CardinalDirection` |
| `adapters/catalog_geometry_transform.py` | Public rotation/translate |
| `adapters/catalog_placement_audit.py` | Pure audit: refs + slice → `CatalogPlacementAudit` |
| `adapters/catalog_footprint_policy.py` | Existing summarize/lookup; may delegate transform |
| `optimization/rttp_solver_summary.py` | `catalog_placement_validation_step_from_audit` |
| `optimization/pipeline.py` | Call audit after validation; append step |
| `optimization/validation/final_validation.py` | PR-2: `ValidationResult` + mapped checks |

**Slice absent:** if `inp.catalog_slice is None`, skip audit (`checked_candidate_count=0`, `catalog_validation_mode=observe_only`, step `passed=True`).

## 8. PR-2 validation (Section 4)

Introduce:

```python
@dataclass(frozen=True, slots=True)
class ValidationIssue:
    issue_code: CatalogPlacementIssueCode  # extends to full ValidationIssueCode set in PR-2
    severity: ValidationSeverity
    candidate_id: str | None
    ...

@dataclass(frozen=True, slots=True)
class ValidationResult:
    passed: bool
    issues: tuple[ValidationIssue, ...]
```

Pipeline adapter:

```python
def validate_final_layout(...) -> bool:
    result = validate_final_layout_result(...)
    return result.passed
```

Top-level `validation_passed` remains `base_layout_ok and catalog_mapped_ok` where `catalog_mapped_ok` ignores unmapped candidates.

## 9. Ops smoke E3

**Real slug** `copy-import-495e552c` (E1):

```text
python manage.py run_solver --slug copy-import-495e552c
exit 0
algorithm_steps contains step_id rttp.catalog_placement_validation
metrics.catalog_validation_mode == observe_only
metrics.catalog_slice_hash present (when catalog slice present)
unmapped count may equal checked count (all synthetic) — allowed
```

**Pytest taxonomy** (E3 fixture proof): single test module proves `matched`, `mismatch`, `unmapped`, and `not_in_slice`/`transform_error` via injected `catalog_placement_ref` on synthetic candidates — no real-map requirement.

## 10. Invariants

| ID | Rule |
|----|------|
| INV-DP-01 | PR-1 must not change `validation_passed` or `run_success` semantics |
| INV-DP-02 | Audit reads `catalog_slice` + committed candidates only — no replay input |
| INV-DP-03 | `optimization/*` must not import `BuildingSnapshot` / forbidden geometry symbols |
| INV-DP-04 | No private imports from `pattern_library` |
| INV-DP-05 | Issue codes are StrEnum members — no free strings in metrics or validation |
| INV-DP-06 | Validation remains read-only (no route/placement/topology mutation) |
| INV-DP-07 | Reconstruction remains topology authority |

## 11. Documentation updates

| File | Change |
|------|--------|
| `docs/adr/ADR-004-game-data-snapshot-boundary.md` | Subsection: D+ PR-1 observe audit; PR-2 assert mapped placements |
| `documents/index/document_inventory.md` | Row: Track D+ catalog placement validation |
| `docs/domain/asteroid_game_data_snapshot.md` | D+ paragraph under Track D |
| `documents/Algorithm/asteroid_lab_08_validation.md` | PR-2: ValidationResult + catalog issue codes |
| `documents/ai/current_plan.md` | ACTIVE Track D+ PR-1 → CLOSED when merged |

## 12. Self-review

| Check | Status |
|-------|--------|
| Mandatory PR-1/PR-2 contract block present | Pass |
| C→A phasing explicit | Pass |
| Private rotation import forbidden; public transform module | Pass |
| CardinalDirection vs genetic_sample Direction | Pass |
| E3 smoke split real slug vs pytest | Pass |
| PR-3 deferred with clear boundary | Pass |
| Connector mismatch deferred PR-1 | Pass |
| No placeholder TBD sections | Pass |
