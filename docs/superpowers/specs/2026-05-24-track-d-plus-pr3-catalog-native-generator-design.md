# Track D+ PR-3 — Catalog-Native Candidate Generator

**Status:** Approved for spec (2026-05-24, post code review)  
**Parent:** [`2026-05-24-track-d-plus-catalog-placement-validation-design.md`](2026-05-24-track-d-plus-catalog-placement-validation-design.md)  
**Predecessor:** D+ PR-2 mapped fail-closed validation (merge to `master` before PR-3 implementation)  
**Roadmap:** Axis A7 — [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md)

## Mandatory contract

```text
PR-3 replaces production candidate enumeration: catalog slice → placement specs → generator.
Every normal BundleCandidate MUST have catalog_placement_ref set at generation time.
occupied_cells MUST match expected_footprint_coords for that ref (same transform as PR-1/2 audit).

lin_* / build_pattern_library() is TEST-ONLY (pytest marker + arch gate).
No production dual-path. No catalog_slice=None synthetic fallback in candidate_generator.

PR-3 does NOT change: selection, fitness, macro, replay semantics, commit-time reprobe,
validation repair, or final_validation bool refactor.
```

## 1. Problem

After D+ PR-1 (observe audit) and PR-2 (mapped fail-closed), production still generates candidates from synthetic `lin_*` patterns via `build_pattern_library()`. `BundleCandidate.catalog_placement_ref` defaults to `None`, so:

- Catalog validation cannot fail-closed on real footprint mismatches in production.
- `unmapped_candidate_count` stays high on real slugs despite a present `catalog_slice`.

**Gap:** generation must declare catalog mapping at creation time, not only at post-commit audit.

## 2. Approach (locked)

**Approach 1 only:** Adapter builds `CatalogPlacementSpec` from `BuildingCatalogSlice`; `generate_candidates` consumes specs. Rejected: Approach 2 (lin + post-match), Approach 3 (production dual-path).

## 3. Success criteria

| ID | Criterion |
|----|-----------|
| SC-1 | `candidate_generator.py` does not import or call `build_pattern_library()` |
| SC-2 | All `normal_candidates` have non-`None` `catalog_placement_ref` |
| SC-3 | `occupied_cells` equals catalog footprint transform for each normal candidate |
| SC-4 | `catalog_slice is None` or zero specs → `normal_count == 0` and pipeline candidate step `passed=False` |
| SC-5 | Ops smoke E5 on `copy-import-495e552c`: `normal_count > 0`, `unmapped_candidate_count == 0` |
| SC-6 | Arch: `optimization/*` does not import forbidden geometry types; generator arch test green |

## 4. Layer boundaries

| Layer | May import | Must not |
|-------|------------|----------|
| `contracts/catalog_candidate.py` | `Coord`, `CardinalDirection` | `BuildingFootprintCell`, connectors |
| `adapters/catalog_candidate_placements.py` | slice, `expected_footprint_coords`, transport policy public API | `pattern_library`, private `_rotation_matrix` |
| `adapters/catalog_output_attachment.py` | connectors, footprint transform helpers | `optimization/*` |
| `adapters/catalog_transport_policy.py` | slice, `TransportKind` | — |
| `optimization/candidates/candidate_generator.py` | specs, `CatalogPlacementRef`, adapters entrypoints | `build_pattern_library`, geometry snapshot types |

## 5. Contracts

### 5.1 `CatalogPlacementSpec` (`contracts/catalog_candidate.py`)

```python
@dataclass(frozen=True, slots=True)
class CatalogPlacementSpec:
    canonical_id: str
    rotation: CardinalDirection
    pattern_id: str
    occupied_offsets: frozenset[Coord]
    output_stub_offset: Coord
    output_dir: str  # "N" | "E" | "S" | "W"
    throughput_factor: int
    topology_kind: str = "catalog"
```

