# RTTP Miner Output Transport Topology — Design Spec

**Date:** 2026-05-27  
**Status:** Approved (§1 + §2 with architect corrections)  
**Work classification:** contract change · implementation change (Phase 1) · follow-up (Phase 2)  
**Surfaces:** Lab replay overlay (A), `run_solver` commit path (B)  
**Branch (Phase 1):** `feat/rttp-miner-output-transport-topology-pr1`

> **Catalog footprint is evidence, not direct `occupied_offsets` authority.**

**Related:**

- [`documents/Algorithm/asteroid_lab_02_pattern_library.md`](../../../documents/Algorithm/asteroid_lab_02_pattern_library.md)
- [`documents/Algorithm/solver_runtime/00_core_principles.md`](../../../documents/Algorithm/solver_runtime/00_core_principles.md) §0.6
- [`documents/ai/plans/exhaustive_sample_gene_seed.md`](../../../documents/ai/plans/exhaustive_sample_gene_seed.md)
- [`2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md`](2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md)
- [`2026-05-26-rttp-confirmed-placement-footprint-design.md`](2026-05-26-rttp-confirmed-placement-footprint-design.md)
- [`2026-05-26-asteroid-game-data-transport-projection-design.md`](2026-05-26-asteroid-game-data-transport-projection-design.md)

**Implementation plan:** [`../plans/2026-05-27-rttp-miner-output-transport-topology-pr1.md`](../plans/2026-05-27-rttp-miner-output-transport-topology-pr1.md) — Gate Review micro-fixes merged; **Subagent-Driven** execution map; plan-only until implementation start.

---

## Problem

On catalog-native RTTP (PR-3), Lab overlay and committed placement previews show:

1. **R-direction (output-axis) cell polluted** — extension or miner footprint on the cell that must be **belt/pipe only** (`fixed_output_transport`).
2. **Expander not on N/W/S** — no real `extension_offsets`; catalog path inferred extensions from **footprint cell count** and `sorted_cells[0]` heuristics.

Root cause: `asteroid_equipment_projection` copies raw `footprint_cells` into `occupied_offsets`; `throughput_factor_for_footprint(len(footprint))` treats the R-adjacent catalog cell as “+1 extension”; `_bundle_pattern_from_spec` marks non-extractor occupied cells as extensions.

---

## Goals

| Phase | Delivers |
|-------|----------|
| **Phase 1** | Normalize miner topology; R cell = transport semantic only; `extension_offsets=()`; throughput from extension count; N/E/S/W invariant tests |
| **Phase 2** | N/W/S-only extension topology synthesis (separate spec/plan); no test/legacy generator import in production |

**Non-goals (Phase 1):**

- `incremental_commit` reprobe / reservation algorithm changes
- `game_data` dump export (Phase B transport projection)
- Exhaustive sample gene seed pipeline (surface C — unconfirmed)

---

## §1 — Coordinate invariants (canonical E, rotate with placement)

```text
extractor_offset              @ (0, 0)   ← equipment occupied
fixed_output_transport_offset @ unit(output_dir) from extractor   ← belt/pipe, NOT occupied
output_stub_offset            @ 2 * unit(output_dir) from extractor   ← route_probe_start
extension_offsets             ← explicit topology only (Phase 1: empty)
```

```text
occupied_offsets = {extractor_offset} ∪ extension_offsets
occupied_offsets ∩ {fixed_output_transport_offset, output_stub_offset} = ∅
```

| ID | Rule |
|----|------|
| INV-R-01 | `fixed_output_transport_offset ∉ occupied_offsets` |
| INV-R-02 | `output_stub_offset` is probe start; not equipment |
| INV-R-03 | `extension_offsets` must not include `extractor_offset + unit(output_dir)` |
| INV-R-05 | `output_stub_offset == fixed_output_transport_offset + unit(output_dir)` |
| INV-R-06 | Raw catalog footprint cells are **not** copied into `occupied_offsets` |
| INV-R-07 | `extension_offsets` from topology synthesis only, never footprint length |
| INV-R-08 | `throughput_factor = 4 × (1 + len(extension_offsets))`, capped at 16 |
| INV-R-09 | **Phase 1:** `extractor_offset == (0, 0)` after normalization; otherwise skip spec (fail-closed) |

