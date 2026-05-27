# RTTP Extension Topology Synthesis (S2b) — Design Spec

**Document type:** Canonical Phase 2 design (miner output transport topology)  
**Status:** Approved (2026-05-30, Release Controller conditional)  
**Work classification:** contract change · implementation change  
**Parent:** [`2026-05-27-rttp-miner-output-transport-topology-design.md`](2026-05-27-rttp-miner-output-transport-topology-design.md) Phase 2  
**Recovery program:** [`2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`](2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md) — S2b / A2 track gate  
**Implementation plan:** [`../plans/2026-05-30-rttp-extension-topology-synthesis.md`](../plans/2026-05-30-rttp-extension-topology-synthesis.md)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Korean title (reference):** RTTP 확장기 topology 합성 (S2b)

---

## §1 — Executive summary

Phase 1 ([`2026-05-27-rttp-miner-output-transport-topology-design.md`](2026-05-27-rttp-miner-output-transport-topology-design.md)) fixed **FOT / output stub / empty extensions** on the catalog-native path. Representative maps still show **`visible_extension_cell_count = 0`** and **`missing_extensions`** in recovery evidence because **no production-safe extension topology** is emitted.

**S2b** adds a **production-safe synthesizer** (`catalog/extension_topology_synthesis.py`) that supplies `extension_offsets` and `throughput_factor` without importing `pattern_library`, `exhaustive_generator`, or other test-only modules.

**S2b-1 (this spec):** For each miner rotation, emit **`extension_count` 0..3** on the **opposite arm** of `output_dir` only → **4 placement specs per rotation**.

**S2b-2 (deferred):** Perpendicular **N/S arm families** (and multi-arm trees) when evidence shows opposite-arm-only is insufficient for Gate B.

**Gate B** (throughput utilization toward `placement_goal_count`) remains **out of scope** here; recapture evidence **after** S2b-1 lands.

---

## §2 — Goals and non-goals

### Goals

| ID | Goal |
|----|------|
| G1 | Production path emits valid `extension_offsets` (0..3) with INV-R invariants |
| G2 | `throughput_factor = throughput_factor_for_extension_count(len(extension_offsets))` |
| G3 | Overlay materializes `Layout_ShapeMinerExtension` / `Layout_FluidMinerExtension` on extension cells |
| G4 | Candidate generator admits specs without `pattern_library` import |
| G5 | Recovery evidence can clear `missing_extensions` **when** ext≥1 candidates are route-feasible and committed |

### Non-goals (S2b-1)

| Item | Disposition |
|------|-------------|
| FOT / belt·pipe install changes | EVTC / FOT PR-1/2 closed; bugfix only |
| EVTC-6b `route_not_shortest_feasible` validation wiring | Separate slice |
| FOT PR-3 ring/trunk probe scoring | After Gate B evidence |
| Gate B selection / regret / A4-2 tuning | Follow-on spec after S2b evidence |
| `final_validation` repair | Forbidden (B-CS3) |
| game_data footprint-derived extension trees | S2b-2+ if needed |
| N/S perpendicular arm enumeration | **S2b-2** |
| `incremental_commit` algorithm changes | Unless proven required by S2b tests |

---

## §3 — Geometry invariants (normative)

Canonical local frame: `extractor_offset = (0, 0)` after normalization (INV-R-09).

```text
unit = cardinal_unit_vector(output_dir)
fixed_output_transport_offset = extractor_offset + unit
output_stub_offset = fixed_output_transport_offset + unit

occupied_offsets = {extractor_offset} ∪ extension_offsets
occupied_offsets ∩ {fixed_output_transport_offset, output_stub_offset} = ∅
```

### Allowed extension arms (required terminology)

**Do not** describe extensions as “perpendicular to output axis only.” For E-output, **W (opposite / backward along the output line) is allowed** and is the S2b-1 canonical arm.

```text
allowed_extension_arms(output_dir) = {N, E, S, W} \ {output_dir}

extension_offsets must lie on cells reachable only via offsets built from
allowed_extension_arms(output_dir), and must satisfy INV-R-03.
```

| `output_dir` | Forbidden arm (INV-R-03) | S2b-1 canonical arm (opposite) | S2b-2 (deferred) |
|--------------|--------------------------|--------------------------------|------------------|
| E | E (+x forward) | W | N, S |
| W | W | E | N, S |
| N | N | S | E, W |
| S | S | N | E, W |

**INV-R-03 (explicit):**

```text
extractor_offset + unit(output_dir) ∉ extension_offsets
```

**E-output S2b-1 example (opposite / W-arm linear):**