| Field | Rule |
|-------|------|
| `pattern_id` | `f"cat_{canonical_id.replace(':', '_')}_{rotation.value}"` — never `lin_*` |
| `occupied_offsets` | Relative to anchor; equals `expected_footprint_coords(..., anchor_coord=(0, 0), rotation=rotation)` |
| `topology_kind` | Always `"catalog"` |

### 5.2 `CatalogPlacementRef` at generation

```python
CatalogPlacementRef(
    canonical_id=spec.canonical_id,
    anchor_coord=anchor,
    rotation=spec.rotation,
)
```

| Invariant | Rule |
|-----------|------|
| INV-PR3-01 | Every normal `BundleCandidate` has `catalog_placement_ref is not None` |
| INV-PR3-02 | `ref.anchor_coord == candidate.anchor_coord` |
| INV-PR3-03 | `candidate.occupied_cells == expected_footprint_coords(variant footprint, anchor_coord=ref.anchor_coord, rotation=ref.rotation)` |

`BundlePattern` on the candidate is derived from the spec for replay/selection field compatibility only; catalog authority is footprint transform + ref.

### 5.3 Throughput factor v0.1 (aligned with `pattern_library`)

Matches `_THROUGHPUT_BY_EXT = (4, 8, 12, 16)` in `pattern_library.py`:

```python
def throughput_factor_for_footprint(cell_count: int) -> int:
    extension_count = min(3, max(0, cell_count - 1))
    return (4, 8, 12, 16)[extension_count]
```

| `len(footprint_cells)` | `extension_count` | `throughput_factor` |
|------------------------|-------------------|---------------------|
| 1 | 0 | 4 |
| 2 | 1 | 8 |
| 3 | 2 | 12 |
| 4+ | 3 (cap) | 16 |

No fitness/regret formula changes; dedupe signature may shift only because footprint-derived throughput replaces synthetic extension counts.

## 6. Adapters

### 6.1 Transport filter — public helper (PR-3 adds)

**File:** `adapters/catalog_transport_policy.py`

```python
def canonical_ids_for_transport_kind(
    catalog_slice: BuildingCatalogSlice,
    transport_kind: TransportKind,
) -> frozenset[str]:
    out: set[str] = set()
    for entry in catalog_slice.transport_registry:
        category = entry.transport_category.strip().lower()
        mapped = _TRANSPORT_CATEGORY_TO_KIND.get(category)
        if mapped is transport_kind:
            out.add(entry.building_variant_canonical_id)
    return frozenset(out)
```

`catalog_candidate_placements.py` **must** call this public helper only — **must not** import private `_TRANSPORT_CATEGORY_TO_KIND`.

### 6.2 Spec enumeration (`adapters/catalog_candidate_placements.py`)

```python
def build_catalog_placement_specs(
    catalog_slice: BuildingCatalogSlice,
    *,
    transport_kind: TransportKind,
) -> tuple[CatalogPlacementSpec, ...]:
```

**Filter order:**

1. `allowed = canonical_ids_for_transport_kind(catalog_slice, transport_kind)`
2. `variant_geometries` where `canonical_id in allowed` and `len(footprint_cells) > 0`
3. For each variant × `CardinalDirection` (N, E, S, W):
   - Build occupied via `expected_footprint_coords` at anchor `(0, 0)`; skip on `CatalogTransformError`
   - Build stub/dir via §6.3; skip when no output connector or stub ∈ occupied
   - Set `throughput_factor` via §5.3
4. Sort specs by `(canonical_id, rotation.value, pattern_id)` for determinism

Do not call `build_pattern_library()`.

### 6.3 Output stub / `output_dir` (`adapters/catalog_output_attachment.py`)

**Primary output connector** (variant-local frame, anchor `(0, 0)`):

```text
candidates = connectors where connector_role.lower() in ("output", "item_output")
                         or connector_role.lower().endswith("_output")
if empty → skip this variant×rotation (no spec)
primary = min(candidates, key=order_index)
```

**Direction rotation (required — matches `pattern_library` rotate semantics):**

