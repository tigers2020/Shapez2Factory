# Manual: Solver · Recipe Graph Logic

Before starting work, review [`AGENTS.md`](../../../AGENTS.md) and solver/graph confusion-prevention rules.

## Location

- Shape domain · parsing: `django_apps/shapez_core/`
- Solver · planner · recipe graph recalculation, etc.: `django_apps/shapez_solver/services/` and related paths

## Dependencies

`shapez_solver` imports only `shapez_core`. **Do not import Django web apps from the solver.**

## Concept separation (required)

Treat the following as **distinct**:

- demand summary
- source quantity / target output count
- materialized graph nodes (physical nodes)
- visual labels
- operation / intermediate node structure

**Matching summary numbers does not automatically mean graph connections · node structure are correct.**

Do **not** connect **operation output → another operation input** directly. Route through **intermediate shape nodes**.

## Tests

```bash
python -m pytest tests/unit/shapez_solver/   # -q / --quiet / --tb=no forbidden
```

Alignment between `recipe_graph_input_carrier` and frontend `recipeConnection`/`operationArity` is fixed by **`tests/fixtures/recipe_connection_rule_scenarios.json`** and `tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py`. Frontend-side fixture verification runs `npm --prefix frontend/recipe_graph_editor test`.

Details: [`testing.md`](testing.md).

## Reference research

[`documents/research/research_shapez2_game_systems_2026-05-01.md`](../../../research/research_shapez2_game_systems_2026-05-01.md) — for **shape physics** such as pins · layer caps · column gravity, treat the "Shape layers · Pin mechanics" section of that document as canonical.

## Related manuals

- UI · editor: [`graph_ui.md`](graph_ui.md)
