# Shapez 2: Pin, Floating Shapes, and Support

## Steam Devlog Summary (Trust: High)

- Shapez 2 is designed **not to allow floating shapes** as in shapez 1.
- **Pin**: Pin Pusher removes an entire quadrant and replaces it with a **pin part** like `P-` (exact character code per game data).

## Solver Meaning (Conceptual)

```text
Upper layer only with no normal part below → invalid
Pin acting as support → valid
```

So a Shapez 2 solver may need a **support validation** layer.

## Rough Algorithm Sketch (Not Final)

```python
is_supported(part at layer L, quadrant Q):
    return exists physical_or_pin_part at layer L-1, same quadrant
        or connected_to_supported_adjacent_part(...)
```

**Exact adjacency and fall rules need further verification** — stating that honestly is appropriate.

## Related

- `pin` part in [solver_domain_model.md](solver_domain_model.md)
