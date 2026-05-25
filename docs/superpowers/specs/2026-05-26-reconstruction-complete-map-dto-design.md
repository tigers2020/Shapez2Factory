# Reconstruction Complete Map DTO — Design Spec

**Date:** 2026-05-26  
**Status:** Approved (Contract Reviewer 2026-05-26 — four amendment items satisfied)  
**Amends:** [`2026-05-25-reconstruction-field-cell-capacity-contract-design.md`](2026-05-25-reconstruction-field-cell-capacity-contract-design.md) — field-cell SoT source only; prior “`recon.cells`” definition is **withdrawn**  
**Depends on:** PR-2a Lab capacity envelope · field-cell capacity contract (terminology) · `display_map.merge_reconstruction_display_cells`  
**Non-goals (this PR):** Renaming `ReconstructionResult.cells` → `overlay_cells`; silently stuffing complete map into `ReconstructionResult.cells`; using replay `full_map` rows as solver algorithm input

---

## Problem

`ReconstructionResult.cells` **reads** like the full reconstructed asteroid map but **means** a **sparse reconstruction overlay** (coords the pipeline overwrote). Product-facing artifacts use the **merged** map:

```text
reconstruction_complete_cells =
  merge(structural_cells_from_cleanup(cleanup), recon.overlay_cells)
```

Replay `reconstruction_final` / `step4_10_asteroid_map_complete` `full_map` and Lab Cell detail (`cell_kind: asteroid_shape_field` on hundreds of tiles) reflect this merged map. Capacity, Lab `asteroid_field_cell_count`, and `OptimizationInput.mineable_cells` currently count **`ReconstructionResult.cells` only**, producing e.g. **32** field cells while the complete map has **hundreds**.

This is not a display bug or a wrong arithmetic formula; it is a **DTO meaning mismatch** that misleads every downstream consumer.

---

## Root cause (locked)

| Name | Implied meaning | Actual meaning today |
|------|-----------------|----------------------|
| `ReconstructionResult.cells` | Complete reconstructed asteroid | Sparse overlay on cleanup structural base |
| `merged_display_cells_from_reconstruction` | (helper only) | **True** complete map for replay/persist/Lab |

Counting `asteroid_*_field` on overlay alone **violates** reconstruction-complete product rule and contradicts `step4_10` inspection.

---

## Architectural decision

### This PR

1. Introduce explicit product/solver DTO: **`ReconstructionCompleteMap`**
2. Build it from `cleanup + ReconstructionResult` via existing merge (same as replay final)
3. Route **capacity, topology mineable, optimization input, Lab observability** through complete map only
4. Document **`ReconstructionResult.cells` as overlay**; forbid overlay for terrain/capacity SoT
5. Add tests that block regression (overlay count ≪ complete field count on real fixtures)

### Follow-up PR (separate)

- Rename `ReconstructionResult.cells` → `overlay_cells`, and/or rename type to `ReconstructionOverlayResult`
- Global call-site migration; no silent semantic flip

### Explicitly rejected this PR

- **Silent B:** Assigning merged cells into `ReconstructionResult.cells` without rename/migration (high regression risk, hides the bug)

---

## DTO contracts

### `ReconstructionResult` (unchanged fields this PR; clarified semantics)

Pipeline stage output from `reconstruct_snapshot` / confidence attachment.

```python
@dataclass(frozen=True)
class ReconstructionResult:
    cells: tuple[DecodedCellDTO, ...]  # OVERLAY ONLY — see normative note below
    ...
```

**Normative (documentation + type docstring):**

```text
ReconstructionResult.cells is reconstruction overlay, not complete terrain.
It must not be consumed as the terrain source for capacity, topology mineable cells,
or OptimizationInput.mineable_cells.
```

**Follow-up (separate PR):** rename `ReconstructionResult.cells` → `ReconstructionResult.overlay_cells` (or type rename to `ReconstructionOverlayResult`). **Forbidden this PR:** silently assigning the merged complete map into `ReconstructionResult.cells`.

Confidence fields (`confirmed_cells`, `ambiguous_cells`, masks in `summary_json`) remain **diagnostic** on overlay/evidence; they must not shrink solver placement domain.

### `ReconstructionCompleteMap` (new)

Product- and solver-facing **single complete cell list** after cleanup structural base + overlay merge.

