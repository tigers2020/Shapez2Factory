# Core Abstraction: Shapes Are Token Grids, Not Physics

## Conclusion

The shapez family shape system is better modeled as a **grid-based symbol manipulation system** than as **rigid-body physics simulation**:

- A shape is not a real rigid body but a normalized token structure of **at most 4 layers × 4 quadrants per layer**.
- Buildings (machines) are close to **pure functions** that transform these tokens.

## One-Line Solver Definition

```text
Shape = Layer[]
Layer = Quadrant[4]   # this project: SW, NW, NE, SE (= quadrants[0..3], shape_encoding.md)
Operation = (Shape, ...) -> (Shape, ...)
```

With this abstraction, **cut, rotate, stack, and paint** are all expressible as array operations, permutations, merges, and color-only replacement.

## Related Documents

- [shape_encoding.md](shape_encoding.md)
- [solver_domain_model.md](solver_domain_model.md)
