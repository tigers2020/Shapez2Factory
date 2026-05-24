# Shapez 2: Spatial Model vs Shape Model

## Summary

- **Factory layout and logistics** may move to 3D/platform-based space.
- **Shapes themselves** are still often described as **layer / part (per-quadrant)** structure.

## Implications for Internal Solver Model

The solver's core concern is the **invariant structure of shape codes** before "which belt layer items ride on":

```python
Shape = tuple[Layer, ...]   # bottom → top
Layer = tuple[Quadrant, Quadrant, Quadrant, Quadrant]
```

Pattern of each quadrant as `Part | Empty` aids documentation and tests ([solver_domain_model.md](solver_domain_model.md)).

## Sources and Trust

- wiki.gg "Shapes", etc.: **Medium–High** (cross-verification recommended).
