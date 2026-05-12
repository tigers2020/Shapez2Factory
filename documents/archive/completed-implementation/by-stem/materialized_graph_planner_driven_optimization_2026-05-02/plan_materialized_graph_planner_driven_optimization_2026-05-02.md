# Materialized Graph Planner-Driven Optimization Plan

## Summary

Convert materialized graph construction to follow the solved planner recipe instead of the single-layer quarter reconstruction shortcut.

## Planned Changes

- Add research and plan documents before code edits.
- Disable the single-layer `_build_single_layer_batch_graph()` shortcut in `materialized_graph_builder`.
- Keep `_build_source_only_graph()` for solved recipes whose final node is already a source.
- Use existing demand propagation to determine:
  - how many source clones to seed from `base_demands`
  - how many times each operation recipe must run
  - how many final target clones must be marked as consumed targets
- Remove materialized-only helpers that exist solely for quarter pooling, alignment, and forced re-stack assembly.

## Fallbacks and Non-Goals

- Fallback remains the source-only graph for direct-source targets.
- No API schema changes.
- No expansion of unsupported multi-layer pin/crystal factory-demand behavior in this change.

## Verification

- Add unit coverage for half-friendly targets to prove materialized operations now follow planner structure.
- Keep mixed-source quantity regression coverage.
- Run `pytest`, `ruff check .`, `mypy .`, and `black .` after implementation.
