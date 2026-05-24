# Phase 2 — Pattern Library / Local DP Compiler

## Purpose

Deterministically generate small local patterns for extractor + extension.

DP/local search in this phase is not full-map optimization.

```text
DP = local pattern compiler
```

## Connection to RouteGoal / probe

Patterns fix geometry via **offsets·`output_dir`·`output_stub_offset`**. Offsets·projected absolute cells are **Server X/Y** (`Coord`). `RouteProbeInput.start` is projected to the **`output_stub` absolute coordinate** after placement (Phase 3). `RouteGoal` set·`RouteCellDomain` come from `OptimizationInput` and are not duplicated on pattern DTOs.

Extension attachment rules (extractor·previous extension·R direction, etc.) are implicitly recoverable in **v0 linear**, but **attachment graph is made explicit** to prevent facing confusion after v1 branching·rotation.

## v0 pattern scope

```text
extractor only
extractor + 1 extension
extractor + 2 extensions
extractor + 3 extensions
```

```text
T-shape
branch extension
ring pattern
nonlinear compact pattern
cross-resource pattern
```

**A pipe/belt always attaches in front of the extractor output direction.**  
*Max size = pipe + extractor + 3 extension = 5*

## DTO

```python
@dataclass(frozen=True)
class ExtensionAttachment:
    extension_offset: Coord
    parent_offset: Coord
    required_facing: Direction
```

`v0 linear`: extractor is parent; each extension has the previous chain cell as parent.

`required_facing` is **the extension module's own attachment·output reference direction**, fixed to **face toward `parent_offset`**. On validation it must **match** `cardinal_unit_toward(extension_offset, parent_offset)` (or equivalent `direction_from(extension → parent)`). If Shapez2 game rules require opposite sign, implementation follows that, but **docs·tests fix “which cell is the subject”** identically.

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

### `throughput_factor` semantics (fixed)

Game rules: extractor base **×4**, **+×4** per extension, max extension 3 → max **×16**.

`throughput_factor` is treated **only as that multiplier integer**: `4`, `8`, `12`, `16` (extractor-only=4, +1=8, …).

The name is fixed as `throughput_factor` rather than `throughput_multiplier` (ambiguous) so implementation does not **mis-scale** with `extension_count + 1`, etc.

## Canonical direction·rotation

**Canonical pattern:** doc·library default generation builds offsets with **`output_dir = E` (east output)** as baseline.

**Rotation:** transform canonical E pattern to target `output_dir` of `N/E/S/W` (rotate coordinates·`output_stub_offset`·`attachments.required_facing`·`occupied_offsets` by the same rule). Follow this baseline when aligning with sprite·editor rotation.

All patterns support 4-direction rotation.

```text
N
E
S
W
```

## Throughput model

Game throughput **absolute canonical values** (30 shapes/min, 300 L/min, Space Belt 480×12, Space Pipe 28.8kL/m×12, saturation 12/72): [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../game_rules/shapez2_asteroid_space_transport_throughput.md).

Basic model:

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
[ ] post-rotation offsets·projection deterministic on Server integer grid
[ ] throughput_factor in {4, 8, 12, 16} and matches extension_count
```

## Tests

```text
test_pattern_library_generates_linear_0_to_3_extensions
test_pattern_library_pattern_ids_are_deterministic
test_pattern_library_output_stub_not_occupied
test_pattern_library_rotations_deterministic_on_server_grid
test_pattern_library_throughput_factor_matches_extension_count
test_pattern_library_attachments_linear_chain
```

## Completion criteria

```text
[ ] linear pattern 0~3 extension generation
[ ] 4-direction rotation support
[ ] deterministic order guarantee
[ ] output_stub computation complete
[ ] ExtensionAttachment·throughput_factor·canonical E contract reflected
```
