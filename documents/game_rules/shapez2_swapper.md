# Shapez 2: Simulated Swapper

## Claim (Reference)

Simulated Swapper takes two shape signals and outputs the result of **swapping the west halves of both shapes**, per wiki-style descriptions.

## Solver Function Form (Conceptual)

```python
swap_west_halves(a, b) -> (a_with_b_west, b_with_a_west)
```

## Optimization Perspective

Checker/stripe patterns may have **shorter paths via swap** than repeated **cut + stack**.

Example pattern (conceptual):

```text
RcRcRcRc + CuCuCuCu
rotate/align then swap halves -> RcCuRcCu family
```

## Trust

- Wiki: **Medium**. Verify simulated building behavior in-game.

## Related

- [solver_search_strategy.md](solver_search_strategy.md)
