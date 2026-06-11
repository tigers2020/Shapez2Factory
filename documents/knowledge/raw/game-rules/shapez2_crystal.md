# Shapez 2: Crystal Generator (Summary and Links)

Detailed mechanics, sources, and solver rules: **[crystal_mechanics.md](crystal_mechanics.md)** is canonical.

## Implementation Status (shapez2Solver)

- **Crystal Generator**: [`crystal_fill_gaps_and_pins`](../../django_apps/shapez_core/domain/crystal_geometry.py) + [`OperationEngine`](../../django_apps/shapez_solver/services/operation_engine.py). Color: node `crystal_color` (one char) or uniform color from second input wire in **recipe graph** ([`apply_operation`](../../django_apps/shapez_solver/services/operation_semantics.py)); same when passing macro `OperationRecipe.color`.
- **Cluster and shatter**: [`connected_crystal_cluster`](../../django_apps/shapez_core/domain/crystal_geometry.py), [`shatter_crystal_cluster`](../../django_apps/shapez_core/domain/crystal_geometry.py) — not yet auto-wired to Cut/Swap/Stack.

## Wiki Summary (Reference)

Crystal Generator fills **gaps and pin positions** on the input shape with crystal, applied up to **highest used layer**, per wiki descriptions.

## Trust

- Wiki and community mix — verify details in-game.

## Related

- [crystal_mechanics.md](crystal_mechanics.md)
- [shapez2_pin_support.md](shapez2_pin_support.md)
