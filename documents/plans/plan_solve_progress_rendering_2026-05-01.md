# Solve Progress Rendering Plan


> **Plans (misc):** Project planning memo; not Asteroid Lab coordinate canon. See [`documents/Algorithm/`](../Algorithm/) and [`docs/superpowers/specs/`](../docs/superpowers/specs/) for active specs.

## Purpose

The renderer is now a core product surface, not just a demo preview. Solver
progress should eventually render the same canonical `ShapeRenderScene` used by
the Three.js glTF viewer.

## Current State

`SolverResult` currently exposes `steps: tuple[str, ...]`. That is enough for a
placeholder, but not enough to render operation progress.

## Future DTO Shape

When the solver begins emitting real intermediate patterns, evolve the
application layer toward:

```python
@dataclass(frozen=True, slots=True)
class SolveStep:
    step_index: int
    operation_name: str
    input_pattern: NormalizedShapePattern
    output_pattern: NormalizedShapePattern
    explanation: str


@dataclass(frozen=True, slots=True)
class SolverResult:
    found: bool
    steps: tuple[SolveStep, ...] = ()
```

The web layer should serialize each `SolveStep.output_pattern` through
`build_shape_render_scene()` and render it through the same Three.js glTF adapter
used by the demo page.

## Boundary

- Solver and domain code own shape correctness and operation semantics.
- `ShapeRenderScene` translates normalized state into renderer-neutral visual data.
- The web adapter owns glTF asset URLs, materials, camera controls, and browser
  interaction.
