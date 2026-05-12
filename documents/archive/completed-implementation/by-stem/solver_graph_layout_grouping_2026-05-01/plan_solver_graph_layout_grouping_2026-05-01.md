# Plan: Solver Graph Layout Grouping

## Summary

Replace the current top-aligned depth-column layout in `solver_timeline.js` with a deterministic layered grouping layout that keeps left-to-right flow while pulling related nodes closer together vertically.

## Changes

- Refactor graph layout into small pure functions inside `django_apps/web/static/web/js/solver_timeline.js`.
- Add depth analysis, adjacency maps, barycenter ordering, and vertical compaction.
- Keep graph rendering, pan/zoom, and API shape unchanged.
- Export layout helpers so tests can validate grouped layout behavior through `node`.

## Verification

- Keep existing page and API smoke tests green.
- Add tests for grouped branch proximity, deterministic output, non-trivial same-depth ordering, and accurate bounds.
- Run `pytest`, `ruff check .`, `mypy .`, and `black .`.
