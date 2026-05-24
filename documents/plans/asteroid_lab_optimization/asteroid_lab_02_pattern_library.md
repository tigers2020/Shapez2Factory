---
status: ARCHIVED
do_not_use_as_authority: true
archived_reason: pre-RTTP plan snapshot; see documents/Algorithm/ and docs/superpowers/specs/
superseded_by:
  - documents/ai/current_plan.md
  - docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md
---

# Phase 2 — Pattern Library / Local DP Compiler


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_02_pattern_library.md`](../../Algorithm/asteroid_lab_02_pattern_library.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

## Purpose

Deterministically generate small local patterns for extractor + extension.

The DP/local search at this stage is not whole-map optimization.

```text
DP = local pattern compiler
```

## Connection to RouteGoal / probe

Patterns fix geometry via **offsets, `output_dir`, `output_stub_offset`**. Absolute cells after offset projection are **island-local (x, y)** (`Coord`). `RouteProbeInput.start` is projected to the **`output_stub` absolute coordinate** after placement (Phase 3). The `RouteGoal` set and `RouteCellDomain` come from `OptimizationInput` and are not duplicated in the pattern DTO.

Extension attachment rules (extractor, prior extension, R direction, etc.) are implicitly recoverable in **v0 linear**, but the **attachment graph is made explicit** to prevent facing confusion after v1 branching/rotation.

## v0 pattern scope

The initial version supports linear patterns only.

```text
extractor only
extractor + 1 extension
extractor + 2 extensions
extractor + 3 extensions
```

## Excluded patterns

The following patterns are excluded in v0.

```text
T-shape
branch extension
ring pattern
nonlinear compact pattern
cross-resource pattern
```

## DTO

```python
@dataclass(frozen=True)
class ExtensionAttachment:
    extension_offset: Coord
    parent_offset: Coord
    required_facing: Direction
```

`v0 linear`: the extractor is the parent; each extension has the previous chain cell as parent.

`required_facing` is fixed as **the extension module's own attachment/output reference direction**, facing **toward `parent_offset`**. On validation it must **match** `cardinal_unit_toward(extension_offset, parent_offset)` (or equivalent `direction_from(extension → parent)`). If Shapez2 game rules require the opposite sign, implementation follows that, but **which cell is the subject** must be fixed identically in docs and tests.

```python
@dataclass(frozen=True)
class BundlePattern:
    pattern_id: str
    extension_count: int
    occupied_offsets: frozenset[Coord]
    extractor_offset: Coord
    extension_offsets: tuple[Coord, ...]
    attachments: tuple[ExtensionAttachment, ...]
    output_dir: Direction
    output_stub_offset: Coord
    throughput_factor: int
    topology_kind: str
```

### `throughput_factor` meaning (fixed)

Game rules: extractor base **×4**, **+×4** per extension, max 3 extensions → max **×16**.

`throughput_factor` is treated **only as that multiplier integer**: `4`, `8`, `12`, `16` (extractor-only=4, +1=8, …).

The name is fixed as `throughput_factor` rather than `throughput_multiplier` (ambiguous) so implementation does not **mis-scale** with `extension_count + 1` etc.

## Canonical direction / rotation

**Canonical pattern:** doc/library default generation builds offsets with **`output_dir = E` (east output)** as baseline.

**Rotation:** rotate the canonical E pattern to target `output_dir` `N/E/S/W` (rotate coordinates, `output_stub_offset`, `attachments.required_facing`, `occupied_offsets` by the same rule). Sprite/editor rotation follows this baseline too.

All patterns support 4-direction rotation.

```text
N
E
S
W
```

## Throughput model

Base model:

```text
extractor base = x4
each extension = +x4
max extension = 3
max total = x16
```

That is:

```text
extractor only = x4
+1 extension = x8
+2 extension = x12
+3 extension = x16
```

## Invariant

```text
[ ] pattern_id deterministic
[ ] output_stub is not occupied
[ ] extractor_offset exactly one
[ ] extension_count <= 3
[ ] occupied_offsets contains extractor + extensions only
[ ] attachments length == extension_count (v0 linear)
[ ] offsets/projection deterministic on island map grid after rotation
[ ] throughput_factor in {4, 8, 12, 16} and matches extension_count
```

## Tests

```text
test_pattern_library_generates_linear_0_to_3_extensions
test_pattern_library_pattern_ids_are_deterministic
test_pattern_library_output_stub_not_occupied
test_pattern_library_rotations_deterministic_on_island_grid
test_pattern_library_throughput_factor_matches_extension_count
test_pattern_library_attachments_linear_chain
```

## Completion criteria

```text
[ ] linear pattern 0~3 extension generation
[ ] 4-direction rotation support
[ ] deterministic order guaranteed
[ ] output_stub computation complete
[ ] ExtensionAttachment·throughput_factor·canonical E contract reflected
```