```python
@dataclass(frozen=True, slots=True)
class ReconstructionCompleteMap:
    """Merged cleanup structural map + reconstruction overlay (replay reconstruction_final parity)."""

    cells: tuple[DecodedCellDTO, ...]
    field_cells: frozenset[Coord]
    shape_field_cell_count: int
    fluid_field_cell_count: int
    external_void_cells: frozenset[Coord]
    coord_frame: CoordFrame
```

---

## Single factory (normative center)

All product/solver terrain semantics derive from **one factory**. Replay frames **must not** be read back in as solver input; they **must** use the **same merge** as this factory (already true in `reconstruction_frames.py` at `reconstruction_final`).

```python
def build_reconstruction_complete_map(
    *,
    cleanup: CleanupResult,
    recon: ReconstructionResult,
) -> ReconstructionCompleteMap:
    """Sole entry point for reconstruction-complete terrain SoT."""
    ...
```

`cleanup` is required for production solver/Lab paths (`ValueError` if missing). Tests may use minimal `CleanupResult` fixtures.

**Derived artifacts (same factory output — do not re-merge elsewhere):**

| Artifact | How produced |
|----------|----------------|
| Replay `reconstruction_final` / `step4_10_asteroid_map_complete` `full_map` | `merge_reconstruction_display_rows` / cells — **same merge as factory** at frame build time |
| Lab Cell detail (`cell_kind` on merged map) | UI reads replay `full_map` / overlay — **output-only**; must match factory cells at same run |
| `build_reconstruction_capacity_envelope` | `count_asteroid_field_cells_by_resource(complete_map)` |
| `OptimizationInput.mineable_cells` | `asteroid_field_cells_from_complete_map(complete_map)` |
| `build_reconstruction_observability` | `complete_map.shape_field_cell_count`, `fluid_field_cell_count`, `len(complete_map.cells)` |

**Parity invariant:**

```text
build_reconstruction_complete_map(cleanup, recon).cells
  ≡ merged_display_cells_from_reconstruction(cleanup, recon)
  ≡ replay reconstruction_final / step4_10 full_map cell set (modulo row dict vs DTO)

build_reconstruction_complete_map(...).field_cells
  ≡ { (x,y) | cell in complete_map.cells ∧ cell_kind ∈ asteroid field kinds }
```

`field_cells` and resource counts are computed **inside the factory** once; public helpers read the DTO, not `ReconstructionResult`.

---

## Canonical field-cell contract (replaces 2026-05-25 `recon.cells` wording)

```text
asteroid_field_cell :=
  coord (x, y) in ReconstructionCompleteMap.cells where
  cell_kind ∈ { asteroid_shape_field, asteroid_fluid_field }

asteroid_field_cells := ReconstructionCompleteMap.field_cells

mineable_cells (OptimizationInput) := asteroid_field_cells
installation_slots (terrain upper bound) := asteroid_field_cells
```

Exclusions unchanged: transport tiles, `external_void`, shell-only evidence not stamped as `asteroid_*_field`.

**Throughput upper bound:**

```text
max_throughput_per_min(resource) =
  ReconstructionCompleteMap.{shape|fluid}_field_cell_count
  × output_per_min(active MiningExtractionRule, throughput_factor=4)
```

---

## `field_cells.py` public API (complete map only)

**Withdrawn:** any public function taking `ReconstructionResult` and iterating `recon.cells` for SoT field counts.

**Normative public API:**

```python
def asteroid_field_cells_from_complete_map(
    complete_map: ReconstructionCompleteMap,
) -> frozenset[Coord]:
    """Returns ``complete_map.field_cells`` (identity; no overlay reads)."""

def count_asteroid_field_cells_by_resource(
    complete_map: ReconstructionCompleteMap,
) -> dict[str, int]:
    """Keys: shape, fluid — from ``complete_map.cells`` only."""
```

Implementation may delegate to `complete_map.field_cells` / stored counts. A private `_count_field_cells_in_decoded_cells(cells: Sequence[DecodedCellDTO])` may exist **only** inside `complete_map.py` for factory construction — **not** exported for capacity/topology/optimization callers.

**Tests only (optional):** `_overlay_field_cells_for_contract_tests(recon: ReconstructionResult)` to assert overlay ≪ complete on fixtures.

---

## Forbidden (normative)