| `extension_count` | `extension_offsets` (local) |
|-------------------|-----------------------------|
| 0 | `()` |
| 1 | `(-1, 0)` |
| 2 | `(-1, 0), (-2, 0)` |
| 3 | `(-1, 0), (-2, 0), (-3, 0)` |

FOT remains `(1, 0)`, stub `(2, 0)` — extensions do **not** occupy output-axis cells.

**Contrast (forbidden in production):** `pattern_library` `lin_E_len1` places extension at `(1, 0)` on the output axis. That pattern remains **test-only**; production synthesis must not copy it.

| ID | Rule |
|----|------|
| INV-R-01 | FOT ∉ occupied |
| INV-R-02 | Stub ∉ occupied |
| INV-R-03 | No extension on `extractor + unit(output_dir)` |
| INV-R-05 | Stub = FOT + unit(output_dir) |
| INV-R-07 | Extensions from synthesizer only |
| INV-R-08 | `throughput_factor = 4 × (1 + len(extension_offsets))`, max 16 |

---

## §4 — Architecture (Approach A)

### Module boundary

| Module | Phase | Responsibility |
|--------|-------|----------------|
| `catalog/miner_placement_topology.py` | 1 | Footprint → base topology; **`extension_offsets=()`** unchanged |
| `catalog/extension_topology_synthesis.py` | **2 NEW** | Deterministic opposite-arm linear topologies per `output_dir` |
| `catalog/asteroid_equipment_projection.py` | 2 | Base topo × synthesis → `ProjectedEquipmentSpec` list |
| `adapters/catalog_candidate_placements.py` | — | Pass-through to `CatalogPlacementSpec` |
| `optimization/candidates/candidate_generator.py` | — | Existing INV-R rejects; **no** `pattern_library` import |
| `optimization/materialization/placement_overlay_projection.py` | — | Extension rows from `pattern.extension_offsets` |
| `optimization/validation/layout_connectivity_validation.py` | — | Read-only; no repair |

### `ExtensionTopologyKind` (no free-form strings)

```python
class ExtensionTopologyKind(StrEnum):
    NONE = "none"
    LINEAR_OPPOSITE_ARM = "linear_opposite_arm"
```

Module-level aliases are acceptable if `StrEnum` is deferred, but replay/metrics must use these values only.

### Synthesis API (conceptual)

```python
@dataclass(frozen=True, slots=True)
class ExtensionTopology:
    extension_offsets: tuple[Coord, ...]
    extension_count: int
    topology_kind: ExtensionTopologyKind
    synthesis_arm: CardinalDirection  # arm used for linear chain (opposite of output_dir in S2b-1)

def synthesize_opposite_arm_linear_topologies(
    *,
    output_dir: CardinalDirection,
    max_extension_count: int = 3,
) -> tuple[ExtensionTopology, ...]:
    """Return exactly max_extension_count + 1 topologies: ext 0..max on opposite arm."""
```

Rotation / unit vectors use `adapters.catalog_geometry_transform` (`cardinal_unit_vector`, `rotate_coord`) — production-safe. **Do not** import `optimization.candidates.pattern_library` (test/legacy; `lin_E_len*` places extensions on the output axis). If helpers are duplicated locally, include a comment forbidding `pattern_library` import (see implementation plan Task 1).

### Emission cardinality (S2b-1)

```text
Per (canonical_id, rotation):
  4 ProjectedEquipmentSpec  (extension_count 0, 1, 2, 3)
  × 4 rotations
  = 16 specs per miner layout (Shape or Fluid)
```

**Not** 10 specs (that count applies to S2b-2 when N/W/S arm families are all emitted).

### `pattern_id`

Extend `catalog_pattern_id` to include extension dimension **always** (including `n = 0`):

```text
cat_{safe_canonical_id}_{rotation}_ext{n}
```

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

`n` = `len(extension_offsets)`. No legacy ID without `_ext0` — S2b is a contract change; update tests that assumed `cat_*_{rot}` without suffix.

### `topology_kind` propagation (required DTO chain)

```text
ExtensionTopology.topology_kind
  → ProjectedEquipmentSpec.topology_kind   (add field)
  → CatalogPlacementSpec.topology_kind     (existing)
  → BundlePattern.topology_kind            (via candidate_generator)
  → replay / overlay / debug metrics       (optional surface)
```

Minimum required for S2b-1: all four DTO layers above must carry `topology_kind` (`ExtensionTopologyKind` value) even when not exposed in persisted replay JSON.

---

## §5 — Data flow