**Phase boundary**

- **Phase 1:** `extension_offsets=()` unless a canonical pattern/topology source supplies them.
- **Phase 2:** N/W/S-only synthesis allowed; R/output-axis cells remain forbidden.

**Manual / CANON_MANUAL 2-cell evidence (fixed):**

```text
footprint_evidence = {(0, 0), (1, 0)}
fixed_output_transport_offset = (1, 0)
extractor_offset = (0, 0)
occupied_offsets = {(0, 0)}
throughput_factor = 4
```

---

## §2 — Architecture

### Layer map

| Module | Responsibility |
|--------|----------------|
| `catalog/miner_placement_topology.py` | Footprint evidence → `MinerPlacementTopology`; INV-R fail-closed |
| `catalog/asteroid_equipment_projection.py` | Variant×rotation → base topology (Phase 1: empty extensions) |
| `adapters/catalog_candidate_placements.py` | Topology → `CatalogPlacementSpec` |
| `optimization/candidates/bundle_pattern.py` | **`fixed_output_transport_offset`** explicit SoT |
| `optimization/candidates/candidate_generator.py` | Spec-driven pattern; geometry rejects |
| `optimization/materialization/placement_overlay_projection.py` | Separate `placement.*_fixed_output_transport` rows |
| `optimization/validation/final_validation.py` | `reserved_route_cells ∩ equipment_occupied = ∅`; cross-commit FOT assert — see hotfix spec |

**Forbidden:** production import of `build_pattern_library()` / `exhaustive_generator` for placement (PR-3 arch gate).

### DTO — `MinerPlacementTopology`

```python
@dataclass(frozen=True, slots=True)
class MinerPlacementTopology:
    canonical_id: str
    rotation: CardinalDirection
    extractor_offset: Coord
    extension_offsets: tuple[Coord, ...]
    fixed_output_transport_offset: Coord
    output_stub_offset: Coord
    output_dir: str
    throughput_factor: int
    footprint_evidence: frozenset[Coord]
```

- `occupied_offsets` = `frozenset({extractor_offset}) | frozenset(extension_offsets)` — recompute on emit; never trust raw footprint length.

### `CatalogPlacementSpec` (contract extension)

Add explicit fields (keep `occupied_offsets` derived for PR-3 audit compatibility):

- `extractor_offset`, `extension_offsets`, `fixed_output_transport_offset`, `output_stub_offset`
- `throughput_factor` from INV-R-08 only

**Deprecate for equipment:** `throughput_factor_for_footprint(cell_count)`.

### `BundlePattern` (explicit SoT)

Add:

```python
fixed_output_transport_offset: Coord
```

Align naming with `GeneTemplate.fixed_output_transport_offset` / `route_probe_start_offset` (= `output_stub_offset` in catalog path).

### Extractor selection (fail-closed — no `min(x,y)`)

```text
extractor_candidates = footprint_evidence - {fixed_output_transport_offset}

if len(extractor_candidates) == 1:
    extractor_offset = only(extractor_candidates)
elif explicit_catalog_anchor is defined for this variant:
    extractor_offset = explicit_catalog_anchor
else:
    skip spec (no candidate for this variant×rotation)
```

`explicit_catalog_anchor`: reserved hook for `island_extractor_defaults` provenance (Phase 1 implements single-candidate path only).

### Footprint normalization steps

1. `footprint_evidence` = rotated catalog footprint at anchor `(0,0)`.
2. `attachment_for_variant_rotation` → `output_dir`, connector local.
3. `output_stub_offset` = connector local + `unit(output_dir)` (existing PR-3 attachment).
4. `fixed_output_transport_offset` = `output_stub_offset - unit(output_dir)` (INV-R-05).
5. `extractor_offset` = fail-closed rule above.
6. `extension_offsets` = `()` (Phase 1).
7. Assert INV-R-01..08; on failure skip spec.