```python
base_dir = tile_direction_to_cardinal(primary.tile_direction)  # East→E, etc.
rotated_dir = rotate_cardinal_direction(base_dir, rotation)

connector_local = (primary.position_x, primary.position_y)
base_stub = (
    connector_local[0] + UNIT_VECTOR[base_dir][0],
    connector_local[1] + UNIT_VECTOR[base_dir][1],
)
output_stub_offset = rotate_point(rotation, base_stub)
output_dir = rotated_dir.value
```

- `rotate_point` / `rotate_cardinal_direction`: same basis as `catalog_geometry_transform` (public); may live in `catalog_output_attachment.py` or shared module — **must not** import `pattern_library._rotation_matrix`.
- If `output_stub_offset` ∈ `occupied_offsets` (local) → skip spec.
- `tile_direction` parse failure → skip spec.
- **PR-3 does not** compute `catalog_connector_mismatch` validation (deferred).

### 6.4 `catalog_slice` absent or empty specs

| Condition | `generate_candidates` | Pipeline `rttp.candidate_pool` step |
|-----------|----------------------|-------------------------------------|
| `inp.catalog_slice is None` | `normal_candidates=()`, no synthetic fallback | `normal_count=0`, `passed=False` (existing code) |
| specs tuple empty | same | same |

**Important:** Empty normal pool does **not** automatically set `validation_passed=false` if nothing commits; PR-3 treats this as **candidate generation failure** (`passed=False` on candidate pool step), not catalog validation failure.

Ops E5 requires `normal_count > 0` on the real slug.

## 7. Generator changes (`optimization/candidates/candidate_generator.py`)

```text
if inp.catalog_slice is None:
    return CandidateGenerationResult(normal_candidates=(), rejected_candidates=())

specs = build_catalog_placement_specs(inp.catalog_slice, transport_kind=inp.transport_kind)
for anchor in anchors:
    for spec in specs:
        translate occupied / output_stub from spec offsets
        ref = CatalogPlacementRef(...)
        pattern = bundle_pattern_from_spec(spec)
        existing geometry + probe_route + dedupe unchanged
        BundleCandidate(..., catalog_placement_ref=ref)
```

- No `build_pattern_library()` import or call.
- `max_candidates` / dedupe signatures unchanged.

## 8. `lin_*` test isolation

| Mechanism | Detail |
|-----------|--------|
| `pattern_library.py` docstring | `SYNTHETIC TEST-ONLY — production uses catalog_candidate_placements` |
| pytest marker | `synthetic_lin_patterns` in `pyproject.toml` |
| Tests calling `build_pattern_library()` | `@pytest.mark.synthetic_lin_patterns` |
| Arch test | `tests/unit/asteroid_lab/test_catalog_native_generator_arch.py` — AST: `candidate_generator.py` has no `build_pattern_library` identifier |
| RTTP narrow gate | `-k "rttp and not macro_real_map and not synthetic_lin_patterns"` |

**No** runtime metric `synthetic_lin_pattern_count` in PR-3 (pipeline currently only `normal_count` / `rejected_count`). E5 does not assert this metric; arch gate is sufficient.

## 9. PR-2 validation linkage

PR-2 behavior (post-merge): unmapped ref → warning; mapped footprint error → `validation_passed=false`.

After PR-3 production path:

- Committed candidates should carry refs → `unmapped_candidate_count == 0` on real slug.
- Fail-closed applies to footprint mismatch, not mapping absence.

PR-3 does not modify `validate_catalog_placements` logic except as needed for imports/metrics wiring already in PR-2.

## 10. Ops smoke E5

**Slug:** `copy-import-495e552c`

```powershell
python manage.py run_solver --slug copy-import-495e552c
```

| ID | Assertion |
|----|-----------|
| E5-1 | Exit 0 |
| E5-2 | Step `rttp.catalog_placement_validation` present |
| E5-3 | `metrics.unmapped_candidate_count == 0` |
| E5-4 | `metrics.checked_candidate_count > 0` |
| E5-5 | Candidate pool step `metrics.normal_count > 0` and `passed == true` |
| E5-6 | `validation_passed == true`, `issue_codes == []` (healthy slug) |

