# materialized graph render parity research

Date: 2026-05-02

## Symptoms

Per user confirmation:

- Solver page body copy looks up to date.
- Materialized graph toggle still shows old curved edges and card scroll.

## Code facts

- Raw and materialized graphs both use `timeline_request.js -> mountGraph() -> renderSolverGraph()` same render path.
- No separate materialized-only graph renderer exists.
- By code alone, raw/materialized display difference should not occur.

## Possible causes

1. **Browser module cache**
   - Template HTML updates but `solver_timeline.js` and nested module imports share same URL so browser may keep old JS.
   - Matches "copy fresh, graph stale" symptom exactly.

2. **Materialized payload render regression**
   - Generic graph sample may pass new markup while real `materialized_graph` structure hits exception path.
   - Requires test fetching actual API payload and validating via `renderSolverGraph(materialized_graph)`.

## Response direction

- Append version query to graph entry script and nested graph module imports for reliable cache busting.
- Add test putting materialized graph API payload through `renderSolverGraph()` to confirm current markup applies.

## Conclusion

This reinforcement is not backend graph semantics change but:

- graph UI module cache busting
- materialized graph rendering parity test addition

Those two items are the safest framing.