### Overlay semantics (A)

| Coord | `overlay_semantic_kind` |
|-------|-------------------------|
| extractor | `placement.{frame}_extractor` |
| extension | `placement.{frame}_extension` |
| fixed_output_transport | `placement.{frame}_fixed_output_transport` (**new**) |
| output_stub | `placement.{frame}_output_stub` |

### Commit / route reservation (B)

| Cell class | vs `reserved_route_cells` |
|------------|---------------------------|
| extractor | must not overlap equipment occupied |
| extension | must not overlap equipment occupied |
| fixed_output_transport | may appear in route materialization / reservation |
| output_stub | route probe start; may appear on path |

**Invariant (existing validation):**

```text
equipment_occupied_cells ∩ reserved_route_cells == ∅
```

`final_validation.validate_final_layout` already returns `False` when `reserved_route_cells & occupied_seen` is non-empty. Phase 1 adds explicit regression tests; **does not change** `incremental_commit.py`.

### `CandidateRejectReason` (enum extension)

| Value | Condition |
|-------|-----------|
| `FIXED_OUTPUT_TRANSPORT_IN_OCCUPIED` | INV-R-01 |
| `ROUTE_PROBE_START_IN_OCCUPIED` | stub ∈ occupied |
| `EXTENSION_ON_OUTPUT_AXIS` | INV-R-03 |

### Phase 2 — Extension topology (outline only)

- Allowlist: `Layout_ShapeMinerExtension`, `Layout_FluidMinerExtension`.
- **Production-safe topology only:** copy canonical N/W/S tree contract into a new adapter (e.g. `catalog/extension_topology_contract.py`) sourced from `pattern_library` linear E + rotation.
- **Must not** import `exhaustive_generator` or other test/legacy-only modules in `optimization/candidates/candidate_generator.py` production path.
- Separate spec: `2026-05-27-rttp-extension-topology-synthesis-design.md` (to be written after Phase 1 ships).

---

## Testing (Phase 1)

| Area | Requirement |
|------|-------------|
| Topology normalize | Manual 2-cell → occupied `{(0,0)}`, FOT `(1,0)`, stub `(2,0)`, throughput `4` |
| Rotation matrix | For `output_dir` in N,E,S,W: INV-R-05, empty occupied∩{FOT,stub}, no extension on output axis |
| Generator | No `extension` on FOT cell; `catalog_placement_ref` present |
| Overlay | FOT semantic on output-axis cell; not `*_extension` (≥ E + N + W cases) |
| Validation | `reserved_route_cells ∩ union(occupied)` empty on greenfield commit fixture |

---

## Doc cross-updates (Phase 1 PR)

- [`2026-05-27-rttp-commit-fot-cross-commit-hotfix.md`](2026-05-27-rttp-commit-fot-cross-commit-hotfix.md) — **PR1.5** cross-commit FOT (`INV-COMMIT-FOT-*`, `INV-VALIDATION-FOT-01`); not Phase 1 candidate scope
- `2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md` — §5.3 footprint throughput footnote
- `2026-05-26-asteroid-game-data-transport-projection-design.md` — equipment § footprint evidence
- `2026-05-26-rttp-confirmed-placement-footprint-design.md` — overlay semantic table row for `fixed_output_transport`

---

## Approval record

```text
§2 approved with corrections:
1. BundlePattern.fixed_output_transport_offset as explicit SoT.
2. Extractor: footprint_evidence - fixed_output_transport fail-closed (no min(x,y)).
3. Commit contract: equipment_occupied ∩ reserved_route_cells == ∅ (validation test, not commit edit).
4. Phase 2: no direct exhaustive_generator import in production.
5. N/E/S/W invariant matrix tests.
6. Gate review (plan): INV-R-09, Task 2/5/6/7 micro-fixes — see plan header § Pre-execution micro-fixes.
```
