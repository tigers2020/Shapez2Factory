# Plan: solver graph quantity replica toggle (2026-05-02)

Related research: [documents/research_solver_graph_quantity_replica_toggle_2026-05-02.md](./research_solver_graph_quantity_replica_toggle_2026-05-02.md)

Original request summary: add a solver graph button that, when active, visually replicates base/source and target nodes according to `quantity`.

## Goals

- Preserve default graph display and API payload.
- User can switch between “representative nodes” and “quantity replica view” via button.
- Replica view expands source/target nodes only; intermediate/operation nodes stay as today.

## Implementation approach

1. Add replica toggle button to solver page graph panel.
2. Keep graph view state on frontend; switch between original and expanded graph on mount.
3. Expand source/target `quantity` into replica nodes/edges in separate helper.
4. Assign ids and display metadata so replica nodes do not conflict with selection/detail panel.
5. Add smoke/unit tests.

## Change targets

- `django_apps/web/templates/web/solver.html`
- `django_apps/web/static/web/js/solver_timeline.js`
- `django_apps/web/static/web/js/solver_timeline/timeline_request.js`
- `django_apps/web/static/web/js/solver_timeline/graph_mount.js`
- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- `django_apps/web/static/web/js/solver_timeline/graph_detail.js`
- One new helper file
  - e.g. `django_apps/web/static/web/js/solver_timeline/graph_quantity_toggle.js`
- Tests
  - `tests/integration/web/test_web_smoke.py`
  - one new unit test file

## Detailed steps

### 1. Add UI toggle

- Add button at top of graph panel.
- Default state off.
- Store current on/off in panel dataset or JS state.
- Toggle label should clearly indicate quantity replica purpose.

Example:

- `Show quantity replicas`
- off/on style change

### 2. Add derived graph helper

New helper contract:

- Input: serialized graph payload
- Output: graph payload with same shape

Behavior:

- If `quantity <= 1`, keep original node
- If `role === "source"` or `role === "target"` and `quantity > 1`:
  - replicate node `quantity` times
  - set replica node `quantity = 1`
  - add replica metadata:
    - `replica_index`
    - `replica_total`
    - `replica_of`
  - replicate related edges per replica

Example id rules:

- `${node.id}::replica::1`
- `${node.id}::replica::2`

### 3. Wire mount flow

- Store latest API graph as original on panel.
- Re-render current graph on toggle without re-fetch.
- When on, pass expanded graph from helper to `renderSolverGraph()` and detail selection.

### 4. Markup / detail display

- Add small badge like `COPY 1/4` on replica node cards.
- Show replica info in detail panel.
- Original quantity badge becomes `x1` on replica nodes; auxiliary copy explains expansion.

### 5. Tests

- integration smoke:
  - toggle marker present on solver page
- unit:
  - helper expands source/target only
  - edge replication correct
  - unchanged when quantity is 1
  - does not mutate original graph

## Tradeoffs

- Pros:
  - no backend contract change
  - fast toggle UX
  - reuse layout engine
- Cons:
  - graph can get wide/complex with large target/source fan-out
  - many duplicate edges can look dense

## Verification plan

- `python -m pytest tests/integration/web/test_web_smoke.py`
- `python -m pytest` or at minimum new web unit test + related smoke
- if needed `python -m ruff check django_apps/web/static/web/js tests`

## Post-approval implementation notes

- Do not touch backend `recipe_graph_builder.py` in this scope.
- Avoid new API response fields first; solve with frontend derived data.
- Limit replica expansion to source/target only.
