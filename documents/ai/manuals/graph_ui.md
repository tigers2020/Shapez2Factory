# Manual: Graph UI (Recipe Graph Screen)

Read when working on visualization · editor. If rules overlap [`solver.md`](solver.md), **solver is canonical**.

## Location (examples)

- Django static · templates: `django_apps/web/`
- Recipe graph editor bundle: `django_apps/web/static/web/js/recipe_graph_editor/`
- Source editor (build when needed): `frontend/recipe_graph_editor/`

## Principles

- Do not confuse **display data** with the **solver's internal physical graph**.
- Keep labels · coordinates · React Flow adapters at the UI/adapter boundary; domain rules stay in core/solver.

## Confusion prevention (repeat)

Demand summary alone does **not** prove **connection graph correctness**. No direct operation-to-operation links · route via intermediate shape nodes — same as [`solver.md`](solver.md).

### Recipe graph: material / fluid wires

In validation messages, **material** means **shape carrier** (connections from ordinary `shape` nodes), not “crystal parts only.” **fluid** means connections from solid-color fluid sources with `source_carrier=fluid`.

**Crystal Generator** (`crystal_generator`): if the node has `crystal_color`, only **one shape input** is required. Without `crystal_color`, connect like Painter: fluid on top `in-1`, material (target shape) on bottom `in`. Rule summary: see [`documents/game_rules/crystal_mechanics.md`](../../game_rules/crystal_mechanics.md) “Recipe graph (wire types)” section.

### When changing operation · wire rules (checklist)

When changing operation types · input slots · material/fluid carrier rules, update **`django_apps/shapez_solver/services/recipe_graph_input_carrier.py`** (canonical) together with **`frontend/recipe_graph_editor/src/recipeConnection.ts`**, **`operationArity.ts`**. Add/update shared scenarios in **`tests/fixtures/recipe_connection_rule_scenarios.json`**, then verify both sides with `python -m pytest tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py` and `npm --prefix frontend/recipe_graph_editor test` (`-q` / `--quiet` / `--tb=no` forbidden — [`testing.md`](testing.md)).

## Browser verification

When needed, run the local server and verify manually or with MCP browser tools (`.cursor/rules/mcp.mdc`).

## Related manuals

- Frontend build · Tailwind: [`frontend.md`](frontend.md)
