# Manual: Frontend · Templates · Static Assets

## Web Interface Guidelines (MUST reference)

When building or reviewing **any** Django web interface (templates, static JS/CSS, `frontend/**`), **always reference** the Vercel Web Interface Guidelines as the default UI quality bar:

- https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md

Auto-applied via [`.cursor/rules/web-interface.mdc`](../../../.cursor/rules/web-interface.mdc). Repo canonical docs (this manual, [`architecture.mdc`](../../../.cursor/rules/architecture.mdc)) take precedence on conflict.

## Django side

- Template · page assembly: `django_apps/web/templates/`
- Static JS/CSS: `django_apps/web/static/`

Keep views thin ([`django.md`](django.md)).

## Recipe Graph editor (Vite, etc.)

- Source: `frontend/recipe_graph_editor/` (Tailwind 4, etc. — check `package.json` in that directory)
- Fixture-based wire rule verification: `npm --prefix frontend/recipe_graph_editor test` (Vitest, synced with `tests/fixtures/recipe_connection_rule_scenarios.json`)
- If build output is bundled into the web app as static assets, confirm **build · copy steps after changes** are included in the current task scope.

## Graph layout engine (`frontend/graph_layout/`)

- Source is TypeScript modules (`graphLayoutEngine.ts` entry + stepwise `graphLayout*.ts` implementations). Shared logic for timeline · editor.
- Django static bundles **`django_apps/web/static/web/js/solver_graph_layout.js`**, **`editor_graph_layout.js`** are **esbuild outputs**. They live in the repo but **must not be edited directly.** After changing layout logic, always regenerate.
- Regenerate: from repo root, `npm run build:graph-layout` (included in root `package.json` `build` script).
- Python unit test `tests/unit/web/test_editor_graph_layout.py` imports `editor_graph_layout.js` via Node; after engine changes, refresh static files with the command above, then run pytest (`-q` / `--quiet` / `--tb=no` forbidden — [`testing.md`](testing.md)).

## Principles

- Do not put business policy in the UI. API · service boundaries: see [`architecture.mdc`](../../../.cursor/rules/architecture.mdc).

## Related manuals

- Graph UI behavior: [`graph_ui.md`](graph_ui.md)
- Testing: [`testing.md`](testing.md)
