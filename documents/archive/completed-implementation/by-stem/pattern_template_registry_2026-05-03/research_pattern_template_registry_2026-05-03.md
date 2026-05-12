# Pattern template registry research (2026-05-03)

## Context

- `PlannerService` already routes repeated single-layer patterns through
  `try_prebuilt_pattern` before generic half/quadrant assembly.
- `prebuilt_pattern_registry.py` currently mixes three responsibilities in one branch:
  pattern matching, template selection, and recipe expansion.
- Existing solver output is based on `SourceRecipe`, `OperationRecipe`, and `SolvedRecipe`.
  Keeping that wire shape avoids changes to graph rendering and API serialization.

## Current behavior

- `half_and_half` targets such as `CuCuRuRu` expand to `cutter`, `cutter`, `swapper`.
- Rotated half-and-half variants restore orientation with a final rotation operation.
- `checker` targets such as `CuRuCuRu` build one half, rotate it 180 degrees, then swap.
- Colored variants rely on the normal paint rule while preserving the same template shape.

## Implementation direction

- Split prebuilt pattern support into two code-level registries:
  pattern definitions and template definitions.
- Keep templates as internal recipe builders, not as new macro recipe nodes.
- Expose template metadata only inside the solver service for tests and future UI work.
- Preserve existing planner rule order and graph/API response shape.

## Risk notes

- Template matching must continue to reject unsupported materials and non-full single-layer
  targets.
- Existing cost sorting depends on expanded recipes, so template builders must keep returning
  ordinary `SolvedRecipe` instances.