```text
- Treating ReconstructionResult.cells as the complete reconstruction map
- Public field_cells / capacity / topology / optimization_input APIs taking ReconstructionResult for terrain SoT
- Counting terrain capacity or Lab asteroid_field_cell_count from overlay cells only
- Using replay persisted full_map JSON as solver/RTTP algorithm input (replay is output-only; factory shares merge, not readback)
- Silently assigning merged cells into ReconstructionResult.cells without rename/migration
- Introducing a second divergent merge implementation (must use display_map merge)
```

Allowed:

```text
- ReconstructionResult.cells for pipeline internals, confidence overlay metrics, trace fill_commit keys
- Replay full_map as UI/output artifact (not solver input)
```

---

## Consumer migration (this PR)

| Consumer | Before | After |
|----------|--------|-------|
| `field_cells.py` | `asteroid_field_cells_from_reconstruction(recon)` | **`asteroid_field_cells_from_complete_map(complete_map)`** only (public) |
| `build_reconstruction_capacity_*` | `recon` only | **`build_reconstruction_complete_map` → `ReconstructionCompleteMap`**; envelope takes `complete_map` |
| `acceptance_topology` | `result.cells` overlay | topology from **`complete_map.cells`** (private builder used inside factory) |
| `optimization_input_from_reconstruction` | overlay | **`cleanup` required** → `complete_map` → `mineable_cells = complete_map.field_cells` |
| `solver_runtime_entry` | `build_*_envelope(recon=recon)` | **`complete_map = build_reconstruction_complete_map(...)` once**; thread through |
| `build_reconstruction_observability` | overlay field count | **`complete_map`** counts only |
| Replay frame builder | merge at `reconstruction_final` | parity test: **`field_count` == complete shape+fluid** (same merge, not readback) |

**`ReconstructionResult` retained** for confidence, quality tier, `summary_json`, trace — not deleted.

---

## Module layout

```text
django_apps/asteroid_lab/reconstruction/
  complete_map.py          # ReconstructionCompleteMap + build_reconstruction_complete_map (factory)
                           # private _count_* on DecodedCellDTO tuple — factory only
  field_cells.py           # public API: *\_from_complete_map(complete_map) only
  acceptance_topology.py   # acceptance_topology_from_complete_map or from cells via factory
  display_map.py           # merge only — no capacity/topology consumers bypassing factory
```

Keep merge logic in `display_map.py`; **`complete_map.py` is the only orchestrator** for solver/Lab terrain SoT.

---

## Testing strategy

1. **Contract test:** On canon / Run-82-class fixture, `len(overlay field cells) < len(complete field cells)` and complete field count matches `snapshot_summary_from_rows(full_map_rows).field_count`.
2. **Parity test:** `build_reconstruction_complete_map` cells equal `merged_display_cells_from_reconstruction` tuple-for-tuple (sorted keys).
3. **Forbidden-path test:** Documented helper that counts overlay fields is only used in tests labeled `overlay`; production call graph grep or arch test optional.
4. **Regression:** Capacity envelope platform count equals complete shape (or fluid) field count, not 32 when complete map has hundreds.
5. **Optimization input:** `inp.mineable_cells == complete.field_cells`.

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Larger solver mineable domain → more RTTP work | Intended; matches product rule |
| Persisted solver summaries still show 32 until re-run | Document; no migration of old JSON |
| Duplicate merge if callers build complete map repeatedly | Build once in `solver_runtime_entry`; thread through |
| `cleanup is None` in rare tests | Explicit `ValueError` or test-only fixture providing cleanup |

---

## Follow-up (out of scope)

- Rename `ReconstructionResult.cells` → `overlay_cells`
- Optional `ReconstructionOverlayResult` type alias rename
- ADR in `docs/domain/` if team wants cross-link from architecture README

---

## Reviewer checklist (2026-05-26)

- [x] `field_cells.py` public API takes `ReconstructionCompleteMap` (not `ReconstructionResult`)
- [x] `build_reconstruction_complete_map(cleanup, recon)` is the single factory; step4_10 / final / Lab / capacity / mineable derive from same merge
- [x] 2026-05-25 Architecture / Data flow amended (withdrawn `recon.cells` SoT path)
- [x] `ReconstructionResult.cells` = overlay-only + explicit forbidden consumers

## Approval record

- **2026-05-26:** Reconstruction Contract Architect — direction approved.
- **2026-05-26:** Reconstruction Contract Reviewer — **Approved** after spec cleanup (four items above).
