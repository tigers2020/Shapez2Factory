# graph_markup.js refactoring plan

Date: 2026-05-02

## Goals

- Split markup assembly responsibilities in `graph_markup.js` into helpers for simpler reading flow.
- Preserve graph render output contract and smoke markers.

## Change scope

- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- `django_apps/web/static/web/js/solver_timeline.js` if needed

## Approach

1. Separate preview markup helper and shape meta badge helper.
2. Separate edge path/label helpers.
3. Separate viewport controls, hint, and stage markup helpers.
4. Replace broken hint strings with ASCII-based normal text.
5. Re-run smoke test scope to verify regression.

## Expected benefits

- Graph card and viewport layout can be read independently.
- Smaller change surface for preview fallback or edge style edits.
- Clearer boundary with next frontend split target `solver_graph_layout.js`.