**Not in E5:** `synthetic_lin_pattern_count` (no PR-3 pipeline metric).

## 11. Test matrix

| ID | File | Purpose |
|----|------|---------|
| T1 | `test_catalog_transport_policy.py` (extend) | `canonical_ids_for_transport_kind` |
| T2 | `test_catalog_candidate_placements.py` | enumeration, filter, sort |
| T3 | `test_catalog_output_attachment.py` | rotated stub/dir; N/S/W parity vs rotate pattern |
| T4 | `test_catalog_native_candidate_generator.py` | all normal have ref; slice None → empty normal |
| T5 | `test_catalog_native_generator_arch.py` | no `build_pattern_library` in generator |
| T6 | `test_catalog_consumption_boundaries.py` | optimization geometry import ban |
| T7 | `test_catalog_geometry_transform.py` | keep lin parity test under `synthetic_lin_patterns` |
| T8 | `test_rttp_candidate_generator.py` | migrate to catalog fixture or synthetic marker |

**Narrow gate:**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_transport_policy.py tests/unit/asteroid_lab/test_catalog_candidate_placements.py tests/unit/asteroid_lab/test_catalog_output_attachment.py tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py tests/unit/asteroid_lab/test_catalog_native_generator_arch.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map and not synthetic_lin_patterns" -v
python -m ruff check django_apps/asteroid_lab/contracts/catalog_candidate.py django_apps/asteroid_lab/adapters/catalog_transport_policy.py django_apps/asteroid_lab/adapters/catalog_candidate_placements.py django_apps/asteroid_lab/adapters/catalog_output_attachment.py django_apps/asteroid_lab/optimization/candidates/candidate_generator.py
```

## 12. File map

| Action | Path |
|--------|------|
| Create | `contracts/catalog_candidate.py` |
| Modify | `adapters/catalog_transport_policy.py` — `canonical_ids_for_transport_kind` |
| Create | `adapters/catalog_candidate_placements.py` |
| Create | `adapters/catalog_output_attachment.py` |
| Modify | `optimization/candidates/candidate_generator.py` |
| Modify | `optimization/candidates/pattern_library.py` — docstring only |
| Modify | `tests/unit/asteroid_lab/conftest.py` — `catalog_slice_minimal`, `greenfield_with_catalog` |
| Create | T1–T5 test modules |
| Modify | `pyproject.toml` — marker |
| Docs | `documents/Algorithm/asteroid_lab_03_candidate_generator.md` — catalog-native § |
| Docs | roadmap A7, `current_plan.md` — on PR-3 close |

## 13. Out of scope

- Synthetic lin production path, dual-path, post-match filtering
- `synthetic_lin_pattern_count` pipeline metric
- Connector mismatch fail-closed
- Macro / selection / fitness / regret / commit reprobe / LNS changes
- Replay as solver input; validation repair
- B-CS2 trunk ops smoke

## 14. Self-review

| Check | Status |
|-------|--------|
| Throughput `(4, 8, 12, 16)` matches `pattern_library` | Pass |
| Output stub rotates base stub + direction (not tile_direction-only) | Pass |
| Transport filter via public `canonical_ids_for_transport_kind` | Pass |
| E5 without `synthetic_lin_pattern_count`; arch gate instead | Pass |
| Empty pool = candidate step `passed=False`; E5 `normal_count > 0` | Pass |
| No TBD / placeholder sections | Pass |
| Single PR scope (generator + adapters) | Pass |
| Contradicts PR-1/2 mandatory contract | None |

## 15. Implementation order

1. Merge D+ PR-2 to `master`; sync `current_plan.md`.
2. Branch `feature/track-d-plus-pr3-catalog-native-generator` from `master`.
3. Implement per implementation plan (TDD).
4. Ops E5 + narrow gate + RTTP regression (excl. synthetic marker).
5. Close A7 on roadmap.
