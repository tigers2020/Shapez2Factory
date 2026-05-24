# Shapez 2: Stacker Input Roles (bottom / top)

## Claim (Reference)

Wiki summaries say Stacker stacks the shape from the **top input** onto the shape from the **bottom input**.

```text
stacker(bottom_input, top_input) -> output
```

## Solver and Graph Model Recommendation

- Always use **bottom / top** terminology.
- Modeling as **left / right** easily misaligns ports, wiring, and demand summaries.

## Trust

- Wiki: **Medium**. Cross-check with in-game tooltips and measurement.

## Related

- [operation_stacker.md](operation_stacker.md)