```text
BuildingCatalogSlice
  → normalize_miner_placement_topology (ext=())
  → synthesize_opposite_arm_linear_topologies(output_dir)
  → merge into ProjectedEquipmentSpec (occupied, throughput_factor, pattern_id)
  → build_catalog_placement_specs
  → generate_candidates (probe + INV-R validation)
  → commit → placement_overlay_projection
  → layout_connectivity_validation (read-only)
```

**Forbidden:**

```text
optimization/candidates/candidate_generator.py  →  pattern_library
optimization/candidates/candidate_generator.py  →  exhaustive_generator
throughput from len(footprint_cells) or throughput_factor_for_footprint in production path
```

---

## §6 — Success criteria

### S2b-1 unit / contract

| Test area | Requirement |
|-----------|-------------|
| Synthesis | E/W/N/S: ext 0..3 opposite-arm offsets; INV-R-01..03, 05, 07, 08 |
| Reject | No topology with extension on `extractor + unit(output_dir)` |
| Throughput | 4, 8, 12, 16 for ext 0..3 |
| pattern_id | Distinct per `ext{n}`; deterministic ordering |
| Import boundary | Architecture or unit test: production modules do not import `pattern_library` |

### S2b-1 integration

| Criterion | Rule |
|-----------|------|
| Gate A regression | `test_rttp_core_recovery_gate_a.py` stays green |
| Tiny pass-capable | `rttp-cert-candidate-tiny-passable-v2` unchanged |
| Extensions visibility | **Conditional** (see below) |

### Conditional extension visibility (recovery)

```text
IF at least one route-feasible candidate with extension_count >= 1 exists
   AND that candidate is selected/committed on the representative slug,
THEN visible_extension_cell_count >= 1.

IF no ext>=1 candidate is route-feasible,
THEN recovery evidence MUST record why (e.g. route_feasible_shortfall,
anchor_overlap, NOT_REACHABLE) — missing_extensions alone is not a product fail.
```

Do **not** treat `visible_extension_cell_count >= 1` as an absolute pass on every run.

### Gate B

Recapture [`docs/superpowers/reports/2026-05-30-rttp-core-recovery-evidence-*.json`](../reports/) **after** S2b-1 merge. Expect improved `throughput_factor` distribution; **467 commits not required** for S2b close.

---

## §7 — S2b-2 outline (deferred)

When opposite-arm-only evidence is insufficient:

- Emit additional `ExtensionTopologyKind` values (e.g. `LINEAR_PERPENDICULAR_ARM`) for N and S arms when `output_dir` is E/W.
- Cap total specs per rotation (documented in follow-on spec) to avoid unbounded pool growth.
- Optional: game_data footprint/connector derivation behind feature flag.

---

## §8 — Documentation cross-updates

| Doc | Update |
|-----|--------|
| [`2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`](2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md) §13 | Link S2b spec; clarify A2-1 footprint work ≠ visible extensions until S2b |
| [`2026-05-27-rttp-miner-output-transport-topology-design.md`](2026-05-27-rttp-miner-output-transport-topology-design.md) § Phase 2 | Point to this spec (replaces “to be written”) |
| `documents/ai/current_plan.md` | ACTIVE row: S2b-1 in progress / plan link |

---

## §9 — Approval record

```text
Approved 2026-05-30 (Release Controller / Architecture Reviewer):

1. Replace "perpendicular_to_output_axis" with allowed_extension_arms(output_dir)
   = all cardinal arms except output_dir; INV-R-03 forbids forward output arm only.

2. S2b-1 scope: opposite-arm linear only → 4 specs per rotation.
   S2b-2: N/S perpendicular families deferred.

3. ExtensionTopologyKind StrEnum (no free-form topology_kind strings in metrics).

4. visible_extension_cell_count >= 1 is conditional on route-feasible ext>=1 commit.

5. Gate B evidence recapture after S2b-1; not part of S2b-1 close.
```

---

## §10 — References

| Doc | Relevance |
|-----|-----------|
| [`2026-05-27-rttp-miner-output-transport-topology-design.md`](2026-05-27-rttp-miner-output-transport-topology-design.md) | INV-R, Phase 1/2 boundary |
| [`2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`](2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md) | Gate A closed; S2b open |
| [`2026-05-26-rttp-confirmed-placement-footprint-design.md`](2026-05-26-rttp-confirmed-placement-footprint-design.md) | Overlay extension semantics |
| `django_apps/asteroid_lab/genetic_sample/gene_template.py` | `throughput_factor_for_extension_count` |
| `optimization/candidates/pattern_library.py` | TEST-ONLY; lin_* anti-pattern for production |
